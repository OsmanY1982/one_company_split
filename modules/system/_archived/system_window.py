"""
系统设置 → 工程舱 · ENGINEERING DECK
小星球导航模式：4颗小星球环绕工程舱核心
"""
import traceback
import os, sqlite3, json, math
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QDialog
)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QFont, QMouseEvent
)
from core.cosmic import CosmicBackground

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

# ═══════ 小星球定义 ═══════
ENGINE_PLANETS = [
    {"id": "base_info",  "name": "基础信息", "color": QColor(100, 120, 140), "orbit": 140, "radius": 28},
    {"id": "activation", "name": "激活码",   "color": QColor(200, 170, 60),  "orbit": 210, "radius": 30},
    {"id": "cloud",      "name": "云端同步", "color": QColor(100, 160, 220), "orbit": 280, "radius": 26},
    {"id": "logs",       "name": "系统日志", "color": QColor(140, 100, 180), "orbit": 350, "radius": 24},
]

CORE_COLOR = QColor(136, 153, 170)  # 金属灰 #8899aa

# ═══════ DB 初始化 ═══════
def _init_dbs():
    db = os.path.join(DATA_DIR, "activation.db")
    conn = sqlite3.connect(db)
    conn.execute('''CREATE TABLE IF NOT EXISTS activation (
        id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL,
        code_type TEXT DEFAULT '试用', duration_days INTEGER DEFAULT 0,
        is_used INTEGER DEFAULT 0, used_by TEXT, used_at TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    conn.commit(); conn.close()

    db = os.path.join(DATA_DIR, "system_logs.db")
    conn = sqlite3.connect(db)
    conn.execute('''CREATE TABLE IF NOT EXISTS op_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, module TEXT, action TEXT,
        detail TEXT, created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sync_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sync_type TEXT,
        status TEXT, detail TEXT, created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS error_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, module TEXT, error TEXT,
        detail TEXT, created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    conn.commit(); conn.close()

_init_dbs()


class SystemWindow(QMainWindow):
    """工程舱 · ENGINEERING DECK — 小星球导航"""

    def __init__(self, parent=None, role="admin"):
        super().__init__(parent)
        self._role = role
        self.setWindowTitle("一人公司 — 工程舱 · ENGINEERING DECK")
        self.setMinimumSize(900, 620)
        self._t = 0
        self._hovered_planet = None
        self._open_windows = {}

        self._cosmic = CosmicBackground()
        self.setCentralWidget(self._cosmic)

        self._hud = QWidget(self)
        self._hud.setAttribute(Qt.WA_TranslucentBackground)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._hud.setMouseTracking(True)
        self._hud.mouseMoveEvent = self._on_mouse_move
        self._hud.mousePressEvent = self._on_click
        self._hud.raise_()

        self._build_ui()

        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(50)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._hud.setGeometry(0, 0, self.width(), self.height())

    def _build_ui(self):
        self._hud.paintEvent = self._paint_hud

        # ── 顶部 Header ──
        header = QWidget(self._hud)
        header.setStyleSheet("background: transparent;")
        header.setGeometry(0, 10, self.width(), 80)
        hl = QVBoxLayout(header)
        hl.setSpacing(4)
        hl.setContentsMargins(24, 0, 24, 0)

        title = QLabel("工程舱")
        title.setStyleSheet("color: #aabbcc; font-size: 22px; font-weight: 800; letter-spacing: 6px; background: transparent;")
        hl.addWidget(title, alignment=Qt.AlignCenter)

        subtitle = QLabel("ENGINEERING DECK · 点击星球进入模块")
        subtitle.setStyleSheet("color: #667788; font-size: 10px; letter-spacing: 2px; background: transparent;")
        hl.addWidget(subtitle, alignment=Qt.AlignCenter)

        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(130,145,165,50),
                stop:0.5 rgba(160,175,195,120),
                stop:0.7 rgba(130,145,165,50), stop:1 transparent);
            border: none;
        """)
        hl.addWidget(line)

    def _get_orbit_center(self) -> QPointF:
        w = self._hud.width()
        h = self._hud.height()
        return QPointF(w * 0.5, h * 0.55)

    def _get_planet_pos(self, planet: dict) -> QPointF:
        cx = self._get_orbit_center()
        idx = ENGINE_PLANETS.index(planet)
        phase = idx * math.pi * 0.55
        angle = phase + self._t * (0.10 + idx * 0.04)
        px = cx.x() + math.cos(angle) * planet["orbit"]
        py = cx.y() + math.sin(angle) * planet["orbit"] * 0.55
        return QPointF(px, py)

    def _planet_at_pos(self, pos: QPointF):
        for p in ENGINE_PLANETS:
            pp = self._get_planet_pos(p)
            dist = math.hypot(pos.x() - pp.x(), pos.y() - pp.y())
            if dist <= p["radius"] + 14:
                return p
        return None

    def _on_mouse_move(self, event: QMouseEvent):
        old = self._hovered_planet
        self._hovered_planet = self._planet_at_pos(event.pos())
        if old != self._hovered_planet:
            self._hud.update()
            if self._hovered_planet:
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def _on_click(self, event: QMouseEvent):
        planet = self._planet_at_pos(event.pos())
        if planet:
            self._open_planet(planet["id"])

    def _open_planet(self, pid: str):
        if pid in self._open_windows:
            try:
                self._open_windows[pid].close()
            except Exception:
                traceback.print_exc()

        if pid == "base_info":
            from modules.system.base_info_window import BaseInfoWindow
            win = BaseInfoWindow(self)
        elif pid == "activation":
            from modules.system.activation_window import ActivationWindow
            win = ActivationWindow(self)
        elif pid == "cloud":
            from modules.system.cloud_window import CloudWindow
            win = CloudWindow(self)
        elif pid == "logs":
            from modules.system.logs_window import LogsWindow
            win = LogsWindow(self)
        else:
            return

        self._open_windows[pid] = win
        win.show()

    def _tick(self):
        self._t += 0.04
        self._hud.update()

    def _paint_hud(self, event):
        QWidget.paintEvent(self._hud, event)
        painter = QPainter(self._hud)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self._hud.width(), self._hud.height()
        cx = self._get_orbit_center()

        # ── 轨道环 ──
        for p in ENGINE_PLANETS:
            r = p["orbit"]
            alpha = 20 if p == self._hovered_planet else 10
            c = p["color"]
            painter.setPen(QPen(QColor(c.red(), c.green(), c.blue(), alpha), 0.8))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(cx, r, r * 0.55)

        # ── 扫描弧线 ──
        scan_r = 380
        scan_a = self._t * 0.35 % (math.pi * 2)
        s_end = QPointF(cx.x() + math.cos(scan_a) * scan_r,
                        cx.y() + math.sin(scan_a) * scan_r * 0.55)
        s_start = QPointF(cx.x() + math.cos(scan_a + 0.5) * scan_r,
                          cx.y() + math.sin(scan_a + 0.5) * scan_r * 0.55)
        sg = QLinearGradient(s_start, s_end)
        sg.setColorAt(0, QColor(0, 0, 0, 0))
        sg.setColorAt(0.45, QColor(140, 155, 175, 10))
        sg.setColorAt(0.5, QColor(160, 175, 195, 35))
        sg.setColorAt(0.55, QColor(140, 155, 175, 10))
        sg.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(QPen(QBrush(sg), 1.5))
        painter.drawLine(s_start, s_end)

        # ── 中心工程舱核心 ──
        core_pulse = 0.5 + 0.5 * math.sin(self._t * 1.1)
        core_r = 22 + core_pulse * 8

        for layer in range(4, 0, -1):
            lr = core_r + layer * 14
            alpha = int((30 + layer * 15) * (1 - layer * 0.18))
            g = QRadialGradient(cx, lr)
            g.setColorAt(0, QColor(150, 165, 185, alpha))
            g.setColorAt(0.5, QColor(100, 115, 135, alpha // 3))
            g.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(g))
            painter.drawEllipse(cx, lr, lr)

        painter.setBrush(QBrush(QColor(200, 210, 225)))
        painter.drawEllipse(cx, core_r, core_r)

        painter.setPen(QPen(QColor(130, 145, 165, 160)))
        painter.setFont(QFont("Menlo", 8))
        painter.drawText(QRectF(cx.x() - 50, cx.y() + core_r + 14, 100, 16),
                         Qt.AlignCenter, "ENGINE CORE")

        # ── 小星球 ──
        for p in ENGINE_PLANETS:
            pp = self._get_planet_pos(p)
            c = p["color"]
            is_hovered = p == self._hovered_planet
            r = p["radius"]

            glow_r = r + (14 if is_hovered else 7)
            for layer in range(3, 0, -1):
                lr = glow_r + layer * 7
                a = int((45 - layer * 10) * (1.3 if is_hovered else 1.0))
                g = QRadialGradient(pp, lr)
                g.setColorAt(0, QColor(c.red(), c.green(), c.blue(), a))
                g.setColorAt(0.6, QColor(c.red(), c.green(), c.blue(), a // 4))
                g.setColorAt(1, QColor(0, 0, 0, 0))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(g))
                painter.drawEllipse(pp, lr, lr)

            body_g = QRadialGradient(
                QPointF(pp.x() - r * 0.25, pp.y() - r * 0.25), r * 1.2
            )
            body_g.setColorAt(0, QColor(
                min(c.red() + 50, 255),
                min(c.green() + 50, 255),
                min(c.blue() + 50, 255),
            ))
            body_g.setColorAt(0.6, c)
            body_g.setColorAt(1, QColor(
                max(c.red() - 35, 0),
                max(c.green() - 35, 0),
                max(c.blue() - 35, 0),
            ))
            painter.setBrush(QBrush(body_g))
            painter.setPen(QPen(QColor(c.red(), c.green(), c.blue(), 80), 1.5))
            painter.drawEllipse(pp, r, r)

            if is_hovered:
                ring_r = r + 5
                ring_g = QRadialGradient(pp, ring_r + 3)
                ring_g.setColorAt(0.7, QColor(0, 0, 0, 0))
                ring_g.setColorAt(0.8, QColor(c.red(), c.green(), c.blue(), 160))
                ring_g.setColorAt(1, QColor(0, 0, 0, 0))
                painter.setPen(QPen(QBrush(ring_g), 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(pp, ring_r, ring_r)

            painter.setPen(QPen(QColor(
                min(c.red() + 70, 255),
                min(c.green() + 70, 255),
                min(c.blue() + 70, 255),
                200 if is_hovered else 100
            )))
            painter.setFont(QFont("PingFang SC", 10, QFont.Bold if is_hovered else QFont.Normal))
            painter.drawText(QRectF(pp.x() - 55, pp.y() + r + 6, 110, 20),
                             Qt.AlignCenter, p["name"])

        painter.setPen(QPen(QColor(60, 70, 85, 80)))
        painter.setFont(QFont("Menlo", 9))
        painter.drawText(QRectF(0, 50, w, 18), Qt.AlignCenter, "ORBIT NAVIGATION")

        painter.end()