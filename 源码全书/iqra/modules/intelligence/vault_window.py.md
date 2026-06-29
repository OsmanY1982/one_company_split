# `iqra/modules/intelligence/vault_window.py`

> 路径：`iqra/modules/intelligence/vault_window.py` | 行数：358


---


```python
"""
密码保险箱 · NEURAL — 独立子窗口
从 tools_window.py 拆分，提供加密密码存储与管理
"""
import os, json, hashlib, base64, secrets
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QLineEdit, QWidget, QMessageBox,
    QInputDialog, QComboBox, QFormLayout, QDialogButtonBox, QMenu, QApplication,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

# ═══════ 常量 ═══════
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
VAULT_FILE = os.path.join(DATA_DIR, "vault_cosmic.enc")
VAULT_CATEGORIES = ["全部", "社交媒体", "银行金融", "购物电商", "工作办公", "游戏娱乐", "邮箱", "开发工具", "其他"]
VAULT_CAT_COLORS = {
    "银行金融": "#e53e3e", "社交媒体": "#3182ce", "购物电商": "#d69e2e",
    "工作办公": "#38a169", "游戏娱乐": "#805ad5", "邮箱": "#dd6b20",
    "开发工具": "#2b6cb0", "其他": "#718096",
}

from core.dark_tool_theme import (
    DARK_BG, DARK_SURFACE, DARK_TEXT, DARK_TEXT_MUTED,
    DARK_TABLE_STYLE, DARK_INPUT_STYLE, DARK_BTN_PRIMARY, DARK_BTN_DANGER,
    ACCENT_BLUE_DIM,
)

TABLE_STYLE = DARK_TABLE_STYLE
INPUT_STYLE = DARK_INPUT_STYLE
BTN_PRIMARY = DARK_BTN_PRIMARY
BTN_DANGER  = DARK_BTN_DANGER


# ═══════ 加解密函数 ═══════
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


# ═══════ 条目编辑对话框 ═══════
class VaultEntryDialog(QDialog):
    """密码保险箱 — 新增/编辑条目"""

    def __init__(self, parent=None, entry=None):
        super().__init__(parent)
        self.setWindowTitle("编辑条目" if entry else "新建条目")
        self.setFixedSize(380, 300)
        self.setStyleSheet("background: rgba(16,8,28,235);")
        l = QFormLayout(self)
        l.setSpacing(10)

        self._title = QLineEdit(entry.get("title", "") if entry else "")
        self._title.setStyleSheet(INPUT_STYLE)
        self._title.setPlaceholderText("如: Google 账号")
        l.addRow("名称:", self._title)

        self._category = QComboBox()
        self._category.addItems(VAULT_CATEGORIES[1:])
        if entry:
            idx = self._category.findText(entry.get("category", "其他"))
            if idx >= 0:
                self._category.setCurrentIndex(idx)
        self._category.setStyleSheet(INPUT_STYLE)
        l.addRow("分类:", self._category)

        self._account = QLineEdit(entry.get("account", "") if entry else "")
        self._account.setStyleSheet(INPUT_STYLE)
        self._account.setPlaceholderText("邮箱 / 手机号")
        l.addRow("账号:", self._account)

        self._password = QLineEdit(entry.get("password", "") if entry else "")
        self._password.setStyleSheet(INPUT_STYLE)
        self._password.setPlaceholderText("密码")
        self._password.setEchoMode(QLineEdit.Password)
        l.addRow("密码:", self._password)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._validate_and_accept)
        btn_box.rejected.connect(self.reject)
        btn_box.setStyleSheet("QPushButton { background: rgba(150,60,220,40); color: #ddaaff; border-radius: 12px; padding: 5px 18px; }")
        l.addRow(btn_box)

    def _validate_and_accept(self):
        if not self._title.text().strip():
            QMessageBox.warning(self, "缺少参数", "请输入名称")
            return
        self.accept()

    def get_data(self):
        return {
            "title": self._title.text().strip(),
            "category": self._category.currentText(),
            "account": self._account.text().strip(),
            "password": self._password.text(),
            "url": ""
        }


# ═══════ 密码保险箱主窗口 ═══════
class VaultWindow(QDialog):
    """密码保险箱 · NEURAL"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("密码保险箱 · NEURAL")
        self.setMinimumSize(780, 540)
        self.setStyleSheet("background: rgba(10,5,20,240);")
        self._vault_master_pwd = None
        self._vault_entries = []
        self._build_ui()

    def _build_ui(self):
        l = QVBoxLayout(self)
        l.setSpacing(8)
        l.setContentsMargins(10, 10, 10, 10)

        # ── 锁定界面 ──
        self._lock_widget = QWidget()
        lock_l = QVBoxLayout(self._lock_widget)
        lock_l.setAlignment(Qt.AlignCenter)

        lock_title = QLabel("密码保险箱")
        lock_title.setStyleSheet("color: #aa99dd; font-size: 20px; font-weight: 700; background: transparent;")
        lock_title.setAlignment(Qt.AlignCenter)
        lock_l.addWidget(lock_title)
        lock_l.addSpacing(20)

        self._pwd_input = QLineEdit()
        self._pwd_input.setPlaceholderText("输入主密码解锁...")
        self._pwd_input.setEchoMode(QLineEdit.Password)
        self._pwd_input.setStyleSheet(INPUT_STYLE + "QLineEdit { max-width: 280px; }")
        self._pwd_input.returnPressed.connect(self._unlock)
        lock_l.addWidget(self._pwd_input, alignment=Qt.AlignCenter)

        self._lock_msg = QLabel("")
        self._lock_msg.setStyleSheet("color: #ff8888; font-size: 12px; background: transparent;")
        self._lock_msg.setAlignment(Qt.AlignCenter)
        lock_l.addWidget(self._lock_msg)

        btn_unlock = QPushButton("解锁")
        btn_unlock.setStyleSheet(BTN_PRIMARY + "QPushButton { max-width: 120px; }")
        btn_unlock.clicked.connect(self._unlock)
        lock_l.addWidget(btn_unlock, alignment=Qt.AlignCenter)
        l.addWidget(self._lock_widget)

        # ── 主界面（解锁后显示） ──
        self._main_widget = QWidget()
        vm_l = QVBoxLayout(self._main_widget)
        vm_l.setContentsMargins(0, 0, 0, 0)
        vm_l.setSpacing(8)

        vault_top = QHBoxLayout()
        self._count_lbl = QLabel("共 0 条")
        self._count_lbl.setStyleSheet("color: #8877aa; font-size: 12px; background: transparent;")
        vault_top.addWidget(self._count_lbl)
        vault_top.addStretch()
        btn_repwd = QPushButton("改密")
        btn_repwd.setStyleSheet(BTN_PRIMARY)
        btn_repwd.clicked.connect(self._change_pwd)
        vault_top.addWidget(btn_repwd)
        btn_add = QPushButton("+ 添加")
        btn_add.setStyleSheet(BTN_PRIMARY)
        btn_add.clicked.connect(self._add_entry)
        vault_top.addWidget(btn_add)
        btn_lock = QPushButton("锁定")
        btn_lock.setStyleSheet(BTN_DANGER)
        btn_lock.clicked.connect(self._lock)
        vault_top.addWidget(btn_lock)
        vm_l.addLayout(vault_top)

        filter_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索...")
        self._search.setStyleSheet(INPUT_STYLE)
        self._search.textChanged.connect(self._refresh)
        filter_row.addWidget(self._search)
        self._cat = QComboBox()
        self._cat.addItems(VAULT_CATEGORIES)
        self._cat.setStyleSheet("background: rgba(20,10,35,230); color: #bb99dd; border: 1px solid rgba(170,80,255,35); border-radius: 8px; padding: 4px 8px;")
        self._cat.currentIndexChanged.connect(self._refresh)
        filter_row.addWidget(self._cat)
        self._show_pwd = QPushButton("显示密码")
        self._show_pwd.setCheckable(True)
        self._show_pwd.setStyleSheet(BTN_PRIMARY)
        self._show_pwd.toggled.connect(self._refresh)
        filter_row.addWidget(self._show_pwd)
        vm_l.addLayout(filter_row)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["名称", "分类", "账号", "密码", "更新时间"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setStyleSheet(TABLE_STYLE)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.doubleClicked.connect(self._edit_entry)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._context_menu)
        vm_l.addWidget(self._table, 1)

        l.addWidget(self._main_widget)
        self._main_widget.hide()

    # ═══════ 保险箱逻辑 ═══════
    def _unlock(self):
        pwd = self._pwd_input.text()
        if not pwd:
            self._lock_msg.setText("请输入主密码")
            return
        if not os.path.exists(VAULT_FILE):
            confirm, ok = QInputDialog.getText(self, "设置主密码", "首次使用，请再次输入确认：", QLineEdit.Password)
            if not ok or pwd != confirm:
                self._lock_msg.setText("两次密码不一致")
                return
            self._vault_master_pwd = pwd
            self._vault_entries = []
            self._save()
            self._show_main()
        else:
            try:
                with open(VAULT_FILE, encoding='utf-8') as f:
                    raw = f.read()
                data = json.loads(vault_decrypt(raw, pwd))
                self._vault_master_pwd = pwd
                self._vault_entries = data.get('entries', [])
                self._show_main()
            except Exception:
                self._lock_msg.setText("密码错误")
                self._pwd_input.clear()

    def _show_main(self):
        self._lock_widget.hide()
        self._main_widget.show()
        self._pwd_input.clear()
        self._lock_msg.setText("")
        self._refresh()

    def _lock(self):
        self._vault_master_pwd = None
        self._vault_entries = []
        self._main_widget.hide()
        self._lock_widget.show()
        self._pwd_input.clear()

    def _save(self):
        data = json.dumps({'entries': self._vault_entries}, ensure_ascii=False)
        enc = vault_encrypt(data, self._vault_master_pwd)
        os.makedirs(os.path.dirname(VAULT_FILE), exist_ok=True)
        with open(VAULT_FILE, 'w', encoding='utf-8') as f:
            f.write(enc)

    def _add_entry(self):
        dlg = VaultEntryDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            entry = dlg.get_data()
            entry['id'] = secrets.token_hex(8)
            entry['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self._vault_entries.append(entry)
            self._save()
            self._refresh()

    def _edit_entry(self):
        row = self._table.currentRow()
        if row < 0:
            return
        idx = self._table.item(row, 0).data(Qt.UserRole)
        entry = next((e for e in self._vault_entries if e.get('id') == idx), None)
        if not entry:
            return
        dlg = VaultEntryDialog(self, entry)
        if dlg.exec_() == QDialog.Accepted:
            entry.update(dlg.get_data())
            entry['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self._save()
            self._refresh()

    def _delete(self, row):
        idx = self._table.item(row, 0).data(Qt.UserRole)
        name = self._table.item(row, 0).text()
        if QMessageBox.Yes == QMessageBox.question(self, "确认删除", f"删除「{name}」？"):
            self._vault_entries = [e for e in self._vault_entries if e.get('id') != idx]
            self._save()
            self._refresh()

    def _context_menu(self, pos):
        row = self._table.rowAt(pos.y())
        if row < 0:
            return
        idx = self._table.item(row, 0).data(Qt.UserRole)
        entry = next((e for e in self._vault_entries if e.get('id') == idx), None)
        if not entry:
            return
        menu = QMenu(self)
        menu.addAction("复制账号", lambda: QApplication.clipboard().setText(entry.get('account', '')))
        menu.addAction("复制密码", lambda: QApplication.clipboard().setText(entry.get('password', '')))
        if entry.get('url'):
            menu.addAction("复制网址", lambda: QApplication.clipboard().setText(entry.get('url', '')))
        menu.addSeparator()
        menu.addAction("编辑", self._edit_entry)
        menu.addAction("删除", lambda: self._delete(row))
        menu.exec_(self._table.viewport().mapToGlobal(pos))

    def _refresh(self):
        keyword = self._search.text().strip().lower()
        cat = self._cat.currentText()
        filtered = [e for e in self._vault_entries
                    if (cat == "全部" or e.get('category') == cat)
                    and (not keyword or keyword in e.get('title', '').lower()
                         or keyword in e.get('account', '').lower())]
        self._table.setRowCount(len(filtered))
        show_pwd = self._show_pwd.isChecked()
        for i, e in enumerate(filtered):
            name_item = QTableWidgetItem(e.get('title', ''))
            name_item.setData(Qt.UserRole, e.get('id'))
            self._table.setItem(i, 0, name_item)
            cat_item = QTableWidgetItem(e.get('category', ''))
            cat_item.setForeground(QColor(VAULT_CAT_COLORS.get(e.get('category', ''), '#718096')))
            self._table.setItem(i, 1, cat_item)
            self._table.setItem(i, 2, QTableWidgetItem(e.get('account', '')))
            pwd = e.get('password', '')
            self._table.setItem(i, 3, QTableWidgetItem(pwd if show_pwd else '*' * len(pwd)))
            self._table.setItem(i, 4, QTableWidgetItem(e.get('updated', '')))
        self._count_lbl.setText(f"共 {len(self._vault_entries)} 条")

    def _change_pwd(self):
        old, ok = QInputDialog.getText(self, "修改主密码", "当前密码：", QLineEdit.Password)
        if not ok or old != self._vault_master_pwd:
            QMessageBox.warning(self, "错误", "密码错误")
            return
        new, ok = QInputDialog.getText(self, "修改主密码", "新密码（至少4位）：", QLineEdit.Password)
        if not ok or len(new) < 4:
            QMessageBox.warning(self, "错误", "新密码至少4位")
            return
        confirm, ok = QInputDialog.getText(self, "修改主密码", "确认新密码：", QLineEdit.Password)
        if not ok or new != confirm:
            QMessageBox.warning(self, "错误", "两次不一致")
            return
        self._vault_master_pwd = new
        self._save()
        QMessageBox.information(self, "成功", "主密码已修改")

```
