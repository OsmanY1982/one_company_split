# -*- coding: utf-8 -*-
"""
中子星 — 极小极亮核心 + 强磁场线 + 高速旋转
"""
import math, random
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QConicalGradient,
    QColor, QPen, QBrush, QPainterPath
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
    core_r = radius * 0.2  # 中子星核心极小

    # ── 高速旋转辐射扇面 ──
    spin_angle = anim_t * 8.0  # 高速旋转
    for beam_i in range(2):
        beam_angle = spin_angle + beam_i * math.pi
        for j in range(3):
            cone = QConicalGradient(cx, cy, math.degrees(beam_angle) + 90 - j * 5)
            cone.setColorAt(0.0, QColor(255, 255, 255, 60 - j * 15))
            cone.setColorAt(0.02, QColor(200, 220, 255, 40 - j * 10))
            cone.setColorAt(0.05, QColor(100, 150, 255, 15))
            cone.setColorAt(0.15, QColor(255, 255, 255, 0))
            cone.setColorAt(0.5, QColor(255, 255, 255, 0))
            cone.setColorAt(0.85, QColor(255, 255, 255, 0))
            cone.setColorAt(0.95, QColor(100, 150, 255, 15))
            cone.setColorAt(0.98, QColor(200, 220, 255, 40 - j * 10))
            cone.setColorAt(1.0, QColor(255, 255, 255, 60 - j * 15))
            p.setBrush(cone); p.setPen(Qt.NoPen)
            beam_len = radius * (2.5 - j * 0.4)
            p.drawEllipse(QPointF(cx, cy), beam_len, beam_len)

    # ── 磁场线（偶极子场线投射到球面）──
    for i in range(16):
        field_angle = i / 16.0 * 2 * math.pi
        field_path = QPainterPath()
        start_r = core_r * 1.3
        start_x = cx + math.cos(field_angle) * start_r
        start_y = cy + math.sin(field_angle) * start_r
        field_path.moveTo(start_x, start_y)
        for j in range(5):
            frac = (j + 1) / 5.0
            r = core_r + (radius * 1.8 - core_r) * frac
            # 磁力线弯曲
            bend = math.sin(field_angle * 2) * radius * 0.3 * frac
            bx = cx + math.cos(field_angle + bend / radius) * r
            by = cy + math.sin(field_angle + bend / radius) * r
            field_path.lineTo(bx, by)
        fa = int(25 + 10 * abs(math.sin(field_angle * 2 + anim_t * 0.5)))
        pen = QPen(QColor(100, 200, 255, fa), 0.8)
        pen.setStyle(Qt.DotLine)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawPath(field_path)

    # ── 外部辉光（多层脉冲）──
    for i in range(4):
        glow_r = radius * (0.6 + i * 0.5)
        glow = QRadialGradient(cx, cy, glow_r)
        pulse = 0.7 + 0.3 * abs(math.sin(anim_t * 12.0 + i * 0.8))
        ga = int((60 - i * 12) * pulse)
        glow.setColorAt(0.0, QColor(200, 220, 255, ga))
        glow.setColorAt(0.3, QColor(150, 190, 255, ga // 2))
        glow.setColorAt(0.6, QColor(80, 140, 240, ga // 3))
        glow.setColorAt(0.85, QColor(30, 80, 200, ga // 5))
        glow.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(center, glow_r, glow_r)

    # ── 核心（超亮白色光球）──
    core_grad = QRadialGradient(cx, cy, core_r * 1.2)
    core_grad.setColorAt(0.0, QColor(255, 255, 255))
    core_grad.setColorAt(0.2, QColor(255, 250, 240))
    core_grad.setColorAt(0.5, QColor(220, 230, 255))
    core_grad.setColorAt(0.8, QColor(150, 190, 255))
    core_grad.setColorAt(1.0, QColor(80, 140, 240))
    p.setBrush(core_grad); p.setPen(Qt.NoPen)
    p.drawEllipse(center, core_r, core_r)

    # ── 核心高光点 ──
    core_highlight = QRadialGradient(cx - core_r * 0.15, cy - core_r * 0.15, core_r * 0.3)
    core_highlight.setColorAt(0.0, QColor(255, 255, 255, 220))
    core_highlight.setColorAt(0.5, QColor(255, 255, 255, 80))
    core_highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(core_highlight); p.setPen(Qt.NoPen)
    p.drawEllipse(center, core_r, core_r)

    # ── 吸积通道粒子（向核心螺旋坠落）──
    acc_rng = random.Random(int(anim_t * 350) % 100000 + 555)
    p.setPen(Qt.NoPen)
    for _ in range(30):
        aa = acc_rng.uniform(0, 2 * math.pi) + anim_t * 5.0
        ad = radius * (0.4 + 0.6 * acc_rng.random())
        ax = cx + math.cos(aa) * ad
        ay = cy + math.sin(aa) * ad
        asize = acc_rng.uniform(0.3, 1.2)
        ag = QRadialGradient(ax, ay, asize * 2.0)
        aa2 = acc_rng.randint(30, 100)
        ag.setColorAt(0.0, QColor(200, 230, 255, aa2))
        ag.setColorAt(0.5, QColor(130, 190, 255, aa2 // 2))
        ag.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(ag)
        p.drawEllipse(QPointF(ax, ay), asize * 2.0, asize * 2.0)

    # ── 边缘逆光（大气散射模拟 + 呼吸微动）──
    rim_breath = 1.0 + 0.03 * math.sin(anim_t * 2.2)
    rim_grad = QRadialGradient(cx + radius * 0.45, cy + radius * 0.50, radius * 0.50)
    rim_grad.setColorAt(0.0, QColor(255, 255, 255, 0))
    rim_grad.setColorAt(0.55, QColor(255, 255, 255, 0))
    rim_grad.setColorAt(0.78, QColor(180, 200, 255, int(15 * rim_breath)))
    rim_grad.setColorAt(0.92, QColor(140, 170, 255, int(30 * rim_breath)))
    rim_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(rim_grad); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

# ── 悬停增强（主题色脉冲光晕 + 呼吸轮廓）──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        # 内层主题光晕
        for i in range(3):
            ir = radius + 2 + i * 5
            ig = QRadialGradient(center, ir)
            ga = int((70 - i * 18) * hp)
            ig.setColorAt(0.60, QColor(255, 255, 255, 0))
            ig.setColorAt(0.78, QColor(150, 200, 255, ga // 2))
            ig.setColorAt(0.90, QColor(150, 200, 255, ga))
            ig.setColorAt(0.97, QColor(150//2, 200//2, 255, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(150, 200, 255, ga // 2))
            og.setColorAt(0.96, QColor(150//2, 200//2, 255, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(150, 200, 255, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)


    p.restore()
