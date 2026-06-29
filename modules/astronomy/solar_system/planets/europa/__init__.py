# -*- coding: utf-8 -*-
"""欧罗巴（木卫二）— 冰壳、线性裂缝、冰下海洋"""
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QRadialGradient

from .._base import _paint_surface, _paint_atmosphere, _paint_label, _paint_hover_border

STYLE = {
    "name": "欧罗巴", "type": "moon",
    "band_colors": [
        (0.00, QColor(210, 215, 220)), (0.25, QColor(225, 230, 235)),
        (0.50, QColor(240, 242, 245)), (0.75, QColor(220, 225, 230)),
        (1.00, QColor(200, 205, 210)),
    ],
    "turbulence": 0.12, "feature_spots": 5,
    "atmosphere": QColor(180, 190, 210, 10),
}


def paint(p: QPainter, c: QPointF, r: float, hovered: bool,
          label: str, font_size: int, anim_t: float):
    import math, random
    _paint_surface(p, c, r, STYLE, anim_t)

    # 线性裂缝（lineae）
    cx, cy = c.x(), c.y()
    random.seed(555)
    p.save()
    clip_path = __import__('PyQt5.QtGui', fromlist=['QPainterPath']).QPainterPath()
    from PyQt5.QtGui import QPainterPath
    cp = QPainterPath()
    cp.addEllipse(c, r, r)
    p.setClipPath(cp)
    for _ in range(18):
        lx = cx + random.uniform(-r * 0.7, r * 0.7)
        ly = cy + random.uniform(-r * 0.7, r * 0.7)
        angle = random.uniform(0, 2 * math.pi)
        length = random.uniform(0.3, 0.9) * r
        dx = math.cos(angle) * length
        dy = math.sin(angle) * length * 0.3
        pen = QPen(QColor(160, 120, 80, random.randint(30, 80)))
        pen.setWidth(max(1, int(r * 0.015)))
        p.setPen(pen)
        p.drawLine(QPointF(lx, ly), QPointF(lx + dx, ly + dy))
    p.restore()
    random.seed()

    _paint_atmosphere(p, c, r, STYLE)
    if hovered:
        from .._base import _paint_hover_glow, _paint_hover_border
        _paint_hover_glow(p, c, r)
        _paint_hover_border(p, c, r)
    if label:
        _paint_label(p, c, r, label, font_size)
