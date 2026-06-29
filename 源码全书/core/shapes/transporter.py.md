# `core/shapes/transporter.py`

> 路径：`core/shapes/transporter.py` | 行数：523


---


```python
# -*- coding: utf-8 -*-
"""
运输舰形态 — 悬浮球变形
真实感设计：多层金属货柜船体 + 装甲板线 + 散热格栅 + 防御炮 + 四引擎
适配悬浮球 ~40px 半径绘制区
"""
import math
import random
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QRadialGradient,
    QLinearGradient, QPainterPath,
)


def paint(p: QPainter, center: QPointF, radius: float, anim_t: float,
          hovered: bool = False, alpha: float = 1.0):
    """绘制运输舰形态"""
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.HighQualityAntialiasing)

    size = radius * 0.95
    w, h = size * 2.4, size * 1.6
    left = center.x() - w / 2
    top = center.y() - h / 2
    cx = left + w / 2

    # === 外层宇宙光晕 ===
    for glow_layer in range(4):
        glow_scale = 1.06 + glow_layer * 0.22
        glow_r = radius * glow_scale
        glow = QRadialGradient(center.x(), center.y(), glow_r)
        ga = max(1, 35 - glow_layer * 8)
        glow.setColorAt(0.0, QColor(255, 255, 255, 0))
        glow.setColorAt(0.25, QColor(200, 200, 255, ga // 2))
        glow.setColorAt(0.55, QColor(120, 140, 255, ga))
        glow.setColorAt(0.80, QColor(60, 80, 200, ga // 2))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(glow)
        p.setPen(Qt.NoPen)
        p.drawEllipse(center, glow_r, glow_r)

    _paint_main_hull(p, cx, left, top, w, h, size, alpha)
    _paint_cargo_modules(p, cx, left, top, w, h, size, alpha)
    _paint_forward_cabin(p, cx, left, top, w, h, size, alpha)
    _paint_superstructure(p, cx, left, top, w, h, size, alpha)
    _paint_armor_panels(p, cx, left, top, w, h, size, alpha)
    _paint_heat_sinks(p, cx, left, top, w, h, size, alpha)
    _paint_rivets(p, cx, left, top, w, h, size, alpha)
    _paint_sensors(p, cx, left, top, w, h, size, anim_t, alpha)
    _paint_antennas(p, cx, left, top, w, h, size, alpha)
    _paint_portholes(p, cx, left, top, w, h, size, anim_t, alpha)
    _paint_engine_nacelles(p, cx, left, top, w, h, size, anim_t, alpha)
    _paint_engine_flames(p, cx, left, top, w, h, size, anim_t, alpha)
    _paint_weapons(p, cx, left, top, w, h, size, anim_t, alpha)
    _paint_lighting(p, cx, left, top, w, h, size, alpha)
    _paint_nav_lights(p, center, size, anim_t, alpha)

    if hovered:
        _paint_hover_glow(p, center, size, anim_t, alpha)


def _paint_main_hull(p, cx, left, top, w, h, size, alpha):
    """主船体 — 箱型货柜轮廓"""
    nose_y = top + h * 0.10
    body_bot_y = top + h * 0.80
    hull_left = left + w * 0.15
    hull_right = left + w * 0.85
    nose_hw = w * 0.03

    # 底层暗面
    shadow_path = QPainterPath()
    shadow_path.moveTo(cx, nose_y - h * 0.015)
    shadow_path.cubicTo(cx + w * 0.05, nose_y + h * 0.02,
                        hull_right, top + h * 0.25,
                        hull_right, body_bot_y)
    shadow_path.lineTo(hull_right + w * 0.01, body_bot_y + h * 0.025)
    shadow_path.lineTo(hull_left - w * 0.01, body_bot_y + h * 0.025)
    shadow_path.lineTo(hull_left, body_bot_y)
    shadow_path.cubicTo(hull_left, top + h * 0.25,
                        cx - w * 0.05, nose_y + h * 0.02,
                        cx, nose_y - h * 0.015)
    shadow_path.closeSubpath()
    p.setBrush(QColor(0x18, 0x1a, 0x20, int(200 * alpha)))
    p.setPen(Qt.NoPen)
    p.drawPath(shadow_path)

    # 中层主体 — 箱型
    hull_path = QPainterPath()
    hull_path.moveTo(cx, nose_y)
    hull_path.cubicTo(cx + nose_hw * 2, nose_y + h * 0.04,
                      hull_right, top + h * 0.22,
                      hull_right, body_bot_y)
    hull_path.lineTo(cx + w * 0.38, body_bot_y + h * 0.03)
    hull_path.lineTo(cx - w * 0.38, body_bot_y + h * 0.03)
    hull_path.lineTo(hull_left, body_bot_y)
    hull_path.cubicTo(hull_left, top + h * 0.22,
                      cx - nose_hw * 2, nose_y + h * 0.04,
                      cx, nose_y)
    hull_path.closeSubpath()

    hull_grad = QLinearGradient(cx, nose_y, cx, body_bot_y)
    hull_grad.setColorAt(0.00, QColor(0x3a, 0x3d, 0x42, int(245 * alpha)))
    hull_grad.setColorAt(0.15, QColor(0x55, 0x58, 0x5e, int(250 * alpha)))
    hull_grad.setColorAt(0.35, QColor(0x7a, 0x7e, 0x85, int(250 * alpha)))
    hull_grad.setColorAt(0.55, QColor(0x5a, 0x5d, 0x63, int(248 * alpha)))
    hull_grad.setColorAt(0.75, QColor(0x3a, 0x3d, 0x42, int(240 * alpha)))
    hull_grad.setColorAt(1.00, QColor(0x22, 0x24, 0x2a, int(235 * alpha)))
    p.setBrush(hull_grad)
    p.setPen(Qt.NoPen)  # was dark outline, removed
    p.drawPath(hull_path)

    # 底部阴影
    shadow_grad = QLinearGradient(cx, body_bot_y, cx, body_bot_y + h * 0.04)
    shadow_grad.setColorAt(0.0, QColor(0x10, 0x12, 0x18, int(160 * alpha)))
    shadow_grad.setColorAt(1.0, QColor(0x10, 0x12, 0x18, 0))
    p.setBrush(shadow_grad)
    p.setPen(Qt.NoPen)
    p.drawRect(QRectF(cx - w * 0.30, body_bot_y + h * 0.02, w * 0.60, h * 0.03))


def _paint_cargo_modules(p, cx, left, top, w, h, size, alpha):
    """货柜模块 — 3 个堆叠的 3D 箱体"""
    cargo_colors = [
        (QColor(0x35, 0x38, 0x3e, int(230 * alpha)),
         QColor(0x60, 0x63, 0x6a, int(225 * alpha)),
         QColor(0x28, 0x2a, 0x30, int(220 * alpha))),
        (QColor(0x32, 0x35, 0x3b, int(230 * alpha)),
         QColor(0x5a, 0x5d, 0x64, int(225 * alpha)),
         QColor(0x25, 0x27, 0x2d, int(220 * alpha))),
        (QColor(0x38, 0x3b, 0x41, int(230 * alpha)),
         QColor(0x62, 0x65, 0x6c, int(225 * alpha)),
         QColor(0x2a, 0x2c, 0x32, int(220 * alpha))),
    ]

    for idx in range(3):
        cw = w * 0.14
        ch = h * 0.22
        cx_idx = cx + (idx - 1) * w * 0.16
        cy_idx = top + h * 0.22

        # 前面板（朝向观察者）
        front_path = QPainterPath()
        front_path.addRect(QRectF(cx_idx - cw / 2, cy_idx, cw, ch))
        front_grad = QLinearGradient(cx_idx - cw / 2, cy_idx, cx_idx + cw / 2, cy_idx)
        front_grad.setColorAt(0.0, QColor(0x30, 0x33, 0x39, int(235 * alpha)))
        front_grad.setColorAt(0.5, QColor(0x68, 0x6b, 0x72, int(230 * alpha)))
        front_grad.setColorAt(1.0, QColor(0x30, 0x33, 0x39, int(225 * alpha)))
        p.setBrush(front_grad)
        p.setPen(Qt.NoPen)  # was dark outline, removed
        p.drawPath(front_path)

        # 顶部面板（3D透视感）
        tp_h = h * 0.04
        top_path = QPainterPath()
        top_path.moveTo(cx_idx - cw * 0.58, cy_idx - tp_h)
        top_path.lineTo(cx_idx - cw / 2, cy_idx)
        top_path.lineTo(cx_idx + cw / 2, cy_idx)
        top_path.lineTo(cx_idx + cw * 0.58, cy_idx - tp_h)
        top_path.closeSubpath()
        top_grad = QLinearGradient(cx_idx - cw / 2, cy_idx - tp_h,
                                   cx_idx - cw / 2, cy_idx)
        top_grad.setColorAt(0.0, QColor(0x50, 0x53, 0x5a, int(215 * alpha)))
        top_grad.setColorAt(1.0, QColor(0x38, 0x3b, 0x42, int(210 * alpha)))
        p.setBrush(top_grad)
        p.setPen(Qt.NoPen)  # was dark outline, removed
        p.drawPath(top_path)

        # 货柜编号标记（小矩形）
        mark_x = cx_idx - cw * 0.2
        mark_w = cw * 0.4
        mark_h = ch * 0.12
        mark_y = cy_idx + ch * 0.2
        p.setBrush(QColor(cargo_colors[idx][0]))
        p.setPen(Qt.NoPen)  # was dark outline, removed
        p.drawRect(QRectF(mark_x, mark_y, mark_w, mark_h))

        # 货柜把手/锁定点
        for si in range(2):
            lx = cx_idx + (si - 0.5) * cw * 0.5
            ly = cy_idx + ch * 0.65
            p.setBrush(QColor(0x1a, 0x1d, 0x22, int(100 * alpha)))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(lx, ly), size * 0.010, size * 0.008)


def _paint_forward_cabin(p, cx, left, top, w, h, size, alpha):
    """前舱 — 驾驶舱模块"""
    fw = w * 0.12
    fh = h * 0.14
    fx = cx - fw / 2
    fy = top + h * 0.14

    cabin_path = QPainterPath()
    cabin_path.addRoundedRect(QRectF(fx, fy, fw, fh), 4, 4)
    cabin_grad = QLinearGradient(cx, fy, cx, fy + fh)
    cabin_grad.setColorAt(0.0, QColor(0x50, 0x53, 0x5a, int(240 * alpha)))
    cabin_grad.setColorAt(0.5, QColor(0x80, 0x84, 0x8c, int(235 * alpha)))
    cabin_grad.setColorAt(1.0, QColor(0x3e, 0x41, 0x48, int(230 * alpha)))
    p.setBrush(cabin_grad)
    p.setPen(Qt.NoPen)  # was dark outline, removed
    p.drawPath(cabin_path)

    # 驾驶舱视窗（大面积弧形舷窗）
    cw = fw * 0.7
    ch = fh * 0.4
    cwx = cx - cw / 2
    cwy = fy + fh * 0.15
    win_grad = QLinearGradient(cwx, cwy, cwx, cwy + ch)
    win_grad.setColorAt(0.0, QColor(140, 200, 240, int(150 * alpha)))
    win_grad.setColorAt(0.5, QColor(60, 160, 220, int(130 * alpha)))
    win_grad.setColorAt(1.0, QColor(20, 80, 140, int(60 * alpha)))
    p.setBrush(win_grad)
    p.setPen(Qt.NoPen)  # was dark outline, removed
    p.drawRoundedRect(QRectF(cwx, cwy, cw, ch), 3, 3)


def _paint_superstructure(p, cx, left, top, w, h, size, alpha):
    """上层建筑 — 舰桥（货柜上方）"""
    bw = w * 0.08
    bh = h * 0.05
    bx = cx - bw / 2
    by = top + h * 0.10

    bridge_path = QPainterPath()
    bridge_path.addRoundedRect(QRectF(bx, by, bw, bh), 3, 3)
    bridge_grad = QLinearGradient(cx, by, cx, by + bh)
    bridge_grad.setColorAt(0.0, QColor(0x60, 0x63, 0x6a, int(240 * alpha)))
    bridge_grad.setColorAt(0.5, QColor(0x88, 0x8c, 0x94, int(235 * alpha)))
    bridge_grad.setColorAt(1.0, QColor(0x45, 0x48, 0x4f, int(230 * alpha)))
    p.setBrush(bridge_grad)
    p.setPen(Qt.NoPen)  # was dark outline, removed
    p.drawPath(bridge_path)

    # 舰桥高光
    hl = QRectF(bx + 1, by + 1, bw - 2, bh * 0.35)
    hl_grad = QLinearGradient(hl.left(), hl.top(), hl.left(), hl.bottom())
    hl_grad.setColorAt(0.0, QColor(255, 255, 255, int(55 * alpha)))
    hl_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(hl_grad)
    p.setPen(Qt.NoPen)
    p.drawRect(hl)


def _paint_armor_panels(p, cx, left, top, w, h, size, alpha):
    """装甲板线 — 8 条"""
    pen = QPen(QColor(0x1a, 0x1d, 0x22, int(70 * alpha)), 0.5)
    p.setPen(pen)

    # 横向装甲线（4条）
    base_y = top + h * 0.42
    for i in range(4):
        ly = base_y + i * h * 0.07 * (1 + i * 0.2)
        hw = w * 0.30 - i * w * 0.01
        p.drawLine(QPointF(cx - hw, ly), QPointF(cx + hw, ly))

    # 纵向装甲线（2条，分列两侧）
    for sign in [-1, 1]:
        p.drawLine(QPointF(cx + sign * w * 0.08, top + h * 0.25),
                   QPointF(cx + sign * w * 0.06, top + h * 0.55))

    # 尾段横线（2条）
    for i in range(2):
        ty = top + h * 0.70 + i * h * 0.04
        thw = w * 0.30 - i * w * 0.02
        p.drawLine(QPointF(cx - thw, ty), QPointF(cx + thw, ty))


def _paint_heat_sinks(p, cx, left, top, w, h, size, alpha):
    """散热格栅 — 两侧各 10 条"""
    pen = QPen(QColor(0x2a, 0x2d, 0x33, int(100 * alpha)), 0.4)
    p.setPen(pen)

    for sign in [-1, 1]:
        sx_base = cx + sign * w * 0.30
        sy_start = top + h * 0.40
        for i in range(10):
            sy = sy_start + i * h * 0.020
            p.drawLine(QPointF(sx_base - sign * size * 0.03, sy),
                       QPointF(sx_base + sign * size * 0.06, sy))


def _paint_rivets(p, cx, left, top, w, h, size, alpha):
    """铆钉点 — 沿货柜装甲线"""
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0x1a, 0x1d, 0x22, int(120 * alpha)))

    rivet_y = [0.42, 0.49, 0.56, 0.63, 0.70, 0.74]
    for ryf in rivet_y:
        ry = top + h * ryf
        hw = w * 0.28
        for sign in [-1, 1]:
            rx = cx + sign * hw * 0.6
            p.drawEllipse(QPointF(rx, ry), size * 0.011, size * 0.011)


def _paint_sensors(p, cx, left, top, w, h, size, anim_t, alpha):
    """传感器阵列 — 船首 4 点"""
    sx = cx
    sy = top + h * 0.12
    for i in range(4):
        ox = (i - 1.5) * size * 0.030
        glow = 0.5 + 0.5 * abs(math.sin(anim_t * 3.5 + i * 0.8))
        sg = QRadialGradient(sx + ox, sy, size * 0.015)
        sg.setColorAt(0.0, QColor(60, 180, 255, int(180 * glow * alpha)))
        sg.setColorAt(1.0, QColor(60, 180, 255, 0))
        p.setBrush(sg)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(sx + ox, sy), size * 0.015, size * 0.015)


def _paint_antennas(p, cx, left, top, w, h, size, alpha):
    """通信天线 — 2 根"""
    for sign in [-1, 1]:
        ant_x = cx + sign * w * 0.04
        ant_base = top + h * 0.095
        ant_tip = top - h * 0.025

        p.setPen(QPen(QColor(0xc0, 0xc4, 0xcc, int(160 * alpha)), 0.5))
        p.drawLine(QPointF(ant_x, ant_base), QPointF(ant_x, ant_tip))

        p.setBrush(QColor(0xc0, 0xc4, 0xcc, int(180 * alpha)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ant_x, ant_tip), size * 0.013, size * 0.013)

    # 主天线（中央）
    main_ant_x = cx
    main_ant_base = top + h * 0.09
    main_ant_tip = top - h * 0.04
    p.setPen(QPen(QColor(0xc0, 0xc4, 0xcc, int(170 * alpha)), 0.6))
    p.drawLine(QPointF(main_ant_x, main_ant_base), QPointF(main_ant_x, main_ant_tip))
    p.setBrush(QColor(0xc0, 0xc4, 0xcc, int(190 * alpha)))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(main_ant_x, main_ant_tip), size * 0.015, size * 0.015)


def _paint_portholes(p, cx, left, top, w, h, size, anim_t, alpha):
    """发光舷窗 — 舰桥 3 个"""
    py = top + h * 0.115
    glow = 0.5 + 0.5 * abs(math.sin(anim_t * 2.5))

    for i in range(3):
        px = cx + (i - 1) * w * 0.02
        p.setBrush(QColor(0xaa, 0xdd, 0xff, int(120 * glow * alpha)))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(px - size * 0.010, py, size * 0.020, size * 0.013), 0.8, 0.8)


def _paint_engine_nacelles(p, cx, left, top, w, h, size, anim_t, alpha):
    """引擎舱 — 4 个引擎，水平排列"""
    engine_y = top + h * 0.82
    pulse = 0.7 + 0.3 * abs(math.sin(anim_t * 4.0))

    for col in range(4):
        offset_x = (col - 1.5) * w * 0.10
        ex = cx + offset_x

        nacelle_grad = QRadialGradient(ex, engine_y, size * 0.075)
        nacelle_grad.setColorAt(0.0, QColor(0x3a, 0x3d, 0x42, int(220 * alpha)))
        nacelle_grad.setColorAt(0.6, QColor(0x2a, 0x2d, 0x33, int(200 * alpha)))
        nacelle_grad.setColorAt(1.0, QColor(0x1a, 0x1d, 0x22, int(100 * alpha)))
        p.setBrush(nacelle_grad)
        p.setPen(Qt.NoPen)  # was dark outline, removed
        p.drawEllipse(QPointF(ex, engine_y), size * 0.075, size * 0.05)

        for ring_i, ring_scale in enumerate([0.7, 0.40]):
            p.setPen(QPen(QColor(0x7a, 0x7e, 0x85, int((80 - ring_i * 20) * pulse * alpha)), 0.35))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(ex, engine_y),
                          size * 0.075 * ring_scale,
                          size * 0.05 * ring_scale)

        core_glow = QRadialGradient(ex, engine_y, size * 0.022)
        core_glow.setColorAt(0.0, QColor(200, 220, 255, int(120 * pulse * alpha)))
        core_glow.setColorAt(1.0, QColor(60, 140, 240, 0))
        p.setBrush(core_glow)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, engine_y), size * 0.022, size * 0.015)


def _paint_engine_flames(p, cx, left, top, w, h, size, anim_t, alpha):
    """引擎尾焰 — 三层叠加，4 个引擎"""
    engine_y = top + h * 0.82
    pulse = 0.55 + 0.45 * abs(math.sin(anim_t * 8.0))

    random.seed(42)
    for col in range(4):
        offset_x = (col - 1.5) * w * 0.10
        ex = cx + offset_x
        length_factor = 1.0 + random.uniform(-0.20, 0.20)

        flame_base_h = size * 0.30 * pulse * length_factor

        # 外层
        outer_a = int(80 * alpha)
        outer_grad = QRadialGradient(ex, engine_y + flame_base_h * 0.3, flame_base_h * 0.80)
        outer_grad.setColorAt(0.0, QColor(0x88, 0xcc, 0xff, outer_a))
        outer_grad.setColorAt(0.5, QColor(0x44, 0x88, 0xcc, outer_a // 2))
        outer_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(outer_grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, engine_y + flame_base_h * 0.15),
                      size * 0.045, flame_base_h * 0.55)

        # 中层
        mid_a = int(180 * alpha)
        mid_grad = QRadialGradient(ex, engine_y + flame_base_h * 0.20, flame_base_h * 0.45)
        mid_grad.setColorAt(0.0, QColor(0x4a, 0xa8, 0xff, mid_a))
        mid_grad.setColorAt(0.6, QColor(0x22, 0x66, 0xcc, mid_a // 2))
        mid_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(mid_grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, engine_y + flame_base_h * 0.08),
                      size * 0.028, flame_base_h * 0.32)

        # 内核
        core_grad = QLinearGradient(ex, engine_y, ex, engine_y + flame_base_h * 0.28)
        core_grad.setColorAt(0.0, QColor(255, 255, 255, int(240 * alpha)))
        core_grad.setColorAt(0.3, QColor(255, 255, 240, int(200 * alpha)))
        core_grad.setColorAt(0.7, QColor(200, 230, 255, int(100 * alpha)))
        core_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(core_grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, engine_y + flame_base_h * 0.03),
                      size * 0.014, flame_base_h * 0.16)


def _paint_weapons(p, cx, left, top, w, h, size, anim_t, alpha):
    """武器系统 — 2 门防御炮，船体上方"""
    charge = 0.4 + 0.6 * abs(math.sin(anim_t * 4.5))

    for sign in [-1, 1]:
        gun_x = cx + sign * w * 0.10
        gun_y = top + h * 0.10
        gun_w = size * 0.035
        gun_h = size * 0.10

        # 炮管
        barrel_path = QPainterPath()
        barrel_path.addRoundedRect(QRectF(gun_x - gun_w / 2, gun_y - gun_h,
                                          gun_w, gun_h), 1.5, 1.5)
        barrel_grad = QLinearGradient(gun_x - gun_w / 2, gun_y, gun_x + gun_w / 2, gun_y)
        barrel_grad.setColorAt(0.0, QColor(0x2a, 0x2d, 0x33, int(220 * alpha)))
        barrel_grad.setColorAt(0.35, QColor(0x5a, 0x5e, 0x65, int(230 * alpha)))
        barrel_grad.setColorAt(0.65, QColor(0x90, 0x94, 0x9c, int(220 * alpha)))
        barrel_grad.setColorAt(1.0, QColor(0x2a, 0x2d, 0x33, int(210 * alpha)))
        p.setBrush(barrel_grad)
        p.setPen(Qt.NoPen)  # was dark outline, removed
        p.drawPath(barrel_path)

        # 高光条
        hl_rect = QRectF(gun_x - gun_w * 0.30, gun_y - gun_h + 1,
                         gun_w * 0.6, gun_h * 0.22)
        hl_grad = QLinearGradient(hl_rect.left(), hl_rect.top(),
                                  hl_rect.left(), hl_rect.bottom())
        hl_grad.setColorAt(0.0, QColor(255, 255, 255, int(75 * alpha)))
        hl_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(hl_grad)
        p.setPen(Qt.NoPen)
        p.drawRect(hl_rect)

        # 炮口能量
        muzzle_x = gun_x
        muzzle_y = gun_y - gun_h
        muzzle_glow = QRadialGradient(muzzle_x, muzzle_y, size * 0.03)
        muzzle_glow.setColorAt(0.0, QColor(255, 150, 30, int(160 * charge * alpha)))
        muzzle_glow.setColorAt(0.6, QColor(255, 80, 15, int(60 * charge * alpha)))
        muzzle_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(muzzle_glow)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(muzzle_x, muzzle_y), size * 0.03, size * 0.03)


def _paint_lighting(p, cx, left, top, w, h, size, alpha):
    """光影 — 顶部高光带"""
    hl_top = top + h * 0.08
    hl_h = h * 0.012
    hl_w = w * 0.45
    hl_grad = QLinearGradient(cx, hl_top, cx, hl_top + hl_h)
    hl_grad.setColorAt(0.0, QColor(255, 255, 255, int(40 * alpha)))
    hl_grad.setColorAt(0.5, QColor(255, 255, 255, int(22 * alpha)))
    hl_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(hl_grad)
    p.setPen(Qt.NoPen)
    p.drawRect(QRectF(cx - hl_w / 2, hl_top, hl_w, hl_h))


def _paint_nav_lights(p, center, size, anim_t, alpha):
    """红绿导航灯"""
    cx, cy = center.x(), center.y()
    for sign, base_color in [(-1, QColor(255, 30, 15)), (1, QColor(15, 255, 35))]:
        nx = cx + sign * size * 0.75
        ny = cy - size * 0.05
        flicker = 0.3 + 0.7 * abs(math.sin(anim_t * 5.0 + sign * 1.5))
        nav_g = QRadialGradient(nx, ny, size * 0.07)
        nav_g.setColorAt(0.0, QColor(base_color.red(), base_color.green(),
                                     base_color.blue(), int(200 * flicker * alpha)))
        nav_g.setColorAt(0.4, QColor(base_color.red(), base_color.green(),
                                     base_color.blue(), int(100 * flicker * alpha)))
        nav_g.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(nav_g)
        p.drawEllipse(QPointF(nx, ny), size * 0.07, size * 0.07)
        p.setBrush(QColor(255, 255, 255, int(180 * flicker * alpha)))
        p.drawEllipse(QPointF(nx, ny), size * 0.022, size * 0.022)


def _paint_hover_glow(p, center, size, anim_t, alpha):
    """Hover 光晕"""
    pulse = 0.7 + 0.3 * abs(math.sin(anim_t * 3.0))
    for i in range(3):
        ir = size * (0.88 + i * 0.12)
        iglow = QRadialGradient(center, ir)
        ga = int((55 - i * 16) * pulse)
        iglow.setColorAt(0.50, QColor(0, 0, 0, 0))
        iglow.setColorAt(0.72, QColor(40, 140, 255, ga // 3))
        iglow.setColorAt(0.85, QColor(0, 120, 240, ga // 2))
        iglow.setColorAt(0.94, QColor(0, 60, 180, ga))
        iglow.setColorAt(1.00, QColor(0, 0, 0, 0))
        p.setBrush(iglow)
        p.setPen(Qt.NoPen)
        p.drawEllipse(center, ir, ir)


```
