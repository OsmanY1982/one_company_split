# `iqra/modules/intelligence/iqra_floating_planet.py`

> 路径：`iqra/modules/intelligence/iqra_floating_planet.py` | 行数：294


---


```python
# -*- coding: utf-8 -*-
"""
iqra 悬浮星球 — 桌面常驻 AI 助理
可拖拽、语音对话（Apple Speech 引擎）、右键菜单导航、双击对话
"""
import sys, os, traceback, math, random
import subprocess
import threading
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QApplication, QMessageBox,
)
from PyQt5.QtCore import (
    Qt, QTimer, QPoint, QRect, QSize, QPointF, QRectF,
    QPropertyAnimation, QEasingCurve, pyqtProperty,
)
from PyQt5.QtGui import (
    QPainter, QColor, QMouseEvent, QFont, QRegion,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.planet_painter import PLANET_STYLES
from core.shapes import SHAPE_PLANETS, SHAPE_ALIENS, SHAPE_STARSHIPS, SHAPE_MODES
from .floating_planet_anim_mixin import FloatingPlanetAnimMixin
from .floating_planet_draw_mixin import FloatingPlanetDrawMixin
from .floating_planet_menu_mixin import FloatingPlanetMenuMixin
from ._floating_planet_modules_mixin import FloatingPlanetModulesMixin
from ._floating_planet_chat_mixin import FloatingPlanetChatMixin
from ._floating_planet_input_mixin import FloatingPlanetInputMixin


class FloatingPlanet(FloatingPlanetAnimMixin, FloatingPlanetDrawMixin,
                     FloatingPlanetMenuMixin, FloatingPlanetModulesMixin,
                     FloatingPlanetChatMixin, FloatingPlanetInputMixin, QWidget):
    """桌面悬浮星球 — frameless + 圆形遮罩"""

    SLEEP = "sleep"
    WAKING = "waking"
    ACTIVE = "active"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    CONVERSING = "conversing"

    SLEEP_SIZE = 85
    ACTIVE_SIZE = 117

    # ── pyqtProperty ──
    def _get_hover_scale(self):
        return self._hover_scale
    def _set_hover_scale(self, val):
        self._hover_scale = val
        self.update()
    hoverScale = pyqtProperty(float, _get_hover_scale, _set_hover_scale)

    def _get_click_pulse(self):
        return self._click_pulse
    def _set_click_pulse(self, val):
        self._click_pulse = val
        self.update()
    clickPulse = pyqtProperty(float, _get_click_pulse, _set_click_pulse)

    def __init__(self, iqra_engine=None,
                 role: str = "admin",
                 membership_info: dict = None,
                 config: dict = None):
        super().__init__()
        self._engine = iqra_engine
        self._role = role or "admin"
        self._membership_info = membership_info or {}
        self._config = config or {}

        self._state = self.SLEEP
        self._current_size = self.SLEEP_SIZE
        self._target_size = self.SLEEP_SIZE
        self._standalone_chat = None
        self._open_windows: dict = {}  # 保持非模态窗口引用防止被 GC 回收
        self._tooltip_text = "经典星球"
        self.TOOLTIP_H = 26
        self._dragging = False
        self._drag_start = QPoint()
        self._anim_t = 0.0
        self._hover = False

        self._hover_scale = 1.0
        self._hover_anim = QPropertyAnimation(self, b"hoverScale")
        self._hover_anim.setDuration(200)
        self._hover_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._click_pulse = 0.0
        self._pulse_anim = QPropertyAnimation(self, b"clickPulse")
        self._pulse_anim.setDuration(350)
        self._pulse_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._scale_multiplier = 1.0

        self._auto_move = True
        self._vx = 0.0
        self._vy = 0.0
        self._gravity = 0.0
        self._bounce_factor = 0.3
        self._drag_pause = False
        self._drag_trail = []
        self._drag_trail_max = 5
        self._wander_timer = 0
        self._next_wander = 120

        self._style = PLANET_STYLES.get("earth", PLANET_STYLES["neptune"])
        self._shape_mode = None
        self._planet_keys = SHAPE_PLANETS.copy()
        self._alien_keys = SHAPE_ALIENS.copy()
        self._starship_keys = SHAPE_STARSHIPS.copy()
        self._current_category = "planet"
        self._current_planet_idx = 0
        self._current_alien_idx = 0
        self._current_starship_idx = 0

        self._aliens = self._spawn_aliens()
        self._mouse_x = 0
        self._mouse_y = 0

        self._all_shape_keys = self._planet_keys + self._alien_keys + self._starship_keys
        self._auto_switch_idx = 0
        self._auto_switch_timer = QTimer(self)
        self._auto_switch_timer.timeout.connect(self._auto_cycle_shape)
        self._auto_switch_timer.start(7000)

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        # self._keep_on_top_timer 已移除：改为 enterEvent 中调用 _smart_raise()
        # 避免持续 raise 导致悬浮球压在其它窗口上面
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._active_popup = None

        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = geom.right() - self.ACTIVE_SIZE - 80
            y = geom.center().y() - self.ACTIVE_SIZE // 2
        else:
            x, y = 1300, 400

        self.setGeometry(x, y, self.ACTIVE_SIZE, self.ACTIVE_SIZE + self.TOOLTIP_H)
        self._apply_circular_mask()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

        self._daemon_cleanup = None
        self._cleanup_done = False

    def _scaled_widget_size(self):
        return max(16, int(self.ACTIVE_SIZE * self._scale_multiplier))

    def _apply_circular_mask(self):
        s = self._scaled_widget_size()
        region = QRegion(0, 0, s, s, QRegion.Ellipse)
        region = region.united(QRegion(0, s, s, self.TOOLTIP_H))
        self.setMask(region)

    # ── 状态切换 ──

    def wake(self):
        if self._state == self.ACTIVE:
            return
        self._state = self.WAKING
        self._target_size = self.ACTIVE_SIZE
        QTimer.singleShot(300, self._on_wake_complete)

    def _on_wake_complete(self):
        if self._state == self.WAKING:
            self._state = self.ACTIVE

    def sleep(self):
        self._state = self.SLEEP
        self._target_size = self.SLEEP_SIZE

    def toggle(self):
        if self._state == self.SLEEP:
            self.wake()
        else:
            self.sleep()
        self._trigger_click_pulse()

    def _trigger_click_pulse(self):
        self._pulse_anim.stop()
        self._click_pulse = 1.0
        self._pulse_anim.setStartValue(1.0)
        self._pulse_anim.setEndValue(0.0)
        self._pulse_anim.start()
        self.update()

    # ── 生命周期 ──

    def showEvent(self, event):
        super().showEvent(event)
        from core.ad_launcher import check_and_prompt_ad
        check_and_prompt_ad(self)

    # ── 鼠标事件 → FloatingPlanetInputMixin
    # ── 模块打开 → FloatingPlanetModulesMixin

    def _switch_to_shape(self, category: str, key: str):
        if category == "planet":
            if key in self._planet_keys:
                self._current_planet_idx = self._planet_keys.index(key)
                self._shape_mode = key
                self._current_category = "planet"
        elif category == "alien":
            if key in self._alien_keys:
                self._current_alien_idx = self._alien_keys.index(key)
                self._shape_mode = key
                self._current_category = "alien"
        elif category == "starship":
            if key in self._starship_keys:
                self._current_starship_idx = self._starship_keys.index(key)
                self._shape_mode = key
                self._current_category = "starship"
        else:
            return
        name = SHAPE_MODES.get(key, {}).get("name", key)
        self._tooltip_text = name
        try:
            print(f"[FloatingPlanet] 切换到形态: {name} ({key})")
        except OSError:
            pass

    # ── AI 对话 → FloatingPlanetChatMixin

    # ── 退出 ──

    def _on_exit(self):
        reply = QMessageBox.question(
            self, "退出悬浮球",
            "确定要退出悬浮球吗？\n可从智能中心重新启动。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._do_cleanup()
            self.close()

    def _do_cleanup(self):
        if self._cleanup_done:
            return
        self._cleanup_done = True
        if self._daemon_cleanup:
            self._daemon_cleanup()

    def closeEvent(self, event):
        if hasattr(self, '_keep_on_top_timer') and self._keep_on_top_timer.isActive():
            self._keep_on_top_timer.stop()
        if not event.spontaneous():
            self._do_cleanup()
        else:
            event.ignore()
            return
        super().closeEvent(event)

    def _toggle_auto_move(self):
        self._auto_move = not self._auto_move
        if self._auto_move:
            angle = random.uniform(0, math.pi * 2)
            kick = random.uniform(3.0, 6.0)
            self._vx = math.cos(angle) * kick
            self._vy = math.sin(angle) * kick

    def _set_scale_multiplier(self, value: float):
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            max_by_width = geom.width() * 0.9 / self.ACTIVE_SIZE
            max_by_height = geom.height() * 0.9 / self.ACTIVE_SIZE
            max_scale = min(3.0, max_by_width, max_by_height)
        else:
            max_scale = 3.0
        value = max(0.5, min(value, max_scale))
        if abs(self._scale_multiplier - value) < 0.01:
            return
        old_s = self._scaled_widget_size()
        self._scale_multiplier = value
        s = self._scaled_widget_size()
        circle_cx = self.x() + old_s // 2
        circle_cy = self.y() + old_s // 2
        self.setFixedSize(s, s + self.TOOLTIP_H)
        new_rect = QRect(
            circle_cx - s // 2,
            circle_cy - s // 2,
            s, s + self.TOOLTIP_H
        )
        self.setGeometry(new_rect)
        self._apply_circular_mask()
        self.update()

```
