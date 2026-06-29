# `modules/astronomy/solar_system/planets/uranus/__init__.py`

> 路径：`modules/astronomy/solar_system/planets/uranus/__init__.py` | 行数：30


---


```python
# -*- coding: utf-8 -*-
"""天王星 — 竖环"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_ring, _paint_label, _paint_hover_border

STYLE = {
    "name": "天王星", "type": "planet",
    "band_colors": [
        (0.00, QColor(60, 180, 170)), (0.15, QColor(80, 200, 190)),
        (0.30, QColor(50, 160, 150)), (0.45, QColor(75, 190, 180)),
        (0.60, QColor(55, 170, 160)), (0.75, QColor(70, 185, 175)),
        (1.00, QColor(60, 180, 170)),
    ],
    "turbulence": 0.12,
}


def paint(p: QPainter, c: QPointF, r: float, hovered: bool,
          label: str, font_size: int, anim_t: float):
    _paint_ring(p, c, r, vertical=True)
    _paint_surface(p, c, r, STYLE, anim_t)
    _paint_atmosphere(p, c, r, {"atmosphere": QColor(100, 220, 200, 40)})
    if hovered:
        from .._base import _paint_hover_glow
        _paint_hover_glow(p, c, r)
        _paint_hover_border(p, c, r)
    if label:
        _paint_label(p, c, r, label, font_size)

```
