# `core/shapes/scout.py`

> 路径：`core/shapes/scout.py` | 行数：457


---


```python
# -*- coding: utf-8 -*-
"""
侦察舰形态 — 悬浮球变形
真实感设计：多层金属碟形船体 + 装甲板线 + 散热格栅 + 传感器阵列 + 三层引擎尾焰 + 轻炮
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
    """绘制侦察舰形态"""
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.HighQualityAntialiasing)

    size = radius * 0.95
    w, h = size * 2.2, size * 1.2
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
    """主船体 — 碟形多层金属渐变"""
    nose_y = top + h * 0.12
    body_bot_y = top + h * 0.78
    nose_hw = w * 0.06
    mid_hw = w * 0.36
    tail_hw = w * 0.20

    # 底层暗面 — 宽大的碟形剪影
    shadow_path = QPainterPath()
    shadow_path.moveTo(cx, nose_y - h * 0.02)
    shadow_path.cubicTo(cx + nose_hw * 1.5, nose_y + h * 0.03,
                        cx + mid_hw * 0.9, top + h * 0.35,
                        cx + mid_hw * 0.75, top + h * 0.55)
    shadow_path.lineTo(cx + tail_hw * 0.9, body_bot_y + h * 0.02)
    shadow_path.lineTo(cx - tail_hw * 0.9, body_bot_y + h * 0.02)
    shadow_path.cubicTo(cx - mid_hw * 0.75, top + h * 0.55,
                        cx - mid_hw * 0.9, top + h * 0.35,
                        cx - nose_hw * 1.5, nose_y + h * 0.03)
    shadow_path.closeSubpath()
    p.setBrush(QColor(0x18, 0x1a, 0x20, int(200 * alpha)))
    p.setPen(Qt.NoPen)
    p.drawPath(shadow_path)

    # 中层主体 — 碟形船体
    hull_path = QPainterPath()
    hull_path.moveTo(cx, nose_y)
    hull_path.cubicTo(cx + nose_hw * 1.8, nose_y + h * 0.05,
                      cx + mid_hw, top + h * 0.32,
                      cx + mid_hw * 0.85, top + h * 0.52)
    hull_path.lineTo(cx + tail_hw, body_bot_y)
    hull_path.lineTo(cx - tail_hw, body_bot_y)
    hull_path.cubicTo(cx - mid_hw * 0.85, top + h * 0.52,
                      cx - mid_hw, top + h * 0.32,
                      cx - nose_hw * 1.8, nose_y + h * 0.05)
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

    # 底部阴影带
    shadow_grad = QLinearGradient(cx, body_bot_y, cx, body_bot_y + h * 0.04)
    shadow_grad.setColorAt(0.0, QColor(0x10, 0x12, 0x18, int(160 * alpha)))
    shadow_grad.setColorAt(1.0, QColor(0x10, 0x12, 0x18, 0))
    p.setBrush(shadow_grad)
    p.setPen(Qt.NoPen)
    p.drawRect(QRectF(cx - tail_hw * 0.8, body_bot_y, tail_hw * 1.6, h * 0.04))


def _paint_superstructure(p, cx, left, top, w, h, size, alpha):
    """上层建筑 — 中脊+小型舰桥"""
    # 中脊
    spine_top = top + h * 0.08
    spine_bot = top + h * 0.18
    spine_hw_top = w * 0.02
    spine_hw_bot = w * 0.035

    path = QPainterPath()
    path.moveTo(cx, spine_top)
    path.lineTo(cx + spine_hw_top, spine_top + h * 0.02)
    path.lineTo(cx + spine_hw_bot, spine_bot)
    path.lineTo(cx - spine_hw_bot, spine_bot)
    path.lineTo(cx - spine_hw_top, spine_top + h * 0.02)
    path.closeSubpath()

    spine_grad = QLinearGradient(cx, spine_top, cx, spine_bot)
    spine_grad.setColorAt(0.0, QColor(0x5a, 0x5e, 0x65, int(240 * alpha)))
    spine_grad.setColorAt(0.5, QColor(0x90, 0x94, 0x9c, int(235 * alpha)))
    spine_grad.setColorAt(1.0, QColor(0x48, 0x4c, 0x53, int(230 * alpha)))
    p.setBrush(spine_grad)
    p.setPen(Qt.NoPen)  # was dark outline, removed
    p.drawPath(path)

    # 舰桥（碟形中部凸起）
    bridge_w = w * 0.10
    bridge_h = h * 0.06
    bridge_x = cx - bridge_w / 2
    bridge_y = top + h * 0.20
    bridge_path = QPainterPath()
    bridge_path.addRoundedRect(QRectF(bridge_x, bridge_y, bridge_w, bridge_h), 3, 3)
    bridge_grad = QLinearGradient(cx, bridge_y, cx, bridge_y + bridge_h)
    bridge_grad.setColorAt(0.0, QColor(0x6a, 0x6e, 0x75, int(240 * alpha)))
    bridge_grad.setColorAt(0.5, QColor(0x98, 0x9c, 0xa4, int(235 * alpha)))
    bridge_grad.setColorAt(1.0, QColor(0x4a, 0x4e, 0x55, int(230 * alpha)))
    p.setBrush(bridge_grad)
    p.setPen(Qt.NoPen)  # was dark outline, removed
    p.drawPath(bridge_path)

    # 舰桥顶部高光
    hl = QRectF(bridge_x + 2, bridge_y + 1, bridge_w - 4, bridge_h * 0.35)
    hl_grad = QLinearGradient(hl.left(), hl.top(), hl.left(), hl.bottom())
    hl_grad.setColorAt(0.0, QColor(255, 255, 255, int(55 * alpha)))
    hl_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(hl_grad)
    p.setPen(Qt.NoPen)
    p.drawRect(hl)


def _paint_armor_panels(p, cx, left, top, w, h, size, alpha):
    """装甲板线 — 8 条疏密变化的面板分割线"""
    pen = QPen(QColor(0x1a, 0x1d, 0x22, int(70 * alpha)), 0.5)
    p.setPen(pen)

    # 船体中段横向装甲线（4条）
    base_y = top + h * 0.30
    for i in range(4):
        ly = base_y + i * h * 0.07 * (1 + i * 0.2)
        frac = (ly - top) / h
        hw = w * (0.30 - frac * 0.22)
        p.drawLine(QPointF(cx - hw, ly), QPointF(cx + hw, ly))

    # 船体下段 V 形线（2条）
    v_center_y = top + h * 0.58
    for sign in [-1, 1]:
        vx1 = cx + sign * w * 0.20
        vx2 = cx + sign * w * 0.06
        vy1 = v_center_y
        vy2 = v_center_y + h * 0.09
        p.drawLine(QPointF(vx1, vy1), QPointF(vx2, vy2))

    # 纵向中线（1条）
    p.drawLine(QPointF(cx, top + h * 0.14), QPointF(cx, top + h * 0.26))

    # 尾段横线（1条）
    p.drawLine(QPointF(cx - w * 0.10, top + h * 0.65),
               QPointF(cx + w * 0.10, top + h * 0.65))


def _paint_heat_sinks(p, cx, left, top, w, h, size, alpha):
    """散热格栅 — 船体两侧各 10 条密集平行短横线"""
    pen = QPen(QColor(0x2a, 0x2d, 0x33, int(100 * alpha)), 0.4)
    p.setPen(pen)

    for sign in [-1, 1]:
        sx_base = cx + sign * w * 0.28
        sy_start = top + h * 0.38
        for i in range(10):
            sy = sy_start + i * h * 0.022
            p.drawLine(QPointF(sx_base - sign * size * 0.03, sy),
                       QPointF(sx_base + sign * size * 0.07, sy))


def _paint_rivets(p, cx, left, top, w, h, size, alpha):
    """铆钉点 — 沿装甲板线分布的深色小圆"""
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0x1a, 0x1d, 0x22, int(120 * alpha)))

    # 沿中段装甲线（4层横向）
    rivet_y_offsets = [0.30, 0.37, 0.44, 0.51]
    for ryf in rivet_y_offsets:
        ry = top + h * ryf
        frac = (ry - top) / h
        hw = w * (0.30 - frac * 0.22)
        for sign in [-1, 1]:
            for ri in range(3):
                r_frac = 0.25 + ri * 0.25
                rx = cx + sign * hw * r_frac
                p.drawEllipse(QPointF(rx, ry), size * 0.012, size * 0.012)


def _paint_sensors(p, cx, left, top, w, h, size, anim_t, alpha):
    """传感器阵列 — 船首 5 个小圆点"""
    sx = cx
    sy = top + h * 0.14
    for i in range(5):
        ox = (i - 2) * size * 0.032
        glow = 0.5 + 0.5 * abs(math.sin(anim_t * 3.5 + i * 0.8))
        sg = QRadialGradient(sx + ox, sy, size * 0.016)
        sg.setColorAt(0.0, QColor(60, 180, 255, int(180 * glow * alpha)))
        sg.setColorAt(1.0, QColor(60, 180, 255, 0))
        p.setBrush(sg)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(sx + ox, sy), size * 0.016, size * 0.016)


def _paint_antennas(p, cx, left, top, w, h, size, alpha):
    """通信天线 — 2 根，细竖线+顶端小圆点"""
    for sign in [-1, 1]:
        ant_x = cx + sign * w * 0.04
        ant_base = top + h * 0.08
        ant_tip = top - h * 0.02

        p.setPen(QPen(QColor(0xc0, 0xc4, 0xcc, int(160 * alpha)), 0.5))
        p.drawLine(QPointF(ant_x, ant_base), QPointF(ant_x, ant_tip))

        p.setBrush(QColor(0xc0, 0xc4, 0xcc, int(180 * alpha)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ant_x, ant_tip), size * 0.014, size * 0.014)

    # 主天线（中央）
    main_ant_x = cx
    main_ant_base = top + h * 0.08
    main_ant_tip = top - h * 0.05
    p.setPen(QPen(QColor(0xc0, 0xc4, 0xcc, int(170 * alpha)), 0.7))
    p.drawLine(QPointF(main_ant_x, main_ant_base), QPointF(main_ant_x, main_ant_tip))
    p.setBrush(QColor(0xc0, 0xc4, 0xcc, int(190 * alpha)))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(main_ant_x, main_ant_tip), size * 0.016, size * 0.016)


def _paint_portholes(p, cx, left, top, w, h, size, anim_t, alpha):
    """发光舷窗 — 舰桥区域 3 个淡蓝微光小矩形"""
    py = top + h * 0.21
    glow = 0.5 + 0.5 * abs(math.sin(anim_t * 2.5))

    for i in range(3):
        px = cx + (i - 1) * w * 0.025
        p.setBrush(QColor(0xaa, 0xdd, 0xff, int(120 * glow * alpha)))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(px - size * 0.012, py, size * 0.024, size * 0.016), 1.0, 1.0)


def _paint_engine_nacelles(p, cx, left, top, w, h, size, anim_t, alpha):
    """引擎舱结构环 — 2 个引擎"""
    engine_y = top + h * 0.80
    pulse = 0.7 + 0.3 * abs(math.sin(anim_t * 4.0))

    for offset in [-w * 0.06, w * 0.06]:
        ex = cx + offset

        # 引擎舱外壳
        nacelle_grad = QRadialGradient(ex, engine_y, size * 0.08)
        nacelle_grad.setColorAt(0.0, QColor(0x3a, 0x3d, 0x42, int(220 * alpha)))
        nacelle_grad.setColorAt(0.6, QColor(0x2a, 0x2d, 0x33, int(200 * alpha)))
        nacelle_grad.setColorAt(1.0, QColor(0x1a, 0x1d, 0x22, int(100 * alpha)))
        p.setBrush(nacelle_grad)
        p.setPen(Qt.NoPen)  # was dark outline, removed
        p.drawEllipse(QPointF(ex, engine_y), size * 0.08, size * 0.055)

        # 结构环
        for ring_i, ring_scale in enumerate([0.7, 0.40]):
            rr_x = size * 0.08 * ring_scale
            rr_y = size * 0.055 * ring_scale
            p.setPen(QPen(QColor(0x7a, 0x7e, 0x85, int((80 - ring_i * 20) * pulse * alpha)), 0.4))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(ex, engine_y), rr_x, rr_y)

        # 发光核心
        core_glow = QRadialGradient(ex, engine_y, size * 0.025)
        core_glow.setColorAt(0.0, QColor(200, 220, 255, int(120 * pulse * alpha)))
        core_glow.setColorAt(1.0, QColor(60, 140, 240, 0))
        p.setBrush(core_glow)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, engine_y), size * 0.025, size * 0.018)


def _paint_engine_flames(p, cx, left, top, w, h, size, anim_t, alpha):
    """引擎尾焰 — 三层叠加，2 个引擎，长度 ±20% 微变"""
    engine_y = top + h * 0.80
    pulse = 0.55 + 0.45 * abs(math.sin(anim_t * 8.0))

    random.seed(42)
    for idx, offset in enumerate([-w * 0.06, w * 0.06]):
        ex = cx + offset
        length_factor = 1.0 + random.uniform(-0.20, 0.20)

        flame_base_h = size * 0.35 * pulse * length_factor

        # 外层 — 淡蓝大椭圆
        outer_a = int(80 * alpha)
        outer_grad = QRadialGradient(ex, engine_y + flame_base_h * 0.3, flame_base_h * 0.85)
        outer_grad.setColorAt(0.0, QColor(0x88, 0xcc, 0xff, outer_a))
        outer_grad.setColorAt(0.5, QColor(0x44, 0x88, 0xcc, outer_a // 2))
        outer_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(outer_grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, engine_y + flame_base_h * 0.15),
                      size * 0.05, flame_base_h * 0.60)

        # 中层 — 蓝色椭圆
        mid_a = int(180 * alpha)
        mid_grad = QRadialGradient(ex, engine_y + flame_base_h * 0.20, flame_base_h * 0.50)
        mid_grad.setColorAt(0.0, QColor(0x4a, 0xa8, 0xff, mid_a))
        mid_grad.setColorAt(0.6, QColor(0x22, 0x66, 0xcc, mid_a // 2))
        mid_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(mid_grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, engine_y + flame_base_h * 0.08),
                      size * 0.03, flame_base_h * 0.35)

        # 内核 — 白色椭圆
        core_grad = QLinearGradient(ex, engine_y, ex, engine_y + flame_base_h * 0.30)
        core_grad.setColorAt(0.0, QColor(255, 255, 255, int(240 * alpha)))
        core_grad.setColorAt(0.3, QColor(255, 255, 240, int(200 * alpha)))
        core_grad.setColorAt(0.7, QColor(200, 230, 255, int(100 * alpha)))
        core_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(core_grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, engine_y + flame_base_h * 0.03),
                      size * 0.016, flame_base_h * 0.18)


def _paint_weapons(p, cx, left, top, w, h, size, anim_t, alpha):
    """武器系统 — 2 门轻炮，翼下挂载"""
    charge = 0.4 + 0.6 * abs(math.sin(anim_t * 4.5))

    for sign in [-1, 1]:
        gun_x = cx + sign * w * 0.30
        gun_y = top + h * 0.52
        gun_w = size * 0.04
        gun_h = size * 0.12

        # 炮管主体
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
        hl_rect = QRectF(gun_x - gun_w * 0.35, gun_y - gun_h + 1,
                         gun_w * 0.7, gun_h * 0.22)
        hl_grad = QLinearGradient(hl_rect.left(), hl_rect.top(),
                                  hl_rect.left(), hl_rect.bottom())
        hl_grad.setColorAt(0.0, QColor(255, 255, 255, int(75 * alpha)))
        hl_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(hl_grad)
        p.setPen(Qt.NoPen)
        p.drawRect(hl_rect)

        # 炮口能量光晕
        muzzle_x = gun_x
        muzzle_y = gun_y - gun_h
        muzzle_glow = QRadialGradient(muzzle_x, muzzle_y, size * 0.035)
        muzzle_glow.setColorAt(0.0, QColor(255, 150, 30, int(180 * charge * alpha)))
        muzzle_glow.setColorAt(0.6, QColor(255, 80, 15, int(80 * charge * alpha)))
        muzzle_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(muzzle_glow)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(muzzle_x, muzzle_y), size * 0.035, size * 0.035)


def _paint_lighting(p, cx, left, top, w, h, size, alpha):
    """光影 — 顶部高光带 + 底部阴影"""
    # 顶部高光带
    hl_top = top + h * 0.09
    hl_h = h * 0.014
    hl_w = w * 0.38
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
        nx = cx + sign * size * 0.65
        ny = cy - size * 0.10
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
    """Hover 光晕 — 淡蓝色径向渐变"""
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
