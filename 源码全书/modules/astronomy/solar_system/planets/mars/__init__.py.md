# `modules/astronomy/solar_system/planets/mars/__init__.py`

> 路径：`modules/astronomy/solar_system/planets/mars/__init__.py` | 行数：32


---


```python
# -*- coding: utf-8 -*-
"""火星"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_label, _paint_hover_border, _paint_craters

STYLE = {
    "name": "火星", "type": "planet",
    "band_colors": [
        (0.00, QColor(180, 70, 30)),   (0.12, QColor(210, 100, 45)),
        (0.25, QColor(160, 55, 20)),   (0.38, QColor(200, 90, 40)),
        (0.50, QColor(170, 60, 25)),   (0.62, QColor(195, 85, 35)),
        (0.75, QColor(150, 50, 20)),   (0.88, QColor(190, 80, 35)),
        (1.00, QColor(180, 70, 30)),
    ],
    "turbulence": 0.22, "feature_spots": 15, "craters": True,
    "atmosphere": QColor(255, 120, 40, 18),
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
