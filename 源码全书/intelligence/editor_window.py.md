# `intelligence/editor_window.py`

> 路径：`intelligence/editor_window.py` | 行数：304


---


```python
"""
文本编辑器 · NEURAL — 独立子窗口
从 tools_window.py 拆分，提供加密/明文文本编辑能力 + Markdown 实时预览
"""
import os, hashlib, base64, re
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QFileDialog, QInputDialog, QMessageBox, QLineEdit,
    QSplitter, QTextBrowser, QCheckBox,
)
from PyQt5.QtCore import Qt
from core.theme import CYBER_PURPLE

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

# ═══════ QSS 主题 ═══════
BTN_ACTIVE = """
    QPushButton {
        background: rgba(180,100,240,70); color: #ffffff;
        border: 1px solid rgba(200,120,255,100); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
"""
PREVIEW_STYLE = """
    QTextBrowser {
        background: rgba(8,4,16,230); color: #ccbbdd;
        border: 1px solid rgba(170,80,255,35); border-radius: 10px;
        padding: 12px; font-size: 13px; line-height: 1.7;
    }
"""


# ═══════ 加解密函数（自包含副本） ═══════
def _derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)

def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

def vault_encrypt(plaintext: str, password: str) -> str:
    salt = os.urandom(16)
    key = _derive_key(password, salt)
    enc = _xor(plaintext.encode('utf-8'), key)
    return base64.b64encode(salt + enc).decode()

def vault_decrypt(ciphertext: str, password: str) -> str:
    payload = base64.b64decode(ciphertext.encode())
    salt = payload[:16]
    enc = payload[16:]
    key = _derive_key(password, salt)
    return _xor(enc, key).decode('utf-8')


# ═══════ Markdown 转 HTML（自包含，零依赖） ═══════
def _md_to_html(text: str) -> str:
    """将 Markdown 文本转为基本 HTML，用于 QTextBrowser 渲染"""
    html = text

    # 代码块 ```...```
    html = re.sub(r'```(\w*)\n(.*?)```', r'<pre style="background:#100820;color:#88ccaa;padding:12px;border-radius:8px;font-family:monospace;font-size:12px;overflow-x:auto;">\2</pre>', html, flags=re.DOTALL)

    # 行内代码 `...`
    html = re.sub(r'`([^`]+)`', r'<code style="background:rgba(170,80,255,25);color:#ddaaff;padding:1px 5px;border-radius:4px;font-family:monospace;">\1</code>', html)

    # 标题
    html = re.sub(r'^#### (.+)$', r'<h4 style="color:#aa88dd;margin:8px 0;">\1</h4>', html, flags=re.M)
    html = re.sub(r'^### (.+)$', r'<h3 style="color:#bb99ee;margin:8px 0;">\1</h3>', html, flags=re.M)
    html = re.sub(r'^## (.+)$', r'<h2 style="color:#ccaaff;margin:8px 0;">\1</h2>', html, flags=re.M)
    html = re.sub(r'^# (.+)$', r'<h1 style="color:#ddbbff;margin:8px 0;">\1</h1>', html, flags=re.M)

    # 粗体 **...** 和 斜体 *...*
    html = re.sub(r'\*\*(.+?)\*\*', r'<b style="color:#eeccff;">\1</b>', html)
    html = re.sub(r'\*(.+?)\*', r'<i style="color:#bb99cc;">\1</i>', html)
    html = re.sub(r'~~(.+?)~~', r'<s style="color:#776699;">\1</s>', html)

    # 无序列表 - item
    html = re.sub(r'^- (.+)$', r'<li style="color:#ccbbdd;margin:2px 0;">\1</li>', html, flags=re.M)

    # 有序列表 1. item
    html = re.sub(r'^\d+\. (.+)$', r'<li style="color:#ccbbdd;margin:2px 0;">\1</li>', html, flags=re.M)

    # 将连续 <li> 包裹进 <ul>
    html = re.sub(r'(<li.*?</li>\n?)+', r'<ul style="padding-left:24px;margin:4px 0;">\g<0></ul>', html)

    # 水平线 ---
    html = re.sub(r'^---+$', r'<hr style="border:none;border-top:1px solid rgba(170,80,255,30);margin:12px 0;">', html, flags=re.M)

    # 链接 [text](url)
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" style="color:#88aaff;">\1</a>', html)

    # 块引用 >
    html = re.sub(r'^> (.+)$', r'<blockquote style="border-left:3px solid rgba(170,80,255,50);padding:4px 12px;margin:6px 0;color:#9988bb;">\1</blockquote>', html, flags=re.M)

    # 段落：连续非空行
    html = re.sub(r'\n\n+', '<br><br>', html)
    html = re.sub(r'\n(?!<)', '<br>', html)

    return html


# ═══════ 文本编辑器窗口 ═══════
class EditorWindow(QDialog):
    """文本编辑器 · NEURAL — 支持 Markdown 预览"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("文本编辑器 · NEURAL")
        self.setMinimumSize(700, 500)
        self.setStyleSheet("background: rgba(10,5,20,240);")
        self._editor_filepath = None
        self._editor_password = None
        self._preview_visible = False
        self._splitter = None
        self._preview = None
        self._build_ui()

    def _build_ui(self):
        l = QVBoxLayout(self)
        l.setSpacing(6)
        l.setContentsMargins(10, 10, 10, 10)

        # ── 工具栏 ──
        tb = QHBoxLayout()
        btn_open = QPushButton("打开")
        btn_open.setStyleSheet(CYBER_PURPLE.BTN_PRIMARY)
        btn_open.clicked.connect(self._open)
        tb.addWidget(btn_open)

        btn_save = QPushButton("保存")
        btn_save.setStyleSheet(CYBER_PURPLE.BTN_PRIMARY)
        btn_save.clicked.connect(self._save)
        tb.addWidget(btn_save)

        btn_enc = QPushButton("加密保存")
        btn_enc.setStyleSheet(CYBER_PURPLE.BTN_PRIMARY)
        btn_enc.clicked.connect(self._save_enc)
        tb.addWidget(btn_enc)

        tb.addSpacing(12)

        self._preview_btn = QPushButton("预览")
        self._preview_btn.setStyleSheet(CYBER_PURPLE.BTN_PRIMARY)
        self._preview_btn.setCheckable(True)
        self._preview_btn.toggled.connect(self._toggle_preview)
        tb.addWidget(self._preview_btn)

        self._auto_preview = QCheckBox("实时")
        self._auto_preview.setStyleSheet(
            "color: #776699; font-size: 11px; background: transparent;"
        )
        self._auto_preview.setChecked(True)
        self._auto_preview.toggled.connect(lambda: self._refresh_preview())
        tb.addWidget(self._auto_preview)

        tb.addStretch()

        self._path_label = QLabel("未打开文件")
        self._path_label.setStyleSheet("color: #8877aa; font-size: 11px; background: transparent;")
        tb.addWidget(self._path_label)
        tb.addStretch()
        l.addLayout(tb)

        # ── 编辑/预览区（QSplitter） ──
        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setStyleSheet("QSplitter::handle { background: rgba(170,80,255,30); width: 2px; }")

        # 编辑面板
        self._editor = QTextEdit()
        self._editor.setStyleSheet("""
            QTextEdit {
                background: rgba(8,4,16,230); color: #ccbbdd;
                border: 1px solid rgba(170,80,255,35); border-radius: 10px;
                padding: 12px; font-size: 13px; line-height: 1.6;
            }
        """)
        self._editor.textChanged.connect(self._on_text_changed)
        self._splitter.addWidget(self._editor)

        # 预览面板（初始隐藏）
        self._preview = QTextBrowser()
        self._preview.setStyleSheet(PREVIEW_STYLE)
        self._preview.setOpenExternalLinks(True)
        self._preview.hide()
        self._splitter.addWidget(self._preview)

        l.addWidget(self._splitter, 1)

        # ── 状态栏 ──
        sb = QHBoxLayout()
        self._status = QLabel("字数: 0")
        self._status.setStyleSheet("color: #8877aa; font-size: 11px; background: transparent;")
        sb.addWidget(self._status)
        sb.addStretch()
        btn_clear = QPushButton("清空")
        btn_clear.setStyleSheet(CYBER_PURPLE.BTN_DANGER)
        btn_clear.clicked.connect(lambda: self._editor.clear())
        sb.addWidget(btn_clear)
        l.addLayout(sb)

    # ═══════ 预览切换 ═══════
    def _toggle_preview(self, checked):
        self._preview_visible = checked
        if checked:
            self._preview_btn.setStyleSheet(BTN_ACTIVE)
            self._preview.show()
            self._refresh_preview()
        else:
            self._preview_btn.setStyleSheet(CYBER_PURPLE.BTN_PRIMARY)
            self._preview.hide()

    def _refresh_preview(self):
        if self._preview_visible and self._preview:
            html = _md_to_html(self._editor.toPlainText())
            self._preview.setHtml(html)

    def _on_text_changed(self):
        self._update_status()
        if self._preview_visible and self._auto_preview.isChecked():
            self._refresh_preview()

    # ═══════ 文件操作 ═══════
    def _open(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开文件", "",
            "文本文件 (*.txt *.md *.py *.json *.html *.csv);;所有文件 (*)")
        if not path:
            return
        try:
            with open(path, 'rb') as f:
                raw = f.read(12)
            if raw.startswith(b'VLT'):
                pwd, ok = QInputDialog.getText(self, "加密文件", "输入密码：", QLineEdit.Password)
                if not ok:
                    return
                with open(path, encoding='utf-8') as f:
                    full = f.read()
                try:
                    content = vault_decrypt(full, pwd)
                    self._editor_filepath = path
                    self._editor_password = pwd
                except Exception:
                    QMessageBox.warning(self, "错误", "密码错误或文件损坏")
                    return
            else:
                with open(path, encoding='utf-8', errors='replace') as f:
                    content = f.read()
                self._editor_filepath = path
                self._editor_password = None
            self._editor.setPlainText(content)
            self._path_label.setText(os.path.basename(path))
            self._update_status()
        except Exception as e:
            QMessageBox.warning(self, "打开失败", str(e))

    def _save(self):
        if not self._editor_filepath:
            return self._save_as()
        try:
            content = self._editor.toPlainText()
            if self._editor_password:
                enc = vault_encrypt(content, self._editor_password)
                with open(self._editor_filepath, 'wb') as f:
                    f.write(enc.encode())
            else:
                with open(self._editor_filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            self._path_label.setText(os.path.basename(self._editor_filepath))
        except Exception as e:
            QMessageBox.warning(self, "保存失败", str(e))

    def _save_enc(self):
        self._save_as(encrypted=True)

    def _save_as(self, encrypted=False):
        ext = ".opc" if encrypted else ".txt"
        path, _ = QFileDialog.getSaveFileName(self, "保存文件", "", f"文本文件 (*{ext});;所有文件 (*)")
        if not path:
            return False
        if encrypted:
            pwd, ok = QInputDialog.getText(self, "设置密码", "请输入加密密码（至少4位）：", QLineEdit.Password)
            if not ok or len(pwd) < 4:
                QMessageBox.warning(self, "错误", "密码至少4位")
                return False
            confirm, ok = QInputDialog.getText(self, "确认密码", "再次输入密码：", QLineEdit.Password)
            if not ok or pwd != confirm:
                QMessageBox.warning(self, "错误", "两次密码不一致")
                return False
            self._editor_password = pwd
            content = self._editor.toPlainText()
            enc = vault_encrypt(content, pwd)
            with open(path, 'wb') as f:
                f.write(enc.encode())
        else:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self._editor.toPlainText())
            self._editor_password = None
        self._editor_filepath = path
        self._path_label.setText(os.path.basename(path))
        return True

    def _update_status(self):
        text = self._editor.toPlainText()
        lines = len(text.splitlines())
        chars = len(text)
        self._status.setText(f"字数: {chars}  行数: {lines}")

```
