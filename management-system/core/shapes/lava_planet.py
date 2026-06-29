# -*- coding: utf-8 -*-
"""
熔岩行星 — 暗红/黑色地表 + 发光的岩浆裂纹脉动 + 火山粒子喷发
"""
import math, random
from PyQt5.QtCore import Qt, QPointF, QRectF
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
    # ── 外层暗红辉光 ──
    for i in range(4):
        gr = radius * (1.04 + i * 0.14)
        glow = QRadialGradient(cx, cy, gr)
        ga = max(0, 55 - i * 12)
        glow.setColorAt(0.0, QColor(255, 80, 20, 0))
        glow.setColorAt(0.3, QColor(255, 60, 10, ga))
        glow.setColorAt(0.6, QColor(200, 30, 5, ga // 2))
        glow.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(center, gr, gr)

    # ── 球体基底：暗黑/深红渐变 ──
    base = QRadialGradient(cx - radius * 0.2, cy - radius * 0.25, radius * 1.05)
    lava_surface = [
        (0.00, "#1a0804"), (0.15, "#2d1008"), (0.30, "#3d140a"),
        (0.45, "#281008"), (0.58, "#3a1608"), (0.70, "#251008"),
        (0.84, "#32140a"), (1.00, "#140604"),
    ]
    for pos, color in lava_surface:
        base.setColorAt(pos, QColor(color))
    p.setBrush(base); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 岩浆裂纹网络 ──
    crack_rng = random.Random(42)  # 确定性种子保持帧间一致
    num_cracks = 18
    p.setPen(Qt.NoPen)
    for ci in range(num_cracks):
        # 裂纹起点（随机球面位置）
        start_angle = crack_rng.uniform(0, 2 * math.pi)
        start_dist = crack_rng.uniform(0.05, 0.85) * radius
        sx = cx + math.cos(start_angle) * start_dist
        sy = cy + math.sin(start_angle) * start_dist

        # 裂纹路径（2-4段折线）
        segments = crack_rng.randint(2, 4)
        path = QPainterPath()
        path.moveTo(sx, sy)
        cur_x, cur_y = sx, sy
        for seg in range(segments):
            angle_delta = crack_rng.uniform(-0.7, 0.7)
            seg_angle = start_angle + angle_delta * (seg + 1)
            seg_len = crack_rng.uniform(0.06, 0.22) * radius
            cur_x += math.cos(seg_angle) * seg_len
            cur_y += math.sin(seg_angle) * seg_len
            # 约束在球体内
            dist_from_center = math.sqrt((cur_x - cx) ** 2 + (cur_y - cy) ** 2)
            if dist_from_center > radius * 0.95:
                break
            path.lineTo(cur_x, cur_y)

        # 裂纹发光（底层宽辉光 + 顶层窄亮线）
        pulse = 0.5 + 0.5 * abs(math.sin(ci * 1.7 + anim_t * 2.0))
        # 底层辉光
        pen = QPen(QColor(255, 100, 20, int(60 * pulse)), 4.0)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawPath(path)
        # 顶层亮线
        pen2 = QPen(QColor(255, 180, 60, int(140 * pulse)), 1.5)
        pen2.setCapStyle(Qt.RoundCap)
        p.setPen(pen2)
        p.drawPath(path)

    # ── 岩浆热点（熔岩池圆斑）──
    pool_rng = random.Random(99 + int(anim_t * 80) % 10000)
    for _ in range(12):
        pa = pool_rng.uniform(0, 2 * math.pi)
        pd = pool_rng.uniform(0.1, 0.82) * radius
        px = cx + math.cos(pa) * pd
        py = cy + math.sin(pa) * pd
        pr = pool_rng.uniform(0.03, 0.10) * radius
        pulse2 = 0.5 + 0.5 * abs(math.sin(pa * 5 + anim_t * 2.8))
        pg = QRadialGradient(px, py, pr * 2.0)
        pg.setColorAt(0.0, QColor(255, 200, 60, int(180 * pulse2)))
        pg.setColorAt(0.3, QColor(255, 130, 20, int(120 * pulse2)))
        pg.setColorAt(0.6, QColor(200, 60, 10, int(60 * pulse2)))
        pg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(pg); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(px, py), pr * 2.0, pr * 2.0)

    # ── 火山喷发粒子（球体表面向外喷出）──
    erupt_rng = random.Random(int(anim_t * 300) % 100000 + 777)
    p.setPen(Qt.NoPen)
    for _ in range(25):
        # 从球体表面附近发射
        ea = erupt_rng.uniform(0, 2 * math.pi)
        ed = radius * (0.92 + erupt_rng.uniform(0, 0.40))
        ex = cx + math.cos(ea) * ed
        ey = cy + math.sin(ea) * ed
        es = erupt_rng.uniform(0.4, 2.0)
        ea2 = erupt_rng.randint(30, 140)
        eg = QRadialGradient(ex, ey, es * 2.5)
        eg.setColorAt(0.0, QColor(255, 180, 40, ea2))
        eg.setColorAt(0.4, QColor(255, 100, 15, ea2 // 2))
        eg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(eg)
        p.drawEllipse(QPointF(ex, ey), es * 2.5, es * 2.5)

    # ── 暗面叠加 ──
    shadow = QRadialGradient(cx, cy, radius * 1.6)
    shadow.setColorAt(0.0, QColor(255, 255, 255, 0))
    shadow.setColorAt(0.38, QColor(0, 0, 0, 10))
    shadow.setColorAt(0.55, QColor(0, 0, 0, 40))
    shadow.setColorAt(0.72, QColor(0, 0, 0, 80))
    shadow.setColorAt(0.88, QColor(0, 0, 0, 140))
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

    # ── 小高光 ──
    spec = QRadialGradient(cx - radius * 0.28, cy - radius * 0.32, radius * 0.38)
    spec.setColorAt(0.0, QColor(255, 200, 140, 35))
    spec.setColorAt(0.4, QColor(255, 150, 80, 10))
    spec.setColorAt(1.0, QColor(255, 100, 40, 0))
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
            ig.setColorAt(0.78, QColor(255, 80, 20, ga // 2))
            ig.setColorAt(0.90, QColor(255, 80, 20, ga))
            ig.setColorAt(0.97, QColor(255//2, 80//2, 50, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(255, 80, 20, ga // 2))
            og.setColorAt(0.96, QColor(255//2, 80//2, 60, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(255, 80, 20, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)


    p.restore()
