# `core/modules/auth/change_password_dialog.py`

> 路径：`core/modules/auth/change_password_dialog.py` | 行数：158


---


```python
from __future__ import annotations
from typing import Any

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox,
    QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from core.paths import CONFIG_DIR, BASE_DIR, DATA_DIR
from core.app_state import AppState
import os
import json

LOGO_FILE = os.path.join(BASE_DIR, "opc_logo.ico")


class ChangePasswordWindow(QDialog):
    """修改密码弹窗"""
    def __init__(self, username: str | None = None, on_success: Any = None, parent: Any = None) -> None:
        super().__init__(parent)
        self.username = username
        self.on_success = on_success
        if os.path.exists(LOGO_FILE):
            self.setWindowIcon(QIcon(LOGO_FILE))
        self.setWindowTitle("修改密码 - 一人公司管理系统")
        self.setFixedSize(420, 420)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("修改密码")
        title.setObjectName("title")
        title.setFont(QFont("PingFang SC", 15, QFont.Bold))
        layout.addWidget(title)

        hint = QLabel(f"账号：{self.username}")
        hint.setStyleSheet("color: #64748b; font-size: 12px;")
        layout.addWidget(hint)

        # 原密码
        layout.addWidget(QLabel("原密码："))
        old_row = QHBoxLayout()
        old_row.setSpacing(0)
        self.old_input = QLineEdit()
        self.old_input.setPlaceholderText("请输入原密码")
        self.old_input.setEchoMode(QLineEdit.Password)
        old_row.addWidget(self.old_input)
        eye1 = QPushButton("\U0001f441")
        eye1.setObjectName("eye")
        eye1.setFixedSize(40, 40)
        eye1.setCheckable(True)
        eye1.toggled.connect(lambda on: self.old_input.setEchoMode(
            QLineEdit.Normal if on else QLineEdit.Password))
        old_row.addWidget(eye1)
        layout.addLayout(old_row)

        # 新密码
        layout.addWidget(QLabel("新密码（至少6位）："))
        new_row = QHBoxLayout()
        new_row.setSpacing(0)
        self.new_input = QLineEdit()
        self.new_input.setPlaceholderText("请输入新密码")
        self.new_input.setEchoMode(QLineEdit.Password)
        new_row.addWidget(self.new_input)
        eye2 = QPushButton("\U0001f441")
        eye2.setObjectName("eye")
        eye2.setFixedSize(40, 40)
        eye2.setCheckable(True)
        eye2.toggled.connect(lambda on: self.new_input.setEchoMode(
            QLineEdit.Normal if on else QLineEdit.Password))
        new_row.addWidget(eye2)
        layout.addLayout(new_row)

        # 确认新密码
        layout.addWidget(QLabel("确认新密码："))
        confirm_row = QHBoxLayout()
        confirm_row.setSpacing(0)
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("再次输入新密码")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.returnPressed.connect(self._do_change)
        confirm_row.addWidget(self.confirm_input)
        eye3 = QPushButton("\U0001f441")
        eye3.setObjectName("eye")
        eye3.setFixedSize(40, 40)
        eye3.setCheckable(True)
        eye3.toggled.connect(lambda on: self.confirm_input.setEchoMode(
            QLineEdit.Normal if on else QLineEdit.Password))
        confirm_row.addWidget(eye3)
        layout.addLayout(confirm_row)

        # 按钮
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("取消")
        btn_cancel.setObjectName("cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_ok = QPushButton("确认修改")
        btn_ok.clicked.connect(self._do_change)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _do_change(self) -> None:
        old_pwd = self.old_input.text()
        new_pwd = self.new_input.text()
        confirm_pwd = self.confirm_input.text()

        from core.modules.auth.auth_service import AuthService
        auth = AuthService()
        ok, msg = auth.modify_password(self.username, old_pwd, new_pwd, confirm_pwd)

        if ok:
            QMessageBox.information(self, "成功", msg)
            try:
                save_file = os.path.join(CONFIG_DIR, "remember.json")
                if os.path.exists(save_file):
                    with open(save_file, encoding='utf-8') as f:
                        data = json.load(f)
                    data['password'] = ''
                    with open(save_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            self.accept()
            self._logout_after_change()
        else:
            QMessageBox.warning(self, "修改失败", msg)
            if "原密码" in msg:
                self.old_input.clear()
                self.old_input.setFocus()
            elif "不一致" in msg:
                self.confirm_input.clear()
                self.confirm_input.setFocus()

    def _logout_after_change(self) -> None:
        try:
            app_state = AppState()
            from core.modules.auth.login_window import LoginWindow
            app_state.logout()
            if app_state._current_dashboard:
                app_state._current_dashboard.close()
                app_state._current_dashboard = None
            win = LoginWindow()
            win.show()
            win.raise_()
        except Exception as e:
            print(f"退出登录失败: {e}")


# 别名：兼容 dashboard_window.py 的导入
ChangePasswordDialog = ChangePasswordWindow

```
