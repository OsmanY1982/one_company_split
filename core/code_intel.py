# -*- coding: utf-8 -*-
"""code_intel — 桥接存根（唯一源: iqra/core/code_intel.py）"""
import os as _os, sys as _sys
_r = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_p = _os.path.join(_r, "iqra")
if _p not in _sys.path: _sys.path.insert(0, _p)
from iqra.core.code_intel import *
