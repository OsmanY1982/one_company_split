# `core/shapes/octopus_alien.py`

> 路径：`core/shapes/octopus_alien.py` | 行数：258


---


```python
# -*- coding: utf-8 -*-
"""
章鱼星人 — 3D圆头 + 8条贝塞尔触手弹性摆动 + 吸盘荧光 + 皮肤曲面光照
"""
import math, random
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QLinearGradient,
    QColor, QPen, QBrush, QPainterPath
)


def paint(painter: QPainter, center: QPointF, radius: float,
          anim_t: float, hovered: bool, alpha: float):
    cx, cy = center.x(), center.y()
    p = painter
    p.save()
    if alpha < 1.0:
        p.setOpacity(alpha)

    s = radius / 50.0
    float_y = math.sin(anim_t * 1.7) * radius * 0.06
    float_x = math.cos(anim_t * 1.4) * radius * 0.03
    body_cx = cx + float_x
    body_cy = cy + float_y
    head_r = radius * 0.52
    head_cx = body_cx
    head_cy = body_cy - radius * 0.10

    # ── 远景：紫色能量场 ──
    silhouette = QRadialGradient(body_cx, body_cy, radius * 1.08)
    silhouette.setColorAt(0.0, QColor(100, 50, 180, 18))
    silhouette.setColorAt(0.5, QColor(60, 30, 140, 8))
    silhouette.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(silhouette); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), radius * 1.08, radius * 1.08)

    # ── 触手（从头部下方辐射）──
    tentacle_rng = random.Random(31)
    tentacles_data = []
    for i in range(8):
        base_angle = -math.pi / 2 + (i - 3.5) * math.pi / 10
        length = radius * tentacle_rng.uniform(0.55, 0.82)
        thickness = radius * tentacle_rng.uniform(0.07, 0.14)
        swing_phase = tentacle_rng.uniform(0, 2 * math.pi)
        swing_freq = tentacle_rng.uniform(2.0, 3.5)
        tentacles_data.append((base_angle, length, thickness, swing_phase, swing_freq))

    for i, (base_angle, length, thickness, swing_phase, swing_freq) in enumerate(tentacles_data):
        swing = math.sin(anim_t * swing_freq + swing_phase) * radius * 0.13
        swing2 = math.cos(anim_t * swing_freq * 1.4 + swing_phase + 1) * radius * 0.07
        segs = 8
        tent_path = QPainterPath()
        start_x = body_cx + math.cos(base_angle) * head_r * 0.95
        start_y = head_cy + head_r * 0.55
        tent_path.moveTo(start_x, start_y)

        prev_x, prev_y = start_x, start_y
        for seg in range(1, segs + 1):
            t = seg / segs
            seg_swing = swing * t + swing2 * (1 - t) * 0.5
            perp = base_angle + math.pi / 2
            nx = start_x + math.cos(base_angle) * length * t + math.cos(perp) * seg_swing
            ny = start_y + math.sin(base_angle) * length * t + math.sin(perp) * seg_swing * 0.5 + length * t * 0.2
            cx1 = (prev_x + nx) / 2 + math.cos(perp) * seg_swing * 0.15
            cy1 = (prev_y + ny) / 2 + math.sin(perp) * seg_swing * 0.15 * 0.5
            tent_path.quadTo(cx1, cy1, nx, ny)
            prev_x, prev_y = nx, ny

            # 吸盘（沿触手内侧闪烁）
            if seg % 2 == 0:
                sucker_alpha = int(80 + 60 * abs(math.sin(anim_t * 4.0 + i * 0.8 + seg)))
                sucker_grad = QRadialGradient(nx, ny, thickness * 0.5)
                hue = (i * 45 + seg * 20) % 360
                sucker_grad.setColorAt(0.0, QColor.fromHsv(hue, 150, 220, sucker_alpha))
                sucker_grad.setColorAt(0.6, QColor.fromHsv(hue, 180, 160, sucker_alpha // 2))
                sucker_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
                p.setBrush(sucker_grad); p.setPen(Qt.NoPen)
                p.drawEllipse(QPointF(nx, ny), thickness * 0.5, thickness * 0.5)

        # 触手管道（深紫→青渐变，粗线模拟立体管道）
        tent_grad = QLinearGradient(start_x, start_y, prev_x, prev_y)
        hue_t = (i * 40 + 270) % 360
        tent_grad.setColorAt(0.0, QColor.fromHsv(hue_t, 180, 140, 220))
        tent_grad.setColorAt(0.5, QColor.fromHsv(hue_t, 200, 120, 200))
        tent_grad.setColorAt(1.0, QColor.fromHsv(hue_t, 220, 90, 170))
        pen = QPen(QBrush(tent_grad), thickness)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawPath(tent_path)

        # 内层高光细线（模拟触手顶部受光）
        inner_pen = QPen(QColor.fromHsv(hue_t, 120, 200, 50), thickness * 0.3)
        inner_pen.setCapStyle(Qt.RoundCap)
        p.setPen(inner_pen)
        p.drawPath(tent_path)

        # 触手末端吸盘簇球
        tip_grad = QRadialGradient(prev_x, prev_y, thickness * 0.8)
        tip_grad.setColorAt(0.0, QColor.fromHsv(hue_t, 80, 240, 200))
        tip_grad.setColorAt(0.6, QColor.fromHsv(hue_t, 160, 160, 150))
        tip_grad.setColorAt(1.0, QColor.fromHsv(hue_t, 200, 80, 40))
        p.setPen(Qt.NoPen); p.setBrush(tip_grad)
        p.drawEllipse(QPointF(prev_x, prev_y), thickness * 0.8, thickness * 0.8)

    # ── 头部：圆球形 + 3D曲面光照 ──
    head_path = QPainterPath()
    # 头部主体（略微扁椭圆）
    head_path.addEllipse(QPointF(head_cx, head_cy), head_r, head_r * 0.92)
    # 侧边隆起（模拟腮裂结构）
    for sign in (-1, 1):
        bulge_cx = head_cx + sign * head_r * 0.72
        bulge_cy = head_cy + head_r * 0.15
        head_path.addEllipse(QPointF(bulge_cx, bulge_cy), head_r * 0.38, head_r * 0.30)

    head_grad = QRadialGradient(head_cx - head_r * 0.18, head_cy - head_r * 0.20, head_r * 1.08)
    head_grad.setColorAt(0.0, QColor(200, 155, 235))
    head_grad.setColorAt(0.22, QColor(160, 110, 210))
    head_grad.setColorAt(0.52, QColor(110, 65, 165))
    head_grad.setColorAt(0.78, QColor(60, 28, 115))
    head_grad.setColorAt(0.95, QColor(30, 12, 65))
    head_grad.setColorAt(1.0, QColor(12, 4, 30))
    p.setBrush(head_grad); p.setPen(QPen(QColor(70, 30, 130), 1.2 * s))
    p.drawPath(head_path)

    # 头顶高光区
    spec_hl = QRadialGradient(head_cx - head_r * 0.28, head_cy - head_r * 0.30, head_r * 0.33)
    spec_hl.setColorAt(0.0, QColor(230, 200, 255, 55))
    spec_hl.setColorAt(0.5, QColor(190, 150, 240, 15))
    spec_hl.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(spec_hl); p.setPen(Qt.NoPen)
    p.drawPath(head_path)

    # 下颚阴影
    jaw_shadow = QRadialGradient(head_cx, head_cy + head_r * 0.35, head_r * 0.45)
    jaw_shadow.setColorAt(0.0, QColor(0, 0, 0, 0))
    jaw_shadow.setColorAt(0.5, QColor(15, 5, 35, 30))
    jaw_shadow.setColorAt(1.0, QColor(5, 2, 15, 50))
    p.setBrush(jaw_shadow); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(head_cx, head_cy), head_r, head_r * 0.92)

    # ── 眼睛：大椭圆 + 荧光绿瞳孔 + 虹膜 + 角膜高光 ──
    eye_spacing = head_r * 0.28
    eye_rx = head_r * 0.19
    eye_ry = head_r * 0.25
    pupil_scale = 0.62 + 0.04 * math.sin(anim_t * 2.0)

    for sign in (-1, 1):
        ex = head_cx + sign * eye_spacing
        ey = head_cy - head_r * 0.08

        # 眼白
        eye_white = QRadialGradient(ex, ey, eye_rx * 1.12)
        eye_white.setColorAt(0.0, QColor(252, 252, 255))
        eye_white.setColorAt(0.5, QColor(225, 245, 235))
        eye_white.setColorAt(1.0, QColor(170, 210, 195))
        p.setBrush(eye_white); p.setPen(QPen(QColor(50, 25, 90), 1.0 * s))
        p.drawEllipse(QPointF(ex, ey), eye_rx, eye_ry)

        # 虹膜
        iris_rx = eye_rx * 0.70
        iris_ry = eye_ry * 0.60
        iris_grad = QRadialGradient(ex, ey - iris_ry * 0.1, iris_rx)
        iris_grad.setColorAt(0.0, QColor(120, 220, 100))
        iris_grad.setColorAt(0.4, QColor(50, 170, 40))
        iris_grad.setColorAt(0.75, QColor(10, 90, 15))
        iris_grad.setColorAt(1.0, QColor(2, 30, 5))
        p.setBrush(iris_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, ey), iris_rx, iris_ry)

        # 瞳孔（横椭圆、山羊瞳风格）
        pup_rx = iris_rx * pupil_scale * 0.50
        pup_ry = iris_ry * pupil_scale * 0.38
        p.setBrush(QColor(3, 6, 1))
        p.drawEllipse(QPointF(ex, ey), pup_rx, pup_ry)

        # 角膜高光
        hl1_x = ex - eye_rx * 0.3
        hl1_y = ey - eye_ry * 0.3
        p.setBrush(QColor(255, 255, 255, 190))
        p.drawEllipse(QPointF(hl1_x, hl1_y), pup_rx * 0.30, pup_ry * 0.30)
        p.setBrush(QColor(255, 255, 255, 90))
        p.drawEllipse(QPointF(hl1_x + pup_rx * 0.20, hl1_y + pup_ry * 0.25),
                      pup_rx * 0.14, pup_ry * 0.14)

    # ── 嘴巴 ──
    mouth_path = QPainterPath()
    mouth_cx = body_cx
    mouth_cy = head_cy + head_r * 0.28
    mouth_path.moveTo(mouth_cx - head_r * 0.14, mouth_cy)
    mouth_path.cubicTo(mouth_cx - head_r * 0.06, mouth_cy + head_r * 0.12,
                       mouth_cx + head_r * 0.06, mouth_cy + head_r * 0.12,
                       mouth_cx + head_r * 0.14, mouth_cy)
    pen_m = QPen(QColor(35, 12, 70), 1.0 * s)
    pen_m.setCapStyle(Qt.RoundCap)
    p.setPen(pen_m); p.setBrush(Qt.NoBrush)
    p.drawPath(mouth_path)

    # ── 触手间生物荧光微尘 ──
    part_rng = random.Random(int(anim_t * 280) % 100000 + 889)
    p.setPen(Qt.NoPen)
    for _ in range(14):
        pa = part_rng.uniform(0, 2 * math.pi)
        pd = radius * (0.48 + 0.52 * part_rng.random())
        px = body_cx + math.cos(pa) * pd
        py = body_cy + math.sin(pa) * pd
        ps = part_rng.uniform(0.4, 1.5)
        pg = QRadialGradient(px, py, ps * 2)
        ph = part_rng.randint(0, 359)
        pg.setColorAt(0.0, QColor.fromHsv(ph, 150, 255, 50))
        pg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(pg)
        p.drawEllipse(QPointF(px, py), ps * 2, ps * 2)

    # ── 粒子光环 ──
    aura_rng = random.Random(int(anim_t * 280) % 100000 + 88330)
    p.setPen(Qt.NoPen)
    for _ in range(22):
        a_angle = aura_rng.uniform(0, 2 * math.pi)
        a_dist = radius * (0.55 + 0.45 * aura_rng.random())
        a_offset = anim_t * (0.3 + 0.2 * aura_rng.random())
        ax = cx + math.cos(a_angle + a_offset) * a_dist
        ay = cy + math.sin(a_angle + a_offset) * a_dist * 0.7
        a_size = aura_rng.uniform(0.3, 1.8)
        a_alpha = aura_rng.randint(25, 70)
        ag = QRadialGradient(ax, ay, a_size * 2.5)
        ag.setColorAt(0.0, QColor(160, 100, 220, a_alpha))
        ag.setColorAt(0.5, QColor(80, 50, 160, a_alpha // 2))
        ag.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(ag)
        p.drawEllipse(QPointF(ax, ay), a_size * 2.5, a_size * 2.5)

    # ── hover 光晕（紫罗兰主题）──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        for i in range(3):
            ir = radius + 2 + i * 5
            ig = QRadialGradient(center, ir)
            ga = int((70 - i * 18) * hp)
            ig.setColorAt(0.60, QColor(255, 255, 255, 0))
            ig.setColorAt(0.78, QColor(160, 100, 220, ga // 2))
            ig.setColorAt(0.90, QColor(160, 100, 220, ga))
            ig.setColorAt(0.97, QColor(80, 50, 150, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(160, 100, 220, ga // 2))
            og.setColorAt(0.96, QColor(80, 50, 160, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)

    p.restore()

```
