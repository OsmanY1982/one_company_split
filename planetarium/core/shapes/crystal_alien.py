# -*- coding: utf-8 -*-
"""
水晶外星人 — 3D棱面折射晶体 + 多边形面片 + 独立渐变 + 棱线勾勒 + 晶格生长
"""
import math, random
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QLinearGradient,
    QColor, QPen, QBrush, QPainterPath
)


def _cubic_bezier(t, p0, p1, p2, p3):
    """贝塞尔插值辅助"""
    t1 = 1 - t
    return (t1**3 * p0 + 3 * t1**2 * t * p1 + 3 * t1 * t**2 * p2 + t**3 * p3)


def _draw_facet(p, vertices, fill_grad, outline_color=None, outline_width=1.0):
    """绘制一个多边形晶面"""
    if len(vertices) < 3:
        return
    path = QPainterPath()
    path.moveTo(vertices[0][0], vertices[0][1])
    for v in vertices[1:]:
        path.lineTo(v[0], v[1])
    path.closeSubpath()
    p.setBrush(fill_grad)
    if outline_color:
        p.setPen(QPen(outline_color, outline_width))
    else:
        p.setPen(Qt.NoPen)
    p.drawPath(path)


def paint(painter: QPainter, center: QPointF, radius: float,
          anim_t: float, hovered: bool, alpha: float):
    cx, cy = center.x(), center.y()
    p = painter
    p.save()
    if alpha < 1.0:
        p.setOpacity(alpha)

    s = radius / 50.0
    float_y = math.sin(anim_t * 1.3) * radius * 0.05
    float_x = math.cos(anim_t * 1.0) * radius * 0.03
    body_cx = cx + float_x
    body_cy = cy + float_y
    cr = radius * 0.60  # 晶体半径

    # ── 远景：紫晶能量场 ──
    silhouette = QRadialGradient(body_cx, body_cy, radius * 1.1)
    silhouette.setColorAt(0.0, QColor(80, 40, 160, 25))
    silhouette.setColorAt(0.5, QColor(50, 20, 120, 12))
    silhouette.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(silhouette); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), radius * 1.1, radius * 1.1)

    # ── 晶格生长脉动 ──
    growth_pulse = 0.95 + 0.05 * math.sin(anim_t * 2.0 + 1.5)

    # ── 主晶体面片定义（7个顶点，构成复杂多面体）──
    # 顶点坐标
    apex = (body_cx, body_cy - cr * 0.95 * growth_pulse)           # 顶部尖端
    left_top = (body_cx - cr * 0.85, body_cy - cr * 0.25)          # 左上
    left_mid = (body_cx - cr * 0.72, body_cy + cr * 0.10)          # 左中
    left_bot = (body_cx - cr * 0.55, body_cy + cr * 0.55)         # 左下
    right_top = (body_cx + cr * 0.85, body_cy - cr * 0.25)         # 右上
    right_mid = (body_cx + cr * 0.72, body_cy + cr * 0.10)         # 右中
    right_bot = (body_cx + cr * 0.55, body_cy + cr * 0.55)        # 右下
    bottom = (body_cx, body_cy + cr * 0.70 * growth_pulse)         # 底部尖端
    left_outer = (body_cx - cr * 1.05, body_cy - cr * 0.05)        # 左外
    right_outer = (body_cx + cr * 1.05, body_cy - cr * 0.05)       # 右外

    # 中心晶核
    core_center = (body_cx, body_cy - cr * 0.08)
    core_wing_l = (body_cx - cr * 0.32, body_cy + cr * 0.15)
    core_wing_r = (body_cx + cr * 0.32, body_cy + cr * 0.15)

    # ── 面片1：中心上三角（晶核）──
    grad1 = QLinearGradient(core_center[0], core_center[1],
                            (core_wing_l[0] + core_wing_r[0]) / 2,
                            (core_wing_l[1] + core_wing_r[1]) / 2)
    grad1.setColorAt(0.0, QColor(220, 140, 255, 230))
    grad1.setColorAt(0.5, QColor(140, 70, 240, 200))
    grad1.setColorAt(1.0, QColor(90, 30, 200, 180))
    _draw_facet(p, [core_center, core_wing_l, core_wing_r], grad1, QColor(200, 160, 255, 180), 0.8 * s)

    # ── 面片2：左上棱面 ──
    grad2 = QLinearGradient(apex[0], apex[1], left_mid[0], left_mid[1])
    grad2.setColorAt(0.0, QColor(190, 100, 255, 200))
    grad2.setColorAt(0.5, QColor(130, 60, 230, 170))
    grad2.setColorAt(1.0, QColor(80, 20, 190, 150))
    _draw_facet(p, [apex, left_top, left_mid], grad2, QColor(210, 170, 255, 160), 0.7 * s)

    # ── 面片3：右上棱面 ──
    grad3 = QLinearGradient(apex[0], apex[1], right_mid[0], right_mid[1])
    grad3.setColorAt(0.0, QColor(200, 110, 255, 200))
    grad3.setColorAt(0.5, QColor(140, 70, 240, 170))
    grad3.setColorAt(1.0, QColor(85, 25, 195, 150))
    _draw_facet(p, [apex, right_mid, right_top], grad3, QColor(210, 170, 255, 160), 0.7 * s)

    # ── 面片4：左侧面 ──
    grad4 = QLinearGradient(left_top[0], left_top[1], left_bot[0], left_bot[1])
    grad4.setColorAt(0.0, QColor(160, 80, 240, 180))
    grad4.setColorAt(0.5, QColor(110, 45, 210, 160))
    grad4.setColorAt(1.0, QColor(60, 15, 170, 140))
    _draw_facet(p, [left_top, left_mid, left_bot, left_outer], grad4, QColor(180, 130, 255, 140), 0.6 * s)

    # ── 面片5：右侧面 ──
    grad5 = QLinearGradient(right_top[0], right_top[1], right_bot[0], right_bot[1])
    grad5.setColorAt(0.0, QColor(170, 90, 250, 180))
    grad5.setColorAt(0.5, QColor(120, 50, 220, 160))
    grad5.setColorAt(1.0, QColor(65, 18, 175, 140))
    _draw_facet(p, [right_top, right_outer, right_bot, right_mid], grad5, QColor(180, 130, 255, 140), 0.6 * s)

    # ── 面片6：左下底面 ──
    grad6 = QLinearGradient(left_mid[0], left_mid[1], bottom[0], bottom[1])
    grad6.setColorAt(0.0, QColor(120, 55, 220, 170))
    grad6.setColorAt(0.5, QColor(70, 25, 180, 150))
    grad6.setColorAt(1.0, QColor(40, 10, 140, 130))
    _draw_facet(p, [left_mid, left_bot, bottom, core_wing_l], grad6, QColor(170, 120, 250, 120), 0.6 * s)

    # ── 面片7：右下底面 ──
    grad7 = QLinearGradient(right_mid[0], right_mid[1], bottom[0], bottom[1])
    grad7.setColorAt(0.0, QColor(130, 60, 230, 170))
    grad7.setColorAt(0.5, QColor(75, 28, 185, 150))
    grad7.setColorAt(1.0, QColor(42, 12, 145, 130))
    _draw_facet(p, [right_mid, core_wing_r, bottom, right_bot], grad7, QColor(170, 120, 250, 120), 0.6 * s)

    # ── 面片8：左外延棱 ──
    grad8 = QLinearGradient(left_outer[0], left_outer[1], left_top[0], left_top[1])
    grad8.setColorAt(0.0, QColor(100, 40, 220, 150))
    grad8.setColorAt(1.0, QColor(150, 80, 245, 170))
    _draw_facet(p, [left_outer, left_top, left_bot], grad8, QColor(140, 90, 230, 100), 0.5 * s)

    # ── 面片9：右外延棱 ──
    grad9 = QLinearGradient(right_outer[0], right_outer[1], right_top[0], right_top[1])
    grad9.setColorAt(0.0, QColor(105, 42, 225, 150))
    grad9.setColorAt(1.0, QColor(155, 85, 250, 170))
    _draw_facet(p, [right_outer, right_bot, right_top], grad9, QColor(140, 90, 230, 100), 0.5 * s)

    # ── 棱线勾勒（强化折射感）──
    p.setPen(QPen(QColor(220, 190, 255, 80), 0.5 * s))
    p.setBrush(Qt.NoBrush)
    for (x1, y1), (x2, y2) in [
        (apex, left_top), (apex, right_top),
        (left_top, left_mid), (right_top, right_mid),
        (left_mid, left_bot), (right_mid, right_bot),
        (core_center, core_wing_l), (core_center, core_wing_r),
        (left_outer, left_top), (left_outer, left_bot),
        (right_outer, right_top), (right_outer, right_bot),
    ]:
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    # ── 微棱分裂线 ──
    p.setPen(QPen(QColor(190, 150, 255, 60), 0.3 * s))
    for frac in [0.35, 0.65]:
        # 左中→底 分裂
        lx = _cubic_bezier(frac, left_mid[0], left_mid[0], bottom[0], bottom[0])
        ly = left_mid[1] + frac * (bottom[1] - left_mid[1])
        rx = _cubic_bezier(frac, right_mid[0], right_mid[0], bottom[0], bottom[0])
        ry = right_mid[1] + frac * (bottom[1] - right_mid[1])
        p.drawLine(QPointF(lx, ly), QPointF(rx, ry))

    # ── 副晶散落 ──
    sub_rng = random.Random(999)
    for _ in range(5):
        sa = sub_rng.uniform(0, 2 * math.pi)
        sd = cr * (0.70 + 0.35 * sub_rng.random())
        sx = body_cx + math.cos(sa) * sd
        sy = body_cy + math.sin(sa) * sd * 0.7
        ss = cr * 0.08 * sub_rng.uniform(0.5, 1.2)
        sh = sub_rng.randint(240, 300)
        sub_grad = QRadialGradient(sx, sy, ss * 1.5)
        sub_grad.setColorAt(0.0, QColor.fromHsv(sh, 150, 255, 180))
        sub_grad.setColorAt(0.5, QColor.fromHsv(sh, 180, 200, 80))
        sub_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(sub_grad); p.setPen(QPen(QColor(200, 160, 255, 100), 0.3 * s))
        p.drawEllipse(QPointF(sx, sy), ss, ss * 0.8)

    # ── 彩虹闪光射线（周期性出现）──
    flash_alpha = int(40 * (0.5 + 0.5 * math.sin(anim_t * 5.5 + 2.0)))
    if flash_alpha > 10:
        p.setPen(QPen(QColor(180, 130, 255, flash_alpha), 0.8 * s))
        for angle in [0, math.pi * 2 / 5, math.pi * 4 / 5, math.pi * 6 / 5, math.pi * 8 / 5]:
            rx = body_cx + math.cos(angle + anim_t * 0.3) * cr * 0.8
            ry = body_cy + math.sin(angle + anim_t * 0.3) * cr * 0.8
            p.drawLine(QPointF(body_cx, body_cy), QPointF(rx, ry))

    # ── 粒子光环 ──
    aura_rng = random.Random(int(anim_t * 280) % 100000 + 83921)
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
        ag.setColorAt(0.0, QColor(160, 100, 255, a_alpha))
        ag.setColorAt(0.5, QColor(80, 50, 200, a_alpha // 2))
        ag.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(ag)
        p.drawEllipse(QPointF(ax, ay), a_size * 2.5, a_size * 2.5)

    # ── hover 光晕（紫晶色主题）──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        for i in range(3):
            ir = radius + 2 + i * 5
            ig = QRadialGradient(center, ir)
            ga = int((70 - i * 18) * hp)
            ig.setColorAt(0.60, QColor(255, 255, 255, 0))
            ig.setColorAt(0.78, QColor(160, 100, 240, ga // 2))
            ig.setColorAt(0.90, QColor(160, 100, 240, ga))
            ig.setColorAt(0.97, QColor(80, 50, 180, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(160, 100, 240, ga // 2))
            og.setColorAt(0.96, QColor(80, 50, 180, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)

    p.restore()
