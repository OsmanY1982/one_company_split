# `core/shapes/energy_being.py`

> 路径：`core/shapes/energy_being.py` | 行数：203


---


```python
# -*- coding: utf-8 -*-
"""
能量体外星人 — 3D半透明人形能量轮廓 + HSL色彩循环 + 脉动光核 + 粒子带
"""
import math, random
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QLinearGradient,
    QColor, QPen, QBrush, QPainterPath
)


def _color_at(t: float, a: int):
    """HSL 色彩循环，t 在 0~1 之间循环"""
    h = int((t % 360 + 360) % 360)
    return QColor.fromHsv(h, 200, 255, a)


def paint(painter: QPainter, center: QPointF, radius: float,
          anim_t: float, hovered: bool, alpha: float):
    cx, cy = center.x(), center.y()
    p = painter
    p.save()
    if alpha < 1.0:
        p.setOpacity(alpha)

    s = radius / 50.0
    float_y = math.sin(anim_t * 1.9) * radius * 0.10
    float_x = math.cos(anim_t * 1.5) * radius * 0.06
    body_cx = cx + float_x
    body_cy = cy + float_y

    # HSL 基准色调
    hue_base = int((anim_t * 45) % 360)

    # ── 远景：暗色能量场剪影 ──
    silhouette = QRadialGradient(body_cx, body_cy, radius * 1.25)
    silhouette.setColorAt(0.0, QColor.fromHsv(int(hue_base), 180, 40, 35))
    silhouette.setColorAt(0.4, QColor.fromHsv(int(hue_base), 200, 25, 15))
    silhouette.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(silhouette); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, body_cy), radius * 1.25, radius * 1.25)

    # ── 脉冲光晕层（多层叠加）──
    for layer in range(4):
        lr = radius * (0.65 + layer * 0.15)
        la = int((60 - layer * 14) * (0.5 + 0.5 * math.sin(anim_t * 2.2 + layer * 1.3)))
        hue_ly = (hue_base + layer * 30) % 360
        glow = QRadialGradient(body_cx, body_cy, lr)
        glow.setColorAt(0.0, QColor.fromHsv(int(hue_ly), 150, 255, la))
        glow.setColorAt(0.35, QColor.fromHsv(int(hue_ly), 180, 200, int(la * 0.6)))
        glow.setColorAt(0.65, QColor.fromHsv(int(hue_ly), 200, 140, int(la * 0.25)))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(body_cx, body_cy), lr, lr)

    # ── 中景：半透明人形能量轮廓 ──
    body_path = QPainterPath()
    head_r = radius * 0.42
    head_cy = body_cy - radius * 0.20
    body_top = head_cy + head_r * 0.65
    body_bot = body_cy + radius * 0.35
    body_w_top = head_r * 0.48
    body_w_bot = head_r * 0.72

    # 头部椭圆
    body_path.addEllipse(QPointF(body_cx, head_cy), head_r * 0.88, head_r * 0.78)
    # 身体：上窄下宽梯形
    body_path.moveTo(body_cx - body_w_top, body_top)
    body_path.cubicTo(
        body_cx - body_w_top * 1.05, body_top + (body_bot - body_top) * 0.5,
        body_cx - body_w_bot * 0.95, body_bot - head_r * 0.1,
        body_cx - body_w_bot * 0.5, body_bot
    )
    body_path.quadTo(body_cx, body_bot + head_r * 0.06,
                     body_cx + body_w_bot * 0.5, body_bot)
    body_path.cubicTo(
        body_cx + body_w_bot * 0.95, body_bot - head_r * 0.1,
        body_cx + body_w_top * 1.05, body_top + (body_bot - body_top) * 0.5,
        body_cx + body_w_top, body_top
    )
    body_path.closeSubpath()

    body_alpha = int(100 + 50 * math.sin(anim_t * 1.6))
    body_grad = QLinearGradient(body_cx, body_top, body_cx, body_bot)
    hue_body = (hue_base + 30) % 360
    body_grad.setColorAt(0.0, QColor.fromHsv(int(hue_body), 180, 255, body_alpha))
    body_grad.setColorAt(0.4, QColor.fromHsv(int(hue_body), 200, 220, int(body_alpha * 0.7)))
    body_grad.setColorAt(0.7, QColor.fromHsv(int(hue_body), 220, 180, int(body_alpha * 0.4)))
    body_grad.setColorAt(1.0, QColor.fromHsv(int(hue_body), 240, 130, int(body_alpha * 0.15)))
    p.setBrush(body_grad); p.setPen(Qt.NoPen)
    p.drawPath(body_path)

    # 头部渐变
    head_grad = QRadialGradient(body_cx - head_r * 0.15, head_cy - head_r * 0.15, head_r)
    hue_hd = hue_base
    head_grad.setColorAt(0.0, QColor.fromHsv(int(hue_hd), 100, 255, body_alpha))
    head_grad.setColorAt(0.5, QColor.fromHsv(int(hue_hd), 150, 220, int(body_alpha * 0.6)))
    head_grad.setColorAt(1.0, QColor.fromHsv(int(hue_hd), 200, 140, int(body_alpha * 0.2)))
    p.setBrush(head_grad); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(body_cx, head_cy), head_r * 0.88, head_r * 0.78)

    # ── 眼睛：空洞光点（能量体无瞳孔）──
    for sign in (-1, 1):
        ex = body_cx + sign * head_r * 0.22
        ey = head_cy - head_r * 0.05
        eye_pulse = 0.6 + 0.4 * math.sin(anim_t * 3.0 + sign * 1.5)
        hue_eye = (hue_base + 60) % 360
        eye_glow = QRadialGradient(ex, ey, head_r * 0.14)
        eye_glow.setColorAt(0.0, QColor.fromHsv(int(hue_eye), 50, 255, int(200 * eye_pulse)))
        eye_glow.setColorAt(0.3, QColor.fromHsv(int(hue_eye), 80, 240, int(140 * eye_pulse)))
        eye_glow.setColorAt(0.6, QColor.fromHsv(int(hue_eye), 120, 200, int(60 * eye_pulse)))
        eye_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(eye_glow); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(ex, ey), head_r * 0.14, head_r * 0.16)
        # 核心白点
        p.setBrush(QColor(255, 255, 255, int(220 * eye_pulse)))
        p.drawEllipse(QPointF(ex, ey), head_r * 0.04, head_r * 0.04)

    # ── 核心光点（胸部脉动能量核）──
    core_y = body_cy + radius * 0.05
    core_pulse = 0.5 + 0.5 * math.sin(anim_t * 4.5)
    for layer in range(3):
        lr = radius * (0.08 + layer * 0.09)
        la = int((60 - layer * 18) * core_pulse)
        hue_core = (hue_base + 90) % 360
        core_glow = QRadialGradient(body_cx, core_y, lr)
        core_glow.setColorAt(0.0, QColor.fromHsv(int(hue_core), 50, 255, la))
        core_glow.setColorAt(0.35, QColor.fromHsv(int(hue_core), 80, 230, int(la * 0.5)))
        core_glow.setColorAt(0.7, QColor.fromHsv(int(hue_core), 120, 180, int(la * 0.2)))
        core_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(core_glow); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(body_cx, core_y), lr, lr)
    # 核心白点
    p.setBrush(QColor(255, 255, 255, int(230 * core_pulse)))
    p.drawEllipse(QPointF(body_cx, core_y), radius * 0.04, radius * 0.04)

    # ── 粒子带（环绕能量体）──
    part_rng = random.Random(555)
    p.setPen(Qt.NoPen)
    for _ in range(35):
        pa = part_rng.uniform(0, 2 * math.pi)
        pd = radius * (0.55 + 0.50 * part_rng.random())
        poff = anim_t * (1.0 + 0.8 * part_rng.random())
        px = body_cx + math.cos(pa + poff) * pd
        py = body_cy + math.sin(pa + poff * 0.7) * pd * 0.75
        ps = part_rng.uniform(0.3, 2.0)
        ph = (hue_base + part_rng.randint(0, 60)) % 360
        pa_ = part_rng.randint(40, 100)
        part_grad = QRadialGradient(px, py, ps * 3)
        part_grad.setColorAt(0.0, QColor.fromHsv(ph, 160, 255, pa_))
        part_grad.setColorAt(0.5, QColor.fromHsv(ph, 200, 180, pa_ // 2))
        part_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(part_grad)
        p.drawEllipse(QPointF(px, py), ps * 3, ps * 3)

    # ── 粒子光环 ──
    aura_rng = random.Random(int(anim_t * 280) % 100000 + 5555)
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
        hue_aura = (hue_base + aura_rng.randint(0, 40)) % 360
        ag.setColorAt(0.0, QColor.fromHsv(hue_aura, 180, 255, a_alpha))
        ag.setColorAt(0.5, QColor.fromHsv(hue_aura, 200, 200, a_alpha // 2))
        ag.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(ag)
        p.drawEllipse(QPointF(ax, ay), a_size * 2.5, a_size * 2.5)

    # ── hover 光晕（彩虹主题）──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        for i in range(3):
            ir = radius + 2 + i * 5
            ig = QRadialGradient(center, ir)
            ga = int((70 - i * 18) * hp)
            hue_hv = (hue_base + i * 60) % 360
            ig.setColorAt(0.60, QColor(255, 255, 255, 0))
            ig.setColorAt(0.78, QColor.fromHsv(hue_hv, 160, 255, ga // 2))
            ig.setColorAt(0.90, QColor.fromHsv(hue_hv, 180, 255, ga))
            ig.setColorAt(0.97, QColor.fromHsv(hue_hv, 200, 200, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            hue_hv2 = (hue_base + i * 90) % 360
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor.fromHsv(hue_hv2, 160, 255, ga // 2))
            og.setColorAt(0.96, QColor.fromHsv(hue_hv2, 180, 220, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)

    p.restore()

```
