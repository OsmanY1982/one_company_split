# -*- coding: utf-8 -*-
"""
Wallets Tab Mixin — 钱包列表页签（浅色主题）
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLabel, QLineEdit, QAbstractItemView,
    QMessageBox,
)

from core.ui_components import PrimaryButton, SecondaryButton, DangerButton
from core.modules.personnel.wallet_service import (
    get_all_wallets, get_wallet,
)


class _WalletsTabMixin:
    """钱包列表页签"""

    def _build_wallets_tab(self):
        tab = QWidget()
        vl = QVBoxLayout(tab)
        vl.setContentsMargins(16, 10, 16, 16)

        # 操作区域
        op_layout = QHBoxLayout()
        op_layout.addWidget(QLabel("筛选用户ID:"))
        self.wallet_search = QLineEdit()
        self.wallet_search.setPlaceholderText("输入用户ID筛选")
        self.wallet_search.setMaximumWidth(180)
        self.wallet_search.textChanged.connect(self.load_wallets)
        op_layout.addWidget(self.wallet_search)
        op_layout.addStretch()
        btn_create = PrimaryButton("创建钱包")
        btn_create.clicked.connect(self._show_create_dialog)
        op_layout.addWidget(btn_create)
        btn_recharge = SecondaryButton("充值")
        btn_recharge.clicked.connect(self._show_recharge_dialog)
        op_layout.addWidget(btn_recharge)
        btn_withdraw_req = SecondaryButton("提现申请")
        btn_withdraw_req.clicked.connect(self._show_withdrawal_request_dialog)
        op_layout.addWidget(btn_withdraw_req)
        btn_transfer = SecondaryButton("转账")
        btn_transfer.clicked.connect(self._show_transfer_dialog)
        op_layout.addWidget(btn_transfer)
        btn_commission = SecondaryButton("发放佣金")
        btn_commission.clicked.connect(self._show_commission_dialog)
        op_layout.addWidget(btn_commission)
        vl.addLayout(op_layout)

        # 表格
        self.wallet_table = QTableWidget()
        self.wallet_table.setColumnCount(6)
        self.wallet_table.setHorizontalHeaderLabels(
            ["ID", "用户ID", "余额", "冻结金额", "状态", "创建时间"]
        )
        self.wallet_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.wallet_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.wallet_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.wallet_table.setSortingEnabled(True)
        self.wallet_table.cellClicked.connect(self._on_wallet_selected)
        vl.addWidget(self.wallet_table)

        # 底部按钮
        footer = QHBoxLayout()
        btn_toggle = SecondaryButton("封禁/激活")
        btn_toggle.clicked.connect(self._toggle_status)
        footer.addWidget(btn_toggle)
        btn_delete = DangerButton("删除钱包")
        btn_delete.clicked.connect(self._do_delete_wallet)
        footer.addWidget(btn_delete)
        footer.addStretch()
        footer.addWidget(QLabel("💡 选中钱包后可充值/提现/转账/发佣金"))
        vl.addLayout(footer)

        self.tabs.addTab(tab, "钱包列表")

    def load_wallets(self):
        keyword = self.wallet_search.text().strip() or None
        rows = get_all_wallets(keyword)
        self.wallet_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.wallet_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.wallet_table.setItem(i, 1, QTableWidgetItem(str(r["user_id"])))
            self.wallet_table.setItem(i, 2, QTableWidgetItem(f"{r['balance']:.2f}"))
            self.wallet_table.setItem(i, 3, QTableWidgetItem(f"{r['frozen_amount']:.2f}"))
            self.wallet_table.setItem(i, 4, QTableWidgetItem(str(r["status"])))
            self.wallet_table.setItem(i, 5, QTableWidgetItem(str(r.get("created_at", ""))))
