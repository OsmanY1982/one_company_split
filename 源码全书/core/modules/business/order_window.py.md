# `core/modules/business/order_window.py`

> 路径：`core/modules/business/order_window.py` | 行数：446


---


```python
"""
订单管理 · ORBIT — 独立弹窗模块
"""
import traceback
import os
from core.database import get_conn, close_conn
from sqlite3 import OperationalError
import random
import csv
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QHeaderView, QMessageBox,
    QFormLayout, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox,
    QDateEdit, QFileDialog, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# ── 路径 ──
from core.data import ORDER_DB, FINANCE_DB
from core.ui_components import SectionTitle, PrimaryButton, SecondaryButton, DangerButton
from core.light_tool_theme import LIGHT_TOOL_STYLE
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── 数据库初始化 ──
def _init_order_db():
    os.makedirs(os.path.dirname(ORDER_DB), exist_ok=True)
    conn = get_conn('order.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_no TEXT UNIQUE NOT NULL,
        customer_name TEXT,
        product_name TEXT,
        quantity INTEGER DEFAULT 1,
        unit_price REAL DEFAULT 0,
        total_amount REAL DEFAULT 0,
        status TEXT DEFAULT '待处理',
        note TEXT,
        payment_method TEXT DEFAULT '',
        date TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    # 迁移：为已有 orders 表补充业务字段
    for col, col_def in [
        ("date", "TEXT DEFAULT ''"),
        ("payment_method", "TEXT DEFAULT ''"),
    ]:
        try: c.execute(f"ALTER TABLE orders ADD COLUMN {col} {col_def}")
        except OperationalError: pass
    conn.commit()
    close_conn('order.db')


def _init_finance_db():
    """初始化财务表，与 data/finance.db 保持一致"""
    os.makedirs(os.path.dirname(FINANCE_DB), exist_ok=True)
    conn = get_conn('finance.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        category TEXT DEFAULT '',
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        description TEXT DEFAULT '',
        order_no TEXT DEFAULT '',
        finance_no TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    # 迁移：为已有 finance 表补充业务字段
    for col, col_def in [
        ("order_no", "TEXT DEFAULT ''"),
        ("finance_no", "TEXT DEFAULT ''"),
    ]:
        try: c.execute(f"ALTER TABLE finance ADD COLUMN {col} {col_def}")
        except OperationalError: pass
    conn.commit()
    close_conn('finance.db')


# ── 白底工具统一样式（LIGHT_TOOL_STYLE）+ 表格补充 ──
LIGHT_TABLE_STYLE = """
    QTableWidget {
        background: white;
        color: #2d3748;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        gridline-color: #e2e8f0;
        selection-background-color: #bee3f8;
    }
    QTableWidget::item {
        padding: 4px 8px;
    }
    QHeaderView::section {
        background: #edf2f7;
        color: #2d3748;
        border: 1px solid #e2e8f0;
        padding: 6px;
        font-weight: bold;
    }
"""


# ═══════════════════════════════════════════════════════
#  OrderDialog — 新增/编辑表单
# ═══════════════════════════════════════════════════════

class OrderDialog(QDialog):
    def __init__(self, parent=None, order_data=None):
        super().__init__(parent)
        self.setWindowTitle("新增订单" if order_data is None else "编辑订单")
        self.resize(460, 480)
        self.setStyleSheet(LIGHT_TOOL_STYLE)
        self._order_data = order_data

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("新增订单" if order_data is None else "编辑订单")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.customer_edit = QLineEdit()
        self.customer_edit.setPlaceholderText("客户名称")
        self.product_edit = QLineEdit()
        self.product_edit.setPlaceholderText("产品名称")
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 99999)
        self.quantity_spin.setValue(1)
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 99999999.99)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("¥ ")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(datetime.now().date())
        self.status_combo = QComboBox()
        self.status_combo.addItems(["待处理", "处理中", "已完成", "已取消"])
        self.remark_edit = QTextEdit()
        self.remark_edit.setMaximumHeight(80)

        form.addRow("客户:", self.customer_edit)
        form.addRow("产品:", self.product_edit)
        form.addRow("数量:", self.quantity_spin)
        form.addRow("金额:", self.amount_spin)
        form.addRow("日期:", self.date_edit)
        form.addRow("状态:", self.status_combo)
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

        # 编辑时填充
        if order_data:
            self._fill_data(order_data)

    def _fill_data(self, data):
        self.customer_edit.setText(data.get("customer_name", ""))
        self.product_edit.setText(data.get("product_name", ""))
        self.quantity_spin.setValue(data.get("quantity", 1))
        self.amount_spin.setValue(data.get("total_amount", 0))
        self.remark_edit.setPlainText(data.get("note", ""))
        date_str = data.get("date", "")
        if date_str:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                self.date_edit.setDate(dt.date())
            except ValueError:
                traceback.print_exc()
        status = data.get("status", "待处理")
        idx = self.status_combo.findText(status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)

    def _on_save(self):
        if not self.customer_edit.text().strip():
            QMessageBox.warning(self, "提示", "请输入客户名称")
            return
        self.accept()

    def get_data(self):
        return {
            "customer_name": self.customer_edit.text().strip(),
            "product_name": self.product_edit.text().strip(),
            "quantity": self.quantity_spin.value(),
            "total_amount": self.amount_spin.value(),
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "status": self.status_combo.currentText(),
            "note": self.remark_edit.toPlainText().strip(),
        }


# ═══════════════════════════════════════════════════════
#  OrderWindow
# ═══════════════════════════════════════════════════════

class OrderWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("订单管理 · ORBIT")
        self.resize(600, 600)
        self.setStyleSheet(LIGHT_TOOL_STYLE)

        _init_order_db()
        _init_finance_db()

        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 标题
        title = SectionTitle("订单管理 · ORBIT")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 搜索栏
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索客户 / 产品 / 订单号...")
        self.search_edit.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["编号", "客户", "产品", "数量", "金额", "日期", "状态", "备注"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setStyleSheet(LIGHT_TABLE_STYLE)
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
        self.export_btn = SecondaryButton("导出CSV")
        self.export_btn.clicked.connect(self._on_export)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addWidget(self.export_btn)
        layout.addLayout(btn_layout)

    def _get_conn(self):
        conn = get_conn('order.db')
        return conn

    def _load_data(self, search=""):
        conn = self._get_conn()
        c = conn.cursor()
        if search:
            c.execute("""SELECT * FROM orders
                WHERE customer_name LIKE ? OR product_name LIKE ? OR order_no LIKE ?
                ORDER BY created_at DESC""",
                (f"%{search}%", f"%{search}%", f"%{search}%"))
        else:
            c.execute("SELECT * FROM orders ORDER BY created_at DESC")
        rows = c.fetchall()
        close_conn('order.db')

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            items = [
                row["order_no"] or "",
                row["customer_name"] or "",
                row["product_name"] or "",
                str(row["quantity"] or ""),
                f"¥{row['total_amount']:,.2f}" if row["total_amount"] else "",
                str(row["date"] or ""),
                row["status"] or "待处理",
                row["note"] or "",
            ]
            for j, val in enumerate(items):
                self.table.setItem(i, j, QTableWidgetItem(val))

    def _on_search(self, text):
        self._load_data(text.strip())

    def _get_selected_id(self):
        idx = self.table.currentRow()
        if idx < 0:
            return None
        item = self.table.item(idx, 0)
        if item is None:
            return None
        return item.text()

    def _on_add(self):
        dlg = OrderDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_data()
        order_no = "OR" + datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))

        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""INSERT INTO orders (order_no, customer_name, product_name, quantity, total_amount, date, status, note)
            VALUES (?,?,?,?,?,?,?,?)""",
            (order_no, data["customer_name"], data["product_name"], data["quantity"],
             data["total_amount"], data["date"], data["status"], data["note"]))
        conn.commit()
        close_conn('order.db')

        # 联动：写入财务收入
        self._sync_finance(order_no, data["total_amount"])

        self._load_data(self.search_edit.text().strip())

    def _on_edit(self):
        order_no = self._get_selected_id()
        if order_no is None:
            QMessageBox.information(self, "提示", "请先选择一条订单")
            return

        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM orders WHERE order_no = ?", (order_no,))
        row = c.fetchone()
        close_conn('order.db')
        if row is None:
            return

        data = dict(row)
        dlg = OrderDialog(self, order_data=data)
        if dlg.exec_() != QDialog.Accepted:
            return
        new_data = dlg.get_data()

        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""UPDATE orders SET customer_name=?, product_name=?, quantity=?,
            total_amount=?, date=?, status=?, note=? WHERE order_no=?""",
            (new_data["customer_name"], new_data["product_name"], new_data["quantity"],
             new_data["total_amount"], new_data["date"], new_data["status"],
             new_data["note"], order_no))
        conn.commit()
        close_conn('order.db')

        # 联动：更新财务记录
        self._sync_finance(order_no, new_data["total_amount"])

        self._load_data(self.search_edit.text().strip())

    def _on_delete(self):
        order_no = self._get_selected_id()
        if order_no is None:
            QMessageBox.information(self, "提示", "请先选择一条订单")
            return
        reply = QMessageBox.question(self, "确认删除", f"确定要删除订单 {order_no} 吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM orders WHERE order_no = ?", (order_no,))
        conn.commit()
        close_conn('order.db')

        # 联动：清理财务记录
        self._delete_finance(order_no)

        self._load_data(self.search_edit.text().strip())

    def _on_export(self):
        desktop = os.path.expanduser("~/Desktop")
        default_name = f"订单导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "导出CSV", os.path.join(desktop, default_name),
                                              "CSV Files (*.csv)")
        if not path:
            return

        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM orders ORDER BY created_at DESC")
        rows = c.fetchall()
        close_conn('order.db')

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["订单编号", "客户", "产品", "数量", "金额", "日期", "状态", "备注", "创建时间"])
            for row in rows:
                writer.writerow([
                    row["order_no"], row["customer_name"], row["product_name"],
                    row["quantity"], row["total_amount"], row["date"],
                    row["status"], row["note"], row["created_at"],
                ])

        QMessageBox.information(self, "导出成功", f"已导出至:\n{path}")

    def _sync_finance(self, order_no, amount, category="订单收入"):
        try:
            conn = get_conn('finance.db')
            c = conn.cursor()
            c.execute("DELETE FROM finance WHERE order_no = ?", (order_no,))
            finance_no = "FN" + datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))
            c.execute("""INSERT INTO finance (type, category, amount, date, description, order_no, finance_no)
                VALUES (?,?,?,?,?,?,?)""",
                ("收入", category, amount,
                 datetime.now().strftime("%Y-%m-%d"),
                 f"订单{order_no}", order_no, finance_no))
            conn.commit()
            close_conn('finance.db')
        except Exception:
            traceback.print_exc()

    def _delete_finance(self, order_no):
        """删除订单时清理对应财务记录"""
        try:
            conn = get_conn('finance.db')
            c = conn.cursor()
            c.execute("DELETE FROM finance WHERE order_no = ?", (order_no,))
            conn.commit()
            close_conn('finance.db')
        except Exception:
            traceback.print_exc()

```
