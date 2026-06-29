# `core/modules/personnel/distribution_window/_stat_card.py`

> 路径：`core/modules/personnel/distribution_window/_stat_card.py` | 行数：43


---


```python
"""
GoldStatCard — 金色统计卡片小控件
"""
from PyQt5.QtWidgets import QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QPainter, QColor, QLinearGradient, QPen, QBrush, QFont, QPainterPath,
)


class GoldStatCard(QFrame):
    def __init__(self, title, color_start, color_end, parent=None):
        super().__init__(parent)
        self._title = title
        self._value_str = "0"
        self._color_start = QColor(*color_start)
        self._color_end = QColor(*color_end)
        self.setFixedSize(180, 80)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def set_value(self, v):
        self._value_str = str(v)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 12, 12)
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0, self._color_start)
        grad.setColorAt(1, self._color_end)
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(QColor(210, 160, 40, 60), 1))
        painter.drawPath(path)
        painter.setPen(QColor(210, 180, 120, 180))
        painter.setFont(QFont("sans-serif", 10))
        painter.drawText(14, 24, self._title)
        painter.setPen(QColor(255, 230, 180))
        painter.setFont(QFont("sans-serif", 22, QFont.Bold))
        painter.drawText(14, 56, self._value_str)
        painter.end()

```
