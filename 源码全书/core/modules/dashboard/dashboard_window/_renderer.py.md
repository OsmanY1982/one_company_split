# `core/modules/dashboard/dashboard_window/_renderer.py`

> 路径：`core/modules/dashboard/dashboard_window/_renderer.py` | 行数：164


---


```python
"""
星球渲染 — _RendererMixin
包含 _get_orbit_center、_get_planet_pos、_planet_at_pos、
_on_hud_mouse_move、_on_hud_click、_tick、_paint_hud
"""
import math
import traceback
from datetime import datetime

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QPainterPath, QFont, QMouseEvent
)

try:
    from cosmic import ACCENT_CYAN, ACCENT_GOLD, ACCENT_PURPLE
    from planet_painter import PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line
except ImportError:
    try:
        from cosmic import ACCENT_CYAN, ACCENT_GOLD, ACCENT_PURPLE
    except ImportError:
        from core.cosmic import ACCENT_CYAN, ACCENT_GOLD, ACCENT_PURPLE
    try:
        from planet_painter import PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line
    except ImportError:
        from core.planet_painter import PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line
from ._planets import MEMBERSHIP_BADGE_COLORS, MEMBERSHIP_LABELS


class _RendererMixin:
    """星球渲染：动画、绘制 HUD"""

    def _get_orbit_center(self) -> QPointF:
        """轨道中心 — 窗口正中央"""
        w = self._hud.width()
        h = self._hud.height()
        return QPointF(w * 0.5, h * 0.52)

    def _get_planet_pos(self, planet: dict) -> QPointF:
        """计算星球当前位置（基于时间和轨道参数）"""
        cx = self._get_orbit_center()
        idx = self._planets.index(planet)
        phase = idx * math.pi * 2 / len(self._planets)
        angle = phase + self._t * (0.15 + idx * 0.04)  # 不同速度
        px = cx.x() + math.cos(angle) * planet["orbit"]
        py = cx.y() + math.sin(angle) * planet["orbit"] * 0.55  # 椭圆效果
        return QPointF(px, py)

    def _planet_at_pos(self, pos: QPointF) -> dict:
        """返回 pos 处的星球，无则 None"""
        for p in self._planets:
            pp = self._get_planet_pos(p)
            dist = math.hypot(pos.x() - pp.x(), pos.y() - pp.y())
            if dist <= p["radius"] + 12:  # 容忍点击区域
                return p
        return None

    def _on_hud_mouse_move(self, event: QMouseEvent):
        old = self._hovered_planet
        self._hovered_planet = self._planet_at_pos(event.pos())
        if old != self._hovered_planet:
            self._hud.update()

    def _on_hud_click(self, event: QMouseEvent):
        planet = self._planet_at_pos(event.pos())
        if planet:
            self._open_module(planet["id"])

    def _tick(self):
        self._t += 0.04
        self._hud.update()

    def _paint_hud(self, event):
        QWidget.paintEvent(self._hud, event)
        painter = QPainter(self._hud)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self._hud.width(), self._hud.height()

        # ── 轨道环 ──
        cx = self._get_orbit_center()

        # 扫描线
        scan_r = 310
        scan_a = self._t * 0.5 % (math.pi * 2)
        sx = cx.x() + math.cos(scan_a) * scan_r
        sy = cx.y() + math.sin(scan_a) * scan_r * 0.55
        ex = cx.x() + math.cos(scan_a + math.pi) * scan_r
        ey = cx.y() + math.sin(scan_a + math.pi) * scan_r * 0.55
        sg = QLinearGradient(QPointF(ex, ey), QPointF(sx, sy))
        sg.setColorAt(0, QColor(0, 0, 0, 0))
        sg.setColorAt(0.45, QColor(0, 180, 255, 8))
        sg.setColorAt(0.5, QColor(0, 180, 255, 20))
        sg.setColorAt(0.55, QColor(0, 180, 255, 8))
        sg.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(QPen(QBrush(sg), 1.5))
        painter.drawLine(QPointF(ex, ey), QPointF(sx, sy))

        # 轨道线
        for p in self._planets:
            paint_orbit(painter, cx, p["orbit"])

        # ── 星球 ──
        for p in self._planets:
            pp = self._get_planet_pos(p)
            style = PLANET_STYLES.get(p["style"], PLANET_STYLES["neptune"])
            is_hovered = p == self._hovered_planet
            paint_planet(painter, pp, p["radius"], style,
                         hovered=is_hovered, label=p["name"], font_size=11)

        # ── 会员等级徽章（船员模式） ──
        if self._role == "member" and self._membership_info:
            ms = self._membership_info
            level = ms.get("membership", "trial")
            badge_color = MEMBERSHIP_BADGE_COLORS.get(level, MEMBERSHIP_BADGE_COLORS["trial"])
            level_label = MEMBERSHIP_LABELS.get(level, "体验会员")

            expire_str = ms.get("expire_at", "")
            countdown_text = ""
            if expire_str:
                try:
                    expire_dt = datetime.strptime(expire_str, "%Y-%m-%d %H:%M:%S")
                    now = datetime.now()
                    remain = (expire_dt - now).days
                    if remain > 0:
                        countdown_text = f"剩余 {remain} 天"
                    elif remain == 0:
                        countdown_text = "今日到期"
                    else:
                        countdown_text = "已过期"
                except Exception:
                    traceback.print_exc()

            badge_x = w - 200
            badge_y = 14
            badge_w = 180
            badge_h = 32

            path = QPainterPath()
            path.addRoundedRect(QRectF(badge_x, badge_y, badge_w, badge_h), 16, 16)
            painter.setPen(QPen(QColor(badge_color.red(), badge_color.green(), badge_color.blue(), 80), 1))
            painter.setBrush(QBrush(QColor(badge_color.red(), badge_color.green(),
                                          badge_color.blue(), 25)))
            painter.drawPath(path)

            painter.setPen(QPen(QColor(badge_color.red(), badge_color.green(), badge_color.blue(), 220)))
            painter.setFont(QFont("PingFang SC", 10, QFont.Bold))
            painter.drawText(QRectF(badge_x + 10, badge_y, badge_w - 20, badge_h),
                             Qt.AlignVCenter | Qt.AlignLeft, level_label)

            if countdown_text:
                painter.setPen(QPen(QColor(badge_color.red(), badge_color.green(), badge_color.blue(), 150)))
                painter.setFont(QFont("Menlo", 9))
                painter.drawText(QRectF(badge_x + 10, badge_y, badge_w - 20, badge_h),
                                 Qt.AlignVCenter | Qt.AlignRight, countdown_text)

        # ── 底部标签 ──
        painter.setPen(QPen(QColor(50, 80, 130, 60)))
        painter.setFont(QFont("Menlo", 9))
        painter.drawText(QRectF(0, h - 36, w, 18),
                         Qt.AlignCenter, "ORBIT CONTROL")

        painter.end()

```
