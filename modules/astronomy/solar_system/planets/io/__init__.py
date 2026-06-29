# -*- coding: utf-8 -*-
"""伊奥（木卫一）— 硫火山、横纹、熔岩斑"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter, QColor

from .._base import _paint_surface, _paint_atmosphere, _paint_label, _paint_hover_border

STYLE = {
    "name": "伊奥", "type": "moon",
    "band_colors": [
        (0.00, QColor(200, 170, 40)), (0.15, QColor(230, 200, 60)),
        (0.35, QColor(180, 140, 20)), (0.55, QColor(220, 190, 50)),
        (0.75, QColor(170, 130, 30)), (1.00, QColor(190, 160, 40)),
    ],
    "turbulence": 0.35, "feature_spots": 30,
    "atmosphere": QColor(255, 220, 60, 18),
    "bands": True,
}


def paint(p: QPainter, c: QPointF, r: float, hovered: bool,
          label: str, font_size: int, anim_t: float):
    import math, random
    _paint_surface(p, c, r, STYLE, anim_t)

    # ── 火山热点 ──
    cx, cy = c.x(), c.y()
    random.seed(444)
    for _ in range(12):
        hx = cx + random.uniform(-r * 0.75, r * 0.75)
        hy = cy + random.uniform(-r * 0.65, r * 0.65)
        hr = random.uniform(0.03, 0.10) * r
        from PyQt5.QtGui import QRadialGradient
        from PyQt5.QtCore import Qt
        hot = QRadialGradient(QPointF(hx, hy), hr * 1.8)
        hot.setColorAt(0, QColor(255, 100, 20, 160))
        hot.setColorAt(0.3, QColor(220, 60, 10, 100))
        hot.setColorAt(0.7, QColor(180, 30, 5, 40))
        hot.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(hot)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(hx, hy), hr, hr)
    random.seed()

    _paint_atmosphere(p, c, r, STYLE)
    if hovered:
        from .._base import _paint_hover_glow, _paint_hover_border
        _paint_hover_glow(p, c, r)
        _paint_hover_border(p, c, r)
    if label:
        _paint_label(p, c, r, label, font_size)
