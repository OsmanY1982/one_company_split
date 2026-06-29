# `modules/admin/admin_data_mgmt.py`

> 路径：`modules/admin/admin_data_mgmt.py` | 行数：391


---


```python
# -*- coding: utf-8 -*-
"""
管理员后台 - 云端数据全量管理组件
产品 · 订单 · 员工 · 财务 · 会员  五大模块，替代 Supabase 网页端
"""
import sys, os, sqlite3, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.paths import DATA_DIR
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QTabWidget, QLineEdit, QComboBox, QMessageBox,
    QHeaderView, QDialog, QFormLayout, QDialogButtonBox, QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

# ========================= 配置 =========================

CLOUD_TO_LOCAL_MAP = {
    "products": {"name":"name","category":"category","unit_price":"price","stock":"stock","status":"status","note":"description","created_at":"created_at"},
    "orders": {"order_no":"order_no","customer":"customer_name","product":"product_name","unit_price":"unit_price","total_price":"total_amount","quantity":"quantity","status":"status","note":"note","created_at":"created_at"},
    "staff": {"name":"name","position":"position","department":"department","phone":"phone","email":"email","salary":"salary","hire_date":"hire_date","status":"status","created_at":"created_at"},
    "finance": {"type":"type","category":"category","amount":"amount","date":"date","note":"description","order_no":"order_no","created_at":"created_at"},
    "user_memberships": {"username":"username","membership_type":"membership_type","activated_at":"activated_at","expires_at":"expires_at","activation_code":"activation_code"},
}

LOCAL_TO_CLOUD_MAP = {k: {v2:k2 for k2,v2 in v.items()} for k,v in CLOUD_TO_LOCAL_MAP.items()}

TABLES = {
    "products": {"db":"product.db","table":"products","cols":["name","category","price","cost","stock","unit","status","description","created_at","updated_at"], "headers":["名称","分类","售价","成本","库存","单位","状态","备注","创建时间","更新时间"]},
    "orders": {"db":"order.db","table":"orders","cols":["order_no","customer_name","product_name","quantity","unit_price","total_amount","status","payment_method","note","created_at","updated_at"], "headers":["订单号","客户","产品","数量","单价","总价","状态","支付方式","备注","创建","更新"]},
    "staff": {"db":"staff.db","table":"staff","cols":["name","position","department","phone","email","salary","hire_date","status","created_at","updated_at"], "headers":["姓名","职位","部门","电话","邮箱","薪资","入职","状态","创建","更新"]},
    "finance": {"db":"finance.db","table":"finance","cols":["type","category","amount","date","description","order_no","created_at"], "headers":["类型","分类","金额","日期","备注","关联订单","创建"]},
    "user_memberships": {"db":"users.db","table":"user_memberships","cols":["username","membership_type","activated_at","expires_at","activation_code"], "headers":["用户名","会员类型","激活时间","到期时间","激活码"]},
}

def _db_path(db_name):
    return os.path.join(DATA_DIR, db_name)

def _fetch_local(table_key):
    """查询本地 SQLite"""
    cfg = TABLES[table_key]
    try:
        conn = sqlite3.connect(_db_path(cfg["db"]))
        conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
        cur = conn.execute(f"SELECT {','.join(cfg['cols'])} FROM {cfg['table']}")
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        return []

def _exec_local(table_key, sql, params=()):
    cfg = TABLES[table_key]
    conn = sqlite3.connect(_db_path(cfg["db"]))
    conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()

def _delete_local(table_key, where_col, where_val):
    cfg = TABLES[table_key]
    conn = sqlite3.connect(_db_path(cfg["db"]))
    conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
    conn.execute(f"DELETE FROM {cfg['table']} WHERE {where_col}=?", (where_val,))
    conn.commit()
    conn.close()


# ========================= 编辑弹窗 =========================

class EditRowDialog(QDialog):
    def __init__(self, table_key, row_data=None, parent=None):
        super().__init__(parent)
        self.table_key = table_key
        self.cfg = TABLES[table_key]
        self.is_edit = row_data is not None
        self.setWindowTitle(f"{'编辑' if self.is_edit else '新增'} — {table_key}")
        self.setMinimumWidth(420)
        layout = QFormLayout(self)
        self.fields = {}

        skip_cols = {"created_at","updated_at","id"}
        for i, col in enumerate(self.cfg["cols"]):
            if col in skip_cols:
                continue
            le = QLineEdit()
            if row_data and i < len(row_data) and row_data[i] is not None:
                le.setText(str(row_data[i]))
            self.fields[col] = le
            header = self.cfg["headers"][i] if i < len(self.cfg["headers"]) else col
            layout.addRow(header, le)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def get_data(self):
        return {col: le.text().strip() for col, le in self.fields.items()}


# ========================= 单个数据表组件 =========================

class DataTableWidget(QWidget):
    def __init__(self, table_key, parent=None):
        super().__init__(parent)
        self.table_key = table_key
        self.cfg = TABLES[table_key]
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # 工具栏
        tb = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索...")
        self.search_box.setMaximumWidth(200)
        self.search_box.textChanged.connect(self.load_data)
        tb.addWidget(self.search_box)
        tb.addStretch()
        btn_add = QPushButton("➕ 新增")
        btn_add.clicked.connect(self.add_row)
        tb.addWidget(btn_add)
        btn_edit = QPushButton("✏️ 编辑")
        btn_edit.clicked.connect(self.edit_row)
        tb.addWidget(btn_edit)
        btn_del = QPushButton("🗑 删除")
        btn_del.setStyleSheet("color:red;")
        btn_del.clicked.connect(self.delete_row)
        tb.addWidget(btn_del)
        tb.addStretch()
        btn_pull = QPushButton("📥 从云端拉取")
        btn_pull.clicked.connect(self.pull_from_cloud)
        tb.addWidget(btn_pull)
        btn_push = QPushButton("☁️ 同步到云端")
        btn_push.clicked.connect(self.push_to_cloud)
        tb.addWidget(btn_push)
        layout.addLayout(tb)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.cfg["cols"]))
        self.table.setHorizontalHeaderLabels(self.cfg["headers"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # 统计
        self.lbl_count = QLabel("共 0 条")
        self.lbl_count.setStyleSheet("color: #a0aec0; padding:4px;")
        layout.addWidget(self.lbl_count)

        self.load_data()

    def load_data(self):
        rows = _fetch_local(self.table_key)
        keyword = self.search_box.text().strip().lower()
        if keyword:
            rows = [r for r in rows if any(keyword in str(c).lower() for c in r if c)]

        self.table.setRowCount(len(rows))
        for ri, row in enumerate(rows):
            for ci, val in enumerate(row):
                item = QTableWidgetItem(str(val) if val is not None else "")
                if ci == 0 and self.table_key == "finance":
                    if "支出" in str(val) or "expense" in str(val).lower():
                        item.setForeground(Qt.red)
                    elif "收入" in str(val) or "income" in str(val).lower():
                        item.setForeground(QColor("darkgreen"))
                self.table.setItem(ri, ci, item)
        self.lbl_count.setText(f"共 {self.table.rowCount()} 条")

    def add_row(self):
        dlg = EditRowDialog(self.table_key, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_data()
        try:
            cfg = TABLES[self.table_key]
            cols = list(data.keys())
            vals = list(data.values())
            placeholders = ",".join(["?"] * len(cols))
            _exec_local(self.table_key,
                        f"INSERT INTO {cfg['table']} ({','.join(cols)}) VALUES ({placeholders})", vals)
            self.load_data()
            QMessageBox.information(self, "成功", "已添加")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e)[:200])

    def edit_row(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self,"提示","请先选择一行")
            return
        row_data = []
        for ci in range(len(self.cfg["cols"])):
            item = self.table.item(row, ci)
            row_data.append(item.text() if item else "")
        dlg = EditRowDialog(self.table_key, row_data, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        data = dlg.get_data()
        try:
            cfg = TABLES[self.table_key]
            # 用第一列做 WHERE 条件
            pk_col = cfg["cols"][0]
            pk_val = row_data[0]
            sets = ",".join(f"{k}=?" for k in data.keys())
            vals = list(data.values()) + [pk_val]
            _exec_local(self.table_key, f"UPDATE {cfg['table']} SET {sets} WHERE {pk_col}=?", vals)
            self.load_data()
            QMessageBox.information(self, "成功", "已更新")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e)[:200])

    def delete_row(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self,"提示","请先选择一行")
            return
        item0 = self.table.item(row, 0)
        if not item0:
            return
        val = item0.text()
        cfg = TABLES[self.table_key]
        pk = cfg["cols"][0]
        reply = QMessageBox.question(self, "确认", f"确定删除 {pk}={val}？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            _delete_local(self.table_key, pk, val)
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e)[:200])

    def pull_from_cloud(self):
        try:
            from core.cloud_pull import _request
            mapping = CLOUD_TO_LOCAL_MAP.get(self.table_key, {})
            ok, cloud_rows = _request("GET", f"/rest/v1/{self.table_key}?select=*", service_key=True)
            if not ok or not isinstance(cloud_rows, list):
                QMessageBox.warning(self,"拉取失败", str(cloud_rows)[:200])
                return
            cfg = TABLES[self.table_key]
            conn = sqlite3.connect(_db_path(cfg["db"]))
            conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
            conn.execute(f"DELETE FROM {cfg['table']}")
            cols = [mapping.get(c, c) for c in cfg["cols"] if mapping.get(c, c) in cfg["cols"]]
            for crow in cloud_rows:
                loc = {}
                for cc, lc in mapping.items():
                    if cc in crow and lc in cfg["cols"]:
                        loc[lc] = crow[cc]
                if loc:
                    ins_cols = list(loc.keys())
                    ph = ",".join(["?"]*len(ins_cols))
                    conn.execute(f"INSERT INTO {cfg['table']} ({','.join(ins_cols)}) VALUES ({ph})",
                                 [loc[c] for c in ins_cols])
            conn.commit()
            conn.close()
            self.load_data()
            QMessageBox.information(self,"完成",f"已从云端拉取 {len(cloud_rows)} 条")
        except Exception as e:
            QMessageBox.critical(self,"错误", str(e)[:300])

    def push_to_cloud(self):
        """同步本地数据到云端：逐条 UPSERT"""
        try:
            from core.supabase_client import _request
            mapping = LOCAL_TO_CLOUD_MAP.get(self.table_key, {})
            rows = _fetch_local(self.table_key)
            cfg = TABLES[self.table_key]
            success = 0
            errors = []
            pk = cfg["cols"][0]

            for row in rows:
                row_dict = {}
                for i, col in enumerate(cfg["cols"]):
                    if i < len(row):
                        row_dict[col] = row[i]

                cloud_col = mapping.get(pk, pk)
                cloud_val = row_dict.get(pk, "")

                # 查云端是否有
                ok, existing = _request("GET",
                    f"/rest/v1/{self.table_key}?select=*&{cloud_col}=eq.{cloud_val}&limit=1",
                    service_key=True)
                cloud_row = existing[0] if ok and isinstance(existing, list) and existing else None

                payload = {}
                for lcol, ccol in mapping.items():
                    if lcol in row_dict:
                        payload[ccol] = row_dict[lcol]

                if cloud_row:
                    cloud_id = cloud_row.get("id", cloud_val)
                    ok2, _ = _request("PATCH",
                        f"/rest/v1/{self.table_key}?{mapping.get(pk,pk)}=eq.{cloud_val}",
                        payload, service_key=True)
                else:
                    ok2, _ = _request("POST", f"/rest/v1/{self.table_key}", payload, service_key=True)

                if ok2:
                    success += 1
                else:
                    errors.append(f"{cloud_val}: {str(_)[:80]}")

            msg = f"同步完成: {success}/{len(rows)} 条"
            if errors:
                msg += f"\n错误: {'; '.join(errors[:5])}"
            QMessageBox.information(self, "云端同步", msg)
        except Exception as e:
            QMessageBox.critical(self, "同步失败", str(e)[:300])


# ========================= 总组件 =========================

class AdminDataMgmtWidget(QWidget):
    """嵌入 AdminWindow 的多标签数据管理面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("业务数据管理 — 本地与云端双向同步")
        title.setFont(QFont("PingFang SC", 14, QFont.Bold))
        layout.addWidget(title)

        self.tabs = QTabWidget()
        self.tables = {}

        for key, label in [
            ("products", "📦 产品"),
            ("orders", "📋 订单"),
            ("staff", "👥 员工"),
            ("finance", "💰 财务"),
            ("user_memberships", "🌟 会员"),
        ]:
            w = DataTableWidget(key)
            self.tables[key] = w
            self.tabs.addTab(w, label)

        layout.addWidget(self.tabs)

        # 底部全局操作
        bottom = QHBoxLayout()
        bottom.addStretch()
        btn_all_pull = QPushButton("📥 从云端拉取全部")
        btn_all_pull.setMinimumHeight(36)
        btn_all_pull.clicked.connect(self.pull_all)
        bottom.addWidget(btn_all_pull)
        btn_all_push = QPushButton("☁️ 一键同步全部到云端")
        btn_all_push.setMinimumHeight(36)
        btn_all_push.clicked.connect(self.push_all)
        bottom.addWidget(btn_all_push)
        layout.addLayout(bottom)

    def pull_all(self):
        try:
            from core.cloud_pull import pull_all_from_cloud
            result = pull_all_from_cloud()
            for w in self.tables.values():
                w.load_data()
            QMessageBox.information(self, "拉取完成", result.get("summary", "完成"))
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e)[:300])

    def push_all(self):
        results = []
        for key, tab in self.tables.items():
            try:
                tab.push_to_cloud()
                results.append(f"{key}: OK")
            except Exception as e:
                results.append(f"{key}: {e}")
        # 不弹额外信息框，每个 tab 的 push_to_cloud 已经弹过了

    def load_all(self):
        """刷新所有子标签数据"""
        for w in self.tables.values():
            w.load_data()

```
