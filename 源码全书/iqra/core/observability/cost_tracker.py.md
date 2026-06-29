# `iqra/core/observability/cost_tracker.py`

> 路径：`iqra/core/observability/cost_tracker.py` | 行数：95


---


```python
"""
CostTracker — 成本统计

基于 model × token 单价计算实时成本，支持按会话/日/月聚合。
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Callable
from .schema import CostRecord, estimate_cost

logger = logging.getLogger(__name__)


class CostTracker:
    """LLM 成本追踪器"""

    def __init__(self, store_callback: Callable = None):
        self._store_callback = store_callback
        self._lock = threading.RLock()

        # 运行时聚合数据
        self._session_costs: Dict[str, float] = {}    # session_id → cost
        self._daily_costs: Dict[str, float] = {}       # "YYYY-MM-DD" → cost
        self._model_costs: Dict[str, float] = {}       # model → cost
        self._total_cost: float = 0.0

    def record(self, model: str, provider: str, tokens_in: int,
               tokens_out: int, session_id: str = ""):
        """记录一次 LLM 调用的成本"""
        cost = estimate_cost(model, tokens_in, tokens_out)
        if cost <= 0:
            return

        record = CostRecord(
            model=model,
            provider=provider,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost,
            session_id=session_id,
        )

        with self._lock:
            self._total_cost += cost
            date_key = time.strftime("%Y-%m-%d")
            self._daily_costs[date_key] = self._daily_costs.get(date_key, 0) + cost
            self._model_costs[model] = self._model_costs.get(model, 0) + cost
            if session_id:
                self._session_costs[session_id] = self._session_costs.get(session_id, 0) + cost

        if self._store_callback:
            try:
                self._store_callback(record)
            except Exception as e:
                logger.debug("CostTracker store callback failed: %s", e)

    @property
    def total(self) -> float:
        with self._lock:
            return round(self._total_cost, 4)

    def session_summary(self, session_id: str) -> float:
        with self._lock:
            return round(self._session_costs.get(session_id, 0), 4)

    def daily_summary(self, date_str: str = None) -> Dict[str, float]:
        """按日期聚合的成本汇总。不传 date_str 返回今天"""
        if date_str is None:
            date_str = time.strftime("%Y-%m-%d")
        with self._lock:
            return {
                k: round(v, 4)
                for k, v in sorted(self._daily_costs.items())
            }

    def model_summary(self) -> Dict[str, float]:
        with self._lock:
            return {
                k: round(v, 4)
                for k, v in sorted(self._model_costs.items(), key=lambda x: -x[1])
            }

    def full_report(self) -> dict:
        """生成完整成本报告"""
        with self._lock:
            return {
                "total_cost_usd": round(self._total_cost, 4),
                "daily_breakdown": self.daily_summary(),
                "model_breakdown": self.model_summary(),
                "session_costs": {
                    k: round(v, 4) for k, v in self._session_costs.items()
                },
            }

```
