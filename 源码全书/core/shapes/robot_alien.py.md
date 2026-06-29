# `core/shapes/robot_alien.py`

> 路径：`core/shapes/robot_alien.py` | 行数：322


---


```python
# -*- coding: utf-8 -*-
"""
机器外星人 — 3D金属装甲 + QLinearGradient多段金属渐变 + 面板线 + 铆钉 + 电子眼传感器阵列
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
    float_y = math.sin(anim_t * 1.2) * radius * 0.03
    float_x = math.cos(anim_t * 1.0) * radius * 0.02
    body_cx = cx + float_x
    body_cy = cy + float_y
    head_r = radius * 0.52
    head_cx = body_cx
    head_cy = body_cy - radius * 0.16

    # ── 远景：金属辉光 ──
    silhouette = QRadialGradient(body_cx, body_cy, radius * 1.05)
    silhouette.setColorAt(0.0, QColor(80, 85, 95, 20))
    silhouette.setColorAt(0.5, QColor(50, 54, 62, 10))
    silhouette.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(silhouette); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), radius * 1.05, radius * 1.05)

    # ── 六段金属渐变辅助 ──
    def metal_grad_linear(x1, y1, x2, y2):
        g = QLinearGradient(x1, y1, x2, y2)
        g.setColorAt(0.0, QColor(58, 61, 66))        # 深铁灰
        g.setColorAt(0.18, QColor(74, 78, 85))
        g.setColorAt(0.35, QColor(122, 126, 133))     # 银灰
        g.setColorAt(0.55, QColor(192, 196, 204))     # 高光银
        g.setColorAt(0.72, QColor(130, 134, 141))
        g.setColorAt(0.90, QColor(72, 76, 83))
        g.setColorAt(1.0, QColor(42, 45, 50))         # 边缘
        return g

    # ── 头部：六边形金属头盔 ──
    head_path = QPainterPath()
    hw = head_r * 0.72
    hh = head_r * 0.88
    # 顶部
    head_path.moveTo(head_cx - hw * 0.55, head_cy - hh * 0.65)
    head_path.lineTo(head_cx + hw * 0.55, head_cy - hh * 0.65)
    # 右上斜面
    head_path.lineTo(head_cx + hw, head_cy - hh * 0.15)
    # 右侧
    head_path.lineTo(head_cx + hw * 0.80, head_cy + hh * 0.45)
    # 右下颚
    head_path.lineTo(head_cx + hw * 0.35, head_cy + hh * 0.70)
    # 下颚
    head_path.quadTo(head_cx, head_cy + hh * 0.88,
                     head_cx - hw * 0.35, head_cy + hh * 0.70)
    # 左下颚
    head_path.lineTo(head_cx - hw * 0.80, head_cy + hh * 0.45)
    # 左侧
    head_path.lineTo(head_cx - hw, head_cy - hh * 0.15)
    # 左上斜面
    head_path.lineTo(head_cx - hw * 0.55, head_cy - hh * 0.65)
    head_path.closeSubpath()

    p.setBrush(metal_grad_linear(head_cx, head_cy - hh, head_cx, head_cy + hh))
    p.setPen(QPen(QColor(32, 35, 40), 1.5 * s))
    p.drawPath(head_path)

    # ── 装甲板线（头盔面板分割）──
    p.setPen(QPen(QColor(26, 29, 34), 0.8 * s))
    # 竖向中线
    p.drawLine(QPointF(head_cx, head_cy - hh * 0.65),
               QPointF(head_cx, head_cy + hh * 0.78))
    # 横向面板线（2条）
    for fy in [0.0, 0.35]:
        ly = head_cy - hh * 0.2 + fy * hh * 0.5
        lw = hw * (0.65 + fy * 0.12)
        p.drawLine(QPointF(head_cx - lw, ly), QPointF(head_cx + lw, ly))
    # 侧面板斜线
    for sign in (-1, 1):
        p.drawLine(QPointF(head_cx, head_cy - hh * 0.62),
                   QPointF(head_cx + sign * hw * 0.85, head_cy - hh * 0.18))

    # 铆钉（4个角）
    p.setPen(Qt.NoPen)
    for sign_x in (-1, 1):
        for sign_y in (-1, 1):
            rx = head_cx + sign_x * hw * 0.48
            ry = head_cy + sign_y * hh * 0.42
            rivet_grad = QRadialGradient(rx, ry, 2 * s)
            rivet_grad.setColorAt(0.0, QColor(200, 204, 210))
            rivet_grad.setColorAt(0.6, QColor(140, 144, 150))
            rivet_grad.setColorAt(1.0, QColor(40, 44, 50))
            p.setBrush(rivet_grad)
            p.drawEllipse(QPointF(rx, ry), 2 * s, 2 * s)

    # 头顶高光带（环境光反射）
    p.setBrush(QColor(220, 225, 230, 25))
    p.drawRect(QRectF(head_cx - hw * 0.45, head_cy - hh * 0.62,
                       hw * 0.90, head_r * 0.06))
    # 下颚阴影
    p.setBrush(QColor(0, 0, 0, 25))
    p.drawRect(QRectF(head_cx - hw * 0.30, head_cy + hh * 0.50,
                       hw * 0.60, head_r * 0.08))

    # ── 眼睛：电子传感器阵列（发光圆角矩形面板）──
    eye_panel_rx = head_r * 0.48
    eye_panel_ry = head_r * 0.14
    eye_panel_cy = head_cy - hh * 0.20

    # 面板背景
    panel_rect = QRectF(head_cx - eye_panel_rx, eye_panel_cy - eye_panel_ry,
                         eye_panel_rx * 2, eye_panel_ry * 2)
    panel_grad = QLinearGradient(head_cx, eye_panel_cy - eye_panel_ry,
                                 head_cx, eye_panel_cy + eye_panel_ry)
    panel_grad.setColorAt(0.0, QColor(10, 12, 16))
    panel_grad.setColorAt(0.5, QColor(16, 20, 28))
    panel_grad.setColorAt(1.0, QColor(8, 10, 14))
    p.setBrush(panel_grad); p.setPen(QPen(QColor(60, 65, 75), 0.8 * s))
    p.drawRoundedRect(panel_rect, head_r * 0.06, head_r * 0.06)

    # 传感器眼点（5个发光椭圆）
    eye_pulse = 0.5 + 0.5 * math.sin(anim_t * 3.0)
    for ei in range(5):
        ex = head_cx - eye_panel_rx * 0.7 + ei * eye_panel_rx * 0.35
        ey = eye_panel_cy
        # 背景暗红
        p.setBrush(QColor(25, 8, 5))
        p.drawEllipse(QPointF(ex, ey), head_r * 0.04, head_r * 0.055)
        # 发光核心
        led_grad = QRadialGradient(ex, ey, head_r * 0.04)
        led_grad.setColorAt(0.0, QColor(255, 80, 40, int(220 * eye_pulse)))
        led_grad.setColorAt(0.3, QColor(255, 30, 10, int(160 * eye_pulse)))
        led_grad.setColorAt(0.6, QColor(180, 10, 5, int(80 * eye_pulse)))
        led_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(led_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex + head_r * 0.005, ey), head_r * 0.028, head_r * 0.04)

    # ── 嘴部格栅（散热口）──
    mouth_cx_ = head_cx
    mouth_cy_ = head_cy + hh * 0.20
    grill_rx = head_r * 0.22
    grill_ry = head_r * 0.07
    # 格栅背景
    grill_bg = QLinearGradient(mouth_cx_, mouth_cy_ - grill_ry,
                               mouth_cx_, mouth_cy_ + grill_ry)
    grill_bg.setColorAt(0.0, QColor(8, 10, 14))
    grill_bg.setColorAt(0.5, QColor(14, 16, 22))
    grill_bg.setColorAt(1.0, QColor(6, 8, 12))
    p.setBrush(grill_bg); p.setPen(QPen(QColor(30, 34, 40), 0.6 * s))
    p.drawRoundedRect(QRectF(mouth_cx_ - grill_rx, mouth_cy_ - grill_ry,
                              grill_rx * 2, grill_ry * 2),
                       head_r * 0.03, head_r * 0.03)
    # 格栅竖线
    p.setPen(QPen(QColor(50, 55, 65), 0.4 * s))
    for gi in range(7):
        gx = mouth_cx_ - grill_rx * 0.8 + gi * grill_rx * 0.267
        p.drawLine(QPointF(gx, mouth_cy_ - grill_ry * 0.8),
                   QPointF(gx, mouth_cy_ + grill_ry * 0.8))

    # ── 天线（头顶通信塔）──
    ant_base_x = head_cx
    ant_base_y = head_cy - hh * 0.62
    ant_len = head_r * 0.42
    p.setPen(QPen(QColor(90, 95, 105), 1.5 * s))
    p.drawLine(QPointF(ant_base_x, ant_base_y),
               QPointF(ant_base_x, ant_base_y - ant_len))
    # 天线顶端发光球
    ant_top_y = ant_base_y - ant_len
    ant_glow = QRadialGradient(ant_base_x, ant_top_y, head_r * 0.05)
    ant_glow.setColorAt(0.0, QColor(80, 200, 255, 200))
    ant_glow.setColorAt(0.5, QColor(30, 140, 240, 100))
    ant_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(ant_glow); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(ant_base_x, ant_top_y), head_r * 0.05, head_r * 0.05)

    # 第二根天线（斜侧）
    ant2_x = head_cx + head_r * 0.30
    ant2_y = head_cy - hh * 0.55
    ant2_len = head_r * 0.30
    p.setPen(QPen(QColor(80, 85, 95), 1.0 * s))
    p.drawLine(QPointF(ant2_x, ant2_y),
               QPointF(ant2_x + ant2_len * 0.3, ant2_y - ant2_len))

    # ── 躯干：3层叠装甲板 ──
    body_cx2 = head_cx
    body_cy2 = head_cy + hh * 0.48
    body_rx = head_r * 0.70
    body_ry = head_r * 0.55

    # 暗面底层
    body_dark = QRadialGradient(body_cx2, body_cy2 + body_ry * 0.25, body_rx * 1.2)
    body_dark.setColorAt(0.0, QColor(35, 38, 44, 60))
    body_dark.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(body_dark); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx2, body_cy2 + body_ry * 0.1), body_rx * 1.2, body_ry * 1.2)

    # 主体中层：六边形装甲
    armor_path = QPainterPath()
    aw = body_rx
    ah = body_ry
    armor_path.moveTo(body_cx2 - aw * 0.65, body_cy2 - ah * 0.55)
    armor_path.lineTo(body_cx2 + aw * 0.65, body_cy2 - ah * 0.55)
    armor_path.lineTo(body_cx2 + aw * 0.88, body_cy2 - ah * 0.05)
    armor_path.lineTo(body_cx2 + aw * 0.82, body_cy2 + ah * 0.55)
    armor_path.lineTo(body_cx2 + aw * 0.35, body_cy2 + ah * 0.78)
    armor_path.quadTo(body_cx2, body_cy2 + ah * 0.90,
                      body_cx2 - aw * 0.35, body_cy2 + ah * 0.78)
    armor_path.lineTo(body_cx2 - aw * 0.82, body_cy2 + ah * 0.55)
    armor_path.lineTo(body_cx2 - aw * 0.88, body_cy2 - ah * 0.05)
    armor_path.lineTo(body_cx2 - aw * 0.65, body_cy2 - ah * 0.55)
    armor_path.closeSubpath()

    p.setBrush(metal_grad_linear(body_cx2, body_cy2 - ah, body_cx2, body_cy2 + ah))
    p.setPen(QPen(QColor(28, 31, 36), 1.2 * s))
    p.drawPath(armor_path)

    # 装甲板线（躯干）
    p.setPen(QPen(QColor(22, 25, 30), 0.6 * s))
    p.drawLine(QPointF(body_cx2, body_cy2 - ah * 0.50),
               QPointF(body_cx2, body_cy2 + ah * 0.72))
    for i in range(2):
        ly_ = body_cy2 - ah * 0.10 + i * ah * 0.35
        lw_ = aw * (0.55 + i * 0.15)
        p.drawLine(QPointF(body_cx2 - lw_, ly_), QPointF(body_cx2 + lw_, ly_))

    # 核心反应堆（胸口）
    reactor_cy = body_cy2 - ah * 0.05
    reactor_r = body_rx * 0.22
    reactor_pulse = 0.4 + 0.6 * math.sin(anim_t * 4.0)
    for layer in range(3):
        lr = reactor_r * (0.4 + layer * 0.3)
        la = int((70 - layer * 20) * reactor_pulse)
        reactor_glow = QRadialGradient(body_cx2, reactor_cy, lr)
        reactor_glow.setColorAt(0.0, QColor(100, 200, 255, la))
        reactor_glow.setColorAt(0.5, QColor(50, 140, 240, int(la * 0.5)))
        reactor_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(reactor_glow); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(body_cx2, reactor_cy), lr, lr)
    # 外环
    ring_grad = QRadialGradient(body_cx2, reactor_cy, reactor_r * 1.2)
    ring_grad.setColorAt(0.0, QColor(0, 0, 0, 0))
    ring_grad.setColorAt(0.65, QColor(0, 0, 0, 0))
    ring_grad.setColorAt(0.78, QColor(80, 180, 240, int(160 * reactor_pulse)))
    ring_grad.setColorAt(0.90, QColor(40, 120, 220, int(100 * reactor_pulse)))
    ring_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(ring_grad); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx2, reactor_cy), reactor_r * 1.2, reactor_r * 1.2)
    # 核心白点
    p.setBrush(QColor(255, 255, 255, int(200 * reactor_pulse)))
    p.drawEllipse(QPointF(body_cx2, reactor_cy), reactor_r * 0.15, reactor_r * 0.15)

    # ── 身体铆钉 ──
    for sign_x in (-1, 1):
        for sign_y in (-1, 1):
            rbx = body_cx2 + sign_x * aw * 0.55
            rby = body_cy2 + sign_y * ah * 0.35
            rivet_grad2 = QRadialGradient(rbx, rby, 1.5 * s)
            rivet_grad2.setColorAt(0.0, QColor(190, 195, 202))
            rivet_grad2.setColorAt(0.6, QColor(130, 135, 142))
            rivet_grad2.setColorAt(1.0, QColor(30, 34, 40))
            p.setBrush(rivet_grad2); p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(rbx, rby), 1.5 * s, 1.5 * s)

    # 躯干高光带
    p.setBrush(QColor(200, 205, 215, 20))
    p.drawRect(QRectF(body_cx2 - aw * 0.45, body_cy2 - ah * 0.50,
                       aw * 0.90, body_rx * 0.04))

    # ── 粒子光环 ──
    aura_rng = random.Random(int(anim_t * 280) % 100000 + 11233)
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
        ag.setColorAt(0.0, QColor(120, 180, 255, a_alpha))
        ag.setColorAt(0.5, QColor(60, 100, 220, a_alpha // 2))
        ag.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(ag)
        p.drawEllipse(QPointF(ax, ay), a_size * 2.5, a_size * 2.5)

    # ── hover 光晕（蓝白金属主题）──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        for i in range(3):
            ir = radius + 2 + i * 5
            ig = QRadialGradient(center, ir)
            ga = int((70 - i * 18) * hp)
            ig.setColorAt(0.60, QColor(255, 255, 255, 0))
            ig.setColorAt(0.78, QColor(100, 180, 255, ga // 2))
            ig.setColorAt(0.90, QColor(100, 180, 255, ga))
            ig.setColorAt(0.97, QColor(50, 100, 220, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(100, 180, 255, ga // 2))
            og.setColorAt(0.96, QColor(50, 100, 220, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)

    p.restore()

```
