# `iqra/solar_explorer/__init__.py`

> 路径：`iqra/solar_explorer/__init__.py` | 行数：20


---


```python
# -*- coding: utf-8 -*-
"""
太阳系科普板块 · SOLAR EXPLORER
星谱目录 | 天体详情 | 语音朗读
"""
__version__ = "1.0.0"

# ── 从拆分后的子模块统一导出所有天体常量 ──
from solar_explorer.body_data_entries import (
    SUN_ENTRY,
    MERCURY_ENTRY, VENUS_ENTRY, EARTH_ENTRY, MARS_ENTRY,
    JUPITER_ENTRY, SATURN_ENTRY, URANUS_ENTRY, NEPTUNE_ENTRY,
    PLUTO_ENTRY, CERES_ENTRY, ERIS_ENTRY, MAKEMAKE_ENTRY, HAUMEA_ENTRY,
    MOON_GANYMEDE, MOON_TITAN, MOON_CALLISTO, MOON_IO,
    MOON_MOON, MOON_EUROPA, MOON_TRITON, MOON_TITANIA,
    MOON_RHEA, MOON_OBERON, MOON_IAPETUS, MOON_CHARON,
    MOON_UMBRIEL, MOON_ARIEL, MOON_DIONE, MOON_TETHYS,
    MOON_ENCELADUS, MOON_MIRANDA, MOON_PROTEUS,
    PLANET_ENTRIES, MOON_ENTRIES,
)

```
