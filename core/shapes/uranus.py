# -*- coding: utf-8 -*-
"""
天王星 — 淡青绿 + 侧躺自转轴 + 细环
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
    # ── 细环（极细、淡色，侧躺轴意味着环视角接近正面）──
    ring_axis_angle = 0.25 * math.pi  # 侧躺 ~45度
    ring_inner = radius * 1.18
    ring_outer = radius * 1.35
    p.save()
    p.translate(cx, cy)
    p.rotate(math.degrees(ring_axis_angle))
    for j in range(30):
        frac = j / 30.0
        r = ring_inner + (ring_outer - ring_inner) * frac
        da = int(50 - 40 * abs(frac - 0.5) * 2)
        rc = QColor(140, 200, 210, da)
        p.setBrush(rc); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(0, 0), r, r * 0.008)
    p.restore()

    # ── 环上粒子 ──
    ring_rng = random.Random(int(anim_t * 170) % 100000 + 999)
    p.save()
    p.translate(cx, cy)
    p.rotate(math.degrees(ring_axis_angle))
    p.setPen(Qt.NoPen)
    for _ in range(15):
        ra = ring_rng.uniform(0, 2 * math.pi)
        rd = ring_rng.uniform(ring_inner, ring_outer)
        rx = math.cos(ra) * rd
        ry = math.sin(ra) * rd
        rg = QRadialGradient(rx, ry, 1.5)
        rg.setColorAt(0.0, QColor(180, 230, 240, 60))
        rg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(rg)
        p.drawEllipse(QPointF(rx, ry), 1.5, 1.5)
    p.restore()

    # ── 球体（淡青绿渐变）──
    sphere = QRadialGradient(cx - radius * 0.12, cy - radius * 0.1, radius * 1.02)
    sphere.setColorAt(0.0, QColor(185, 235, 230))
    sphere.setColorAt(0.3, QColor(145, 210, 210))
    sphere.setColorAt(0.6, QColor(100, 180, 190))
    sphere.setColorAt(0.85, QColor(60, 140, 155))
    sphere.setColorAt(1.0, QColor(30, 100, 115))
    p.setBrush(sphere); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 垂直云带（侧躺旋转轴，云带接近水平）──
    for band_i in range(8):
        band_y = cy - radius * 0.65 + radius * 1.3 * band_i / 7.0
        dx = radius * math.sqrt(max(0, 1 - ((band_y - cy) / radius) ** 2))
        if dx > 0:
            band_alpha = int(20 + 20 * abs(math.sin(band_i * 1.7 + anim_t * 0.15)))
            p.setPen(QPen(QColor(120, 190, 195, band_alpha), radius * 0.05))
            p.setBrush(Qt.NoBrush)
            band_path = QPainterPath()
            band_path.moveTo(cx - dx, band_y)
            band_path.lineTo(cx + dx, band_y)
            p.drawPath(band_path)

    # ── 高光 ──
    highlight = QRadialGradient(cx - radius * 0.2, cy - radius * 0.25, radius * 0.3)
    highlight.setColorAt(0.0, QColor(210, 245, 245, 50))
    highlight.setColorAt(0.5, QColor(180, 230, 230, 15))
    highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(highlight); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 薄大气光晕 ──
    atmo = QRadialGradient(cx, cy, radius * 1.08)
    atmo.setColorAt(0.0, QColor(255, 255, 255, 0))
    atmo.setColorAt(0.8, QColor(255, 255, 255, 0))
    atmo.setColorAt(0.92, QColor(140, 220, 225, 20))
    atmo.setColorAt(0.97, QColor(100, 190, 200, 10))
    atmo.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(atmo); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius * 1.08, radius * 1.08)

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
            ig.setColorAt(0.78, QColor(140, 220, 225, ga // 2))
            ig.setColorAt(0.90, QColor(140, 220, 225, ga))
            ig.setColorAt(0.97, QColor(140//2, 220//2, 255, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(140, 220, 225, ga // 2))
            og.setColorAt(0.96, QColor(140//2, 220//2, 255, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(140, 220, 225, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)


    p.restore()
