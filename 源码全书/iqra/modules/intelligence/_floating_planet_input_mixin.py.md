# `iqra/modules/intelligence/_floating_planet_input_mixin.py`

> 路径：`iqra/modules/intelligence/_floating_planet_input_mixin.py` | 行数：98


---


```python
# -*- coding: utf-8 -*-
"""
FloatingPlanetInputMixin — 鼠标事件处理
鼠标按下/移动/释放/双击/滚轮/进入/离开事件
"""
import math
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QMouseEvent


class FloatingPlanetInputMixin:
    """鼠标事件 mixin（mousePressEvent ~ leaveEvent）"""

    # ── 鼠标事件 ──

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            s = self._scaled_widget_size()
            cx, cy = s / 2, s / 2
            radius = self._current_size / 2
            hit_alien = self._check_alien_click(cx, cy, radius, pos.x(), pos.y())
            if hit_alien is not None:
                self._alien_click_animation(hit_alien)
                event.accept()
                return
            self._dragging = True
            self._drag_start = event.globalPos() - self.frameGeometry().topLeft()
            self._drag_trail = [(event.globalPos(), datetime.now())]
            self._drag_pause = True
            event.accept()
        elif event.button() == Qt.RightButton:
            self._dragging = False
            global_pos = event.globalPos()
            QTimer.singleShot(10, lambda gp=global_pos: self._show_context_menu(gp))
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        self._mouse_x = event.pos().x()
        self._mouse_y = event.pos().y()
        if self._dragging and event.buttons() & Qt.LeftButton:
            delta = event.globalPos() - (self.frameGeometry().topLeft() + self._drag_start)
            if delta.manhattanLength() > 5 or self._state == self.ACTIVE:
                self.move(event.globalPos() - self._drag_start)
                now = datetime.now()
                self._drag_trail.append((event.globalPos(), now))
                if len(self._drag_trail) > self._drag_trail_max:
                    self._drag_trail = self._drag_trail[-self._drag_trail_max:]
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._dragging:
            total_delta = event.globalPos() - (self.frameGeometry().topLeft() + self._drag_start)
            self._dragging = False
            self._drag_pause = False
            if self._auto_move and len(self._drag_trail) >= 2:
                p0, t0 = self._drag_trail[0]
                p1, t1 = self._drag_trail[-1]
                dt = (t1 - t0).total_seconds()
                if dt > 0.005:
                    dx = p1.x() - p0.x()
                    dy = p1.y() - p0.y()
                    self._vx = (dx / dt) / 60.0
                    self._vy = (dy / dt) / 60.0
                    max_speed = 18.0
                    speed = math.sqrt(self._vx**2 + self._vy**2)
                    if speed > max_speed:
                        self._vx = self._vx / speed * max_speed
                        self._vy = self._vy / speed * max_speed
            self._drag_trail = []
            if total_delta.manhattanLength() < 5:
                self.toggle()
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self._open_chat()
        event.accept()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self._cycle_shape(1 if delta > 0 else -1)
        event.accept()

    def enterEvent(self, event):
        self._hover = True
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_scale)
        self._hover_anim.setEndValue(1.08)
        self._hover_anim.start()
        self._smart_raise()

    def leaveEvent(self, event):
        self._hover = False
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_scale)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()

```
