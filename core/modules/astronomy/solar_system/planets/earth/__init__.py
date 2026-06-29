# -*- coding: utf-8 -*-
"""地球"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_clouds, _paint_label, _paint_hover_border

STYLE = {
    "name": "地球", "type": "planet",
    "band_colors": [
        (0.00, QColor(20, 40, 120)),   (0.08, QColor(15, 60, 160)),
        (0.18, QColor(25, 90, 200)),   (0.25, QColor(30, 70, 140)),
        (0.32, QColor(40, 130, 90)),   (0.38, QColor(30, 100, 60)),
        (0.45, QColor(50, 150, 40)),   (0.50, QColor(180, 160, 50)),
        (0.55, QColor(40, 130, 30)),   (0.60, QColor(25, 90, 180)),
        (0.68, QColor(20, 70, 200)),   (0.75, QColor(180, 160, 50)),
        (0.82, QColor(30, 120, 60)),   (0.90, QColor(15, 60, 170)),
        (1.00, QColor(20, 40, 120)),
    ],
    "turbulence": 0.25, "feature_spots": 8, "clouds": True,
    "atmosphere": QColor(80, 160, 255, 45),
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
