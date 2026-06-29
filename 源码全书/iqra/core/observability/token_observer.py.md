# `iqra/core/observability/token_observer.py`

> 路径：`iqra/core/observability/token_observer.py` | 行数：148


---


```python
"""
TokenObserver — 拦截 LLM 调用，记录 Token 用量和延迟
"""

import time
import logging
from typing import Optional
from .schema import TokenRecord

logger = logging.getLogger(__name__)


class TokenObserver:
    """
    Token 用量观察器。

    通过 monkey-patch 方式注入到 Backend 实例上，
    拦截 chat() 和 chat_stream() 调用，提取 usage 信息。
    """

    def __init__(self, store_callback=None):
        """
        Args:
            store_callback: callable(TokenRecord) — 存储回调，由 ObservableBridge 注入
        """
        self._store_callback = store_callback
        self._current_session_id: str = ""
        self._current_trace_id: str = ""
        self._total_tokens_in: int = 0
        self._total_tokens_out: int = 0

    def set_session(self, session_id: str):
        self._current_session_id = session_id

    def set_trace(self, trace_id: str):
        self._current_trace_id = trace_id

    @property
    def totals(self) -> dict:
        return {
            "tokens_in": self._total_tokens_in,
            "tokens_out": self._total_tokens_out,
        }

    def wrap_backend(self, backend):
        """
        包装 Backend 实例，拦截 chat() 和 chat_stream()。

        Args:
            backend: BaseLLMBackend 实例

        Returns:
            包装后的 backend（原地修改 + 返回）
        """
        original_chat = backend.chat
        original_chat_stream = backend.chat_stream
        provider = getattr(getattr(backend, 'config', None), 'name', 'unknown')
        model = getattr(getattr(backend, 'config', None), 'model', 'unknown')

        def wrapped_chat(messages, tools=None, tool_choice=None):
            t0 = time.time()
            error = ""
            success = True
            tokens_in = self._estimate_tokens(messages)
            tokens_out = 0

            try:
                response = original_chat(messages, tools, tool_choice=tool_choice)
                tokens_out = self._extract_tokens_from_response(response)
            except Exception as e:
                success = False
                error = str(e)[:200]
                raise
            finally:
                latency_ms = (time.time() - t0) * 1000
                self._record(model, provider, tokens_in, tokens_out, latency_ms, success, error)

            return response

        def wrapped_chat_stream(messages, tools=None, tool_choice=None):
            t0 = time.time()
            error = ""
            success = True
            tokens_in = self._estimate_tokens(messages)
            tokens_out = 0

            try:
                for chunk in original_chat_stream(messages, tools, tool_choice=tool_choice):
                    tokens_out += self._extract_tokens_from_response(chunk)
                    yield chunk
            except Exception as e:
                success = False
                error = str(e)[:200]
                raise
            finally:
                latency_ms = (time.time() - t0) * 1000
                self._record(model, provider, tokens_in, tokens_out, latency_ms, success, error)

        backend.chat = wrapped_chat
        backend.chat_stream = wrapped_chat_stream
        return backend

    def _record(self, model: str, provider: str, tokens_in: int,
                tokens_out: int, latency_ms: float, success: bool, error: str):
        self._total_tokens_in += tokens_in
        self._total_tokens_out += tokens_out

        record = TokenRecord(
            trace_id=self._current_trace_id,
            session_id=self._current_session_id,
            model=model,
            provider=provider,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=round(latency_ms, 1),
            success=success,
            error=error,
        )
        if self._store_callback:
            try:
                self._store_callback(record)
            except Exception as e:
                logger.debug("TokenObserver store callback failed: %s", e)

    @staticmethod
    def _estimate_tokens(messages) -> int:
        """粗略估算输入 Token 数：1 token ≈ 3 字符（中英文混合平均）"""
        total_chars = 0
        for m in messages:
            content = m.get("content", "")
            if isinstance(content, str):
                total_chars += len(content)
        return max(1, total_chars // 3)

    @staticmethod
    def _extract_tokens_from_response(response) -> int:
        """从 LLMResponse 中提取输出 token 数"""
        tokens = 0
        # 尝试从 usage 属性提取
        if hasattr(response, 'usage') and response.usage:
            if isinstance(response.usage, dict):
                tokens = response.usage.get("completion_tokens", response.usage.get("output_tokens", 0))
            elif hasattr(response.usage, 'completion_tokens'):
                tokens = response.usage.completion_tokens
        # 降级：从文本估算
        if tokens == 0 and hasattr(response, 'content') and response.content:
            tokens = len(response.content) // 3
        return max(1, tokens)

```
