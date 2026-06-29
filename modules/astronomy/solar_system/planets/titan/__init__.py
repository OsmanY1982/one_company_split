# -*- coding: utf-8 -*-
"""泰坦（土卫六）— 浓密橙黄大气、甲烷湖泊"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_label, _paint_hover_border

STYLE = {
    "name": "泰坦", "type": "moon",
    "band_colors": [
        (0.00, QColor(210, 170, 90)), (0.30, QColor(225, 190, 110)),
        (0.60, QColor(200, 160, 80)), (1.00, QColor(190, 150, 70)),
    ],
    "turbulence": 0.20, "feature_spots": 10,
    "atmosphere": QColor(255, 180, 60, 50),
}


def paint(p: QPainter, c: QPointF, r: float, hovered: bool,
          label: str, font_size: int, anim_t: float):
    import math, random
    _paint_surface(p, c, r, STYLE, anim_t)

    # 浓密大气层（多层橙色雾）
    cx, cy = c.x(), c.y()
    for i in range(4):
        scale = 1.10 + i * 0.07
        alpha = 60 - i * 12
        from PyQt5.QtGui import QRadialGradient
        from PyQt5.QtCore import Qt
        atmos = QRadialGradient(c, r * scale)
        atmos.setColorAt(0, QColor(0, 0, 0, 0))
        atmos.setColorAt(0.6, QColor(255, 160, 40, alpha))
        atmos.setColorAt(0.85, QColor(255, 140, 20, alpha // 2))
        atmos.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(atmos)
        p.setPen(Qt.NoPen)
        p.drawEllipse(c, r * scale, r * scale)

    if hovered:
        from .._base import _paint_hover_glow, _paint_hover_border
        _paint_hover_glow(p, c, r)
        _paint_hover_border(p, c, r)
    if label:
        _paint_label(p, c, r, label, font_size)
