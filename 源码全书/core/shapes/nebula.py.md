# `core/shapes/nebula.py`

> 路径：`core/shapes/nebula.py` | 行数：154


---


```python
# -*- coding: utf-8 -*-
"""
星云 — 不规则彩色气体团 + 缓慢流动 + 星光点缀
"""
import math, random
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QColor, QPen, QBrush, QPainterPath
)


def paint(painter: QPainter, center: QPointF, radius: float,
          anim_t: float, hovered: bool, alpha: float):
    cx, cy = center.x(), center.y()
    p = painter
    p.save()
    if alpha < 1.0:
        p.setOpacity(alpha)


    # ── 多层外辉光（增强质感）──
    for glow_layer in range(4):
        glow_scale = 1.06 + glow_layer * 0.20
        glow_r = radius * glow_scale
        glow = QRadialGradient(cx, cy, glow_r)
        ga = max(1, 35 - glow_layer * 8)
        glow.setColorAt(0.0, QColor(255, 255, 255, 0))
        glow.setColorAt(0.25, QColor(200, 200, 255, ga // 2))
        glow.setColorAt(0.55, QColor(120, 140, 255, ga))
        glow.setColorAt(0.80, QColor(60, 80, 200, ga // 2))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(center, glow_r, glow_r)
    # ── 基底暗空背景 ──
    bg = QRadialGradient(cx, cy, radius * 1.4)
    bg.setColorAt(0.0, QColor(10, 5, 25))
    bg.setColorAt(0.8, QColor(5, 3, 15))
    bg.setColorAt(1.0, QColor(0, 0, 0))
    p.setBrush(bg); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius * 1.4, radius * 1.4)

    # ── 气体团（多层不规则软边缘色块）──
    gas_colors = [
        QColor(180, 60, 180, 60),   # 紫
        QColor(60, 130, 220, 55),   # 蓝
        QColor(220, 80, 140, 50),   # 粉
        QColor(80, 200, 180, 40),   # 青
        QColor(240, 100, 50, 35),   # 橙
        QColor(140, 50, 200, 40),   # 紫蓝
    ]
    nebula_rng = random.Random(12345)
    for layer in range(5):
        for i in range(6 + layer * 2):
            gx = cx + nebula_rng.uniform(-radius * 0.9, radius * 0.9)
            gy = cy + nebula_rng.uniform(-radius * 0.9, radius * 0.9)
            gr = radius * nebula_rng.uniform(0.15, 0.55)
            # 缓慢飘移
            drift_x = math.sin(anim_t * 0.3 + i * 1.3) * radius * 0.06
            drift_y = math.cos(anim_t * 0.25 + i * 0.9) * radius * 0.06
            gx += drift_x
            gy += drift_y
            gc = gas_colors[(i + layer) % len(gas_colors)]
            ggrad = QRadialGradient(gx, gy, gr)
            ggrad.setColorAt(0.0, gc)
            ggrad.setColorAt(0.4, QColor(gc.red(), gc.green(), gc.blue(), gc.alpha() // 2))
            ggrad.setColorAt(0.7, QColor(gc.red(), gc.green(), gc.blue(), gc.alpha() // 4))
            ggrad.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(ggrad); p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(gx, gy), gr, gr * nebula_rng.uniform(0.6, 1.0))

    # ── 气体纤维（丝状结构）──
    for _ in range(12):
        fib_rng = random.Random(nebula_rng.randint(1, 99999))
        fib_path = QPainterPath()
        fx = cx + fib_rng.uniform(-radius * 0.7, radius * 0.7)
        fy = cy + fib_rng.uniform(-radius * 0.7, radius * 0.7)
        fib_path.moveTo(fx, fy)
        for j in range(6):
            frac = (j + 1) / 6.0
            nx = fx + fib_rng.uniform(-radius * 0.4, radius * 0.4)
            ny = fy + math.sin(anim_t * 0.2 + j) * radius * 0.08
            # 保持在球内
            if (nx - cx)**2 + (ny - cy)**2 < radius**2:
                fib_path.lineTo(nx, ny)
            fx, fy = nx, ny
        fa = fib_rng.randint(15, 45)
        fb = fib_rng.choice([QColor(200, 100, 200, fa), QColor(100, 180, 240, fa),
                             QColor(240, 120, 100, fa)])
        pen = QPen(fb, 1.2)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawPath(fib_path)

    # ── 星光（明亮锐利点）──
    star_rng = random.Random(int(anim_t * 50) % 100000 + 2222)
    for _ in range(25):
        sa = star_rng.uniform(0, 2 * math.pi)
        sd = radius * star_rng.uniform(0.1, 1.0)
        sx = cx + math.cos(sa) * sd
        sy = cy + math.sin(sa) * sd
        ss = star_rng.uniform(0.5, 2.0)
        # 星芒十字闪烁
        twinkle = 0.5 + 0.5 * abs(math.sin(anim_t * star_rng.uniform(3.0, 7.0)))
        # 星光晕
        sg = QRadialGradient(sx, sy, ss * 3.0)
        sa2 = int(80 + 120 * twinkle)
        sg.setColorAt(0.0, QColor(255, 255, 255, sa2))
        sg.setColorAt(0.15, QColor(200, 220, 255, sa2 // 2))
        sg.setColorAt(0.4, QColor(100, 150, 240, sa2 // 4))
        sg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(sg); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(sx, sy), ss * 3.0, ss * 3.0)
        # 十字芒
        cross_pen = QPen(QColor(255, 255, 255, int(80 * twinkle)), 0.6)
        p.setPen(cross_pen)
        cross_len = ss * 2.5
        p.drawLine(QPointF(sx - cross_len, sy), QPointF(sx + cross_len, sy))
        p.drawLine(QPointF(sx, sy - cross_len), QPointF(sx, sy + cross_len))
        p.setPen(Qt.NoPen)

        # ── 悬停增强（主题色脉冲光晕 + 呼吸轮廓）──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        # 内层主题光晕
        for i in range(3):
            ir = radius + 2 + i * 5
            ig = QRadialGradient(center, ir)
            ga = int((70 - i * 18) * hp)
            ig.setColorAt(0.60, QColor(255, 255, 255, 0))
            ig.setColorAt(0.78, QColor(180, 100, 220, ga // 2))
            ig.setColorAt(0.90, QColor(180, 100, 220, ga))
            ig.setColorAt(0.97, QColor(180//2, 100//2, 250, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(180, 100, 220, ga // 2))
            og.setColorAt(0.96, QColor(180//2, 100//2, 255, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(180, 100, 220, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)


    p.restore()

```
