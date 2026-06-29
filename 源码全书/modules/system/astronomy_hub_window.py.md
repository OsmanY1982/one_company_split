# `modules/system/astronomy_hub_window.py`

> 路径：`modules/system/astronomy_hub_window.py` | 行数：170


---


```python
# -*- coding: utf-8 -*-
"""
天文馆 · 子星球导航
环绕太阳核心的2颗子星球：太阳系天文馆 + 星谱探索
"""
import math
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame,
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter

from core.planet_painter import (
    PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line,
)

# ═══════ 2颗子星球配置 ═══════
# 窗口 700×600，中心约 (350, 300)，最大允许轨道 ≈ 275（留 25px 边距）
PLANETS = [
    {"id": "solar_system",   "name": "太阳系天文馆", "style": "sun",   "orbit": 180, "size": 55},
    {"id": "solar_explorer", "name": "星谱探索",     "style": "earth", "orbit": 240, "size": 52},
]


class NavigationHUD(QWidget):
    """真实星球导航叠加层"""

    planet_clicked = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._center = QPointF(0, 0)
        self._hovered_planet = None
        self._angle = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    def _tick(self):
        self._angle = (self._angle + 0.3) % 360.0
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._center = QPointF(self.width() / 2, self.height() / 2)

    def _planet_positions(self):
        w2 = self._center
        positions = []
        for i, p in enumerate(PLANETS):
            offset_angle = i * (360.0 / len(PLANETS))
            rad = math.radians(self._angle + offset_angle)
            x = w2.x() + p["orbit"] * math.cos(rad)
            y = w2.y() + p["orbit"] * math.sin(rad)
            positions.append((p, QPointF(x, y)))
        return positions

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w2 = self._center

        for planet in PLANETS:
            paint_orbit(p, w2, planet["orbit"])

        for planet_data, pos in self._planet_positions():
            paint_energy_line(p, w2, pos)

        for planet_data, pos in self._planet_positions():
            style = PLANET_STYLES.get(planet_data.get("style"), PLANET_STYLES["neptune"])
            is_hovered = (self._hovered_planet == planet_data["id"])
            paint_planet(p, pos, planet_data["size"], style,
                         hovered=is_hovered, label=planet_data["name"], font_size=10,
                         anim_t=self._angle)

        p.end()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        self._hovered_planet = None
        for planet_data, pt in self._planet_positions():
            r = planet_data["size"] + 8
            dx = pos.x() - pt.x()
            dy = pos.y() - pt.y()
            if dx * dx + dy * dy <= r * r:
                self._hovered_planet = planet_data["id"]
                self.setCursor(Qt.PointingHandCursor)
                self.update()
                return
        self.setCursor(Qt.ArrowCursor)
        if self._hovered_planet is not None:
            self._hovered_planet = None
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._hovered_planet:
            if self.planet_clicked:
                self.planet_clicked(self._hovered_planet)


class AstronomyHubWindow(QWidget):
    """天文馆 · 子星球导航主窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("一人公司 — 天文馆 · ASTRONOMY HUB")
        self.setFixedSize(700, 600)
        self.setWindowFlags(Qt.Window)
        self._build_ui()

    def _build_ui(self):
        from core.cosmic import CosmicBackground
        bg = CosmicBackground(self)
        bg.setGeometry(0, 0, self.width(), self.height())

        self._hud = NavigationHUD(self)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._hud.planet_clicked = self._on_planet_clicked
        self._hud.raise_()

        header = QWidget(self)
        header.setAttribute(Qt.WA_TranslucentBackground)
        header.setFixedHeight(70)
        header.setGeometry(0, 10, self.width(), 70)

        hl = QVBoxLayout(header)
        hl.setSpacing(2)
        title = QLabel("天文馆")
        title.setStyleSheet(
            "color: #ddaaff; font-size: 24px; font-weight: 800; "
            "letter-spacing: 8px; background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)
        hl.addWidget(title)
        subtitle = QLabel("ASTRONOMY HUB · 2颗子星球")
        subtitle.setStyleSheet(
            "color: #776699; font-size: 11px; letter-spacing: 3px; "
            "background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        hl.addWidget(subtitle)

        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(255,180,40,50),
                stop:0.5 rgba(255,200,60,120),
                stop:0.7 rgba(255,180,40,50), stop:1 transparent);
            border: none;
        """)
        hl.addWidget(line)

    def _on_planet_clicked(self, planet_id):
        try:
            if planet_id == "solar_system":
                from modules.intelligence.solar_system_window import SolarSystemWindow
                win = SolarSystemWindow(self)
                win.show()
            elif planet_id == "solar_explorer":
                from solar_explorer.star_catalog_window import StarCatalogWindow
                win = StarCatalogWindow(self)
                win.show()

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "模块未就绪",
                                f"「{planet_id}」模块加载失败：{e}")

```
