# `modules/admin/admin_activation.py`

> 路径：`modules/admin/admin_activation.py` | 行数：403


---


```python
# -*- coding: utf-8 -*-
"""
管理员后台 - 激活码管理组件
嵌入 AdminWindow 的标签页，直接操作 activation_admin.db
"""
import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from core.paths import DATA_DIR
import secrets, json
from core.database import get_conn
from datetime import datetime, timedelta

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QComboBox, QLineEdit, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


CODE_TYPES = {
    "TRIAL":  {"name": "体验会员",  "days": 7, "price": 0},
    "PRO":    {"name": "VIP会员",  "days": 365, "price": 49},
    "VIP":    {"name": "钻石会员",  "days": 0, "price": 99},
}

# 旧类型兼容映射（后台管理老数据兼容、新UI只显示3种）
_LEGACY_TYPE_MAP = {
    "trial":   "体验会员",
    "month":   "VIP会员",
    "season":  "VIP会员",
    "year":    "VIP会员",
    "forever": "钻石会员",
}


def _get_display_name(user_type):
    """获取统一显示名称（兼容旧数据类型）"""
    if not user_type:
        return "-"
    ut = user_type
    # 优先查新 CODE_TYPES
    if ut in CODE_TYPES:
        return CODE_TYPES[ut]["name"]
    # 兼容旧类型
    if ut in _LEGACY_TYPE_MAP:
        return _LEGACY_TYPE_MAP[ut]
    # 大小写不敏感再试
    ut_upper = ut.upper()
    if ut_upper in CODE_TYPES:
        return CODE_TYPES[ut_upper]["name"]
    if ut.lower() in _LEGACY_TYPE_MAP:
        return _LEGACY_TYPE_MAP[ut.lower()]
    return ut


class AdminActivationWidget(QWidget):
    """管理员后台 - 激活码管理"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_codes()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # ── 统计卡片 ──
        stats_group = QGroupBox("激活码统计")
        stats_layout = QHBoxLayout(stats_group)
        self.stat_labels = {}
        for key, info in CODE_TYPES.items():
            card = QWidget()
            card.setStyleSheet("background:transparent; border-radius:6px; padding:8px; min-width:100px;")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(0, 0, 0, 0)
            lb = QLabel(info["name"])
            lb.setStyleSheet("color:#718096; font-size:11px;")
            cl.addWidget(lb)
            cnt = QLabel("0")
            cnt.setStyleSheet("color:#e0e0ff; font-size:18px; font-weight:bold;")
            cl.addWidget(cnt)
            self.stat_labels[key] = cnt
            stats_layout.addWidget(card)
        layout.addWidget(stats_group)

        # ── 生成区域 ──
        gen_group = QGroupBox("生成激活码")
        gen_layout = QHBoxLayout(gen_group)
        gen_layout.addWidget(QLabel("类型:"))
        self.type_combo = QComboBox()
        for k, v in CODE_TYPES.items():
            lbl = f"{v['name']}({'永久' if v['days']==0 else str(v['days'])+'天'})"
            self.type_combo.addItem(lbl, k)
        gen_layout.addWidget(self.type_combo)

        gen_layout.addWidget(QLabel("数量:"))
        self.count_combo = QComboBox()
        self.count_combo.addItems(["1", "5", "10", "20", "50", "100"])
        gen_layout.addWidget(self.count_combo)

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("备注（可选）")
        gen_layout.addWidget(self.note_input)

        btn_gen = QPushButton("生成激活码")
        btn_gen.setStyleSheet("background:#28a745; color:white; padding:8px 20px; font-weight:bold;")
        btn_gen.clicked.connect(self.generate_codes)
        gen_layout.addWidget(btn_gen)

        btn_gen10 = QPushButton("批量×10")
        btn_gen10.setStyleSheet("background:#17a2b8; color:white; padding:8px 16px;")
        btn_gen10.clicked.connect(lambda: self._quick_gen(10))
        gen_layout.addWidget(btn_gen10)
        gen_layout.addStretch()
        layout.addWidget(gen_group)

        # ── 操作栏 ──
        op_layout = QHBoxLayout()
        op_layout.addWidget(QLabel("筛选:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "未使用", "已使用", "已过期"])
        self.filter_combo.currentIndexChanged.connect(self.load_codes)
        op_layout.addWidget(self.filter_combo)

        op_layout.addWidget(QLabel("搜索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("激活码/账号")
        self.search_input.textChanged.connect(self.search_codes)
        op_layout.addWidget(self.search_input)
        op_layout.addStretch()

        btn_sync_cloud = QPushButton("☁️ 同步到云端")
        btn_sync_cloud.setStyleSheet("background:#6f42c1; color:white; padding:6px 14px; font-weight:bold;")
        btn_sync_cloud.clicked.connect(self._sync_to_cloud)
        op_layout.addWidget(btn_sync_cloud)

        btn_pull_cloud = QPushButton("📥 从云端拉取")
        btn_pull_cloud.setStyleSheet("background:#3182ce; color:white; padding:6px 14px;")
        btn_pull_cloud.clicked.connect(self._pull_from_cloud)
        op_layout.addWidget(btn_pull_cloud)

        btn_delete = QPushButton("🗑 删除选中")
        btn_delete.setStyleSheet("background:#dc3545; color:white; padding:6px 14px;")
        btn_delete.clicked.connect(self.delete_selected)
        op_layout.addWidget(btn_delete)

        btn_refresh = QPushButton("🔄 刷新")
        btn_refresh.clicked.connect(self.load_codes)
        op_layout.addWidget(btn_refresh)
        layout.addLayout(op_layout)

        # ── 表格 ──
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "激活码", "类型", "状态", "绑定账号", "生成时间", "到期时间"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)
        layout.addWidget(self.table)

    # ==================== 数据操作 ====================
    def _get_conn(self):
        """统一连接管理器"""
        return get_conn("activation_admin.db")

    def load_codes(self):
        """加载激活码列表"""
        try:
            conn = self._get_conn()
            cur = conn.cursor()

            # 确保表存在
            cur.execute('''CREATE TABLE IF NOT EXISTS admin_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                user_type TEXT DEFAULT 'month',
                status TEXT DEFAULT 'unused',
                bound_account TEXT,
                bound_machine TEXT,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_at TIMESTAMP,
                expires_at TIMESTAMP
            )''')
            conn.commit()

            filt = self.filter_combo.currentText()
            where = ""
            params = []
            if filt == "未使用":
                where = "WHERE status='unused'"
            elif filt == "已使用":
                where = "WHERE status='used'"
            elif filt == "已过期":
                where = "WHERE status='expired'"

            cur.execute(f"SELECT id,code,user_type,status,bound_account,created_at,expires_at FROM admin_codes {where} ORDER BY id DESC", params)
            rows = cur.fetchall()

            self.table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                for j, v in enumerate(r):
                    if j == 2:  # 类型列：用统一显示名称
                        item = QTableWidgetItem(_get_display_name(v))
                    else:
                        item = QTableWidgetItem(str(v) if v else "")
                    if j == 3:  # 状态列着色
                        if v == "unused":
                            item.setForeground(Qt.darkGreen)
                        elif v == "used":
                            item.setForeground(Qt.blue)
                        elif v == "expired":
                            item.setForeground(Qt.red)
                    self.table.setItem(i, j, item)

            # 统计（兼容旧类型映射到新分类）
            _STAT_MAP = {
                "TRIAL": "TRIAL", "trial": "TRIAL",
                "PRO": "PRO", "month": "PRO", "season": "PRO", "year": "PRO",
                "VIP": "VIP", "forever": "VIP",
            }
            stats = {"TRIAL": 0, "PRO": 0, "VIP": 0}
            cur.execute("SELECT user_type, COUNT(*) FROM admin_codes GROUP BY user_type")
            for ut, cnt in cur.fetchall():
                mapped = _STAT_MAP.get(ut, "PRO")  # 未知类型归入VIP会员
                stats[mapped] = stats.get(mapped, 0) + cnt
            for k, lbl in self.stat_labels.items():
                lbl.setText(str(stats.get(k, 0)))

        except Exception as e:
            print(f"加载激活码失败: {e}")

    def search_codes(self):
        """搜索激活码"""
        txt = self.search_input.text().strip()
        if not txt:
            self.load_codes()
            return
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            like = f"%{txt}%"
            cur.execute(
                "SELECT id,code,user_type,status,bound_account,created_at,expires_at FROM admin_codes "
                "WHERE code LIKE ? OR bound_account LIKE ? OR user_type LIKE ? ORDER BY id DESC",
                (like, like, like)
            )
            rows = cur.fetchall()
            self.table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                for j, v in enumerate(r):
                    if j == 2:
                        item = QTableWidgetItem(_get_display_name(v))
                    else:
                        item = QTableWidgetItem(str(v) if v else "")
                    if j == 3:
                        if v == "unused": item.setForeground(Qt.darkGreen)
                        elif v == "used": item.setForeground(Qt.blue)
                    self.table.setItem(i, j, item)

        except Exception as e:
            print(f"搜索失败: {e}")

    def _make_code(self, prefix, length=12):
        raw = secrets.token_hex(length // 2)
        return f"{prefix}{raw[:4].upper()}{raw[4:8].upper()}{raw[8:12].upper()}"

    def _quick_gen(self, count):
        self.count_combo.setCurrentText(str(count))
        self.generate_codes()

    def generate_codes(self):
        """生成激活码"""
        code_type = self.type_combo.currentData()
        count = int(self.count_combo.currentText())
        note = self.note_input.text().strip()
        info = CODE_TYPES.get(code_type, CODE_TYPES["month"])
        days = info["days"]

        conn = self._get_conn()
        cur = conn.cursor()
        generated = []

        for _ in range(count):
            code = self._make_code(code_type)
            expires = None
            if days > 0:
                expires = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            try:
                cur.execute(
                    "INSERT INTO admin_codes (code, user_type, status, note, expires_at, created_at) VALUES (?,?,?,?,?,?)",
                    (code, code_type, "unused", note, expires, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                generated.append(code)
            except Exception:
                continue  # 碰撞重试

        conn.commit()


        if generated:
            QMessageBox.information(self, "生成成功",
                f"✅ 已生成 {len(generated)} 个 {info['name']}激活码")
            self.load_codes()
        else:
            QMessageBox.warning(self, "生成失败", "未能生成任何激活码")

    def delete_selected(self):
        """删除选中的激活码"""
        rows = set(idx.row() for idx in self.table.selectedIndexes())
        if not rows:
            QMessageBox.warning(self, "提示", "请先选中要删除的激活码")
            return
        reply = QMessageBox.question(self, "确认删除",
            f"确定要删除 {len(rows)} 个激活码吗？\n此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        try:
            conn = self._get_conn()
            cur = conn.cursor()
            for r in rows:
                cid = self.table.item(r, 0).text()
                cur.execute("DELETE FROM admin_codes WHERE id=?", (cid,))
            conn.commit()

            self.load_codes()
        except Exception as e:
            QMessageBox.warning(self, "删除失败", str(e)[:200])

    # ==================== 云端同步 ====================
    def _sync_to_cloud(self):
        """同步本地激活码 → 云端"""
        try:
            from core.supabase_client import _request
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM admin_codes")
            rows = cur.fetchall()
            col_names = [d[0] for d in cur.description]


            if not rows:
                QMessageBox.information(self, "提示", "没有需要同步的激活码")
                return

            # 先拉云端已有codes做去重
            ok, cloud_data = _request("GET", "/rest/v1/activation_codes?select=code", service_key=True)
            cloud_codes = set()
            if ok and isinstance(cloud_data, list):
                cloud_codes = {r.get("code", "") for r in cloud_data}

            success = 0
            skip = 0
            for row in rows:
                item = dict(zip(col_names, row))
                code = item.get("code", "")
                if code in cloud_codes:
                    skip += 1
                    continue
                # 去除 id 列（云端自动生成UUID）
                item.pop("id", None)
                # 清理值为 None 的字段
                payload = {k: v for k, v in item.items() if v is not None}
                ok, _ = _request("POST", "/rest/v1/activation_codes", payload, service_key=True)
                if ok:
                    success += 1

            msg = f"✅ 同步完成: 新增 {success} 个, 跳过 {skip} 个（已存在）"
            QMessageBox.information(self, "同步成功", msg)
        except Exception as e:
            QMessageBox.critical(self, "同步失败", str(e)[:200])

    def _pull_from_cloud(self):
        """从云端拉取激活码 → 本地"""
        reply = QMessageBox.question(self, "确认拉取",
            "将从云端拉取激活码到本地，覆盖本地数据。\n确认继续？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        try:
            from core.cloud_pull import pull_activation_codes
            cnt = pull_activation_codes()
            QMessageBox.information(self, "拉取完成", f"✅ 从云端拉取 {cnt} 个激活码")
            self.load_codes()
        except Exception as e:
            QMessageBox.critical(self, "拉取失败", str(e)[:200])


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = AdminActivationWidget()
    w.show()
    app.exec_()

```
