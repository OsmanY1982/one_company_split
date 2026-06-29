# `modules/astronomy/solar_system/planets/ganymede/__init__.py`

> 路径：`modules/astronomy/solar_system/planets/ganymede/__init__.py` | 行数：58


---


```python
# -*- coding: utf-8 -*-
"""加尼米德（木卫三）— 最大卫星、暗区/亮脊构造"""
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QRadialGradient

from .._base import _paint_surface, _paint_atmosphere, _paint_label, _paint_hover_border, _paint_craters

STYLE = {
    "name": "加尼米德", "type": "moon",
    "band_colors": [
        (0.00, QColor(140, 130, 120)), (0.20, QColor(160, 150, 135)),
        (0.45, QColor(200, 195, 185)), (0.70, QColor(150, 145, 130)),
        (1.00, QColor(130, 120, 110)),
    ],
    "turbulence": 0.30, "feature_spots": 12,
    "atmosphere": QColor(170, 160, 150, 6), "craters": True,
}


def paint(p: QPainter, c: QPointF, r: float, hovered: bool,
          label: str, font_size: int, anim_t: float):
    import math, random
    _paint_surface(p, c, r, STYLE, anim_t)
    _paint_craters(p, c, r, anim_t * 0.5)

    # 亮脊条纹
    cx, cy = c.x(), c.y()
    random.seed(666)
    p.save()
    from PyQt5.QtGui import QPainterPath
    cp = QPainterPath()
    cp.addEllipse(c, r, r)
    p.setClipPath(cp)
    for _ in range(10):
        sx = cx + random.uniform(-r * 0.5, r * 0.5)
        sy = cy + random.uniform(-r * 0.4, r * 0.4)
        angle = random.uniform(0, 2 * math.pi)
        length = random.uniform(0.2, 0.55) * r
        dx = math.cos(angle) * length
        dy = math.sin(angle) * length * 0.25
        pen = QPen(QColor(220, 210, 190, random.randint(20, 60)))
        pen.setWidth(max(1, int(r * 0.02)))
        p.setPen(pen)
        for j in range(4):
            off = j * r * 0.03
            px = sx + dy * 0.3 + off * 0.5
            py = sy + dx * 0.3 + off
            p.drawLine(QPointF(px, py), QPointF(px + dx, py + dy))
    p.restore()
    random.seed()

    _paint_atmosphere(p, c, r, STYLE)
    if hovered:
        from .._base import _paint_hover_glow, _paint_hover_border
        _paint_hover_glow(p, c, r)
        _paint_hover_border(p, c, r)
    if label:
        _paint_label(p, c, r, label, font_size)

```
