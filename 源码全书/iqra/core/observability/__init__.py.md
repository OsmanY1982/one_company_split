# `iqra/core/observability/__init__.py`

> 路径：`iqra/core/observability/__init__.py` | 行数：189


---


```python
"""
Iqra Observability — 可观测性模块

统一管理 Token 用量追踪、调用链监控、成本统计三个维度。
通过 ObservableBridge 入口接入 AgentBridge 和 ChatEngine。

用法:
    from iqra.core.observability import ObservableBridge

    obs = ObservableBridge(memory_store=smart_memory_store)
    obs.attach_to(backend)            # 拦截 LLM 调用
    trace_id = obs.trace_begin(...)   # 开始追踪
    obs.trace_end()                   # 结束追踪并持久化
"""

import json
import logging
from typing import Optional

from .token_observer import TokenObserver
from .trace_manager import TraceManager
from .cost_tracker import CostTracker

try:
    from ..rag_context import _HAVE_SEMANTIC_SEARCH
except ImportError:
    _HAVE_SEMANTIC_SEARCH = False

logger = logging.getLogger(__name__)


class ObservableBridge:
    """
    可观测性统一入口。

    聚合 TokenObserver / TraceManager / CostTracker，
    为 AgentBridge 和 ChatEngine 提供统一的可观测性注入点。
    """

    def __init__(self, memory_store=None):
        """
        Args:
            memory_store: SmartMemoryStore 实例，用于持久化（通过 _core_memory）
        """
        self._core_memory = None
        if memory_store and hasattr(memory_store, '_core_memory'):
            self._core_memory = memory_store._core_memory

        self.token_observer = TokenObserver(
            store_callback=self._persist_token_record,
        )
        self.trace_manager = TraceManager(
            store_callback=self._persist_trace_record,
        )
        self.cost_tracker = CostTracker(
            store_callback=self._persist_cost_record,
        )

        self._session_id: str = ""
        self._enabled: bool = True

    # ── 启用/禁用 ──

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    # ── Backend Hook ──

    def attach_to(self, backend):
        """
        拦截 Backend 的 chat/chat_stream 方法。

        Args:
            backend: BaseLLMBackend 实例

        Returns:
            包装后的 backend
        """
        if not self._enabled:
            return backend
        self.token_observer.wrap_backend(backend)
        logger.debug("ObservableBridge attached to backend")
        return backend

    # ── Trace 生命周期 ──

    def trace_begin(self, session_id: str = "", user_message: str = "") -> str:
        """开始新调用链，返回 trace_id"""
        if not self._enabled:
            return ""
        self._session_id = session_id
        self.token_observer.set_session(session_id)
        trace_id = self.trace_manager.start_trace(session_id, user_message)
        self.token_observer.set_trace(trace_id)
        return trace_id

    def step_begin(self, step_name: str, metadata: dict = None) -> int:
        if not self._enabled:
            return -1
        return self.trace_manager.step_begin(step_name, metadata)

    def step_end(self, step_index: int = None, error: str = "", metadata: dict = None):
        if not self._enabled:
            return
        self.trace_manager.step_end(step_index, error, metadata)

    # ── 语义搜索步骤追踪 ──

    def semantic_search_begin(self, query: str = "") -> int:
        """标记语义搜索开始"""
        if not self._enabled:
            return -1
        return self.trace_manager.step_begin("semantic_search", {
            "query": query[:200],
            "search_mode": "hybrid" if _HAVE_SEMANTIC_SEARCH else "bm25_only",
        })

    def semantic_search_end(self, step_index: int, result_count: int = 0, elapsed_ms: float = 0, error: str = ""):
        """标记语义搜索结束"""
        if not self._enabled or step_index < 0:
            return
        self.trace_manager.step_end(step_index, error, {
            "result_count": result_count,
            "elapsed_ms": round(elapsed_ms, 2),
        })

    def trace_end(self):
        """结束当前调用链并持久化"""
        if not self._enabled:
            return
        # 同步 token 用量到 trace
        totals = self.token_observer.totals
        self.trace_manager.set_token_usage(totals["tokens_in"], totals["tokens_out"])
        self.trace_manager.end_trace()

    # ── 持久化回调（写入 IqraMemory，agent_id='observability'）──

    def _persist_token_record(self, record):
        # 成本追踪（不依赖 core_memory，始终生效）
        self.cost_tracker.record(
            model=record.model,
            provider=record.provider,
            tokens_in=record.tokens_in,
            tokens_out=record.tokens_out,
            session_id=record.session_id,
        )
        # 持久化（需 core_memory）
        if not self._core_memory:
            return
        try:
            self._core_memory.add(
                category="observability/token",
                content=json.dumps(record.__dict__, ensure_ascii=False),
            )
        except Exception as e:
            logger.debug("Persist token record failed: %s", e)

    def _persist_trace_record(self, record):
        if not self._core_memory:
            return
        try:
            self._core_memory.add(
                category="observability/trace",
                content=json.dumps(record.to_dict(), ensure_ascii=False),
            )
        except Exception as e:
            logger.debug("Persist trace record failed: %s", e)

    def _persist_cost_record(self, record):
        if not self._core_memory:
            return
        try:
            self._core_memory.add(
                category="observability/cost",
                content=json.dumps(record.__dict__, ensure_ascii=False),
            )
        except Exception as e:
            logger.debug("Persist cost record failed: %s", e)

    # ── 查询接口 ──

    def get_token_totals(self) -> dict:
        return self.token_observer.totals

    def get_cost_report(self) -> dict:
        return self.cost_tracker.full_report()

```
