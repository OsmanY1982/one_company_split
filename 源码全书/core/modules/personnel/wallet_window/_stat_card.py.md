# `core/modules/personnel/wallet_window/_stat_card.py`

> 路径：`core/modules/personnel/wallet_window/_stat_card.py` | 行数：54


---


```python
# -*- coding: utf-8 -*-
"""
StatCard — 统计卡片控件（浅色主题）
"""
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtGui import QFont

CARD_BG = "#ffffff"
TEXT_SECONDARY = "#6b7280"
BORDER_ACCENT = "#3182ce"
BORDER_SUCCESS = "#38a169"
BORDER_WARNING = "#d69e2e"
BORDER_DANGER = "#e53e3e"
BORDER_SECONDARY = "#a0aec0"


class StatCard(QFrame):
    """统计卡片 — 白底左侧色条"""

    _BORDER_MAP = {
        "accent": BORDER_ACCENT, "success": BORDER_SUCCESS,
        "warning": BORDER_WARNING, "danger": BORDER_DANGER,
        "secondary": BORDER_SECONDARY,
        "#3182ce": BORDER_ACCENT, "#38a169": BORDER_SUCCESS,
        "#d69e2e": BORDER_WARNING, "#e53e3e": BORDER_DANGER,
        "#a0aec0": BORDER_SECONDARY, "#6b7280": BORDER_SECONDARY,
    }

    def __init__(self, title, value, color=None, parent=None):
        if color is None:
            color = BORDER_ACCENT
        border_color = self._BORDER_MAP.get(color, color)
        super().__init__(parent)
        self._border_color = border_color
        self.setStyleSheet(
            f"background-color: {CARD_BG}; border-left: 4px solid {border_color}; "
            "border-radius: 6px; padding: 12px;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        lbl_title.setFont(QFont("PingFang SC", 11))
        layout.addWidget(lbl_title)
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(
            f"color: {border_color}; font-size: 22px; font-weight: bold;"
        )
        self.lbl_value.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.lbl_value)
        self.setMinimumWidth(180)

    def set_value(self, value):
        self.lbl_value.setText(value)

```
