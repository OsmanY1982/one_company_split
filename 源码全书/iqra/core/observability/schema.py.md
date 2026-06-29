# `iqra/core/observability/schema.py`

> 路径：`iqra/core/observability/schema.py` | 行数：178


---


```python
"""
Iqra Observability Schema — 可观测性数据模型
"""

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List


@dataclass
class TokenRecord:
    """Token 用量记录"""
    record_id: str = ""
    trace_id: str = ""
    session_id: str = ""
    model: str = ""
    provider: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: float = 0.0
    timestamp: float = 0.0
    success: bool = True
    error: str = ""

    def __post_init__(self):
        if not self.record_id:
            self.record_id = str(uuid.uuid4())[:12]
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class TraceStep:
    """调用链步骤"""
    step_name: str           # e.g. "user_input", "rag_inject", "super_intel", "llm_call", "tool_exec", "response"
    step_index: int
    started_at: float
    ended_at: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: str = ""

    @property
    def duration_ms(self) -> float:
        if self.ended_at:
            return (self.ended_at - self.started_at) * 1000
        return 0.0


@dataclass
class TraceRecord:
    """调用链记录 — 一次完整对话轮次"""
    trace_id: str = ""
    session_id: str = ""
    user_message: str = ""
    steps: List[TraceStep] = field(default_factory=list)
    created_at: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=lambda: {"in": 0, "out": 0})
    total_latency_ms: float = 0.0

    def __post_init__(self):
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())[:12]
        if not self.created_at:
            self.created_at = time.time()

    def add_step(self, name: str, metadata: Dict[str, Any] = None) -> int:
        idx = len(self.steps)
        self.steps.append(TraceStep(
            step_name=name,
            step_index=idx,
            started_at=time.time(),
            metadata=metadata or {},
        ))
        return idx

    def end_step(self, step_index: int, error: str = "", metadata: Dict[str, Any] = None):
        if 0 <= step_index < len(self.steps):
            self.steps[step_index].ended_at = time.time()
            if error:
                self.steps[step_index].error = error
            if metadata:
                self.steps[step_index].metadata.update(metadata)

    def finalize(self):
        self.total_latency_ms = (time.time() - self.created_at) * 1000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "user_message": self.user_message,
            "steps": [asdict(s) for s in self.steps],
            "created_at": self.created_at,
            "token_usage": self.token_usage,
            "total_latency_ms": self.total_latency_ms,
        }


@dataclass
class CostRecord:
    """成本统计记录"""
    record_id: str = ""
    model: str = ""
    provider: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    timestamp: float = 0.0
    session_id: str = ""

    def __post_init__(self):
        if not self.record_id:
            self.record_id = str(uuid.uuid4())[:12]
        if not self.timestamp:
            self.timestamp = time.time()


# ═══════════════════════════════════════════
# 各模型 Token 单价（USD / 1M tokens）
# 数据来源：各供应商官方定价，2026-06
# ═══════════════════════════════════════════

MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # OpenAI
    "gpt-4o":                {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini":           {"input": 0.15,  "output": 0.60},
    "gpt-4.1":               {"input": 2.00,  "output": 8.00},
    "gpt-4.1-mini":          {"input": 0.40,  "output": 1.60},
    "gpt-4.1-nano":          {"input": 0.10,  "output": 0.40},
    "o4-mini":               {"input": 1.10,  "output": 4.40},
    # Anthropic
    "claude-sonnet-4-20250514":  {"input": 3.00,  "output": 15.00},
    "claude-3.5-sonnet":     {"input": 3.00,  "output": 15.00},
    "claude-3.5-haiku":      {"input": 0.80,  "output": 4.00},
    # DeepSeek
    "deepseek-chat":         {"input": 0.27,  "output": 1.10},
    "deepseek-reasoner":     {"input": 0.55,  "output": 2.19},
    # 通义千问
    "qwen-turbo":            {"input": 0.14,  "output": 0.28},
    "qwen-plus":             {"input": 0.29,  "output": 0.57},
    "qwen-max":              {"input": 2.86,  "output": 5.71},
    # Google
    "gemini-2.5-flash":      {"input": 0.15,  "output": 0.60},
    "gemini-2.5-pro":        {"input": 1.25,  "output": 10.00},
    # 智谱
    "glm-4":                 {"input": 0.14,  "output": 0.14},
    # Moonshot
    "moonshot-v1-8k":        {"input": 1.71,  "output": 1.71},
    # 本地模型免费
    "local":                 {"input": 0.0,   "output": 0.0},
}


def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """
    估算单次调用成本。

    优先精确匹配模型名；匹配不到则用模型名前缀匹配降级；
    完全未知返回 0.0。
    """
    # 精确匹配
    if model in MODEL_PRICING:
        p = MODEL_PRICING[model]
    else:
        # 前缀降级匹配
        p = None
        model_lower = model.lower()
        for key, pricing in MODEL_PRICING.items():
            if model_lower.startswith(key.split("-")[0]):
                p = pricing
                break
        if p is None:
            return 0.0

    input_cost = (tokens_in / 1_000_000) * p["input"]
    output_cost = (tokens_out / 1_000_000) * p["output"]
    return round(input_cost + output_cost, 6)

```
