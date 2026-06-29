# `core/tool_registry.py`

> 路径：`core/tool_registry.py` | 行数：7


---


```python
# -*- coding: utf-8 -*-
"""tool_registry — 桥接存根（唯一源: iqra/core/tool_registry.py）"""
import os as _os, sys as _sys
_r = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_p = _os.path.join(_r, "iqra")
if _p not in _sys.path: _sys.path.insert(0, _p)
from iqra.core.tool_registry import *

```
