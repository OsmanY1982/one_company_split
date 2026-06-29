# `core/shapes/reptilian.py`

> 路径：`core/shapes/reptilian.py` | 行数：294


---


```python
# -*- coding: utf-8 -*-
"""
蜥蜴人 — 3D鳞片质感 + 几丁质甲壳 + 竖瞳 + 分叉舌 + 鳞片弧线纹理
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
    float_y = math.sin(anim_t * 1.4) * radius * 0.04
    float_x = math.cos(anim_t * 1.1) * radius * 0.03
    body_cx = cx + float_x
    body_cy = cy + float_y
    head_r = radius * 0.55
    head_cx = body_cx
    head_cy = body_cy - radius * 0.16

    # ── 远景：暗绿剪影 ──
    silhouette = QRadialGradient(body_cx, body_cy, radius * 1.05)
    silhouette.setColorAt(0.0, QColor(20, 50, 15, 20))
    silhouette.setColorAt(0.5, QColor(10, 30, 8, 10))
    silhouette.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(silhouette); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), radius * 1.05, radius * 1.05)

    # ── 头部：尖椭圆几丁质头骨（QPainterPath）──
    head_path = QPainterPath()
    hw_top = head_r * 0.72
    hw_mid = head_r * 0.58
    hw_jaw = head_r * 0.35
    hh_top = head_r * 0.65
    hh_mid = head_r * 0.30
    hh_jaw = head_r * 0.88

    head_path.moveTo(head_cx + hw_mid * 0.4, head_cy - hh_mid * 0.5)
    head_path.cubicTo(
        head_cx + hw_top, head_cy - hh_top * 0.6,
        head_cx + hw_top * 0.65, head_cy - hh_top,
        head_cx, head_cy - hh_top
    )
    head_path.cubicTo(
        head_cx - hw_top * 0.65, head_cy - hh_top,
        head_cx - hw_top, head_cy - hh_top * 0.6,
        head_cx - hw_mid * 0.4, head_cy - hh_mid * 0.5
    )
    head_path.cubicTo(
        head_cx - hw_mid, head_cy + hh_mid * 0.5,
        head_cx - hw_jaw * 0.7, head_cy + hh_jaw * 0.55,
        head_cx - hw_jaw * 0.35, head_cy + hh_jaw
    )
    head_path.quadTo(head_cx, head_cy + hh_jaw + head_r * 0.05,
                     head_cx + hw_jaw * 0.35, head_cy + hh_jaw)
    head_path.cubicTo(
        head_cx + hw_jaw * 0.7, head_cy + hh_jaw * 0.55,
        head_cx + hw_mid, head_cy + hh_mid * 0.5,
        head_cx + hw_mid * 0.4, head_cy - hh_mid * 0.5
    )
    head_path.closeSubpath()

    # 几丁质渐变：深褐绿 → 绿褐 → 暗绿
    skin_grad = QRadialGradient(head_cx - head_r * 0.18, head_cy - head_r * 0.22, head_r * 1.0)
    skin_grad.setColorAt(0.0, QColor(110, 165, 65))     # 高光绿褐
    skin_grad.setColorAt(0.25, QColor(80, 135, 45))
    skin_grad.setColorAt(0.50, QColor(50, 100, 28))     # 主体
    skin_grad.setColorAt(0.75, QColor(30, 65, 15))      # 暗面
    skin_grad.setColorAt(1.0, QColor(15, 35, 8))        # 边缘
    p.setBrush(skin_grad)
    p.setPen(QPen(QColor(12, 30, 6), 1.5 * s))
    p.drawPath(head_path)

    # ── 鳞片质感：6-8排鳞片弧线 ──
    scale_rng = random.Random(9876)
    # 短弧鳞片纹理
    for row in range(7):
        row_y = head_cy - head_r * 0.42 + row * head_r * 0.12
        row_count = 5 + row
        row_width = head_r * (0.55 + row * 0.06)
        for col in range(row_count):
            sx = head_cx - row_width + col * (row_width * 2 / (row_count - 1)) if row_count > 1 else head_cx
            sy = row_y + scale_rng.uniform(-head_r * 0.02, head_r * 0.02)
            sw = head_r * 0.04
            sh = head_r * 0.025
            scale_path = QPainterPath()
            scale_path.moveTo(sx - sw, sy)
            scale_path.quadTo(sx, sy - sh, sx + sw, sy)
            p.setPen(QPen(QColor(20, 50, 10, 80), 0.6 * s))
            p.setBrush(Qt.NoBrush)
            p.drawPath(scale_path)

    # 甲壳接缝线（深色线条模拟几丁质板接缝）
    p.setPen(QPen(QColor(8, 20, 4, 50), 0.5 * s))
    for i in range(3):
        ly = head_cy - head_r * 0.25 + i * head_r * 0.25
        lx_l = head_cx - head_r * 0.55
        lx_r = head_cx + head_r * 0.55
        p.drawLine(QPointF(lx_l, ly), QPointF(lx_r, ly))

    # 头顶高光区
    spec_hl = QRadialGradient(head_cx - head_r * 0.22, head_cy - head_r * 0.32, head_r * 0.32)
    spec_hl.setColorAt(0.0, QColor(140, 200, 85, 45))
    spec_hl.setColorAt(0.5, QColor(100, 160, 60, 12))
    spec_hl.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(spec_hl); p.setPen(Qt.NoPen)
    p.drawPath(head_path)

    # 下颚阴影
    jaw_shadow = QRadialGradient(head_cx, head_cy + head_r * 0.45, head_r * 0.4)
    jaw_shadow.setColorAt(0.0, QColor(0, 0, 0, 0))
    jaw_shadow.setColorAt(0.5, QColor(8, 20, 4, 35))
    jaw_shadow.setColorAt(1.0, QColor(3, 10, 2, 60))
    p.setBrush(jaw_shadow); p.setPen(Qt.NoPen)
    p.drawPath(head_path)

    # ── 眼睛：竖瞳 + 黄绿虹膜 + 角膜高光 ──
    blink_phase = (anim_t * 0.45) % 5.0
    blink = 1.0
    if blink_phase < 0.15:
        blink = blink_phase / 0.15
    elif blink_phase > 4.85:
        blink = (5.0 - blink_phase) / 0.15

    pupil_scale = 0.7 + 0.05 * math.sin(anim_t * 1.5)

    for sign in (-1, 1):
        ex = head_cx + sign * head_r * 0.22
        ey = head_cy - head_r * 0.12
        # 眼白（黄绿底色）
        eye_white = QRadialGradient(ex, ey, head_r * 0.16)
        eye_white.setColorAt(0.0, QColor(225, 245, 110))
        eye_white.setColorAt(0.5, QColor(190, 210, 70))
        eye_white.setColorAt(1.0, QColor(100, 135, 25))
        p.setBrush(eye_white); p.setPen(QPen(QColor(25, 60, 8), 0.8 * s))
        p.drawEllipse(QRectF(ex - head_r * 0.14, ey - head_r * 0.20 * blink,
                              head_r * 0.28, head_r * 0.40 * blink))

        # 虹膜（横向椭圆）
        iris_rx = head_r * 0.10
        iris_ry = head_r * 0.14 * pupil_scale
        iris_grad = QRadialGradient(ex, ey, iris_rx * 1.1)
        iris_grad.setColorAt(0.0, QColor(180, 200, 50))
        iris_grad.setColorAt(0.5, QColor(130, 160, 30))
        iris_grad.setColorAt(1.0, QColor(40, 80, 10))
        p.setBrush(iris_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, ey), iris_rx, iris_ry)

        # 竖瞳（窄椭圆）
        if blink > 0.2:
            pupil_rx = head_r * 0.035
            pupil_ry = head_r * 0.15 * blink * pupil_scale
            p.setBrush(QColor(3, 8, 1))
            p.drawEllipse(QPointF(ex, ey), pupil_rx, pupil_ry)

        # 角膜高光
        if blink > 0.3:
            p.setBrush(QColor(255, 255, 255, 160))
            p.drawEllipse(QPointF(ex - iris_rx * 0.3, ey - iris_ry * 0.35), pupil_rx * 0.5, pupil_rx * 0.5)

    # ── 鼻孔 ──
    for sign in (-1, 1):
        nx = head_cx + sign * head_r * 0.11
        ny = head_cy + head_r * 0.16
        nostril_grad = QRadialGradient(nx, ny, head_r * 0.06)
        nostril_grad.setColorAt(0.0, QColor(10, 25, 5))
        nostril_grad.setColorAt(1.0, QColor(20, 40, 10, 0))
        p.setBrush(nostril_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(nx, ny), head_r * 0.05, head_r * 0.03)

    # ── 嘴巴 + 分叉舌伸缩 ──
    mouth_path = QPainterPath()
    mouth_cx2 = head_cx
    mouth_cy = head_cy + head_r * 0.36
    mouth_path.moveTo(mouth_cx2 - head_r * 0.22, mouth_cy)
    mouth_path.quadTo(mouth_cx2, mouth_cy + head_r * 0.06, mouth_cx2 + head_r * 0.22, mouth_cy)
    p.setPen(QPen(QColor(10, 25, 5), 0.9 * s))
    p.setBrush(Qt.NoBrush)
    p.drawPath(mouth_path)

    # 分叉舌（周期性伸缩）
    tongue_phase = (anim_t * 1.2) % 6.0
    tongue_extend = 0.0
    if tongue_phase < 0.5:
        tongue_extend = tongue_phase / 0.5
    elif 2.5 < tongue_phase < 3.0:
        tongue_extend = (3.0 - tongue_phase) / 0.5
    if tongue_extend > 0:
        tongue_len = head_r * 0.42 * tongue_extend
        tongue_path = QPainterPath()
        tongue_path.moveTo(mouth_cx2, mouth_cy)
        tongue_path.lineTo(mouth_cx2, mouth_cy + tongue_len * 0.7)
        fork_width = tongue_len * 0.3
        tongue_path.moveTo(mouth_cx2, mouth_cy + tongue_len * 0.5)
        tongue_path.lineTo(mouth_cx2 - fork_width, mouth_cy + tongue_len)
        tongue_path.moveTo(mouth_cx2, mouth_cy + tongue_len * 0.5)
        tongue_path.lineTo(mouth_cx2 + fork_width, mouth_cy + tongue_len)
        p.setPen(QPen(QColor(185, 55, 35, int(200 * tongue_extend)), 1.6 * s))
        p.setBrush(Qt.NoBrush)
        p.drawPath(tongue_path)

    # ── 躯干：3层构造（肩宽下窄）──
    body_rx = head_r * 0.52
    body_ry = head_r * 0.42
    body_cx2 = head_cx
    body_cy2 = body_cy + radius * 0.38

    # 暗面底层
    body_dark = QRadialGradient(body_cx2, body_cy2 + body_ry * 0.25, body_rx * 1.15)
    body_dark.setColorAt(0.0, QColor(12, 30, 6, 60))
    body_dark.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(body_dark); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx2, body_cy2 + body_ry * 0.1), body_rx * 1.15, body_ry * 1.15)

    # 主体中层
    body_grad = QRadialGradient(body_cx2 - body_rx * 0.1, body_cy2 - body_ry * 0.15, body_rx * 1.05)
    body_grad.setColorAt(0.0, QColor(95, 158, 52))
    body_grad.setColorAt(0.4, QColor(65, 125, 32))
    body_grad.setColorAt(0.75, QColor(38, 85, 18))
    body_grad.setColorAt(1.0, QColor(18, 45, 8))
    p.setBrush(body_grad); p.setPen(QPen(QColor(10, 28, 5), 1.0 * s))
    p.drawEllipse(QPointF(body_cx2, body_cy2), body_rx, body_ry)

    # 高光表层
    body_hl = QRadialGradient(body_cx2 - body_rx * 0.22, body_cy2 - body_ry * 0.22, body_rx * 0.38)
    body_hl.setColorAt(0.0, QColor(130, 195, 80, 35))
    body_hl.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(body_hl); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx2, body_cy2), body_rx, body_ry)

    # 身体鳞片纹理
    body_scale_rng = random.Random(7654)
    for _ in range(12):
        bsx = body_cx2 + body_scale_rng.uniform(-body_rx * 0.7, body_rx * 0.7)
        bsy = body_cy2 + body_scale_rng.uniform(-body_ry * 0.6, body_ry * 0.6)
        bsw = body_scale_rng.uniform(2.5, 5.0) * s
        bsh = body_scale_rng.uniform(1.5, 3.0) * s
        p.setBrush(QColor(25, 55, 12, body_scale_rng.randint(15, 35)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(bsx, bsy), bsw, bsh)

    # ── 粒子光环 ──
    aura_rng = random.Random(int(anim_t * 280) % 100000 + 90803)
    p.setPen(Qt.NoPen)
    for _ in range(22):
        a_angle = aura_rng.uniform(0, 2 * math.pi)
        a_dist = radius * (0.58 + 0.42 * aura_rng.random())
        a_offset = anim_t * (0.3 + 0.2 * aura_rng.random())
        ax = cx + math.cos(a_angle + a_offset) * a_dist
        ay = cy + math.sin(a_angle + a_offset) * a_dist * 0.7
        a_size = aura_rng.uniform(0.3, 1.8)
        a_alpha = aura_rng.randint(25, 70)
        ag = QRadialGradient(ax, ay, a_size * 2.5)
        ag.setColorAt(0.0, QColor(80, 200, 60, a_alpha))
        ag.setColorAt(0.5, QColor(40, 100, 70, a_alpha // 2))
        ag.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(ag)
        p.drawEllipse(QPointF(ax, ay), a_size * 2.5, a_size * 2.5)

    # ── hover 光晕（橄榄绿主题）──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        for i in range(3):
            ir = radius + 2 + i * 5
            ig = QRadialGradient(center, ir)
            ga = int((70 - i * 18) * hp)
            ig.setColorAt(0.60, QColor(255, 255, 255, 0))
            ig.setColorAt(0.78, QColor(90, 180, 50, ga // 2))
            ig.setColorAt(0.90, QColor(90, 180, 50, ga))
            ig.setColorAt(0.97, QColor(45, 100, 30, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(90, 180, 50, ga // 2))
            og.setColorAt(0.96, QColor(45, 100, 30, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)

    p.restore()

```
