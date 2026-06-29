# -*- coding: utf-8 -*-
"""月球"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_label, _paint_hover_border, _paint_craters

STYLE = {
    "name": "月球", "type": "moon",
    "band_colors": [
        (0.00, QColor(180, 180, 185)), (0.20, QColor(200, 200, 205)),
        (0.40, QColor(160, 160, 165)), (0.60, QColor(190, 190, 195)),
        (0.80, QColor(170, 170, 175)), (1.00, QColor(180, 180, 185)),
    ],
    "turbulence": 0.35, "feature_spots": 50, "craters": True,
    "atmosphere": QColor(200, 200, 200, 5),
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
