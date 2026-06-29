# `iqra/core/_agent_fallbacks.py`

> 路径：`iqra/core/_agent_fallbacks.py` | 行数：37


---


```python
# -*- coding: utf-8 -*-
"""
工具降级映射 — 工具失败时的分层错误恢复策略

从 agent_loop.py 拆分出的纯数据模块。
"""

from typing import Dict, List, Tuple, Callable


# 工具降级映射：工具失败时尝试的替代方案
TOOL_FALLBACK_MAP: Dict[str, List[Tuple[str, Callable[[dict], dict]]]] = {
    # read_file 失败 → 尝试 execute_shell cat（系统级兜底）
    "read_file": [
        ("execute_shell", lambda args: {
            "command": f"cat {args.get('file_path', '')}",
            "description": f"降级读取: {args.get('file_path', '')}",
        }),
    ],
    # search_files 失败 → 尝试 execute_shell find 或 mdfind
    "search_files": [
        ("execute_shell", lambda args: {
            "command": (
                f"find {args.get('root_path', '.')} "
                f"-name '*{args.get('query', '*')}*' "
                f"2>/dev/null | head -50"
            ),
            "description": "降级搜索: find",
        }),
    ],
    "list_directory": [
        ("execute_shell", lambda args: {
            "command": f"ls -la {args.get('path', '.')}",
            "description": "降级列目录",
        }),
    ],
}

```
