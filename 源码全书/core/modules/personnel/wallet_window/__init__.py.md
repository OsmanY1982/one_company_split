# `core/modules/personnel/wallet_window/__init__.py`

> 路径：`core/modules/personnel/wallet_window/__init__.py` | 行数：295


---


```python
# -*- coding: utf-8 -*-
"""
钱包管理界面 — 模块化拆分（浅色主题）
通过 Mixin 多重继承组合。
"""
import csv
import sys

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QDialog, QFormLayout,
    QLineEdit, QTabWidget, QAbstractItemView, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.ui_components import PrimaryButton, SecondaryButton, DangerButton
from core.light_tool_theme import LIGHT_TOOL_STYLE
from core.modules.personnel.wallet_service import (
    init_db, get_wallet, get_pending_withdrawals,
    update_wallet_status, delete_wallet,
)
from core.modules.personnel.wallet_window._stat_card import StatCard
from core.modules.personnel.wallet_window._dashboard_tab import _DashboardTabMixin
from core.modules.personnel.wallet_window._wallets_tab import _WalletsTabMixin
from core.modules.personnel.wallet_window._transactions_tab import _TransactionsTabMixin
from core.modules.personnel.wallet_window._withdrawal_tab import _WithdrawalTabMixin
from core.modules.personnel.wallet_window._batch_ops import _BatchOpsMixin
from core.modules.personnel.wallet_window._dialogs import _DialogsMixin
from core.modules.personnel.wallet_window._address_book import _AddressBookMixin


class WalletWindow(
    QMainWindow,
    _DashboardTabMixin,
    _WalletsTabMixin,
    _TransactionsTabMixin,
    _WithdrawalTabMixin,
    _BatchOpsMixin,
    _DialogsMixin,
    _AddressBookMixin,
):
    """钱包管理主窗口 — Mixin 多重继承"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("钱包管理")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(LIGHT_TOOL_STYLE)
        init_db()
        self.init_ui()
        self.load_dashboard()
        self.load_wallets()
        self.load_transactions()

    # ──────────────────────────────────────
    #  UI 初始化
    # ──────────────────────────────────────
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        # 标题栏
        top_layout = QHBoxLayout()
        title = QLabel("💰 钱包管理")
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        top_layout.addWidget(title)
        top_layout.addStretch()
        btn_export = PrimaryButton("📥 导出 CSV")
        btn_export.clicked.connect(self._do_export_csv)
        top_layout.addWidget(btn_export)
        btn_back = SecondaryButton("返回主控")
        btn_back.clicked.connect(self._go_back)
        top_layout.addWidget(btn_back)
        layout.addLayout(top_layout)

        # Tab 控件
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # ── Tab 0: 📊 看板 ──
        self._build_dashboard_tab()

        # ── Tab 1: 💼 钱包列表 ──
        self._build_wallets_tab()

        # ── Tab 2: 📋 交易记录 ──
        self._build_transactions_tab()

        # ── Tab 3: ⏳ 提现审批 ──
        self._build_withdrawal_queue_tab()

        # ── 批量操作 Tab ──
        tab_batch = QWidget()
        self.tabs.addTab(tab_batch, "批量操作")
        self._init_batch_tab(tab_batch)

        # ── 地址簿 Tab ──
        tab_addr = QWidget()
        tal = QVBoxLayout(tab_addr)
        tal.setContentsMargins(10, 10, 10, 10)
        addr_h = QHBoxLayout()
        addr_h.addWidget(QLabel("地址簿"))
        addr_h.addStretch()
        self.addr_owner_input = QLineEdit()
        self.addr_owner_input.setPlaceholderText("所属用户")
        self.addr_owner_input.setMaximumWidth(150)
        self.addr_owner_input.textChanged.connect(self._load_address_book)
        addr_h.addWidget(self.addr_owner_input)
        btn_add_addr = PrimaryButton("添加地址")
        btn_add_addr.clicked.connect(self._show_add_address_dialog)
        addr_h.addWidget(btn_add_addr)
        btn_edit_addr = SecondaryButton("编辑地址")
        btn_edit_addr.clicked.connect(self._edit_address)
        tal.addLayout(addr_h)
        self.addr_table = QTableWidget()
        self.addr_table.setColumnCount(5)
        self.addr_table.setHorizontalHeaderLabels(
            ["ID", "标签", "地址", "类型", "备注"]
        )
        self.addr_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.addr_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.addr_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tal.addWidget(self.addr_table)
        addr_btn_h = QHBoxLayout()
        btn_del_addr = DangerButton("删除选中")
        btn_del_addr.clicked.connect(self._delete_address)
        addr_btn_h.addWidget(btn_del_addr)
        addr_btn_h.addStretch()
        tal.addLayout(addr_btn_h)
        self.tabs.addTab(tab_addr, "地址簿")

    # ──────────────────────────────────────
    #  选择器 & 事件
    # ──────────────────────────────────────
    def _on_wallet_selected(self):
        pass

    def _on_withdrawal_selected(self):
        row = self.withdraw_table.currentRow()
        if row < 0:
            self.lbl_selected_req.setText("请选择一条待审批记录")
            return
        req_id = self.withdraw_table.item(row, 0).text()
        user_id = self.withdraw_table.item(row, 1).text()
        amount = self.withdraw_table.item(row, 2).text()
        status = self.withdraw_table.item(row, 4).text()
        if status == "pending":
            self.lbl_selected_req.setText(
                f"已选: #{req_id} | {user_id} | ¥{amount}"
            )
        else:
            self.lbl_selected_req.setText(f"#{req_id} - {status}")

    def _get_selected_wallet(self):
        row = self.wallet_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先在表格中选择一个钱包")
            return None
        return (
            int(self.wallet_table.item(row, 0).text()),
            self.wallet_table.item(row, 1).text(),
        )

    def _toggle_status(self):
        sel = self._get_selected_wallet()
        if not sel:
            return
        wallet_id, user_id = sel
        w = get_wallet(user_id)
        current = w.get("status", "active")
        new_status = "banned" if current == "active" else "active"
        msg = (f"确认要将用户 {user_id} 的钱包"
               + ("封禁" if new_status == "banned" else "激活") + "？")
        reply = QMessageBox.question(
            self, "确认", msg, QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            result = update_wallet_status(user_id, new_status)
            if result["ok"]:
                QMessageBox.information(
                    self, "成功",
                    f"钱包已{'封禁' if new_status == 'banned' else '激活'}"
                )
                self.load_wallets()
            else:
                QMessageBox.warning(self, "错误",
                                    result.get("error", "操作失败"))

    def _do_delete_wallet(self):
        sel = self._get_selected_wallet()
        if not sel:
            return
        wallet_id, user_id = sel
        w = get_wallet(user_id)
        if not w:
            return
        balance = w.get("balance", 0)
        frozen = w.get("frozen_amount", 0)
        pending = get_pending_withdrawals()
        has_pending = any(p["user_id"] == user_id for p in pending)
        if has_pending:
            QMessageBox.information(
                self, "无法删除",
                f"用户 {user_id} 有待审批的提现申请，"
                "请先在「提现审批」中处理后再删除。"
            )
            return
        if frozen != 0:
            reply = QMessageBox.question(
                self, "⚠️ 有冻结金额",
                f"用户 {user_id} 的钱包有冻结金额 ¥{frozen:.2f}。\n"
                f"强制删除将清零冻结金额，确定要继续吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            result = delete_wallet(user_id, force=True)
        elif balance != 0:
            reply = QMessageBox.question(
                self, "⚠️ 有余额",
                f"用户 {user_id} 的钱包余额为 ¥{balance:.2f}。\n"
                f"强制删除将清零余额，确定要继续吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            result = delete_wallet(user_id, force=True)
        else:
            reply = QMessageBox.question(
                self, "确认删除",
                f"确定要删除用户 {user_id} 的钱包吗？\n（此操作不可恢复）",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            result = delete_wallet(user_id, force=False)
        if result["ok"]:
            QMessageBox.information(self, "成功", f"钱包 {user_id} 已删除")
            self.load_wallets()
            self.load_dashboard()
        else:
            QMessageBox.warning(self, "删除失败", result.get("error", "未知错误"))

    def _go_back(self):
        self.close()
        parent = self.parent()
        if parent and hasattr(parent, 'show') and callable(parent.show):
            parent.show()

    def _do_export_csv(self):
        """导出钱包数据为 CSV 文件"""
        path, _ = QFileDialog.getSaveFileName(
            self, "导出钱包数据", "wallets_export.csv",
            "CSV 文件 (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                # 导出钱包列表
                writer.writerow(["钱包列表"])
                writer.writerow(["ID", "用户ID", "余额", "冻结金额", "状态", "创建时间"])
                for row_idx in range(self.wallet_table.rowCount()):
                    row_data = []
                    for col_idx in range(self.wallet_table.columnCount()):
                        item = self.wallet_table.item(row_idx, col_idx)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
                writer.writerow([])
                # 导出交易记录
                writer.writerow(["交易记录"])
                writer.writerow(["ID", "钱包ID", "类型", "金额", "方向", "时间"])
                for row_idx in range(self.tx_table.rowCount()):
                    row_data = []
                    for col_idx in range(self.tx_table.columnCount()):
                        item = self.tx_table.item(row_idx, col_idx)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "导出成功", f"数据已导出到:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", str(e))


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = WalletWindow()
    w.show()
    sys.exit(app.exec_())

```
