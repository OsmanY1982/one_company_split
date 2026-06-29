# `iqra/core/_agent_loop_base.py`

> 路径：`iqra/core/_agent_loop_base.py` | 行数：709


---


```python
# -*- coding: utf-8 -*-
"""
AgentLoopBase — Agent 循环基类

包含 __init__、公开接口、内部辅助方法、_execute_loop/_execute_loop_stream。
从 agent_loop.py 拆分出的 QObject 基类层，供 mixin 组合。

v5.4: 增加 AgentDelegate 任务分解入口 — 多步骤复杂任务自动拆+并行
"""

import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Iterator, List, Any

from PyQt5.QtCore import QObject, pyqtSignal

from ._agent_events import AgentEventType, AgentEvent, AgentResult
from ._agent_prompts import AGENT_SYSTEM_PROMPT
from .chat_engine import ChatEngine
from .iqra_logging import logger
from .rag_context import RAGContextInjector
from .proactive_engine import SuggestionEngine

# ── AgentDelegate 复杂度检测配置 ──

COMPLEX_TASK_KEYWORDS = [
    r"多步骤", r"先.*再", r"同时", r"并行", r"然后", r"接着", r"最终",
    r"第一步", r"第二步", r"首先.*其次", r"首先.*然后", r"并且.*同时",
    r"分步", r"先.*后", r"之后", r"接下来", r"以及.*同时",
    r"先.*然后.*最后", r"分阶段", r"逐批",
]
COMPLEX_TASK_LENGTH_THRESHOLD = 200  # 超过此长度的消息视为复杂任务


class AgentLoopBase(QObject):
    """
    自主 Agent 执行循环基类

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
        use_llm_decompose: bool = True,
    ):
        """
        Args:
            engine: ChatEngine 实例（已配置后端和工具）
            max_iterations: 最大迭代次数（超过后强制终止）
            max_retries: 单个操作的最大重试次数
            timeout_seconds: 总执行超时（秒）
            verbose: 是否发出详细事件
            use_llm_decompose: 是否优先使用 LLM 拆解任务（v6.0）
        """
        super().__init__()
        self._engine = engine
        self._max_iterations = max_iterations
        self._max_retries = max_retries
        self._timeout_seconds = timeout_seconds
        self._verbose = verbose
        self._use_llm_decompose = use_llm_decompose

        self._cancelled = False
        self._events: List[AgentEvent] = []
        self._tools_called: List[str] = []
        self._errors: List[str] = []
        self._start_time: float = 0.0
        self._current_step = 0
        self._total_steps = 0
        self._running_pids: set = set()  # 正在执行工具的进程 PID
        self._tool_timeout = self.DEFAULT_TOOL_TIMEOUT_SECONDS

        # 保存原始 system prompt，以便注入 Agent 指令后恢复
        self._original_system_prompt = ""

        # RAG 上下文注入器（单例）
        self._rag_injector = RAGContextInjector()

        # 智能建议生成器（任务完成后生成下一步建议）
        self._suggester: Optional[SuggestionEngine] = None

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

    @property
    def use_llm_decompose(self) -> bool:
        """是否使用 LLM 语义拆解（默认 True）"""
        return self._use_llm_decompose

    @use_llm_decompose.setter
    def use_llm_decompose(self, value: bool):
        """动态切换 LLM 语义拆解开关"""
        self._use_llm_decompose = bool(value)

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

    # ── LLM 任务拆解（v6.0）──

    def _try_llm_decompose(self, user_message: str) -> Optional[dict]:
        """
        使用 TaskDecomposer (LLM 语义拆解) 将任务拆为有序步骤并逐步执行

        与 _try_delegate 的区别：
          - _try_delegate 基于 handler（业务处理器）粒度，适合粗粒度委派
          - _try_llm_decompose 基于 tool（底层工具）粒度，适合精细步骤拆解

        流程:
          TaskDecomposer.decompose() → 逐步执行 → 收集结果

        Returns:
            成功时返回 {"success": bool, "summary": str, "steps": [...]}
            不适用或失败时返回 None（调用方回退到原有流程）
        """
        if not self._use_llm_decompose:
            return None

        try:
            from iqra.core.task_decomposer import TaskDecomposer as LLMTaskDecomposer

            # 获取可用工具 schema
            tool_schemas = []
            try:
                tools = self._engine.registry.to_openai_tools()
                if tools:
                    for t in tools:
                        tool_schemas.append({
                            "name": t.get("function", {}).get("name", ""),
                            "description": t.get("function", {}).get("description", ""),
                            "parameters": t.get("function", {}).get("parameters", {}),
                        })
            except Exception:
                pass

            decomposer = LLMTaskDecomposer(self._engine.backend)
            steps = decomposer.decompose(user_message, available_tools=tool_schemas)

            # 如果只拆出 1 步且是机械回退 → 不适用，交给正常流程
            if not steps or len(steps) <= 1:
                return None

            step_count = len(steps)
            logger.info(
                "TaskDecomposer: LLM 拆解出 %d 步: %s",
                step_count,
                " → ".join(f"{s.tool_name}" for s in steps),
            )

            # 逐步执行
            step_results = []
            all_success = True

            for i, step in enumerate(steps):
                if self._cancelled:
                    return {"success": False, "summary": "执行被取消", "steps": step_results}

                self._current_step = i + 1
                self._tools_called.append(step.tool_name)

                self._emit(
                    AgentEventType.ACT,
                    f"步骤 {step.step_id}/{step_count}: {step.tool_name} — {step.reason}",
                    {"step": step.step_id, "tool": step.tool_name, "args": step.arguments},
                )

                # 构造 ToolCall 并执行
                try:
                    from iqra.core.llm_backend import ToolCall
                    import uuid

                    tc = ToolCall(
                        id=f"decompose_{uuid.uuid4().hex[:8]}",
                        name=step.tool_name,
                        arguments=step.arguments,
                    )
                    result = self._execute_one_tool(tc)
                except Exception as e:
                    result = {"success": False, "error": str(e)}

                success = result.get("success", False)
                output = str(result.get("result", result.get("error", "")))[:500]

                self._emit(
                    AgentEventType.OBSERVE,
                    f"{'OK' if success else 'FAIL'} 步骤 {step.step_id}: {output[:200]}",
                    {"step": step.step_id, "success": success, "output": output},
                )

                step_results.append({
                    "step_id": step.step_id,
                    "tool_name": step.tool_name,
                    "reason": step.reason,
                    "success": success,
                    "result": result,
                    "output": output,
                })

                if not success:
                    all_success = False
                    # 下一步有依赖时停止
                    break

            # 汇总
            summary_parts = []
            for sr in step_results:
                icon = "OK" if sr["success"] else "FAIL"
                summary_parts.append(f"[{icon}] 步骤{sr['step_id']}: {sr['reason']}")

            summary = "\n".join(summary_parts)

            if all_success:
                self._emit(AgentEventType.COMPLETE, summary)
            else:
                self._emit(AgentEventType.REFLECT, f"部分步骤未完成，汇总如下:\n{summary[:200]}")

            self._emit_suggestions(user_message, summary)
            self.on_progress.emit(100)

            return {
                "success": all_success,
                "summary": summary,
                "steps": step_results,
                "decompose_mode": "llm",
            }

        except ImportError as e:
            logger.debug("TaskDecomposer 不可用，跳过: %s", e)
            return None
        except Exception as e:
            logger.warning("LLM 拆解失败，回退到原有流程: %s", e)
            return None

    # ── AgentDelegate 集成（v5.4）──

    def _is_complex_task(self, user_message: str) -> bool:
        """
        检测任务是否为多步骤复杂任务

        判断依据：
          1. 消息长度超过阈值（默认 200 字符）
          2. 包含多步骤关键词（"先A再B"、"同时"、"然后" 等）

        Returns:
            True 如果判断为复杂任务
        """
        if len(user_message) > COMPLEX_TASK_LENGTH_THRESHOLD:
            return True
        for pattern in COMPLEX_TASK_KEYWORDS:
            if re.search(pattern, user_message):
                return True
        return False

    def _try_delegate(self, user_message: str) -> Optional[dict]:
        """
        尝试通过 AgentDelegate 分解并执行复杂任务

        流程:
          TaskDecomposer → DependencyResolver → ParallelExecutor → ResultAggregator

        Returns:
            成功时返回 {"success": bool, "summary": str, "tasks": [...]}
            不适用或失败时返回 None（调用方回退到原有流程）
        """
        if not self._is_complex_task(user_message):
            return None

        try:
            from iqra.core.agent_delegate_adapter import (
                TaskDecomposer, DependencyResolver,
                ParallelExecutor, ResultAggregator,
            )

            decomposer = TaskDecomposer(self._engine.backend)
            subtasks_raw = decomposer.decompose(user_message)

            # 如果只拆出 1 个任务 → 不必走委派，交给正常流程
            if len(subtasks_raw) <= 1:
                return None

            # 依赖解析
            try:
                batches = DependencyResolver.resolve(subtasks_raw)
            except ValueError as e:
                logger.warning("AgentDelegate: 依赖解析失败: %s", e)
                return None

            # 构建通用处理器：每个子任务通过 ChatEngine 执行
            engine_ref = self._engine

            def sub_task_handler(context: str, toolsets: list) -> dict:
                """子任务处理器：调用 ChatEngine 的 LLM + 工具"""
                try:
                    tools = (
                        engine_ref.registry.to_openai_tools()
                        if engine_ref.registry.count() > 0
                        else None
                    )
                    msgs = [
                        {"role": "system", "content": "你是 Iqra 助手。完成以下子任务，直接返回结果。"},
                        {"role": "user", "content": context},
                    ]
                    response = engine_ref.backend.chat(msgs, tools)

                    result_text = response.content or ""

                    # 如果 LLM 返回了工具调用，执行它们
                    if response.tool_calls:
                        for tc in response.tool_calls:
                            try:
                                tool_result = engine_ref.registry.execute(tc)
                                out = str(tool_result.get("result", tool_result.get("error", "")))[:500]
                                result_text += f"\n[{tc.name} 结果]: {out}"
                            except Exception as e:
                                result_text += f"\n[{tc.name} 失败]: {e}"

                    return {"success": True, "result": result_text, "context": context}
                except Exception as e:
                    return {"success": False, "error": str(e), "context": context}

            # 逐批执行
            executor = ParallelExecutor(max_workers=5)
            all_results = []
            for batch_idx, batch in enumerate(batches):
                batch_results = executor.execute(batch, sub_task_handler)
                # 同步子任务 goal 并标注状态
                for j, bt in enumerate(batch):
                    if j < len(batch_results):
                        batch_results[j]["goal"] = bt.get("goal", "")
                        batch_results[j].setdefault(
                            "status",
                            "completed" if batch_results[j].get("success", False) else "failed",
                        )
                all_results.extend(batch_results)

            # 聚合
            aggregator = ResultAggregator(decomposer)
            summary = aggregator.aggregate(user_message, all_results)

            all_success = all(r.get("success", False) for r in all_results)

            logger.info(
                "AgentDelegate: 任务分解完成 — %d 子任务 / %d 批次 / %s",
                len(all_results), len(batches),
                "全部成功" if all_success else "部分失败",
            )

            return {
                "success": all_success,
                "summary": summary,
                "tasks": all_results,
                "batches": len(batches),
            }

        except ImportError as e:
            logger.debug("AgentDelegate 适配层不可用，跳过: %s", e)
            return None
        except Exception as e:
            logger.warning("AgentDelegate 执行失败，回退到原有流程: %s", e)
            return None

    def _execute_loop(self, user_message: str) -> dict:
        """核心执行循环（同步版）"""

        # ── v6.0: LLM 语义拆解（优先级最高）──
        llm_result = self._try_llm_decompose(user_message)
        if llm_result is not None:
            step_count = len(llm_result.get("steps", []))
            self._current_step = step_count
            self._total_steps = step_count
            self._emit(
                AgentEventType.THINK,
                f"LLM 语义拆解为 {step_count} 步: "
                + " → ".join(s.get("tool_name", "?") for s in llm_result.get("steps", [])),
            )
            return {"success": llm_result["success"], "summary": llm_result["summary"]}

        # ── v5.4: 尝试 AgentDelegate 分解复杂任务 ──
        delegate_result = self._try_delegate(user_message)
        if delegate_result is not None:
            task_count = len(delegate_result.get("tasks", []))
            self._emit(
                AgentEventType.THINK,
                f"检测到复杂任务，自动拆分为 {task_count} 个子任务",
            )
            self._current_step = task_count
            self._total_steps = task_count

            summary = delegate_result.get("summary", "")
            success = delegate_result.get("success", False)

            if success:
                self._emit(AgentEventType.COMPLETE, summary)
            else:
                self._emit(AgentEventType.REFLECT, f"部分子任务未完成，汇总如下: {summary[:200]}")

            self._emit_suggestions(user_message, summary)
            self.on_progress.emit(100)
            return {"success": success, "summary": summary}

        # ── 原有流程：LLM 分析并生成计划 ──
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

        # ── v6.0: LLM 语义拆解（优先级最高）──
        llm_result = self._try_llm_decompose(user_message)
        if llm_result is not None:
            step_count = len(llm_result.get("steps", []))
            tool_chain = " → ".join(s.get("tool_name", "?") for s in llm_result.get("steps", []))
            think_event = AgentEvent(
                AgentEventType.THINK, 0, step_count,
                f"LLM 语义拆解为 {step_count} 步: {tool_chain}",
            )
            self._events.append(think_event)
            yield think_event

            self._current_step = step_count
            self._total_steps = step_count

            summary = llm_result.get("summary", "")
            success = llm_result.get("success", False)

            if success:
                event = AgentEvent(AgentEventType.COMPLETE, step_count, step_count, summary)
            else:
                event = AgentEvent(AgentEventType.REFLECT, step_count, step_count,
                                   f"部分步骤未完成，汇总如下: {summary[:200]}")
            self._events.append(event)
            yield event
            self._emit_suggestions(user_message, summary)
            return

        # ── v5.4: 尝试 AgentDelegate 分解复杂任务 ──
        delegate_result = self._try_delegate(user_message)
        if delegate_result is not None:
            task_count = len(delegate_result.get("tasks", []))
            think_event = AgentEvent(
                AgentEventType.THINK, 0, task_count,
                f"检测到复杂任务，自动拆分为 {task_count} 个子任务",
            )
            self._events.append(think_event)
            yield think_event

            self._current_step = task_count
            self._total_steps = task_count

            summary = delegate_result.get("summary", "")
            success = delegate_result.get("success", False)

            if success:
                event = AgentEvent(AgentEventType.COMPLETE, task_count, task_count, summary)
            else:
                event = AgentEvent(AgentEventType.REFLECT, task_count, task_count,
                                   f"部分子任务未完成，汇总如下: {summary[:200]}")
            self._events.append(event)
            yield event
            self._emit_suggestions(user_message, summary)
            return

        # ── 原有流程 ──
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

```
