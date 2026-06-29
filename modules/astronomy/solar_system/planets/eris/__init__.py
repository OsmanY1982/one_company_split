# -*- coding: utf-8 -*-
"""阋神星（矮行星）— 极亮高反照率甲烷冰壳"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_label, _paint_hover_border

STYLE = {
    "name": "阋神星", "type": "dwarf_planet",
    "band_colors": [
        (0.00, QColor(230, 225, 220)), (0.30, QColor(240, 238, 235)),
        (0.60, QColor(250, 248, 245)), (1.00, QColor(225, 220, 215)),
    ],
    "turbulence": 0.08, "feature_spots": 3,
    "atmosphere": QColor(220, 210, 200, 12),
}


def paint(p: QPainter, c: QPointF, r: float, hovered: bool,
          label: str, font_size: int, anim_t: float):
    _paint_surface(p, c, r, STYLE, anim_t)
    _paint_atmosphere(p, c, r, STYLE)
    if hovered:
        from .._base import _paint_hover_glow, _paint_hover_border
        _paint_hover_glow(p, c, r)
        _paint_hover_border(p, c, r)
    if label:
        _paint_label(p, c, r, label, font_size)
