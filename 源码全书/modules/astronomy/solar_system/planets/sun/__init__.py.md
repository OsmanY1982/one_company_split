# `modules/astronomy/solar_system/planets/sun/__init__.py`

> 路径：`modules/astronomy/solar_system/planets/sun/__init__.py` | 行数：68


---


```python
# -*- coding: utf-8 -*-
"""太阳 — 恒星"""
import math, random
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QRadialGradient, QLinearGradient, QColor, QPen, QBrush

from .._base import _lerp_color, _noise_1d, _band_interpolate, _paint_atmosphere

STYLE = {
    "name": "太阳", "type": "star",
    "band_colors": [
        (0.00, QColor(255, 240, 80)),  (0.08, QColor(255, 200, 30)),
        (0.16, QColor(255, 180, 20)),  (0.25, QColor(255, 220, 60)),
        (0.35, QColor(255, 160, 10)),  (0.45, QColor(255, 210, 50)),
        (0.55, QColor(255, 170, 25)),  (0.65, QColor(255, 230, 70)),
        (0.75, QColor(255, 150, 10)),  (0.85, QColor(255, 200, 40)),
        (1.00, QColor(255, 240, 80)),
    ],
    "turbulence": 0.12, "feature_spots": 30, "glow": True,
    "atmosphere": QColor(255, 180, 30, 60),
}


def paint(p: QPainter, c: QPointF, r: float, hovered: bool,
          label: str, font_size: int, anim_t: float):
    from .._base import _paint_surface, _paint_label, _paint_hover_border
    _paint_surface(p, c, r, STYLE, anim_t)
    _paint_sun_glow(p, c, r, anim_t)
    _paint_atmosphere(p, c, r, STYLE)
    if hovered:
        _paint_hover_border(p, c, r)
    if label:
        _paint_label(p, c, r, label, font_size)


def _paint_sun_glow(p: QPainter, c: QPointF, r: float, anim_t: float):
    cx, cy = c.x(), c.y()
    for i in range(4):
        scale = 1.2 + i * 0.3
        pulse = 1.0 + 0.05 * math.sin(anim_t * 1.5 + i)
        sr = r * scale * pulse
        glow = QRadialGradient(c, sr)
        glow.setColorAt(0, QColor(255, 180, 30, 50 - i * 10))
        glow.setColorAt(0.3, QColor(255, 140, 20, 25 - i * 6))
        glow.setColorAt(0.6, QColor(255, 80, 10, 10 - i * 3))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(glow)
        p.setPen(Qt.NoPen)
        p.drawEllipse(c, sr, sr)
    p.save()
    random.seed(42)
    for i in range(12):
        angle = anim_t * 0.3 + i * (2 * math.pi / 12)
        ray_len = r * random.uniform(1.3, 1.8)
        ray = QLinearGradient(
            cx + r * 0.9 * math.cos(angle), cy + r * 0.9 * math.sin(angle),
            cx + ray_len * math.cos(angle), cy + ray_len * math.sin(angle),
        )
        ray.setColorAt(0, QColor(255, 200, 50, 40))
        ray.setColorAt(1, QColor(255, 100, 10, 0))
        pen = QPen(QBrush(ray), 2)
        p.setPen(pen)
        p.drawLine(
            QPointF(cx + r * 1.05 * math.cos(angle), cy + r * 1.05 * math.sin(angle)),
            QPointF(cx + ray_len * math.cos(angle), cy + ray_len * math.sin(angle)),
        )
    random.seed()
    p.restore()

```
