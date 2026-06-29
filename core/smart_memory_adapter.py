# -*- coding: utf-8 -*-
"""smart_memory_adapter — 桥接存根（唯一源: iqra/core/smart_memory_adapter.py）"""
import os as _os, sys as _sys
_r = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_p = _os.path.join(_r, "iqra")
if _p not in _sys.path: _sys.path.insert(0, _p)
from iqra.core.smart_memory_adapter import *
