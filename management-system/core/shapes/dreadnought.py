# -*- coding: utf-8 -*-
"""
无畏舰形态 — 悬浮球变形
真实感设计：多重楔形装甲船体 + 密集装甲板线 + 散热格栅 + 主炮阵列 + 副炮炮塔 + 八引擎矩阵
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
    """绘制无畏舰形态"""
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.HighQualityAntialiasing)

    size = radius * 0.95
    w, h = size * 3.0, size * 2.0
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
    _paint_upper_deck(p, cx, left, top, w, h, size, alpha)
    _paint_superstructure(p, cx, left, top, w, h, size, alpha)
    _paint_bridge_complex(p, cx, left, top, w, h, size, alpha)
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
    """主船体 — 重型楔形，三层叠层"""
    nose_y = top + h * 0.03
    body_bot_y = top + h * 0.72
    nose_hw = w * 0.03
    mid_hw = w * 0.32
    tail_hw = w * 0.18

    # 底层暗面剪影（最大轮廓）
    shadow_path = QPainterPath()
    shadow_path.moveTo(cx, nose_y - h * 0.01)
    shadow_path.cubicTo(cx + w * 0.04, nose_y + h * 0.02,
                        cx + mid_hw * 0.9, top + h * 0.30,
                        cx + mid_hw * 0.7, top + h * 0.50)
    shadow_path.lineTo(cx + tail_hw * 0.8, body_bot_y + h * 0.03)
    shadow_path.lineTo(cx - tail_hw * 0.8, body_bot_y + h * 0.03)
    shadow_path.cubicTo(cx - mid_hw * 0.7, top + h * 0.50,
                        cx - mid_hw * 0.9, top + h * 0.30,
                        cx - w * 0.04, nose_y + h * 0.02)
    shadow_path.closeSubpath()
    p.setBrush(QColor(0x18, 0x1a, 0x20, int(200 * alpha)))
    p.setPen(Qt.NoPen)
    p.drawPath(shadow_path)

    # 中层主体 — 楔形船体
    hull_path = QPainterPath()
    hull_path.moveTo(cx, nose_y)
    hull_path.cubicTo(cx + nose_hw * 2, nose_y + h * 0.03,
                      cx + mid_hw, top + h * 0.28,
                      cx + mid_hw * 0.85, top + h * 0.48)
    hull_path.lineTo(cx + tail_hw, body_bot_y)
    hull_path.lineTo(cx - tail_hw, body_bot_y)
    hull_path.cubicTo(cx - mid_hw * 0.85, top + h * 0.48,
                      cx - mid_hw, top + h * 0.28,
                      cx - nose_hw * 2, nose_y + h * 0.03)
    hull_path.closeSubpath()

    hull_grad = QLinearGradient(cx, nose_y, cx, body_bot_y)
    hull_grad.setColorAt(0.00, QColor(0x3a, 0x3d, 0x42, int(245 * alpha)))
    hull_grad.setColorAt(0.12, QColor(0x50, 0x53, 0x5a, int(250 * alpha)))
    hull_grad.setColorAt(0.30, QColor(0x7a, 0x7e, 0x85, int(250 * alpha)))
    hull_grad.setColorAt(0.50, QColor(0x5a, 0x5d, 0x63, int(248 * alpha)))
    hull_grad.setColorAt(0.72, QColor(0x3a, 0x3d, 0x42, int(240 * alpha)))
    hull_grad.setColorAt(1.00, QColor(0x22, 0x24, 0x2a, int(235 * alpha)))
    p.setBrush(hull_grad)
    p.setPen(Qt.NoPen)  # was dark outline, removed
    p.drawPath(hull_path)

    # 底部阴影
    shadow_grad = QLinearGradient(cx, body_bot_y, cx, body_bot_y + h * 0.05)
    shadow_grad.setColorAt(0.0, QColor(0x10, 0x12, 0x18, int(160 * alpha)))
    shadow_grad.setColorAt(1.0, QColor(0x10, 0x12, 0x18, 0))
    p.setBrush(shadow_grad)
    p.setPen(Qt.NoPen)
    p.drawRect(QRectF(cx - w * 0.14, body_bot_y, w * 0.28, h * 0.05))


def _paint_upper_deck(p, cx, left, top, w, h, size, alpha):
    """上层装甲甲板"""
    ud_top = top + h * 0.05
    ud_bot = top + h * 0.20
    ud_hw_top = w * 0.06
    ud_hw_bot = w * 0.24

    path = QPainterPath()
    path.moveTo(cx, ud_top)
    path.cubicTo(cx + ud_hw_top * 0.5, ud_top + h * 0.02,
                 cx + ud_hw_bot * 0.5, top + h * 0.14,
                 cx + ud_hw_bot, ud_bot)
    path.lineTo(cx - ud_hw_bot, ud_bot)
    path.cubicTo(cx - ud_hw_bot * 0.5, top + h * 0.14,
                 cx - ud_hw_top * 0.5, ud_top + h * 0.02,
                 cx, ud_top)
    path.closeSubpath()

    ud_grad = QLinearGradient(cx, ud_top, cx, ud_bot)
    ud_grad.setColorAt(0.0, QColor(0x50, 0x53, 0x5a, int(240 * alpha)))
    ud_grad.setColorAt(0.5, QColor(0x85, 0x89, 0x91, int(235 * alpha)))
    ud_grad.setColorAt(1.0, QColor(0x42, 0x45, 0x4c, int(230 * alpha)))
    p.setBrush(ud_grad)
    p.setPen(Qt.NoPen)  # was dark outline, removed
    p.drawPath(path)


def _paint_superstructure(p, cx, left, top, w, h, size, alpha):
    """上层建筑 — 指挥塔基座"""
    ss_top = top + h * 0.06
    ss_bot = top + h * 0.15
    ss_hw_top = w * 0.03
    ss_hw_bot = w * 0.09

    path = QPainterPath()
    path.moveTo(cx, ss_top)
    path.lineTo(cx + ss_hw_top, ss_top + h * 0.015)
    path.lineTo(cx + ss_hw_bot, ss_bot)
    path.lineTo(cx - ss_hw_bot, ss_bot)
    path.lineTo(cx - ss_hw_top, ss_top + h * 0.015)
    path.closeSubpath()

    ss_grad = QLinearGradient(cx, ss_top, cx, ss_bot)
    ss_grad.setColorAt(0.0, QColor(0x5a, 0x5e, 0x65, int(240 * alpha)))
    ss_grad.setColorAt(0.5, QColor(0x90, 0x94, 0x9c, int(235 * alpha)))
    ss_grad.setColorAt(1.0, QColor(0x48, 0x4c, 0x53, int(230 * alpha)))
    p.setBrush(ss_grad)
    p.setPen(Qt.NoPen)  # was dark outline, removed
    p.drawPath(path)


def _paint_bridge_complex(p, cx, left, top, w, h, size, alpha):
    """舰桥复合体 — 主舰桥+副塔"""
    # 主舰桥
    bb_w = w * 0.10
    bb_h = h * 0.065
    bb_x = cx - bb_w / 2
    bb_y = top + h * 0.16
    bb_path = QPainterPath()
    bb_path.addRoundedRect(QRectF(bb_x, bb_y, bb_w, bb_h), 3, 3)
    bb_grad = QLinearGradient(cx, bb_y, cx, bb_y + bb_h)
    bb_grad.setColorAt(0.0, QColor(0x68, 0x6c, 0x73, int(240 * alpha)))
    bb_grad.setColorAt(0.5, QColor(0x98, 0x9c, 0xa4, int(235 * alpha)))
    bb_grad.setColorAt(1.0, QColor(0x48, 0x4c, 0x53, int(230 * alpha)))
    p.setBrush(bb_grad)
    p.setPen(Qt.NoPen)  # was dark outline, removed
    p.drawPath(bb_path)

    # 舰桥高光
    hl = QRectF(bb_x + 2, bb_y + 1, bb_w - 4, bb_h * 0.3)
    hl_grad = QLinearGradient(hl.left(), hl.top(), hl.left(), hl.bottom())
    hl_grad.setColorAt(0.0, QColor(255, 255, 255, int(55 * alpha)))
    hl_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(hl_grad)
    p.setPen(Qt.NoPen)
    p.drawRect(hl)

    # 副塔（右侧通信阵列）
    at_w = w * 0.03
    at_h = h * 0.08
    at_x = cx + w * 0.12
    at_y = top + h * 0.10
    at_path = QPainterPath()
    at_path.addRoundedRect(QRectF(at_x, at_y, at_w, at_h), 2, 2)
    at_grad = QLinearGradient(at_x, at_y, at_x + at_w, at_y)
    at_grad.setColorAt(0.0, QColor(0x55, 0x58, 0x5e, int(230 * alpha)))
    at_grad.setColorAt(0.6, QColor(0x80, 0x84, 0x8c, int(225 * alpha)))
    at_grad.setColorAt(1.0, QColor(0x40, 0x43, 0x4a, int(220 * alpha)))
    p.setBrush(at_grad)
    p.setPen(Qt.NoPen)  # was dark outline, removed
    p.drawPath(at_path)


def _paint_armor_panels(p, cx, left, top, w, h, size, alpha):
    """装甲板线 — 12 条密集分割线"""
    pen = QPen(QColor(0x1a, 0x1d, 0x22, int(70 * alpha)), 0.5)
    p.setPen(pen)

    # 中段横向装甲线（6条）
    base_y = top + h * 0.26
    for i in range(6):
        ly = base_y + i * h * 0.05 * (1 + i * 0.15)
        frac = (ly - top) / h
        hw = w * (0.28 - frac * 0.22)
        p.drawLine(QPointF(cx - hw, ly), QPointF(cx + hw, ly))

    # V形装甲线（2条）
    v_center_y = top + h * 0.56
    for sign in [-1, 1]:
        vx1 = cx + sign * w * 0.18
        vx2 = cx + sign * w * 0.05
        vy1 = v_center_y
        vy2 = v_center_y + h * 0.08
        p.drawLine(QPointF(vx1, vy1), QPointF(vx2, vy2))

    # 船首纵向线（2条）
    for sign in [-1, 1]:
        p.drawLine(QPointF(cx + sign * w * 0.04, top + h * 0.10),
                   QPointF(cx + sign * w * 0.03, top + h * 0.22))

    # 上层甲板横线（2条）
    for i in range(2):
        ly = top + h * (0.12 + i * 0.04)
        hw = w * 0.12 - i * w * 0.02
        p.drawLine(QPointF(cx - hw, ly), QPointF(cx + hw, ly))


def _paint_heat_sinks(p, cx, left, top, w, h, size, alpha):
    """散热格栅 — 两侧各 15 条"""
    pen = QPen(QColor(0x2a, 0x2d, 0x33, int(100 * alpha)), 0.4)
    p.setPen(pen)

    for sign in [-1, 1]:
        sx_base = cx + sign * w * 0.26
        sy_start = top + h * 0.34
        for i in range(15):
            sy = sy_start + i * h * 0.016
            p.drawLine(QPointF(sx_base - sign * size * 0.03, sy),
                       QPointF(sx_base + sign * size * 0.08, sy))


def _paint_rivets(p, cx, left, top, w, h, size, alpha):
    """铆钉点 — 10 个沿装甲板线分布"""
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0x1a, 0x1d, 0x22, int(120 * alpha)))

    rivet_y = [0.26, 0.31, 0.36, 0.41, 0.46, 0.51, 0.56, 0.61]
    for ryf in rivet_y:
        ry = top + h * ryf
        frac = (ry - top) / h
        hw = w * (0.28 - frac * 0.22)
        for sign in [-1, 1]:
            rx = cx + sign * hw * 0.55
            p.drawEllipse(QPointF(rx, ry), size * 0.012, size * 0.012)

    # 上层甲板铆钉
    for ryf in [0.10, 0.14]:
        ry = top + h * ryf
        hw = w * 0.08
        for sign in [-1, 1]:
            rx = cx + sign * hw * 0.6
            p.drawEllipse(QPointF(rx, ry), size * 0.010, size * 0.010)


def _paint_sensors(p, cx, left, top, w, h, size, anim_t, alpha):
    """传感器阵列 — 船首 6 点"""
    sx = cx
    sy = top + h * 0.05
    for i in range(6):
        ox = (i - 2.5) * size * 0.030
        glow = 0.5 + 0.5 * abs(math.sin(anim_t * 3.5 + i * 0.8))
        sg = QRadialGradient(sx + ox, sy, size * 0.016)
        sg.setColorAt(0.0, QColor(60, 180, 255, int(180 * glow * alpha)))
        sg.setColorAt(1.0, QColor(60, 180, 255, 0))
        p.setBrush(sg)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(sx + ox, sy), size * 0.016, size * 0.016)


def _paint_antennas(p, cx, left, top, w, h, size, alpha):
    """通信天线 — 3 根（1主+2从，不对称高度）"""
    # 主天线
    ant_x = cx
    ant_base = top + h * 0.06
    ant_tip = top - h * 0.07
    p.setPen(QPen(QColor(0xc0, 0xc4, 0xcc, int(170 * alpha)), 0.8))
    p.drawLine(QPointF(ant_x, ant_base), QPointF(ant_x, ant_tip))
    p.setBrush(QColor(0xc0, 0xc4, 0xcc, int(190 * alpha)))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(ant_x, ant_tip), size * 0.017, size * 0.017)

    # 横臂
    ant_mid = top + h * 0.02
    p.setPen(QPen(QColor(0xc0, 0xc4, 0xcc, int(110 * alpha)), 0.4))
    p.drawLine(QPointF(ant_x - size * 0.04, ant_mid), QPointF(ant_x + size * 0.04, ant_mid))

    # 副天线
    for sign, height_ratio in [(-1, 0.70), (1, 0.50)]:
        sax = cx + sign * w * 0.07
        sabase = top + h * 0.08
        satip = top - h * 0.07 * height_ratio
        p.setPen(QPen(QColor(0xb0, 0xb4, 0xbc, int(140 * alpha)), 0.5))
        p.drawLine(QPointF(sax, sabase), QPointF(sax, satip))
        p.setBrush(QColor(0xb0, 0xb4, 0xbc, int(160 * alpha)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(sax, satip), size * 0.012, size * 0.012)


def _paint_portholes(p, cx, left, top, w, h, size, anim_t, alpha):
    """发光舷窗 — 舰桥区域 5 个"""
    py = top + h * 0.175
    glow = 0.5 + 0.5 * abs(math.sin(anim_t * 2.5))

    for i in range(5):
        px = cx + (i - 2) * w * 0.015
        p.setBrush(QColor(0xaa, 0xdd, 0xff, int(120 * glow * alpha)))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(px - size * 0.010, py, size * 0.020, size * 0.014), 0.8, 0.8)

    # 副塔舷窗
    at_py = top + h * 0.12
    for i in range(2):
        at_px = cx + w * 0.12 + w * 0.015
        p.setBrush(QColor(0xaa, 0xdd, 0xff, int(100 * glow * alpha)))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(at_px + i * w * 0.010, at_py, size * 0.015, size * 0.010), 0.5, 0.5)


def _paint_engine_nacelles(p, cx, left, top, w, h, size, anim_t, alpha):
    """引擎舱 — 8 个引擎，双排4x2矩阵"""
    pulse = 0.7 + 0.3 * abs(math.sin(anim_t * 4.0))

    engine_y_top = top + h * 0.74
    engine_y_bot = top + h * 0.80

    for row_idx, ey in enumerate([engine_y_top, engine_y_bot]):
        nacelle_rx = size * (0.065 if row_idx == 0 else 0.072)
        nacelle_ry = size * (0.042 if row_idx == 0 else 0.048)
        for col in range(4):
            offset_x = (col - 1.5) * w * 0.06
            ex = cx + offset_x

            nacelle_grad = QRadialGradient(ex, ey, nacelle_rx)
            nacelle_grad.setColorAt(0.0, QColor(0x3a, 0x3d, 0x42, int(220 * alpha)))
            nacelle_grad.setColorAt(0.6, QColor(0x2a, 0x2d, 0x33, int(200 * alpha)))
            nacelle_grad.setColorAt(1.0, QColor(0x1a, 0x1d, 0x22, int(100 * alpha)))
            p.setBrush(nacelle_grad)
            p.setPen(Qt.NoPen)  # was dark outline, removed
            p.drawEllipse(QPointF(ex, ey), nacelle_rx, nacelle_ry)

            for ring_i, ring_scale in enumerate([0.7, 0.40]):
                p.setPen(QPen(QColor(0x7a, 0x7e, 0x85, int((80 - ring_i * 20) * pulse * alpha)), 0.35))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(QPointF(ex, ey),
                              nacelle_rx * ring_scale,
                              nacelle_ry * ring_scale)

            core_glow = QRadialGradient(ex, ey, nacelle_rx * 0.25)
            core_glow.setColorAt(0.0, QColor(200, 220, 255, int(120 * pulse * alpha)))
            core_glow.setColorAt(1.0, QColor(60, 140, 240, 0))
            p.setBrush(core_glow)
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(ex, ey), nacelle_rx * 0.25, nacelle_ry * 0.25)


def _paint_engine_flames(p, cx, left, top, w, h, size, anim_t, alpha):
    """引擎尾焰 — 8 个引擎，三层叠加"""
    pulse = 0.55 + 0.45 * abs(math.sin(anim_t * 8.0))

    engine_pairs = [(top + h * 0.74, size * 0.28), (top + h * 0.80, size * 0.32)]
    random.seed(42)

    for row_idx, (ey, base_flame_h) in enumerate(engine_pairs):
        for col in range(4):
            offset_x = (col - 1.5) * w * 0.06
            ex = cx + offset_x
            length_factor = 1.0 + random.uniform(-0.20, 0.20)

            flame_base_h = base_flame_h * pulse * length_factor

            # 外层
            outer_a = int(80 * alpha)
            outer_grad = QRadialGradient(ex, ey + flame_base_h * 0.3, flame_base_h * 0.75)
            outer_grad.setColorAt(0.0, QColor(0x88, 0xcc, 0xff, outer_a))
            outer_grad.setColorAt(0.5, QColor(0x44, 0x88, 0xcc, outer_a // 2))
            outer_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setBrush(outer_grad)
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(ex, ey + flame_base_h * 0.15),
                          size * 0.04, flame_base_h * 0.50)

            # 中层
            mid_a = int(180 * alpha)
            mid_grad = QRadialGradient(ex, ey + flame_base_h * 0.20, flame_base_h * 0.42)
            mid_grad.setColorAt(0.0, QColor(0x4a, 0xa8, 0xff, mid_a))
            mid_grad.setColorAt(0.6, QColor(0x22, 0x66, 0xcc, mid_a // 2))
            mid_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setBrush(mid_grad)
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(ex, ey + flame_base_h * 0.08),
                          size * 0.024, flame_base_h * 0.28)

            # 内核
            core_grad = QLinearGradient(ex, ey, ex, ey + flame_base_h * 0.25)
            core_grad.setColorAt(0.0, QColor(255, 255, 255, int(240 * alpha)))
            core_grad.setColorAt(0.3, QColor(255, 255, 240, int(200 * alpha)))
            core_grad.setColorAt(0.7, QColor(200, 230, 255, int(100 * alpha)))
            core_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setBrush(core_grad)
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(ex, ey + flame_base_h * 0.03),
                          size * 0.012, flame_base_h * 0.14)


def _paint_weapons(p, cx, left, top, w, h, size, anim_t, alpha):
    """武器系统 — 4 门主炮（船首重型）+ 6 门副炮（舷侧炮塔）"""
    charge = 0.4 + 0.6 * abs(math.sin(anim_t * 4.5))

    # === 4 门主炮 — 重型，粗长 ===
    main_gun_configs = [
        (cx - w * 0.10, top + h * 0.35, size * 0.06, size * 0.20),
        (cx + w * 0.10, top + h * 0.35, size * 0.06, size * 0.20),
        (cx - w * 0.04, top + h * 0.38, size * 0.055, size * 0.22),
        (cx + w * 0.04, top + h * 0.38, size * 0.055, size * 0.22),
    ]

    for gun_x, gun_y, gun_w, gun_h in main_gun_configs:
        barrel_path = QPainterPath()
        barrel_path.addRoundedRect(QRectF(gun_x - gun_w / 2, gun_y - gun_h,
                                          gun_w, gun_h), 2.5, 2.5)
        barrel_grad = QLinearGradient(gun_x - gun_w / 2, gun_y, gun_x + gun_w / 2, gun_y)
        barrel_grad.setColorAt(0.0, QColor(0x2a, 0x2d, 0x33, int(220 * alpha)))
        barrel_grad.setColorAt(0.30, QColor(0x55, 0x58, 0x5e, int(230 * alpha)))
        barrel_grad.setColorAt(0.50, QColor(0x90, 0x94, 0x9c, int(225 * alpha)))
        barrel_grad.setColorAt(0.70, QColor(0x55, 0x58, 0x5e, int(220 * alpha)))
        barrel_grad.setColorAt(1.0, QColor(0x2a, 0x2d, 0x33, int(210 * alpha)))
        p.setBrush(barrel_grad)
        p.setPen(Qt.NoPen)  # was dark outline, removed
        p.drawPath(barrel_path)

        # 高光条
        hl_rect = QRectF(gun_x - gun_w * 0.30, gun_y - gun_h + 2,
                         gun_w * 0.6, gun_h * 0.20)
        hl_grad = QLinearGradient(hl_rect.left(), hl_rect.top(),
                                  hl_rect.left(), hl_rect.bottom())
        hl_grad.setColorAt(0.0, QColor(255, 255, 255, int(80 * alpha)))
        hl_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(hl_grad)
        p.setPen(Qt.NoPen)
        p.drawRect(hl_rect)

        # 炮口能量
        muzzle_x = gun_x
        muzzle_y = gun_y - gun_h
        muzzle_glow = QRadialGradient(muzzle_x, muzzle_y, size * 0.045)
        muzzle_glow.setColorAt(0.0, QColor(255, 150, 30, int(180 * charge * alpha)))
        muzzle_glow.setColorAt(0.6, QColor(255, 80, 15, int(80 * charge * alpha)))
        muzzle_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(muzzle_glow)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(muzzle_x, muzzle_y), size * 0.045, size * 0.045)

    # === 6 门副炮 — 舷侧炮塔 ===
    secondary_configs = [
        (cx - w * 0.25, top + h * 0.42, size * 0.035, size * 0.10),
        (cx + w * 0.25, top + h * 0.42, size * 0.035, size * 0.10),
        (cx - w * 0.22, top + h * 0.52, size * 0.032, size * 0.09),
        (cx + w * 0.22, top + h * 0.52, size * 0.032, size * 0.09),
        (cx - w * 0.18, top + h * 0.60, size * 0.030, size * 0.08),
        (cx + w * 0.18, top + h * 0.60, size * 0.030, size * 0.08),
    ]

    for gun_x, gun_y, gun_w, gun_h in secondary_configs:
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

        # 高光
        hl_rect = QRectF(gun_x - gun_w * 0.30, gun_y - gun_h + 1,
                         gun_w * 0.6, gun_h * 0.20)
        hl_grad = QLinearGradient(hl_rect.left(), hl_rect.top(),
                                  hl_rect.left(), hl_rect.bottom())
        hl_grad.setColorAt(0.0, QColor(255, 255, 255, int(70 * alpha)))
        hl_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(hl_grad)
        p.setPen(Qt.NoPen)
        p.drawRect(hl_rect)

        # 炮口
        muzzle_x = gun_x
        muzzle_y = gun_y - gun_h
        muzzle_glow = QRadialGradient(muzzle_x, muzzle_y, size * 0.028)
        muzzle_glow.setColorAt(0.0, QColor(255, 150, 30, int(160 * charge * alpha)))
        muzzle_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(muzzle_glow)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(muzzle_x, muzzle_y), size * 0.028, size * 0.028)


def _paint_lighting(p, cx, left, top, w, h, size, alpha):
    """光影 — 顶部高光带 + 底部阴影"""
    # 顶部高光
    hl_top = top + h * 0.07
    hl_h = h * 0.013
    hl_w = w * 0.40
    hl_grad = QLinearGradient(cx, hl_top, cx, hl_top + hl_h)
    hl_grad.setColorAt(0.0, QColor(255, 255, 255, int(45 * alpha)))
    hl_grad.setColorAt(0.5, QColor(255, 255, 255, int(25 * alpha)))
    hl_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(hl_grad)
    p.setPen(Qt.NoPen)
    p.drawRect(QRectF(cx - hl_w / 2, hl_top, hl_w, hl_h))


def _paint_nav_lights(p, center, size, anim_t, alpha):
    """红绿导航灯 + 白色尾灯"""
    cx, cy = center.x(), center.y()
    for sign, base_color in [(-1, QColor(255, 30, 15)), (1, QColor(15, 255, 35))]:
        nx = cx + sign * size * 0.85
        ny = cy - size * 0.20
        flicker = 0.3 + 0.7 * abs(math.sin(anim_t * 5.0 + sign * 1.5))
        nav_g = QRadialGradient(nx, ny, size * 0.08)
        nav_g.setColorAt(0.0, QColor(base_color.red(), base_color.green(),
                                     base_color.blue(), int(200 * flicker * alpha)))
        nav_g.setColorAt(0.4, QColor(base_color.red(), base_color.green(),
                                     base_color.blue(), int(100 * flicker * alpha)))
        nav_g.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(nav_g)
        p.drawEllipse(QPointF(nx, ny), size * 0.08, size * 0.08)
        p.setBrush(QColor(255, 255, 255, int(180 * flicker * alpha)))
        p.drawEllipse(QPointF(nx, ny), size * 0.025, size * 0.025)


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

