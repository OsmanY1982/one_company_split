# -*- coding: utf-8 -*-
"""
水星 — 灰色陨石坑密布 + 无大气 + 高反差明暗
"""
import math, random
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QColor, QPen, QBrush
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
    # ── 基底（灰白→深灰，高反差明暗）──
    base = QRadialGradient(cx - radius * 0.05, cy - radius * 0.05, radius * 1.02)
    base.setColorAt(0.0, QColor(200, 200, 205))
    base.setColorAt(0.25, QColor(170, 170, 175))
    base.setColorAt(0.45, QColor(130, 130, 135))
    base.setColorAt(0.65, QColor(90, 90, 95))
    base.setColorAt(0.82, QColor(55, 55, 60))
    base.setColorAt(0.94, QColor(30, 30, 35))
    base.setColorAt(1.0, QColor(15, 15, 18))
    p.setBrush(base); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 陨石坑（大量密集小坑 + 偶见大坑）──
    crater_rng = random.Random(17)
    for _ in range(35):
        crx = cx + crater_rng.uniform(-radius * 0.88, radius * 0.88)
        cry = cy + crater_rng.uniform(-radius * 0.88, radius * 0.88)
        crr = radius * crater_rng.uniform(0.02, 0.10)
        if (crx - cx)**2 + (cry - cy)**2 > (radius * 0.92)**2:
            continue
        # 坑内暗色
        in_grad = QRadialGradient(crx, cry - crr * 0.1, crr)
        in_grad.setColorAt(0.0, QColor(60, 60, 65, 120))
        in_grad.setColorAt(0.7, QColor(100, 100, 105, 60))
        in_grad.setColorAt(1.0, QColor(160, 160, 165, 10))
        p.setBrush(in_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(crx, cry), crr, crr)
        # 坑缘高亮（迎着光的一侧）
        rim_alpha = crater_rng.randint(30, 70)
        rim_grad = QRadialGradient(crx - crr * 0.2, cry - crr * 0.25, crr * 0.7)
        rim_grad.setColorAt(0.0, QColor(210, 210, 215, rim_alpha))
        rim_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(rim_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(crx, cry), crr * 1.15, crr * 1.15)

    # ── 大号陨石坑（3-5个显著的大型撞击坑）──
    big_crater_rng = random.Random(29)
    for _ in range(4):
        bx = cx + big_crater_rng.uniform(-radius * 0.50, radius * 0.50)
        by = cy + big_crater_rng.uniform(-radius * 0.50, radius * 0.50)
        br = radius * big_crater_rng.uniform(0.12, 0.22)
        if (bx - cx)**2 + (by - cy)**2 > (radius * 0.65)**2:
            continue
        # 大坑暗底
        bg = QRadialGradient(bx, by - br * 0.08, br)
        bg.setColorAt(0.0, QColor(40, 40, 44, 160))
        bg.setColorAt(0.5, QColor(70, 70, 74, 100))
        bg.setColorAt(1.0, QColor(130, 130, 135, 30))
        p.setBrush(bg); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(bx, by), br, br)
        # 坑缘
        pen = QPen(QColor(180, 180, 185, 80), 1.2)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(bx, by), br + 1, br + 1)

    # ── 表面龟裂纹理（冷却收缩裂谷）──
    crack_rng = random.Random(83)
    for _ in range(6):
        sx = cx + crack_rng.uniform(-radius * 0.55, radius * 0.55)
        sy = cy + crack_rng.uniform(-radius * 0.55, radius * 0.55)
        angle = crack_rng.uniform(0, 2 * math.pi)
        length = radius * crack_rng.uniform(0.15, 0.35)
        ex = sx + math.cos(angle) * length
        ey = sy + math.sin(angle) * length
        pen = QPen(QColor(50, 50, 54, 80), 0.8)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawLine(QPointF(sx, sy), QPointF(ex, ey))

    # ── 锐利明暗分界线（无大气散射 = 硬边界）──
    terminator = QRadialGradient(cx - radius * 0.70, cy + radius * 0.05, radius * 1.5)
    terminator.setColorAt(0.0, QColor(255, 255, 255, 0))
    terminator.setColorAt(0.35, QColor(255, 255, 255, 0))
    terminator.setColorAt(0.52, QColor(0, 0, 0, 60))
    terminator.setColorAt(0.65, QColor(0, 0, 0, 140))
    terminator.setColorAt(0.78, QColor(0, 0, 0, 200))
    terminator.setColorAt(1.0, QColor(0, 0, 0, 240))
    p.setBrush(terminator); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 球面高光 ──
    highlight = QRadialGradient(cx - radius * 0.30, cy - radius * 0.35, radius * 0.30)
    highlight.setColorAt(0.0, QColor(255, 255, 255, 55))
    highlight.setColorAt(0.5, QColor(240, 240, 245, 20))
    highlight.setColorAt(1.0, QColor(200, 200, 205, 0))
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
            ig.setColorAt(0.78, QColor(180, 180, 185, ga // 2))
            ig.setColorAt(0.90, QColor(180, 180, 185, ga))
            ig.setColorAt(0.97, QColor(180//2, 180//2, 215, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(180, 180, 185, ga // 2))
            og.setColorAt(0.96, QColor(180//2, 180//2, 225, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(180, 180, 185, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)


    p.restore()
