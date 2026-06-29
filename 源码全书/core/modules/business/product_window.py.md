# `core/modules/business/product_window.py`

> 路径：`core/modules/business/product_window.py` | 行数：330


---


```python
"""
产品管理 · ORBIT — 独立弹窗模块
"""
import os
from core.database import get_conn, close_conn
from sqlite3 import OperationalError
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QLineEdit, QHeaderView, QMessageBox,
    QFormLayout, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# ── 路径 ──
from core.data import PRODUCT_DB
from core.ui_components import SectionTitle, PrimaryButton, SecondaryButton, DangerButton
from core.light_tool_theme import LIGHT_TOOL_STYLE
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _init_product_db():
    os.makedirs(os.path.dirname(PRODUCT_DB), exist_ok=True)
    conn = get_conn('product.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_no TEXT,
        name TEXT NOT NULL,
        category TEXT DEFAULT '',
        price REAL DEFAULT 0,
        cost REAL DEFAULT 0,
        stock INTEGER DEFAULT 0,
        unit TEXT DEFAULT '个',
        description TEXT DEFAULT '',
        status TEXT DEFAULT '在售',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    # 迁移：为已有 product 表补充业务字段
    try: c.execute("ALTER TABLE products ADD COLUMN product_no TEXT")
    except OperationalError: pass
    conn.commit()
    close_conn('product.db')


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
#  ProductDialog — 新增/编辑表单
# ═══════════════════════════════════════════════════════

class ProductDialog(QDialog):
    def __init__(self, parent=None, product_data=None):
        super().__init__(parent)
        self.setWindowTitle("新增产品" if product_data is None else "编辑产品")
        self.resize(420, 420)
        self.setStyleSheet(LIGHT_TOOL_STYLE)
        self._product_data = product_data

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("新增产品" if product_data is None else "编辑产品")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("产品名称")
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems(["硬件", "软件", "服务", "耗材", "其他"])
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0, 99999999.99)
        self.cost_spin.setDecimals(2)
        self.cost_spin.setPrefix("¥ ")
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 99999999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setPrefix("¥ ")
        self.stock_spin = QSpinBox()
        self.stock_spin.setRange(0, 999999)
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)

        form.addRow("名称:", self.name_edit)
        form.addRow("分类:", self.category_combo)
        form.addRow("成本:", self.cost_spin)
        form.addRow("售价:", self.price_spin)
        form.addRow("库存:", self.stock_spin)
        form.addRow("描述:", self.desc_edit)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = PrimaryButton("保存")
        save_btn.clicked.connect(self._on_save)
        cancel_btn = SecondaryButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        if product_data:
            self._fill_data(product_data)

    def _fill_data(self, data):
        self.name_edit.setText(data.get("name", ""))
        cat = data.get("category", "")
        idx = self.category_combo.findText(cat)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        elif cat:
            self.category_combo.setCurrentText(cat)
        self.cost_spin.setValue(data.get("cost", 0))
        self.price_spin.setValue(data.get("price", 0))
        self.stock_spin.setValue(data.get("stock", 0))
        self.desc_edit.setPlainText(data.get("description", ""))

    def _on_save(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "提示", "请输入产品名称")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "category": self.category_combo.currentText().strip(),
            "cost": self.cost_spin.value(),
            "price": self.price_spin.value(),
            "stock": self.stock_spin.value(),
            "description": self.desc_edit.toPlainText().strip(),
        }


# ═══════════════════════════════════════════════════════
#  ProductWindow
# ═══════════════════════════════════════════════════════

class ProductWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("产品管理 · ORBIT")
        self.resize(550, 500)
        self.setStyleSheet(LIGHT_TOOL_STYLE)

        _init_product_db()

        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = SectionTitle("产品管理 · ORBIT")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 搜索栏
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索产品名称 / 分类...")
        self.search_edit.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["编号", "名称", "分类", "成本", "售价", "库存", "描述"])
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

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        layout.addLayout(btn_layout)

    def _get_conn(self):
        conn = get_conn('product.db')
        
        return conn

    def _load_data(self, search=""):
        conn = self._get_conn()
        c = conn.cursor()
        if search:
            c.execute("""SELECT * FROM products
                WHERE name LIKE ? OR category LIKE ? OR product_no LIKE ?
                ORDER BY created_at DESC""",
                (f"%{search}%", f"%{search}%", f"%{search}%"))
        else:
            c.execute("SELECT * FROM products ORDER BY created_at DESC")
        rows = c.fetchall()
        close_conn('product.db')

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            items = [
                row["product_no"] or "",
                row["name"] or "",
                row["category"] or "",
                f"¥{row['cost']:,.2f}" if row["cost"] else "¥0.00",
                f"¥{row['price']:,.2f}" if row["price"] else "¥0.00",
                str(row["stock"] or 0),
                row["description"] or "",
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
        dlg = ProductDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_data()
        product_no = "PR" + datetime.now().strftime("%Y%m%d%H%M%S")

        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""INSERT INTO products (product_no, name, category, cost, price, stock, description)
            VALUES (?,?,?,?,?,?,?)""",
            (product_no, data["name"], data["category"], data["cost"],
             data["price"], data["stock"], data["description"]))
        conn.commit()
        close_conn('product.db')

        self._load_data(self.search_edit.text().strip())

    def _on_edit(self):
        product_no = self._get_selected_id()
        if product_no is None:
            QMessageBox.information(self, "提示", "请先选择一条产品")
            return

        conn = self._get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM products WHERE product_no = ?", (product_no,))
        row = c.fetchone()
        close_conn('product.db')
        if row is None:
            return

        data = dict(row)
        dlg = ProductDialog(self, product_data=data)
        if dlg.exec_() != QDialog.Accepted:
            return
        new_data = dlg.get_data()

        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""UPDATE products SET name=?, category=?, cost=?, price=?,
            stock=?, description=? WHERE product_no=?""",
            (new_data["name"], new_data["category"], new_data["cost"],
             new_data["price"], new_data["stock"], new_data["description"],
             product_no))
        conn.commit()
        close_conn('product.db')
        self._load_data(self.search_edit.text().strip())

    def _on_delete(self):
        product_no = self._get_selected_id()
        if product_no is None:
            QMessageBox.information(self, "提示", "请先选择一条产品")
            return
        reply = QMessageBox.question(self, "确认删除", f"确定要删除产品 {product_no} 吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM products WHERE product_no = ?", (product_no,))
        conn.commit()
        close_conn('product.db')
        self._load_data(self.search_edit.text().strip())

```
