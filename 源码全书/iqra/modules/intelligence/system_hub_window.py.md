# `iqra/modules/intelligence/system_hub_window.py`

> 路径：`iqra/modules/intelligence/system_hub_window.py` | 行数：200


---


```python
# -*- coding: utf-8 -*-
"""
系统管理中心 · SOLAR VAULT（真实星球子导航）
4颗子星球环绕，点击弹出独立系统管理窗口
"""
import os, math
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QFrame, QDialog,
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QFontMetrics

from core.planet_painter import (
    PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line,
)

# ═══════ 5颗系统管理子星球 ═══════
SYSTEM_PLANETS = [
    {"id": "base_info",     "name": "系统设置",   "style": "uranus",  "orbit": 120, "size": 42},
    {"id": "activation",    "name": "激活码",     "style": "sun",     "orbit": 165, "size": 44},
    {"id": "cloud_server",  "name": "云端同步",   "style": "neptune", "orbit": 210, "size": 46},
    {"id": "system_logs",   "name": "系统日志",   "style": "pluto",   "orbit": 255, "size": 44},
    {"id": "admin",         "name": "后台管理",   "style": "mars",    "orbit": 300, "size": 44},
]


class SystemHubHUD(QWidget):
    """系统管理星球导航"""

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
        n = len(SYSTEM_PLANETS)
        for i, p in enumerate(SYSTEM_PLANETS):
            offset_angle = i * (360.0 / n)
            rad = math.radians(self._angle + offset_angle)
            x = w2.x() + p["orbit"] * math.cos(rad)
            y = w2.y() + p["orbit"] * math.sin(rad)
            positions.append((p, QPointF(x, y)))
        return positions

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w2 = self._center

        for sp in SYSTEM_PLANETS:
            paint_orbit(p, w2, sp["orbit"])

        for _, pos in self._planet_positions():
            paint_energy_line(p, w2, pos)

        for sp, pos in self._planet_positions():
            style = PLANET_STYLES.get(sp["style"], PLANET_STYLES["neptune"])
            hovered = (self._hovered_planet == sp["id"])
            paint_planet(p, pos, sp["size"], style,
                         hovered=hovered, label=sp["name"], font_size=10)

        p.end()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        self._hovered_planet = None
        for sp, pt in self._planet_positions():
            r = sp["size"] + 8
            dx = pos.x() - pt.x()
            dy = pos.y() - pt.y()
            if dx * dx + dy * dy <= r * r:
                self._hovered_planet = sp["id"]
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


class SystemHubWindow(QMainWindow):
    """系统管理中心 · SOLAR VAULT"""

    def __init__(self, parent=None, role="admin"):
        super().__init__(parent)
        self._role = role
        self.setWindowTitle("一人公司 — 系统管理 · SOLAR VAULT")
        self.setMinimumSize(900, 700)
        self.resize(900, 700)
        if self._role != "admin":
            self._show_access_denied()
        else:
            self._build_ui()

    def _show_access_denied(self):
        """非管理员拒绝访问"""
        from PyQt5.QtWidgets import QMessageBox
        w = QWidget(self)
        w.setStyleSheet("background: #1a1020;")
        self.setCentralWidget(w)
        QMessageBox.warning(self, "权限不足", "仅管理员可访问系统管理中心。")

    def _build_ui(self):
        from core.cosmic import CosmicBackground
        bg = CosmicBackground()
        self.setCentralWidget(bg)

        self._hud = SystemHubHUD(self)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._hud.planet_clicked = self._on_planet_clicked
        self._hud.raise_()

        header = QWidget(self)
        header.setAttribute(Qt.WA_TranslucentBackground)
        header.setFixedHeight(60)
        header.setGeometry(0, 10, self.width(), 60)

        hl = QVBoxLayout(header)
        hl.setSpacing(2)
        title = QLabel("系统管理")
        title.setStyleSheet(
            "color: #ffcc80; font-size: 22px; font-weight: 800;"
            " letter-spacing: 6px; background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)
        hl.addWidget(title)
        subtitle = QLabel("SOLAR VAULT · 5颗子星")
        subtitle.setStyleSheet(
            "color: #887766; font-size: 10px; letter-spacing: 3px;"
            " background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        hl.addWidget(subtitle)

        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(255,180,80,40),
                stop:0.5 rgba(255,200,100,100),
                stop:0.7 rgba(255,180,80,40), stop:1 transparent);
            border: none;
        """)
        hl.addWidget(line)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_hud'):
            self._hud.setGeometry(0, 0, self.width(), self.height())

    def _on_planet_clicked(self, planet_id):
        try:
            if planet_id == "base_info":
                from modules.system.base_info_window import BaseInfoWindow
                dlg = BaseInfoWindow(self)
                dlg.exec_()
            elif planet_id == "activation":
                from modules.account.account_activation import AccountActivationWindow
                dlg = AccountActivationWindow(self)
                dlg.exec_()
            elif planet_id == "cloud_server":
                from modules.system.cloud_window import CloudWindow
                dlg = CloudWindow(self)
                dlg.exec_()
            elif planet_id == "system_logs":
                from modules.system.logs_window import LogsWindow
                dlg = LogsWindow(self)
                dlg.exec_()
            elif planet_id == "admin":
                from modules.admin.admin_window import AdminWindow
                dlg = AdminWindow(self)
                dlg.show()
        except ImportError as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "模块未就绪",
                                f"「{planet_id}」模块加载失败：{e}")

```
