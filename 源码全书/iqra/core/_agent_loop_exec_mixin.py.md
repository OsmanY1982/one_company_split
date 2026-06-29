# `iqra/core/_agent_loop_exec_mixin.py`

> 路径：`iqra/core/_agent_loop_exec_mixin.py` | 行数：572


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
from typing import Iterator, Tuple

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

    # ── 卡死检测配置 ──
    STUCK_CONSECUTIVE_THRESHOLD = 3  # 连续 N 轮无进展视为卡死

    def _detect_stuck_progress(self, current_tool_calls: list) -> bool:
        """
        检测 Agent 是否陷入死循环 / 卡死。

        判定条件（任一命中即为卡死）：
          1. 连续 STUCK_CONSECUTIVE_THRESHOLD 轮工具全部返回失败（error）
          2. 连续 STUCK_CONSECUTIVE_THRESHOLD 轮重复调用同一工具
             （相同工具名 + 相同参数 JSON 摘要）

        调用方在检测到卡死后应停止循环并请求用户介入。
        """
        if not hasattr(self, '_stuck_rounds_err'):
            self._stuck_rounds_err = 0
        if not hasattr(self, '_stuck_last_call_signatures'):
            self._stuck_last_call_signatures = []

        tool_names = [tc.name for tc in current_tool_calls]
        if not tool_names:
            # 无工具调用 → 不视为卡死（交给 LLM 自然结束判断）
            self._stuck_rounds_err = 0
            self._stuck_last_call_signatures = []
            return False

        # 条件1：全部工具失败
        all_failed = self._all_last_round_failed if hasattr(self, '_all_last_round_failed') else False

        # 条件2：重复调用检测
        current_sigs = []
        for tc in current_tool_calls:
            try:
                args_str = json.dumps(tc.arguments, ensure_ascii=False, sort_keys=True)
            except Exception:
                args_str = str(tc.arguments)
            current_sigs.append(f"{tc.name}:{args_str}")

        is_duplicate = (
            len(self._stuck_last_call_signatures) > 0
            and sorted(current_sigs) == sorted(self._stuck_last_call_signatures)
        )

        if all_failed:
            self._stuck_rounds_err += 1
            if self._stuck_rounds_err >= self.STUCK_CONSECUTIVE_THRESHOLD:
                self._stuck_rounds_err = 0
                return True
        else:
            self._stuck_rounds_err = 1 if all_failed else 0

        if is_duplicate:
            # 与上一轮完全相同 → 肯定卡死
            self._stuck_rounds_err = 0
            return True

        self._stuck_last_call_signatures = current_sigs
        return False

    def _check_tool_permission(self, tc) -> Tuple[bool, str]:
        """
        权限检查包装：调用 PermissionManager.check()。
        返回 (allowed, reason)。若被拒绝，自动发出 ERROR 事件。
        """
        pm = getattr(self, '_permission_manager', None)
        if pm is None:
            return (True, "")

        allowed, reason = pm.check(tc.name, getattr(tc, 'arguments', {}))
        if not allowed:
            self._emit(AgentEventType.ERROR, f"权限拒绝: {tc.name} — {reason}")
            self._errors.append(f"权限拒绝 [{tc.name}]: {reason}")
        return (allowed, reason)

    def _tool_loop(self, user_message: str) -> dict:
        """工具调用循环（同步版）— 含卡死检测"""
        augmented_message = self._inject_rag_context(user_message)
        self._engine.messages.append({"role": "user", "content": augmented_message})
        self._engine._trim_context()

        tools = self._engine.registry.to_openai_tools() if self._engine.registry.count() > 0 else None

        # 卡死检测状态
        self._stuck_rounds_err = 0
        self._stuck_last_call_signatures = []
        self._all_last_round_failed = False

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

            # 卡死检测（执行前检查上一轮结果）
            if self._detect_stuck_progress(response.tool_calls):
                stuck_msg = (
                    f"检测到 Agent 死循环：连续 {self.STUCK_CONSECUTIVE_THRESHOLD} 轮无有效进展。"
                    f"当前重复调用: {', '.join(tc.name for tc in response.tool_calls)}"
                )
                self._emit(AgentEventType.ERROR, stuck_msg)
                self._errors.append(stuck_msg)
                return {"success": False, "summary": stuck_msg}

            # 处理工具调用 — 并行执行独立调用
            assistant_msg = {"role": "assistant", "content": None, "tool_calls": []}
            tool_count = len(response.tool_calls)
            round_success_count = 0

            if tool_count == 1:
                # 单工具调用：权限检查 + 串行执行（含重试）
                tc = response.tool_calls[0]
                allowed, reason = self._check_tool_permission(tc)
                if not allowed:
                    self._engine.messages.append({
                        "role": "tool", "tool_call_id": tc.id,
                        "content": json.dumps({"success": False, "error": reason}, ensure_ascii=False),
                    })
                    self._all_last_round_failed = True
                    continue

                self._tools_called.append(tc.name)
                self._emit(AgentEventType.ACT, f"调用工具: {tc.name}",
                          {"tool": tc.name, "args": tc.arguments})
                result = self._execute_one_tool(tc)
                success = result.get("success", False)
                if success:
                    round_success_count += 1
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
                # 多工具调用：权限检查 + 并行执行
                # 先做权限预检，拒绝的工具标记为 blocked
                blocked_tools = {}
                allowed_calls = []
                for tc in response.tool_calls:
                    allowed, reason = self._check_tool_permission(tc)
                    if allowed:
                        allowed_calls.append(tc)
                    else:
                        blocked_tools[tc.id] = (tc, reason)

                # 全部被拒 → 继续下一轮
                if not allowed_calls:
                    self._all_last_round_failed = True
                    for tid, (tc, reason) in blocked_tools.items():
                        self._engine.messages.append({
                            "role": "tool", "tool_call_id": tid,
                            "content": json.dumps({"success": False, "error": reason}, ensure_ascii=False),
                        })
                    continue

                self._emit(AgentEventType.ACT,
                          f"并行调用 {len(allowed_calls)} 个工具: "
                          f"{', '.join(tc.name for tc in allowed_calls)}"
                          + (f"（{len(blocked_tools)} 个被权限拒绝）" if blocked_tools else ""),
                          {"parallel": True, "count": len(allowed_calls),
                           "blocked": len(blocked_tools)})

                futures = {}
                future_to_idx = {}
                with ThreadPoolExecutor(max_workers=min(tool_count, 8)) as pool:
                    for idx, tc in enumerate(response.tool_calls):
                        self._tools_called.append(tc.name)
                        f = pool.submit(self._execute_one_tool, tc)
                        futures[f] = tc
                        future_to_idx[f] = idx

                    idx_results = {}
                    for future in as_completed(futures):
                        tc = futures[future]
                        idx = future_to_idx[future]
                        try:
                            result = future.result()
                        except Exception as e:
                            result = {"success": False, "error": str(e)}
                            self._errors.append(f"{tc.name}: {e}")
                            self._emit(AgentEventType.ERROR, f"{tc.name} 并行执行异常: {e}")
                        if result.get("success", False):
                            round_success_count += 1
                        idx_results[idx] = (tc, result)
                        success = result.get("success", False)
                        output = str(result.get("result", result.get("error", "")))[:500]
                        self._emit(AgentEventType.OBSERVE,
                                  f"{'✅' if success else '❌'} {tc.name}: {output[:200]}",
                                  {"tool": tc.name, "success": success, "output": output})

                # 按原始顺序构建消息（确保 LLM 能正确匹配 tool_call_id）
                for idx, tc in enumerate(response.tool_calls):
                    # 被权限拒绝的工具
                    if tc.id in blocked_tools:
                        _, reason = blocked_tools[tc.id]
                        assistant_msg["tool_calls"].append({
                            "id": tc.id, "type": "function",
                            "function": {"name": tc.name,
                                        "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
                        })
                        self._engine.messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps({"success": False, "error": reason}, ensure_ascii=False),
                        })
                        continue

                    # 正常执行的工具
                    assistant_msg["tool_calls"].append({
                        "id": tc.id, "type": "function",
                        "function": {"name": tc.name,
                                    "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
                    })
                    tc_and_result = idx_results.get(idx, (tc, {"success": False, "error": "执行结果缺失"}))
                    _, result = tc_and_result
                    self._engine.messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })

            # 记录本轮是否有工具成功（供下一轮卡死检测用）
            self._all_last_round_failed = (round_success_count == 0)
            self._engine.messages.append(assistant_msg)

        # 达到最大迭代
        self._emit(AgentEventType.ERROR,
                  f"达到最大迭代次数 {self._max_iterations}，任务可能未完成")
        return {"success": False,
                "summary": f"达到最大迭代次数 ({self._max_iterations} 步)。"
                          f"已调用工具: {', '.join(self._tools_called)}"}

    def _tool_loop_stream(self, user_message: str) -> Iterator[AgentEvent]:
        """工具调用循环（流式版）— 含卡死检测"""
        augmented_message = self._inject_rag_context(user_message)
        self._engine.messages.append({"role": "user", "content": augmented_message})
        self._engine._trim_context()

        tools = self._engine.registry.to_openai_tools() if self._engine.registry.count() > 0 else None

        # 卡死检测状态
        self._stuck_rounds_err = 0
        self._stuck_last_call_signatures = []
        self._all_last_round_failed = False

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

            # 卡死检测
            if self._detect_stuck_progress(response.tool_calls):
                stuck_msg = (
                    f"检测到 Agent 死循环：连续 {self.STUCK_CONSECUTIVE_THRESHOLD} 轮无有效进展。"
                    f"当前重复调用: {', '.join(tc.name for tc in response.tool_calls)}"
                )
                event = AgentEvent(AgentEventType.ERROR, self._current_step, self._total_steps, stuck_msg)
                self._events.append(event)
                self._errors.append(stuck_msg)
                yield event
                return

            round_success_count = 0
            assistant_msg = {"role": "assistant", "content": None, "tool_calls": []}
            for tc in response.tool_calls:
                # 权限检查
                allowed, reason = self._check_tool_permission(tc)
                if not allowed:
                    self._engine.messages.append({
                        "role": "tool", "tool_call_id": tc.id,
                        "content": json.dumps({"success": False, "error": reason}, ensure_ascii=False),
                    })
                    assistant_msg["tool_calls"].append({
                        "id": tc.id, "type": "function",
                        "function": {"name": tc.name,
                                    "arguments": json.dumps(tc.arguments, ensure_ascii=False)},
                    })
                    self._all_last_round_failed = True
                    continue

                self._tools_called.append(tc.name)
                tool_data = {"tool": tc.name, "args": tc.arguments}
                event = AgentEvent(AgentEventType.ACT, self._current_step, self._total_steps,
                                  f"调用工具: {tc.name}", tool_data)
                self._events.append(event)
                yield event

                result = self._execute_one_tool(tc)

                success = result.get("success", False)
                if success:
                    round_success_count += 1
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

            self._all_last_round_failed = (round_success_count == 0)
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
