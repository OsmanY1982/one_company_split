# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QDialog, QDialogButtonBox, QLabel,
    QTextEdit, QMessageBox
)
from PyQt5.QtGui import QFont


class PasswordDialog(QDialog):
    def __init__(self, parent=None, title="输入密码", confirm=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(340)
        self.setStyleSheet
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        hint = QLabel("🔐 此文件已加密，请输入密码：" if not confirm else "🔐 设置加密密码：")
        hint.setStyleSheet("color: #718096; font-size: 12px;")
        layout.addWidget(hint)
        self._pwd = QLineEdit()
        self._pwd.setEchoMode(QLineEdit.Password)
        self._pwd.setPlaceholderText("密码")
        self._pwd.returnPressed.connect(self.accept)
        layout.addWidget(self._pwd)
        if confirm:
            self._pwd2 = QLineEdit()
            self._pwd2.setEchoMode(QLineEdit.Password)
            self._pwd2.setPlaceholderText("再次输入密码确认")
            layout.addWidget(self._pwd2)
        else:
            self._pwd2 = None
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("确定")
        btns.button(QDialogButtonBox.Cancel).setText("取消")
        btns.accepted.connect(self._check)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _check(self):
        if not self._pwd.text():
            QMessageBox.warning(self, "提示", "密码不能为空")
            return
        if self._pwd2 and self._pwd.text() != self._pwd2.text():
            QMessageBox.warning(self, "提示", "两次密码不一致")
            return
        self.accept()

    def password(self) -> str:
        return self._pwd.text()


class NoteTab(QWidget):
    def __init__(self, title="新文档", content="", filepath=None, encrypted=False, password=None):
        super().__init__()
        self.title     = title
        self.filepath  = filepath
        self.encrypted = encrypted
        self.password  = password
        self.modified  = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.editor = QTextEdit()
        self.editor.setFont(QFont("微软雅黑", 13))
        self.editor.setStyleSheet(
            "QTextEdit { border: 1px solid #ccc; border-radius: 4px; padding: 8px; }"
        )
        self.editor.textChanged.connect(self._on_changed)
        layout.addWidget(self.editor)
        self.modified = False

    def _on_changed(self):
        self.modified = True

    def get_content(self) -> str:
        return self.editor.toHtml()
