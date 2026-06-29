# -*- coding: utf-8 -*-
"""
脉冲星 — 快速旋转中子星 + 辐射束脉冲闪烁 + 磁场线
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
    rot_speed = anim_t * 8.0  # 快速旋转

    # ── 外层射线辉光（脉冲明暗）──
    pulse = 0.3 + 0.7 * abs(math.sin(anim_t * 12.0))
    for i in range(3):
        gr = radius * (1.1 + i * 0.30)
        glow = QRadialGradient(cx, cy, gr)
        ga = int((50 - i * 14) * pulse)
        glow.setColorAt(0.0, QColor(180, 220, 255, 0))
        glow.setColorAt(0.4, QColor(120, 180, 255, ga))
        glow.setColorAt(0.7, QColor(60, 120, 240, ga // 2))
        glow.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(center, gr, gr)

    # ── 核心球体（炽白→蓝白渐变）──
    core = QRadialGradient(cx, cy, radius * 1.02)
    core.setColorAt(0.0, QColor(255, 255, 255))
    core.setColorAt(0.08, QColor(220, 240, 255))
    core.setColorAt(0.20, QColor(150, 200, 255))
    core.setColorAt(0.40, QColor(80, 140, 240))
    core.setColorAt(0.65, QColor(40, 80, 200))
    core.setColorAt(0.85, QColor(15, 40, 140))
    core.setColorAt(1.0, QColor(5, 15, 60))
    p.setBrush(core); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 自转纹理（圆锥渐变旋转带）──
    spin = QConicalGradient(cx, cy, rot_speed * 60)
    for i in range(6):
        pos = i / 6
        spin.setColorAt(pos, QColor(255, 255, 255, 20 if i % 2 == 0 else 40))
    p.setBrush(spin)
    p.drawEllipse(center, radius, radius)

    # ── 辐射束（两个锥形光束沿磁轴方向）──
    beam_angle = anim_t * 3.0  # 磁轴慢旋
    for sign in (-1, 1):
        for beam_i in range(3):
            beam_len = radius * (1.6 + beam_i * 0.35)
            beam_width = radius * (0.28 - beam_i * 0.07)
            beam_dir = beam_angle + math.pi * (1 if sign > 0 else 0)
            bx = cx + math.cos(beam_dir) * beam_len * 0.45
            by = cy + math.sin(beam_dir) * beam_len * 0.45

            beam = QPainterPath()
            perp = beam_dir + math.pi / 2
            bw = beam_width * (1.0 - beam_i * 0.25)
            start_x = cx + math.cos(perp) * bw * sign
            start_y = cy + math.sin(perp) * bw * sign
            beam.moveTo(start_x, start_y)

            tip_x = cx + math.cos(beam_dir) * beam_len
            tip_y = cy + math.sin(beam_dir) * beam_len
            beam.lineTo(tip_x, tip_y)
            beam.lineTo(cx - math.cos(perp) * bw * sign * 0.5,
                        cy - math.sin(perp) * bw * sign * 0.5)
            beam.closeSubpath()

            ba = int((80 - beam_i * 25) * pulse)
            bg = QRadialGradient(cx, cy, beam_len)
            bg.setColorAt(0.0, QColor(200, 230, 255, ba))
            bg.setColorAt(0.4, QColor(120, 180, 255, ba // 2))
            bg.setColorAt(0.8, QColor(60, 100, 220, ba // 4))
            bg.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(bg); p.setPen(Qt.NoPen)
            p.drawPath(beam)

    # ── 磁场线（弯曲双极线）──
    for sign in (-1, 1):
        for line_i in range(5):
            field_angle = beam_angle + sign * (0.15 + line_i * 0.22)
            field_len = radius * (1.5 + line_i * 0.15)
            field = QPainterPath()
            field.moveTo(cx, cy)
            cp1_x = cx + math.cos(field_angle) * field_len * 0.3
            cp1_y = cy + math.sin(field_angle) * field_len * 0.3
            ep_x = cx + math.cos(field_angle) * field_len * 0.55
            ep_y = cy + math.sin(field_angle) * field_len * 0.55
            cp2_x = cx + math.cos(field_angle - sign * 0.5) * field_len
            cp2_y = cy + math.sin(field_angle - sign * 0.5) * field_len
            ep2_x = cx + math.cos(field_angle - sign * 0.7) * field_len * 1.2
            ep2_y = cy + math.sin(field_angle - sign * 0.7) * field_len * 1.2
            field.cubicTo(cp1_x, cp1_y, cp2_x, cp2_y, ep2_x, ep2_y)
            fa = 20 + line_i * 3
            pen = QPen(QColor(150, 200, 255, fa), 0.7)
            pen.setStyle(Qt.DotLine if line_i % 2 == 0 else Qt.SolidLine)
            p.setPen(pen); p.setBrush(Qt.NoBrush)
            p.drawPath(field)

    # ── 表面闪烁热点 ──
    hot_rng = random.Random(int(anim_t * 500) % 100000 + 555)
    p.setPen(Qt.NoPen)
    for _ in range(10):
        ha = hot_rng.uniform(0, 2 * math.pi)
        hd = hot_rng.uniform(0.05, 0.90) * radius
        hx = cx + math.cos(ha) * hd
        hy = cy + math.sin(ha) * hd
        hs = hot_rng.uniform(0.3, 1.2)
        ha2 = int(60 + 120 * hot_rng.random())
        hg = QRadialGradient(hx, hy, hs * 2.0)
        hg.setColorAt(0.0, QColor(255, 255, 255, ha2))
        hg.setColorAt(0.4, QColor(200, 220, 255, ha2 // 2))
        hg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(hg)
        p.drawEllipse(QPointF(hx, hy), hs * 2.0, hs * 2.0)

    # ── 暗面叠加 ──
    shadow = QRadialGradient(cx, cy, radius * 1.6)
    shadow.setColorAt(0.0, QColor(255, 255, 255, 0))
    shadow.setColorAt(0.5, QColor(0, 0, 0, 20))
    shadow.setColorAt(0.7, QColor(0, 0, 0, 55))
    shadow.setColorAt(0.88, QColor(0, 0, 0, 130))
    shadow.setColorAt(1.0, QColor(0, 0, 0, 200))
    p.setBrush(shadow); p.setPen(Qt.NoPen); p.drawEllipse(center, radius, radius)
    # ── 暗面呼吸增强（微妙的亮度波动）──
    shadow_breath = QRadialGradient(cx, cy, radius * 0.72)
    sb = int(12 * abs(math.sin(anim_t * 1.7 + 0.5)))
    shadow_breath.setColorAt(0.0, QColor(0, 0, 0, 0))
    shadow_breath.setColorAt(0.5, QColor(0, 0, 0, sb))
    shadow_breath.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(shadow_breath); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 高光 ──
    spec = QRadialGradient(cx - radius * 0.30, cy - radius * 0.35, radius * 0.35)
    spec.setColorAt(0.0, QColor(255, 255, 255, 80))
    spec.setColorAt(0.3, QColor(255, 255, 255, 30))
    spec.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(spec); p.setPen(Qt.NoPen); p.drawEllipse(center, radius, radius)

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
