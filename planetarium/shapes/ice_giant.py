# -*- coding: utf-8 -*-
"""
冰巨星 — 海王星蓝风格，冰晶大气 + 甲烷吸收红光 + 微光环
"""
import math, random
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QConicalGradient,
    QColor, QPen, QBrush
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
    # ── 辉光外层（冰蓝 + 青色）──
    breath = 1.0 + 0.05 * math.sin(anim_t * 1.8 + 0.3)
    for i in range(5):
        gr = radius * (1.04 + i * 0.15) * breath
        glow = QRadialGradient(cx, cy, gr)
        ga = max(0, 50 - i * 9)
        glow.setColorAt(0.0, QColor(100, 200, 255, 0))
        glow.setColorAt(0.35, QColor(80, 180, 255, ga))
        glow.setColorAt(0.65, QColor(50, 140, 240, ga // 2))
        glow.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(center, gr, gr)

    # ── 球体表面（深蓝→亮青多层）──
    base = QRadialGradient(cx - radius * 0.22, cy - radius * 0.28, radius * 1.05)
    surface = [
        (0.00, "#041040"), (0.10, "#0a2060"), (0.22, "#1a3a90"),
        (0.36, "#2868c8"), (0.48, "#3a88e8"), (0.56, "#50a8f0"),
        (0.66, "#3a88e8"), (0.78, "#1a5ab8"), (0.90, "#0a3070"),
        (1.00, "#041040"),
    ]
    for pos, color in surface:
        base.setColorAt(pos, QColor(color))
    p.setBrush(base); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 圆锥渐变叠加（青蓝旋转纹理）──
    conical = QConicalGradient(cx, cy, anim_t * 8.0 + 30)
    for i in range(8):
        pos = i / 8
        conical.setColorAt(pos, QColor(60, 160, 255, 15))
    p.setBrush(conical)
    p.drawEllipse(center, radius, radius)

    # ── 冰晶云带（水平柔光条纹）──
    p.save()
    from PyQt5.QtGui import QPainterPath
    from PyQt5.QtCore import QRectF
    clip = QPainterPath()
    clip.addEllipse(center, radius * 0.98, radius * 0.98)
    p.setClipPath(clip)
    p.setPen(Qt.NoPen)
    for band in range(14):
        by = cy - radius * 0.85 + band * (radius * 1.7 / 14)
        dy = by - cy
        if abs(dy) >= radius * 0.95:
            continue
        hw = math.sqrt(max(0, radius * radius - dy * dy))
        wave = math.sin(band * 0.8 + anim_t * 0.4) * radius * 0.08
        ba = 25 + int(15 * abs(math.sin(band * 0.5 + anim_t * 0.3)))
        bc = QColor(120, 200, 255, ba) if band % 3 == 0 else QColor(60, 150, 230, ba // 2)
        p.setBrush(bc)
        p.drawRect(QRectF(cx - hw + wave, by, hw * 2, radius * 1.7 / 14 + 1.0))
    p.restore()

    # ── 甲烷吸收暗斑（右下紫暗区域）──
    methane = QRadialGradient(cx + radius * 0.25, cy + radius * 0.30, radius * 0.55)
    methane.setColorAt(0.0, QColor(40, 10, 120, 40))
    methane.setColorAt(0.4, QColor(30, 5, 100, 60))
    methane.setColorAt(0.7, QColor(20, 5, 80, 40))
    methane.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(methane); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 冰晶微粒闪烁 ──
    ice_rng = random.Random(int(anim_t * 350) % 100000 + 444)
    p.setPen(Qt.NoPen)
    for _ in range(30):
        angle = ice_rng.uniform(0, 2 * math.pi)
        dist = radius * (0.15 + 0.80 * ice_rng.random())
        ix = cx + math.cos(angle) * dist
        iy = cy + math.sin(angle) * dist
        isize = ice_rng.uniform(0.3, 1.2)
        twinkle = 0.4 + 0.6 * abs(math.sin(angle * 8 + anim_t * 5.0))
        ia = int((20 + 40 * twinkle))
        ig = QRadialGradient(ix, iy, isize * 2.5)
        ig.setColorAt(0.0, QColor(180, 230, 255, ia))
        ig.setColorAt(0.5, QColor(140, 210, 255, ia // 3))
        ig.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(ig)
        p.drawEllipse(QPointF(ix, iy), isize * 2.5, isize * 2.5)
    # 少量十字星芒
    for _ in range(6):
        angle = ice_rng.uniform(0, 2 * math.pi)
        dist = radius * (0.3 + 0.6 * ice_rng.random())
        sx = cx + math.cos(angle) * dist
        sy = cy + math.sin(angle) * dist
        sa = ice_rng.randint(30, 90)
        p.setPen(QPen(QColor(200, 240, 255, sa), 0.5))
        p.drawLine(QPointF(sx - 3, sy), QPointF(sx + 3, sy))
        p.drawLine(QPointF(sx, sy - 3), QPointF(sx, sy + 3))
        p.setPen(Qt.NoPen)

    # ── 暗面叠加 ──
    shadow = QRadialGradient(cx, cy, radius * 1.6)
    shadow.setColorAt(0.0, QColor(255, 255, 255, 0))
    shadow.setColorAt(0.40, QColor(0, 0, 0, 8))
    shadow.setColorAt(0.55, QColor(0, 0, 0, 35))
    shadow.setColorAt(0.70, QColor(0, 0, 0, 70))
    shadow.setColorAt(0.85, QColor(0, 0, 0, 120))
    shadow.setColorAt(1.0, QColor(0, 0, 0, 190))
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
    spec = QRadialGradient(cx - radius * 0.30, cy - radius * 0.36, radius * 0.48)
    spec.setColorAt(0.0, QColor(255, 255, 255, 60))
    spec.setColorAt(0.25, QColor(255, 255, 255, 28))
    spec.setColorAt(0.55, QColor(200, 240, 255, 8))
    spec.setColorAt(1.0, QColor(180, 220, 255, 0))
    p.setBrush(spec); p.setPen(Qt.NoPen); p.drawEllipse(center, radius, radius)

    # ── 冰晶光环（细环，微倾斜）──
    ring_alpha = 50 + int(20 * abs(math.sin(anim_t * 0.6)))
    ring_inner = radius * 1.15
    ring_outer = radius * 1.50
    for i in range(40):
        pos = i / 40
        r_current = ring_inner + (ring_outer - ring_inner) * pos
        ia2 = int(ring_alpha * (0.6 + 0.4 * abs(math.sin(pos * 30 + anim_t * 0.5))))
        p.setBrush(QColor(100, 180, 240, ia2)); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy), r_current, r_current * 0.06)

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
            ig.setColorAt(0.78, QColor(100, 200, 255, ga // 2))
            ig.setColorAt(0.90, QColor(100, 200, 255, ga))
            ig.setColorAt(0.97, QColor(100//2, 200//2, 255, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(100, 200, 255, ga // 2))
            og.setColorAt(0.96, QColor(100//2, 200//2, 255, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(100, 200, 255, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)


    p.restore()
