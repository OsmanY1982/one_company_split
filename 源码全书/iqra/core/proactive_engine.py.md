# `iqra/core/proactive_engine.py`

> 路径：`iqra/core/proactive_engine.py` | 行数：366


---


```python
# -*- coding: utf-8 -*-
"""
ProactiveEngine — AI 主动执行与推送引擎

解决 AI "问一句回一句"的被动模式，实现:
  1. 完成后自动建议下一步（上下文意图推测）
  2. 后台监控 + 主动推送消息到对话窗口
  3. 自主持续执行循环（遇阻塞才问，否则不打扰）

用法:
    from iqra.core.proactive_engine import ProactiveEngine

    engine = ProactiveEngine(chat_engine=chat_engine, agent=agent_loop)
    engine.on_push.connect(chat_window.append_message)   # 主动推送
    engine.on_suggest.connect(chat_window.show_suggestion) # 建议气泡

    # 启动后台监控
    engine.start_monitoring()

    # 完成一次任务后自动建议
    engine.suggest_next(user_message="帮我整理桌面文件",
                        completion_summary="桌面文件已按类型归类到 4 个文件夹")
"""

import json
from typing import Optional, List, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal

from .iqra_logging import logger
from .proactive_monitors import (
    BaseMonitor,
    FileWatchMonitor,
    FSEventMonitor,
    ProjectHealthMonitor,
    ProactiveEvent,
    ProactiveEventType,
)


# ═══════════════════════════════════════════
# 建议生成器
# ═══════════════════════════════════════════

SUGGESTION_SYSTEM_PROMPT = """你是 AI 助手的主动建议生成器。根据已完成的任务和当前系统状态，生成 1-2 条用户可能需要的下一步建议。

规则:
1. 每条建议必须是具体可操作的（不是泛泛的"你还可以做XX"）
2. 优先关联刚完成的任务（如"刚整理了桌面，要不要把下载文件夹也整理？"）
3. 如果没有明显建议，可以基于系统状态（如"发现 3 个 7 天未清理的临时文件"）
4. 建议要简短，每条不超过 25 字
5. 输出纯 JSON 数组: [{"title": "...", "body": "..."}]
6. 如果实在没有建议，输出空数组 []

上下文:
{context}"""


class SuggestionEngine:
    """智能建议生成"""

    def __init__(self, backend=None):
        self._backend = backend

    def generate(
        self,
        user_message: str,
        completion_summary: str,
        system_context: str = "",
    ) -> List[Dict]:
        """
        生成下一步建议

        Args:
            user_message: 原始用户请求
            completion_summary: 完成结果总结
            system_context: 系统状态摘要（当前项目、打开文件等）

        Returns:
            [{title, body}, ...]
        """
        if not self._backend:
            return []

        context_parts = [
            f"用户请求: {user_message}",
            f"完成结果: {completion_summary}",
        ]
        if system_context:
            context_parts.append(f"系统状态: {system_context}")

        messages = [
            {"role": "system", "content": SUGGESTION_SYSTEM_PROMPT.format(
                context="\n".join(context_parts)
            )},
            {"role": "user", "content": "请生成建议。"},
        ]

        try:
            response = self._backend.chat(messages)
            content = response.content.strip() if hasattr(response, 'content') else str(response).strip()

            # 提取 JSON
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.split("```")[0].strip()

            suggestions = json.loads(content)
            if not isinstance(suggestions, list):
                return []
            return suggestions

        except Exception as e:
            logger.debug("建议生成跳过: %s", e)
            return []


# ═══════════════════════════════════════════
# ProactiveEngine 主类
# ═══════════════════════════════════════════

class ProactiveEngine(QObject):
    """
    主动执行与推送引擎

    信号:
      on_push: 主动推送事件（告警/洞察/提醒）
      on_suggest: 智能建议事件（任务完成后的下一步）
    """

    on_push = pyqtSignal(ProactiveEvent)
    on_suggest = pyqtSignal(ProactiveEvent)

    def __init__(
        self,
        backend=None,
        project_path: str = "",
        watch_paths: List[str] = None,
    ):
        """
        Args:
            backend: BaseLLMBackend 实例（用于生成智能建议）
            project_path: 项目根目录（用于健康监控）
            watch_paths: 需要监控文件变化的目录列表
        """
        super().__init__()
        self._backend = backend
        self._suggester = SuggestionEngine(backend)
        self._monitors: List[BaseMonitor] = []
        self._is_monitoring = False

        # 初始化监控器
        if project_path:
            self.add_monitor(ProjectHealthMonitor(project_path))
        if watch_paths:
            if FSEventMonitor is not None:
                self.add_monitor(FSEventMonitor(watch_paths))
            else:
                self.add_monitor(FileWatchMonitor(watch_paths))

    # ── 建议生成 ──

    def suggest_next(
        self,
        user_message: str,
        completion_summary: str,
        system_context: str = "",
    ) -> List[ProactiveEvent]:
        """
        任务完成后生成下一步建议

        Args:
            user_message: 原始用户请求
            completion_summary: 完成结果总结
            system_context: 系统状态（当前项目、打开文件等）

        Returns:
            ProactiveEvent 列表（供调用方通过 on_suggest 信号发送）
        """
        suggestions = self._suggester.generate(
            user_message, completion_summary, system_context,
        )

        events = []
        for s in suggestions:
            event = ProactiveEvent(
                type=ProactiveEventType.SUGGESTION,
                title=s.get("title", ""),
                body=s.get("body", ""),
                action_label="试试看",
                action_payload={"action": "execute", "prompt": s.get("body", "")},
                priority=0,
            )
            events.append(event)

        return events

    def suggest_and_push(
        self,
        user_message: str,
        completion_summary: str,
        system_context: str = "",
    ) -> None:
        """生成建议并自动推送到 on_suggest 信号"""
        events = self.suggest_next(user_message, completion_summary, system_context)
        for event in events:
            self.on_suggest.emit(event)

    # ── 监控管理 ──

    def add_monitor(self, monitor: BaseMonitor):
        """添加监控器"""
        monitor.set_callback(self._on_monitor_event)
        self._monitors.append(monitor)

    def remove_monitor(self, name: str) -> bool:
        """移除监控器"""
        for m in self._monitors:
            if m.name == name:
                m.stop()
                self._monitors.remove(m)
                return True
        return False

    def start_monitoring(self):
        """启动所有后台监控"""
        for m in self._monitors:
            if not m.is_alive():
                m.start()
        self._is_monitoring = True
        logger.info("ProactiveEngine: 启动 %d 个监控器", len(self._monitors))

    def stop_monitoring(self):
        """停止所有后台监控"""
        for m in self._monitors:
            m.stop()
        self._is_monitoring = False
        logger.info("ProactiveEngine: 已停止所有监控")

    @property
    def is_monitoring(self) -> bool:
        return self._is_monitoring

    @property
    def monitors(self) -> List[str]:
        return [m.name for m in self._monitors]

    # ── 心跳检测 ──

    def check_heartbeats(self, timeout: float = None) -> List[str]:
        """
        检测所有监控器的心跳状态，返回僵死监控器名称列表

        Args:
            timeout: 覆盖各监控器的心跳超时阈值；不传则使用各监控器自身配置

        Returns:
            僵死（is_stale=True）的监控器名称列表
        """
        stale = []
        for m in self._monitors:
            if m.is_stale(timeout=timeout):
                stale.append(m.name)
        return stale

    def restart_stale_monitors(self, timeout: float = None) -> int:
        """
        检测并重启所有僵死监控器

        Args:
            timeout: 覆盖各监控器的心跳超时阈值

        Returns:
            实际重启的监控器数量
        """
        restarted = 0
        for m in self._monitors:
            if m.is_stale(timeout=timeout):
                logger.warning("ProactiveEngine: %s 心跳超时，正在重启…", m.name)
                try:
                    m.stop()
                    m.join(timeout=5)
                except Exception:
                    pass
                new_monitor = self._recreate_monitor(m)
                if new_monitor:
                    self._monitors.remove(m)
                    self.add_monitor(new_monitor)
                    restarted += 1
        return restarted

    def _recreate_monitor(self, stale_monitor: BaseMonitor) -> Optional[BaseMonitor]:
        """根据僵死监控器的类型重新创建等价实例"""
        from .proactive_monitors import (
            FileWatchMonitor as _FWM,
            FSEventMonitor as _FSM,
            ProjectHealthMonitor as _PHM,
        )
        name = stale_monitor.name
        if name == "FileWatchMonitor":
            paths = getattr(stale_monitor, '_watch_paths', [])
            interval = stale_monitor.interval_seconds
            return _FWM(paths, interval)
        elif name == "FSEventMonitor" and _FSM is not None:
            paths = getattr(stale_monitor, '_watch_paths', [])
            return _FSM(paths)
        elif name == "ProjectHealthMonitor":
            pp = getattr(stale_monitor, 'project_path', "")
            return _PHM(pp)
        return None

    # ── 手动推送 ──

    def push_alert(self, title: str, body: str, priority: int = 1):
        """手动推送告警"""
        self.on_push.emit(ProactiveEvent(
            type=ProactiveEventType.ALERT,
            title=title, body=body, priority=priority,
        ))

    def push_insight(self, title: str, body: str, action_label: str = "",
                     action_payload: Dict = None):
        """手动推送洞察"""
        self.on_push.emit(ProactiveEvent(
            type=ProactiveEventType.INSIGHT,
            title=title, body=body,
            action_label=action_label,
            action_payload=action_payload or {},
        ))

    # ── 内部回调 ──

    def _on_monitor_event(self, event: ProactiveEvent):
        """监控器回调：转发到 on_push 信号"""
        self.on_push.emit(event)


# ═══════════════════════════════════════════
# 全局实例
# ═══════════════════════════════════════════

_proactive: Optional[ProactiveEngine] = None


def get_proactive_engine(
    backend=None,
    project_path: str = "",
    watch_paths: List[str] = None,
) -> ProactiveEngine:
    """获取全局 ProactiveEngine 单例"""
    global _proactive
    if _proactive is None:
        _proactive = ProactiveEngine(
            backend=backend,
            project_path=project_path,
            watch_paths=watch_paths,
        )
    return _proactive


def reset_proactive_engine():
    global _proactive
    if _proactive:
        _proactive.stop_monitoring()
    _proactive = None

```
