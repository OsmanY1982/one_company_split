# `iqra/modules/auth/select_mode_window.py`

> 路径：`iqra/modules/auth/select_mode_window.py` | 行数：62


---


```python
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from core.dark_theme import apply_dark_theme, BG_MAIN, BG_CARD, BG_INPUT, BTN_NORMAL, BTN_HOVER, BTN_PRESSED, TEXT_WHITE, TEXT_LIGHT, TEXT_MUTED, ACCENT, SUCCESS, WARNING, DANGER, BORDER, BORDER_LIGHT
# 导入账号密码登录窗口
from modules.auth.login_window import LoginWindow

class SelectModeWindow(QMainWindow):
    """本地/云端登录选择界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        apply_dark_theme(self)
        self.setWindowTitle("登录方式选择")
        self.setFixedSize(380, 280)  # 比登录界面稍窄一点，贴合原设计
        self.init_ui()

    def init_ui(self):
        # 核心布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(25)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setAlignment(Qt.AlignCenter)

        # 标题
        title = QLabel("请选择登录方式")
        title.setFont(QFont("PingFang SC", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 本地登录按钮
        local_btn = QPushButton("本地登录")
        local_btn.setFixedHeight(45)
        local_btn.setFont(QFont("PingFang SC", 12))
        local_btn.clicked.connect(self.go_local_login)
        layout.addWidget(local_btn)

        # 云端登录按钮（先做界面，后续龙虾可补逻辑）
        cloud_btn = QPushButton("云端登录")
        cloud_btn.setFixedHeight(45)
        cloud_btn.setFont(QFont("PingFang SC", 12))
        cloud_btn.clicked.connect(self.go_cloud_login)
        layout.addWidget(cloud_btn)

    def go_local_login(self):
        """本地登录：打开原账号密码登录界面"""
        self.close()
        self.login_win = LoginWindow()
        self.login_win.show()
        self.login_win.raise_()
        self.login_win.activateWindow()

    def go_cloud_login(self):
        """云端登录：先占位，后续龙虾可补对接逻辑"""
        QMessageBox.information(self, "提示", "云端登录功能暂未开发，即将上线！")
        # 若想临时跳本地登录，把下面注释打开
        # self.close()
        # self.login_win = LoginWindow()
        # self.login_win.show()

```
