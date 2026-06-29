# `iqra/core/proactive_monitors.py`

> 路径：`iqra/core/proactive_monitors.py` | 行数：451


---


```python
# -*- coding: utf-8 -*-
"""
proactive_monitors — 主动引擎监控器模块

内含:
  - BaseMonitor: 监控器基类（心跳检测、僵死判断）
  - FileWatchMonitor: 轮询式文件变化监控
  - FSEventMonitor: macOS FSEvents 零轮询文件监控（watchdog 可用时）
  - ProjectHealthMonitor: 项目健康度监控（__pycache__ 膨胀等）
"""

import os
import time
import threading
from typing import Optional, Callable, List, Dict

from .iqra_logging import logger

# ═══════════════════════════════════════════
# 事件类型（从 proactive_engine 迁出，打破循环导入）
# ═══════════════════════════════════════════
from enum import Enum, auto
from dataclasses import dataclass, field


class ProactiveEventType(Enum):
    SUGGESTION = auto()     # 智能建议（任务完成后的下一步）
    ALERT = auto()          # 监控告警（文件异常、进程崩溃等）
    INSIGHT = auto()        # 洞察发现（发现可优化项）
    REMINDER = auto()       # 提醒（定时任务到期）


@dataclass
class ProactiveEvent:
    """主动推送事件"""
    type: ProactiveEventType
    title: str                        # 简短标题
    body: str                         # 详细信息
    action_label: str = ""            # 可操作按钮文字（如"执行"）
    action_payload: Dict = field(default_factory=dict)  # 操作附带数据
    priority: int = 0                 # 0=常规, 1=重要, 2=紧急
    timestamp: float = field(default_factory=lambda: __import__('time').time())

# watchdog (macOS FSEvents) — 可选依赖，不可用时回退轮询
try:
    from watchdog.observers.fsevents import FSEventsObserver as _FSObserver
    from watchdog.events import FileSystemEventHandler as _FSHandler
    _WATCHDOG_AVAILABLE = True
except ImportError:
    _WATCHDOG_AVAILABLE = False


# ═══════════════════════════════════════════
# 监控器基类
# ═══════════════════════════════════════════

class BaseMonitor(threading.Thread):
    """监控器基类（支持心跳检测僵死）"""

    def __init__(self, interval_seconds: float = 30.0, name: str = "Monitor",
                 heartbeat_timeout: float = 0.0):
        """
        Args:
            interval_seconds: 检查间隔（秒）；FSEventMonitor 等事件驱动型为 0
            name: 监控器名称
            heartbeat_timeout: 心跳超时阈值（秒），超过此时间未心跳视为僵死；
                               0 表示不启用心跳检测（事件驱动型监控器无需轮询心跳）
        """
        super().__init__(daemon=True)
        self.interval_seconds = interval_seconds
        self.name = name
        self._stop_event = threading.Event()
        self._callback: Optional[Callable[[ProactiveEvent], None]] = None
        self._last_heartbeat: float = 0.0
        self._heartbeat_timeout = heartbeat_timeout
        self._heartbeat_lock = threading.Lock()

    def set_callback(self, callback: Callable[[ProactiveEvent], None]):
        self._callback = callback

    def stop(self):
        self._stop_event.set()

    def run(self):
        """子类重写 _check() 方法"""
        self._update_heartbeat()
        while not self._stop_event.wait(self.interval_seconds):
            try:
                events = self._check()
                self._update_heartbeat()
                if events and self._callback:
                    for event in events:
                        self._callback(event)
            except Exception as e:
                logger.debug("%s 检查异常: %s", self.name, e)
                self._update_heartbeat()

    def _update_heartbeat(self):
        """更新心跳时间戳（线程安全）"""
        with self._heartbeat_lock:
            self._last_heartbeat = time.time()

    def is_stale(self, timeout: float = None) -> bool:
        """
        判断监控器是否僵死（超过心跳超时未更新）

        Args:
            timeout: 覆盖实例的 heartbeat_timeout；不传则使用构造时设置的值

        Returns:
            True 如果心跳超时（僵死），False 如果健康
        """
        if not self.is_alive():
            return False  # 已退出不算僵死，算正常终止
        with self._heartbeat_lock:
            last = self._last_heartbeat
        # 刚启动尚未执行第一次检查
        if last == 0.0:
            return False
        threshold = timeout if timeout is not None else self._heartbeat_timeout
        if threshold <= 0:
            return False  # 未启用心跳检测
        return (time.time() - last) > threshold

    @property
    def last_heartbeat(self) -> float:
        """最后一次心跳时间戳（Unix 时间）"""
        with self._heartbeat_lock:
            return self._last_heartbeat

    def _check(self) -> List[ProactiveEvent]:
        """子类实现：返回发现的主动事件列表"""
        return []


# ═══════════════════════════════════════════
# 文件变化监控（轮询）
# ═══════════════════════════════════════════

class FileWatchMonitor(BaseMonitor):
    """
    文件变化监控器（轮询模式）

    监控指定目录下的文件变化（新增/删除/修改），
    发现异常变化时推送告警。

    心跳机制：若 _check() 因网络文件系统等原因阻塞，
    可在 interval_seconds * 3 内被 ProactiveEngine 检测并重启。
    """

    def __init__(self, watch_paths: List[str] = None, interval_seconds: float = 30.0):
        super().__init__(interval_seconds, "FileWatchMonitor",
                         heartbeat_timeout=interval_seconds * 3.0)
        self._watch_paths = watch_paths or []
        self._last_snapshot: Dict[str, Dict] = {}  # path → {mtime, size}

    def add_path(self, path: str):
        if path not in self._watch_paths:
            self._watch_paths.append(path)

    def _check(self) -> List[ProactiveEvent]:
        events = []
        for watch_path in self._watch_paths:
            if not os.path.exists(watch_path):
                continue

            try:
                current = {}
                for entry in os.scandir(watch_path):
                    if entry.is_file():
                        stat = entry.stat()
                        current[entry.name] = {
                            "mtime": stat.st_mtime,
                            "size": stat.st_size,
                        }
            except PermissionError:
                continue

            prev = self._last_snapshot.get(watch_path, {})

            # 检测新增和修改
            for name, info in current.items():
                if name not in prev:
                    events.append(ProactiveEvent(
                        type=ProactiveEventType.ALERT,
                        title=f"新文件: {name}",
                        body=f"{watch_path}/{name} ({info['size']} bytes)",
                        priority=0,
                    ))
                elif info["mtime"] != prev[name].get("mtime"):
                    events.append(ProactiveEvent(
                        type=ProactiveEventType.INSIGHT,
                        title=f"文件已更新: {name}",
                        body=f"{watch_path}/{name}",
                        priority=0,
                    ))

            self._last_snapshot[watch_path] = current

        return events


# ═══════════════════════════════════════════
# 文件变化监控 (FSEvents — 零轮询)
# ═══════════════════════════════════════════

if _WATCHDOG_AVAILABLE:

    class FSEventMonitor(BaseMonitor):
        """
        macOS FSEvents 文件监控器（零轮询，内核级事件驱动）

        替代 FileWatchMonitor 的 os.scandir 轮询，节省 CPU 和磁盘 I/O。
        通过 watchdog 封装内核 FSEvents API，在文件变化时毫秒级回调。

        特性:
          - 事件去重：0.5s 内同文件多事件合并为一条通知
          - 自动忽略临时文件（~ $ .swp .tmp .lock 等）
          - 优雅降级：watchdog 不可用时自动回退 FileWatchMonitor
        """

        #    忽略的临时文件后缀
        IGNORE_SUFFIXES = (".tmp", ".swp", ".swx", ".lock", ".part", ".crdownload")

        class _Handler(_FSHandler):
            """watchdog 事件处理器（内部类）"""

            def __init__(self, monitor):
                super().__init__()
                self._mon = monitor  # type: FSEventMonitor

            def on_created(self, event):
                if event.is_directory:
                    return
                self._mon._record_event("created", event.src_path)

            def on_modified(self, event):
                if event.is_directory:
                    return
                self._mon._record_event("modified", event.src_path)

            def on_deleted(self, event):
                if event.is_directory:
                    return
                self._mon._record_event("deleted", event.src_path)

            def on_moved(self, event):
                if event.is_directory:
                    return
                self._mon._record_event("moved", event.dest_path)

        def __init__(self, watch_paths: List[str] = None, **_kw):
            super().__init__(interval_seconds=0.0, name="FSEventMonitor")
            self._watch_paths = list(watch_paths or [])
            self._observer = _FSObserver()
            self._handler = FSEventMonitor._Handler(self)
            self._pending: Dict[str, Dict] = {}  # path → {type, first_seen}
            self._dedup_lock = threading.Lock()
            self._flush_timer: Optional[threading.Timer] = None

        # ── 路径管理 ──

        def add_path(self, path: str):
            if path not in self._watch_paths and os.path.isdir(path):
                self._watch_paths.append(path)
                if self.is_alive():
                    self._observer.unschedule_all()
                    for p in self._watch_paths:
                        self._observer.schedule(self._handler, p, recursive=True)

        def remove_path(self, path: str) -> bool:
            if path in self._watch_paths:
                self._watch_paths.remove(path)
                if self.is_alive():
                    self._observer.unschedule_all()
                    for p in self._watch_paths:
                        self._observer.schedule(self._handler, p, recursive=True)
                return True
            return False

        # ── 生命周期 ──

        def run(self):
            """启动 watchdog observer 替代轮询"""
            if not self._watch_paths:
                logger.debug("FSEventMonitor: 无监控路径，线程退出")
                return

            for p in self._watch_paths:
                if os.path.isdir(p):
                    try:
                        self._observer.schedule(self._handler, p, recursive=True)
                    except Exception as e:
                        logger.warning("FSEventMonitor 无法监控 %s: %s", p, e)

            self._observer.start()
            logger.info("FSEventMonitor: 已启动，监控 %d 个目录", len(self._watch_paths))

            # watchdog observer 内部线程已运行，本线程只需等待停止信号
            try:
                while not self._stop_event.wait(1.0):
                    pass
            finally:
                self._observer.stop()
                try:
                    self._observer.join(timeout=3)
                except Exception:
                    pass
                logger.info("FSEventMonitor: 已停止")

        def stop(self):
            """停止监控"""
            self._stop_event.set()
            # 刷新积压事件
            self._flush_pending()

        # ── 事件去重与推送 ──

        def _record_event(self, event_type: str, path: str):
            """记录文件事件（去重缓冲）"""
            basename = os.path.basename(path)

            # 忽略临时文件
            if basename.startswith(".") or basename.startswith("~"):
                return
            if basename.endswith(self.IGNORE_SUFFIXES):
                return

            with self._dedup_lock:
                now = time.time()
                if path in self._pending:
                    old = self._pending[path]
                    # 合并事件类型：保留更严重的（created > modified > deleted）
                    old_type = old["type"]
                    if event_type == "created":
                        pass  # 覆盖
                    elif event_type == "modified" and old_type not in ("created",):
                        old["type"] = "modified" if old_type != "created" else "created"
                    if old_type == "created":
                        event_type = "created"
                else:
                    self._pending[path] = {"type": event_type, "first_seen": now}

            # 启动/重置去重定时器
            if self._flush_timer:
                self._flush_timer.cancel()
            self._flush_timer = threading.Timer(0.5, self._flush_pending)
            self._flush_timer.daemon = True
            self._flush_timer.start()

        def _flush_pending(self):
            """将去重缓冲冲洗为 ProactiveEvent"""
            events = []
            with self._dedup_lock:
                for path, info in list(self._pending.items()):
                    evt_type = info["type"]
                    fname = os.path.basename(path)
                    fdir = os.path.dirname(path)

                    if evt_type == "created":
                        try:
                            sz = os.path.getsize(path)
                            body = f"{path} ({sz} bytes)"
                        except OSError:
                            body = path
                        events.append(ProactiveEvent(
                            type=ProactiveEventType.ALERT,
                            title=f"新文件: {fname}",
                            body=body,
                            priority=0,
                        ))
                    elif evt_type == "modified":
                        events.append(ProactiveEvent(
                            type=ProactiveEventType.INSIGHT,
                            title=f"文件已更新: {fname}",
                            body=path,
                            priority=0,
                        ))
                    elif evt_type == "deleted":
                        events.append(ProactiveEvent(
                            type=ProactiveEventType.ALERT,
                            title=f"文件已删除: {fname}",
                            body=f"{fdir}/（原文件: {fname}）",
                            priority=0,
                        ))
                    elif evt_type == "moved":
                        events.append(ProactiveEvent(
                            type=ProactiveEventType.INSIGHT,
                            title=f"文件已移动: {fname}",
                            body=f"新位置: {path}",
                            priority=0,
                        ))

                self._pending.clear()

            if events and self._callback:
                for evt in events:
                    self._callback(evt)

else:
    FSEventMonitor = None  # watchdog 不可用时设为 None，调用方自动回退


# ═══════════════════════════════════════════
# 项目健康度监控
# ═══════════════════════════════════════════

class ProjectHealthMonitor(BaseMonitor):
    """
    项目健康度监控器

    检查项目中的常见问题:
      - __pycache__ 膨胀（>50MB）
    """

    def __init__(self, project_path: str = "", interval_seconds: float = 300.0):
        super().__init__(interval_seconds, "ProjectHealthMonitor")
        self.project_path = project_path

    def set_project(self, path: str):
        self.project_path = path

    def _check(self) -> List[ProactiveEvent]:
        events = []
        if not self.project_path or not os.path.isdir(self.project_path):
            return events

        # 检查 __pycache__ 膨胀
        pycache_size = 0
        pycache_count = 0
        for root, dirs, files in os.walk(self.project_path):
            if "__pycache__" in root:
                for f in files:
                    try:
                        fp = os.path.join(root, f)
                        pycache_size += os.path.getsize(fp)
                        pycache_count += 1
                    except OSError:
                        pass

        if pycache_size > 50 * 1024 * 1024:  # 50MB
            events.append(ProactiveEvent(
                type=ProactiveEventType.INSIGHT,
                title=f"__pycache__ 膨胀: {pycache_size / 1024 / 1024:.0f}MB",
                body=f"共 {pycache_count} 个 .pyc 文件，建议 `py3clean .` 清理",
                action_label="清理缓存",
                action_payload={"action": "clean_pycache", "path": self.project_path},
                priority=0,
            ))

        return events

```
