# `modules/astronomy/solar_system/planets/venus/__init__.py`

> 路径：`modules/astronomy/solar_system/planets/venus/__init__.py` | 行数：31


---


```python
# -*- coding: utf-8 -*-
"""金星"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_clouds, _paint_label, _paint_hover_border

STYLE = {
    "name": "金星", "type": "planet",
    "band_colors": [
        (0.00, QColor(240, 200, 110)), (0.15, QColor(250, 220, 140)),
        (0.30, QColor(230, 190, 100)), (0.45, QColor(245, 215, 130)),
        (0.60, QColor(225, 180, 95)),  (0.75, QColor(240, 210, 120)),
        (1.00, QColor(240, 200, 110)),
    ],
    "turbulence": 0.25, "feature_spots": 0, "clouds": True,
    "atmosphere": QColor(255, 220, 100, 60),
}


def paint(p: QPainter, c: QPointF, r: float, hovered: bool,
          label: str, font_size: int, anim_t: float):
    _paint_surface(p, c, r, STYLE, anim_t)
    _paint_clouds(p, c, r, anim_t)
    _paint_atmosphere(p, c, r, STYLE)
    if hovered:
        from .._base import _paint_hover_glow
        _paint_hover_glow(p, c, r)
        _paint_hover_border(p, c, r)
    if label:
        _paint_label(p, c, r, label, font_size)

```
