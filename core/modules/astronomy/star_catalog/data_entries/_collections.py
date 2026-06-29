# -*- coding: utf-8 -*-
"""
天体条目集合 — PLANET_ENTRIES 和 MOON_ENTRIES
从子模块导入所有个体条目并构建合并字典。
"""

from ._sun import SUN_ENTRY
from ._planets import (
    MERCURY_ENTRY, VENUS_ENTRY, EARTH_ENTRY, MARS_ENTRY,
    JUPITER_ENTRY, SATURN_ENTRY, URANUS_ENTRY, NEPTUNE_ENTRY,
)
from ._dwarf_planets import (
    PLUTO_ENTRY, ERIS_ENTRY, CERES_ENTRY, HAUMEA_ENTRY, MAKEMAKE_ENTRY,
)
from ._moons_jupiter import MOON_GANYMEDE, MOON_CALLISTO, MOON_IO, MOON_EUROPA
from ._moons_saturn import MOON_TITAN, MOON_RHEA, MOON_IAPETUS, MOON_DIONE, MOON_TETHYS, MOON_ENCELADUS
from ._moons_uranus import MOON_TITANIA, MOON_OBERON, MOON_UMBRIEL, MOON_ARIEL, MOON_MIRANDA
from ._moons_neptune import MOON_TRITON, MOON_PROTEUS
from ._moons_earth import MOON_MOON
from ._moons_pluto import MOON_CHARON

# 13 个行星/矮行星详细条目 (合并)
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

# 19 颗大卫星详细条目 (key 为 name_en，通过 SOLAR_CATALOG 的 name_en 字段匹配，不依赖索引顺序)
MOON_ENTRIES = {
    "Ganymede":    MOON_GANYMEDE,   # 木卫三
    "Titan":       MOON_TITAN,      # 土卫六
    "Callisto":    MOON_CALLISTO,   # 木卫四
    "Io":          MOON_IO,         # 木卫一
    "Moon":        MOON_MOON,       # 月球
    "Europa":      MOON_EUROPA,     # 木卫二
    "Triton":      MOON_TRITON,     # 海卫一
    "Titania":     MOON_TITANIA,    # 天卫三
    "Rhea":        MOON_RHEA,       # 土卫五
    "Oberon":      MOON_OBERON,     # 天卫四
    "Iapetus":     MOON_IAPETUS,    # 土卫八
    "Charon":      MOON_CHARON,     # 冥卫一
    "Umbriel":     MOON_UMBRIEL,    # 天卫二
    "Ariel":       MOON_ARIEL,      # 天卫一
    "Dione":       MOON_DIONE,      # 土卫四
    "Tethys":      MOON_TETHYS,     # 土卫三
    "Enceladus":   MOON_ENCELADUS,  # 土卫二
    "Miranda":     MOON_MIRANDA,    # 天卫五
    "Proteus":     MOON_PROTEUS,    # 海卫八
}
