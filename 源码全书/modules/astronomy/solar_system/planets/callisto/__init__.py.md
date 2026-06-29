# `modules/astronomy/solar_system/planets/callisto/__init__.py`

> 路径：`modules/astronomy/solar_system/planets/callisto/__init__.py` | 行数：31


---


```python
# -*- coding: utf-8 -*-
"""卡利斯托（木卫四）— 古老密集撞击坑、暗色表面"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_label, _paint_hover_border, _paint_craters

STYLE = {
    "name": "卡利斯托", "type": "moon",
    "band_colors": [
        (0.00, QColor(100, 95, 90)), (0.30, QColor(115, 110, 105)),
        (0.60, QColor(105, 100, 95)), (1.00, QColor(90, 85, 80)),
    ],
    "turbulence": 0.25, "feature_spots": 0,
    "atmosphere": QColor(80, 75, 70, 4), "craters": True,
}


def paint(p: QPainter, c: QPointF, r: float, hovered: bool,
          label: str, font_size: int, anim_t: float):
    _paint_surface(p, c, r, STYLE, anim_t)
    # 额外大量撞击坑
    _paint_craters(p, c, r, anim_t * 0.7)

    _paint_atmosphere(p, c, r, STYLE)
    if hovered:
        from .._base import _paint_hover_glow, _paint_hover_border
        _paint_hover_glow(p, c, r)
        _paint_hover_border(p, c, r)
    if label:
        _paint_label(p, c, r, label, font_size)

```
