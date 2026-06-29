# -*- coding: utf-8 -*-
"""恩克拉多斯（土卫二）— 纯白高反照率冰壳、南极羽流"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_label, _paint_hover_border

STYLE = {
    "name": "恩克拉多斯", "type": "moon",
    "band_colors": [
        (0.00, QColor(235, 238, 242)), (0.30, QColor(245, 247, 250)),
        (0.60, QColor(240, 243, 247)), (1.00, QColor(230, 233, 238)),
    ],
    "turbulence": 0.05, "feature_spots": 2,
    "atmosphere": QColor(200, 210, 230, 15),
}


def paint(p: QPainter, c: QPointF, r: float, hovered: bool,
          label: str, font_size: int, anim_t: float):
    import math, random
    _paint_surface(p, c, r, STYLE, anim_t)

    # 虎纹裂缝
    cx, cy = c.x(), c.y()
    random.seed(888)
    p.save()
    from PyQt5.QtGui import QPainterPath, QPen
    from PyQt5.QtCore import Qt
    cp = QPainterPath()
    cp.addEllipse(c, r, r)
    p.setClipPath(cp)
    for _ in range(4):
        tx = cx + random.uniform(-r * 0.3, r * 0.3)
        ty = cy - r * 0.5 + random.uniform(-r * 0.15, r * 0.15)
        length = r * 0.7
        pen = QPen(QColor(120, 140, 180, random.randint(60, 130)))
        pen.setWidth(max(1, int(r * 0.02)))
        p.setPen(pen)
        p.drawLine(QPointF(tx - length / 2, ty), QPointF(tx + length / 2, ty))
    p.restore()
    random.seed()

    _paint_atmosphere(p, c, r, STYLE)
    if hovered:
        from .._base import _paint_hover_glow, _paint_hover_border
        _paint_hover_glow(p, c, r)
        _paint_hover_border(p, c, r)
    if label:
        _paint_label(p, c, r, label, font_size)
