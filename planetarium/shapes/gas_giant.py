# -*- coding: utf-8 -*-
"""
气态巨行星 — 木星风格，多层水平条纹 + 大红斑风暴 + 云带波动
"""
import math, random
from PyQt5.QtCore import Qt, QPointF, QRectF
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
    # ── 外层暖色辉光 ──
    for i in range(4):
        gr = radius * (1.04 + i * 0.12)
        glow = QRadialGradient(cx, cy, gr)
        gc = QColor(255, 180, 60, max(0, 40 - i * 8))
        glow.setColorAt(0.0, QColor(255, 200, 80, 0))
        glow.setColorAt(0.3, gc)
        glow.setColorAt(0.6, QColor(200, 120, 30, max(0, 25 - i * 6)))
        glow.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(center, gr, gr)

    # ── 球体基底：径向渐变（暖棕→橙黄→深棕）──
    base = QRadialGradient(cx - radius * 0.25, cy - radius * 0.3, radius * 1.05)
    band_colors = [
        (0.00, "#6b1a00"), (0.06, "#8b3a0a"), (0.14, "#c47a2a"),
        (0.22, "#deb040"), (0.28, "#c47220"), (0.34, "#a05018"),
        (0.42, "#deb040"), (0.48, "#c47a2a"), (0.54, "#8b3a0a"),
        (0.62, "#c88030"), (0.70, "#e8c050"), (0.78, "#c47220"),
        (0.86, "#9a4010"), (0.92, "#c88030"), (1.00, "#5a1000"),
    ]
    for pos, color in band_colors:
        base.setColorAt(pos, QColor(color))
    p.setBrush(base); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 圆锥渐变叠加（旋转色带纹理）──
    conical = QConicalGradient(cx, cy, anim_t * 12.0)
    for i, (pos, color) in enumerate(band_colors):
        conical.setColorAt(i / len(band_colors), QColor(color).darker(140))
    p.setBrush(conical)
    p.drawEllipse(center, radius, radius)

    # ── 动态云带波纹（横向波浪条纹）──
    p.save()
    clip = QPainterPath()
    clip.addEllipse(center, radius, radius)
    p.setClipPath(clip)
    p.setPen(Qt.NoPen)
    for band_idx in range(22):
        base_y = cy - radius + band_idx * (radius * 2 / 22)
        dy = base_y - cy
        if abs(dy) >= radius * 0.96:
            continue
        half_w = math.sqrt(max(0, radius * radius - dy * dy))
        # 波浪偏移
        wave1 = math.sin(band_idx * 0.55 + anim_t * 0.7) * radius * 0.12
        wave2 = math.cos(band_idx * 0.7 + anim_t * 0.55) * radius * 0.08
        wave = wave1 + wave2
        # 条纹颜色 —— 明暗交替
        if band_idx % 4 == 0:
            alpha = 80 + int(20 * abs(math.sin(band_idx * 0.3 + anim_t * 0.4)))
            band_color = QColor(255, 220, 110, alpha)
        elif band_idx % 4 == 1:
            alpha = 50 + int(15 * abs(math.sin(band_idx * 0.4 + anim_t * 0.35)))
            band_color = QColor(220, 140, 50, alpha)
        elif band_idx % 4 == 2:
            alpha = 55
            band_color = QColor(180, 90, 30, alpha)
        else:
            alpha = 35
            band_color = QColor(140, 60, 20, alpha)
        p.setBrush(band_color)
        bx = cx - half_w + wave
        bw = half_w * 2
        bh = radius * 2 / 22 + 1.5
        p.drawRect(QRectF(bx, base_y, bw, bh))
    p.restore()

    # ── 大红斑（风暴漩涡）──
    storm_cx = cx + radius * 0.22 * math.cos(anim_t * 0.12)
    storm_cy = cy + radius * 0.15
    storm_rx = radius * 0.30
    storm_ry = radius * 0.18
    for i in range(3):
        srx = storm_rx * (0.4 + i * 0.30)
        sry = storm_ry * (0.4 + i * 0.30)
        sa = 120 - i * 35
        grad = QRadialGradient(storm_cx, storm_cy, srx)
        gc = QColor(220, 90, 40, sa)
        grad.setColorAt(0, gc)
        grad.setColorAt(0.45, QColor(200, 70, 30, max(0, sa - 30)))
        grad.setColorAt(0.75, QColor(180, 100, 50, max(0, sa - 60)))
        grad.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(storm_cx, storm_cy), srx, sry)
    # 旋臂
    p.save()
    p.setClipRect(QRectF(storm_cx - storm_rx, storm_cy - storm_ry, storm_rx * 2, storm_ry * 2))
    for j in range(4):
        path = QPainterPath()
        angle_base = j * 1.57 + anim_t * 0.4
        path.moveTo(storm_cx, storm_cy)
        cp1_x = storm_cx + math.cos(angle_base) * storm_rx * 0.5
        cp1_y = storm_cy + math.sin(angle_base) * storm_ry * 0.5
        cp2_x = storm_cx + math.cos(angle_base + 1.0) * storm_rx * 0.85
        cp2_y = storm_cy + math.sin(angle_base + 1.0) * storm_ry * 0.85
        end_x = storm_cx + math.cos(angle_base + 1.8) * storm_rx * 0.45
        end_y = storm_cy + math.sin(angle_base + 1.8) * storm_ry * 0.45
        path.cubicTo(cp1_x, cp1_y, cp2_x, cp2_y, end_x, end_y)
        pen = QPen(QColor(240, 120, 50, 60))
        pen.setWidthF(2.0)
        p.setPen(pen); p.setBrush(Qt.NoBrush); p.drawPath(path)
    p.restore()

    # ── 暗面叠加 ──
    shadow = QRadialGradient(cx, cy, radius * 1.6)
    shadow.setColorAt(0.0, QColor(255, 255, 255, 0))
    shadow.setColorAt(0.38, QColor(0, 0, 0, 6))
    shadow.setColorAt(0.52, QColor(0, 0, 0, 30))
    shadow.setColorAt(0.68, QColor(0, 0, 0, 65))
    shadow.setColorAt(0.82, QColor(0, 0, 0, 110))
    shadow.setColorAt(0.94, QColor(0, 0, 0, 160))
    shadow.setColorAt(1.0, QColor(0, 0, 0, 195))
    p.setBrush(shadow); p.setPen(Qt.NoPen); p.drawEllipse(center, radius, radius)
    # ── 暗面呼吸增强（微妙的亮度波动）──
    shadow_breath = QRadialGradient(cx, cy, radius * 0.72)
    sb = int(12 * abs(math.sin(anim_t * 1.7 + 0.5)))
    shadow_breath.setColorAt(0.0, QColor(0, 0, 0, 0))
    shadow_breath.setColorAt(0.5, QColor(0, 0, 0, sb))
    shadow_breath.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(shadow_breath); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 镜面高光 ──
    spec = QRadialGradient(cx - radius * 0.28, cy - radius * 0.35, radius * 0.45)
    spec.setColorAt(0.0, QColor(255, 255, 255, 55))
    spec.setColorAt(0.25, QColor(255, 255, 252, 30))
    spec.setColorAt(0.55, QColor(255, 250, 240, 10))
    spec.setColorAt(1.0, QColor(255, 240, 220, 0))
    p.setBrush(spec); p.setPen(Qt.NoPen); p.drawEllipse(center, radius, radius)

    # ── 漂浮粒子 ──
    prng = random.Random(int(anim_t * 500) % 100000 + 200)
    p.setPen(Qt.NoPen)
    for _ in range(20):
        angle = prng.uniform(0, 2 * math.pi)
        dist = radius * (1.05 + 0.30 * prng.random())
        px = cx + math.cos(angle) * dist
        py = cy + math.sin(angle) * dist
        ps = prng.uniform(0.4, 1.4)
        pa = prng.randint(20, 80)
        pg = QRadialGradient(px, py, ps * 2.5)
        pg.setColorAt(0.0, QColor(255, 200, 80, pa))
        pg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(pg)
        p.drawEllipse(QPointF(px, py), ps * 2.5, ps * 2.5)

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
            ig.setColorAt(0.78, QColor(255, 180, 60, ga // 2))
            ig.setColorAt(0.90, QColor(255, 180, 60, ga))
            ig.setColorAt(0.97, QColor(255//2, 180//2, 90, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(255, 180, 60, ga // 2))
            og.setColorAt(0.96, QColor(255//2, 180//2, 100, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(255, 180, 60, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)


    p.restore()
