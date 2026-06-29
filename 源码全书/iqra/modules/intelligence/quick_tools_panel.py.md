# `iqra/modules/intelligence/quick_tools_panel.py`

> 路径：`iqra/modules/intelligence/quick_tools_panel.py` | 行数：10


---


```python
# -*- coding: utf-8 -*-
"""
快捷工具面板 — 重导出模块
QuickToolsWidget + APIKeyConfigDialog 已拆分到 _quick_tools_widget.py / _api_key_dialog.py
"""

from ._quick_tools_widget import QuickToolsWidget
from ._api_key_dialog import APIKeyConfigDialog

__all__ = ["QuickToolsWidget", "APIKeyConfigDialog"]

```
