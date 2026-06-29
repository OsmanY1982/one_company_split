# -*- coding: utf-8 -*-
"""AgentLoop — 桥接存根（唯一源: iqra/core/agent_loop.py）

由于项目根 core/ 包先于 iqra/core/ 被 Python import 缓存命中，
core.agent_loop 无法直接解析到 iqra/core/agent_loop.py。
此存根通过动态路径注入将 import 重定向到 iqra 下的真实实现。
"""
import os as _os
import sys as _sys

# 确保 iqra 在 sys.path 中
_iqra_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_iqra_pkg = _os.path.join(_iqra_root, "iqra")
if _iqra_pkg not in _sys.path:
    _sys.path.insert(0, _iqra_pkg)

# 从 iqra 的真实 agent_loop 重导出所有符号
from iqra.core.agent_loop import (
    AgentLoop,
    AgentEventType,
    AgentEvent,
    AgentResult,
    AGENT_SYSTEM_PROMPT,
    TOOL_FALLBACK_MAP,
)

__all__ = [
    "AgentLoop",
    "AgentEventType",
    "AgentEvent",
    "AgentResult",
    "AGENT_SYSTEM_PROMPT",
    "TOOL_FALLBACK_MAP",
]
