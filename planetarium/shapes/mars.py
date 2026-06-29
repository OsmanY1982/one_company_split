# -*- coding: utf-8 -*-
"""
火星 — 红色氧化铁地表 + 极冠白色 + 沙尘暴粒子
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
    # ── 基底（火星红棕渐变）──
    base = QRadialGradient(cx - radius * 0.15, cy - radius * 0.15, radius * 1.1)
    base.setColorAt(0.0, QColor(235, 140, 80))
    base.setColorAt(0.35, QColor(200, 95, 45))
    base.setColorAt(0.65, QColor(165, 65, 30))
    base.setColorAt(0.85, QColor(130, 45, 20))
    base.setColorAt(1.0, QColor(90, 25, 10))
    p.setBrush(base); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 地表纹理（暗斑模拟陨石坑/高地）──
    tex_rng = random.Random(42)
    for _ in range(8):
        tx = cx + tex_rng.uniform(-radius * 0.72, radius * 0.72)
        ty = cy + tex_rng.uniform(-radius * 0.72, radius * 0.72)
        tr = radius * tex_rng.uniform(0.06, 0.18)
        if (tx - cx)**2 + (ty - cy)**2 < (radius * 0.8)**2:
            spot = QRadialGradient(tx, ty, tr)
            spot.setColorAt(0.0, QColor(150, 55, 20, 80))
            spot.setColorAt(0.6, QColor(160, 60, 25, 40))
            spot.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(spot); p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(tx, ty), tr, tr)

    # ── 陨石坑（小环）──
    for _ in range(6):
        crx = cx + tex_rng.uniform(-radius * 0.55, radius * 0.55)
        cry = cy + tex_rng.uniform(-radius * 0.55, radius * 0.55)
        crr = radius * tex_rng.uniform(0.04, 0.12)
        if (crx - cx)**2 + (cry - cy)**2 < (radius * 0.7)**2:
            p.setBrush(QColor(170, 70, 30, 50))
            p.setPen(QPen(QColor(120, 40, 15, 60), 1.0))
            p.drawEllipse(QPointF(crx, cry), crr, crr)

    # ── 极冠（顶部白色冰盖）──
    cap_path = QPainterPath()
    cap_path.moveTo(cx - radius * 0.45, cy - radius * 0.45)
    cap_path.quadTo(cx, cy - radius * 1.05, cx + radius * 0.45, cy - radius * 0.45)
    cap_path.quadTo(cx + radius * 0.15, cy - radius * 0.75, cx, cy - radius * 0.50)
    cap_path.quadTo(cx - radius * 0.15, cy - radius * 0.75, cx - radius * 0.45, cy - radius * 0.45)
    cap_grad = QRadialGradient(cx, cy - radius * 0.82, radius * 0.55)
    cap_grad.setColorAt(0.0, QColor(255, 255, 255, 200))
    cap_grad.setColorAt(0.5, QColor(240, 245, 250, 120))
    cap_grad.setColorAt(1.0, QColor(220, 230, 240, 0))
    p.setBrush(cap_grad); p.setPen(Qt.NoPen)
    p.drawPath(cap_path)

    # ── 大气薄层 ──
    atmo = QRadialGradient(cx, cy, radius * 1.05)
    atmo.setColorAt(0.0, QColor(255, 255, 255, 0))
    atmo.setColorAt(0.82, QColor(255, 255, 255, 0))
    atmo.setColorAt(0.92, QColor(255, 180, 140, 30))
    atmo.setColorAt(0.97, QColor(255, 150, 100, 15))
    atmo.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(atmo); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius * 1.05, radius * 1.05)

    # ── 沙尘暴粒子 ──
    storm_rng = random.Random(int(anim_t * 180) % 100000 + 1234)
    for _ in range(30):
        sa = storm_rng.uniform(0, 2 * math.pi)
        sd = radius * (0.3 + 0.7 * storm_rng.random())
        storm_angle = anim_t * 0.4 + storm_rng.uniform(0, 0.8)
        sx = cx + math.cos(sa + storm_angle) * sd
        sy = cy + math.sin(sa + storm_angle) * sd * 0.55
        ss = storm_rng.uniform(0.6, 2.2)
        sg = QRadialGradient(sx, sy, ss * 2.5)
        sa2 = storm_rng.randint(25, 80)
        sg.setColorAt(0.0, QColor(220, 160, 110, sa2))
        sg.setColorAt(0.5, QColor(200, 120, 80, sa2 // 2))
        sg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(sg); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(sx, sy), ss * 2.5, ss * 2.5)

    # ── 球面高光 ──
    highlight = QRadialGradient(cx - radius * 0.28, cy - radius * 0.30, radius * 0.35)
    highlight.setColorAt(0.0, QColor(255, 210, 170, 50))
    highlight.setColorAt(0.5, QColor(255, 180, 140, 15))
    highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(highlight); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

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
            ig.setColorAt(0.78, QColor(255, 140, 80, ga // 2))
            ig.setColorAt(0.90, QColor(255, 140, 80, ga))
            ig.setColorAt(0.97, QColor(255//2, 140//2, 110, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(255, 140, 80, ga // 2))
            og.setColorAt(0.96, QColor(255//2, 140//2, 120, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(255, 140, 80, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)


    p.restore()
