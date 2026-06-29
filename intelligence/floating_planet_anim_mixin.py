# -*- coding: utf-8 -*-
"""悬浮球动画 Mixin — 物理漫游、外星人、形态循环"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QRegion

from core.shapes import alien, robot_alien, ghost_alien, jellyfish_alien, SHAPE_MODES


class FloatingPlanetAnimMixin:
    """动画：物理漫游、外星人、形态循环切换"""

    def _tick(self):
        """每帧更新 —— 物理漫游 + 尺寸过渡 + 动画参数"""
        if self._auto_move and not self._drag_pause and not self._dragging:
            self._vy += self._gravity
            self._vx *= 0.9970
            self._vy *= 0.9970
            self._wander_timer += 1
            if self._wander_timer >= self._next_wander:
                self._wander_timer = 0
                self._next_wander = random.randint(180, 480)
                kick_vx = random.uniform(-1.8, 1.8)
                kick_vy = random.uniform(-1.8, 1.8)
                self._vx += kick_vx
                self._vy += kick_vy
            new_x = self.x() + int(self._vx)
            new_y = self.y() + int(self._vy)
            screen = QApplication.primaryScreen()
            if screen:
                geom = screen.availableGeometry()
                s = self._scaled_widget_size()
                left, top = geom.left(), geom.top()
                right, bottom = geom.right() - s, geom.bottom() - s - self.TOOLTIP_H
                if new_x < left:
                    new_x = left
                    self._vx = abs(self._vx) * self._bounce_factor
                    self._vy += random.uniform(-1.5, 1.5)
                elif new_x > right:
                    new_x = right
                    self._vx = -abs(self._vx) * self._bounce_factor
                    self._vy += random.uniform(-1.5, 1.5)
                if new_y < top:
                    new_y = top
                    self._vy = abs(self._vy) * self._bounce_factor
                    self._vx += random.uniform(-2.0, 2.0)
                elif new_y > bottom:
                    new_y = bottom
                    self._vy = -abs(self._vy) * self._bounce_factor
                    self._vx += random.uniform(-2.0, 2.0)
                    if abs(self._vy) < 1.0:
                        self._vy = 0
                        new_y = bottom
            if abs(self._vx) < 0.3 and abs(self._vy) < 0.3:
                self._vx = random.uniform(-1.5, 1.5)
                self._vy = random.uniform(-1.5, 1.5)
            self.move(new_x, new_y)

        diff = self._target_size - self._current_size
        if abs(diff) > 0.5:
            self._current_size += diff * 0.08
            self._center_on_current_pos()
        else:
            self._current_size = self._target_size

        self._anim_t += 0.0133
        self._tick_aliens()
        self.update()

    def _center_on_current_pos(self):
        old_s = self._scaled_widget_size()
        circle_cx = self.x() + old_s // 2
        circle_cy = self.y() + old_s // 2
        base_s = max(int(self._current_size), self.ACTIVE_SIZE)
        s = max(base_s, self._scaled_widget_size())
        new_rect = QRect(
            circle_cx - s // 2,
            circle_cy - s // 2,
            s, s + self.TOOLTIP_H
        )
        self.setFixedSize(s, s + self.TOOLTIP_H)
        self.setGeometry(new_rect)
        region = QRegion(0, 0, s, s, QRegion.Ellipse)
        region = region.united(QRegion(0, s, s, self.TOOLTIP_H))
        self.setMask(region)

    def _spawn_aliens(self):
        alien_types = [alien, robot_alien, ghost_alien, jellyfish_alien]
        count = random.randint(2, 3)
        aliens = []
        for i in range(count):
            angle = i * (2 * math.pi / count) + random.uniform(-0.3, 0.3)
            dist = random.uniform(1.4, 2.2)
            aliens.append([
                random.choice(alien_types),
                math.cos(angle) * dist,
                math.sin(angle) * dist,
                random.uniform(-0.3, 0.3),
                random.uniform(-0.3, 0.3),
                random.uniform(0, 2 * math.pi),
                random.uniform(12, 18),
            ])
        return aliens

    def _tick_aliens(self):
        rng = random.Random(int(self._anim_t * 1000) % 100000 + 42)
        for a in self._aliens:
            x, y = a[1], a[2]
            dist = math.hypot(x, y)
            angle = math.atan2(y, x)
            target_dist = 1.6 + a[6] * 0.03
            radial_force = (target_dist - dist) * 0.003
            orbital_speed = 0.15 + a[6] * 0.004
            a[3] += math.cos(angle) * radial_force - math.sin(angle) * orbital_speed
            a[4] += math.sin(angle) * radial_force + math.cos(angle) * orbital_speed
            a[3] += rng.uniform(-0.02, 0.02)
            a[4] += rng.uniform(-0.02, 0.02)
            a[3] *= 0.99
            a[4] *= 0.99
            speed = math.hypot(a[3], a[4])
            max_speed = 0.8
            if speed > max_speed:
                a[3] *= max_speed / speed
                a[4] *= max_speed / speed
            a[1] += a[3]
            a[2] += a[4]
            a[5] += 0.033

    def _check_alien_click(self, cx, cy, radius, click_x, click_y):
        planet_r = radius * 0.82
        for a in self._aliens:
            ax = cx + a[1] * planet_r
            ay = cy + a[2] * planet_r
            dist = math.hypot(click_x - ax, click_y - ay)
            if dist < a[6] * 1.5:
                return a[0]
        return None

    def _alien_click_animation(self, alien_type):
        type_names = {
            alien: "小绿外星人",
            robot_alien: "机器外星人",
            ghost_alien: "幽灵外星人",
            jellyfish_alien: "水母外星人",
        }
        name = type_names.get(alien_type, "外星来客")
        self._trigger_click_pulse()
        if self._voice:
            try:
                self._voice.speak(f"你好，我是{name}")
            except Exception:
                pass

    def _cycle_shape(self, direction: int):
        if self._current_category == "planet":
            keys = self._planet_keys
            idx = (self._current_planet_idx + direction) % len(keys)
            self._current_planet_idx = idx
        elif self._current_category == "starship":
            keys = self._starship_keys
            idx = (self._current_starship_idx + direction) % len(keys)
            self._current_starship_idx = idx
        else:
            keys = self._alien_keys
            idx = (self._current_alien_idx + direction) % len(keys)
            self._current_alien_idx = idx
        key = keys[idx]
        self._switch_to_shape(self._current_category, key)
        try:
            self._auto_switch_idx = self._all_shape_keys.index(key)
        except (AttributeError, ValueError):
            pass

    def _auto_cycle_shape(self):
        total = len(self._all_shape_keys)
        if total == 0:
            return
        key = self._all_shape_keys[self._auto_switch_idx]
        self._auto_switch_idx = (self._auto_switch_idx + 1) % total
        if key in self._planet_keys:
            category = "planet"
        elif key in self._alien_keys:
            category = "alien"
        else:
            category = "starship"
        self._switch_to_shape(category, key)
        name = SHAPE_MODES.get(key, {}).get("name", key)
        try:
            print(f"[AutoSwitch] #{self._auto_switch_idx}/{total} -> {name} ({key})")
        except OSError:
            pass
