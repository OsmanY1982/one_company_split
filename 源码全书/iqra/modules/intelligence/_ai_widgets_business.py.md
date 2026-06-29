# `iqra/modules/intelligence/_ai_widgets_business.py`

> 路径：`iqra/modules/intelligence/_ai_widgets_business.py` | 行数：149


---


```python
# -*- coding: utf-8 -*-
"""业务 AI Widget — BusinessAIWidget

拆分自 _ai_widgets.py（原 784 行 → 本文件 ~140 行）
为纯后端模块 business_ai_assistant / business_tools / crm_tools / inventory_tools /
marketing_tools / smart_report_tools 提供可视化界面
"""

import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QGridLayout,
    QGroupBox, QTextEdit, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class BusinessAIWidget(QWidget):
    """业务 AI 可视化面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        from modules.intelligence.business_ai_assistant import BusinessAIAssistant
        from modules.intelligence.business_tools import query_products, query_orders, query_customers, query_finance
        from modules.intelligence.crm_tools import analyze_customer_value, get_customer_segments, get_contact_reminders
        from modules.intelligence.inventory_tools import query_inventory, get_inventory_alerts, get_inventory_summary
        from modules.intelligence.marketing_tools import MarketingTools
        from modules.intelligence.smart_report_tools import generate_customer_ranking, generate_product_performance

        self._assistant = BusinessAIAssistant()

        self._data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
        self._query_products = query_products
        self._query_orders = query_orders
        self._query_customers = query_customers
        self._query_finance = query_finance
        self._crm_analyze = analyze_customer_value
        self._crm_segments = get_customer_segments
        self._crm_reminders = get_contact_reminders
        self._inv_query = query_inventory
        self._inv_alerts = get_inventory_alerts
        self._inv_summary = get_inventory_summary
        self._marketing_tools = MarketingTools(self._data_dir)
        self._report_customer_ranking = generate_customer_ranking
        self._report_product_perf = generate_product_performance

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("💼 业务 AI 助手")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet("color: #1a202c;")
        layout.addWidget(title)

        desc = QLabel("智能客服 · 销售预测 · 库存预警 · 数据洞察 · 自然语言查询")
        desc.setStyleSheet("color: #718096; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        modules_group = QGroupBox("业务能力")
        modules_group.setStyleSheet("QGroupBox { font-weight: 600; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-top: 10px; }")
        mod_layout = QGridLayout(modules_group)
        mod_layout.setSpacing(10)

        modules = [
            ("🤖 智能客服", "自动回复客户咨询"),
            ("📈 销售预测", "基于历史预测销量"),
            ("📦 库存预警", "智能补货建议"),
            ("🔍 数据洞察", "自动分析业务数据"),
            ("💬 NL查询", "自然语言问销售额"),
        ]
        for i, (name, desc_text) in enumerate(modules):
            card = QFrame()
            card.setStyleSheet("QFrame { background: #f7fafc; border-radius: 8px; padding: 8px; }")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            nl = QLabel(name)
            nl.setFont(QFont("PingFang SC", 13, QFont.Bold))
            nl.setStyleSheet("color: #2c3e50;")
            card_layout.addWidget(nl)
            dl = QLabel(desc_text)
            dl.setStyleSheet("color: #7f8c8d; font-size: 12px;")
            card_layout.addWidget(dl)
            mod_layout.addWidget(card, i // 3, i % 3)

        layout.addWidget(modules_group)

        query_group = QGroupBox("自然语言查询")
        query_group.setStyleSheet(modules_group.styleSheet())
        query_layout = QVBoxLayout(query_group)

        input_row = QHBoxLayout()
        self._query_input = QLineEdit()
        self._query_input.setPlaceholderText("例如：今年销售额最高的产品是什么？")
        self._query_input.setMinimumHeight(40)
        self._query_input.setStyleSheet("border: 2px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; font-size: 14px;")
        self._query_input.returnPressed.connect(self._run_query)
        input_row.addWidget(self._query_input)

        query_btn = QPushButton("🔍 查询")
        query_btn.setMinimumHeight(40)
        query_btn.setCursor(Qt.PointingHandCursor)
        query_btn.setStyleSheet("QPushButton { background: #2b6cb0; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-size: 14px; font-weight: 600; } QPushButton:hover { background: #2c5282; }")
        query_btn.clicked.connect(self._run_query)
        input_row.addWidget(query_btn)
        query_layout.addLayout(input_row)

        layout.addWidget(query_group)

        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("查询结果将显示在这里...")
        self._output.setStyleSheet("background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 13px;")
        layout.addWidget(self._output)

    def _run_query(self):
        query = self._query_input.text().strip()
        if not query:
            return
        self._output.append(f"\n🔍 查询: {query}")
        try:
            if hasattr(self._assistant, 'natural_language_query'):
                result = self._assistant.natural_language_query(query)
                self._output.append(f"📊 结果: {result}")
            elif hasattr(self, '_query_products'):
                if any(kw in query for kw in ['产品', '商品', 'product']):
                    data = self._query_products(self._data_dir, '')
                    self._output.append(f"📦 产品查询: {data.get('message', '')}")
                elif any(kw in query for kw in ['订单', '销售', 'order']):
                    data = self._query_orders(self._data_dir, '')
                    self._output.append(f"📋 订单查询: {data.get('message', '')}")
                elif any(kw in query for kw in ['客户', 'customer']):
                    data = self._query_customers(self._data_dir, '')
                    self._output.append(f"👤 客户查询: {data.get('message', '')}")
                elif any(kw in query for kw in ['财务', '收支', 'finance']):
                    data = self._query_finance(self._data_dir)
                    self._output.append(f"💰 财务查询: {data.get('message', '')}")
                else:
                    self._output.append("💡 请使用更具体的查询关键词（产品/订单/客户/财务）")
            else:
                self._output.append("✅ 业务 AI 助手已就绪，可通过 query() 方法执行自然语言查询")
        except Exception as e:
            self._output.append(f"❌ 查询出错: {e}")

```
