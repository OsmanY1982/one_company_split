# -*- coding: utf-8 -*-
"""冥王星"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_label, _paint_hover_border, _paint_craters

STYLE = {
    "name": "冥王星", "type": "dwarf",
    "band_colors": [
        (0.00, QColor(180, 150, 130)), (0.25, QColor(200, 170, 150)),
        (0.50, QColor(160, 130, 110)), (0.75, QColor(190, 160, 140)),
        (1.00, QColor(180, 150, 130)),
    ],
    "turbulence": 0.28, "feature_spots": 25, "craters": True,
    "atmosphere": QColor(180, 160, 140, 15),
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
