# -*- coding: utf-8 -*-
"""土星 — 带光环"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_ring, _paint_label, _paint_hover_border

STYLE = {
    "name": "土星", "type": "planet",
    "band_colors": [
        (0.00, QColor(210, 190, 140)), (0.10, QColor(230, 210, 165)),
        (0.20, QColor(195, 170, 120)), (0.30, QColor(220, 200, 150)),
        (0.40, QColor(200, 175, 125)), (0.50, QColor(215, 195, 145)),
        (0.60, QColor(190, 165, 115)), (0.70, QColor(225, 205, 155)),
        (0.80, QColor(200, 175, 125)), (0.90, QColor(215, 195, 145)),
        (1.00, QColor(210, 190, 140)),
    ],
    "turbulence": 0.10,
}


def paint(p: QPainter, c: QPointF, r: float, hovered: bool,
          label: str, font_size: int, anim_t: float):
    _paint_ring(p, c, r, vertical=False)
    _paint_surface(p, c, r, STYLE, anim_t)
    _paint_atmosphere(p, c, r, {"atmosphere": QColor(220, 200, 150, 35)})
    if hovered:
        from .._base import _paint_hover_glow
        _paint_hover_glow(p, c, r)
        _paint_hover_border(p, c, r)
    if label:
        _paint_label(p, c, r, label, font_size)
