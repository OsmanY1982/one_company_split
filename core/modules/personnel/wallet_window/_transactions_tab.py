# -*- coding: utf-8 -*-
"""
Transactions Tab Mixin — 交易记录页签（浅色主题）
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QLineEdit, QComboBox,
    QAbstractItemView,
)

from core.ui_components import SecondaryButton
from core.modules.personnel.wallet_service import get_transactions

PAGE_SIZE = 50


class _TransactionsTabMixin:
    """交易记录页签"""

    def _build_transactions_tab(self):
        tab = QWidget()
        vl = QVBoxLayout(tab)
        vl.setContentsMargins(16, 10, 16, 16)

        # 筛选栏
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("用户ID:"))
        self.tx_user_input = QLineEdit()
        self.tx_user_input.setPlaceholderText("输入用户ID筛选")
        self.tx_user_input.setMaximumWidth(150)
        filter_layout.addWidget(self.tx_user_input)

        filter_layout.addWidget(QLabel("类型:"))
        self.tx_type_combo = QComboBox()
        self.tx_type_combo.addItems([
            "全部", "recharge", "withdrawal", "transfer",
            "commission", "adjustment"
        ])
        self.tx_type_combo.setMaximumWidth(120)
        filter_layout.addWidget(self.tx_type_combo)

        filter_layout.addStretch()
        btn_search = SecondaryButton("🔍 查询")
        btn_search.clicked.connect(self.load_transactions)
        filter_layout.addWidget(btn_search)
        btn_clear = SecondaryButton("清除筛选")
        btn_clear.clicked.connect(self._clear_tx_filter)
        filter_layout.addWidget(btn_clear)
        vl.addLayout(filter_layout)

        # 表格
        self.tx_table = QTableWidget()
        self.tx_table.setColumnCount(6)
        self.tx_table.setHorizontalHeaderLabels(
            ["ID", "钱包ID", "类型", "金额", "方向", "时间"]
        )
        self.tx_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tx_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tx_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tx_table.setSortingEnabled(True)
        vl.addWidget(self.tx_table)

        # 分页
        page_layout = QHBoxLayout()
        page_layout.addStretch()
        self.btn_prev_page = SecondaryButton("◀ 上一页")
        self.btn_prev_page.clicked.connect(self._prev_page)
        page_layout.addWidget(self.btn_prev_page)
        self.lbl_page_info = QLabel("第 1 页")
        page_layout.addWidget(self.lbl_page_info)
        self.btn_next_page = SecondaryButton("下一页 ▶")
        self.btn_next_page.clicked.connect(self._next_page)
        page_layout.addWidget(self.btn_next_page)
        vl.addLayout(page_layout)
        self._tx_offset = 0

        self.tabs.addTab(tab, "交易记录")

    def load_transactions(self):
        keyword = self.tx_user_input.text().strip() or None
        tx_type = self.tx_type_combo.currentText()
        if tx_type == "全部":
            tx_type = None

        rows = get_transactions(
            keyword=keyword,
            txn_type=tx_type or "",
            limit=PAGE_SIZE,
            offset=self._tx_offset,
        )

        self.tx_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.tx_table.setItem(i, 0, QTableWidgetItem(str(r.get("id", ""))))
            self.tx_table.setItem(i, 1, QTableWidgetItem(str(r.get("wallet_id", ""))))
            self.tx_table.setItem(i, 2, QTableWidgetItem(str(r.get("txn_type", ""))))
            amount = r.get("amount", 0)
            self.tx_table.setItem(i, 3, QTableWidgetItem(f"¥{amount:+.2f}"))
            self.tx_table.setItem(i, 4, QTableWidgetItem(str(r.get("direction", ""))))
            self.tx_table.setItem(i, 5, QTableWidgetItem(str(r.get("created_at", ""))))

        has_more = len(rows) == PAGE_SIZE
        page_num = (self._tx_offset // PAGE_SIZE) + 1
        self.lbl_page_info.setText(f"第 {page_num} 页")
        self.btn_prev_page.setEnabled(self._tx_offset > 0)
        self.btn_next_page.setEnabled(has_more)

    def _clear_tx_filter(self):
        self.tx_user_input.clear()
        self.tx_type_combo.setCurrentIndex(0)
        self._tx_offset = 0
        self.load_transactions()

    def _prev_page(self):
        if self._tx_offset >= PAGE_SIZE:
            self._tx_offset -= PAGE_SIZE
            self.load_transactions()

    def _next_page(self):
        self._tx_offset += PAGE_SIZE
        self.load_transactions()
