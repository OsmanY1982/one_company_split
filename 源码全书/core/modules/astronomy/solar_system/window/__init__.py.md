# `core/modules/astronomy/solar_system/window/__init__.py`

> 路径：`core/modules/astronomy/solar_system/window/__init__.py` | 行数：18


---


```python
# -*- coding: utf-8 -*-
import sys as _sys, os as _os
_dir = _os.path.dirname(_os.path.abspath(__file__))
for _ in range(10):
    if _os.path.exists(_os.path.join(_dir, 'dark_theme.py')):
        _parent = _os.path.dirname(_dir)
        if _parent not in _sys.path:
            _sys.path.insert(0, _parent)
        break
    _dir = _os.path.dirname(_dir)

"""
太阳系天文馆 · window 子包
"""
from ._window import SolarSystemWindow
from ._hud import SolarSystemHUD

__all__ = ["SolarSystemWindow", "SolarSystemHUD"]

```
