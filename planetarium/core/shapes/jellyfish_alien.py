# -*- coding: utf-8 -*-
"""
水母外星人 — 3D半透明凝胶伞盖 + 多层透明度叠加 + 发光触手贝塞尔摆动 + 脉冲光核
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
    float_y = math.sin(anim_t * 1.1) * radius * 0.08
    float_x = math.cos(anim_t * 0.9) * radius * 0.05
    body_cx = cx + float_x
    body_cy = cy + float_y
    head_r = radius * 0.48

    # ── 远景：粉色能量场 ──
    silhouette = QRadialGradient(body_cx, body_cy, radius * 1.12)
    silhouette.setColorAt(0.0, QColor(255, 100, 180, 18))
    silhouette.setColorAt(0.4, QColor(200, 50, 160, 8))
    silhouette.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(silhouette); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), radius * 1.12, radius * 1.12)

    # ── 触手（12条贝塞尔弹性摆动）──
    tentacle_rng = random.Random(17)
    tentacles = []
    for i in range(12):
        base_angle = -math.pi / 2 + (i - 5.5) * math.pi / 14
        length = radius * tentacle_rng.uniform(0.60, 0.90)
        thickness = radius * tentacle_rng.uniform(0.02, 0.06)
        swing_phase = tentacle_rng.uniform(0, 2 * math.pi)
        swing_freq = tentacle_rng.uniform(1.5, 3.0)
        tentacles.append((base_angle, length, thickness, swing_phase, swing_freq))

    for base_angle, length, thickness, swing_phase, swing_freq in tentacles:
        swing = math.sin(anim_t * swing_freq + swing_phase) * radius * 0.15
        swing2 = math.cos(anim_t * swing_freq * 1.6 + swing_phase + 0.8) * radius * 0.08
        start_x = body_cx + math.cos(base_angle) * head_r * 0.50
        start_y = body_cy + head_r * 0.25

        tent_path = QPainterPath()
        tent_path.moveTo(start_x, start_y)
        cp1_x = start_x + math.cos(base_angle) * length * 0.20 + swing * 0.2
        cp1_y = start_y + length * 0.35
        cp2_x = start_x + math.cos(base_angle) * length * 0.55 + swing * 0.6
        cp2_y = start_y + length * 0.65
        tip_x = start_x + math.cos(base_angle) * length * 0.80 + swing + swing2 * 0.5
        tip_y = start_y + length * 0.90
        tent_path.cubicTo(cp1_x, cp1_y, cp2_x, cp2_y, tip_x, tip_y)

        # 触手发光渐变（粉色→紫→青）
        tent_grad = QLinearGradient(start_x, start_y, tip_x, tip_y)
        tent_grad.setColorAt(0.0, QColor(255, 100, 190, 160))
        tent_grad.setColorAt(0.4, QColor(200, 60, 220, 130))
        tent_grad.setColorAt(0.7, QColor(100, 80, 240, 100))
        tent_grad.setColorAt(1.0, QColor(40, 120, 230, 60))
        pen = QPen(QBrush(tent_grad), thickness)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawPath(tent_path)

        # 触手内层发光线（模拟凝胶光管）
        inner_pen = QPen(QColor(255, 220, 255, 30), thickness * 0.35)
        inner_pen.setCapStyle(Qt.RoundCap)
        p.setPen(inner_pen)
        p.drawPath(tent_path)

        # 触手末端发光小泡
        tip_glow = QRadialGradient(tip_x, tip_y, thickness * 1.5)
        tip_glow.setColorAt(0.0, QColor(255, 180, 240, 180))
        tip_glow.setColorAt(0.5, QColor(200, 100, 230, 80))
        tip_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen); p.setBrush(tip_glow)
        p.drawEllipse(QPointF(tip_x, tip_y), thickness * 1.5, thickness * 1.5)

        # 触手微吸盘（隔一段放一个荧光点）
        for seg_t in [0.2, 0.5, 0.8]:
            sx = start_x + math.cos(base_angle) * length * seg_t + swing * seg_t
            sy = start_y + length * seg_t
            sucker_grad = QRadialGradient(sx, sy, thickness * 1.2)
            sucker_grad.setColorAt(0.0, QColor(255, 160, 240, 90))
            sucker_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setBrush(sucker_grad); p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(sx, sy), thickness * 1.2, thickness * 1.2)

    # ── 伞盖：多层半透明椭圆叠加（alpha递减）──
    for layer in range(5):
        if layer == 0:
            # 底层暗面
            dome_grad = QRadialGradient(body_cx, body_cy + head_r * 0.1, head_r * 1.1)
            dome_grad.setColorAt(0.0, QColor(180, 50, 180, 40))
            dome_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        else:
            la = int((120 - layer * 22) * (0.65 + 0.35 * math.sin(anim_t * 1.8 + layer * 0.7)))
            dome_grad = QRadialGradient(body_cx - head_r * 0.08, body_cy - head_r * 0.15,
                                         head_r * (0.85 + layer * 0.04))
            dome_grad.setColorAt(0.0, QColor(255, 150, 220, la))
            dome_grad.setColorAt(0.25, QColor(240, 100, 200, int(la * 0.8)))
            dome_grad.setColorAt(0.55, QColor(200, 60, 180, int(la * 0.5)))
            dome_grad.setColorAt(0.8, QColor(130, 40, 160, int(la * 0.2)))
            dome_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(dome_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(body_cx, body_cy), head_r, head_r * 0.78)

    # 伞盖边缘勾勒
    dome_edge_grad = QRadialGradient(body_cx, body_cy - head_r * 0.05, head_r * 1.05)
    dome_edge_grad.setColorAt(0.0, QColor(255, 200, 230, 0))
    dome_edge_grad.setColorAt(0.82, QColor(255, 130, 210, 0))
    dome_edge_grad.setColorAt(0.88, QColor(255, 130, 210, 30))
    dome_edge_grad.setColorAt(0.92, QColor(200, 80, 180, 15))
    dome_edge_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(dome_edge_grad); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), head_r, head_r * 0.78)

    # 伞盖顶部高光
    dome_spec = QRadialGradient(body_cx - head_r * 0.25, body_cy - head_r * 0.30, head_r * 0.38)
    dome_spec.setColorAt(0.0, QColor(255, 230, 255, 60))
    dome_spec.setColorAt(0.5, QColor(255, 190, 240, 20))
    dome_spec.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(dome_spec); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), head_r, head_r * 0.78)

    # ── 内部神经束（6条辐射状脉络，从伞盖中心向下）──
    for i in range(6):
        nerve_angle = -math.pi / 2 + (i - 2.5) * math.pi / 7
        nerve_path = QPainterPath()
        nx0 = body_cx
        ny0 = body_cy - head_r * 0.15
        nerve_path.moveTo(nx0, ny0)
        for t_frac in [0.15, 0.35, 0.55, 0.75]:
            nx = nx0 + math.cos(nerve_angle + math.sin(anim_t * 2 + i) * 0.05) * head_r * 0.6 * t_frac
            ny = ny0 + head_r * 0.55 * t_frac
            nerve_path.lineTo(nx, ny)
        nerve_alpha = int(40 + 30 * abs(math.sin(anim_t * 1.5 + i * 1.1)))
        p.setPen(QPen(QColor(255, 140, 220, nerve_alpha), 0.7 * s))
        p.setBrush(Qt.NoBrush)
        p.drawPath(nerve_path)

    # ── 核心脉冲光点（伞盖中心）──
    core_pulse = 0.5 + 0.5 * math.sin(anim_t * 5.0)
    for layer in range(3):
        lr = head_r * (0.06 + layer * 0.06)
        la = int((80 - layer * 24) * core_pulse)
        core_glow = QRadialGradient(body_cx, body_cy - head_r * 0.15, lr)
        core_glow.setColorAt(0.0, QColor(255, 220, 255, la))
        core_glow.setColorAt(0.5, QColor(255, 140, 220, int(la * 0.5)))
        core_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(core_glow); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(body_cx, body_cy - head_r * 0.15), lr, lr)
    p.setBrush(QColor(255, 240, 255, int(220 * core_pulse)))
    p.drawEllipse(QPointF(body_cx, body_cy - head_r * 0.15), head_r * 0.03, head_r * 0.03)

    # ── 粒子光环 ──
    aura_rng = random.Random(int(anim_t * 280) % 100000 + 707)
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
        ag.setColorAt(0.0, QColor(255, 120, 200, a_alpha))
        ag.setColorAt(0.5, QColor(150, 60, 220, a_alpha // 2))
        ag.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(ag)
        p.drawEllipse(QPointF(ax, ay), a_size * 2.5, a_size * 2.5)

    # ── hover 光晕（粉紫主题）──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        for i in range(3):
            ir = radius + 2 + i * 5
            ig = QRadialGradient(center, ir)
            ga = int((70 - i * 18) * hp)
            ig.setColorAt(0.60, QColor(255, 255, 255, 0))
            ig.setColorAt(0.78, QColor(255, 120, 200, ga // 2))
            ig.setColorAt(0.90, QColor(255, 120, 200, ga))
            ig.setColorAt(0.97, QColor(150, 60, 180, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(255, 120, 200, ga // 2))
            og.setColorAt(0.96, QColor(150, 60, 180, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)

    p.restore()
