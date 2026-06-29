# -*- coding: utf-8 -*-
"""
AI 智能看板窗口
一企通 AI 版核心界面
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QTableWidget, 
    QTableWidgetItem, QStackedWidget, QGroupBox, QGridLayout,
    QMessageBox, QHeaderView, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

from core.modules.intelligence.ai_features_ai_dashboard import AIDashboard
from core.modules.intelligence.ai_features_inventory_ai import InventoryAI
from core.modules.intelligence.ai_features_pricing_ai import PricingAI
from core.modules.intelligence.ai_features_sales_ai import SalesAI
from core.modules.intelligence.ai_features_customer_ai import CustomerAI


class AIDashboardWindow(QMainWindow):
    """AI 智能看板主窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🤖 一企通 AI 智能看板")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化 AI 模块
        self.ai_dashboard = AIDashboard()
        self.inventory_ai = InventoryAI()
        self.pricing_ai = PricingAI()
        self.sales_ai = SalesAI()
        self.customer_ai = CustomerAI()
        
        self._setup_ui()
        self._load_data()
        
        # 自动刷新定时器（每5分钟）
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._load_data)
        self.refresh_timer.start(300000)  # 5分钟
    
    def _setup_ui(self):
        """设置界面"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 标题
        title = QLabel("🤖 一企通 AI 智能看板")
        title_font = QFont("PingFang SC", 18, QFont.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(title)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新数据")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        refresh_btn.clicked.connect(self._load_data)
        layout.addWidget(refresh_btn, alignment=Qt.AlignRight)
        
        # 轨道式标签页 — 使用 QStackedWidget 替代 QTabWidget
        self._tab_stack = QStackedWidget()
        
        # 导航按钮栏
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(0)
        self._tab_btns = []
        tab_defs = [
            ("📊 总览", 0),
            ("📦 库存智能", 1),
            ("💰 定价优化", 2),
            ("📈 销售分析", 3),
            ("👥 客户洞察", 4),
        ]
        for name, idx in tab_defs:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 10px 20px; background: #f5f5f5;
                    border: 1px solid #ddd; font-size: 13px;
                }
                QPushButton:checked {
                    background: #2196F3; color: white;
                }
            """)
            btn.clicked.connect(lambda checked, i=idx: self._switch_tab(i))
            nav_layout.addWidget(btn)
            self._tab_btns.append(btn)
        nav_layout.addStretch()
        
        layout.addLayout(nav_layout)
        
        # 概览页
        self.overview_tab = self._create_overview_tab()
        self._tab_stack.addWidget(self.overview_tab)
        
        # 库存页
        self.inventory_tab = self._create_inventory_tab()
        self._tab_stack.addWidget(self.inventory_tab)
        
        # 定价页
        self.pricing_tab = self._create_pricing_tab()
        self._tab_stack.addWidget(self.pricing_tab)
        
        # 销售页
        self.sales_tab = self._create_sales_tab()
        self._tab_stack.addWidget(self.sales_tab)
        
        # 客户页
        self.customer_tab = self._create_customer_tab()
        self._tab_stack.addWidget(self.customer_tab)
        
        layout.addWidget(self._tab_stack)
        
        # 默认选中第一个
        self._tab_btns[0].setChecked(True)
        self._tab_stack.setCurrentIndex(0)
        
    def _switch_tab(self, idx):
        """切换轨道式标签页"""
        self._tab_stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._tab_btns):
            btn.setChecked(i == idx)
    
    def _create_overview_tab(self) -> QWidget:
        """创建概览页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 行动建议卡片
        self.action_card = QGroupBox("🎯 今日行动建议")
        self.action_layout = QVBoxLayout(self.action_card)
        layout.addWidget(self.action_card)
        
        # 关键指标
        metrics_layout = QGridLayout()
        
        self.metric_revenue = self._create_metric_card("💰 本周营收", "¥0")
        self.metric_orders = self._create_metric_card("📋 本周订单", "0")
        self.metric_customers = self._create_metric_card("👥 客户总数", "0")
        self.metric_risk = self._create_metric_card("⚠️ 流失风险", "0")
        
        metrics_layout.addWidget(self.metric_revenue, 0, 0)
        metrics_layout.addWidget(self.metric_orders, 0, 1)
        metrics_layout.addWidget(self.metric_customers, 0, 2)
        metrics_layout.addWidget(self.metric_risk, 0, 3)
        
        layout.addLayout(metrics_layout)
        
        # 报告文本
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                padding: 10px;
                font-family: PingFang SC;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.report_text)
        
        return tab
    
    def _create_metric_card(self, title: str, value: str) -> QGroupBox:
        """创建指标卡片"""
        card = QGroupBox(title)
        layout = QVBoxLayout(card)
        
        label = QLabel(value)
        label_font = QFont("PingFang SC", 24, QFont.Bold)
        label.setFont(label_font)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #2196F3;")
        
        layout.addWidget(label)
        card.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
            QGroupBox::title {
                color: #666;
                font-size: 12px;
            }
        """)
        
        return card
    
    def _create_inventory_tab(self) -> QWidget:
        """创建库存智能页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 补货建议表格
        reorder_group = QGroupBox("📦 补货建议")
        reorder_layout = QVBoxLayout(reorder_group)
        
        self.reorder_table = QTableWidget()
        self.reorder_table.setColumnCount(5)
        self.reorder_table.setHorizontalHeaderLabels([
            "商品名称", "当前库存", "建议补货", "紧急程度", "原因"
        ])
        self.reorder_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        reorder_layout.addWidget(self.reorder_table)
        
        layout.addWidget(reorder_group)
        
        # 滞销商品
        slow_group = QGroupBox("🐌 滞销商品")
        slow_layout = QVBoxLayout(slow_group)
        
        self.slow_table = QTableWidget()
        self.slow_table.setColumnCount(4)
        self.slow_table.setHorizontalHeaderLabels([
            "商品名称", "当前库存", "滞销天数", "建议"
        ])
        self.slow_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        slow_layout.addWidget(self.slow_table)
        
        layout.addWidget(slow_group)
        
        return tab
    
    def _create_pricing_tab(self) -> QWidget:
        """创建定价优化页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 定价机会
        opp_group = QGroupBox("💰 定价优化机会")
        opp_layout = QVBoxLayout(opp_group)
        
        self.pricing_table = QTableWidget()
        self.pricing_table.setColumnCount(5)
        self.pricing_table.setHorizontalHeaderLabels([
            "商品名称", "机会类型", "当前价", "建议价", "预计增收"
        ])
        self.pricing_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        opp_layout.addWidget(self.pricing_table)
        
        layout.addWidget(opp_group)
        
        # 促销建议
        promo_group = QGroupBox("🎉 促销建议")
        promo_layout = QVBoxLayout(promo_group)
        
        self.promo_table = QTableWidget()
        self.promo_table.setColumnCount(4)
        self.promo_table.setHorizontalHeaderLabels([
            "商品名称", "建议折扣", "预期效果", "操作"
        ])
        self.promo_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        promo_layout.addWidget(self.promo_table)
        
        layout.addWidget(promo_group)
        
        return tab
    
    def _create_sales_tab(self) -> QWidget:
        """创建销售分析页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 销售概况
        summary_group = QGroupBox("📈 销售概况")
        summary_layout = QVBoxLayout(summary_group)
        
        self.sales_summary = QTextEdit()
        self.sales_summary.setReadOnly(True)
        summary_layout.addWidget(self.sales_summary)
        
        layout.addWidget(summary_group)
        
        # 热销商品
        top_group = QGroupBox("🔥 热销商品")
        top_layout = QVBoxLayout(top_group)
        
        self.top_products_table = QTableWidget()
        self.top_products_table.setColumnCount(4)
        self.top_products_table.setHorizontalHeaderLabels([
            "商品名称", "销量", "销售额", "订单数"
        ])
        self.top_products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        top_layout.addWidget(self.top_products_table)
        
        layout.addWidget(top_group)
        
        return tab
    
    def _create_customer_tab(self) -> QWidget:
        """创建客户洞察页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 客户分层
        segment_group = QGroupBox("👥 客户分层")
        segment_layout = QVBoxLayout(segment_group)
        
        self.segment_table = QTableWidget()
        self.segment_table.setColumnCount(4)
        self.segment_table.setHorizontalHeaderLabels([
            "客户名称", "总消费", "订单数", "分层"
        ])
        self.segment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        segment_layout.addWidget(self.segment_table)
        
        layout.addWidget(segment_group)
        
        # 流失预警
        churn_group = QGroupBox("⚠️ 流失预警")
        churn_layout = QVBoxLayout(churn_group)
        
        self.churn_table = QTableWidget()
        self.churn_table.setColumnCount(5)
        self.churn_table.setHorizontalHeaderLabels([
            "客户名称", "风险等级", "距今天数", "总消费", "建议行动"
        ])
        self.churn_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        churn_layout.addWidget(self.churn_table)
        
        layout.addWidget(churn_group)
        
        return tab
    
    def _load_data(self):
        """加载 AI 数据"""
        try:
            # 生成报告
            report = self.ai_dashboard.get_daily_report()
            
            # 更新概览
            self._update_overview(report)
            
            # 更新库存
            self._update_inventory()
            
            # 更新定价
            self._update_pricing()
            
            # 更新销售
            self._update_sales()
            
            # 更新客户
            self._update_customers()
            
        except Exception as e:
            QMessageBox.warning(self, "数据加载失败", str(e))
    
    def _update_overview(self, report: dict):
        """更新概览页"""
        # 行动建议
        # 清除旧内容
        while self.action_layout.count():
            child = self.action_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        for action in report['actions']:
            label = QLabel(f"• {action}")
            label.setStyleSheet("font-size: 14px; padding: 5px;")
            self.action_layout.addWidget(label)
        
        # 指标
        self._update_metric_card(self.metric_revenue, f"¥{report['sales']['week_revenue']}")
        self._update_metric_card(self.metric_orders, str(report['sales']['week_orders']))
        self._update_metric_card(self.metric_customers, str(report['customers']['total_customers']))
        self._update_metric_card(self.metric_risk, str(report['customers']['at_risk_count']))
        
        # 报告文本
        report_text = self.ai_dashboard.export_report(report, format='text')
        self.report_text.setText(report_text)
    
    def _update_metric_card(self, card: QGroupBox, value: str):
        """更新指标卡片"""
        layout = card.layout()
        label = layout.itemAt(0).widget()
        label.setText(value)
    
    def _update_inventory(self):
        """更新库存页"""
        # 补货建议
        reorder = self.inventory_ai.get_reorder_suggestions()
        self.reorder_table.setRowCount(len(reorder))
        
        for i, item in enumerate(reorder):
            self.reorder_table.setItem(i, 0, QTableWidgetItem(item['product_name']))
            self.reorder_table.setItem(i, 1, QTableWidgetItem(str(item['current_stock'])))
            self.reorder_table.setItem(i, 2, QTableWidgetItem(str(item['suggested_qty'])))
            self.reorder_table.setItem(i, 3, QTableWidgetItem(item['urgency']))
            self.reorder_table.setItem(i, 4, QTableWidgetItem(item['reason']))
            
            # 紧急程度颜色
            if item['urgency'] == '紧急':
                self.reorder_table.item(i, 3).setBackground(QColor(255, 200, 200))
        
        # 滞销商品
        slow = self.inventory_ai.get_slow_moving_products(days=30)
        self.slow_table.setRowCount(len(slow))
        
        for i, item in enumerate(slow):
            self.slow_table.setItem(i, 0, QTableWidgetItem(item['product_name']))
            self.slow_table.setItem(i, 1, QTableWidgetItem(str(item['current_stock'])))
            days = str(item['days_since_last_sale']) if item['days_since_last_sale'] > 0 else "从未"
            self.slow_table.setItem(i, 2, QTableWidgetItem(days))
            self.slow_table.setItem(i, 3, QTableWidgetItem(item['suggestion']))
    
    def _update_pricing(self):
        """更新定价页"""
        # 定价机会
        opportunities = self.pricing_ai.get_pricing_opportunities()
        self.pricing_table.setRowCount(len(opportunities))
        
        for i, opp in enumerate(opportunities):
            self.pricing_table.setItem(i, 0, QTableWidgetItem(opp['product_name']))
            self.pricing_table.setItem(i, 1, QTableWidgetItem(opp['opportunity']))
            self.pricing_table.setItem(i, 2, QTableWidgetItem(f"¥{opp['current_price']}"))
            self.pricing_table.setItem(i, 3, QTableWidgetItem(f"¥{opp['suggested_price']}"))
            self.pricing_table.setItem(i, 4, QTableWidgetItem(f"¥{opp['potential_profit_increase']}"))
        
        # 促销建议
        promotions = self.pricing_ai.get_promotion_suggestions()
        self.promo_table.setRowCount(len(promotions))
        
        for i, promo in enumerate(promotions):
            self.promo_table.setItem(i, 0, QTableWidgetItem(promo['product_name']))
            self.promo_table.setItem(i, 1, QTableWidgetItem(f"{int(promo['discount_rate']*10)}折"))
            self.promo_table.setItem(i, 2, QTableWidgetItem(promo['expected_effect']))
            
            # 操作按钮
            btn = QPushButton("应用")
            btn.setStyleSheet("background-color: #FF9800; color: white;")
            self.promo_table.setCellWidget(i, 3, btn)
    
    def _update_sales(self):
        """更新销售页"""
        # 销售概况
        summary = self.sales_ai.get_sales_summary(days=7)
        forecast = self.sales_ai.get_sales_forecast(days=7)
        
        summary_text = f"""
📊 本周销售概况
━━━━━━━━━━━━━━━━━━━━━━━━
💰 总营收: ¥{summary['total_revenue']}
📋 总订单: {summary['total_orders']}
📦 总商品: {summary['total_items']}
💵 客单价: ¥{summary['avg_order_value']}
📈 销售趋势: {summary['trend']}

🔮 下周预测
━━━━━━━━━━━━━━━━━━━━━━━━
💰 预测营收: ¥{forecast['forecast_revenue']}
📋 预测订单: {forecast['forecast_orders']}
🎯 置信度: {forecast['confidence']*100:.0f}%

💡 建议: {forecast['suggestion']}
        """
        self.sales_summary.setText(summary_text)
        
        # 热销商品
        top_products = summary['top_products']
        self.top_products_table.setRowCount(len(top_products))
        
        for i, product in enumerate(top_products):
            self.top_products_table.setItem(i, 0, QTableWidgetItem(product['product_name']))
            self.top_products_table.setItem(i, 1, QTableWidgetItem(str(product['total_qty'])))
            self.top_products_table.setItem(i, 2, QTableWidgetItem(f"¥{product['total_revenue']}"))
            self.top_products_table.setItem(i, 3, QTableWidgetItem(str(product['order_count'])))
    
    def _update_customers(self):
        """更新客户页"""
        # 客户分层
        segments = self.customer_ai.get_customer_segments()
        
        # 合并所有客户
        all_customers = []
        for segment, customers in segments['segments'].items():
            for customer in customers:
                customer['segment'] = segment
                all_customers.append(customer)
        
        # 按消费排序
        all_customers.sort(key=lambda x: x['total_spent'], reverse=True)
        
        self.segment_table.setRowCount(min(len(all_customers), 20))
        for i, customer in enumerate(all_customers[:20]):
            self.segment_table.setItem(i, 0, QTableWidgetItem(customer['name']))
            self.segment_table.setItem(i, 1, QTableWidgetItem(f"¥{customer['total_spent']}"))
            self.segment_table.setItem(i, 2, QTableWidgetItem(str(customer['total_orders'])))
            self.segment_table.setItem(i, 3, QTableWidgetItem(customer['segment']))
            
            # VIP 高亮
            if customer['segment'] == 'VIP客户':
                self.segment_table.item(i, 3).setBackground(QColor(255, 215, 0))
        
        # 流失预警
        churn_alerts = self.customer_ai.get_churn_alerts()
        self.churn_table.setRowCount(len(churn_alerts))
        
        for i, alert in enumerate(churn_alerts):
            self.churn_table.setItem(i, 0, QTableWidgetItem(alert['customer_name']))
            self.churn_table.setItem(i, 1, QTableWidgetItem(alert['risk_level']))
            self.churn_table.setItem(i, 2, QTableWidgetItem(str(alert['days_since'])))
            self.churn_table.setItem(i, 3, QTableWidgetItem(f"¥{alert['total_spent']}"))
            self.churn_table.setItem(i, 4, QTableWidgetItem(alert['suggested_action']))
            
            # 风险等级颜色
            if alert['risk_level'] == '高':
                self.churn_table.item(i, 1).setBackground(QColor(255, 100, 100))


def show_ai_dashboard(parent=None):
    """显示 AI 智能看板"""
    window = AIDashboardWindow(parent)
    window.show()
    return window


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AIDashboardWindow()
    window.show()
    sys.exit(app.exec_())
