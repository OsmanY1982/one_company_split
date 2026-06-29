# `iqra/core/_agent_events.py`

> 路径：`iqra/core/_agent_events.py` | 行数：50


---


```python
# -*- coding: utf-8 -*-
"""
Agent 事件模型 — AgentEventType / AgentEvent / AgentResult

从 agent_loop.py 拆分出的数据模型层，供 AgentLoopBase 和所有 mixin 共享。
"""

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Any, List


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

```
