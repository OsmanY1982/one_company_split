# -*- coding: utf-8 -*-
"""
冰巨星 — 青蓝渐变+白色冰晶纹理+甲烷吸收带
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

    # ── 外辉光 ──
    for gl in range(4):
        gr = radius * (1.06 + gl * 0.20)
        g = QRadialGradient(cx, cy, gr)
        ga = max(1, 35 - gl * 8)
        g.setColorAt(0.0, QColor(255, 255, 255, 0))
        g.setColorAt(0.25, QColor(180, 220, 255, ga // 2))
        g.setColorAt(0.55, QColor(100, 170, 255, ga))
        g.setColorAt(0.80, QColor(50, 100, 200, ga // 2))
        g.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(g); p.setPen(Qt.NoPen)
        p.drawEllipse(center, gr, gr)

    # ── 球体基底（青→深蓝多层渐变）──
    body = QRadialGradient(cx - radius * 0.13, cy - radius * 0.11, radius * 1.04)
    body.setColorAt(0.0, QColor(160, 225, 240))
    body.setColorAt(0.15, QColor(120, 200, 230))
    body.setColorAt(0.32, QColor(80, 170, 215))
    body.setColorAt(0.50, QColor(50, 135, 195))
    body.setColorAt(0.66, QColor(30, 100, 165))
    body.setColorAt(0.80, QColor(15, 65, 125))
    body.setColorAt(0.92, QColor(8, 35, 80))
    body.setColorAt(1.0, QColor(3, 12, 35))
    p.setBrush(body); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 甲烷吸收带（暗蓝水平条纹）──
    for i in range(6):
        by = cy - radius * 0.60 + radius * 1.20 * i / 5.0
        dx = radius * math.sqrt(max(0, 1 - ((by - cy) / radius) ** 2))
        if dx <= 0:
            continue
        wave = math.sin(anim_t * 0.3 + i * 1.7) * radius * 0.02
        bp = QPainterPath()
        for s in range(25):
            frac = s / 24.0
            bx = cx - dx + 2 * dx * frac
            bw = by + wave + math.sin(frac * 14 + anim_t * 0.7) * radius * 0.01
            if s == 0:
                bp.moveTo(bx, bw)
            else:
                bp.lineTo(bx, bw)
        band_alpha = int(30 + 25 * abs(math.sin(i * 2.1)))
        pen = QPen(QColor(20, 60, 130, band_alpha), radius * 0.06)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawPath(bp)

    # ── 冰晶纹理（六角形冰晶+碎冰亮点）──
    crystal_rng = random.Random(33)
    for _ in range(28):
        hx = cx + crystal_rng.uniform(-radius * 0.82, radius * 0.82)
        hy = cy + crystal_rng.uniform(-radius * 0.82, radius * 0.82)
        if (hx - cx) ** 2 + (hy - cy) ** 2 > (radius * 0.90) ** 2:
            continue
        hs = radius * crystal_rng.uniform(0.015, 0.06)
        hg = QRadialGradient(hx, hy, hs)
        ha = crystal_rng.randint(40, 110)
        hg.setColorAt(0.0, QColor(220, 245, 255, ha))
        hg.setColorAt(0.5, QColor(180, 220, 250, ha // 3))
        hg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(hg); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(hx, hy), hs, hs)
        # 冰晶十字星芒
        if crystal_rng.random() > 0.6:
            cross_pen = QPen(QColor(220, 240, 255, ha // 2), 0.4)
            p.setPen(cross_pen)
            cl = hs * 1.8
            p.drawLine(QPointF(hx - cl, hy), QPointF(hx + cl, hy))
            p.drawLine(QPointF(hx, hy - cl), QPointF(hx, hy + cl))
            p.setPen(Qt.NoPen)

    # ── 雪花飘落动画（表层缓慢旋转的冰晶图案）──
    flake_rng = random.Random(int(anim_t * 180) % 100000 + 7711)
    for _ in range(15):
        fa = flake_rng.uniform(0, 2 * math.pi) + anim_t * 0.12
        fd = radius * flake_rng.uniform(0.20, 0.85)
        fx = cx + math.cos(fa) * fd
        fy = cy + math.sin(fa) * fd
        fs = flake_rng.uniform(0.4, 1.8)
        fg = QRadialGradient(fx, fy, fs * 1.5)
        fa2 = flake_rng.randint(30, 80)
        fg.setColorAt(0.0, QColor(235, 250, 255, fa2))
        fg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(fg); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(fx, fy), fs * 1.5, fs * 1.5)

    # ── 极地雾霭（淡白蓝极冠）──
    for sign in (-1, 1):
        pole = QRadialGradient(cx, cy + sign * radius * 0.65, radius * 0.42)
        pole.setColorAt(0.0, QColor(190, 230, 248, 80))
        pole.setColorAt(0.4, QColor(150, 210, 240, 40))
        pole.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(pole); p.setPen(Qt.NoPen)
        p.drawEllipse(center, radius, radius)

    # ── 高光 ──
    hl = QRadialGradient(cx - radius * 0.24, cy - radius * 0.26, radius * 0.33)
    hl.setColorAt(0.0, QColor(210, 245, 255, 55))
    hl.setColorAt(0.5, QColor(170, 220, 250, 18))
    hl.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(hl); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 暗面 ──
    shadow = QRadialGradient(cx + radius * 0.50, cy + radius * 0.42, radius * 0.78)
    shadow.setColorAt(0.0, QColor(255, 255, 255, 0))
    shadow.setColorAt(0.30, QColor(0, 0, 0, 28))
    shadow.setColorAt(0.52, QColor(0, 0, 0, 80))
    shadow.setColorAt(0.73, QColor(0, 0, 0, 155))
    shadow.setColorAt(0.91, QColor(0, 0, 0, 215))
    shadow.setColorAt(1.0, QColor(0, 0, 0, 240))
    p.setBrush(shadow); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 边缘逆光 ──
    rim_breath = 1.0 + 0.03 * math.sin(anim_t * 2.2)
    rim = QRadialGradient(cx + radius * 0.45, cy + radius * 0.50, radius * 0.50)
    rim.setColorAt(0.0, QColor(255, 255, 255, 0))
    rim.setColorAt(0.55, QColor(255, 255, 255, 0))
    rim.setColorAt(0.78, QColor(160, 220, 255, int(15 * rim_breath)))
    rim.setColorAt(0.92, QColor(120, 180, 255, int(32 * rim_breath)))
    rim.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(rim); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 悬停增强 ──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        for i in range(3):
            ir = radius + 2 + i * 5
            ig = QRadialGradient(center, ir)
            ga = int((70 - i * 18) * hp)
            ig.setColorAt(0.60, QColor(255, 255, 255, 0))
            ig.setColorAt(0.78, QColor(140, 220, 240, ga // 2))
            ig.setColorAt(0.90, QColor(140, 220, 240, ga))
            ig.setColorAt(0.97, QColor(70, 110, 180, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(140, 220, 240, ga // 2))
            og.setColorAt(0.96, QColor(70, 110, 190, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(140, 220, 240, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)

    p.restore()
