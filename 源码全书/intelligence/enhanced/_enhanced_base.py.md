# `intelligence/enhanced/_enhanced_base.py`

> 路径：`intelligence/enhanced/_enhanced_base.py` | 行数：170


---


```python
# -*- coding: utf-8 -*-
"""
增强 AI 工具集 — 基座模块（导入 + 路径常量 + 工具注册表 + 执行调度）
"""

import os
from typing import Dict, Any, List

# ── 数据目录 ──────────────────────────────────────────────────────────────────
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
_DATA_DIR = os.path.join(_PROJECT_ROOT, "data", "enhanced")
os.makedirs(_DATA_DIR, exist_ok=True)


def _safe_path(path: str) -> str:
    """将相对路径转换为绝对路径"""
    if os.path.isabs(path):
        return path
    return os.path.join(_PROJECT_ROOT, path)


class EnhancedAIAssistantBase:
    """增强 AI 工具助手 — 工具注册表基座"""

    def __init__(self):
        self._tools = self._register_tools()

    # ═══════════════════════════════════════════════════════════════
    # 工具注册
    # ═══════════════════════════════════════════════════════════════
    def _register_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "file_read",
                "icon": "📄",
                "description": "读取本地文件内容，自动检测编码",
                "parameters": {
                    "path": {"type": "string", "description": "文件路径（绝对或相对）", "required": True},
                    "encoding": {"type": "string", "description": "文件编码（默认自动检测）", "default": "auto"},
                },
            },
            {
                "name": "file_write",
                "icon": "💾",
                "description": "将内容写入文件（原子写入，防止损坏）",
                "parameters": {
                    "path": {"type": "string", "description": "目标文件路径", "required": True},
                    "content": {"type": "string", "description": "要写入的文本内容", "required": True},
                },
            },
            {
                "name": "multi_search",
                "icon": "🔍",
                "description": "本地全文搜索：按文件名+内容关键词查找文件",
                "parameters": {
                    "query": {"type": "string", "description": "搜索关键词", "required": True},
                    "directory": {"type": "string", "description": "搜索目录（默认项目根目录）", "default": "auto"},
                },
            },
            {
                "name": "run_code",
                "icon": "▶",
                "description": "在独立进程中执行 Python 代码（10 秒超时）",
                "parameters": {
                    "code": {"type": "string", "description": "Python 代码", "required": True},
                    "timeout": {"type": "integer", "description": "超时秒数", "default": 10},
                },
            },
            {
                "name": "browser_navigate",
                "icon": "🌐",
                "description": "在默认浏览器中打开指定 URL",
                "parameters": {
                    "url": {"type": "string", "description": "目标 URL", "required": True},
                },
            },
            {
                "name": "browser_screenshot",
                "icon": "📸",
                "description": "网页截图（需要 Playwright，否则降级为打开浏览器）",
                "parameters": {},
            },
            {
                "name": "browser_extract",
                "icon": "📋",
                "description": "提取网页文本内容（使用 urllib）",
                "parameters": {
                    "url": {"type": "string", "description": "目标 URL", "default": ""},
                },
            },
            {
                "name": "web_fetch_page",
                "icon": "🌐",
                "description": "抓取网页正文内容（提取纯文本，过滤脚本/样式）",
                "parameters": {
                    "url": {"type": "string", "description": "网页 URL（含 https://）", "required": True},
                },
            },
            {
                "name": "web_search",
                "icon": "🔍",
                "description": "网页搜索（通过 DuckDuckGo HTML 搜索结果，返回标题/链接/摘要）",
                "parameters": {
                    "query": {"type": "string", "description": "搜索关键词", "required": True},
                },
            },
            {
                "name": "exec",
                "icon": "⚙",
                "description": "执行 Shell 命令并返回输出",
                "parameters": {
                    "command": {"type": "string", "description": "Shell 命令", "required": True},
                },
            },
            {
                "name": "schedule_task",
                "icon": "⏰",
                "description": "创建简单任务提醒（存储到本地 JSON）",
                "parameters": {
                    "title": {"type": "string", "description": "任务名称", "required": True},
                    "note": {"type": "string", "description": "备注", "default": ""},
                },
            },
            {
                "name": "memory_save",
                "icon": "🧠",
                "description": "保存记忆条目到本地 JSON 存储",
                "parameters": {
                    "key": {"type": "string", "description": "记忆键", "required": True},
                    "value": {"type": "string", "description": "记忆内容", "required": True},
                },
            },
            {
                "name": "memory_load",
                "icon": "📖",
                "description": "读取所有记忆或指定键的记忆",
                "parameters": {
                    "key": {"type": "string", "description": "记忆键（留空加载所有）", "default": ""},
                },
            },
            {
                "name": "session_create",
                "icon": "💬",
                "description": "创建新会话并返回会话 ID",
                "parameters": {
                    "name": {"type": "string", "description": "会话名称", "default": "新会话"},
                },
            },
            {
                "name": "session_list",
                "icon": "📋",
                "description": "列出所有已创建的会话",
                "parameters": {},
            },
        ]

    def list_tools(self) -> List[Dict[str, Any]]:
        """返回可用工具列表"""
        return self._tools

    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行指定工具"""
        method_name = f"_tool_{tool_name}"
        if hasattr(self, method_name):
            try:
                return getattr(self, method_name)(**params)
            except Exception as e:
                return {"success": False, "error": f"{tool_name}: {str(e)}"}
        else:
            return {"success": False, "error": f"未知工具: {tool_name}"}

```
