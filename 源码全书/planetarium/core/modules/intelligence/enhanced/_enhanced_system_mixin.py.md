# `planetarium/core/modules/intelligence/enhanced/_enhanced_system_mixin.py`

> 路径：`planetarium/core/modules/intelligence/enhanced/_enhanced_system_mixin.py` | 行数：67


---


```python
# -*- coding: utf-8 -*-
"""
增强 AI 工具集 — 系统操作 Mixin（exec / schedule_task）
"""

import os
import json
import subprocess
import hashlib
from datetime import datetime
from typing import Dict, Any

from ._enhanced_base import _PROJECT_ROOT, _DATA_DIR


class EnhancedSystemMixin:
    """系统操作工具集"""

    def _tool_exec(self, command: str) -> Dict[str, Any]:
        """执行 Shell 命令"""
        dangerous_keywords = ["rm -rf", "format", "dd if=", "mkfs", ":(){ :|:& };:"]
        for kw in dangerous_keywords:
            if kw in command.lower():
                return {"success": False, "error": f"命令包含危险操作，已拒绝: {kw}"}

        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30,
                cwd=_PROJECT_ROOT,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip() or "(无输出)",
                "stderr": result.stderr.strip() or "",
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "命令执行超时（30 秒）"}

    def _tool_schedule_task(self, title: str, note: str = "") -> Dict[str, Any]:
        """创建任务提醒"""
        tasks_file = os.path.join(_DATA_DIR, "tasks.json")
        tasks = []
        if os.path.exists(tasks_file):
            try:
                with open(tasks_file, "r", encoding="utf-8") as f:
                    tasks = json.load(f)
            except (json.JSONDecodeError, IOError):
                tasks = []

        task = {
            "id": hashlib.md5(f"{title}{datetime.now().isoformat()}".encode()).hexdigest()[:8],
            "title": title,
            "note": note,
            "created_at": datetime.now().isoformat(),
            "status": "pending",
        }
        tasks.append(task)

        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "task": task,
            "total_tasks": len(tasks),
        }

```
