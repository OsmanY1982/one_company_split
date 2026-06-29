# `core/modules/astronomy/star_catalog/data_entries/__init__.py`

> 路径：`core/modules/astronomy/star_catalog/data_entries/__init__.py` | 行数：38


---


```python
# -*- coding: utf-8 -*-
"""
天体百科数据 — Solar System Encyclopedia
33 颗主要天体的详细中文科普介绍（太阳+9行星+5矮行星+19大卫星）
数据来源：NASA、ESA、JAXA 公开资料

拆分为子模块：
- _sun.py: 太阳条目
- _planets.py: 八大行星条目
- _dwarf_planets.py: 五颗矮行星条目
- _moons_jupiter.py: 木星卫星（4颗）
- _moons_saturn.py: 土星卫星（6颗）
- _moons_uranus.py: 天王星卫星（5颗）
- _moons_neptune.py: 海王星卫星（2颗）
- _moons_earth.py: 地球卫星（1颗）
- _moons_pluto.py: 冥王星卫星（1颗）
- _collections.py: 合并集合
"""

from ._collections import PLANET_ENTRIES, MOON_ENTRIES

# 单独导出所有 MOON_* 常量，支持 from data_entries import MOON_TITAN 等直接引用
from ._moons_jupiter import MOON_GANYMEDE, MOON_CALLISTO, MOON_IO, MOON_EUROPA
from ._moons_saturn import MOON_TITAN, MOON_RHEA, MOON_IAPETUS, MOON_DIONE, MOON_TETHYS, MOON_ENCELADUS
from ._moons_uranus import MOON_TITANIA, MOON_OBERON, MOON_UMBRIEL, MOON_ARIEL, MOON_MIRANDA
from ._moons_neptune import MOON_TRITON, MOON_PROTEUS
from ._moons_earth import MOON_MOON
from ._moons_pluto import MOON_CHARON

__all__ = [
    "PLANET_ENTRIES", "MOON_ENTRIES",
    "MOON_GANYMEDE", "MOON_CALLISTO", "MOON_IO", "MOON_EUROPA",
    "MOON_TITAN", "MOON_RHEA", "MOON_IAPETUS", "MOON_DIONE", "MOON_TETHYS", "MOON_ENCELADUS",
    "MOON_TITANIA", "MOON_OBERON", "MOON_UMBRIEL", "MOON_ARIEL", "MOON_MIRANDA",
    "MOON_TRITON", "MOON_PROTEUS",
    "MOON_MOON",
    "MOON_CHARON",
]

```
