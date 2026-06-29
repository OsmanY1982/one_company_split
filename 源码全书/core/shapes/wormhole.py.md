# `core/shapes/wormhole.py`

> 路径：`core/shapes/wormhole.py` | 行数：187


---


```python
# -*- coding: utf-8 -*-
"""
虫洞 — 暗黑中心 + 旋转扭曲吸积盘 + 爱因斯坦环 + 时空弯曲光线
"""
import math, random
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QConicalGradient,
    QColor, QPen, QBrush, QPainterPath
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
    throat_r = radius * 0.20      # 虫洞喉部（暗中心）
    ring_inner = radius * 0.28    # 爱因斯坦环内缘
    ring_outer = radius * 0.52    # 爱因斯坦环外缘
    disk_inner = radius * 0.60    # 吸积盘内缘
    disk_outer = radius * 1.52    # 吸积盘外缘
    rot = anim_t * 2.4

    # ── 时空弯曲光晕（多层变色畸变环，模拟引力透镜弯曲光线）──
    for i in range(6):
        lens_r = radius * (1.2 + i * 0.28)
        lens = QRadialGradient(cx, cy, lens_r)
        la = int((55 - i * 8) * (0.6 + 0.4 * abs(math.sin(anim_t * 1.3 + i * 0.7))))
        t = i / 5
        r_val = int(80 + t * 140)
        g_val = int(60 - t * 20 + abs(math.sin(i)) * 60)
        b_val = int(180 - t * 100 + abs(math.cos(i)) * 40)
        lens.setColorAt(0.0, QColor(r_val, g_val, b_val, 0))
        lens.setColorAt(0.25, QColor(r_val, g_val, b_val, la // 4))
        lens.setColorAt(0.45, QColor(r_val + 20, g_val + 10, b_val - 20, la))
        lens.setColorAt(0.60, QColor(r_val, g_val, b_val, la // 2))
        lens.setColorAt(0.75, QColor(r_val - 20, g_val, b_val + 20, la // 3))
        lens.setColorAt(0.88, QColor(r_val // 2, g_val // 2, b_val, la // 5))
        lens.setColorAt(0.97, QColor(r_val // 4, 0, b_val // 2, la // 8))
        lens.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(lens); p.setPen(Qt.NoPen)
        p.drawEllipse(center, lens_r, lens_r)

    # ── 爱因斯坦环（亮环，模拟强引力透镜聚焦光）──
    einstein = QRadialGradient(cx, cy, ring_outer)
    flare = 0.7 + 0.3 * abs(math.sin(anim_t * 2.0))
    einstein.setColorAt(0.0, QColor(255, 255, 255, 0))
    einstein.setColorAt(ring_inner / ring_outer - 0.02, QColor(255, 255, 255, 0))
    einstein.setColorAt(ring_inner / ring_outer, QColor(140, 200, 255, int(180 * flare)))
    einstein.setColorAt((ring_inner + ring_outer) / (2 * ring_outer), QColor(220, 240, 255, int(220 * flare)))
    einstein.setColorAt(ring_outer / ring_outer - 0.03, QColor(100, 170, 255, int(160 * flare)))
    einstein.setColorAt(ring_outer / ring_outer, QColor(255, 255, 255, 0))
    einstein.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(einstein); p.setPen(Qt.NoPen)
    p.drawEllipse(center, ring_outer, ring_outer)

    # ── 旋转扭曲吸积盘（椭圆环，圆锥渐变旋转）──
    p.save()
    p.translate(cx, cy)
    p.rotate(rot * 25)
    p.scale(1.0, 0.22)  # 扁平化 = 倾斜视角
    disk_cx, disk_cy = 0, 0

    # 吸积盘主体：圆锥渐变模拟温度梯度
    for i_disk in range(5):
        inner = disk_inner + i_disk * (disk_outer - disk_inner) / 5
        outer = disk_inner + (i_disk + 1) * (disk_outer - disk_inner) / 5
        ring_grad = QConicalGradient(disk_cx, disk_cy, -rot * 40 + i_disk * 20)
        for j in range(36):
            pos = j / 36
            hue = int(200 + 30 * math.sin(j * 0.5 + i_disk))
            brightness = int(100 + 130 * abs(math.sin(j * 0.3 + i_disk * 0.7)))
            ring_grad.setColorAt(pos, QColor(min(hue, 255), min(brightness, 240), min(hue - 30, 255), 120))
        p.setBrush(ring_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(disk_cx, disk_cy), outer, outer * 0.8)
        # 擦除内圈
        p.setCompositionMode(QPainter.CompositionMode_DestinationOut)
        p.setBrush(QColor(0, 0, 0))
        p.drawEllipse(QPointF(disk_cx, disk_cy), inner, inner * 0.8)
        p.setCompositionMode(QPainter.CompositionMode_SourceOver)

    p.restore()

    # ── 吸积盘垂直射流（两极微弱蓝白喷流）──
    for sign in (-1, 1):
        jet_len = radius * (1.0 + 0.3 * abs(math.sin(anim_t * 1.5)))
        jet_width = radius * 0.05
        jet_grad = QRadialGradient(cx, cy + sign * jet_len * 0.2, jet_len * 0.7)
        jet_grad.setColorAt(0.0, QColor(180, 220, 255, 35))
        jet_grad.setColorAt(0.4, QColor(100, 160, 240, 15))
        jet_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setBrush(jet_grad); p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx, cy + sign * jet_len * 0.45), jet_width * 8, jet_len * 0.5)

    # ── 虫洞喉部（极暗核心 + 微弱蓝紫内缘辉光）──
    throat = QRadialGradient(cx, cy, throat_r * 1.8)
    throat.setColorAt(0.0, QColor(0, 0, 0))
    throat.setColorAt(0.30, QColor(1, 0, 3))
    throat.setColorAt(0.55, QColor(8, 2, 18))
    throat.setColorAt(0.75, QColor(15, 5, 40, 180))
    throat.setColorAt(0.90, QColor(30, 20, 80, 80))
    throat.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(throat); p.setPen(Qt.NoPen)
    p.drawEllipse(center, throat_r * 1.8, throat_r * 1.8)

    # ── 时空涟漪波（同心扭曲环，绕中心旋转）──
    for i_rip in range(3):
        rip_r = radius * (0.22 + i_rip * 0.14)
        rip_shift = math.sin(anim_t * 1.8 + i_rip) * radius * 0.08
        rip_grad = QRadialGradient(cx + rip_shift * 0.5, cy + rip_shift * 0.3, rip_r * 0.35)
        rip_grad.setColorAt(0.0, QColor(120, 80, 220, 70 - i_rip * 20))
        rip_grad.setColorAt(0.5, QColor(80, 40, 180, 35 - i_rip * 10))
        rip_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        p.setPen(QPen(QColor(100, 60, 200, 40 - i_rip * 12), 1.0))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(cx + rip_shift * 0.5, cy + rip_shift * 0.3), rip_r, rip_r)

    # ── 球面高光 ──
    spec = QRadialGradient(cx - radius * 0.18, cy - radius * 0.22, radius * 0.22)
    spec.setColorAt(0.0, QColor(180, 220, 255, 40))
    spec.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(spec); p.setPen(Qt.NoPen)
    p.drawEllipse(center, radius, radius)

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
            ig.setColorAt(0.78, QColor(140, 200, 240, ga // 2))
            ig.setColorAt(0.90, QColor(140, 200, 240, ga))
            ig.setColorAt(0.97, QColor(140//2, 200//2, 255, ga // 3))
            ig.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(ig)
            p.drawEllipse(center, ir, ir)
        # 外层扩散光晕
        for i in range(3):
            outer_r = radius + 10 + i * 10
            og = QRadialGradient(center, outer_r)
            ga = int((50 - i * 14) * hp)
            og.setColorAt(0.75, QColor(255, 255, 255, 0))
            og.setColorAt(0.88, QColor(140, 200, 240, ga // 2))
            og.setColorAt(0.96, QColor(140//2, 200//2, 255, ga // 3))
            og.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.setPen(Qt.NoPen); p.setBrush(og)
            p.drawEllipse(center, outer_r, outer_r)
        # 明亮轮廓环（呼吸感）
        br = 0.6 + 0.4 * abs(math.sin(anim_t * 4.0))
        rpen = QPen(QColor(140, 200, 240, int(220 * hp * br)), 2.5 + 1.0 * br)
        p.setPen(rpen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, radius + 3, radius + 3)


    p.restore()

```
