# `core/modules/personnel/wallet_window/_dashboard_tab.py`

> 路径：`core/modules/personnel/wallet_window/_dashboard_tab.py` | 行数：58


---


```python
# -*- coding: utf-8 -*-
"""
Dashboard Tab Mixin — 看板页签（浅色主题）
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ._stat_card import StatCard
from core.modules.personnel.wallet_service import get_wallet_stats, get_pending_withdrawals


class _DashboardTabMixin:
    """看板页签"""

    def _build_dashboard_tab(self):
        tab = QWidget()
        vl = QVBoxLayout(tab)
        vl.setContentsMargins(16, 16, 16, 16)

        # 统计卡片
        card_grid = QGridLayout()
        self.card_balance = StatCard("💰 总余额", "—", "accent")
        card_grid.addWidget(self.card_balance, 0, 0)
        self.card_frozen = StatCard("❄️ 总冻结", "—", "secondary")
        card_grid.addWidget(self.card_frozen, 0, 1)
        self.card_deposit = StatCard("📥 总充值", "—", "success")
        card_grid.addWidget(self.card_deposit, 0, 2)
        self.card_withdraw = StatCard("📤 提现中", "—", "warning")
        card_grid.addWidget(self.card_withdraw, 0, 3)
        vl.addLayout(card_grid)

        vl.addSpacing(10)
        lbl_title = QLabel("📊 按用户统计")
        lbl_title.setFont(QFont("PingFang SC", 14, QFont.Bold))
        vl.addWidget(lbl_title)
        vl.addStretch()
        self.tabs.addTab(tab, "看板")

    def load_dashboard(self):
        stats = get_wallet_stats()
        pending = get_pending_withdrawals()
        pending_sum = sum(p.get("amount", 0) for p in pending)
        pending_count = len(pending)
        self.card_balance.set_value(
            f"¥{stats['total_balance']:,.2f}"
        )
        self.card_frozen.set_value(
            f"¥{stats['total_frozen']:,.2f}"
        )
        self.card_deposit.set_value(
            f"¥{stats['total_income']:,.2f}"
        )
        self.card_withdraw.set_value(
            f"¥{pending_sum:,.2f} ({pending_count} 笔)"
        )

```
