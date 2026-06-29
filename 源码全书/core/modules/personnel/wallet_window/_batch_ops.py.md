# `core/modules/personnel/wallet_window/_batch_ops.py`

> 路径：`core/modules/personnel/wallet_window/_batch_ops.py` | 行数：253


---


```python
# -*- coding: utf-8 -*-
"""
Batch Operations Mixin — 批量操作页签（浅色主题）
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt

from core.ui_components import PrimaryButton, DangerButton
from core.modules.personnel.wallet_service import (
    recharge, transfer, add_commission,
)


class _BatchOpsMixin:
    """批量操作页签"""

    def _init_batch_tab(self, tab: QWidget):
        vl = QVBoxLayout(tab)
        vl.setContentsMargins(15, 15, 15, 15)
        vl.addWidget(QLabel("<b>📦 批量操作</b> — 可一次性向多个用户充值/转账/发佣金"))
        vl.addSpacing(5)

        # ── 批量充值 ──
        group_rech = QGroupBox("💰 批量充值")
        rech_layout = QVBoxLayout()

        rech_table_layout = QHBoxLayout()
        self.batch_rech_table = QTableWidget(0, 3)
        self.batch_rech_table.setHorizontalHeaderLabels(["用户ID", "金额", "备注"])
        self.batch_rech_table.setMinimumHeight(120)
        self.batch_rech_table.horizontalHeader().setStretchLastSection(True)
        rech_table_layout.addWidget(self.batch_rech_table)

        rech_btn_col = QVBoxLayout()
        btn_add_rech = QPushButton("➕ 添加行")
        btn_add_rech.clicked.connect(
            lambda: self._add_batch_row(self.batch_rech_table))
        btn_del_rech = QPushButton("🗑 删除选中")
        btn_del_rech.clicked.connect(
            lambda: self._del_batch_row(self.batch_rech_table))
        rech_btn_col.addWidget(btn_add_rech)
        rech_btn_col.addWidget(btn_del_rech)
        rech_btn_col.addStretch()
        rech_table_layout.addLayout(rech_btn_col)
        rech_layout.addLayout(rech_table_layout)

        rech_footer = QHBoxLayout()
        rech_footer.addStretch()
        btn_rech_all = PrimaryButton("🚀 执行批量充值")
        btn_rech_all.clicked.connect(self._do_batch_recharge)
        rech_footer.addWidget(btn_rech_all)
        rech_layout.addLayout(rech_footer)
        group_rech.setLayout(rech_layout)
        vl.addWidget(group_rech)

        # ── 批量转账 ──
        group_trans = QGroupBox("🔄 批量转账（单账户→多人）")
        trans_layout = QVBoxLayout()

        from_layout = QHBoxLayout()
        from_layout.addWidget(QLabel("转出用户ID:"))
        self.batch_trans_from = QLineEdit()
        self.batch_trans_from.setPlaceholderText("输入转出方用户ID")
        from_layout.addWidget(self.batch_trans_from)
        from_layout.addWidget(QLabel("说明:"))
        self.batch_trans_desc = QLineEdit()
        self.batch_trans_desc.setPlaceholderText("统一备注（可选）")
        from_layout.addWidget(self.batch_trans_desc)
        trans_layout.addLayout(from_layout)

        trans_table_layout = QHBoxLayout()
        self.batch_trans_table = QTableWidget(0, 2)
        self.batch_trans_table.setHorizontalHeaderLabels(["收款用户ID", "金额"])
        self.batch_trans_table.setMinimumHeight(120)
        trans_table_layout.addWidget(self.batch_trans_table)

        trans_btn_col = QVBoxLayout()
        btn_add_trans = QPushButton("➕ 添加行")
        btn_add_trans.clicked.connect(
            lambda: self._add_batch_row(self.batch_trans_table, cols=2))
        btn_del_trans = QPushButton("🗑 删除选中")
        btn_del_trans.clicked.connect(
            lambda: self._del_batch_row(self.batch_trans_table))
        trans_btn_col.addWidget(btn_add_trans)
        trans_btn_col.addWidget(btn_del_trans)
        trans_btn_col.addStretch()
        trans_table_layout.addLayout(trans_btn_col)
        trans_layout.addLayout(trans_table_layout)

        trans_footer = QHBoxLayout()
        lbl_trans_hint = QLabel("💡 提示：总金额不能超过转出用户可用余额")
        lbl_trans_hint.setStyleSheet("color: #6b7280; font-size: 12px;")
        trans_footer.addWidget(lbl_trans_hint)
        trans_footer.addStretch()
        btn_trans_all = PrimaryButton("🚀 执行批量转账")
        btn_trans_all.clicked.connect(self._do_batch_transfer)
        trans_footer.addWidget(btn_trans_all)
        trans_layout.addLayout(trans_footer)
        group_trans.setLayout(trans_layout)
        vl.addWidget(group_trans)

        # ── 批量佣金 ──
        group_comm = QGroupBox("🎯 批量发放佣金")
        comm_layout = QVBoxLayout()

        comm_table_layout = QHBoxLayout()
        self.batch_comm_table = QTableWidget(0, 3)
        self.batch_comm_table.setHorizontalHeaderLabels(["用户ID", "佣金金额", "说明"])
        self.batch_comm_table.setMinimumHeight(120)
        comm_table_layout.addWidget(self.batch_comm_table)

        comm_btn_col = QVBoxLayout()
        btn_add_comm = QPushButton("➕ 添加行")
        btn_add_comm.clicked.connect(
            lambda: self._add_batch_row(self.batch_comm_table))
        btn_del_comm = QPushButton("🗑 删除选中")
        btn_del_comm.clicked.connect(
            lambda: self._del_batch_row(self.batch_comm_table))
        comm_btn_col.addWidget(btn_add_comm)
        comm_btn_col.addWidget(btn_del_comm)
        comm_btn_col.addStretch()
        comm_table_layout.addLayout(comm_btn_col)
        comm_layout.addLayout(comm_table_layout)

        comm_footer = QHBoxLayout()
        comm_footer.addStretch()
        btn_comm_all = PrimaryButton("🚀 执行批量佣金")
        btn_comm_all.clicked.connect(self._do_batch_commission)
        comm_footer.addWidget(btn_comm_all)
        comm_layout.addLayout(comm_footer)
        group_comm.setLayout(comm_layout)
        vl.addWidget(group_comm)

        vl.addStretch()

    # ──────────────────────────────────────
    #  批量操作辅助方法
    # ──────────────────────────────────────
    def _add_batch_row(self, table: 'QTableWidget', cols: int = None):
        if cols is None:
            cols = table.columnCount()
        table.insertRow(table.rowCount())
        for col in range(cols):
            table.setCellWidget(table.rowCount() - 1, col, QLineEdit())

    def _del_batch_row(self, table: 'QTableWidget'):
        row = table.currentRow()
        if row >= 0:
            table.removeRow(row)

    def _table_to_dicts(self, table: 'QTableWidget',
                        col_keys: list) -> list:
        items = []
        for row in range(table.rowCount()):
            row_data = {}
            for col, key in enumerate(col_keys):
                w = table.cellWidget(row, col)
                if isinstance(w, QLineEdit):
                    val = w.text().strip()
                else:
                    val = ""
                row_data[key] = val
            if any(v for v in row_data.values()):
                items.append(row_data)
        return items

    def _do_batch_recharge(self):
        items = self._table_to_dicts(
            self.batch_rech_table, ["user_id", "amount", "description"])
        if not items:
            QMessageBox.information(self, "提示", "请先添加充值记录（至少填一行）")
            return
        results = []
        for it in items:
            try:
                amount = float(it["amount"])
                desc = it["description"] or "批量充值"
                r = recharge(it["user_id"], amount, desc)
                results.append({"user_id": it["user_id"], "ok": r["ok"],
                                "error": r.get("error", "")})
            except ValueError:
                results.append({"user_id": it["user_id"], "ok": False,
                                "error": "金额格式错误"})
            except Exception as e:
                results.append({"user_id": it["user_id"], "ok": False,
                                "error": str(e)})
        self._show_batch_result("充值", results)
        self.load_wallets()
        self.load_dashboard()

    def _do_batch_transfer(self):
        from_user = self.batch_trans_from.text().strip()
        if not from_user:
            QMessageBox.information(self, "提示", "请填写转出用户ID")
            return
        desc = self.batch_trans_desc.text().strip()
        items = self._table_to_dicts(
            self.batch_trans_table, ["user_id", "amount"])
        if not items:
            QMessageBox.information(self, "提示", "请先添加转账记录")
            return
        results = []
        for it in items:
            try:
                amount = float(it["amount"])
                r = transfer(from_user, it["user_id"], amount, desc)
                results.append({"user_id": it["user_id"], "ok": r["ok"],
                                "error": r.get("error", "")})
            except ValueError:
                results.append({"user_id": it["user_id"], "ok": False,
                                "error": "金额格式错误"})
            except Exception as e:
                results.append({"user_id": it["user_id"], "ok": False,
                                "error": str(e)})
        self._show_batch_result("批量转账", results)
        self.load_wallets()
        self.load_dashboard()

    def _do_batch_commission(self):
        items = self._table_to_dicts(
            self.batch_comm_table, ["user_id", "amount", "description"])
        if not items:
            QMessageBox.information(self, "提示", "请先添加佣金记录")
            return
        results = []
        for it in items:
            try:
                amount = float(it["amount"])
                desc = it["description"] or "批量佣金"
                r = add_commission(it["user_id"], amount, desc)
                results.append({"user_id": it["user_id"], "ok": r["ok"],
                                "error": r.get("error", "")})
            except ValueError:
                results.append({"user_id": it["user_id"], "ok": False,
                                "error": "金额格式错误"})
            except Exception as e:
                results.append({"user_id": it["user_id"], "ok": False,
                                "error": str(e)})
        self._show_batch_result("佣金发放", results)
        self.load_wallets()
        self.load_dashboard()

    def _show_batch_result(self, operation: str, results: list):
        succeeded = sum(1 for r in results if r.get("ok"))
        failed = len(results) - succeeded
        lines = [f"✅ 成功: {succeeded} 条 | ❌ 失败: {failed} 条\n"]
        for r in results:
            status = "✅" if r.get("ok") else f"❌ {r.get('error', '')}"
            lines.append(f"  {r.get('user_id', '?')} → {status}")
        QMessageBox.information(self, f"{operation}结果", "\n".join(lines))

```
