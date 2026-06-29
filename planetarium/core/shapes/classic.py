# -*- coding: utf-8 -*-
"""
经典类地行星 — 保留现有星球渲染引擎（地球/火星/海王星等），纯 QPainter 实现
"""
import math, random, hashlib
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QConicalGradient, QLinearGradient,
    QColor, QPen, QBrush, QFont, QPainterPath
)


def paint(painter: QPainter, center: QPointF, radius: float,
          anim_t: float, hovered: bool, alpha: float,
          style: dict = None, label: str = "", font_size: int = 9):
    """绘制经典类地行星（地球风格）。保留完整星球渲染管线。"""
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
    if style is None:
        style = {
            "surface": [
                (0.00, "#0a3d62"), (0.12, "#1a5f8a"), (0.22, "#2e86c1"),
                (0.36, "#16a085"), (0.44, "#27ae60"), (0.50, "#f0c040"),
                (0.58, "#27ae60"), (0.66, "#16a085"), (0.78, "#2e86c1"),
                (0.90, "#1a5f8a"), (1.00, "#0a3d62"),
            ],
            "atmosphere": QColor(80, 160, 255, 50),
            "aurora": QColor(40, 220, 160, 30),
            "clouds": True,
        }

    # 漂浮粒子
    _paint_particles(p, center, radius, style, anim_t)

    # 外层大气光晕
    _paint_atmosphere(p, center, radius, style, anim_t)

    # 光环
    if style.get("has_ring"):
        _paint_ring(p, center, radius, style, style.get("ring_vertical", False), anim_t)

    # 极光带
    _paint_aurora_band(p, center, radius, style, anim_t)

    # 球体表面
    _paint_surface(p, center, radius, style, anim_t)

    # 云层/条纹/环形山/风暴
    if style.get("clouds"):
        _paint_clouds(p, center, radius, anim_t)
    if style.get("bands"):
        _paint_bands(p, center, radius, style, anim_t)
    if style.get("craters"):
        _paint_craters(p, center, radius)
    if style.get("storm"):
        _paint_storm_swirls(p, center, radius, style, anim_t)

    # 表面微纹
    _paint_surface_micro_detail(p, center, radius, anim_t)

    # 球体高光（多层）
    _paint_specular(p, center, radius, anim_t)

    # 边缘逆光
    _paint_rim_light(p, center, radius, style, anim_t)

    # 悬停增强（主题色脉冲光晕 + 呼吸轮廓）──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        # 内层主题光晕
        for i in range(3):
            ir = radius + 2 + i * 5
            ig = QRadialGradient(center, ir)
            ga = int((70 - i * 18) * hp)
            ig.setColorAt(0.60, QColor(255, 255, 255, 0))
            ig.setColorAt(0.78, QColor(100, 180, 255, ga // 2))
            ig.setColorAt(0.90, QColor(100, 180, 255, ga))
            ig.setColorAt(0.97, QColor(50, 90, 175, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(100, 180, 255, ga // 2))
            og.setColorAt(0.96, QColor(50, 90, 175, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(100, 180, 255, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)

    # 标签
    if label:
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(label)
        tx = cx - tw / 2
        ty = cy + radius + 14
        p.setPen(QColor(200, 180, 240))
        p.setFont(QFont("PingFang SC", font_size))
        p.drawText(QPointF(tx + 0.5, ty + 0.5), label)
        p.setPen(QColor(255, 255, 255, 180))
        p.drawText(QPointF(tx, ty), label)

    p.restore()


# ═══════════════════════════════════════════
# 内部绘制函数（从 planet_painter.py 迁移）
# ═══════════════════════════════════════════

def _paint_atmosphere(p, c, r, style, anim_t):
    atmos = style.get("atmosphere", QColor(100, 100, 255, 30))
    aurora = style.get("aurora")
    breath = 1.0 + 0.06 * math.sin(anim_t * 2.0 + 0.5)
    for i in range(5):
        scale = (1.06 + i * 0.16) * breath
        alpha = int(atmos.alpha() * (0.65 ** i))
        grad = QRadialGradient(c, r * scale)
        ac = QColor(atmos.red(), atmos.green(), atmos.blue(), max(1, alpha))
        grad.setColorAt(0.00, QColor(ac.red(), ac.green(), ac.blue(), alpha // 4))
        grad.setColorAt(0.25, ac)
        grad.setColorAt(0.55, QColor(ac.red(), ac.green(), ac.blue(), alpha // 2))
        grad.setColorAt(0.80, QColor(ac.red(), ac.green(), ac.blue(), alpha // 5))
        grad.setColorAt(1.00, QColor(255, 255, 255, 0))
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(c, r * scale, r * scale)
    if aurora and aurora.alpha() > 0:
        for i in range(3):
            scale = (1.30 + i * 0.22) * breath
            alpha = int(aurora.alpha() * (0.55 ** i))
            grad = QRadialGradient(c, r * scale)
            ac = QColor(aurora.red(), aurora.green(), aurora.blue(), alpha)
            grad.setColorAt(0.00, QColor(255, 255, 255, 0))
            grad.setColorAt(0.40, QColor(ac.red(), ac.green(), ac.blue(), alpha // 3))
            grad.setColorAt(0.65, ac)
            grad.setColorAt(0.85, QColor(ac.red(), ac.green(), ac.blue(), alpha // 3))
            grad.setColorAt(1.00, QColor(255, 255, 255, 0))
            p.setBrush(grad)
            p.setPen(Qt.NoPen)
            p.drawEllipse(c, r * scale, r * scale)
    if style.get("glow"):
        for i in range(4):
            scale = (1.20 + i * 0.32) * breath
            alpha = max(0, 65 - i * 15)
            glow = QRadialGradient(c, r * scale)
            glow.setColorAt(0.00, QColor(255, 220, 60, alpha))
            glow.setColorAt(0.35, QColor(255, 160, 30, alpha // 2))
            glow.setColorAt(0.65, QColor(255, 120, 15, alpha // 4))
            glow.setColorAt(1.00, QColor(255, 255, 255, 0))
            p.setBrush(glow)
            p.setPen(Qt.NoPen)
            p.drawEllipse(c, r * scale, r * scale)


def _paint_surface(p, c, r, style, anim_t):
    cx, cy = c.x(), c.y()
    surface = style.get("surface", [])
    if not surface:
        return
    grad = QRadialGradient(cx - r * 0.28, cy - r * 0.34, r * 1.05)
    for pos, color in surface:
        grad.setColorAt(pos, QColor(color))
    p.setBrush(grad)
    p.setPen(Qt.NoPen)
    p.drawEllipse(c, r, r)
    if style.get("bands") or style.get("storm"):
        conical = QConicalGradient(cx, cy, anim_t * 15.0)
        for i in range(len(surface)):
            pos = i / len(surface)
            color = QColor(surface[i][1])
            color.setAlpha(18)
            conical.setColorAt(pos, color)
        p.setBrush(conical)
        p.drawEllipse(c, r, r)
    shadow_grad = QRadialGradient(cx, cy, r * 1.60)
    shadow_grad.setColorAt(0.00, QColor(255, 255, 255, 0))
    shadow_grad.setColorAt(0.30, QColor(0, 0, 0, 4))
    shadow_grad.setColorAt(0.42, QColor(0, 0, 0, 12))
    shadow_grad.setColorAt(0.52, QColor(0, 0, 0, 28))
    shadow_grad.setColorAt(0.62, QColor(0, 0, 0, 48))
    shadow_grad.setColorAt(0.72, QColor(0, 0, 0, 75))
    shadow_grad.setColorAt(0.82, QColor(0, 0, 0, 110))
    shadow_grad.setColorAt(0.92, QColor(0, 0, 0, 155))
    shadow_grad.setColorAt(1.00, QColor(0, 0, 0, 190))
    p.setBrush(shadow_grad)
    p.drawEllipse(c, r, r)


def _paint_specular(p, c, r, anim_t):
    cx, cy = c.x(), c.y()
    shift_x = math.sin(anim_t * 0.6) * r * 0.04
    shift_y = math.cos(anim_t * 0.6) * r * 0.04
    spec1 = QRadialGradient(cx - r * 0.35 + shift_x, cy - r * 0.40 + shift_y, r * 0.50)
    spec1.setColorAt(0.00, QColor(255, 255, 255, 70))
    spec1.setColorAt(0.20, QColor(255, 255, 252, 45))
    spec1.setColorAt(0.45, QColor(255, 255, 250, 18))
    spec1.setColorAt(0.70, QColor(255, 252, 245, 4))
    spec1.setColorAt(1.00, QColor(255, 250, 240, 0))
    p.setBrush(spec1); p.setPen(Qt.NoPen); p.drawEllipse(c, r, r)
    spec2 = QRadialGradient(cx - r * 0.33 + shift_x * 1.3, cy - r * 0.38 + shift_y * 1.3, r * 0.72)
    spec2.setColorAt(0.00, QColor(255, 255, 255, 28))
    spec2.setColorAt(0.35, QColor(255, 255, 250, 12))
    spec2.setColorAt(0.65, QColor(255, 252, 245, 3))
    spec2.setColorAt(1.00, QColor(255, 250, 240, 0))
    p.setBrush(spec2); p.drawEllipse(c, r, r)
    spec3 = QRadialGradient(cx - r * 0.36 + shift_x * 0.7, cy - r * 0.42 + shift_y * 0.7, r * 0.18)
    spec3.setColorAt(0.00, QColor(255, 255, 255, 90))
    spec3.setColorAt(0.25, QColor(255, 255, 255, 35))
    spec3.setColorAt(0.60, QColor(255, 255, 255, 5))
    spec3.setColorAt(1.00, QColor(255, 255, 255, 0))
    p.setBrush(spec3); p.drawEllipse(c, r, r)


def _paint_rim_light(p, c, r, style, anim_t):
    cx, cy = c.x(), c.y()
    atmos = style.get("atmosphere", QColor(100, 100, 255, 30))
    breath = 0.8 + 0.2 * abs(math.sin(anim_t * 1.3 + 0.7))
    rim_grad = QRadialGradient(cx + r * 0.40, cy + r * 0.55, r * 0.55)
    alpha = int(atmos.alpha() * 0.55 * breath)
    rc = QColor(atmos.red(), atmos.green(), atmos.blue(), alpha)
    rim_grad.setColorAt(0.00, QColor(255, 255, 255, 0))
    rim_grad.setColorAt(0.50, QColor(255, 255, 255, 0))
    rim_grad.setColorAt(0.78, QColor(rc.red(), rc.green(), rc.blue(), alpha // 2))
    rim_grad.setColorAt(0.92, rc)
    rim_grad.setColorAt(1.00, QColor(255, 255, 255, 0))
    p.setBrush(rim_grad); p.setPen(Qt.NoPen); p.drawEllipse(c, r, r)


def _paint_surface_micro_detail(p, c, r, anim_t):
    cx, cy = c.x(), c.y()
    if r < 20:
        return
    seed = int(anim_t * 400) % 100000
    rng = random.Random(42 + seed * 17)
    p.save()
    clip = QPainterPath()
    clip.addEllipse(c, r, r)
    p.setClipPath(clip)
    p.setPen(Qt.NoPen)
    num_dots = min(int(r * 1.8), 80)
    for _ in range(num_dots):
        angle = rng.uniform(0, 2 * math.pi)
        dist = rng.uniform(0.08, 0.92) * r
        dx = cx + math.cos(angle) * dist
        dy = cy + math.sin(angle) * dist
        dot_r = rng.uniform(0.4, 1.0)
        alpha = rng.randint(3, 12)
        p.setBrush(QColor(255, 255, 255, alpha))
        p.drawEllipse(QPointF(dx, dy), dot_r, dot_r)
        if rng.random() < 0.25:
            dx2 = cx + math.cos(angle + 0.15) * dist * 0.98
            dy2 = cy + math.sin(angle + 0.15) * dist * 0.98
            p.setBrush(QColor(0, 0, 0, rng.randint(2, 8)))
            p.drawEllipse(QPointF(dx2, dy2), dot_r * 0.7, dot_r * 0.7)
    p.restore()


def _paint_clouds(p, c, r, anim_t):
    cx, cy = c.x(), c.y()
    p.save()
    p.setClipRect(QRectF(cx - r, cy - r, r * 2, r * 2))
    drift = anim_t * 0.025
    p.setPen(Qt.NoPen)
    frame_seed = int(abs(hashlib.md5(f"clouds_{anim_t:.6f}".encode()).digest()[0]) * 16807) % 2147483647
    rng = random.Random(frame_seed)
    for _ in range(10):
        angle = rng.uniform(0, 2 * math.pi) + drift
        dist = rng.uniform(0.08, 0.72) * r
        cloud_cx = cx + math.cos(angle) * dist
        cloud_cy = cy + math.sin(angle) * dist
        cloud_rx = rng.uniform(0.10, 0.26) * r
        cloud_ry = rng.uniform(0.04, 0.12) * r
        cloud_grad = QRadialGradient(cloud_cx, cloud_cy, max(cloud_rx, cloud_ry) * 1.3)
        ba = rng.randint(30, 65)
        cloud_grad.setColorAt(0.00, QColor(255, 255, 255, ba))
        cloud_grad.setColorAt(0.30, QColor(255, 255, 255, int(ba * 0.7)))
        cloud_grad.setColorAt(0.55, QColor(255, 255, 255, int(ba * 0.35)))
        cloud_grad.setColorAt(0.80, QColor(255, 255, 255, int(ba * 0.10)))
        cloud_grad.setColorAt(1.00, QColor(255, 255, 255, 0))
        p.setBrush(cloud_grad)
        p.drawEllipse(QPointF(cloud_cx, cloud_cy), cloud_rx, cloud_ry)
    for _ in range(18):
        angle = rng.uniform(0, 2 * math.pi) + drift * 1.4
        dist = rng.uniform(0.05, 0.80) * r
        sx = cx + math.cos(angle) * dist
        sy = cy + math.sin(angle) * dist
        sr = rng.uniform(0.02, 0.08) * r
        alpha = rng.randint(10, 30)
        sg = QRadialGradient(sx, sy, sr * 2.0)
        sg.setColorAt(0.00, QColor(255, 255, 255, alpha))
        sg.setColorAt(0.40, QColor(255, 255, 255, alpha // 2))
        sg.setColorAt(1.00, QColor(255, 255, 255, 0))
        p.setBrush(sg)
        p.drawEllipse(QPointF(sx, sy), sr, sr * 0.7)
    for band_idx in range(4):
        base_y = cy + rng.uniform(-0.30, 0.30) * r
        if abs(base_y - cy) > r * 0.95:
            continue
        half_w = math.sqrt(max(0, r * r - (base_y - cy) ** 2))
        path = QPainterPath()
        path.moveTo(cx - half_w, base_y)
        wave_amp = rng.uniform(4, 10)
        cp1_y = base_y + math.sin(anim_t * 0.5 + band_idx * 1.7) * wave_amp
        cp2_y = base_y + math.cos(anim_t * 0.5 + band_idx * 1.7 + 0.8) * wave_amp
        path.cubicTo(cx - half_w * 0.5, cp1_y, cx + half_w * 0.5, cp2_y, cx + half_w, base_y)
        pen_width = rng.uniform(1.0, 3.0)
        pen_alpha = rng.randint(12, 38)
        pen = QPen(QColor(255, 255, 255, pen_alpha))
        pen.setWidthF(pen_width); pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen); p.setBrush(Qt.NoBrush); p.drawPath(path)
    p.restore()


def _paint_bands(p, c, r, style, anim_t):
    cx, cy = c.x(), c.y()
    surface = style.get("surface", [])
    if not surface:
        return
    p.setPen(Qt.NoPen)
    num_bands = 18
    band_height = (r * 2) / num_bands
    for i in range(num_bands):
        y = cy - r + i * band_height
        dy = y - cy
        if abs(dy) >= r * 0.98:
            continue
        half_width = math.sqrt(max(0, r * r - dy * dy))
        wave_offset = math.sin(i * 0.7 + anim_t * 0.5) * r * 0.05
        idx = int(i / num_bands * len(surface))
        color = QColor(surface[min(idx, len(surface) - 1)][1])
        base_alpha = 40 if i % 3 == 0 else (22 if i % 3 == 1 else 8)
        alpha = base_alpha + int(8 * abs(math.sin(i * 0.4 + anim_t * 0.35)))
        band_color = QColor(color.red(), color.green(), color.blue(), min(alpha, 55))
        p.setBrush(band_color)
        bx = cx - half_width + wave_offset
        p.drawRect(QRectF(bx, y, half_width * 2, band_height + 1.0))


def _paint_storm_swirls(p, c, r, style, anim_t):
    cx, cy = c.x(), c.y()
    storm_color = style.get("storm_color", QColor(200, 80, 40, 90))
    storm_cx = cx + r * 0.18 * math.cos(anim_t * 0.15)
    storm_cy = cy + r * 0.22
    storm_rx, storm_ry = r * 0.28, r * 0.16
    for i in range(3):
        sr = storm_rx * (0.45 + i * 0.28)
        alpha = storm_color.alpha() - i * 28
        grad = QRadialGradient(storm_cx, storm_cy, sr)
        sc = QColor(storm_color.red(), storm_color.green(), storm_color.blue(), max(0, alpha))
        grad.setColorAt(0, sc)
        grad.setColorAt(0.5, QColor(sc.red(), sc.green(), sc.blue(), max(0, alpha // 2)))
        grad.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(storm_cx, storm_cy), sr, storm_ry * (0.45 + i * 0.28) / storm_rx * sr)
    p.save()
    p.setClipRect(QRectF(storm_cx - storm_rx, storm_cy - storm_ry, storm_rx * 2, storm_ry * 2))
    for j in range(3):
        path = QPainterPath()
        angle = j * 2.1 + anim_t * 0.3
        path.moveTo(storm_cx, storm_cy)
        cp1_x = storm_cx + math.cos(angle) * storm_rx * 0.6
        cp1_y = storm_cy + math.sin(angle) * storm_ry * 0.6
        cp2_x = storm_cx + math.cos(angle + 1.2) * storm_rx * 0.9
        cp2_y = storm_cy + math.sin(angle + 1.2) * storm_ry * 0.9
        end_x = storm_cx + math.cos(angle + 2.0) * storm_rx * 0.5
        end_y = storm_cy + math.sin(angle + 2.0) * storm_ry * 0.5
        path.cubicTo(cp1_x, cp1_y, cp2_x, cp2_y, end_x, end_y)
        pen = QPen(QColor(storm_color.red(), storm_color.green(), storm_color.blue(), max(0, storm_color.alpha() - 40)))
        pen.setWidthF(1.5)
        p.setPen(pen); p.setBrush(Qt.NoBrush); p.drawPath(path)
    p.restore()


def _paint_ring(p, c, r, style, vertical, anim_t):
    cx, cy = c.x(), c.y()
    ring_inner = r * 1.18; ring_outer = r * 1.82
    cassini_gap_outer = r * 1.38; cassini_gap_inner = r * 1.31
    surface = style.get("surface", [])
    ring_base = QColor(210, 180, 140, 120)
    if surface:
        mid_color = QColor(surface[len(surface) // 2][1])
        ring_base = QColor(mid_color.red(), mid_color.green(), mid_color.blue(), 100)
    p.save()
    ring_layers = [
        (ring_inner, cassini_gap_inner, 95, False),
        (cassini_gap_inner, cassini_gap_outer, 10, True),
        (cassini_gap_outer, ring_outer * 0.68, 80, False),
        (ring_outer * 0.68, ring_outer * 0.74, 12, True),
        (ring_outer * 0.74, ring_outer * 0.96, 60, False),
        (ring_outer * 0.96, ring_outer, 30, False),
    ]
    ring_count = 80
    for inner, outer, alpha, is_gap in ring_layers:
        if vertical and is_gap:
            continue
        for i in range(ring_count):
            pos = i / ring_count
            r_current = inner + (outer - inner) * pos
            actual_alpha = alpha
            if is_gap and not vertical:
                noise = 0.5 + 0.5 * math.sin(pos * 120 + inner * 0.3)
                actual_alpha = int(alpha * noise)
            color = QColor(ring_base.red(), ring_base.green(), ring_base.blue(), actual_alpha)
            p.setBrush(color); p.setPen(Qt.NoPen)
            if vertical:
                p.drawEllipse(QPointF(cx, cy), r_current, r_current * 0.12)
            else:
                p.drawEllipse(QPointF(cx, cy), r_current, r_current * 0.07)
    ring_rng = random.Random(int(anim_t * 120) % 10000)
    p.setPen(Qt.NoPen)
    for _ in range(55):
        angle = ring_rng.uniform(0, 2 * math.pi)
        dist = ring_rng.uniform(ring_inner, ring_outer)
        if cassini_gap_inner <= dist <= cassini_gap_outer:
            dist = ring_rng.choice([ring_inner, ring_outer]) + ring_rng.uniform(-0.03, 0.03) * r
        px = cx + math.cos(angle) * dist
        py = cy + math.sin(angle) * dist * (0.12 if vertical else 0.07)
        particle_r = ring_rng.uniform(0.4, 1.6)
        alpha = ring_rng.randint(20, 90)
        p.setBrush(QColor(ring_base.red(), ring_base.green(), ring_base.blue(), alpha))
        p.drawEllipse(QPointF(px, py), particle_r, particle_r)
    p.restore()


def _paint_aurora_band(p, c, r, style, anim_t):
    aurora = style.get("aurora")
    if not aurora or aurora.alpha() <= 0:
        return
    cx, cy = c.x(), c.y()
    wave = math.sin(anim_t * 1.2) * 0.15
    p.save()
    clip_path = QPainterPath()
    clip_path.addEllipse(c, r * 1.05, r * 1.05)
    p.setClipPath(clip_path)
    for i in range(3):
        aurora_y = cy - r * (0.5 + i * 0.25)
        aurora_rx = r * (0.75 + i * 0.15)
        aurora_ry = r * (0.12 + i * 0.05)
        offset_x = math.sin(anim_t * 0.5 + i * 1.5) * r * (0.10 + wave)
        grad = QRadialGradient(cx + offset_x, aurora_y, aurora_rx)
        alpha = int(aurora.alpha() * (0.35 - i * 0.10))
        ac = QColor(aurora.red(), aurora.green(), aurora.blue(), max(0, alpha))
        grad.setColorAt(0, QColor(255, 255, 255, 0))
        grad.setColorAt(0.4, ac)
        grad.setColorAt(0.6, QColor(ac.red(), ac.green(), ac.blue(), alpha // 2))
        grad.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx + offset_x, aurora_y), aurora_rx, aurora_ry)
    p.restore()


def _paint_craters(p, c, r):
    cx, cy = c.x(), c.y()
    random.seed(123)
    p.setPen(Qt.NoPen)
    for _ in range(20):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0.08, 0.88) * r
        crater_cx = cx + math.cos(angle) * dist
        crater_cy = cy + math.sin(angle) * dist
        crater_r = random.uniform(0.02, 0.11) * r
        rim_grad = QRadialGradient(crater_cx - crater_r * 0.3, crater_cy - crater_r * 0.3, crater_r * 1.05)
        rim_grad.setColorAt(0, QColor(200, 200, 200, 50))
        rim_grad.setColorAt(0.4, QColor(140, 140, 140, 30))
        rim_grad.setColorAt(0.7, QColor(60, 60, 60, 80))
        rim_grad.setColorAt(1, QColor(100, 100, 100, 15))
        p.setBrush(rim_grad)
        p.drawEllipse(QPointF(crater_cx, crater_cy), crater_r, crater_r * 0.75)


def _paint_particles(p, c, r, style, anim_t):
    cx, cy = c.x(), c.y()
    atmos = style.get("atmosphere", QColor(100, 100, 255, 30))
    aurora = style.get("aurora")
    p.setPen(Qt.NoPen)
    inner_rng = random.Random(int(anim_t * 600) % 100000 + 777)
    for i in range(22):
        base_angle = (i / 22) * 2 * math.pi
        angle = base_angle + anim_t * (0.35 + 0.12 * math.sin(i * 2.1))
        dist = r * (1.08 + 0.20 * abs(math.sin(i * 1.6 + anim_t * 0.45)))
        px = cx + math.cos(angle) * dist
        py = cy + math.sin(angle) * dist
        size = 0.6 + 1.0 * abs(math.sin(i * 2.7 + anim_t * 2.0))
        pulse = 0.4 + 0.6 * abs(math.sin(i * 1.9 + anim_t * 3.0))
        if aurora and aurora.alpha() > 0:
            alpha = int(aurora.alpha() * 0.45 * pulse)
            pc = QColor(aurora.red(), aurora.green(), aurora.blue(), alpha)
        else:
            alpha = int(atmos.alpha() * 0.35 * pulse)
            pc = QColor(atmos.red(), atmos.green(), atmos.blue(), alpha)
        glow_r = size * 2.0
        glow = QRadialGradient(px, py, glow_r)
        glow.setColorAt(0.00, QColor(pc.red(), pc.green(), pc.blue(), pc.alpha()))
        glow.setColorAt(0.45, QColor(pc.red(), pc.green(), pc.blue(), pc.alpha() // 3))
        glow.setColorAt(1.00, QColor(255, 255, 255, 0))
        p.setBrush(glow)
        p.drawEllipse(QPointF(px, py), glow_r, glow_r)
        p.setBrush(QColor(255, 255, 255, int(alpha * 1.3)))
        p.drawEllipse(QPointF(px, py), size * 0.45, size * 0.45)
    outer_rng = random.Random(int(anim_t * 400) % 100000 + 333)
    for i in range(14):
        base_angle = (i / 14) * 2 * math.pi + 0.5
        angle = base_angle + anim_t * (0.15 + 0.08 * math.sin(i * 3.3))
        dist = r * (1.30 + 0.40 * abs(math.sin(i * 2.0 + anim_t * 0.35)))
        px = cx + math.cos(angle) * dist
        py = cy + math.sin(angle) * dist
        twinkle = 0.3 + 0.7 * abs(math.sin(i * 3.7 + anim_t * 4.5))
        size = 0.5 + 1.2 * twinkle
        alpha = int(35 + 40 * twinkle)
        if twinkle > 0.82 and size > 1.2:
            cross_len = size * 3.5
            cross_alpha = int(alpha * 0.5)
            p.setPen(QPen(QColor(255, 255, 255, cross_alpha), 0.6))
            p.drawLine(QPointF(px - cross_len, py), QPointF(px + cross_len, py))
            p.drawLine(QPointF(px, py - cross_len), QPointF(px, py + cross_len))
            p.setPen(Qt.NoPen)
        glow = QRadialGradient(px, py, size * 3.0)
        glow.setColorAt(0.00, QColor(255, 255, 255, alpha))
        glow.setColorAt(0.35, QColor(255, 255, 255, alpha // 3))
        glow.setColorAt(1.00, QColor(255, 255, 255, 0))
        p.setBrush(glow)
        p.drawEllipse(QPointF(px, py), size * 3.0, size * 3.0)
        p.setBrush(QColor(255, 255, 255, alpha))
        p.drawEllipse(QPointF(px, py), size * 0.5, size * 0.5)
