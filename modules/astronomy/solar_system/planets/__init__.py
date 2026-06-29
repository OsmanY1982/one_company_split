# -*- coding: utf-8 -*-
"""
星球模块 — 每颗天体一个文件，统一路由
"""

# ═══ 行星 ═══
from .sun import STYLE as _sun_style, paint as _sun_paint
from .mercury import STYLE as _mercury_style, paint as _mercury_paint
from .venus import STYLE as _venus_style, paint as _venus_paint
from .earth import STYLE as _earth_style, paint as _earth_paint
from .mars import STYLE as _mars_style, paint as _mars_paint
from .jupiter import STYLE as _jupiter_style, paint as _jupiter_paint
from .saturn import STYLE as _saturn_style, paint as _saturn_paint
from .uranus import STYLE as _uranus_style, paint as _uranus_paint
from .neptune import STYLE as _neptune_style, paint as _neptune_paint

# ═══ 矮行星 ═══
from .pluto import STYLE as _pluto_style, paint as _pluto_paint
from .ceres import STYLE as _ceres_style, paint as _ceres_paint
from .eris import STYLE as _eris_style, paint as _eris_paint
from .makemake import STYLE as _makemake_style, paint as _makemake_paint
from .haumea import STYLE as _haumea_style, paint as _haumea_paint

# ═══ 卫星 ═══
from .moon import STYLE as _moon_style, paint as _moon_paint
from .io import STYLE as _io_style, paint as _io_paint
from .europa import STYLE as _europa_style, paint as _europa_paint
from .ganymede import STYLE as _ganymede_style, paint as _ganymede_paint
from .callisto import STYLE as _callisto_style, paint as _callisto_paint
from .titan import STYLE as _titan_style, paint as _titan_paint
from .enceladus import STYLE as _enceladus_style, paint as _enceladus_paint

# 风格名 → (STYLE, paint)
PLANET_MAP = {}

def _register(key, style, paint_fn):
    PLANET_MAP[key] = (style, paint_fn)

_register("sun",       _sun_style,       _sun_paint)
_register("mercury",   _mercury_style,   _mercury_paint)
_register("venus",     _venus_style,     _venus_paint)
_register("earth",     _earth_style,     _earth_paint)
_register("mars",      _mars_style,      _mars_paint)
_register("jupiter",   _jupiter_style,   _jupiter_paint)
_register("saturn",    _saturn_style,    _saturn_paint)
_register("uranus",    _uranus_style,    _uranus_paint)
_register("neptune",   _neptune_style,   _neptune_paint)
_register("pluto",     _pluto_style,     _pluto_paint)
_register("ceres",     _ceres_style,     _ceres_paint)
_register("eris",      _eris_style,      _eris_paint)
_register("makemake",  _makemake_style,  _makemake_paint)
_register("haumea",    _haumea_style,    _haumea_paint)
_register("moon",      _moon_style,      _moon_paint)
_register("io",        _io_style,        _io_paint)
_register("europa",    _europa_style,    _europa_paint)
_register("ganymede",  _ganymede_style,  _ganymede_paint)
_register("callisto",  _callisto_style,  _callisto_paint)
_register("titan",     _titan_style,     _titan_paint)
_register("enceladus", _enceladus_style, _enceladus_paint)
