# `iqra/core/_agent_loop_exec_mixin.py`

> 路径：`iqra/core/_agent_loop_exec_mixin.py` | 行数：399


---


```python
# -*- coding: utf-8 -*-
"""
AgentLoopExecMixin — 工具执行引擎 mixin

包含 _execute_one_tool / _execute_with_timeout / _terminate_running_tools /
_tool_loop / _tool_loop_stream。依赖 AgentLoopBase 提供的 _engine / _emit 等属性。
从 agent_loop.py 拆分。
"""

import json
import os
import time
import signal
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from typing import Iterator

from ._agent_events import AgentEventType, AgentEvent
from ._agent_fallbacks import TOOL_FALLBACK_MAP
from .iqra_logging import logger


class AgentLoopExecMixin:
    """工具执行引擎 — 供 AgentLoop 多重继承使用，不继承任何基类"""

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
        executor = AgentLoopExecMixin._get_tool_executor()

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
                pass
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
                            pass
            except Exception:
                pass
            # 如果 SIGTERM 不够，延迟一点再 SIGKILL
            if killed > 0:
                time.sleep(0.3)
                for pid in list(self._running_pids):
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except Exception:
                        pass

        if killed > 0:
            logger.info("已终止 %d 个工具子进程", killed)

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

    @classmethod
    def _get_tool_executor(cls):
        """委托到 AgentLoopBase 的类级线程池"""
        from ._agent_loop_base import AgentLoopBase
        return AgentLoopBase._get_tool_executor()

```
