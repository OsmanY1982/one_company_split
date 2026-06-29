# `core/modules/data_center/data_window.py`

> 路径：`core/modules/data_center/data_window.py` | 行数：216


---


```python
"""
数据中心 → 星云观测站 · NEBULA OBSERVATORY
小星球导航模式：3颗小星球环绕轨道
"""
import traceback
import os, sqlite3, csv, math
from datetime import datetime
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
from core.planet_painter import PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line
from core.ui_components import SectionTitle, Subtitle
from core.light_tool_theme import LIGHT_TOOL_STYLE

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

# ═══════ 3颗星球 — 使用 planet_painter 真实纹理 ═══════
# 窗口 900×620，中心约 (450, 341)，轨道均匀排列
NEBULA_PLANETS = [
    {"id": "report",   "name": "数据报表", "style": "neptune", "orbit": 145, "size": 48},
    {"id": "bi",       "name": "数据大屏", "style": "earth",   "orbit": 215, "size": 50},
    {"id": "industry", "name": "行业报告", "style": "mars",    "orbit": 280, "size": 52},
]

class DataWindow(QMainWindow):
    """星云观测站 · NEBULA OBSERVATORY — 小星球导航"""

    def __init__(self, parent=None, role="admin"):
        super().__init__(parent)
        self._role = role
        self.setWindowTitle("一人公司 — 数据中心 · NEBULA OBSERVATORY")
        self.setMinimumSize(900, 620)
        self._t = 0
        self._hovered_planet = None
        self._open_windows = {}

        # 星空背景
        self.setStyleSheet(LIGHT_TOOL_STYLE)
        self._cosmic = CosmicBackground()
        self.setCentralWidget(self._cosmic)

        # HUD 层 — 必须是窗口直接子控件，不是 _cosmic 子控件
        # 否则 _cosmic 的 WA_TransparentForMouseEvents 会在 macOS 26.x 拦截所有鼠标事件
        self._hud = QWidget(self)
        self._hud.setAttribute(Qt.WA_TranslucentBackground)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._hud.setMouseTracking(True)
        self._hud.mouseMoveEvent = self._on_mouse_move
        self._hud.mousePressEvent = self._on_click

        self._build_ui()

        # 确保 HUD 在星空背景之上
        self._hud.raise_()

        # 动画
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

        title = SectionTitle("数据中心")
        title.setStyleSheet("color: #b0c4de; font-size: 22px; font-weight: 800; letter-spacing: 6px; background: transparent;")
        hl.addWidget(title, alignment=Qt.AlignCenter)

        subtitle = Subtitle("NEBULA OBSERVATORY · 点击星球进入模块")
        subtitle.setStyleSheet("color: #5a7d9a; font-size: 10px; letter-spacing: 2px; background: transparent;")
        hl.addWidget(subtitle, alignment=Qt.AlignCenter)

        # 辉光线
        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(74,144,217,30),
                stop:0.5 rgba(126,184,218,100),
                stop:0.7 rgba(74,144,217,30), stop:1 transparent);
            border: none;
        """)
        hl.addWidget(line)

        # 底部提示
        hint = QLabel("点击轨道星球进入对应模块")
        hint.setStyleSheet("color: #4a5d6d; font-size: 10px; background: transparent;")
        hint.setAlignment(Qt.AlignCenter)
        hint.setGeometry(0, self.height() - 30, self.width(), 24)

    def _get_orbit_center(self) -> QPointF:
        w = self._hud.width()
        h = self._hud.height()
        return QPointF(w * 0.5, h * 0.55)

    def _get_planet_pos(self, planet: dict) -> QPointF:
        cx = self._get_orbit_center()
        idx = NEBULA_PLANETS.index(planet)
        phase = idx * math.pi * 0.75
        angle = phase + self._t * (0.12 + idx * 0.06)
        px = cx.x() + math.cos(angle) * planet["orbit"]
        py = cx.y() + math.sin(angle) * planet["orbit"]
        return QPointF(px, py)

    def _planet_at_pos(self, pos: QPointF):
        for p in NEBULA_PLANETS:
            pp = self._get_planet_pos(p)
            dist = math.hypot(pos.x() - pp.x(), pos.y() - pp.y())
            if dist <= p["size"] + 14:
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

        if pid == "report":
            from core.modules.data_center.report_window import ReportWindow
            win = ReportWindow(self)
        elif pid == "bi":
            from core.modules.data_center.bi_window import BIWindow
            win = BIWindow(self)
        elif pid == "industry":
            from core.modules.industry.industry_window import IndustryWindow
            win = IndustryWindow(self)
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

        # ── 轨道线（使用 planet_painter 轨道） ──
        for p in NEBULA_PLANETS:
            paint_orbit(painter, cx, p["orbit"])

        # ── 扫描弧线 ──
        scan_r = 235
        scan_a = self._t * 0.4 % (math.pi * 2)
        s_end = QPointF(cx.x() + math.cos(scan_a) * scan_r,
                        cx.y() + math.sin(scan_a) * scan_r)
        s_start = QPointF(cx.x() + math.cos(scan_a + 0.5) * scan_r,
                          cx.y() + math.sin(scan_a + 0.5) * scan_r)
        sg = QLinearGradient(s_start, s_end)
        sg.setColorAt(0, QColor(0, 0, 0, 0))
        sg.setColorAt(0.45, QColor(74, 144, 217, 10))
        sg.setColorAt(0.5, QColor(126, 184, 218, 35))
        sg.setColorAt(0.55, QColor(74, 144, 217, 10))
        sg.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(QPen(QBrush(sg), 1.5))
        painter.drawLine(s_start, s_end)

        # ── 星球（使用 planet_painter） ──
        for p in NEBULA_PLANETS:
            pp = self._get_planet_pos(p)
            style = PLANET_STYLES.get(p["style"], PLANET_STYLES["neptune"])
            is_hovered = (p == self._hovered_planet)
            paint_planet(painter, pp, p["size"], style,
                         hovered=is_hovered, label=p["name"], font_size=10)

            # 能量线
            if is_hovered:
                paint_energy_line(painter, cx, pp)

        # ── 顶部标签 ──
        painter.setPen(QPen(QColor(42, 58, 74, 80)))
        painter.setFont(QFont("Menlo", 9))
        painter.drawText(QRectF(0, 50, w, 18), Qt.AlignCenter, "ORBIT NAVIGATION")

        painter.end()
```
