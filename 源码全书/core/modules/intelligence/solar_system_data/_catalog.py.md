# `core/modules/intelligence/solar_system_data/_catalog.py`

> 路径：`core/modules/intelligence/solar_system_data/_catalog.py` | 行数：82


---


```python
# -*- coding: utf-8 -*-
from ._core import _moon_color
from ._data import (
    PLANETS, DWARFS,
    MOONS_EARTH, MOONS_MARS, MOONS_JUPITER, MOONS_SATURN,
    MOONS_URANUS, MOONS_NEPTUNE, MOONS_PLUTO,
    MOONS_ERIS, MOONS_HAUMEA, MOONS_MAKEMAKE,
)


def build_catalog():
    catalog = {}

    catalog["sun"] = {
        "id": "sun", "name": "太阳", "parent": None, "type": "star",
        "orbit_km": 0, "radius_km": 696340, "period_d": 0,
        "style": "sun", "ring": False, "tier": 0,
    }

    for pid, name, orbit, radius, period, style, ring in PLANETS:
        catalog[pid] = {
            "id": pid, "name": name, "parent": "sun", "type": "planet",
            "orbit_km": orbit, "radius_km": radius, "period_d": period,
            "style": style, "ring": ring, "tier": 0,
        }

    for did, name, orbit, radius, period, style, ring in DWARFS:
        catalog[did] = {
            "id": did, "name": name, "parent": "sun", "type": "dwarf",
            "orbit_km": orbit, "radius_km": radius, "period_d": period,
            "style": style, "ring": ring, "tier": 0,
        }

    _add_moons(catalog, MOONS_EARTH,   "earth",   "earth")
    _add_moons(catalog, MOONS_MARS,    "mars",    "mars")
    _add_moons(catalog, MOONS_JUPITER, "jupiter", "jupiter")
    _add_moons(catalog, MOONS_SATURN,  "saturn",  "saturn")
    _add_moons(catalog, MOONS_URANUS,  "uranus",  "uranus")
    _add_moons(catalog, MOONS_NEPTUNE, "neptune", "neptune")
    _add_moons(catalog, MOONS_PLUTO,   "pluto",   "pluto")
    _add_moons(catalog, MOONS_ERIS,    "eris",    "dwarf")
    _add_moons(catalog, MOONS_HAUMEA,  "haumea",  "dwarf")
    _add_moons(catalog, MOONS_MAKEMAKE,"makemake","dwarf")

    return catalog


def _add_moons(catalog, moon_list, parent_id, palette_key):
    for i, (name_cn, name_en, orbit, radius, period) in enumerate(moon_list):
        mid = f"{parent_id}_moon_{i}"
        color = _moon_color(palette_key, i)
        if radius >= 500:
            tier = 1
        elif radius >= 50:
            tier = 2
        else:
            tier = 3
        catalog[mid] = {
            "id": mid, "name": name_cn, "name_en": name_en,
            "parent": parent_id, "type": "moon",
            "orbit_km": orbit, "radius_km": radius, "period_d": period,
            "style": None, "color": color, "ring": False, "tier": tier,
        }


SOLAR_CATALOG = build_catalog()


def total_count():
    return len(SOLAR_CATALOG)


def get_children(parent_id):
    return [b for b in SOLAR_CATALOG.values() if b["parent"] == parent_id]


def get_body(body_id):
    return SOLAR_CATALOG.get(body_id)


def all_bodies():
    return list(SOLAR_CATALOG.values())

```
