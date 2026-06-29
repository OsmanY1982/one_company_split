# `iqra/core/permission_manager.py`

> 路径：`iqra/core/permission_manager.py` | 行数：196


---


```python
# -*- coding: utf-8 -*-
"""
权限管理器 — restricted / ask / auto 三级权限

对标 Claude Code 5 级权限，Phase 1 实现三级：

  restricted: 只读操作，禁止写/删/shell/网络
  ask（默认）: 每个工具调用需用户确认
  auto:      全部自动执行

用法:
    pm = PermissionManager("ask")
    allowed, reason = pm.check("write_file", {"file_path": "/tmp/test.py"})
    # 或设置回调处理 ask 模式:
    pm.set_ask_callback(lambda tool, args: input(f"允许 {tool}? [y/N] ") == "y")
"""

from enum import Enum
from typing import Callable, Dict, Optional, Tuple

from .iqra_logging import logger


class PermissionLevel(str, Enum):
    RESTRICTED = "restricted"
    ASK = "ask"
    AUTO = "auto"


# ── 工具危险等级分类 ──

# 只读工具（所有模式下都允许）
READONLY_TOOLS = {
    "read_file", "read_text", "search_files", "search_image",
    "list_directory", "analyze_image", "web_search",
    "get_file_info", "get_user_persona",
}

# 高风险工具（restricted 模式下禁止，ask 模式下必须确认）
HIGH_RISK_TOOLS = {
    "delete", "shell_executor", "python_executor",
}

# 写入工具（restricted 模式下禁止，ask 模式下需确认）
WRITE_TOOLS = {
    "write_file", "edit_file", "create_directory",
    "move_file", "copy_file", "rename_file",
    "convert_file",
}

# 网络/外部工具（restricted 模式下需特别谨慎）
NETWORK_TOOLS = {
    "web_fetch", "dispatch_task", "create_scheduled_task",
    "modify_scheduled_task",
}


class PermissionManager:
    """
    权限管理器

    核心方法:
      check(tool_name, tool_args) → (allowed: bool, reason: str)
        - restricted: 只允许 READONLY_TOOLS
        - ask: 调用 ask_callback，由用户决定
        - auto: 全部允许

    ask_callback 签名:
      def callback(tool_name: str, tool_args: dict) -> bool:
          return True  # 允许  /  False  # 拒绝
    """

    def __init__(
        self,
        level: str = "ask",
        ask_callback: Optional[Callable[[str, dict], bool]] = None,
    ):
        self._level = PermissionLevel(level)
        self._ask_callback = ask_callback
        self._blocked_count: int = 0
        self._allowed_count: int = 0

    # ── 属性 ──

    @property
    def level(self) -> PermissionLevel:
        return self._level

    @level.setter
    def level(self, value: str):
        self._level = PermissionLevel(value)
        logger.info("PermissionManager: 切换到 %s 模式", value)

    @property
    def stats(self) -> Dict[str, int]:
        return {"blocked": self._blocked_count, "allowed": self._allowed_count}

    # ── 回调设置 ──

    def set_ask_callback(self, callback: Callable[[str, dict], bool]):
        """设置 ask 模式的用户确认回调"""
        self._ask_callback = callback

    # ── 权限检查 ──

    def check(self, tool_name: str, tool_args: dict = None) -> Tuple[bool, str]:
        """
        检查是否允许执行指定工具。

        Returns:
            (allowed, reason)
        """
        tool_args = tool_args or {}

        if self._level == PermissionLevel.AUTO:
            self._allowed_count += 1
            return (True, "")

        if self._level == PermissionLevel.RESTRICTED:
            return self._check_restricted(tool_name, tool_args)

        if self._level == PermissionLevel.ASK:
            return self._check_ask(tool_name, tool_args)

        # 未知模式 → 保守拒绝
        self._blocked_count += 1
        return (False, f"未知权限模式: {self._level}")

    def _check_restricted(self, tool_name: str, tool_args: dict) -> Tuple[bool, str]:
        """restricted 模式：只允许只读操作"""
        if tool_name in READONLY_TOOLS:
            self._allowed_count += 1
            return (True, "")

        if tool_name in HIGH_RISK_TOOLS:
            self._blocked_count += 1
            return (False, f"restricted 模式禁止高风险操作: {tool_name}")

        if tool_name in WRITE_TOOLS:
            self._blocked_count += 1
            return (False, f"restricted 模式禁止写入: {tool_name}")

        if tool_name in NETWORK_TOOLS:
            self._blocked_count += 1
            return (False, f"restricted 模式禁止网络操作: {tool_name}")

        # 未知工具 → 保守拒绝
        self._blocked_count += 1
        return (False, f"restricted 模式不允许未知工具: {tool_name}")

    def _check_ask(self, tool_name: str, tool_args: dict) -> Tuple[bool, str]:
        """ask 模式：只读自动放行，其他需用户确认"""
        # 只读工具自动放行（减少确认打扰）
        if tool_name in READONLY_TOOLS:
            self._allowed_count += 1
            return (True, "")

        # 有回调 → 询问用户
        if self._ask_callback:
            try:
                allowed = self._ask_callback(tool_name, tool_args)
            except Exception as e:
                logger.warning("PermissionManager: ask_callback 异常: %s", e)
                self._blocked_count += 1
                return (False, f"确认回调失败: {e}")

            if allowed:
                self._allowed_count += 1
                return (True, "")
            else:
                self._blocked_count += 1
                return (False, f"用户拒绝了工具调用: {tool_name}")

        # 无回调 → 默认拒绝（安全优先）
        self._blocked_count += 1
        return (False, f"ask 模式需要用户确认（无回调）: {tool_name}")

    # ── 工具分类查询 ──

    @staticmethod
    def classify(tool_name: str) -> str:
        """返回工具的危险等级分类"""
        if tool_name in READONLY_TOOLS:
            return "readonly"
        if tool_name in HIGH_RISK_TOOLS:
            return "high_risk"
        if tool_name in WRITE_TOOLS:
            return "write"
        if tool_name in NETWORK_TOOLS:
            return "network"
        return "unknown"

    @staticmethod
    def is_dangerous(tool_name: str) -> bool:
        """是否为高风险/写入操作"""
        return tool_name in HIGH_RISK_TOOLS or tool_name in WRITE_TOOLS

```
