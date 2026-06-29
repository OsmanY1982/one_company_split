# -*- coding: utf-8 -*-
"""
太阳系天文馆 · 主窗口 — SolarSystemWindow
"""
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer

try:
    from cosmic import CosmicBackground
except ImportError:
    try:
        from cosmic import CosmicBackground
    except ImportError:
        from core.cosmic import CosmicBackground

from ._hud import SolarSystemHUD
from core.modules.astronomy.solar_system.data import total_count


class SolarSystemWindow(QWidget):
    """太阳系天文馆 — 可缩放交互窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("太阳系天文馆")
        self.setMinimumSize(700, 500)
        self.resize(1000, 750)

        # 底层宇宙背景
        self._bg = CosmicBackground(self)
        self._bg.setGeometry(0, 0, self.width(), self.height())

        # 太阳系 HUD
        self._hud = SolarSystemHUD(self)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._hud.raise_()

        # 底部状态标签
        count = total_count()
        self._status = QLabel(f"太阳系 · 已命名天体 {count}", self)
        self._status.setStyleSheet(
            "color: #7766aa; background: transparent; font-size: 11px;"
            " font-family: 'PingFang SC';"
        )
        self._status.setAlignment(Qt.AlignCenter)
        self._status.setGeometry(0, self.height() - 24, self.width(), 20)

        # 提示标签
        self._hint = QLabel("滚轮缩放 · 拖拽平移 · 悬停查看", self)
        self._hint.setStyleSheet(
            "color: #554477; background: transparent; font-size: 10px;"
            " font-family: 'PingFang SC';"
        )
        self._hint.setAlignment(Qt.AlignRight)
        self._hint.setGeometry(self.width() - 260, self.height() - 24, 250, 20)

        # 星谱跳转按钮
        self._catalog_btn = QPushButton("📖 打开星谱", self)
        self._catalog_btn.setStyleSheet(
            "QPushButton {"
            " color: #7799cc; background: rgba(20, 35, 65, 0.85);"
            " border: 1px solid rgba(60, 130, 200, 0.3); border-radius: 6px;"
            " padding: 3px 12px; font-size: 11px; font-family: 'PingFang SC';"
            " }"
            " QPushButton:hover {"
            " background: rgba(40, 70, 130, 0.9); color: #00ccff;"
            " border-color: rgba(0, 200, 255, 0.5);"
            " }"
        )
        self._catalog_btn.clicked.connect(self._open_catalog)
        self._catalog_btn.setGeometry(8, self.height() - 26, 110, 24)

        # 缩放相关
        self._speed = 1.0
        self._build_zoom_controls()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Equal:
            self._speed = min(self._speed * 1.5, 100.0)
            self._show_speed_hint()
            self._sync_speed_ui()
        elif event.key() == Qt.Key_Minus:
            self._speed = max(self._speed / 1.5, 0.05)
            self._show_speed_hint()
            self._sync_speed_ui()
        else:
            super().keyPressEvent(event)

    def _show_speed_hint(self):
        from PyQt5.QtWidgets import QLabel
        from PyQt5.QtCore import QTimer
        if hasattr(self, '_speed_label') and self._speed_label:
            self._speed_label.setText(f"⏱ {self._speed:.1f}x")
        else:
            self._speed_label = QLabel(f"⏱ {self._speed:.1f}x", self)
            self._speed_label.setStyleSheet(
                "background:rgba(0,0,0,180);color:#fff;font-size:14px;padding:4px 10px;border-radius:6px;"
            )
            self._speed_label.move(12, 12)
            self._speed_label.show()
        QTimer.singleShot(1500, self._hide_speed_hint)

    def _hide_speed_hint(self):
        if hasattr(self, '_speed_label') and self._speed_label:
            self._speed_label.hide()

    def _build_zoom_controls(self):
        """构建公转速度控件：−/+ 按钮和滑动条"""
        from PyQt5.QtWidgets import QSlider

        btn_style = (
            "QPushButton {"
            " color: #7799cc; background: rgba(20, 35, 65, 0.85);"
            " border: 1px solid rgba(60, 130, 200, 0.3); border-radius: 6px;"
            " padding: 2px 6px; font-size: 13px; font-family: 'PingFang SC';"
            " }"
            " QPushButton:hover {"
            " background: rgba(40, 70, 130, 0.9); color: #00ccff;"
            " border-color: rgba(0, 200, 255, 0.5);"
            " }"
        )

        self._speed_down_btn = QPushButton("−", self)
        self._speed_down_btn.setStyleSheet(btn_style)
        self._speed_down_btn.setFixedSize(28, 28)
        self._speed_down_btn.clicked.connect(self._speed_down)

        self._speed_up_btn = QPushButton("+", self)
        self._speed_up_btn.setStyleSheet(btn_style)
        self._speed_up_btn.setFixedSize(28, 28)
        self._speed_up_btn.clicked.connect(self._speed_up)

        self._speed_slider = QSlider(Qt.Horizontal, self)
        self._speed_slider.setRange(5, 10000)
        self._speed_slider.setValue(int(self._speed * 100))
        self._speed_slider.setFixedWidth(100)
        self._speed_slider.valueChanged.connect(self._on_speed_slider)

        self._speed_label = QLabel(f"{self._speed:.1f}x", self)
        self._speed_label.setStyleSheet(
            "color: #7799cc; background: transparent; font-size: 10px;"
            " font-family: 'PingFang SC';"
        )
        self._speed_label.setAlignment(Qt.AlignCenter)
        self._speed_label.setFixedWidth(40)

        self._reposition_zoom_controls()

    def _speed_up(self):
        self._speed = min(self._speed * 1.5, 100.0)
        self._sync_speed_ui()

    def _speed_down(self):
        self._speed = max(self._speed / 1.5, 0.05)
        self._sync_speed_ui()

    def _on_speed_slider(self, val):
        self._speed = val / 100.0
        self._speed_label.setText(f"{self._speed:.1f}x")

    def _sync_speed_ui(self):
        val = int(self._speed * 100)
        self._speed_slider.blockSignals(True)
        self._speed_slider.setValue(val)
        self._speed_slider.blockSignals(False)
        self._speed_label.setText(f"{self._speed:.1f}x")

    def _reposition_zoom_controls(self):
        w = self.width()
        y = self.height() - 42
        self._speed_down_btn.move(w - 200, y)
        self._speed_slider.move(w - 168, y + 4)
        self._speed_up_btn.move(w - 62, y)
        self._speed_label.move(w - 30, y + 2)

    def _open_catalog(self):
        from core.modules.astronomy.star_catalog.catalog import StarCatalogWindow
        self._catalog_win = StarCatalogWindow(self)
        self._catalog_win.show()
        self.hide()

    def resizeEvent(self, event):
        # ── 窗口调整 ──
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        if hasattr(self, '_bg'):
            self._bg.setGeometry(0, 0, w, h)
        if hasattr(self, '_hud'):
            self._hud.setGeometry(0, 0, w, h)
        if hasattr(self, '_status'):
            self._status.setGeometry(0, h - 24, w, 20)
        if hasattr(self, '_hint'):
            self._hint.setGeometry(w - 260, h - 24, 250, 20)
        if hasattr(self, '_catalog_btn'):
            self._catalog_btn.setGeometry(8, h - 26, 110, 24)
        if hasattr(self, '_speed_down_btn'):
            self._reposition_zoom_controls()
