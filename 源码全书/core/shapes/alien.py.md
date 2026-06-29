# `core/shapes/alien.py`

> 路径：`core/shapes/alien.py` | 行数：306


---


```python
# -*- coding: utf-8 -*-
"""
小绿外星人 — 3D真实感异形头骨 + 曲面光照 + 呼吸瞳孔 + 弹性触角
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
    float_y = math.sin(anim_t * 2.2) * radius * 0.08
    float_x = math.cos(anim_t * 1.7) * radius * 0.04
    body_cx = cx + float_x
    body_cy = cy + float_y
    head_r = radius * 0.62
    head_cx = body_cx
    head_cy = body_cy - radius * 0.18

    # ── 远景：暗色剪影辉光 ──
    silhouette = QRadialGradient(body_cx, body_cy, radius * 1.15)
    silhouette.setColorAt(0.0, QColor(15, 40, 10, 25))
    silhouette.setColorAt(0.5, QColor(8, 25, 5, 12))
    silhouette.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(silhouette); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), radius * 1.15, radius * 1.15)

    # ── 头部：不规则异形头骨（QPainterPath cubicTo）──
    # 倒梨形头骨：上部宽阔隆起，眼窝凹陷，下颌收缩
    head_path = QPainterPath()
    hw_top = head_r * 0.88     # 头顶宽度
    hw_mid = head_r * 0.72     # 眼窝宽度
    hw_eye = head_r * 0.55     # 眼窝凹陷宽度
    hw_jaw = head_r * 0.38     # 下颌宽度
    hh_top = head_r * 0.92     # 头顶高度
    hh_eye = head_r * 0.15     # 眼窝位置
    hh_mid = head_r * 0.40     # 中部
    hh_jaw = head_r * 0.78     # 下颌底

    # 头顶右侧 → 头顶 → 头顶左侧
    head_path.moveTo(head_cx + hw_mid * 0.6, head_cy + hh_eye * 0.4)
    head_path.cubicTo(
        head_cx + hw_top, head_cy - hh_top * 0.5,
        head_cx + hw_top * 0.7, head_cy - hh_top,
        head_cx, head_cy - hh_top
    )
    head_path.cubicTo(
        head_cx - hw_top * 0.7, head_cy - hh_top,
        head_cx - hw_top, head_cy - hh_top * 0.5,
        head_cx - hw_mid * 0.6, head_cy + hh_eye * 0.4
    )
    # 左眼窝凹陷
    head_path.cubicTo(
        head_cx - hw_eye, head_cy - hh_eye * 0.3,
        head_cx - hw_eye * 0.9, head_cy + hh_eye * 1.8,
        head_cx - hw_mid, head_cy + hh_mid * 0.6
    )
    # 左颊 → 下颌
    head_path.cubicTo(
        head_cx - hw_jaw * 0.9, head_cy + hh_jaw * 0.6,
        head_cx - hw_jaw * 0.5, head_cy + hh_jaw,
        head_cx, head_cy + hh_jaw
    )
    # 下颌 → 右颊
    head_path.cubicTo(
        head_cx + hw_jaw * 0.5, head_cy + hh_jaw,
        head_cx + hw_jaw * 0.9, head_cy + hh_jaw * 0.6,
        head_cx + hw_mid, head_cy + hh_mid * 0.6
    )
    # 右眼窝凹陷 → 回起点
    head_path.cubicTo(
        head_cx + hw_eye * 0.9, head_cy + hh_eye * 1.8,
        head_cx + hw_eye, head_cy - hh_eye * 0.3,
        head_cx + hw_mid * 0.6, head_cy + hh_eye * 0.4
    )
    head_path.closeSubpath()

    # 皮肤：QRadialGradient 曲面光照（左上光源）
    skin_grad = QRadialGradient(head_cx - head_r * 0.25, head_cy - head_r * 0.3, head_r * 1.05)
    skin_grad.setColorAt(0.0, QColor(160, 255, 110))   # 高光
    skin_grad.setColorAt(0.18, QColor(130, 230, 85))
    skin_grad.setColorAt(0.40, QColor(90, 200, 55))    # 主色
    skin_grad.setColorAt(0.65, QColor(50, 145, 28))
    skin_grad.setColorAt(0.85, QColor(25, 90, 12))     # 暗面
    skin_grad.setColorAt(1.0, QColor(10, 50, 5))       # 边缘阴影
    p.setBrush(skin_grad)
    p.setPen(QPen(QColor(18, 80, 10), 1.2 * s))
    p.drawPath(head_path)

    # 头顶高光区（左上光源反射）
    spec_hl = QRadialGradient(head_cx - head_r * 0.3, head_cy - head_r * 0.42, head_r * 0.38)
    spec_hl.setColorAt(0.0, QColor(200, 255, 160, 65))
    spec_hl.setColorAt(0.4, QColor(170, 245, 130, 25))
    spec_hl.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(spec_hl); p.setPen(Qt.NoPen)
    p.drawPath(head_path)

    # 下颚阴影区
    jaw_shadow = QRadialGradient(head_cx, head_cy + head_r * 0.5, head_r * 0.5)
    jaw_shadow.setColorAt(0.0, QColor(0, 0, 0, 0))
    jaw_shadow.setColorAt(0.5, QColor(5, 25, 3, 30))
    jaw_shadow.setColorAt(1.0, QColor(2, 10, 1, 60))
    p.setBrush(jaw_shadow); p.setPen(Qt.NoPen)
    p.drawPath(head_path)

    # ── 眼睛：大黑椭圆 + 瞳孔 + 虹膜 + 角膜高光 ──
    eye_spacing = head_r * 0.28
    eye_rx = head_r * 0.22
    eye_ry = head_r * 0.30

    blink_phase = (anim_t * 0.7) % 3.0
    blink = 1.0
    if blink_phase < 0.15:
        blink = blink_phase / 0.15
    elif 2.85 < blink_phase <= 3.0:
        blink = (3.0 - blink_phase) / 0.15

    pupil_scale = 0.65 + 0.04 * math.sin(anim_t * 1.8)  # 呼吸缩放

    for sign in (-1, 1):
        ex = head_cx + sign * eye_spacing
        ey = head_cy - head_r * 0.05
        # 眼白（微绿底色）
        eye_white = QRadialGradient(ex, ey, eye_rx * 1.15)
        eye_white.setColorAt(0.0, QColor(250, 255, 245))
        eye_white.setColorAt(0.6, QColor(235, 250, 235))
        eye_white.setColorAt(1.0, QColor(180, 220, 185))
        p.setBrush(eye_white); p.setPen(QPen(QColor(25, 80, 18), 0.8 * s))
        if blink < 1.0:
            p.drawEllipse(QRectF(ex - eye_rx, ey - eye_ry * blink,
                                  eye_rx * 2, eye_ry * 2 * blink))
        else:
            p.drawEllipse(QPointF(ex, ey), eye_rx, eye_ry)

        # 虹膜（径向渐变，深绿→黑）
        iris_r = eye_rx * 0.78
        iris_grad = QRadialGradient(ex + eye_rx * 0.05, ey - eye_ry * 0.05, iris_r * 1.05)
        iris_grad.setColorAt(0.0, QColor(120, 180, 60))
        iris_grad.setColorAt(0.3, QColor(70, 140, 30))
        iris_grad.setColorAt(0.7, QColor(25, 70, 10))
        iris_grad.setColorAt(1.0, QColor(5, 20, 3))
        p.setBrush(iris_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, ey), iris_r, iris_r)

        # 瞳孔（深黑椭圆，呼吸缩放）
        pupil_rx = iris_r * pupil_scale * 0.55
        pupil_ry = iris_r * pupil_scale * 0.7
        p.setBrush(QColor(3, 8, 1))
        p.drawEllipse(QPointF(ex, ey), pupil_rx, pupil_ry)

        # 角膜高光（双高光点）
        hl1_x = ex - eye_rx * 0.28
        hl1_y = ey - eye_ry * 0.30
        p.setBrush(QColor(255, 255, 255, 210))
        p.drawEllipse(QPointF(hl1_x, hl1_y), pupil_rx * 0.28, pupil_rx * 0.28)
        p.setBrush(QColor(255, 255, 255, 100))
        p.drawEllipse(QPointF(hl1_x + pupil_rx * 0.18, hl1_y + pupil_rx * 0.22),
                      pupil_rx * 0.13, pupil_rx * 0.13)

        # 眼睛微光投射到面部
        eye_glow = QRadialGradient(ex, ey, eye_rx * 2.0)
        eye_glow.setColorAt(0.0, QColor(120, 230, 80, 18))
        eye_glow.setColorAt(0.5, QColor(60, 180, 40, 6))
        eye_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(eye_glow); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, ey), eye_rx * 2.0, eye_rx * 2.0)

    # ── 微笑嘴巴（QPainterPath弧线）──
    mouth_cx = head_cx
    mouth_cy = head_cy + head_r * 0.38
    mouth = QPainterPath()
    mouth.moveTo(mouth_cx - head_r * 0.18, mouth_cy)
    mouth.cubicTo(mouth_cx - head_r * 0.08, mouth_cy + head_r * 0.12,
                  mouth_cx + head_r * 0.08, mouth_cy + head_r * 0.12,
                  mouth_cx + head_r * 0.18, mouth_cy)
    pen_m = QPen(QColor(18, 65, 12), 1.0 * s)
    pen_m.setCapStyle(Qt.RoundCap)
    p.setPen(pen_m); p.setBrush(Qt.NoBrush)
    p.drawPath(mouth)

    # ── 触角（两根，贝塞尔弹性摆动）──
    for side in (-1, 1):
        ant_base_x = head_cx + side * head_r * 0.30
        ant_base_y = head_cy - head_r * 0.80
        ant_len = radius * 0.52
        swing = math.sin(anim_t * 3.5 + side * 1.2) * radius * 0.11
        swing2 = math.cos(anim_t * 4.2 + side * 0.7) * radius * 0.05
        ant_path = QPainterPath()
        ant_path.moveTo(ant_base_x, ant_base_y)
        cp1_x = ant_base_x + side * ant_len * 0.22 + swing
        cp1_y = ant_base_y - ant_len * 0.38
        cp2_x = ant_base_x + side * ant_len * 0.48 + swing * 1.5
        cp2_y = ant_base_y - ant_len * 0.68
        tip_x = ant_base_x + side * ant_len * 0.25 + swing * 1.9 + swing2
        tip_y = ant_base_y - ant_len * 0.88
        ant_path.cubicTo(cp1_x, cp1_y, cp2_x, cp2_y, tip_x, tip_y)
        # 触角渐变
        ant_grad = QLinearGradient(ant_base_x, ant_base_y, tip_x, tip_y)
        ant_grad.setColorAt(0.0, QColor(90, 220, 60))
        ant_grad.setColorAt(0.5, QColor(60, 180, 35))
        ant_grad.setColorAt(1.0, QColor(30, 130, 18))
        pen = QPen(QBrush(ant_grad), 2.2 * s)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawPath(ant_path)
        # 触角末端发光球
        ball_grad = QRadialGradient(tip_x, tip_y, 3.5 * s)
        ball_grad.setColorAt(0.0, QColor(180, 255, 120))
        ball_grad.setColorAt(0.5, QColor(100, 230, 70))
        ball_grad.setColorAt(1.0, QColor(20, 120, 15))
        p.setPen(Qt.NoPen); p.setBrush(ball_grad)
        p.drawEllipse(QPointF(tip_x, tip_y), 3.5 * s, 3.5 * s)

    # ── 躯干：3层构造 ──
    body_rx = head_r * 0.50
    body_ry = head_r * 0.32
    body_cx2 = head_cx
    body_cy2 = head_cy + head_r * 0.92

    # 暗面底层
    body_dark = QRadialGradient(body_cx2, body_cy2 + body_ry * 0.3, body_rx * 1.15)
    body_dark.setColorAt(0.0, QColor(15, 60, 8, 80))
    body_dark.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(body_dark); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx2, body_cy2 + body_ry * 0.15), body_rx * 1.15, body_ry * 1.15)

    # 主体中层（曲面渐变）
    body_grad = QRadialGradient(body_cx2 - body_rx * 0.15, body_cy2 - body_ry * 0.2, body_rx * 1.05)
    body_grad.setColorAt(0.0, QColor(120, 240, 80))
    body_grad.setColorAt(0.35, QColor(85, 200, 55))
    body_grad.setColorAt(0.7, QColor(45, 150, 28))
    body_grad.setColorAt(1.0, QColor(15, 80, 10))
    p.setBrush(body_grad); p.setPen(QPen(QColor(20, 90, 12), 1.0 * s))
    p.drawEllipse(QPointF(body_cx2, body_cy2), body_rx, body_ry)

    # 高光表层
    body_hl = QRadialGradient(body_cx2 - body_rx * 0.3, body_cy2 - body_ry * 0.3, body_rx * 0.45)
    body_hl.setColorAt(0.0, QColor(180, 255, 130, 45))
    body_hl.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(body_hl); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx2, body_cy2), body_rx, body_ry)

    # ── 肩膀连接球 ──
    for sign in (-1, 1):
        shx = body_cx2 + sign * body_rx * 0.85
        shy = body_cy2 - body_ry * 0.35
        sh_grad = QRadialGradient(shx, shy, body_rx * 0.28)
        sh_grad.setColorAt(0.0, QColor(110, 220, 65, 140))
        sh_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(sh_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(shx, shy), body_rx * 0.28, body_rx * 0.28)

    # ── 粒子光环 ──
    aura_rng = random.Random(int(anim_t * 280) % 100000 + 43132)
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
        ag.setColorAt(0.0, QColor(120, 200, 240, a_alpha))
        ag.setColorAt(0.5, QColor(60, 100, 200, a_alpha // 2))
        ag.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(ag)
        p.drawEllipse(QPointF(ax, ay), a_size * 2.5, a_size * 2.5)

    # ── hover 光晕（绿色主题）──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        for i in range(3):
            ir = radius + 2 + i * 5
            ig = QRadialGradient(center, ir)
            ga = int((70 - i * 18) * hp)
            ig.setColorAt(0.60, QColor(255, 255, 255, 0))
            ig.setColorAt(0.78, QColor(100, 230, 80, ga // 2))
            ig.setColorAt(0.90, QColor(100, 230, 80, ga))
            ig.setColorAt(0.97, QColor(50, 150, 40, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(100, 230, 80, ga // 2))
            og.setColorAt(0.96, QColor(50, 150, 40, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)

    p.restore()

```
