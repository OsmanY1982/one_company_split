# `iqra/core/agent_loop.py`

> 路径：`iqra/core/agent_loop.py` | 行数：1060


---


```python
import logging

logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-
"""
AgentLoop — 自主 Agent 执行循环 (对标 Codex / Claude Code)

在 ChatEngine 的工具调用循环之上叠加 Think → Plan → Act → Observe → Reflect
自主执行模式，支持多步推理、错误恢复、进度追踪和可中断执行。

与 ChatEngine 的关系：
  - AgentLoop 是 ChatEngine 的上层封装，复用其工具注册表和 LLM 后端
  - AgentLoop 可直接替换 ChatEngine 用于需要自主多步执行的场景
  - ChatEngine 保留用于简单单轮问答

用法:
    from iqra.core.agent_loop import AgentLoop
    from iqra.core.chat_engine import ChatEngine

    engine = ChatEngine(backend=..., registry=..., ...)
    agent = AgentLoop(engine)

    # 同步执行
    result = agent.run("帮我重构 src/ 下所有 Python 文件的 import 语句")

    # 流式执行
    for event in agent.run_stream("排查为什么 API 返回 500"):
        print(event)

    # 取消执行
    agent.cancel()

特性:
  - Think-Plan-Act-Observe-Reflect 五阶段 ReAct 循环
  - 自动错误恢复（最多 3 次重试，每次尝试不同策略）
  - 进度事件流（每一步都有回调）
  - 可中断（cancel() 方法）
  - 可配置最大迭代、超时
"""

import json
import os
import time
import signal
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Iterator, Callable, List, Dict, Any, Tuple, Set
from PyQt5.QtCore import QObject, pyqtSignal

from .chat_engine import ChatEngine
from .iqra_logging import logger
from .rag_context import RAGContextInjector
from .proactive_engine import SuggestionEngine
from .verification_hook import VerificationHook, ReviewResult, format_findings_context


# ═══════════════════════════════════════════
# 事件类型
# ═══════════════════════════════════════════

class AgentEventType(Enum):
    THINK = auto()       # 分析需求
    PLAN = auto()        # 生成计划
    ACT = auto()         # 执行工具
    OBSERVE = auto()     # 观察结果
    REFLECT = auto()     # 反思调整
    COMPLETE = auto()    # 任务完成
    ERROR = auto()       # 错误
    CANCELLED = auto()   # 被取消
    PROGRESS = auto()    # 进度更新


@dataclass
class AgentEvent:
    """Agent 执行过程中的事件"""
    type: AgentEventType
    step: int = 0                     # 当前步数
    total_steps: int = 0              # 预计总步数（PLAN 时设定）
    message: str = ""                 # 事件描述
    data: Dict[str, Any] = field(default_factory=dict)  # 附加数据
    timestamp: float = field(default_factory=time.time)


@dataclass
class AgentResult:
    """Agent 执行结果"""
    success: bool
    summary: str                      # 自然语言总结
    steps_taken: int                  # 实际执行步数
    tools_called: List[str]           # 调用过的工具名列表
    errors: List[str]                 # 遇到的错误
    events: List[AgentEvent]          # 完整事件日志
    duration_seconds: float           # 执行耗时


# ═══════════════════════════════════════════
# Agent 系统提示词
# ═══════════════════════════════════════════

AGENT_SYSTEM_PROMPT = """你处于自主 Agent 执行模式，能独立完成多步骤复杂任务。

## 工具选择铁律（硬性约束，违反导致低效/错误）

1. **读文件** → 只用 read_file，严禁 execute_shell cat/more/head/tail/osascript
2. **搜文件** → 只用 search_files（或 list_directory+匹配），严禁 execute_shell find/grep/mdfind/ls
3. **写文件** → 只用 write_file/edit_file，严禁 execute_shell + echo/printf/tee 重定向
4. **执行命令** → 只用 execute_shell，严禁 osascript/open/xdg-open
5. **禁止串行等待**：多个无依赖的独立操作（如读多个文件、搜多个关键词）必须同轮并行发起，严禁逐个串行等待
6. **文件定位优先级**：用户给出的路径 > /Volumes/D盘工作区/ 根目录 > 当前打开的项目根目录 > ~/用户主目录

## AI 设计规范铁律（代码修改场景）

1. **禁止擅自备份/恢复/同步**：不主动执行 gen_book.py、rsync、git push、回滚等。代码改完停在自检环节，等用户下令
2. **改动前全局搜索引用**：改任何函数/类/变量前，先 search_files 搜索全项目所有引用方，穷举隐藏依赖
3. **修复后自行验证**：改完代码要验证修复是否真正解决原问题，并检查同模块是否有同类问题；避免改完即止
4. **排查前查项目全书**：先看项目全书卷宗了解架构和文件关系，再动手修改；禁止靠 grep 猜测模块位置
5. **快速定位直接修改**：定位核心问题后直接动手改代码，避免冗长解释或反复确认

## 执行模式：Think → Plan → Act → Observe → Reflect

1. **THINK（分析）**：理解需求，识别所需信息和潜在障碍。优先确定文件/路径是否存在
2. **PLAN（规划）**：拆解为原子步骤，优先完成搜索定位再操作。同一轮的独立操作标记为可并行
3. **ACT（执行）**：调用工具执行。每次 LLM 响应中的多个独立 tool_call 会并行执行以加速
4. **OBSERVE（观察）**：检查工具结果。成功→继续下一步；失败→分析原因，切换替代策略
5. **REFLECT（反思）**：判断任务是否完成。未完成则基于当前状态调整计划继续，不重复已完成的查询

## 关键执行规则

- **错误不盲重试**：同一工具同一参数最多重试 2 次，之后必须切换策略（换参数/换工具/降级方案）
- **并行优先**：同轮内无依赖的多个读取/搜索操作必须并行，严禁逐个等待
- **搜索结果驱动**：文件操作前先搜索确定路径，不凭猜测指定路径
- **完成后简洁总结**：任务完成用中文汇报完成内容和关键结果"""


# ═══════════════════════════════════════════
# 分层错误恢复策略
# ═══════════════════════════════════════════

# 工具降级映射：工具失败时尝试的替代方案
TOOL_FALLBACK_MAP: Dict[str, List[Tuple[str, Callable[[dict], dict]]]] = {
    # read_file 失败 → 尝试 execute_shell cat（系统级兜底）
    "read_file": [
        ("execute_shell", lambda args: {
            "command": f"cat {args.get('file_path', '')}",
            "description": f"降级读取: {args.get('file_path', '')}",
        }),
    ],
    # search_files 失败 → 尝试 execute_shell find 或 mdfind
    "search_files": [
        ("execute_shell", lambda args: {
            "command": (
                f"find {args.get('root_path', '.')} "
                f"-name '*{args.get('query', '*')}*' "
                f"2>/dev/null | head -50"
            ),
            "description": "降级搜索: find",
        }),
    ],
    "list_directory": [
        ("execute_shell", lambda args: {
            "command": f"ls -la {args.get('path', '.')}",
            "description": "降级列目录",
        }),
    ],
}


# ═══════════════════════════════════════════
# AgentLoop 主类
# ═══════════════════════════════════════════

class AgentLoop(QObject):
    """
    自主 Agent 执行循环

    信号:
      on_event: 每一步发出事件（THINK/PLAN/ACT/OBSERVE/REFLECT/COMPLETE/ERROR/CANCELLED）
      on_progress: 进度百分比更新 (0-100)
      on_tool_start: 工具开始执行（兼容 ChatEngine 信号）
      on_tool_result: 工具执行结果（兼容 ChatEngine 信号）
    """

    on_event = pyqtSignal(AgentEvent)
    on_progress = pyqtSignal(int)
    on_tool_start = pyqtSignal(str, dict)
    on_tool_result = pyqtSignal(str, bool, str)
    on_suggestion = pyqtSignal(str, str)  # (title, body) — 任务完成后的下一步建议

    # 默认配置
    DEFAULT_MAX_ITERATIONS = 50
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_TIMEOUT_SECONDS = 600  # 10 分钟
    DEFAULT_TOOL_TIMEOUT_SECONDS = 120  # 单个工具执行超时（秒）

    # 类级单线程池：用于工具超时控制（所有 AgentLoop 实例共享）
    _tool_executor: Optional[ThreadPoolExecutor] = None

    @classmethod
    def _get_tool_executor(cls) -> ThreadPoolExecutor:
        if cls._tool_executor is None:
            cls._tool_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="tool-")
        return cls._tool_executor

    def __init__(
        self,
        engine: ChatEngine,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        verbose: bool = True,
    ):
        """
        Args:
            engine: ChatEngine 实例（已配置后端和工具）
            max_iterations: 最大迭代次数（超过后强制终止）
            max_retries: 单个操作的最大重试次数
            timeout_seconds: 总执行超时（秒）
            verbose: 是否发出详细事件
        """
        super().__init__()
        self._engine = engine
        self._max_iterations = max_iterations
        self._max_retries = max_retries
        self._timeout_seconds = timeout_seconds
        self._verbose = verbose

        self._cancelled = False
        self._events: List[AgentEvent] = []
        self._tools_called: List[str] = []
        self._errors: List[str] = []
        self._start_time: float = 0.0
        self._current_step = 0
        self._total_steps = 0
        self._running_pids: Set[int] = set()  # 正在执行工具的进程 PID
        self._tool_timeout = self.DEFAULT_TOOL_TIMEOUT_SECONDS

        # 保存原始 system prompt，以便注入 Agent 指令后恢复
        self._original_system_prompt = ""

        # RAG 上下文注入器（单例）
        self._rag_injector = RAGContextInjector()

        # 智能建议生成器（任务完成后生成下一步建议）
        self._suggester: Optional[SuggestionEngine] = None

        # 执行后自检钩子（工具调用完成后、COMPLETE 前触发）
        self._verification: Optional[VerificationHook] = None

        # 转发内部 engine 的信号到 AgentLoop 自身信号
        self._engine.on_tool_start.connect(self.on_tool_start.emit)
        self._engine.on_tool_result.connect(self.on_tool_result.emit)

    # ── 公开接口 ──

    def enable_suggestions(self, backend):
        """启用智能建议：传入 BaseLLMBackend 实例"""
        self._suggester = SuggestionEngine(backend)

    def disable_suggestions(self):
        """关闭智能建议"""
        self._suggester = None

    def enable_verification(self):
        """启用执行后自检：Agent 完成工具调用后自动审查操作正确性"""
        if self._engine and hasattr(self._engine, "backend"):
            self._verification = VerificationHook(
                chat_fn=self._engine.backend.chat,
                enabled=True,
            )

    def disable_verification(self):
        """关闭执行后自检"""
        self._verification = None

    def _emit_suggestions(self, user_message: str, completion_text: str):
        """生成并发射下一步建议"""
        if not self._suggester:
            return
        suggestions = self._suggester.generate(
            user_message=user_message,
            completion_summary=completion_text,
        )
        for s in suggestions:
            self.on_suggestion.emit(s.get("title", ""), s.get("body", ""))

    def run(self, user_message: str) -> AgentResult:
        """
        同步执行任务

        Args:
            user_message: 用户的任务描述

        Returns:
            AgentResult: 包含成功状态、总结、事件日志等
        """
        self._reset()
        self._start_time = time.time()

        try:
            self._inject_agent_prompt()
            result = self._execute_loop(user_message)
        finally:
            self._restore_system_prompt()

        elapsed = time.time() - self._start_time
        return AgentResult(
            success=result.get("success", False),
            summary=result.get("summary", ""),
            steps_taken=self._current_step,
            tools_called=self._tools_called,
            errors=self._errors,
            events=self._events,
            duration_seconds=elapsed,
        )

    def run_stream(self, user_message: str) -> Iterator[AgentEvent]:
        """
        流式执行任务（生成器），每步 yield 事件

        Usage:
            for event in agent.run_stream("排查 API 报错"):
                if event.type == AgentEventType.COMPLETE:
                    print(event.message)
        """
        self._reset()
        self._start_time = time.time()

        try:
            self._inject_agent_prompt()
            for event in self._execute_loop_stream(user_message):
                yield event
        finally:
            self._restore_system_prompt()

    def cancel(self) -> None:
        """取消当前执行（含强制终止正在运行的工具进程）"""
        self._cancelled = True
        self._terminate_running_tools()
        event = AgentEvent(
            type=AgentEventType.CANCELLED,
            step=self._current_step,
            message="执行已被用户取消",
        )
        self._events.append(event)
        self.on_event.emit(event)
        logger.info("AgentLoop 被用户取消（已终止 %d 个子进程）", len(self._running_pids))

    # ── 内部方法 ──

    def _reset(self) -> None:
        self._cancelled = False
        self._events = []
        self._tools_called = []
        self._errors = []
        self._current_step = 0
        self._total_steps = 0

    def _inject_agent_prompt(self) -> None:
        """注入 Agent 系统提示词到 engine 的消息列表头部"""
        msgs = self._engine.messages
        self._original_system_prompt = ""

        # 替换已有的 system 消息（如果存在）为 Agent 增强版
        for i, msg in enumerate(msgs):
            if msg.get("role") == "system":
                self._original_system_prompt = msg["content"]
                msgs[i] = {
                    "role": "system",
                    "content": self._original_system_prompt + "\n\n" + AGENT_SYSTEM_PROMPT,
                }
                return

        # 没有 system 消息，插入到头部
        msgs.insert(0, {"role": "system", "content": AGENT_SYSTEM_PROMPT})

    def _restore_system_prompt(self) -> None:
        """恢复原始 system prompt"""
        msgs = self._engine.messages
        if not msgs or msgs[0].get("role") != "system":
            return

        if self._original_system_prompt:
            msgs[0]["content"] = self._original_system_prompt
        else:
            # 没有原始 prompt，说明是我们新插入的 → 移除
            msgs.pop(0)

    def _emit(self, event_type: AgentEventType, message: str, data: dict = None) -> None:
        """发出事件"""
        event = AgentEvent(
            type=event_type,
            step=self._current_step,
            total_steps=self._total_steps,
            message=message,
            data=data or {},
        )
        self._events.append(event)
        if self._verbose:
            self.on_event.emit(event)

        # 进度估算
        if self._total_steps > 0:
            progress = min(int(self._current_step / self._total_steps * 100), 99)
            self.on_progress.emit(progress)

    def _check_timeout(self) -> bool:
        """检查是否超时"""
        if self._timeout_seconds <= 0:
            return False
        elapsed = time.time() - self._start_time
        return elapsed > self._timeout_seconds

    def _inject_rag_context(self, user_message: str) -> str:
        """
        通过 RAGContextInjector 注入相关工作区上下文

        在每次 _tool_loop 迭代前调用，自动注入项目全书、设计规范等
        相关文件内容到用户消息中，减少 LLM 盲猜和重复文件读取。

        Returns:
            注入上下文后的消息（可能在原消息前添加了 <workspace_context> 块）
        """
        try:
            # 只在 injector 已有项目配置时才注入
            if not self._rag_injector.has_project:
                return user_message
            return self._rag_injector.inject_context(user_message)
        except Exception as e:
            logger.debug("RAG 上下文注入跳过: %s", e)
            return user_message

    def _execute_one_tool(self, tc) -> dict:
        """
        执行单个工具调用（含缓存 + 分层错误恢复 + 超时），线程安全

        分层恢复策略:
          L1: 缓存命中 → 直接返回（跳过执行）
          L2: 首次执行失败 → 重试同参数（最多 max_retries 次）
              每轮执行包在 threading.Timer 超时控制中（默认120s）
          L3: 重试耗尽 → 尝试降级工具（TOOL_FALLBACK_MAP）
          L4: 降级也失败 → 返回错误，记录到 _errors

        取消/中断: 每轮重试前检查 _cancelled，超时或取消时强制终止工具进程。
        """
        # L1: 缓存检查（下沉到 ToolRegistry.execute() 类级共享缓存）
        retry_count = 0
        last_error = None
        while retry_count <= self._max_retries:
            # ── 取消检查 ──
            if self._cancelled:
                self._emit(AgentEventType.CANCELLED,
                           f"⏹️ 工具 {tc.name} 被用户取消")
                return {"success": False, "error": "用户取消执行", "cancelled": True}

            try:
                self._engine.on_tool_start.emit(tc.name, tc.arguments)
                result = self._execute_with_timeout(tc)
                success = result.get("success", False)
                self._engine.on_tool_result.emit(
                    tc.name, success,
                    str(result.get("result", result.get("error", "")))[:200],
                )
                if success:
                    return result
            except TimeoutError:
                last_error = TimeoutError(
                    f"{tc.name} 执行超时（>{self._tool_timeout}s），已强制终止"
                )
                self._terminate_running_tools()
                self._emit(AgentEventType.OBSERVE,
                           f"⏰ {tc.name} 执行超时（>{self._tool_timeout}s），已终止子进程")
            except Exception as e:
                last_error = e
                self._terminate_running_tools()

            retry_count += 1
            if retry_count <= self._max_retries:
                # 超时重试需更长的退避
                backoff = 0.5 * retry_count if not isinstance(last_error, TimeoutError) else 2.0 * retry_count
                self._emit(AgentEventType.OBSERVE,
                           f"{tc.name} 失败，重试 {retry_count}/{self._max_retries}: {last_error}")
                time.sleep(backoff)

        # L3: 降级策略
        fallbacks = TOOL_FALLBACK_MAP.get(tc.name, [])
        if fallbacks:
            self._emit(AgentEventType.OBSERVE,
                       f"{tc.name} 重试耗尽，尝试降级方案...")
            for fallback_name, arg_transformer in fallbacks:
                # 降级前检查取消
                if self._cancelled:
                    return {"success": False, "error": "用户取消执行", "cancelled": True}
                try:
                    fallback_args = arg_transformer(tc.arguments)
                    from .tool_registry import ToolCall as TC
                    fallback_tc = TC(fallback_name, fallback_args)
                    self._engine.on_tool_start.emit(fallback_name, fallback_args)
                    result = self._execute_with_timeout(fallback_tc)
                    self._engine.on_tool_result.emit(
                        fallback_name, result.get("success", False),
                        str(result.get("result", result.get("error", "")))[:200],
                    )
                    self._emit(AgentEventType.OBSERVE,
                               f"⬇️ 降级成功: {tc.name} → {fallback_name}")
                    return result
                except Exception as fe:
                    logger.warning("降级也失败 (%s → %s): %s", tc.name, fallback_name, fe)
                    self._terminate_running_tools()

        # L4: 全部失败
        error_msg = (
            f"工具 {tc.name} 执行失败（已重试 {self._max_retries} 次"
            + ("，降级方案也失败" if fallbacks else "")
            + f"）: {last_error}"
        )
        self._errors.append(error_msg)
        self._emit(AgentEventType.ERROR, error_msg)
        return {"success": False, "error": error_msg}

    def _execute_with_timeout(self, tc) -> dict:
        """在独立线程中执行工具，带超时控制。超时时触发 _terminate_running_tools()。

        线程安全：registry 内部保证线程安全；这里用 ThreadPoolExecutor
        提交一个 task，future.result(timeout) 实现超时。
        """
        executor = self._get_tool_executor()

        def _run_with_pid_tracking():
            """在线程内执行工具，同时跟踪可能产生的子进程 PID"""
            # 保存线程 ID 以便超时时关联子进程
            self._tool_thread_id = threading.get_ident()
            return self._engine.registry.execute(tc)

        future = executor.submit(_run_with_pid_tracking)
        try:
            return future.result(timeout=self._tool_timeout)
        except FutureTimeoutError:
            # 超时：尝试取消 future，并终止相关子进程
            future.cancel()
            self._terminate_running_tools()
            raise TimeoutError(
                f"工具 {tc.name} 执行超时（>{self._tool_timeout}s）"
            )

    def _terminate_running_tools(self):
        """强制终止正在执行的工具子进程（通过扫描当前线程的子孙进程）"""
        import subprocess
        killed = 0
        # 方案 A：尝试通过已注册的 PID 终止
        for pid in list(self._running_pids):
            try:
                os.kill(pid, signal.SIGTERM)
                killed += 1
            except (ProcessLookupError, PermissionError):
                logger.exception("异常详情")
        self._running_pids.clear()

        # 方案 B：通过 ps 找当前工具线程的子孙 shell 进程兜底
        if hasattr(self, '_tool_thread_id'):
            parent_pid = os.getpid()
            try:
                cp = subprocess.run(
                    ["pgrep", "-P", str(parent_pid)],
                    capture_output=True, text=True, timeout=2
                )
                if cp.returncode == 0 and cp.stdout.strip():
                    for child_pid_str in cp.stdout.strip().split():
                        try:
                            os.kill(int(child_pid_str), signal.SIGTERM)
                            killed += 1
                        except (ProcessLookupError, PermissionError):
                            logger.exception("异常详情")
            except Exception:
                logger.exception("异常详情")
            # 如果 SIGTERM 不够，延迟一点再 SIGKILL
            if killed > 0:
                time.sleep(0.3)
                for pid in list(self._running_pids):
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except Exception:
                        logger.exception("异常详情")

        if killed > 0:
            logger.info("已终止 %d 个工具子进程", killed)

    def _execute_loop(self, user_message: str) -> dict:
        """核心执行循环（同步版）"""
        # 先让 LLM 分析并生成计划（单轮）
        self._emit(AgentEventType.THINK, f"分析任务: {user_message[:100]}...")

        # RAG 上下文注入
        augmented_message = self._inject_rag_context(user_message)

        # 直接将用户消息发给 engine（engine 会自动追加到 messages）
        response = self._engine.backend.chat(
            self._engine.messages + [{"role": "user", "content": augmented_message}],
            self._engine.registry.to_openai_tools() if self._engine.registry.count() > 0 else None,
        )

        # 处理首轮响应
        if response.content and not response.tool_calls:
            # LLM 直接给出文本回复 → 简单任务，无需多步
            self._current_step = 1
            self._emit(AgentEventType.COMPLETE, response.content)
            self._emit_suggestions(user_message, response.content)
            self.on_progress.emit(100)
            return {"success": True, "summary": response.content}

        # 有工具调用 → 进入多步循环
        self._total_steps = self._max_iterations
        self._emit(AgentEventType.PLAN, f"开始执行，最多 {self._max_iterations} 步")

        return self._tool_loop(user_message)

    def _execute_loop_stream(self, user_message: str) -> Iterator[AgentEvent]:
        """核心执行循环（流式版）"""
        event = AgentEvent(AgentEventType.THINK, 0, 0, f"分析任务: {user_message[:100]}...")
        self._events.append(event)
        yield event

        augmented_message = self._inject_rag_context(user_message)

        response = self._engine.backend.chat(
            self._engine.messages + [{"role": "user", "content": augmented_message}],
            self._engine.registry.to_openai_tools() if self._engine.registry.count() > 0 else None,
        )

        if response.content and not response.tool_calls:
            self._current_step = 1
            event = AgentEvent(AgentEventType.COMPLETE, 1, 1, response.content)
            self._events.append(event)
            yield event
            self._emit_suggestions(user_message, response.content)
            yield from []  # end generator
            return

        self._total_steps = self._max_iterations
        event = AgentEvent(AgentEventType.PLAN, 0, self._max_iterations,
                          f"开始执行，最多 {self._max_iterations} 步")
        self._events.append(event)
        yield event

        yield from self._tool_loop_stream(user_message)

    def _tool_loop(self, user_message: str) -> dict:
        """工具调用循环（同步版）"""
        # 使用 engine 的 chat 方法（它会自动处理多轮工具调用）
        # 但我们需要在每一轮之间插入观察和反思
        augmented_message = self._inject_rag_context(user_message)
        self._engine.messages.append({"role": "user", "content": augmented_message})
        self._engine._trim_context()

        tools = self._engine.registry.to_openai_tools() if self._engine.registry.count() > 0 else None

        for iteration in range(self._max_iterations):
            if self._cancelled:
                return {"success": False, "summary": "执行被取消"}

            if self._check_timeout():
                self._emit(AgentEventType.ERROR, f"执行超时（{self._timeout_seconds} 秒）")
                return {"success": False, "summary": f"超时: 已执行 {self._current_step} 步"}

            self._current_step = iteration + 1

            # ACT 阶段
            try:
                response = self._engine.backend.chat(self._engine.messages, tools)
            except Exception as e:
                error_msg = f"LLM 调用失败: {e}"
                self._errors.append(error_msg)
                self._emit(AgentEventType.ERROR, error_msg)
                # 尝试重试
                if iteration < self._max_retries:
                    time.sleep(1)
                    continue
                return {"success": False, "summary": error_msg}

            # 无工具调用 → 任务完成
            if not response.tool_calls:
                content = response.content or ""
                self._engine.messages.append({"role": "assistant", "content": content})
                self._emit(AgentEventType.REFLECT, "任务完成")

                # 执行后自检（在 COMPLETE 前）
                self._run_verification()

                self._emit(AgentEventType.COMPLETE, content)
                self._emit_suggestions(user_message, content)
                self.on_progress.emit(100)
                return {"success": True, "summary": content}

            # 处理工具调用 — 并行执行独立调用
            assistant_msg = {"role": "assistant", "content": None, "tool_calls": []}
            tool_count = len(response.tool_calls)

            if tool_count == 1:
                # 单工具调用：走原有串行逻辑（含重试）
                tc = response.tool_calls[0]
                self._tools_called.append(tc.name)
                self._emit(AgentEventType.ACT, f"调用工具: {tc.name}",
                          {"tool": tc.name, "args": tc.arguments})
                result = self._execute_one_tool(tc)
                success = result.get("success", False)
                output = str(result.get("result", result.get("error", "")))[:500]
                self._emit(AgentEventType.OBSERVE,
                          f"{'✅' if success else '❌'} {tc.name}: {output[:200]}",
                          {"tool": tc.name, "success": success, "output": output})
                assistant_msg["tool_calls"].append({
                    "id": tc.id, "type": "function",
                    "function": {"name": tc.name,
                                "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
                })
                self._engine.messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
            else:
                # 多工具调用：并行执行
                self._emit(AgentEventType.ACT,
                          f"并行调用 {tool_count} 个工具: "
                          f"{', '.join(tc.name for tc in response.tool_calls)}",
                          {"parallel": True, "count": tool_count})

                # 并行提交所有工具调用
                futures = {}
                future_to_idx = {}  # future → (tc, index) 保持顺序
                with ThreadPoolExecutor(max_workers=min(tool_count, 8)) as pool:
                    for idx, tc in enumerate(response.tool_calls):
                        self._tools_called.append(tc.name)
                        f = pool.submit(self._execute_one_tool, tc)
                        futures[f] = tc
                        future_to_idx[f] = idx

                    # 收集结果（按完成顺序处理事件，但按原始顺序构建消息）
                    idx_results = {}  # index → result
                    for future in as_completed(futures):
                        tc = futures[future]
                        idx = future_to_idx[future]
                        try:
                            result = future.result()
                        except Exception as e:
                            result = {"success": False, "error": str(e)}
                            self._errors.append(f"{tc.name}: {e}")
                            self._emit(AgentEventType.ERROR, f"{tc.name} 并行执行异常: {e}")
                        idx_results[idx] = (tc, result)
                        success = result.get("success", False)
                        output = str(result.get("result", result.get("error", "")))[:500]
                        self._emit(AgentEventType.OBSERVE,
                                  f"{'✅' if success else '❌'} {tc.name}: {output[:200]}",
                                  {"tool": tc.name, "success": success, "output": output})

                # 按原始顺序构建消息（确保 LLM 能正确匹配 tool_call_id）
                for idx, tc in enumerate(response.tool_calls):
                    assistant_msg["tool_calls"].append({
                        "id": tc.id, "type": "function",
                        "function": {"name": tc.name,
                                    "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
                    })
                    # 追加对应的 tool 结果消息
                    tc_and_result = idx_results.get(idx, (tc, {"success": False, "error": "执行结果缺失"}))
                    _, result = tc_and_result
                    self._engine.messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })

            self._engine.messages.append(assistant_msg)

        # 达到最大迭代
        self._emit(AgentEventType.ERROR,
                  f"达到最大迭代次数 {self._max_iterations}，任务可能未完成")
        return {"success": False,
                "summary": f"达到最大迭代次数 ({self._max_iterations} 步)。"
                          f"已调用工具: {', '.join(self._tools_called)}"}

    def _tool_loop_stream(self, user_message: str) -> Iterator[AgentEvent]:
        """工具调用循环（流式版）"""
        augmented_message = self._inject_rag_context(user_message)
        self._engine.messages.append({"role": "user", "content": augmented_message})
        self._engine._trim_context()

        tools = self._engine.registry.to_openai_tools() if self._engine.registry.count() > 0 else None

        for iteration in range(self._max_iterations):
            if self._cancelled:
                event = AgentEvent(AgentEventType.CANCELLED, self._current_step, self._total_steps, "执行被取消")
                self._events.append(event)
                yield event
                return

            if self._check_timeout():
                event = AgentEvent(AgentEventType.ERROR, self._current_step, self._total_steps,
                                  f"执行超时（{self._timeout_seconds} 秒）")
                self._events.append(event)
                yield event
                return

            self._current_step = iteration + 1

            try:
                response = self._engine.backend.chat(self._engine.messages, tools)
            except Exception as e:
                error_msg = f"LLM 调用失败: {e}"
                self._errors.append(error_msg)
                event = AgentEvent(AgentEventType.ERROR, self._current_step, self._total_steps, error_msg)
                self._events.append(event)
                yield event
                if iteration < self._max_retries:
                    time.sleep(1)
                    continue
                return

            if not response.tool_calls:
                content = response.content or ""
                self._engine.messages.append({"role": "assistant", "content": content})
                event = AgentEvent(AgentEventType.REFLECT, self._current_step, self._total_steps, "任务完成")
                self._events.append(event)
                yield event

                # 执行后自检（在 COMPLETE 前）
                self._run_verification()

                event = AgentEvent(AgentEventType.COMPLETE, self._current_step, self._total_steps, content)
                self._events.append(event)
                yield event
                self._emit_suggestions(user_message, content)
                return

            assistant_msg = {"role": "assistant", "content": None, "tool_calls": []}
            for tc in response.tool_calls:
                self._tools_called.append(tc.name)
                tool_data = {"tool": tc.name, "args": tc.arguments}
                event = AgentEvent(AgentEventType.ACT, self._current_step, self._total_steps,
                                  f"调用工具: {tc.name}", tool_data)
                self._events.append(event)
                yield event

                result = self._execute_one_tool(tc)

                success = result.get("success", False)
                output = str(result.get("result", result.get("error", "")))[:500]
                event = AgentEvent(AgentEventType.OBSERVE, self._current_step, self._total_steps,
                                  f"{'✅' if success else '❌'} {tc.name}: {output[:200]}",
                                  {"tool": tc.name, "success": success, "output": output})
                self._events.append(event)
                yield event

                assistant_msg["tool_calls"].append({
                    "id": tc.id, "type": "function",
                    "function": {"name": tc.name,
                                "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
                })
                self._engine.messages.append({
                    "role": "tool", "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })

            self._engine.messages.append(assistant_msg)

        event = AgentEvent(AgentEventType.ERROR, self._current_step, self._total_steps,
                          f"达到最大迭代次数 {self._max_iterations}")
        self._events.append(event)
        yield event

    # ── ChatEngine 兼容接口 ──

    def chat_stream(self, user_message: str) -> Iterator[str]:
        """
        与 ChatEngine.chat_stream 完全兼容的流式接口。
        ChatWorker 可以直接使用 AgentLoop 替代 ChatEngine。

        Yields:
            str: 每个事件或工具结果的描述字符串
        """
        self._reset()
        self._start_time = time.time()

        try:
            self._inject_agent_prompt()

            # 使用 engine 的 chat_stream 驱动多轮调用
            augmented_message = self._inject_rag_context(user_message)
            self._engine.messages.append({"role": "user", "content": augmented_message})
            self._engine._trim_context()

            tools = self._engine.registry.to_openai_tools() if self._engine.registry.count() > 0 else None

            for iteration in range(self._max_iterations):
                if self._cancelled:
                    yield "\n\n[执行已被取消]"
                    return

                if self._check_timeout():
                    yield f"\n\n[执行超时（{self._timeout_seconds} 秒），已执行 {self._current_step} 步]"
                    return

                self._current_step = iteration + 1

                try:
                    response = self._engine.backend.chat(self._engine.messages, tools)
                except Exception as e:
                    error_msg = f"\n\n[LLM 调用失败: {e}]"
                    self._errors.append(error_msg)
                    yield error_msg
                    if iteration < self._max_retries:
                        time.sleep(1)
                        continue
                    return

                # 无工具调用 → 任务完成
                if not response.tool_calls:
                    content = response.content or ""
                    self._engine.messages.append({"role": "assistant", "content": content})
                    yield content
                    return

                # 处理工具调用
                assistant_msg = {"role": "assistant", "content": None, "tool_calls": []}
                for tc in response.tool_calls:
                    self._tools_called.append(tc.name)
                    yield f"\n\n🔧 调用工具: {tc.name}..."

                    retry_count = 0
                    while retry_count <= self._max_retries:
                        try:
                            self._engine.on_tool_start.emit(tc.name, tc.arguments)
                            result = self._engine.registry.execute(tc)
                            self._engine.on_tool_result.emit(
                                tc.name, result.get("success", False),
                                str(result.get("result", result.get("error", "")))[:200],
                            )
                            break
                        except Exception as e:
                            retry_count += 1
                            if retry_count > self._max_retries:
                                error_msg = f"  ❌ {tc.name} 失败: {e}"
                                self._errors.append(error_msg)
                                result = {"success": False, "error": str(e)}
                                yield error_msg
                                break
                            yield f"  ⚠️ 重试 {retry_count}/{self._max_retries}..."
                            time.sleep(0.5)

                    success = result.get("success", False)
                    output = str(result.get("result", result.get("error", "")))[:300]
                    yield f"\n{'✅' if success else '❌'} {tc.name}: {output}"

                    assistant_msg["tool_calls"].append({
                        "id": tc.id, "type": "function",
                        "function": {"name": tc.name,
                                    "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
                    })
                    self._engine.messages.append({
                        "role": "tool", "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })

                self._engine.messages.append(assistant_msg)

            yield f"\n\n[达到最大迭代次数 {self._max_iterations}，任务可能未完成]"
        finally:
            self._restore_system_prompt()

    def _run_verification(self) -> None:
        """执行后自检：调用 VerificationHook 审查本轮工具调用"""
        if not self._verification or not self._verification.enabled:
            return
        if not self._tools_called:
            return

        # 收集工具结果（从 events 中提取）
        tool_results = []
        for ev in self._events:
            if ev.type == AgentEventType.OBSERVE and ev.data:
                tool_results.append({
                    "tool": ev.data.get("tool", ""),
                    "success": ev.data.get("success", False),
                    "output": ev.data.get("output", ""),
                })

        # 获取 user_query（从 messages 第一条 user 消息）
        user_query = ""
        for msg in self._engine.messages:
            if msg.get("role") == "user":
                user_query = msg.get("content", "")[:500]
                break

        result = self._verification.review(
            messages=self._engine.messages,
            tools_called=self._tools_called,
            tool_results=tool_results,
            user_query=user_query,
        )

        if result.findings:
            context = format_findings_context(result.findings)
            self._emit(AgentEventType.OBSERVE,
                      f"自检: {result.verdict} ({len(result.findings)} 项发现)",
                      {"verification_verdict": result.verdict,
                       "verification_summary": result.summary,
                       "verification_findings_count": len(result.findings)})
            logger.info("VerificationHook: verdict=%s, findings=%d, summary=%s",
                       result.verdict, len(result.findings), result.summary)

    # ── ChatEngine 兼容属性与方法 ──

    @property
    def backend(self):
        """兼容 ChatEngine.backend"""
        return self._engine.backend

    @property
    def messages(self):
        return self._engine.messages

    @messages.setter
    def messages(self, value):
        self._engine.messages = value

    def chat(self, user_message: str) -> str:
        """兼容 ChatEngine.chat（同步版）"""
        result = self.run(user_message)
        return result.summary

    def reset(self) -> None:
        if self._engine:
            self._engine.reset()
        self._current_step = 0

    def save(self) -> bool:
        return self._engine.save() if self._engine else False

    def get_history(self) -> list:
        return self._engine.get_history() if self._engine else []

    def message_count(self) -> int:
        return self._engine.message_count() if self._engine else 0

    def inject_context(self, text: str) -> None:
        if self._engine:
            self._engine.inject_context(text)

    def inject_skill(self, skill_name: str) -> bool:
        return self._engine.inject_skill(skill_name) if self._engine else False

    def refresh_skills(self) -> int:
        return self._engine.refresh_skills() if self._engine else 0

    def inject_relevant_skills(self, user_query: str, max_count: int = 5) -> int:
        return self._engine.inject_relevant_skills(user_query, max_count) if self._engine else 0

    def initialize_session(self) -> None:
        if self._engine:
            self._engine.initialize_session()

```
