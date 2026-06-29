# `iqra/core/_agent_loop_compat_mixin.py`

> 路径：`iqra/core/_agent_loop_compat_mixin.py` | 行数：166


---


```python
# -*- coding: utf-8 -*-
"""
AgentLoopCompatMixin — ChatEngine 兼容层 mixin

提供 chat_stream / chat / 属性包装 / reset / save / get_history 等
与 ChatEngine 完全兼容的接口，供 ChatWorker 直接用 AgentLoop 替代 ChatEngine。
从 agent_loop.py 拆分。
"""

import json
import time
from typing import Iterator


class AgentLoopCompatMixin:
    """ChatEngine 兼容层 — 供 AgentLoop 多重继承使用，不继承任何基类"""

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
