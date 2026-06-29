# `modules/astronomy/solar_system/renderer.py`

> 路径：`modules/astronomy/solar_system/renderer.py` | 行数：67


---


```python
# -*- coding: utf-8 -*-
"""
太阳系渲染调度器 — 组合所有星球文件，统一对外接口
"""
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainter

# 直接使用 planets/__init__.py 的 PLANET_MAP 路由
from .planets import PLANET_MAP as _PLANET_MAP

# 收集所有 STYLE
PLANET_STYLES = {k: v[0] for k, v in _PLANET_MAP.items()}


def paint_planet(painter: QPainter, center: QPointF, radius: float,
                 style: dict, hovered: bool = False, label: str = "",
                 font_size: int = 9, anim_t: float = 0.0):
    """路由到对应星球模块"""
    for key, (sty, paint_fn) in _PLANET_MAP.items():
        if sty is style:
            paint_fn(painter, center, radius, hovered, label, font_size, anim_t)
            return

    # 回退：用基础渲染
    from .planets._base import (_paint_surface, _paint_atmosphere,
                                 _paint_label, _paint_hover_border)
    _paint_surface(painter, center, radius, style, anim_t)
    _paint_atmosphere(painter, center, radius, style)
    if hovered:
        from .planets._base import _paint_hover_glow
        _paint_hover_glow(painter, center, radius * 1.15)
        _paint_hover_border(painter, center, radius * 1.15)
    if label:
        _paint_label(painter, center, radius * 1.15, label, font_size)


# ═══════════════════════════════════════════
# 星云背景（共用）
# ═══════════════════════════════════════════
import random
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QRadialGradient, QColor

_NEBULAE = []
_rng = random.Random(42)
for _ in range(5):
    _NEBULAE.append((
        _rng.uniform(0.05, 0.95), _rng.uniform(0.05, 0.95),
        _rng.uniform(0.15, 0.40), _rng.uniform(0.10, 0.30),
        [QColor(30, 20, 80, 15), QColor(20, 50, 80, 12), QColor(60, 20, 20, 10)][_rng.randint(0, 2)],
    ))
del _rng


def paint_nebula(p: QPainter, width: int, height: int):
    for nx, ny, nw, nh, nc in _NEBULAE:
        cx = int(width * nx)
        cy = int(height * ny)
        rw = int(width * nw)
        rh = int(height * nh)
        grad = QRadialGradient(QPointF(cx, cy), max(rw, rh))
        grad.setColorAt(0, nc)
        grad.setColorAt(0.5, QColor(nc.red(), nc.green(), nc.blue(), nc.alpha() // 3))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy), rw, rh)

```
