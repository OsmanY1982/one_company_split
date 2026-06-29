# `core/shapes/black_hole.py`

> 路径：`core/shapes/black_hole.py` | 行数：176


---


```python
# -*- coding: utf-8 -*-
"""
黑洞 — 暗核事件视界 + 旋转吸积盘 + 引力透镜光晕畸变
"""
import math, random
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QConicalGradient,
    QColor, QPen, QBrush
)


def paint(painter: QPainter, center: QPointF, radius: float,
          anim_t: float, hovered: bool, alpha: float):
    cx, cy = center.x(), center.y()
    p = painter
    p.save()
    if alpha < 1.0:
        p.setOpacity(alpha)


    # ── 多层外辉光（增强质感）──
    for glow_layer in range(4):
        glow_scale = 1.06 + glow_layer * 0.20
        glow_r = radius * glow_scale
        glow = QRadialGradient(cx, cy, glow_r)
        ga = max(1, 35 - glow_layer * 8)
        glow.setColorAt(0.0, QColor(255, 255, 255, 0))
        glow.setColorAt(0.25, QColor(200, 200, 255, ga // 2))
        glow.setColorAt(0.55, QColor(120, 140, 255, ga))
        glow.setColorAt(0.80, QColor(60, 80, 200, ga // 2))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setBrush(glow); p.setPen(Qt.NoPen)
        p.drawEllipse(center, glow_r, glow_r)
    event_horizon_r = radius * 0.32  # 事件视界半径
    disk_inner = radius * 0.42
    disk_outer = radius * 1.45

    # ── 引力透镜光晕（外层畸变光环，多层）──
    for i in range(5):
        lens_r = radius * (1.3 + i * 0.22)
        lens = QRadialGradient(cx, cy, lens_r)
        la = int((50 - i * 10) * (0.7 + 0.3 * abs(math.sin(anim_t * 1.5))))
        lens.setColorAt(0.0, QColor(80, 40, 140, 0))
        lens.setColorAt(0.4, QColor(60, 30, 130, la // 3))
        lens.setColorAt(0.6, QColor(100, 50, 180, la))
        lens.setColorAt(0.75, QColor(140, 80, 220, la // 2))
        lens.setColorAt(0.88, QColor(60, 20, 120, la // 3))
        lens.setColorAt(0.96, QColor(30, 10, 80, la // 4))
        lens.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(lens); p.setPen(Qt.NoPen)
        p.drawEllipse(center, lens_r, lens_r)

    # ── 吸积盘（椭圆椭圆环，旋转发光）──
    rot = anim_t * 1.8
    for i in range(3):
        inner = disk_inner + i * (disk_outer - disk_inner) * 0.12
        outer = disk_inner + (i + 1) * (disk_outer - disk_inner) * 0.12
        # 椭圆吸积盘（倾斜视角）
        p.save()
        p.translate(cx, cy)
        p.rotate(rot * 30 + i * 18)
        p.scale(1.0, 0.25)
        for j in range(60):
            pos = j / 60
            r_current = inner + (outer - inner) * pos
            # 颜色：内圈黄白→外圈橙红→最外暗紫
            if r_current < disk_inner + (disk_outer - disk_inner) * 0.2:
                da = int(80 + 80 * pos * 5)
                dc = QColor(255, 220, 140, da)
            elif r_current < disk_inner + (disk_outer - disk_inner) * 0.5:
                da = int(60 + 60 * (1 - pos))
                dc = QColor(255, 150, 50, da)
            else:
                da = int(30 + 40 * (1 - pos))
                dc = QColor(180, 60, 180, da)
            p.setBrush(dc); p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(0, 0), r_current, r_current * 0.02)
        p.restore()

    # ── 吸积盘颗粒（螺旋轨道粒子）──
    disk_rng = random.Random(int(anim_t * 300) % 100000 + 888)
    p.setPen(Qt.NoPen)
    for _ in range(50):
        da2 = disk_rng.uniform(0, 2 * math.pi)
        dd = disk_rng.uniform(disk_inner, disk_outer)
        spiral_offset = (dd - disk_inner) / (disk_outer - disk_inner) * 4.0
        da2 += rot * spiral_offset
        dx = cx + math.cos(da2) * dd
        dy = cy + math.sin(da2) * dd * 0.25  # 压扁
        ds = disk_rng.uniform(0.3, 1.5)
        da3 = disk_rng.randint(30, 140)
        dg = QRadialGradient(dx, dy, ds * 2.0)
        dg.setColorAt(0.0, QColor(255, 200, 80, da3))
        dg.setColorAt(0.5, QColor(255, 120, 30, da3 // 2))
        dg.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(dg)
        p.drawEllipse(QPointF(dx, dy), ds * 2.0, ds * 2.0)

    # ── 事件视界（纯黑核心 + 光子环）──
    # 纯黑球核
    p.setBrush(QColor(0, 0, 0))
    p.setPen(Qt.NoPen)
    p.drawEllipse(center, event_horizon_r, event_horizon_r)

    # 光子环（事件视界边缘的薄光环）
    photon = QRadialGradient(cx, cy, event_horizon_r * 1.12)
    photon.setColorAt(0.0, QColor(255, 255, 255, 0))
    photon.setColorAt(0.82, QColor(255, 255, 255, 0))
    photon.setColorAt(0.90, QColor(255, 200, 100, 80))
    photon.setColorAt(0.95, QColor(255, 150, 50, 120))
    photon.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(photon)
    p.drawEllipse(center, event_horizon_r * 1.12, event_horizon_r * 1.12)

    # ── 相对论喷流（上下两个锥形喷流）──
    jet_pulse = 0.6 + 0.4 * abs(math.sin(anim_t * 2.5))
    for sign in (-1, 1):
        jet_len = radius * 1.2
        jet_path_top = cx
        jet_path_top_y = cy + sign * event_horizon_r * 1.1
        jet_grad = QRadialGradient(cx, jet_path_top_y, jet_len)
        ja = int(90 * jet_pulse)
        jet_grad.setColorAt(0.0, QColor(200, 180, 255, ja))
        jet_grad.setColorAt(0.3, QColor(150, 120, 240, ja // 2))
        jet_grad.setColorAt(0.6, QColor(100, 70, 200, ja // 3))
        jet_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(jet_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy + sign * event_horizon_r * 1.1),
                      jet_len * 0.12, jet_len * 0.35)

    # ── 边缘逆光（大气散射模拟 + 呼吸微动）──
    rim_breath = 1.0 + 0.03 * math.sin(anim_t * 2.2)
    rim_grad = QRadialGradient(cx + radius * 0.45, cy + radius * 0.50, radius * 0.50)
    rim_grad.setColorAt(0.0, QColor(255, 255, 255, 0))
    rim_grad.setColorAt(0.55, QColor(255, 255, 255, 0))
    rim_grad.setColorAt(0.78, QColor(180, 200, 255, int(15 * rim_breath)))
    rim_grad.setColorAt(0.92, QColor(140, 170, 255, int(30 * rim_breath)))
    rim_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(rim_grad); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

# ── 悬停增强（主题色脉冲光晕 + 呼吸轮廓）──
    if hovered:
        hp = 0.7 + 0.3 * abs(math.sin(anim_t * 3.5))
        # 内层主题光晕
        for i in range(3):
            ir = radius + 2 + i * 5
            ig = QRadialGradient(center, ir)
            ga = int((70 - i * 18) * hp)
            ig.setColorAt(0.60, QColor(255, 255, 255, 0))
            ig.setColorAt(0.78, QColor(100, 50, 180, ga // 2))
            ig.setColorAt(0.90, QColor(100, 50, 180, ga))
            ig.setColorAt(0.97, QColor(100//2, 50//2, 210, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(100, 50, 180, ga // 2))
            og.setColorAt(0.96, QColor(100//2, 50//2, 220, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(100, 50, 180, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)


    p.restore()

```
