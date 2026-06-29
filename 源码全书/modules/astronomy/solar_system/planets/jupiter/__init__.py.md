# `modules/astronomy/solar_system/planets/jupiter/__init__.py`

> 路径：`modules/astronomy/solar_system/planets/jupiter/__init__.py` | 行数：36


---


```python
# -*- coding: utf-8 -*-
"""木星"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_label, _paint_hover_border

STYLE = {
    "name": "木星", "type": "planet",
    "band_colors": [
        (0.00, QColor(180, 140, 80)),  (0.06, QColor(210, 180, 110)),
        (0.12, QColor(190, 120, 50)),  (0.18, QColor(220, 190, 130)),
        (0.25, QColor(170, 110, 40)),  (0.32, QColor(200, 170, 100)),
        (0.40, QColor(160, 100, 35)),  (0.48, QColor(220, 200, 140)),
        (0.55, QColor(185, 130, 55)),  (0.62, QColor(200, 160, 90)),
        (0.70, QColor(170, 110, 40)),  (0.78, QColor(210, 180, 120)),
        (0.85, QColor(160, 95, 35)),   (0.92, QColor(195, 150, 80)),
        (1.00, QColor(180, 140, 80)),
    ],
    "turbulence": 0.18, "feature_spots": 5, "bands": True,
    "atmosphere": QColor(200, 150, 80, 40),
    "great_spot": {"y": 0.58, "x": 0.65, "w": 0.22, "h": 0.12,
                    "color": QColor(210, 80, 40, 200)},
}


def paint(p: QPainter, c: QPointF, r: float, hovered: bool,
          label: str, font_size: int, anim_t: float):
    _paint_surface(p, c, r, STYLE, anim_t)
    _paint_atmosphere(p, c, r, STYLE)
    if hovered:
        from .._base import _paint_hover_glow
        _paint_hover_glow(p, c, r)
        _paint_hover_border(p, c, r)
    if label:
        _paint_label(p, c, r, label, font_size)

```
