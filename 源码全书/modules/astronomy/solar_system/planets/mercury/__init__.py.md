# `modules/astronomy/solar_system/planets/mercury/__init__.py`

> 路径：`modules/astronomy/solar_system/planets/mercury/__init__.py` | 行数：30


---


```python
# -*- coding: utf-8 -*-
"""水星"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_label, _paint_hover_border, _paint_craters

STYLE = {
    "name": "水星", "type": "planet",
    "band_colors": [
        (0.00, QColor(140, 140, 145)), (0.20, QColor(160, 160, 165)),
        (0.40, QColor(120, 120, 125)), (0.60, QColor(150, 150, 155)),
        (0.80, QColor(130, 130, 135)), (1.00, QColor(140, 140, 145)),
    ],
    "turbulence": 0.30, "feature_spots": 40,
    "atmosphere": QColor(180, 180, 180, 10), "craters": True,
}


def paint(p: QPainter, c: QPointF, r: float, hovered: bool,
          label: str, font_size: int, anim_t: float):
    _paint_surface(p, c, r, STYLE, anim_t)
    _paint_craters(p, c, r, anim_t)
    _paint_atmosphere(p, c, r, STYLE)
    if hovered:
        from .._base import _paint_hover_glow
        _paint_hover_glow(p, c, r)
        _paint_hover_border(p, c, r)
    if label:
        _paint_label(p, c, r, label, font_size)

```
