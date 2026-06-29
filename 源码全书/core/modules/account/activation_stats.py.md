# `core/modules/account/activation_stats.py`

> 路径：`core/modules/account/activation_stats.py` | 行数：140


---


```python
# -*- coding: utf-8 -*-
from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR

import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.modules.account.activation_stats_service import get_kpi_stats, get_activated_users, get_activation_logs


class ActivationStatsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("激活数据统计")
        self.setMinimumSize(900, 650)
        self.setStyleSheet("background:#f5f5f5;")
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # 标题
        title = QLabel("📊 激活数据统计")
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        layout.addWidget(title)

        # KPI 卡片行
        kpi_layout = QHBoxLayout()
        self._kpi_cards = {}
        for key, label, color in [
            ("total",   "总激活码",   "#3182ce"),
            ("used",    "已激活",     "#38a169"),
            ("unused",  "未使用",     "#d69e2e"),
            ("trial",   "体验会员",   "#805ad5"),
            ("pro",     "VIP会员",   "#3182ce"),
            ("vip",     "VIP用户",    "#d69e2e"),
        ]:
            card = QWidget()
            card.setStyleSheet(f"background:white; border-radius:10px; border-left: 4px solid {color}; padding:12px;")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(12, 8, 12, 8)
            lbl = QLabel(label)
            lbl.setStyleSheet("color:#718096; font-size:12px;")
            cl.addWidget(lbl)
            val = QLabel("0")
            val.setFont(QFont("PingFang SC", 22, QFont.Bold))
            val.setStyleSheet(f"color:{color};")
            cl.addWidget(val)
            kpi_layout.addWidget(card)
            self._kpi_cards[key] = val
        layout.addLayout(kpi_layout)

        # 最近激活记录
        log_group = QGroupBox("最近激活记录（最新20条）")
        log_layout = QVBoxLayout(log_group)
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(6)
        self.log_table.setHorizontalHeaderLabels(["账号", "机器码", "激活码", "类型", "结果", "时间"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.log_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.log_table.setAlternatingRowColors(True)
        log_layout.addWidget(self.log_table)
        layout.addWidget(log_group)

        # 已激活用户列表
        user_group = QGroupBox("已激活用户")
        user_layout = QVBoxLayout(user_group)
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(5)
        self.user_table.setHorizontalHeaderLabels(["账号", "类型", "激活码", "机器码", "激活时间"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.user_table.setAlternatingRowColors(True)
        user_layout.addWidget(self.user_table)
        layout.addWidget(user_group)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("🔄 刷新")
        btn_refresh.clicked.connect(self._load_data)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addStretch()
        btn_close = QPushButton("关闭")
        btn_close.setStyleSheet("background:#6c757d; color:white;")
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _load_data(self):
        # KPI
        stats = get_kpi_stats()
        self._kpi_cards["total"].setText(str(stats["total"]))
        self._kpi_cards["used"].setText(str(stats["used"]))
        self._kpi_cards["unused"].setText(str(stats["unused"]))
        self._kpi_cards["trial"].setText(str(stats["trial"]))
        self._kpi_cards["pro"].setText(str(stats["pro"]))
        self._kpi_cards["vip"].setText(str(stats["vip"]))

        # 已激活用户
        user_rows = get_activated_users()
        type_map = {"TRIAL": "体验会员", "PRO": "VIP会员", "VIP": "钻石会员"}
        self.user_table.setRowCount(len(user_rows))
        for i, r in enumerate(user_rows):
            vals = [r.get("bound_account", ""), r.get("user_type", ""), r.get("code", ""),
                    r.get("bound_machine", ""), r.get("used_at", "")]
            for j, val in enumerate(vals):
                text = type_map.get(val, val) if j == 1 else (str(val) if val else "-")
                item = QTableWidgetItem(text)
                if j == 1:
                    color_map = {"TRIAL": "#805ad5", "PRO": "#3182ce", "VIP": "#d69e2e"}
                    item.setForeground(Qt.darkGreen if r.get("user_type") == "VIP" else Qt.blue)
                self.user_table.setItem(i, j, item)

        # 激活日志
        log_rows = get_activation_logs(20)
        result_map = {
            "SUCCESS": "✅ 成功", "INVALID_FORMAT": "❌ 格式错误",
            "ALREADY_USED": "❌ 已使用", "MACHINE_MISMATCH": "❌ 设备不匹配",
            "TAMPERED": "⚠️ 被篡改"
        }
        self.log_table.setRowCount(len(log_rows))
        for i, r in enumerate(log_rows):
            vals = [r.get("account", ""), r.get("machine_code", ""), r.get("code", ""),
                    r.get("code_type", ""), r.get("result", ""), r.get("created_at", "")]
            for j, val in enumerate(vals):
                text = result_map.get(val, val) if j == 4 else (str(val)[:20] if val else "-")
                item = QTableWidgetItem(text)
                if j == 4 and val != "SUCCESS":
                    item.setForeground(Qt.red)
                self.log_table.setItem(i, j, item)

```
