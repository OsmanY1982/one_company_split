# `core/modules/intelligence/solar_system_data/_core.py`

> 路径：`core/modules/intelligence/solar_system_data/_core.py` | 行数：32


---


```python
# -*- coding: utf-8 -*-
import math

KM_SCALE = 0.00384
ORBIT_BASE = 30

def km_to_px(orbit_km, zoom=1.0):
    return ORBIT_BASE + math.sqrt(max(orbit_km, 1)) * KM_SCALE * zoom

def radius_to_px(radius_km, zoom=1.0):
    if radius_km <= 0:
        return 1.0
    return max(0.8, math.log10(radius_km + 1) * 3.2 * zoom)

PLANET_PALETTE = {
    "jupiter": ["#e8c46a", "#d4a056", "#f5d78e", "#c8a040", "#b89050",
                "#dcc090", "#c0a870", "#e0d0a0", "#b8a060", "#d8b878"],
    "saturn":  ["#f5deb3", "#d4c090", "#e8d8b0", "#c8b880", "#f0e0c0",
                "#dcc8a0", "#e0d4b8", "#c4b490", "#ecdcc0", "#d0c0a0"],
    "uranus":  ["#80cbc4", "#60b8b0", "#90d8d0", "#70c0b8", "#a0ddd8",
                "#78c8c0", "#88d0c8", "#68b8b0", "#98d4d0", "#80c4c0"],
    "neptune": ["#42a5f5", "#3090e0", "#50b0ff", "#4098e8", "#60b8ff",
                "#3890e0", "#48a0f0", "#4090e0", "#58b0f8", "#48a0e8"],
    "mars":    ["#c08570", "#b07060", "#d09080", "#a06050", "#c88070"],
    "earth":   ["#bdbdbd"],
    "pluto":   ["#bcaaa4", "#c0b0a8", "#b8a8a0", "#c4b4ac", "#b0a098"],
    "dwarf":   ["#a09088", "#988880", "#a89890", "#908078", "#b0a098"],
}

def _moon_color(parent, idx):
    palette = PLANET_PALETTE.get(parent, PLANET_PALETTE["dwarf"])
    return palette[idx % len(palette)]

```
