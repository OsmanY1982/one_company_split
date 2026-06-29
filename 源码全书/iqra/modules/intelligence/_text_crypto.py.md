# `iqra/modules/intelligence/_text_crypto.py`

> 路径：`iqra/modules/intelligence/_text_crypto.py` | 行数：111


---


```python
# -*- coding: utf-8 -*-
"""文本编辑器：加密工具、密码对话框、标签页组件、路径常量、导入块。"""
from core.paths import DATA_DIR

import os, json, base64, hashlib
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QDialog, QLineEdit, QDialogButtonBox, QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

NOTES_DIR  = os.path.join(DATA_DIR, "notes")
INDEX_FILE = os.path.join(DATA_DIR, "notes/index.json")
ENC_MAGIC  = b"OPC_ENC_V1:"   # 加密文件头标识

# ── 加密/解密 ──
def _derive_key(password: str) -> bytes:
    salt = b"OPC_TextEditor_Salt_2026"
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)

def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

def encrypt_text(text: str, password: str) -> bytes:
    key  = _derive_key(password)
    enc  = _xor(text.encode('utf-8'), key)
    return ENC_MAGIC + base64.b64encode(enc)

def decrypt_text(data: bytes, password: str) -> str:
    if not data.startswith(ENC_MAGIC):
        raise ValueError("不是加密文件")
    enc  = base64.b64decode(data[len(ENC_MAGIC):])
    key  = _derive_key(password)
    return _xor(enc, key).decode('utf-8')

def is_encrypted(filepath: str) -> bool:
    try:
        with open(filepath, 'rb') as f:
            return f.read(len(ENC_MAGIC)) == ENC_MAGIC
    except Exception: return False


# ── 密码对话框 ──
class PasswordDialog(QDialog):
    def __init__(self, parent=None, title="输入密码", confirm=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(340)
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


# ── 单个标签页 ──
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

```
