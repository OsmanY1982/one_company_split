# `iqra/solar_explorer/body_data_entries.py`

> 路径：`iqra/solar_explorer/body_data_entries.py` | 行数：71


---


```python
# -*- coding: utf-8 -*-
"""
天体百科数据 — Solar System Encyclopedia
33 颗主要天体的详细中文科普介绍（太阳+9行星+5矮行星+19大卫星）
数据来源：NASA、ESA、JAXA 公开资料

原始单体文件已于 2026-06-24 拆分为按天体类别分组的子模块：
  _sun.py        — 太阳
  _planets.py    — 八大行星
  _dwarf_planets.py — 五颗矮行星
  _moons.py      — 19 颗大卫星

本文件为向后兼容的重导出模块。
"""

# ── 从子模块导入所有常量 ──
from solar_explorer._sun import SUN_ENTRY
from solar_explorer._planets import (
    MERCURY_ENTRY, VENUS_ENTRY, EARTH_ENTRY, MARS_ENTRY,
    JUPITER_ENTRY, SATURN_ENTRY, URANUS_ENTRY, NEPTUNE_ENTRY,
)
from solar_explorer._dwarf_planets import (
    PLUTO_ENTRY, CERES_ENTRY, ERIS_ENTRY, MAKEMAKE_ENTRY, HAUMEA_ENTRY,
)
from solar_explorer._moons import (
    MOON_GANYMEDE, MOON_TITAN, MOON_CALLISTO, MOON_IO,
    MOON_MOON, MOON_EUROPA, MOON_TRITON, MOON_TITANIA,
    MOON_RHEA, MOON_OBERON, MOON_IAPETUS, MOON_CHARON,
    MOON_UMBRIEL, MOON_ARIEL, MOON_DIONE, MOON_TETHYS,
    MOON_ENCELADUS, MOON_MIRANDA, MOON_PROTEUS,
)

# ── 聚合字典（供 body_encyclopedia.py 等使用者） ──
PLANET_ENTRIES = {
    "sun": SUN_ENTRY,
    "mercury": MERCURY_ENTRY,
    "venus": VENUS_ENTRY,
    "earth": EARTH_ENTRY,
    "mars": MARS_ENTRY,
    "jupiter": JUPITER_ENTRY,
    "saturn": SATURN_ENTRY,
    "uranus": URANUS_ENTRY,
    "neptune": NEPTUNE_ENTRY,
    "pluto": PLUTO_ENTRY,
    "eris": ERIS_ENTRY,
    "ceres": CERES_ENTRY,
    "haumea": HAUMEA_ENTRY,
    "makemake": MAKEMAKE_ENTRY,
}

MOON_ENTRIES = {
    "jupiter_moon_2": MOON_GANYMEDE,
    "saturn_moon_5": MOON_TITAN,
    "jupiter_moon_3": MOON_CALLISTO,
    "jupiter_moon_0": MOON_IO,
    "earth_moon_0": MOON_MOON,
    "jupiter_moon_1": MOON_EUROPA,
    "neptune_moon_0": MOON_TRITON,
    "uranus_moon_2": MOON_TITANIA,
    "saturn_moon_7": MOON_RHEA,
    "uranus_moon_3": MOON_OBERON,
    "saturn_moon_2": MOON_IAPETUS,
    "pluto_moon_0": MOON_CHARON,
    "uranus_moon_1": MOON_UMBRIEL,
    "uranus_moon_0": MOON_ARIEL,
    "saturn_moon_3": MOON_DIONE,
    "saturn_moon_0": MOON_TETHYS,
    "saturn_moon_1": MOON_ENCELADUS,
    "uranus_moon_4": MOON_MIRANDA,
    "neptune_moon_7": MOON_PROTEUS,
}

```
