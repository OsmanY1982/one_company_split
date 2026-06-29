# -*- coding: utf-8 -*-
"""
系统管理中心 · 子星球导航
环绕太阳核心的4颗子星球，点击分别路由到系统模块窗口
"""
import math
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QFrame,
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QFontMetrics

from core.planet_painter import (
    PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line,
)

# ═══════ 6颗子星球配置 ═══════
# 窗口 800×650，中心约 (400, 325)，最大允许轨道 ≈ 300（留 25px 边距）
PLANETS = [
    {"id": "system_settings", "name": "系统设置", "style": "uranus",  "orbit": 120, "size": 55},
    {"id": "activation",      "name": "激活码",   "style": "sun",     "orbit": 160, "size": 55},
    {"id": "cloud_sync",      "name": "云端同步", "style": "neptune", "orbit": 200, "size": 52},
    {"id": "system_logs",     "name": "系统日志", "style": "moon",    "orbit": 240, "size": 52},
    {"id": "cloud_server",    "name": "云服务器", "style": "mercury", "orbit": 280, "size": 50},
    {"id": "admin",           "name": "后台管理", "style": "mars",    "orbit": 300, "size": 52},
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


class SystemHubWindow(QMainWindow):
    """系统管理中心 · 子星球导航主窗口"""

    def __init__(self, parent=None, role="admin"):
        super().__init__(parent)
        self._role = role
        self.setWindowTitle("一人公司 — 系统管理中心 · SOLAR HUB")
        self.setMinimumSize(800, 650)
        self.resize(800, 650)
        if self._role != "admin":
            self._show_access_denied()
            return
        self._build_ui()

    def _show_access_denied(self):
        """非管理员用户，显示拒绝访问并自动关闭窗口"""
        from PyQt5.QtWidgets import QMessageBox, QWidget
        w = QWidget(self)
        w.setStyleSheet("background: #1a1020;")
        self.setCentralWidget(w)
        QMessageBox.warning(self, "权限不足", "仅管理员可访问系统管理中心。")
        self.close()

    def _build_ui(self):
        from core.cosmic import CosmicBackground
        bg = CosmicBackground()
        self.setCentralWidget(bg)

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
        title = QLabel("系统管理")
        title.setStyleSheet("color: #ddaaff; font-size: 24px; font-weight: 800; letter-spacing: 8px; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        hl.addWidget(title)
        subtitle = QLabel("SOLAR HUB · 6颗子星球")
        subtitle.setStyleSheet("color: #776699; font-size: 11px; letter-spacing: 3px; background: transparent;")
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_hud'):
            self._hud.setGeometry(0, 0, self.width(), self.height())

    def _on_planet_clicked(self, planet_id):
        try:
            if planet_id == "system_settings":
                from modules.system.base_info_window import BaseInfoWindow
                dlg = BaseInfoWindow(self)
                dlg.exec_()
            elif planet_id == "activation":
                from modules.account.account_activation import AccountActivationWindow
                dlg = AccountActivationWindow(self)
                dlg.exec_()
            elif planet_id == "cloud_sync":
                from modules.system.cloud_window import CloudWindow
                dlg = CloudWindow(self)
                dlg.exec_()
            elif planet_id == "system_logs":
                from modules.system.logs_window import LogsWindow
                dlg = LogsWindow(self)
                dlg.exec_()
            elif planet_id == "cloud_server":
                from modules.system.cloud_server_window import CloudServerWindow
                win = CloudServerWindow(self)
                win.show()
            elif planet_id == "admin":
                from modules.admin.admin_window import AdminWindow
                win = AdminWindow(self)
                win.show()

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "模块未就绪",
                                f"「{planet_id}」模块加载失败：{e}")
