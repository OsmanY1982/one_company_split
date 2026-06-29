# -*- coding: utf-8 -*-
"""
熔岩行星 — 深色地壳裂缝+亮橙岩浆脉络+火山热斑
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

    # ── 外辉光（暖色炽热）──
    for gl in range(4):
        gr = radius * (1.06 + gl * 0.20)
        g = QRadialGradient(cx, cy, gr)
        ga = max(1, 35 - gl * 8)
        g.setColorAt(0.0, QColor(255, 255, 255, 0))
        g.setColorAt(0.25, QColor(255, 180, 80, ga // 2))
        g.setColorAt(0.55, QColor(255, 120, 40, ga))
        g.setColorAt(0.80, QColor(180, 60, 20, ga // 2))
        g.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(g); p.setPen(Qt.NoPen)
        p.drawEllipse(center, gr, gr)

    # ── 基底（暗色玄武岩地壳→深灰黑）──
    crust = QRadialGradient(cx - radius * 0.10, cy - radius * 0.10, radius * 1.04)
    crust.setColorAt(0.0, QColor(55, 48, 42))
    crust.setColorAt(0.18, QColor(42, 36, 30))
    crust.setColorAt(0.38, QColor(30, 25, 20))
    crust.setColorAt(0.58, QColor(20, 16, 12))
    crust.setColorAt(0.76, QColor(12, 10, 7))
    crust.setColorAt(0.90, QColor(6, 5, 3))
    crust.setColorAt(1.0, QColor(2, 1, 1))
    p.setBrush(crust); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 地壳龟裂纹理（暗色裂纹网）──
    crack_rng = random.Random(13)
    for _ in range(22):
        sx = cx + crack_rng.uniform(-radius * 0.80, radius * 0.80)
        sy = cy + crack_rng.uniform(-radius * 0.80, radius * 0.80)
        ang = crack_rng.uniform(0, 2 * math.pi)
        length = radius * crack_rng.uniform(0.08, 0.35)
        ex = sx + math.cos(ang) * length
        ey = sy + math.sin(ang) * length
        for seg in range(3):
            frac = seg / 2.0
            inter_x = sx + (ex - sx) * frac + crack_rng.uniform(-0.03, 0.03) * radius
            inter_y = sy + (ey - sy) * frac + crack_rng.uniform(-0.03, 0.03) * radius
            if seg == 0:
                px, py = sx, sy
            elif seg == 1:
                px, py = inter_x, inter_y
            else:
                nx, ny = inter_x, inter_y
                pen = QPen(QColor(15, 12, 9, 130), 0.7)
                p.setPen(pen); p.setBrush(Qt.NoBrush)
                p.drawLine(QPointF(px, py), QPointF(nx, ny))

    # ── 岩浆脉络（亮橙/金黄，沿裂缝流动）──
    lava_rng = random.Random(47)
    for _ in range(16):
        lx = cx + lava_rng.uniform(-radius * 0.75, radius * 0.75)
        ly = cy + lava_rng.uniform(-radius * 0.75, radius * 0.75)
        lang = lava_rng.uniform(0, 2 * math.pi)
        llen = radius * lava_rng.uniform(0.10, 0.45)
        pulse = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5 + lava_rng.random() * 10))
        lpath = QPainterPath()
        lpath.moveTo(lx, ly)
        for j in range(10):
            frac = j / 9.0
            nx = lx + math.cos(lang + frac * 0.6) * llen * frac
            ny = ly + math.sin(lang + frac * 0.6) * llen * frac
            lpath.lineTo(nx, ny)
        # 外辉光（暖色扩散）
        pen_outer = QPen(QColor(255, 100, 15, int(40 * pulse)), radius * 0.06)
        pen_outer.setCapStyle(Qt.RoundCap)
        p.setPen(pen_outer); p.setBrush(Qt.NoBrush)
        p.drawPath(lpath)
        # 内核（白热）
        pen_core = QPen(QColor(255, 220, 100, int(180 * pulse)), radius * 0.012)
        pen_core.setCapStyle(Qt.RoundCap)
        p.setPen(pen_core)
        p.drawPath(lpath)

    # ── 岩浆湖面（大块圆形岩浆汇聚区）──
    pool_rng = random.Random(91)
    for _ in range(6):
        px = cx + pool_rng.uniform(-radius * 0.55, radius * 0.55)
        py = cy + pool_rng.uniform(-radius * 0.55, radius * 0.55)
        pr = radius * pool_rng.uniform(0.06, 0.14)
        if (px - cx) ** 2 + (py - cy) ** 2 > (radius * 0.80) ** 2:
            continue
        pool_pulse = 0.6 + 0.4 * abs(math.sin(anim_t * 2.8 + pool_rng.random() * 7))
        pg = QRadialGradient(px, py, pr * 1.5)
        pg.setColorAt(0.0, QColor(255, 200, 50, int(180 * pool_pulse)))
        pg.setColorAt(0.3, QColor(255, 130, 20, int(120 * pool_pulse)))
        pg.setColorAt(0.6, QColor(220, 60, 10, int(60 * pool_pulse)))
        pg.setColorAt(1.0, QColor(40, 15, 5, 20))
        p.setBrush(pg); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(px, py), pr * 1.5, pr * 1.5)

    # ── 火山热斑闪烁（亮白炽热喷口）──
    vent_rng = random.Random(int(anim_t * 200) % 100000 + 3333)
    for _ in range(10):
        vx = cx + vent_rng.uniform(-radius * 0.65, radius * 0.65)
        vy = cy + vent_rng.uniform(-radius * 0.65, radius * 0.65)
        vs = radius * vent_rng.uniform(0.01, 0.04)
        vp = 0.5 + 0.5 * abs(math.sin(anim_t * vent_rng.uniform(6, 14)))
        vg = QRadialGradient(vx, vy, vs * 2.5)
        vg.setColorAt(0.0, QColor(255, 255, 200, int(200 * vp)))
        vg.setColorAt(0.4, QColor(255, 180, 60, int(100 * vp)))
        vg.setColorAt(1.0, QColor(255, 50, 10, 0))
        p.setBrush(vg); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(vx, vy), vs * 2.5, vs * 2.5)

    # ── 大气烟雾（暗灰尘埃层，半透明覆盖）──
    haze = QRadialGradient(cx, cy, radius * 1.06)
    haze.setColorAt(0.0, QColor(40, 30, 20, 0))
    haze.setColorAt(0.7, QColor(40, 30, 20, 0))
    haze.setColorAt(0.85, QColor(50, 35, 25, 30))
    haze.setColorAt(0.93, QColor(30, 20, 12, 50))
    haze.setColorAt(0.98, QColor(80, 40, 20, 30))
    haze.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(haze); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius * 1.06, radius * 1.06)

    # ── 高光（左上角微弱反光，模拟熔岩反射）──
    hl = QRadialGradient(cx - radius * 0.28, cy - radius * 0.30, radius * 0.28)
    hl.setColorAt(0.0, QColor(255, 150, 60, 35))
    hl.setColorAt(0.6, QColor(200, 100, 30, 10))
    hl.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(hl); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 暗面 ──
    shadow = QRadialGradient(cx + radius * 0.50, cy + radius * 0.42, radius * 0.75)
    shadow.setColorAt(0.0, QColor(255, 255, 255, 0))
    shadow.setColorAt(0.30, QColor(0, 0, 0, 35))
    shadow.setColorAt(0.52, QColor(0, 0, 0, 90))
    shadow.setColorAt(0.73, QColor(0, 0, 0, 170))
    shadow.setColorAt(0.91, QColor(0, 0, 0, 225))
    shadow.setColorAt(1.0, QColor(0, 0, 0, 245))
    p.setBrush(shadow); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

    # ── 边缘逆光（暖色炽热逆光）──
    rim_breath = 1.0 + 0.03 * math.sin(anim_t * 2.2)
    rim = QRadialGradient(cx + radius * 0.45, cy + radius * 0.50, radius * 0.50)
    rim.setColorAt(0.0, QColor(255, 255, 255, 0))
    rim.setColorAt(0.55, QColor(255, 255, 255, 0))
    rim.setColorAt(0.78, QColor(255, 150, 60, int(18 * rim_breath)))
    rim.setColorAt(0.92, QColor(220, 100, 30, int(35 * rim_breath)))
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
            ig.setColorAt(0.78, QColor(255, 120, 30, ga // 2))
            ig.setColorAt(0.90, QColor(255, 120, 30, ga))
            ig.setColorAt(0.97, QColor(128, 60, 25, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(255, 120, 30, ga // 2))
            og.setColorAt(0.96, QColor(128, 60, 35, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(255, 120, 30, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)

    p.restore()
