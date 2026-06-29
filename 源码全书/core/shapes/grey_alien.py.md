# `core/shapes/grey_alien.py`

> 路径：`core/shapes/grey_alien.py` | 行数：306


---


```python
# -*- coding: utf-8 -*-
"""
灰人 — 3D硅胶质感 + 倒梨形头骨 + 血管纹理 + 超大倾斜眼 + 凝视感
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
    float_y = math.sin(anim_t * 1.5) * radius * 0.05
    float_x = math.cos(anim_t * 1.2) * radius * 0.03
    body_cx = cx + float_x
    body_cy = cy + float_y
    head_r = radius * 0.58
    head_cx = body_cx
    head_cy = body_cy - radius * 0.20

    # ── 远景：冷灰剪影 ──
    silhouette = QRadialGradient(body_cx, body_cy, radius * 1.1)
    silhouette.setColorAt(0.0, QColor(60, 65, 70, 20))
    silhouette.setColorAt(0.5, QColor(40, 43, 48, 10))
    silhouette.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(silhouette); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), radius * 1.1, radius * 1.1)

    # ── 头部：倒梨形头骨（QPainterPath + 3D曲面光照）──
    head_path = QPainterPath()
    hw_top = head_r * 0.82
    hw_mid = head_r * 0.70
    hw_jaw = head_r * 0.36
    hh_top = head_r * 0.95
    hh_mid = head_r * 0.15
    hh_jaw = head_r * 0.72

    head_path.moveTo(head_cx + hw_mid * 0.5, head_cy - hh_top * 0.15)
    head_path.cubicTo(
        head_cx + hw_top * 0.95, head_cy - hh_top * 0.55,
        head_cx + hw_top * 0.6, head_cy - hh_top,
        head_cx, head_cy - hh_top
    )
    head_path.cubicTo(
        head_cx - hw_top * 0.6, head_cy - hh_top,
        head_cx - hw_top * 0.95, head_cy - hh_top * 0.55,
        head_cx - hw_mid * 0.5, head_cy - hh_top * 0.15
    )
    head_path.cubicTo(
        head_cx - hw_mid, head_cy + hh_mid * 0.8,
        head_cx - hw_jaw * 0.85, head_cy + hh_jaw * 0.6,
        head_cx - hw_jaw * 0.45, head_cy + hh_jaw
    )
    head_path.quadTo(head_cx, head_cy + hh_jaw + head_r * 0.03,
                     head_cx + hw_jaw * 0.45, head_cy + hh_jaw)
    head_path.cubicTo(
        head_cx + hw_jaw * 0.85, head_cy + hh_jaw * 0.6,
        head_cx + hw_mid, head_cy + hh_mid * 0.8,
        head_cx + hw_mid * 0.5, head_cy - hh_top * 0.15
    )
    head_path.closeSubpath()

    # 皮肤：QRadialGradient 高反差硅胶感
    skin_grad = QRadialGradient(head_cx - head_r * 0.2, head_cy - head_r * 0.28, head_r * 1.0)
    skin_grad.setColorAt(0.0, QColor(192, 196, 204))    # 亮灰高光
    skin_grad.setColorAt(0.15, QColor(175, 180, 188))
    skin_grad.setColorAt(0.40, QColor(148, 153, 162))   # 主体
    skin_grad.setColorAt(0.68, QColor(115, 120, 130))
    skin_grad.setColorAt(0.88, QColor(88, 92, 100))     # 暗面
    skin_grad.setColorAt(1.0, QColor(60, 64, 72))       # 边缘
    p.setBrush(skin_grad)
    p.setPen(QPen(QColor(70, 74, 80), 1.0 * s))
    p.drawPath(head_path)

    # 微细血管纹理（5-8条极细曲线）
    vein_rng = random.Random(42)
    p.setPen(Qt.NoPen)
    for _ in range(6):
        vx = head_cx + vein_rng.uniform(-head_r * 0.55, head_r * 0.55)
        vy = head_cy + vein_rng.uniform(-head_r * 0.4, head_r * 0.4)
        vr = vein_rng.uniform(1.2, 2.5) * s
        p.setBrush(QColor(100, 105, 115, vein_rng.randint(10, 25)))
        p.drawEllipse(QPointF(vx, vy), vr, vr * 0.4)
    # 细血管曲线
    for _ in range(5):
        path_v = QPainterPath()
        vx0 = head_cx + vein_rng.uniform(-head_r * 0.5, head_r * 0.5)
        vy0 = head_cy + vein_rng.uniform(-head_r * 0.6, head_r * 0.5)
        path_v.moveTo(vx0, vy0)
        cp_vx = vx0 + vein_rng.uniform(-head_r * 0.2, head_r * 0.2)
        cp_vy = vy0 + vein_rng.uniform(head_r * 0.1, head_r * 0.35)
        vx1 = vx0 + vein_rng.uniform(-head_r * 0.15, head_r * 0.15)
        vy1 = vy0 + vein_rng.uniform(head_r * 0.3, head_r * 0.55)
        path_v.quadTo(cp_vx, cp_vy, vx1, vy1)
        p.setPen(QPen(QColor(90, 95, 105, 25), 0.4 * s))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path_v)

    # 头顶高光区
    spec_hl = QRadialGradient(head_cx - head_r * 0.3, head_cy - head_r * 0.38, head_r * 0.35)
    spec_hl.setColorAt(0.0, QColor(220, 225, 230, 55))
    spec_hl.setColorAt(0.5, QColor(200, 205, 215, 18))
    spec_hl.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(spec_hl); p.setPen(Qt.NoPen)
    p.drawPath(head_path)

    # 下颚阴影区
    jaw_shadow = QRadialGradient(head_cx, head_cy + head_r * 0.5, head_r * 0.45)
    jaw_shadow.setColorAt(0.0, QColor(0, 0, 0, 0))
    jaw_shadow.setColorAt(0.5, QColor(40, 42, 48, 30))
    jaw_shadow.setColorAt(1.0, QColor(30, 32, 38, 55))
    p.setBrush(jaw_shadow); p.setPen(Qt.NoPen)
    p.drawPath(head_path)

    # ── 眼睛：超大倾斜椭圆 + 深黑虹膜 + 角膜高光 ──
    eye_spacing = head_r * 0.26
    eye_rx = head_r * 0.27
    eye_ry = head_r * 0.40
    eye_tilt = -9

    blink_phase = (anim_t * 0.5) % 4.0
    blink = 1.0
    if blink_phase < 0.2:
        blink = blink_phase / 0.2
    elif blink_phase > 3.8:
        blink = (4.0 - blink_phase) / 0.2

    pupil_scale = 0.65 + 0.03 * math.sin(anim_t * 1.6)

    for sign in (-1, 1):
        ex = head_cx + sign * eye_spacing
        ey = head_cy - head_r * 0.08
        p.save()
        p.translate(ex, ey)
        p.rotate(sign * eye_tilt)

        # 超大黑色眼球
        eye_grad = QRadialGradient(0, 0, eye_rx * 1.05)
        eye_grad.setColorAt(0.0, QColor(20, 20, 25))
        eye_grad.setColorAt(0.35, QColor(8, 8, 10))
        eye_grad.setColorAt(0.75, QColor(2, 2, 3))
        eye_grad.setColorAt(1.0, QColor(0, 0, 0))
        p.setBrush(eye_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(-eye_rx, -eye_ry * blink, eye_rx * 2, eye_ry * 2 * blink))

        # 暗色虹膜（几乎不可见，融入眼黑）
        iris_r = eye_rx * 0.70 * pupil_scale
        iris_grad = QRadialGradient(0, -eye_ry * 0.05, iris_r)
        iris_grad.setColorAt(0.0, QColor(25, 25, 30))   # 极暗
        iris_grad.setColorAt(1.0, QColor(2, 2, 3))
        p.setBrush(iris_grad)
        p.drawEllipse(QPointF(0, 0), iris_r, iris_r * 1.15)

        # 瞳孔（更暗圆点）
        pup_r = iris_r * 0.35
        p.setBrush(QColor(0, 0, 0))
        p.drawEllipse(QPointF(0, 0), pup_r, pup_r)

        # 角膜高光（双点反射）
        if blink > 0.3:
            pt_grad = QRadialGradient(-eye_rx * 0.35, -eye_ry * 0.33, eye_rx * 0.18)
            pt_grad.setColorAt(0.0, QColor(255, 255, 255, 180))
            pt_grad.setColorAt(0.5, QColor(210, 215, 220, 60))
            pt_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setBrush(pt_grad)
            p.drawEllipse(QPointF(-eye_rx * 0.38, -eye_ry * 0.35), eye_rx * 0.18, eye_ry * blink * 0.18)
            # 小高光点
            p.setBrush(QColor(255, 255, 255, 120))
            p.drawEllipse(QPointF(-eye_rx * 0.22, -eye_ry * 0.42), eye_rx * 0.07, eye_ry * blink * 0.07)

        p.restore()

        # 眼睛微光投射
        eye_glow = QRadialGradient(ex, ey, eye_rx * 1.8)
        eye_glow.setColorAt(0.0, QColor(80, 85, 95, 12))
        eye_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(eye_glow); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, ey), eye_rx * 1.8, eye_rx * 1.8)

    # ── 小鼻孔 ──
    for sign in (-1, 1):
        nx = head_cx + sign * head_r * 0.09
        ny = head_cy + head_r * 0.22
        nostril_grad = QRadialGradient(nx, ny, head_r * 0.06)
        nostril_grad.setColorAt(0.0, QColor(45, 48, 55))
        nostril_grad.setColorAt(1.0, QColor(70, 74, 80, 0))
        p.setBrush(nostril_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(nx, ny), head_r * 0.04, head_r * 0.025)

    # ── 细线嘴 ──
    mouth_path = QPainterPath()
    mouth_path.moveTo(head_cx - head_r * 0.16, head_cy + head_r * 0.38)
    mouth_path.quadTo(head_cx, head_cy + head_r * 0.46, head_cx + head_r * 0.16, head_cy + head_r * 0.38)
    p.setPen(QPen(QColor(55, 58, 65), 0.7 * s))
    p.setBrush(Qt.NoBrush)
    p.drawPath(mouth_path)

    # ── 躯干：3层构造 ──
    body_rx = head_r * 0.38
    body_ry = head_r * 0.48
    body_cx2 = head_cx
    body_cy2 = body_cy + radius * 0.40

    # 暗面底层
    body_dark = QRadialGradient(body_cx2, body_cy2 + body_ry * 0.3, body_rx * 1.2)
    body_dark.setColorAt(0.0, QColor(50, 54, 60, 60))
    body_dark.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(body_dark); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx2, body_cy2 + body_ry * 0.1), body_rx * 1.2, body_ry * 1.2)

    # 主体中层
    body_grad = QRadialGradient(body_cx2 - body_rx * 0.1, body_cy2 - body_ry * 0.15, body_rx * 1.08)
    body_grad.setColorAt(0.0, QColor(168, 174, 182))
    body_grad.setColorAt(0.4, QColor(145, 151, 160))
    body_grad.setColorAt(0.75, QColor(115, 121, 132))
    body_grad.setColorAt(1.0, QColor(85, 90, 100))
    p.setBrush(body_grad); p.setPen(QPen(QColor(70, 75, 82), 0.8 * s))
    p.drawEllipse(QPointF(body_cx2, body_cy2), body_rx, body_ry)

    # 高光表层
    body_hl = QRadialGradient(body_cx2 - body_rx * 0.25, body_cy2 - body_ry * 0.25, body_rx * 0.4)
    body_hl.setColorAt(0.0, QColor(200, 206, 214, 40))
    body_hl.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(body_hl); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx2, body_cy2), body_rx, body_ry)

    # ── 细长胳膊 + 手指 ──
    for sign in (-1, 1):
        arm_path = QPainterPath()
        shoulder_x = body_cx2 + sign * body_rx * 0.85
        shoulder_y = body_cy2 - body_ry * 0.25
        arm_path.moveTo(shoulder_x, shoulder_y)
        elbow_x = shoulder_x + sign * body_rx * 1.5
        elbow_y = body_cy2 + body_ry * 0.2
        arm_path.quadTo(
            shoulder_x + sign * body_rx * 0.8, shoulder_y + body_ry * 0.3,
            elbow_x, elbow_y
        )
        p.setPen(QPen(QColor(120, 126, 136), 2.2 * s))
        p.setBrush(Qt.NoBrush)
        p.drawPath(arm_path)
        # 手指（3根）
        for fi in range(3):
            finger_path = QPainterPath()
            f_angle = -sign * 0.4 + fi * sign * 0.4
            f_len = body_rx * 1.0
            f_tip_x = elbow_x + math.cos(f_angle + math.pi / 2) * f_len
            f_tip_y = elbow_y + math.sin(f_angle + math.pi / 2) * f_len
            finger_path.moveTo(elbow_x, elbow_y)
            finger_path.lineTo(f_tip_x, f_tip_y)
            p.setPen(QPen(QColor(108, 114, 124), 1.0 * s))
            p.drawPath(finger_path)

    # ── 粒子光环 ──
    aura_rng = random.Random(int(anim_t * 280) % 100000 + 87772)
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
        ag.setColorAt(0.0, QColor(140, 150, 160, a_alpha))
        ag.setColorAt(0.5, QColor(70, 75, 130, a_alpha // 2))
        ag.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(ag)
        p.drawEllipse(QPointF(ax, ay), a_size * 2.5, a_size * 2.5)

    # ── hover 光晕（冷白色主题匹配）──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        for i in range(3):
            ir = radius + 2 + i * 5
            ig = QRadialGradient(center, ir)
            ga = int((70 - i * 18) * hp)
            ig.setColorAt(0.60, QColor(255, 255, 255, 0))
            ig.setColorAt(0.78, QColor(180, 185, 195, ga // 2))
            ig.setColorAt(0.90, QColor(180, 185, 195, ga))
            ig.setColorAt(0.97, QColor(90, 95, 110, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(180, 185, 195, ga // 2))
            og.setColorAt(0.96, QColor(90, 95, 120, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)

    p.restore()

```
