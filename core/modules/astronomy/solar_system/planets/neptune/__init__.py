# -*- coding: utf-8 -*-
"""海王星"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_clouds, _paint_label, _paint_hover_border

STYLE = {
    "name": "海王星", "type": "planet",
    "band_colors": [
        (0.00, QColor(25, 35, 130)),   (0.15, QColor(40, 60, 170)),
        (0.30, QColor(30, 50, 150)),   (0.45, QColor(45, 75, 190)),
        (0.60, QColor(30, 45, 140)),   (0.75, QColor(50, 80, 200)),
        (1.00, QColor(25, 35, 130)),
    ],
    "turbulence": 0.15, "feature_spots": 3, "clouds": True,
    "atmosphere": QColor(80, 130, 255, 45),
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
