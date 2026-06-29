# `core/modules/intelligence/enhanced/_enhanced_storage_mixin.py`

> 路径：`core/modules/intelligence/enhanced/_enhanced_storage_mixin.py` | 行数：94


---


```python
# -*- coding: utf-8 -*-
"""
增强 AI 工具集 — 记忆 + 会话存储 Mixin（memory_save / memory_load / session_create / session_list）
"""

import os
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, Any

from ._enhanced_base import _DATA_DIR


class EnhancedStorageMixin:
    """持久化存储工具集"""

    def _tool_memory_save(self, key: str, value: str) -> Dict[str, Any]:
        """保存记忆"""
        memory_file = os.path.join(_DATA_DIR, "memory.json")
        memories = {}
        if os.path.exists(memory_file):
            try:
                with open(memory_file, "r", encoding="utf-8") as f:
                    memories = json.load(f)
            except (json.JSONDecodeError, IOError):
                memories = {}

        memories[key] = {
            "value": value,
            "updated_at": datetime.now().isoformat(),
        }

        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)

        return {"success": True, "key": key, "message": f"记忆 '{key}' 已保存"}

    def _tool_memory_load(self, key: str = "") -> Dict[str, Any]:
        """读取记忆"""
        memory_file = os.path.join(_DATA_DIR, "memory.json")
        if not os.path.exists(memory_file):
            return {"success": True, "memories": {}, "message": "暂无记忆"}

        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                memories = json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"success": True, "memories": {}, "message": "记忆文件损坏"}

        if key:
            if key in memories:
                return {"success": True, "key": key, "value": memories[key]["value"]}
            return {"success": False, "error": f"记忆 '{key}' 不存在"}

        return {"success": True, "memories": memories, "count": len(memories)}

    def _tool_session_create(self, name: str = "新会话") -> Dict[str, Any]:
        """创建会话"""
        sessions_file = os.path.join(_DATA_DIR, "sessions.json")
        sessions = []
        if os.path.exists(sessions_file):
            try:
                with open(sessions_file, "r", encoding="utf-8") as f:
                    sessions = json.load(f)
            except (json.JSONDecodeError, IOError):
                sessions = []

        session = {
            "id": hashlib.md5(f"{name}{time.time()}".encode()).hexdigest()[:12],
            "name": name,
            "created_at": datetime.now().isoformat(),
        }
        sessions.append(session)

        with open(sessions_file, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)

        return {"success": True, "session": session}

    def _tool_session_list(self) -> Dict[str, Any]:
        """列出会话"""
        sessions_file = os.path.join(_DATA_DIR, "sessions.json")
        if not os.path.exists(sessions_file):
            return {"success": True, "sessions": [], "count": 0}

        try:
            with open(sessions_file, "r", encoding="utf-8") as f:
                sessions = json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"success": True, "sessions": [], "count": 0}

        return {"success": True, "sessions": sessions, "count": len(sessions)}

```
