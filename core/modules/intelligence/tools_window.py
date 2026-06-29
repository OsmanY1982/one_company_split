# -*- coding: utf-8 -*-
"""
工具箱 · NEURAL NEXUS（星球导航模式）
4颗星球环绕，点击打开：编辑器 / 保险箱 / 计算器 / 扫码工具
"""
import os, math
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QFrame, QDialog,
    QLineEdit, QPushButton, QGridLayout, QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter

from core.planet_painter import (
    PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line,
)
from core.ui_components import SectionTitle, Subtitle
from core.light_tool_theme import LIGHT_TOOL_STYLE

# ═══════ 4颗工具星球 ═══════
PLANETS = [
    {"id": "editor",     "name": "编辑器",   "style": "mercury", "orbit": 130, "size": 46},
    {"id": "vault",      "name": "保险箱",   "style": "saturn",  "orbit": 210, "size": 48},
    {"id": "calculator", "name": "计算器",   "style": "moon",    "orbit": 290, "size": 46},
    {"id": "scanner",    "name": "扫码工具", "style": "uranus",  "orbit": 370, "size": 46},
]

# ═══════ 计算器内嵌 ═══════
CALC_DISPLAY = """
    QLineEdit {
        background: rgba(14,8,26,230);
        color: #ddaaff;
        border: 1px solid rgba(170,80,255,40);
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 24px;
        font-weight: 700;
        font-family: 'Menlo', monospace;
    }
"""
CALC_BTN = """
    QPushButton {
        background: rgba(22,14,38,220);
        color: #ccbbdd;
        border: 1px solid rgba(170,80,255,35);
        border-radius: 10px;
        padding: 10px;
        font-size: 16px;
        font-weight: 700;
    }
    QPushButton:hover {
        background: rgba(36,22,56,235);
        border: 1px solid rgba(200,100,255,80);
    }
    QPushButton:pressed {
        background: rgba(50,30,70,220);
    }
"""


class CalcDialog(QDialog):
    """计算器 · NEURAL"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("计算器 · NEURAL")
        self.setMinimumSize(340, 440)
        self.setStyleSheet("background: rgba(10,5,20,240);")
        self._expression = ""
        self._build_ui()

    def _build_ui(self):
        l = QVBoxLayout(self)
        l.setSpacing(10)
        l.setContentsMargins(16, 12, 16, 12)

        self._display = QLineEdit()
        self._display.setReadOnly(True)
        self._display.setAlignment(Qt.AlignRight)
        self._display.setStyleSheet(CALC_DISPLAY)
        self._display.setText("0")
        l.addWidget(self._display)

        grid = QGridLayout()
        grid.setSpacing(6)

        buttons = [
            ("C", 0, 0, self._clear), ("⌫", 0, 1, self._backspace),
            ("%", 0, 2, self._op), ("÷", 0, 3, self._op),
            ("7", 1, 0, self._digit), ("8", 1, 1, self._digit), ("9", 1, 2, self._digit),
            ("×", 1, 3, self._op),
            ("4", 2, 0, self._digit), ("5", 2, 1, self._digit), ("6", 2, 2, self._digit),
            ("−", 2, 3, self._op),
            ("1", 3, 0, self._digit), ("2", 3, 1, self._digit), ("3", 3, 2, self._digit),
            ("+", 3, 3, self._op),
            ("±", 4, 0, self._negate), ("0", 4, 1, self._digit), (".", 4, 2, self._dot),
            ("=", 4, 3, self._eval),
        ]
        for text, r, c, handler in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(CALC_BTN)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(handler)
            grid.addWidget(btn, r, c)

        l.addLayout(grid)

    def _digit(self):
        b = self.sender()
        self._expression += b.text()
        self._display.setText(self._expression)

    def _op(self):
        b = self.sender()
        op_map = {"×": "*", "÷": "/", "−": "-"}
        self._expression += op_map.get(b.text(), b.text())
        self._display.setText(self._expression)

    def _dot(self):
        self._expression += "."
        self._display.setText(self._expression)

    def _negate(self):
        if self._expression:
            self._expression = f"-({self._expression})" if self._expression[0] != "-" else self._expression[1:]
            self._display.setText(self._expression)

    def _clear(self):
        self._expression = ""
        self._display.setText("0")

    def _backspace(self):
        self._expression = self._expression[:-1]
        self._display.setText(self._expression or "0")

    def _eval(self):
        try:
            result = eval(self._expression, {"__builtins__": {}})
            if isinstance(result, float):
                result = round(result, 10)
                if result == int(result):
                    result = int(result)
            self._display.setText(str(result))
            self._expression = str(result)
        except Exception:
            QMessageBox.warning(self, "计算错误", "表达式无效")
            self._clear()


# ═══════ 星球导航 HUD ═══════
class NavigationHUD(QWidget):
    """工具箱星球导航叠加层"""

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
        n = len(PLANETS)
        for i, p in enumerate(PLANETS):
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

        # 轨道线
        for planet in PLANETS:
            paint_orbit(p, w2, planet["orbit"])

        # 能量连接线
        for _, pos in self._planet_positions():
            paint_energy_line(p, w2, pos)

        # 行星
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


# ═══════ 主窗口 ═══════
class ToolsWindow(QMainWindow):
    """工具箱 · NEURAL NEXUS — 4颗工具星球"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("一人公司 — 工具箱 · NEURAL NEXUS")
        self.setMinimumSize(1200, 850)
        self.resize(1200, 850)
        self.setStyleSheet(LIGHT_TOOL_STYLE)
        self._build_ui()

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
        title = SectionTitle("工具箱", parent=header)
        title.setStyleSheet("font-size: 24px; font-weight: 800; letter-spacing: 8px;")
        title.setAlignment(Qt.AlignCenter)
        hl.addWidget(title)
        subtitle = Subtitle("NEURAL NEXUS · 4颗工具星球", parent=header)
        subtitle.setStyleSheet("font-size: 11px; letter-spacing: 3px;")
        subtitle.setAlignment(Qt.AlignCenter)
        hl.addWidget(subtitle)

        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(170,80,255,50),
                stop:0.5 rgba(200,120,255,120),
                stop:0.7 rgba(170,80,255,50), stop:1 transparent);
            border: none;
        """)
        hl.addWidget(line)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_hud'):
            self._hud.setGeometry(0, 0, self.width(), self.height())

    def _on_planet_clicked(self, planet_id):
        if planet_id == "editor":
            from core.modules.intelligence.editor_window import EditorWindow
            dlg = EditorWindow(self)
            dlg.exec_()
        elif planet_id == "vault":
            from core.modules.intelligence.vault_window import VaultWindow
            dlg = VaultWindow(self)
            dlg.exec_()
        elif planet_id == "calculator":
            dlg = CalcDialog(self)
            dlg.exec_()
        elif planet_id == "scanner":
            from core.modules.intelligence.scan_window import ScanWindow
            dlg = ScanWindow(self)
            dlg.exec_()
