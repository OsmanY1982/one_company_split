"""
客户管理 · ORBIT — 独立弹窗模块
"""
import os
from core.database import get_conn, close_conn
from sqlite3 import OperationalError
import random
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QLineEdit, QHeaderView, QMessageBox,
    QFormLayout, QComboBox, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# ── 路径 ──
from core.data import CUSTOMER_DB
from core.ui_components import SectionTitle, PrimaryButton, SecondaryButton, DangerButton
from core.light_tool_theme import LIGHT_TOOL_STYLE
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── 数据库初始化 ──
def _init_customer_db():
    os.makedirs(os.path.dirname(CUSTOMER_DB), exist_ok=True)
    conn = get_conn('customer.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS customer (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        company TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        address TEXT DEFAULT '',
        level TEXT DEFAULT '普通',
        note TEXT DEFAULT '',
        customer_no TEXT DEFAULT '',
        source TEXT DEFAULT '',
        total_orders INTEGER DEFAULT 0,
        total_amount REAL DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    # 迁移：为已有 customer 表补充业务字段
    for col, col_def in [
        ("customer_no", "TEXT DEFAULT ''"),
        ("source", "TEXT DEFAULT ''"),
        ("total_orders", "INTEGER DEFAULT 0"),
        ("total_amount", "REAL DEFAULT 0"),
    ]:
        try: c.execute(f"ALTER TABLE customer ADD COLUMN {col} {col_def}")
        except OperationalError: pass
    conn.commit()
    close_conn('customer.db')


# ═══════════════════════════════════════════════════════
#  CustomerDialog — 新增/编辑表单
# ═══════════════════════════════════════════════════════

class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer_data=None):
        super().__init__(parent)
        self.setWindowTitle("新增客户" if customer_data is None else "编辑客户")
        self.resize(440, 420)
        self.setStyleSheet(LIGHT_TOOL_STYLE)
        self._customer_data = customer_data

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("新增客户" if customer_data is None else "编辑客户")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("客户姓名")
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("联系电话")
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("邮箱地址")

        self.level_combo = QComboBox()
        self.level_combo.addItems(["普通", "VIP", "钻石"])
        self.source_combo = QComboBox()
        self.source_combo.addItems(["官网", "推荐", "展会", "其他"])
        self.remark_edit = QTextEdit()
        self.remark_edit.setMaximumHeight(80)

        form.addRow("姓名:", self.name_edit)
        form.addRow("电话:", self.phone_edit)
        form.addRow("邮箱:", self.email_edit)
        form.addRow("级别:", self.level_combo)
        form.addRow("来源:", self.source_combo)
        form.addRow("备注:", self.remark_edit)

        layout.addLayout(form)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = PrimaryButton("保存")
        save_btn.clicked.connect(self._on_save)
        cancel_btn = SecondaryButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        if customer_data:
            self._fill_data(customer_data)

    def _fill_data(self, data):
        self.name_edit.setText(data.get("name", ""))
        self.phone_edit.setText(data.get("phone", ""))
        self.email_edit.setText(data.get("email", ""))
        level = data.get("level", "普通")
        idx = self.level_combo.findText(level)
        if idx >= 0:
            self.level_combo.setCurrentIndex(idx)
        source = data.get("source", "")
        idx = self.source_combo.findText(source)
        if idx >= 0:
            self.source_combo.setCurrentIndex(idx)
        self.remark_edit.setPlainText(data.get("remark", ""))

    def _on_save(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "提示", "请输入客户姓名")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "level": self.level_combo.currentText(),
            "source": self.source_combo.currentText(),
            "note": self.remark_edit.toPlainText().strip(),
        }


# ═══════════════════════════════════════════════════════
#  CustomerWindow
# ═══════════════════════════════════════════════════════

class CustomerWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("客户管理 · ORBIT")
        self.resize(550, 500)
        self.setStyleSheet(LIGHT_TOOL_STYLE)

        _init_customer_db()

        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # 标题
        title = SectionTitle("客户管理 · ORBIT")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 搜索栏 + 级别筛选
        top_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索姓名 / 电话...")
        self.search_edit.textChanged.connect(self._on_search)
        top_layout.addWidget(self.search_edit)

        self.level_filter = QComboBox()
        self.level_filter.addItems(["全部", "普通", "VIP", "钻石"])
        self.level_filter.currentTextChanged.connect(self._on_filter)
        top_layout.addWidget(self.level_filter)

        layout.addLayout(top_layout)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["编号", "姓名", "电话", "邮箱", "级别", "累计消费", "来源", "备注"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)

        # 按钮栏
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.add_btn = PrimaryButton("新增")
        self.add_btn.clicked.connect(self._on_add)
        self.edit_btn = SecondaryButton("编辑")
        self.edit_btn.clicked.connect(self._on_edit)
        self.del_btn = DangerButton("删除")
        self.del_btn.clicked.connect(self._on_delete)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        layout.addLayout(btn_layout)

    def _get_conn(self):
        conn = get_conn('customer.db')
        
        return conn

    def _build_query(self):
        search = self.search_edit.text().strip()
        level = self.level_filter.currentText()

        where_clauses = []
        params = []

        if search:
            where_clauses.append("(name LIKE ? OR phone LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        if level and level != "全部":
            where_clauses.append("level = ?")
            params.append(level)

        sql = "SELECT * FROM customer"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += " ORDER BY created_at DESC"
        return sql, params

    def _load_data(self):
        conn = self._get_conn()
        c = conn.cursor()
        sql, params = self._build_query()
        c.execute(sql, params)
        rows = c.fetchall()
        close_conn('customer.db')

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            items = [
                row["customer_no"] or "",
                row["name"] or "",
                row["phone"] or "",
                row["email"] or "",
                row["level"] or "普通",
                f"¥{row['total_amount']:,.2f}" if row["total_amount"] else "¥0.00",
                row["source"] or "",
                row["note"] or "",
            ]
            for j, val in enumerate(items):
                self.table.setItem(i, j, QTableWidgetItem(val))

    def _on_search(self, text):
        self._load_data()

    def _on_filter(self, text):
        self._load_data()

    def _get_selected_id(self):
        idx = self.table.currentRow()
        if idx < 0:
            return None
        item = self.table.item(idx, 0)
        if item is None:
            return None
        return item.text()

    def _on_add(self):
        dlg = CustomerDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_data()
        customer_no = "CU" + datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))

        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""INSERT INTO customer (customer_no, name, phone, email, level, source, note)
            VALUES (?,?,?,?,?,?,?)""",
            (customer_no, data["name"], data["phone"], data["email"],
             data["level"], data["source"], data["note"]))
        conn.commit()
        close_conn('customer.db')
        self._load_data()

    def _on_edit(self):
        customer_no = self._get_selected_id()
        if customer_no is None:
            QMessageBox.information(self, "提示", "请先选择一个客户")
            return

        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM customer WHERE customer_no = ?", (customer_no,))
        row = c.fetchone()
        close_conn('customer.db')
        if row is None:
            return

        data = dict(row)
        dlg = CustomerDialog(self, customer_data=data)
        if dlg.exec_() != QDialog.Accepted:
            return
        new_data = dlg.get_data()

        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""UPDATE customer SET name=?, phone=?, email=?, level=?, source=?, note=?
            WHERE customer_no=?""",
            (new_data["name"], new_data["phone"], new_data["email"],
             new_data["level"], new_data["source"], new_data["note"], customer_no))
        conn.commit()
        close_conn('customer.db')
        self._load_data()

    def _on_delete(self):
        customer_no = self._get_selected_id()
        if customer_no is None:
            QMessageBox.information(self, "提示", "请先选择一个客户")
            return
        reply = QMessageBox.question(self, "确认删除", f"确定要删除客户 {customer_no} 吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM customer WHERE customer_no = ?", (customer_no,))
        conn.commit()
        close_conn('customer.db')
        self._load_data()
