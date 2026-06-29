"""
兼容性桥接模块 — 将业务工具模块的 ToolDefinition/ToolRegistry 导入
重定向到 iqra 核心引擎的对应类，确保所有工具注册统一走一套定义。
"""
from iqra.core.llm_backend import ToolDefinition
from iqra.core.tool_registry import ToolRegistry

__all__ = ["ToolDefinition", "ToolRegistry"]
