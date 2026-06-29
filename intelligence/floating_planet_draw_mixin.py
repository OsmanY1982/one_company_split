# -*- coding: utf-8 -*-
"""悬浮球绘制 Mixin — paintEvent + 外星人绘制"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QFont,
)

from core.planet_painter import paint_planet
from core.shapes import SHAPE_PAINTERS


class FloatingPlanetDrawMixin:
    """绘制：paintEvent、外星人渲染"""

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        s = self._scaled_widget_size()
        center = QPointF(s / 2.0, s / 2.0)
        r = self._current_size * self._scale_multiplier / 2

        scaled_r = int(r * self._hover_scale)

        # ── 语音状态光效 ──
        if self._state == self.LISTENING:
            for layer in range(3):
                wave_phase = self._anim_t * (5 + layer * 2)
                pulse_r = scaled_r + 8 + int((10 + layer * 6) * abs(math.sin(wave_phase)))
                pulse_grad = QRadialGradient(center, pulse_r)
                pulse_grad.setColorAt(0, QColor(255, 80, 80, 0))
                pulse_grad.setColorAt(0.35, QColor(255, 100, 80, 30 - layer * 8))
                pulse_grad.setColorAt(0.7, QColor(255, 60, 60, 15 - layer * 5))
                pulse_grad.setColorAt(1.0, QColor(255, 80, 80, 0))
                p.setBrush(pulse_grad)
                p.setPen(Qt.NoPen)
                p.drawEllipse(center, pulse_r, pulse_r)
        elif self._state == self.THINKING:
            for layer in range(3):
                wave_phase = self._anim_t * (4 + layer * 1.5)
                think_r = scaled_r + 6 + int((6 + layer * 4) * abs(math.sin(wave_phase)))
                think_grad = QRadialGradient(center, think_r)
                think_grad.setColorAt(0, QColor(80, 160, 255, 0))
                think_grad.setColorAt(0.3, QColor(100, 180, 255, 35 - layer * 10))
                think_grad.setColorAt(0.6, QColor(140, 100, 255, 20 - layer * 6))
                think_grad.setColorAt(1.0, QColor(80, 160, 255, 0))
                p.setBrush(think_grad)
                p.setPen(Qt.NoPen)
                p.drawEllipse(center, think_r, think_r)
        elif self._state == self.SPEAKING:
            for layer in range(3):
                wave_phase = self._anim_t * (6 + layer * 2)
                speak_r = scaled_r + 6 + int((8 + layer * 5) * abs(math.sin(wave_phase)))
                speak_grad = QRadialGradient(center, speak_r)
                speak_grad.setColorAt(0, QColor(80, 255, 120, 0))
                speak_grad.setColorAt(0.3, QColor(80, 255, 140, 35 - layer * 10))
                speak_grad.setColorAt(0.6, QColor(60, 220, 100, 20 - layer * 6))
                speak_grad.setColorAt(1.0, QColor(80, 255, 120, 0))
                p.setBrush(speak_grad)
                p.setPen(Qt.NoPen)
                p.drawEllipse(center, speak_r, speak_r)
        elif self._state == self.CONVERSING:
            for layer in range(3):
                wave_phase = self._anim_t * (3.5 + layer * 2.2)
                conv_r = scaled_r + 5 + int((7 + layer * 4) * abs(math.sin(wave_phase)))
                conv_grad = QRadialGradient(center, conv_r)
                conv_grad.setColorAt(0, QColor(255, 200, 60, 0))
                conv_grad.setColorAt(0.3, QColor(255, 180, 40, 40 - layer * 10))
                conv_grad.setColorAt(0.6, QColor(255, 160, 20, 25 - layer * 7))
                conv_grad.setColorAt(1.0, QColor(255, 140, 0, 0))
                p.setBrush(conv_grad)
                p.setPen(Qt.NoPen)
                p.drawEllipse(center, conv_r, conv_r)
        elif self._state in (self.WAKING, self.ACTIVE):
            for layer in range(2):
                wave_phase = self._anim_t * (3 + layer * 1.8)
                wave_r = scaled_r + 4 + int((6 + layer * 4) * abs(math.sin(wave_phase)))
                wave_grad = QRadialGradient(center, wave_r)
                wave_grad.setColorAt(0, QColor(80, 160, 255, 0))
                wave_grad.setColorAt(0.4, QColor(80, 160, 255, 12 - layer * 4))
                wave_grad.setColorAt(0.75, QColor(120, 100, 255, 8 - layer * 3))
                wave_grad.setColorAt(1.0, QColor(80, 160, 255, 0))
                p.setBrush(wave_grad)
                p.setPen(Qt.NoPen)
                p.drawEllipse(center, wave_r, wave_r)

        # ── 点击脉冲波纹 ──
        if self._click_pulse > 0.01:
            pulse_alpha = int(80 * self._click_pulse)
            pulse_ring_r = scaled_r + 4 + int(20 * (1.0 - self._click_pulse))
            pulse_grad = QRadialGradient(center, pulse_ring_r)
            pulse_grad.setColorAt(0, QColor(255, 255, 255, 0))
            pulse_grad.setColorAt(0.5, QColor(255, 255, 255, pulse_alpha // 3))
            pulse_grad.setColorAt(0.85, QColor(100, 200, 255, pulse_alpha))
            pulse_grad.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(pulse_grad)
            p.setPen(Qt.NoPen)
            p.drawEllipse(center, pulse_ring_r, pulse_ring_r)

        # 渲染形态：优先 shapes 系统，否则回退 planet_painter
        if self._shape_mode and self._shape_mode in SHAPE_PAINTERS:
            painter_fn = SHAPE_PAINTERS[self._shape_mode]
            painter_fn(p, center, scaled_r, self._anim_t, self._hover, 1.0)
        else:
            paint_planet(p, center, scaled_r, self._style, hovered=self._hover,
                         anim_t=self._anim_t)

        # 休眠态覆盖半透明暗层
        if self._state == self.SLEEP:
            overlay = QColor(0, 0, 0, 100)
            p.setBrush(overlay)
            p.setPen(Qt.NoPen)
            p.drawEllipse(center, int(r), int(r))

        # ── 外星人装饰 ──
        self._draw_aliens(p, center.x(), center.y(), scaled_r)

        # ── 昵称文本 ──
        if self._tooltip_text:
            s = self._scaled_widget_size()
            tip_y = max(s, int(self._current_size)) + 4
            p.setFont(QFont("PingFang SC", 9))
            p.setPen(QColor(255, 255, 255, 180))
            p.drawText(QRectF(0, tip_y, self.width(), self.TOOLTIP_H - 4),
                       Qt.AlignCenter, self._tooltip_text)

        p.end()

    def _draw_aliens(self, painter, cx, cy, radius):
        """绘制所有外星人"""
        planet_r = radius * 0.82
        for a in self._aliens:
            atype = a[0]
            ax = cx + a[1] * planet_r
            ay = cy + a[2] * planet_r
            asize = a[6]
            draw_center = QPointF(ax, ay)
            dist_to_mouse = math.hypot(
                self._mouse_x - ax, self._mouse_y - ay
            )
            hovered = dist_to_mouse < asize * 1.5
            try:
                atype.paint(painter, draw_center, asize,
                           a[5], hovered, 0.85)
            except Exception:
                pass
