# `modules/astronomy/solar_system/planets/ceres/__init__.py`

> 路径：`modules/astronomy/solar_system/planets/ceres/__init__.py` | 行数：50


---


```python
# -*- coding: utf-8 -*-
"""谷神星（矮行星）— 冰岩混合、亮斑、水冰火山"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_label, _paint_hover_border, _paint_craters

STYLE = {
    "name": "谷神星", "type": "dwarf_planet",
    "band_colors": [
        (0.00, QColor(110, 105, 100)), (0.25, QColor(130, 125, 115)),
        (0.50, QColor(145, 140, 130)), (0.75, QColor(125, 120, 110)),
        (1.00, QColor(105, 100, 95)),
    ],
    "turbulence": 0.40, "feature_spots": 15,
    "atmosphere": QColor(200, 190, 180, 8), "craters": True,
}


def paint(p: QPainter, c: QPointF, r: float, hovered: bool,
          label: str, font_size: int, anim_t: float):
    import math, random
    _paint_surface(p, c, r, STYLE, anim_t)
    _paint_craters(p, c, r, anim_t * 0.6)

    # ── 特征亮斑 ──
    cx, cy = c.x(), c.y()
    from PyQt5.QtGui import QRadialGradient
    from PyQt5.QtCore import Qt
    random.seed(777)
    for _ in range(4):
        bx = cx + random.uniform(-r * 0.5, r * 0.5)
        by = cy + random.uniform(-r * 0.4, r * 0.4)
        br = random.uniform(0.03, 0.08) * r
        spot = QRadialGradient(QPointF(bx, by), br * 1.5)
        spot.setColorAt(0, QColor(255, 255, 245, 140))
        spot.setColorAt(0.4, QColor(240, 235, 220, 70))
        spot.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(spot)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(bx, by), br, br * 0.7)
    random.seed()

    _paint_atmosphere(p, c, r, STYLE)
    if hovered:
        from .._base import _paint_hover_glow
        _paint_hover_glow(p, c, r)
        _paint_hover_border(p, c, r)
    if label:
        _paint_label(p, c, r, label, font_size)

```
