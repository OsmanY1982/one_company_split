# -*- coding: utf-8 -*-
"""密码工具箱"""
import random
import string
import hashlib
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QGroupBox, QComboBox, QSpinBox,
                             QSizePolicy)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt


class QRLabel(QLabel):
    """支持动态缩放的 QLabel，用于二维码显示"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap: QPixmap | None = None
        self.setAlignment(Qt.AlignCenter)

    def set_qpixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self._update_pixmap()

    def _update_pixmap(self) -> None:
        if self._pixmap is None:
            super().setPixmap(QPixmap())
            return
        size = self.size()
        if size.width() <= 0 or size.height() <= 0:
            return
        scaled = self._pixmap.scaled(
            size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        super().setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_pixmap()

class PasswordTools(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("密码工具箱")
        self.resize(700, 600)
        self.setStyleSheet("""
            QWidget { background-color: #f5f5f5; }
            QGroupBox { font-weight: bold; font-size: 14px; border: 2px solid #3182ce; 
                        border-radius: 8px; margin-top: 10px; padding: 10px;
                        background-color: white; }
            QPushButton { background-color: #3182ce; color: white; border: none;
                          border-radius: 6px; padding: 8px 20px; font-size: 14px; }
            QPushButton:hover { background-color: #2b6cb0; }
            QLineEdit { border: 1px solid #ccc; border-radius: 4px; padding: 6px; font-size: 14px; }
            QTextEdit { border: 1px solid #ccc; border-radius: 4px; font-size: 13px; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 标题
        title = QLabel("🔐 密码工具箱")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ── 随机密码生成 ──
        pwd_group = QGroupBox("🎲 随机密码生成")
        pwd_layout = QVBoxLayout(pwd_group)
        
        pwd_len_layout = QHBoxLayout()
        pwd_len_layout.addWidget(QLabel("密码长度:"))
        self.pwd_len_spin = QSpinBox()
        self.pwd_len_spin.setRange(6, 64)
        self.pwd_len_spin.setValue(16)
        pwd_len_layout.addWidget(self.pwd_len_spin)
        
        self.pwd_upper_cb = self._cb("大写字母 (A-Z)")
        self.pwd_lower_cb = self._cb("小写字母 (a-z)", True)
        self.pwd_digit_cb = self._cb("数字 (0-9)", True)
        self.pwd_special_cb = self._cb("特殊字符 (!@#$)")
        
        pwd_len_layout.addWidget(self.pwd_upper_cb)
        pwd_len_layout.addWidget(self.pwd_lower_cb)
        pwd_len_layout.addWidget(self.pwd_digit_cb)
        pwd_len_layout.addWidget(self.pwd_special_cb)
        pwd_layout.addLayout(pwd_len_layout)
        
        pwd_btn_layout = QHBoxLayout()
        gen_btn = QPushButton("🔄 生成密码")
        gen_btn.clicked.connect(self._gen_password)
        copy_btn = QPushButton("📋 复制")
        copy_btn.clicked.connect(self._copy_password)
        pwd_btn_layout.addWidget(gen_btn)
        pwd_btn_layout.addWidget(copy_btn)
        pwd_btn_layout.addStretch()
        pwd_layout.addLayout(pwd_btn_layout)
        
        self.pwd_result = QLineEdit()
        self.pwd_result.setFont(QFont("Menlo", 14))
        self.pwd_result.setReadOnly(True)
        pwd_layout.addWidget(self.pwd_result)
        layout.addWidget(pwd_group)

        # ── MD5加密 ──
        md5_group = QGroupBox("🔏 MD5加密")
        md5_layout = QVBoxLayout(md5_group)
        md5_input_layout = QHBoxLayout()
        md5_input_layout.addWidget(QLabel("输入:"))
        self.md5_input = QLineEdit()
        self.md5_input.setPlaceholderText("输入要加密的字符串...")
        self.md5_input.textChanged.connect(self._do_md5)
        md5_input_layout.addWidget(self.md5_input)
        md5_layout.addLayout(md5_input_layout)
        md5_layout.addWidget(QLabel("结果 (32位小写):"))
        self.md5_result = QLineEdit()
        self.md5_result.setFont(QFont("Menlo", 13))
        self.md5_result.setReadOnly(True)
        md5_copy_btn = QPushButton("📋 复制结果")
        md5_copy_btn.clicked.connect(self._copy_md5)
        md5_layout.addWidget(self.md5_result)
        md5_layout.addWidget(md5_copy_btn)
        layout.addWidget(md5_group)

        # ── 二维码生成 ──
        qr_group = QGroupBox("📱 二维码生成")
        qr_layout = QVBoxLayout(qr_group)
        qr_input_layout = QHBoxLayout()
        qr_input_layout.addWidget(QLabel("内容:"))
        self.qr_input = QLineEdit()
        self.qr_input.setPlaceholderText("输入二维码内容...")
        self.qr_input.returnPressed.connect(self._gen_qr)
        qr_input_layout.addWidget(self.qr_input)
        qr_btn = QPushButton("📱 生成二维码")
        qr_btn.clicked.connect(self._gen_qr)
        qr_input_layout.addWidget(qr_btn)
        qr_layout.addLayout(qr_input_layout)
        
        self.qr_label = QRLabel()
        self.qr_label.setMinimumSize(200, 200)
        self.qr_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        qr_layout.addWidget(self.qr_label)
        layout.addWidget(qr_group)

        layout.addStretch()

    def _cb(self, text, checked=False):
        from PyQt5.QtWidgets import QCheckBox
        cb = QCheckBox(text)
        cb.setChecked(checked)
        return cb

    def _gen_password(self):
        chars = ""
        if self.pwd_upper_cb.isChecked(): chars += string.ascii_uppercase
        if self.pwd_lower_cb.isChecked(): chars += string.ascii_lowercase
        if self.pwd_digit_cb.isChecked(): chars += string.digits
        if self.pwd_special_cb.isChecked(): chars += "!@#$%^&*"
        if not chars:
            self.pwd_result.setText("请至少选择一种字符类型")
            return
        length = self.pwd_len_spin.value()
        pwd = ''.join(random.choice(chars) for _ in range(length))
        self.pwd_result.setText(pwd)

    def _copy_password(self):
        text = self.pwd_result.text()
        if text:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(text)

    def _copy_md5(self):
        text = self.md5_result.text()
        if text:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(text)

    def _do_md5(self, text):
        if not text:
            self.md5_result.clear()
            return
        self.md5_result.setText(hashlib.md5(text.encode('utf-8')).hexdigest())

    def _gen_qr(self):
        text = self.qr_input.text().strip()
        if not text:
            return
        try:
            import qrcode
            from PyQt5.QtCore import QBuffer, QIODevice
            img = qrcode.make(text)
            buf = QBuffer()
            buf.open(QIODevice.WriteOnly)
            img.save(buf, "PNG")
            pix = QPixmap()
            pix.loadFromData(buf.data())
            self.qr_label.set_qpixmap(pix)
        except ImportError:
            self.qr_label.setText("需要安装 qrcode 库\npip install qrcode pillow")
