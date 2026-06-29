# `core/shapes/ghost_alien.py`

> 路径：`core/shapes/ghost_alien.py` | 行数：231


---


```python
# -*- coding: utf-8 -*-
"""
幽灵外星人 — 3D半透明飘浮斗篷体 + 多层透明度叠加 + 拖尾光带 + 空灵眼洞
"""
import math, random
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QLinearGradient,
    QColor, QPen, QBrush, QPainterPath
)


def paint(painter: QPainter, center: QPointF, radius: float,
          anim_t: float, hovered: bool, alpha: float):
    cx, cy = center.x(), center.y()
    p = painter
    p.save()
    if alpha < 1.0:
        p.setOpacity(alpha)

    s = radius / 50.0
    float_amp = 0.12
    float_y = math.sin(anim_t * 0.8) * radius * float_amp
    float_x = math.cos(anim_t * 0.65) * radius * float_amp * 0.5
    body_cx = cx + float_x
    body_cy = cy + float_y
    head_r = radius * 0.42

    # ── 远景：冷蓝扩散场 ──
    silhouette = QRadialGradient(body_cx, body_cy, radius * 1.2)
    silhouette.setColorAt(0.0, QColor(50, 180, 240, 15))
    silhouette.setColorAt(0.4, QColor(30, 120, 200, 8))
    silhouette.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(silhouette); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), radius * 1.2, radius * 1.2)

    # ── 拖尾光带（斗篷底部的流动性拖尾）──
    for i in range(4):
        tail_phase = anim_t + i * 0.18
        tail_offs = math.sin(tail_phase * 2.5) * radius * 0.15
        tail_x = body_cx + math.cos(tail_phase * 1.3 + i * 0.7) * radius * 0.25
        tail_bot = body_cy + radius * (0.45 + i * 0.10)
        tail_path = QPainterPath()
        tail_path.moveTo(tail_x - radius * 0.12, body_cy + radius * 0.35)
        tail_path.quadTo(tail_x + tail_offs, tail_bot - radius * 0.05,
                         tail_x + tail_offs * 0.5, tail_bot)
        tail_path.quadTo(tail_x, tail_bot - radius * 0.02,
                         tail_x + radius * 0.12, body_cy + radius * 0.35)
        tail_grad = QLinearGradient(tail_x, body_cy + radius * 0.35, tail_x + tail_offs * 0.5, tail_bot)
        tail_grad.setColorAt(0.0, QColor(100, 200, 235, 50))
        tail_grad.setColorAt(0.5, QColor(60, 150, 210, 25))
        tail_grad.setColorAt(1.0, QColor(10, 80, 160, 0))
        p.setBrush(tail_grad); p.setPen(Qt.NoPen)
        p.drawPath(tail_path)

    # ── 主要斗篷体（QPainterPath）──
    cloak_path = QPainterPath()
    cloak_top = body_cy - radius * 0.48
    cloak_mid = body_cy + radius * 0.05
    cloak_bot = body_cy + radius * 0.52
    cw_top = head_r * 0.55
    cw_mid = head_r * 0.95

    cloak_path.moveTo(body_cx + cw_top * 0.5, cloak_top + radius * 0.05)
    cloak_path.cubicTo(
        body_cx + cw_top, cloak_top,
        body_cx + cw_top * 0.7, cloak_top - radius * 0.02,
        body_cx, cloak_top - radius * 0.02
    )
    cloak_path.cubicTo(
        body_cx - cw_top * 0.7, cloak_top - radius * 0.02,
        body_cx - cw_top, cloak_top,
        body_cx - cw_top * 0.5, cloak_top + radius * 0.05
    )
    # 左侧飘带
    cloak_path.cubicTo(
        body_cx - cw_mid * 0.7, cloak_mid + radius * 0.05,
        body_cx - cw_mid * 0.65, cloak_bot - radius * 0.05,
        body_cx - radius * 0.28, cloak_bot + radius * 0.05
    )
    cloak_path.quadTo(body_cx, cloak_bot + radius * 0.28,
                      body_cx + radius * 0.28, cloak_bot + radius * 0.05)
    cloak_path.cubicTo(
        body_cx + cw_mid * 0.65, cloak_bot - radius * 0.05,
        body_cx + cw_mid * 0.7, cloak_mid + radius * 0.05,
        body_cx + cw_top * 0.5, cloak_top + radius * 0.05
    )
    cloak_path.closeSubpath()

    # ── 多层半透明叠加（alpha递减）──
    for layer in range(4):
        la = int((90 - layer * 20) * (0.7 + 0.3 * math.sin(anim_t * 1.5 + layer * 0.8)))
        cloak_grad = QRadialGradient(body_cx - radius * 0.08, body_cy - radius * 0.12,
                                      radius * (0.55 + layer * 0.12))
        cloak_grad.setColorAt(0.0, QColor(80, 200, 250, la))
        cloak_grad.setColorAt(0.35, QColor(55, 160, 220, int(la * 0.7)))
        cloak_grad.setColorAt(0.65, QColor(30, 110, 180, int(la * 0.4)))
        cloak_grad.setColorAt(0.85, QColor(15, 60, 130, int(la * 0.15)))
        cloak_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(cloak_grad); p.setPen(Qt.NoPen)
        p.drawPath(cloak_path)

    # 斗篷边缘发光
    edge_alpha = int(30 + 20 * math.sin(anim_t * 2.0))
    p.setPen(QPen(QColor(130, 220, 255, edge_alpha), 1.5 * s))
    p.setBrush(Qt.NoBrush)
    p.drawPath(cloak_path)

    # ── 中景实体：头部（悬浮球）──
    head_cx = body_cx
    head_cy = body_cy - radius * 0.22
    head_path = QPainterPath()
    head_path.addEllipse(QPointF(head_cx, head_cy), head_r, head_r * 0.85)

    head_grad = QRadialGradient(head_cx - head_r * 0.15, head_cy - head_r * 0.15, head_r * 1.1)
    head_grad.setColorAt(0.0, QColor(240, 250, 255, 170))
    head_grad.setColorAt(0.3, QColor(180, 225, 245, 140))
    head_grad.setColorAt(0.6, QColor(100, 180, 220, 100))
    head_grad.setColorAt(0.85, QColor(40, 100, 170, 50))
    head_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(head_grad); p.setPen(Qt.NoPen)
    p.drawPath(head_path)

    # 头部高光区（左上光源）
    head_hl = QRadialGradient(head_cx - head_r * 0.28, head_cy - head_r * 0.28, head_r * 0.35)
    head_hl.setColorAt(0.0, QColor(255, 255, 255, 80))
    head_hl.setColorAt(0.5, QColor(220, 240, 255, 30))
    head_hl.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(head_hl); p.setPen(Qt.NoPen)
    p.drawPath(head_path)

    # ── 眼睛：空洞黑洞 + 周围冷光 ──
    eye_spacing = head_r * 0.24
    eye_rx = head_r * 0.20
    eye_ry = head_r * 0.26
    pupil_scale = 0.68 + 0.06 * math.sin(anim_t * 1.3)

    for sign in (-1, 1):
        ex = head_cx + sign * eye_spacing
        ey = head_cy - head_r * 0.05

        # 周围冷光
        glow_eye = QRadialGradient(ex, ey, eye_rx * 1.5)
        glow_eye.setColorAt(0.0, QColor(120, 220, 255, 10))
        glow_eye.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(glow_eye); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, ey), eye_rx * 1.5, eye_ry * 1.5)

        # 眼洞（深黑渐变）
        eye_hole = QRadialGradient(ex, ey, eye_rx * 1.1)
        eye_hole.setColorAt(0.0, QColor(0, 0, 5, 220))
        eye_hole.setColorAt(0.4, QColor(2, 2, 10, 180))
        eye_hole.setColorAt(0.7, QColor(8, 8, 20, 100))
        eye_hole.setColorAt(1.0, QColor(30, 50, 80, 30))
        p.setBrush(eye_hole); p.setPen(QPen(QColor(40, 100, 180, 80), 0.8 * s))
        p.drawEllipse(QPointF(ex, ey), eye_rx, eye_ry)

        # 虹膜光环
        iris_rx = eye_rx * 0.55
        iris_ry = eye_ry * 0.55 * pupil_scale
        iris_grad = QRadialGradient(ex, ey, iris_rx * 1.2)
        iris_grad.setColorAt(0.0, QColor(20, 180, 240, 160))
        iris_grad.setColorAt(0.5, QColor(10, 100, 200, 100))
        iris_grad.setColorAt(1.0, QColor(0, 0, 50, 0))
        p.setBrush(iris_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, ey), iris_rx, iris_ry)

        # 瞳孔（更暗圆点）
        pup_r = iris_rx * 0.45 * pupil_scale
        p.setBrush(QColor(0, 0, 5, 240))
        p.drawEllipse(QPointF(ex, ey), pup_r, pup_r)

        # 微型光点
        p.setBrush(QColor(255, 255, 255, 180))
        p.drawEllipse(QPointF(ex - eye_rx * 0.25, ey - eye_ry * 0.28), pup_r * 0.25, pup_r * 0.28)

    # ── 嘴巴 ──
    mouth_path = QPainterPath()
    mouth_cx_ = body_cx
    mouth_cy_ = head_cy + head_r * 0.42
    mouth_path.moveTo(mouth_cx_ - head_r * 0.15, mouth_cy_ - head_r * 0.02)
    mouth_path.quadTo(mouth_cx_, mouth_cy_ + head_r * 0.10,
                      mouth_cx_ + head_r * 0.15, mouth_cy_ - head_r * 0.02)
    p.setPen(QPen(QColor(40, 120, 200, 100), 0.6 * s))
    p.setBrush(Qt.NoBrush)
    p.drawPath(mouth_path)

    # ── 粒子光环 ──
    aura_rng = random.Random(int(anim_t * 280) % 100000 + 29100)
    p.setPen(Qt.NoPen)
    for _ in range(22):
        a_angle = aura_rng.uniform(0, 2 * math.pi)
        a_dist = radius * (0.58 + 0.42 * aura_rng.random())
        a_offset = anim_t * (0.3 + 0.2 * aura_rng.random())
        ax = cx + math.cos(a_angle + a_offset) * a_dist
        ay = cy + math.sin(a_angle + a_offset) * a_dist * 0.7
        a_size = aura_rng.uniform(0.3, 1.8)
        a_alpha = aura_rng.randint(25, 70)
        ag = QRadialGradient(ax, ay, a_size * 2.5)
        ag.setColorAt(0.0, QColor(100, 210, 255, a_alpha))
        ag.setColorAt(0.5, QColor(40, 120, 220, a_alpha // 2))
        ag.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(ag)
        p.drawEllipse(QPointF(ax, ay), a_size * 2.5, a_size * 2.5)

    # ── hover 光晕（寒蓝主题）──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        for i in range(3):
            ir = radius + 2 + i * 5
            ig = QRadialGradient(center, ir)
            ga = int((70 - i * 18) * hp)
            ig.setColorAt(0.60, QColor(255, 255, 255, 0))
            ig.setColorAt(0.78, QColor(80, 200, 240, ga // 2))
            ig.setColorAt(0.90, QColor(80, 200, 240, ga))
            ig.setColorAt(0.97, QColor(30, 120, 200, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(80, 200, 240, ga // 2))
            og.setColorAt(0.96, QColor(30, 120, 200, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)

    p.restore()

```
