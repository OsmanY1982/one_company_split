# -*- coding: utf-8 -*-
"""obscura_provider — 桥接存根（唯一源: iqra/core/obscura_provider.py）"""
import os as _os
import sys as _sys
_iqra_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_iqra_pkg = _os.path.join(_iqra_root, "iqra")
if _iqra_pkg not in _sys.path:
    _sys.path.insert(0, _iqra_pkg)
from iqra.core.obscura_provider import get_provider

__all__ = ["get_provider"]
