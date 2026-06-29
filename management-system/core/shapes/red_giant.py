# -*- coding: utf-8 -*-
"""
红巨星 — 巨大暗红 + 表面米粒组织 + 慢速翻滚对流 + 日冕抛射
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
    # ── 外层日冕辉光（极宽大红晕）──
    for i in range(4):
        gr = radius * (1.10 + i * 0.50)
        glow = QRadialGradient(cx, cy, gr)
        ga = int((55 - i * 12) * (0.75 + 0.25 * abs(math.sin(anim_t * 0.6 + i))))
        glow.setColorAt(0.0, QColor(220, 90, 30, 0))
        glow.setColorAt(0.25, QColor(200, 70, 20, ga // 3))
        glow.setColorAt(0.45, QColor(180, 50, 15, ga))
        glow.setColorAt(0.65, QColor(140, 35, 10, ga // 2))
        glow.setColorAt(0.82, QColor(100, 20, 5, ga // 4))
        glow.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(center, gr, gr)

    # ── 主体（暗红→橙红渐变）──
    body = QRadialGradient(cx, cy, radius * 1.02)
    body.setColorAt(0.0, QColor(240, 120, 40))
    body.setColorAt(0.20, QColor(210, 85, 25))
    body.setColorAt(0.40, QColor(180, 55, 15))
    body.setColorAt(0.60, QColor(150, 35, 10))
    body.setColorAt(0.78, QColor(110, 20, 5))
    body.setColorAt(0.92, QColor(70, 10, 3))
    body.setColorAt(1.0, QColor(35, 5, 1))
    p.setBrush(body); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 米粒组织（蜂窝状表面对流包）──
    gran_rng = random.Random(101)
    for _ in range(55):
        ga2 = gran_rng.uniform(0, 2 * math.pi)
        gd = gran_rng.uniform(0.15, 0.92) * radius
        gx = cx + math.cos(ga2) * gd
        gy = cy + math.sin(ga2) * gd
        gs = radius * gran_rng.uniform(0.03, 0.08)
        # 米粒中心亮（上升热气流），边缘暗（下沉冷气流）
        c_normal = gran_rng.randint(180, 255)
        cell = QRadialGradient(gx, gy, gs)
        cell.setColorAt(0.0, QColor(c_normal, gran_rng.randint(80, 140), gran_rng.randint(20, 50), 60))
        cell.setColorAt(0.4, QColor(c_normal - 30, gran_rng.randint(50, 100), gran_rng.randint(10, 30), 40))
        cell.setColorAt(1.0, QColor(c_normal - 60, gran_rng.randint(20, 60), gran_rng.randint(5, 15), 20))
        p.setBrush(cell); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(gx, gy), gs, gs)

    # ── 慢速翻滚对流暗带（大尺度水平条纹）──
    for i in range(5):
        band_y = cy + (i - 2) * radius * 0.25
        band_shift = math.sin(anim_t * 0.25 + i * 1.1) * radius * 0.10
        band = QRadialGradient(cx, band_y + band_shift, radius * 0.35)
        band.setColorAt(0.0, QColor(255, 100, 20, 15))
        band.setColorAt(0.5, QColor(200, 60, 10, 30))
        band.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(band); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, band_y + band_shift), radius * 0.95, radius * 0.35)

    # ── 日冕物质抛射（偶发弧线抛射）──
    cme_rng = random.Random(int(anim_t * 50) % 100000 + 333)
    cme_trigger = abs(math.sin(anim_t * 0.15)) > 0.85
    if cme_trigger:
        for _ in range(2):
            cme_angle = cme_rng.uniform(-0.6, 0.6) - math.pi / 2  # 基本向上
            cme_len = radius * cme_rng.uniform(0.8, 1.8)
            cme_path = QPainterPath()
            sx = cx + math.cos(cme_angle) * radius * 0.75
            sy = cy + math.sin(cme_angle) * radius * 0.75
            cme_path.moveTo(sx, sy)
            cp1_x = sx + math.cos(cme_angle - 0.4) * cme_len * 0.4
            cp1_y = sy + math.sin(cme_angle - 0.4) * cme_len * 0.4
            cp2_x = sx + math.cos(cme_angle + 0.3) * cme_len * 0.7
            cp2_y = sy + math.sin(cme_angle + 0.3) * cme_len * 0.7
            ep_x = sx + math.cos(cme_angle) * cme_len
            ep_y = sy + math.sin(cme_angle) * cme_len
            cme_path.cubicTo(cp1_x, cp1_y, cp2_x, cp2_y, ep_x, ep_y)
            pen = QPen(QColor(255, 140, 40, 120), 2.5)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen); p.setBrush(Qt.NoBrush)
            p.drawPath(cme_path)
            # 抛射末端亮斑
            tip_grad = QRadialGradient(ep_x, ep_y, radius * 0.08)
            tip_grad.setColorAt(0.0, QColor(255, 200, 100, 150))
            tip_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(tip_grad); p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(ep_x, ep_y), radius * 0.08, radius * 0.08)

    # ── 临边昏暗（大气吸收，中心亮边缘暗）──
    limb = QRadialGradient(cx, cy, radius)
    limb.setColorAt(0.0, QColor(255, 255, 255, 0))
    limb.setColorAt(0.50, QColor(255, 255, 255, 0))
    limb.setColorAt(0.70, QColor(0, 0, 0, 30))
    limb.setColorAt(0.85, QColor(0, 0, 0, 80))
    limb.setColorAt(0.95, QColor(0, 0, 0, 160))
    limb.setColorAt(1.0, QColor(0, 0, 0, 210))
    p.setBrush(limb); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 高光 ──
    spec = QRadialGradient(cx - radius * 0.25, cy - radius * 0.30, radius * 0.28)
    spec.setColorAt(0.0, QColor(255, 200, 140, 50))
    spec.setColorAt(0.5, QColor(255, 150, 80, 15))
    spec.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(spec); p.setPen(Qt.NoPen)
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
            ig.setColorAt(0.78, QColor(255, 100, 30, ga // 2))
            ig.setColorAt(0.90, QColor(255, 100, 30, ga))
            ig.setColorAt(0.97, QColor(255//2, 100//2, 60, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(255, 100, 30, ga // 2))
            og.setColorAt(0.96, QColor(255//2, 100//2, 70, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(255, 100, 30, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)


    p.restore()
