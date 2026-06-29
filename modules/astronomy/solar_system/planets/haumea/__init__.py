# -*- coding: utf-8 -*-
"""妊神星（矮行星）— 三轴椭球水冰壳+暗红斑"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_label, _paint_hover_border

STYLE = {
    "name": "妊神星", "type": "dwarf_planet",
    "band_colors": [
        (0.00, QColor(200, 210, 220)), (0.30, QColor(220, 225, 235)),
        (0.60, QColor(210, 220, 230)), (1.00, QColor(190, 200, 210)),
    ],
    "turbulence": 0.20, "feature_spots": 6,
    "atmosphere": QColor(180, 190, 200, 6),
}


def paint(p: QPainter, c: QPointF, r: float, hovered: bool,
          label: str, font_size: int, anim_t: float):
    import math, random
    _paint_surface(p, c, r, STYLE, anim_t)

    # 暗红斑
    cx, cy = c.x(), c.y()
    random.seed(333)
    dsx = cx + random.uniform(-r * 0.25, r * 0.25)
    dsy = cy + random.uniform(-r * 0.2, r * 0.2)
    from PyQt5.QtGui import QRadialGradient
    from PyQt5.QtCore import Qt
    spot = QRadialGradient(QPointF(dsx, dsy), r * 0.35)
    spot.setColorAt(0, QColor(120, 60, 40, 80))
    spot.setColorAt(0.5, QColor(100, 50, 30, 40))
    spot.setColorAt(1, QColor(0, 0, 0, 0))
    p.setBrush(spot)
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(dsx, dsy), r * 0.35, r * 0.25)
    random.seed()

    # 拉伸椭球形状（极扁）
    p.save()
    p.translate(cx, cy)
    p.scale(0.55, 1.0)
    p.translate(-cx, -cy)
    _paint_atmosphere(p, c, r, STYLE)
    p.restore()

    if hovered:
        from .._base import _paint_hover_glow, _paint_hover_border
        _paint_hover_glow(p, c, r)
        _paint_hover_border(p, c, r)
    if label:
        _paint_label(p, c, r, label, font_size)
