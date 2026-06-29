# `core/modules/personnel/wallet_window/_withdrawal_tab.py`

> 路径：`core/modules/personnel/wallet_window/_withdrawal_tab.py` | 行数：146


---


```python
# -*- coding: utf-8 -*-
"""
Withdrawal Tab Mixin — 提现审批页签（浅色主题）
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QAbstractItemView,
    QDialog, QFormLayout, QMessageBox,
)
from PyQt5.QtCore import Qt

from core.ui_components import PrimaryButton, SecondaryButton, DangerButton
from core.light_tool_theme import LIGHT_TOOL_STYLE
from core.modules.personnel.wallet_service import (
    get_pending_withdrawals, approve_withdrawal, reject_withdrawal,
)


class _WithdrawalTabMixin:
    """提现审批页签"""

    def _build_withdrawal_queue_tab(self):
        tab = QWidget()
        vl = QVBoxLayout(tab)
        vl.setContentsMargins(16, 10, 16, 16)

        header = QHBoxLayout()
        header.addWidget(QLabel("提现审批队列"))
        header.addStretch()
        self.lbl_selected_req = QLabel("请选择一条待审批记录")
        header.addWidget(self.lbl_selected_req)
        vl.addLayout(header)

        self.withdraw_table = QTableWidget()
        self.withdraw_table.setColumnCount(5)
        self.withdraw_table.setHorizontalHeaderLabels(
            ["ID", "用户ID", "金额", "备注", "状态"]
        )
        self.withdraw_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.withdraw_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.withdraw_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.withdraw_table.cellClicked.connect(self._on_withdrawal_selected)
        vl.addWidget(self.withdraw_table)

        footer = QHBoxLayout()
        btn_approve = PrimaryButton("批准")
        btn_approve.clicked.connect(self._approve_withdrawal)
        footer.addWidget(btn_approve)
        btn_reject = DangerButton("拒绝")
        btn_reject.clicked.connect(self._reject_withdrawal)
        footer.addWidget(btn_reject)
        footer.addStretch()
        btn_refresh = SecondaryButton("刷新")
        btn_refresh.clicked.connect(self.load_withdrawal_queue)
        footer.addWidget(btn_refresh)
        vl.addLayout(footer)

        self.tabs.addTab(tab, "提现审批")

    def load_withdrawal_queue(self):
        rows = get_pending_withdrawals()
        self.withdraw_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.withdraw_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.withdraw_table.setItem(i, 1, QTableWidgetItem(str(r.get("user_id", ""))))
            self.withdraw_table.setItem(i, 2, QTableWidgetItem(f"¥{r.get('amount', 0):.2f}"))
            self.withdraw_table.setItem(i, 3, QTableWidgetItem(str(r.get("description", ""))))

            status = r.get("status", "")
            status_item = QTableWidgetItem(str(status))
            if status == "pending":
                status_item.setForeground(Qt.yellow)
            elif status == "approved":
                status_item.setForeground(Qt.green)
            elif status == "rejected":
                status_item.setForeground(Qt.red)
            self.withdraw_table.setItem(i, 4, status_item)

    def _approve_withdrawal(self):
        row = self.withdraw_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一条提现申请")
            return
        req_id = int(self.withdraw_table.item(row, 0).text())
        user_id = self.withdraw_table.item(row, 1).text()
        amount = self.withdraw_table.item(row, 2).text()

        reply = QMessageBox.question(
            self, "确认审批",
            f"确认批准 {user_id} 的提现申请\n金额: {amount}\n\n"
            "批准后将从用户余额中扣除。",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        result = approve_withdrawal(req_id)
        if result["ok"]:
            QMessageBox.information(self, "已批准",
                                    result.get("message", ""))
            self.load_withdrawal_queue()
            self.load_wallets()
            self.load_dashboard()
            self.load_transactions()
        else:
            QMessageBox.warning(self, "审批失败",
                                result.get("error", "未知错误"))

    def _reject_withdrawal(self):
        row = self.withdraw_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一条提现申请")
            return
        req_id = int(self.withdraw_table.item(row, 0).text())
        user_id = self.withdraw_table.item(row, 1).text()

        dlg = QDialog(self)
        dlg.setWindowTitle(f"拒绝提现 #{req_id} - {user_id}")
        dlg.setMinimumWidth(350)
        dlg.setStyleSheet(LIGHT_TOOL_STYLE)
        layout = QFormLayout(dlg)

        reason_label = QLabel(
            "拒绝后冻结金额将自动解冻。\n请输入拒绝原因（可选）："
        )
        layout.addRow(reason_label)
        reason_input = QLabel()
        layout.addRow(reason_input)

        btn_confirm = DangerButton("确认拒绝")
        def do_reject():
            result = reject_withdrawal(req_id)
            if result["ok"]:
                QMessageBox.information(dlg, "已拒绝",
                                        result.get("message", ""))
                dlg.accept()
                self.load_withdrawal_queue()
                self.load_wallets()
                self.load_dashboard()
            else:
                QMessageBox.warning(dlg, "操作失败",
                                    result.get("error", "未知错误"))

        btn_confirm.clicked.connect(do_reject)
        layout.addRow(btn_confirm)
        dlg.exec_()

```
