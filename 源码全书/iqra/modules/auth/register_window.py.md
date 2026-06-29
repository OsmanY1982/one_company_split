# `iqra/modules/auth/register_window.py`

> 路径：`iqra/modules/auth/register_window.py` | 行数：172


---


```python
# -*- coding: utf-8 -*-
"""独立的注册窗口 —— 与登录窗口完全分开"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QCheckBox,
    QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from core.paths import CONFIG_DIR, BASE_DIR, DATA_DIR
from core.app_state import app_state
from modules.auth.auth_service import AuthService
from core.operation_log import log_action
import os
import datetime

LOGO_FILE = os.path.join(BASE_DIR, "opc_logo.ico")


class RegisterWindow(QMainWindow):
    def __init__(self, on_success=None, on_back=None, parent=None):
        super().__init__(parent)
        self.on_success = on_success      # 注册成功后做什么（通常关闭自己）
        self.on_back = on_back            # 返回登录
        if os.path.exists(LOGO_FILE):
            self.setWindowIcon(QIcon(LOGO_FILE))
        self.setWindowTitle("注册账号 - 一人公司管理系统")
        self.setFixedSize(440, 520)
        self.setStyleSheet("""
            QWidget { background-color: #ffffff; }
            QLineEdit { border: 1px solid #dcdcdc; border-radius: 4px; padding: 8px; }
            QPushButton { border: none; border-radius: 4px; padding: 10px 20px; }
        """)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        # 标题
        title = QLabel("注册账号")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet("color: #28a745;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("创建你的账号")
        subtitle.setFont(QFont("PingFang SC", 12))
        subtitle.setStyleSheet("color: #666;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addSpacing(5)
        layout.addWidget(subtitle)
        layout.addSpacing(15)

        # 账号输入
        self.account_input = QLineEdit()
        self.account_input.setPlaceholderText("账号（字母/数字，6位以上）")
        self.account_input.setMinimumHeight(36)
        layout.addWidget(self.account_input)

        # 密码输入
        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("密码（至少6位）")
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setMinimumHeight(36)
        layout.addWidget(self.pwd_input)

        # 确认密码
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("再次输入密码")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setMinimumHeight(36)
        layout.addWidget(self.confirm_input)

        # 记住密码（注册不保存密码，只是复选框占位）
        self.remember_checkbox = QCheckBox("记住密码")
        self.remember_checkbox.setStyleSheet("color: #666;")
        self.remember_checkbox.setChecked(True)
        layout.addWidget(self.remember_checkbox)

        # 注册按钮
        btn_reg = QPushButton("注册")
        btn_reg.setMinimumHeight(40)
        btn_reg.setFont(QFont("PingFang SC", 12, QFont.Bold))
        btn_reg.setStyleSheet(
            "background-color: #28a745; color: white;"
            "QPushButton:hover { background-color: #218838; }"
        )
        btn_reg.clicked.connect(self._do_register)
        layout.addWidget(btn_reg)

        # 返回登录
        btn_back = QPushButton("返回登录")
        btn_back.setMinimumHeight(36)
        btn_back.setStyleSheet(
            "QPushButton { background-color: transparent; color: #0078d4; border: none; text-decoration: underline; }"
        )
        btn_back.clicked.connect(self._go_back)
        layout.addWidget(btn_back)

        layout.addStretch()

    def _go_back(self):
        self.close()
        if self.on_back:
            self.on_back()

    def _do_register(self):
        account = self.account_input.text().strip()
        pwd = self.pwd_input.text().strip()
        confirm = self.confirm_input.text().strip()

        if not account or not pwd:
            QMessageBox.warning(self, "提示", "账号密码不能为空")
            return

        if len(account) < 4:
            QMessageBox.warning(self, "提示", "账号至少4位")
            return

        if len(pwd) < 6:
            QMessageBox.warning(self, "提示", "密码至少6位")
            return

        if pwd != confirm:
            QMessageBox.warning(self, "提示", "两次输入的密码不一致")
            self.confirm_input.clear()
            self.confirm_input.setFocus()
            return

        # 禁止注册保留账号
        if account.lower() in ["admin", "管理员", "system", "developer"]:
            QMessageBox.warning(self, "注册失败", "该账号名为系统保留，请选择其他账号名")
            return

        try:
            auth = AuthService()
            ok, msg = auth.register(account, pwd)

            if ok:
                try:
                    log_action(account, "注册", "login", "新用户注册")
                except Exception:
                    pass

                # ── 打通全模块：注册后自动创建本地会员记录 ──
                try:
                    from core.business_service import on_user_registered
                    on_user_registered(account)
                except Exception as e:
                    print(f"[register] on_user_registered failed (non-blocking): {e}")

                # 注册成功 → 弹出成功提示，然后关闭注册窗口，回到登录
                QMessageBox.information(
                    self, "注册成功",
                    f"账号 {account} 注册成功！\n\n请返回登录页面输入账号密码登录。"
                )

                # 关闭注册窗口，返回登录
                self.close()
                if self.on_success:
                    self.on_success()
            else:
                QMessageBox.warning(self, "注册失败", msg)

        except Exception as e:
            QMessageBox.critical(self, "注册异常", f"注册过程出错：{str(e)}")
            print(f"注册异常: {e}")

```
