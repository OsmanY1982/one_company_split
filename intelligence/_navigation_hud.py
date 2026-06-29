# -*- coding: utf-8 -*-
"""
AI 助手导航 HUD — 13颗真实星球环绕中央 AI 核心
"""
import math
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter

from core.planet_painter import (
    PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line,
)

# ═══════════════════════════════════════════
# 12颗星球配置 — 11种 style 全覆盖，无重复
# ═══════════════════════════════════════════
PLANETS = [
    {"id": "iqra_chat",         "name": "AI对话",       "style": "earth",    "orbit": 85,  "size": 48},
    {"id": "super_intelligence",   "name": "超级智能",     "style": "jupiter",  "orbit": 113, "size": 44},
    {"id": "enhanced_chat",        "name": "增强对话",     "style": "neptune",  "orbit": 141, "size": 40},
    {"id": "knowledge_base",       "name": "知识库",       "style": "uranus",   "orbit": 169, "size": 42},
    {"id": "system_monitor",       "name": "系统监控",     "style": "mars",     "orbit": 197, "size": 38},
    {"id": "quick_actions",        "name": "快捷操作",     "style": "mercury",  "orbit": 225, "size": 36},
    {"id": "anomaly_detector",     "name": "异常检测",     "style": "pluto",    "orbit": 253, "size": 36},
    {"id": "recommendation_engine","name": "推荐引擎",     "style": "sun",      "orbit": 281, "size": 40},
    {"id": "data_visualization",   "name": "数据可视化",   "style": "moon",     "orbit": 309, "size": 38},
    {"id": "smart_workflow",       "name": "智能工作流",   "style": "venus",    "orbit": 337, "size": 42},
    {"id": "business_ai",          "name": "商业AI",       "style": "saturn",   "orbit": 365, "size": 44},
    {"id": "voice_interface",      "name": "语音接口",     "style": "earth",    "orbit": 393, "size": 38},
]


class NavigationHUD(QWidget):
    """透明叠加层 — 13颗星球 + 轨道 + 中央 AI 核心"""

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
        self._angle = (self._angle + 0.2) % 360.0
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

        # ── 轨道线 ──
        for planet in PLANETS:
            paint_orbit(p, w2, planet["orbit"])

        # ── 能量连接线 ──
        for _, pos in self._planet_positions():
            paint_energy_line(p, w2, pos)

        # ── 13颗行星 ──
        for planet_data, pos in self._planet_positions():
            style = PLANET_STYLES.get(planet_data["style"], PLANET_STYLES["neptune"])
            hovered = (self._hovered_planet == planet_data["id"])
            paint_planet(p, pos, planet_data["size"], style,
                         hovered=hovered, label=planet_data["name"], font_size=10)

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