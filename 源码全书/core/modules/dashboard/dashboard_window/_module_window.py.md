# `core/modules/dashboard/dashboard_window/_module_window.py`

> 路径：`core/modules/dashboard/dashboard_window/_module_window.py` | 行数：82


---


```python
"""
子模块弹窗 — 近景星球视图（_ModuleWindow 类）
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

try:
    from planet_painter import PLANET_STYLES
except ImportError:
    try:
        from planet_painter import PLANET_STYLES
    except ImportError:
        from core.planet_painter import PLANET_STYLES


class _ModuleWindow(QMainWindow):
    """模块弹窗 — 近景星球视图"""

    def __init__(self, planet: dict, parent=None):
        super().__init__(parent)
        self._planet = planet
        self.setWindowTitle(f"一人公司 — {planet['name']}")
        self.setMinimumSize(600, 440)

        # 从 style 推导主题色
        style = PLANET_STYLES.get(planet.get("style", "neptune"), PLANET_STYLES["neptune"])
        surface = style.get("surface", [("0.5", "#4488ff")])
        main_color = surface[len(surface)//2][1]
        c = QColor(main_color)
        color_name = c.name()

        bg = QWidget()
        bg.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(4,8,20,240), stop:1 rgba(8,16,36,240));
            border: 2px solid rgba({c.red()},{c.green()},{c.blue()},60);
            border-radius: 14px;
        """)
        self.setCentralWidget(bg)

        layout = QVBoxLayout(bg)
        layout.setSpacing(10)
        layout.setContentsMargins(30, 24, 30, 24)

        head = QHBoxLayout()
        icon = QLabel("●")
        icon.setStyleSheet(f"color: {color_name}; font-size: 20px; background:transparent;")
        head.addWidget(icon)

        name = QLabel(planet["name"])
        name.setStyleSheet(f"color: #ddeeff; font-size: 20px; font-weight: 700; letter-spacing: 4px; background:transparent;")
        head.addWidget(name)
        head.addStretch()
        layout.addLayout(head)

        body = QLabel(f"「{planet['name']}」模块\n\n功能开发中...\n\n通过 Agent 对话或语音来操作此模块。")
        body.setAlignment(Qt.AlignCenter)
        body.setWordWrap(True)
        body.setStyleSheet("color: #667788; font-size: 14px; background: transparent; line-height: 1.8;")
        layout.addWidget(body, 1)

        close_btn = QPushButton("关闭")
        close_btn.setFixedSize(100, 34)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba({c.red()},{c.green()},{c.blue()},30);
                color: {color_name};
                border: 1px solid rgba({c.red()},{c.green()},{c.blue()},50);
                border-radius: 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: rgba({c.red()},{c.green()},{c.blue()},60);
            }}
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

```
