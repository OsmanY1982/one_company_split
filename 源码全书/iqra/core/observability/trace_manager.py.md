# `iqra/core/observability/trace_manager.py`

> 路径：`iqra/core/observability/trace_manager.py` | 行数：79


---


```python
"""
TraceManager — 调用链监控

为每次对话轮次分配 trace_id，串联完整调用链：
  user_input → pipeline(rag/super_intel/token_opt) → LLM call → tool calls → response
"""

import time
import logging
from typing import Optional, Dict, Any
from .schema import TraceRecord

logger = logging.getLogger(__name__)


class TraceManager:
    """调用链管理器"""

    def __init__(self, store_callback=None):
        """
        Args:
            store_callback: callable(TraceRecord) — 存储回调
        """
        self._store_callback = store_callback
        self._active_trace: Optional[TraceRecord] = None
        self._step_stack: list = []  # 步骤索引栈，支持嵌套

    def start_trace(self, session_id: str, user_message: str) -> str:
        """开始新一次调用链追踪，返回 trace_id"""
        self._active_trace = TraceRecord(
            session_id=session_id,
            user_message=user_message[:500],  # 截断长消息
        )
        self._step_stack.clear()
        return self._active_trace.trace_id

    @property
    def active_trace_id(self) -> str:
        return self._active_trace.trace_id if self._active_trace else ""

    def step_begin(self, step_name: str, metadata: Dict[str, Any] = None) -> int:
        """标记一个管线步骤开始，返回步骤索引"""
        if not self._active_trace:
            return -1
        idx = self._active_trace.add_step(step_name, metadata)
        self._step_stack.append(idx)
        return idx

    def step_end(self, step_index: int = None, error: str = "",
                 metadata: Dict[str, Any] = None):
        """标记步骤结束"""
        if not self._active_trace:
            return
        if step_index is None and self._step_stack:
            step_index = self._step_stack.pop()
        elif step_index is not None and self._step_stack:
            # 从栈中移除 matching 的索引
            try:
                self._step_stack.remove(step_index)
            except ValueError:
                pass
        self._active_trace.end_step(step_index, error, metadata)

    def set_token_usage(self, tokens_in: int, tokens_out: int):
        if self._active_trace:
            self._active_trace.token_usage = {"in": tokens_in, "out": tokens_out}

    def end_trace(self):
        """结束调用链并存储"""
        if not self._active_trace:
            return
        self._active_trace.finalize()
        if self._store_callback:
            try:
                self._store_callback(self._active_trace)
            except Exception as e:
                logger.debug("TraceManager store callback failed: %s", e)
        self._active_trace = None
        self._step_stack.clear()

```
