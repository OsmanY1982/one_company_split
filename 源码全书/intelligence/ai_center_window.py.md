# `intelligence/ai_center_window.py`

> 路径：`intelligence/ai_center_window.py` | 行数：625


---


```python
# -*- coding: utf-8 -*-
"""
智能中心 - 统一AI功能入口 (V2增强版)
直接连接数据库，提供真正可用的AI功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QTableWidget, 
    QTableWidgetItem, QTabWidget, QGroupBox, QGridLayout,
    QMessageBox, QHeaderView, QProgressBar, QComboBox,
    QLineEdit, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from core.database import get_conn, close_conn
from datetime import datetime, timedelta

class AICenterWindow(QMainWindow):
    """智能中心主窗口 - V2版本，直接连接数据库"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("智能中心 V2")
        self.setMinimumSize(1200, 800)
        
        # 数据库路径 - 使用实际项目的数据库
        self.db_path = self._find_database()
        
        self._setup_ui()
        self._load_data()
    
    def _find_database(self):
        """查找数据库文件"""
        # 优先使用data目录下的orders.db
        db_paths = [
            os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'orders.db'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'orders.db'),
            'D:/one_company_desktop/data/orders.db',
        ]
        
        for path in db_paths:
            if os.path.exists(path):
                return path
        
        # 如果找不到，返回默认路径（会生成测试数据）
        return db_paths[0]
    
    def _get_conn(self):
        """获取数据库连接（使用连接池）"""
        return get_conn('order.db')
    
    def _setup_ui(self):
        """设置UI界面"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 标题
        title = QLabel("智能中心 V2 - 数据驱动决策")
        title.setFont(QFont("PingFang SC", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 数据库状态
        self.db_status = QLabel(f"数据库: {self.db_path}")
        self.db_status.setStyleSheet("color: gray;")
        layout.addWidget(self.db_status)
        
        # 标签页
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # 1. 智能总览
        tabs.addTab(self._create_overview_tab(), "智能总览")
        # 2. 数据分析
        tabs.addTab(self._create_analysis_tab(), "数据分析")
        # 3. 智能报表
        tabs.addTab(self._create_report_tab(), "智能报表")
        # 4. 业务洞察
        tabs.addTab(self._create_insights_tab(), "业务洞察")
    
    def _create_overview_tab(self):
        """创建智能总览标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # KPI卡片
        kpi_layout = QHBoxLayout()
        
        self.kpi_cards = {}
        kpi_items = [
            ('orders', '订单总数', '#3498db'),
            ('revenue', '总销售额', '#2ecc71'),
            ('products', '产品数量', '#e74c3c'),
            ('customers', '客户数量', '#f39c12')
        ]
        
        for key, title, color in kpi_items:
            card = QGroupBox(title)
            card.setStyleSheet(f"QGroupBox {{ font-weight: bold; border: 2px solid {color}; }}")
            card_layout = QVBoxLayout(card)
            
            value = QLabel("加载中...")
            value.setFont(QFont("PingFang SC", 24, QFont.Bold))
            value.setStyleSheet(f"color: {color};")
            value.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(value)
            
            self.kpi_cards[key] = value
            kpi_layout.addWidget(card)
        
        layout.addLayout(kpi_layout)
        
        # 快速查询
        query_group = QGroupBox("快速查询")
        query_layout = QHBoxLayout(query_group)
        
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("输入查询：销售额、订单、产品、客户、库存...")
        query_layout.addWidget(self.query_input)
        
        query_btn = QPushButton("查询")
        query_btn.clicked.connect(self._execute_query)
        query_layout.addWidget(query_btn)
        
        layout.addWidget(query_group)
        
        # 查询结果
        self.query_result = QTextEdit()
        self.query_result.setReadOnly(True)
        self.query_result.setPlaceholderText("查询结果将显示在这里...")
        layout.addWidget(self.query_result)
        
        return widget
    
    def _create_analysis_tab(self):
        """创建数据分析标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 分析按钮
        btn_layout = QHBoxLayout()
        
        sales_btn = QPushButton("销售趋势分析")
        sales_btn.clicked.connect(self._show_sales_trend)
        btn_layout.addWidget(sales_btn)
        
        product_btn = QPushButton("产品销售分析")
        product_btn.clicked.connect(self._show_product_analysis)
        btn_layout.addWidget(product_btn)
        
        customer_btn = QPushButton("客户分析")
        customer_btn.clicked.connect(self._show_customer_analysis)
        btn_layout.addWidget(customer_btn)
        
        inventory_btn = QPushButton("库存预警")
        inventory_btn.clicked.connect(self._show_inventory_alert)
        btn_layout.addWidget(inventory_btn)
        
        layout.addLayout(btn_layout)
        
        # 分析结果
        self.analysis_result = QTextEdit()
        self.analysis_result.setReadOnly(True)
        layout.addWidget(self.analysis_result)
        
        return widget
    
    def _create_report_tab(self):
        """创建智能报表标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 报表类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("报表类型："))
        
        self.report_type = QComboBox()
        self.report_type.addItems(["销售报表", "产品报表", "客户报表", "综合报表"])
        type_layout.addWidget(self.report_type)
        
        generate_btn = QPushButton("生成报表")
        generate_btn.clicked.connect(self._generate_report)
        type_layout.addWidget(generate_btn)
        
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # 报表结果
        self.report_result = QTextEdit()
        self.report_result.setReadOnly(True)
        layout.addWidget(self.report_result)
        
        return widget
    
    def _create_insights_tab(self):
        """创建业务洞察标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 洞察按钮
        btn_layout = QHBoxLayout()
        
        hot_btn = QPushButton("热销产品")
        hot_btn.clicked.connect(self._show_hot_products)
        btn_layout.addWidget(hot_btn)
        
        churn_btn = QPushButton("流失风险客户")
        churn_btn.clicked.connect(self._show_churn_risk)
        btn_layout.addWidget(churn_btn)
        
        stock_btn = QPushButton("库存建议")
        stock_btn.clicked.connect(self._show_stock_suggestions)
        btn_layout.addWidget(stock_btn)
        
        revenue_btn = QPushButton("营收预测")
        revenue_btn.clicked.connect(self._show_revenue_forecast)
        btn_layout.addWidget(revenue_btn)
        
        layout.addLayout(btn_layout)
        
        # 洞察结果
        self.insights_result = QTextEdit()
        self.insights_result.setReadOnly(True)
        layout.addWidget(self.insights_result)
        
        return widget
    
    def _load_data(self):
        """加载数据到KPI卡片"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # 订单数
            cursor.execute("SELECT COUNT(*) FROM orders")
            orders_count = cursor.fetchone()[0]
            self.kpi_cards['orders'].setText(str(orders_count))
            
            # 销售额
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM orders")
            revenue = cursor.fetchone()[0]
            self.kpi_cards['revenue'].setText(f"{revenue:,.0f}")
            
            # 产品数
            cursor.execute("SELECT COUNT(*) FROM products")
            products_count = cursor.fetchone()[0]
            self.kpi_cards['products'].setText(str(products_count))
            
            # 客户数
            cursor.execute("SELECT COUNT(*) FROM customers")
            customers_count = cursor.fetchone()[0]
            self.kpi_cards['customers'].setText(str(customers_count))
            
            close_conn('order.db')
            self.db_status.setText(f"数据库已连接: {self.db_path}")
            
        except Exception as e:
            self.db_status.setText(f"数据库连接失败: {e}")
            # 生成测试数据
            self._generate_test_data()
    
    def _generate_test_data(self):
        """生成测试数据"""
        try:
            # 检查是否有测试数据生成器
            test_gen_path = os.path.join(os.path.dirname(__file__), '..', '..', 'test_data_generator.py')
            if os.path.exists(test_gen_path):
                os.system(f'cd "{os.path.dirname(test_gen_path)}" && python test_data_generator.py')
                self._load_data()  # 重新加载
        except Exception as e:
            self.query_result.setText(f"生成测试数据失败: {e}")
    
    def _execute_query(self):
        """执行快速查询"""
        query = self.query_input.text().strip().lower()
        
        if not query:
            QMessageBox.warning(self, "提示", "请输入查询内容")
            return
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            result_text = f"查询: {query}\n" + "="*50 + "\n\n"
            
            if '销售' in query or '金额' in query or 'revenue' in query:
                cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM orders")
                total = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM orders")
                count = cursor.fetchone()[0]
                result_text += f"总销售额: {total:,.2f} CNY\n"
                result_text += f"订单数量: {count}\n"
                result_text += f"平均订单金额: {total/count if count > 0 else 0:,.2f} CNY\n"
                
            elif '订单' in query or 'order' in query:
                cursor.execute("SELECT COUNT(*) FROM orders")
                count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM orders WHERE status='completed'")
                completed = cursor.fetchone()[0]
                result_text += f"总订单: {count}\n"
                result_text += f"已完成: {completed}\n"
                result_text += f"完成率: {completed/count*100 if count > 0 else 0:.1f}%\n"
                
            elif '产品' in query or 'product' in query:
                cursor.execute("SELECT COUNT(*) FROM products")
                count = cursor.fetchone()[0]
                cursor.execute("SELECT COALESCE(SUM(stock), 0) FROM products")
                stock = cursor.fetchone()[0]
                result_text += f"产品种类: {count}\n"
                result_text += f"总库存: {stock} 件\n"
                
            elif '客户' in query or 'customer' in query:
                cursor.execute("SELECT COUNT(*) FROM customers")
                count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM customers WHERE is_vip=1")
                vip = cursor.fetchone()[0]
                result_text += f"客户总数: {count}\n"
                result_text += f"VIP客户: {vip}\n"
                
            elif '库存' in query or 'stock' in query:
                cursor.execute("SELECT name, stock FROM products WHERE stock < 50")
                low_stock = cursor.fetchall()
                result_text += f"库存预警产品 ({len(low_stock)}个):\n"
                for name, stock in low_stock:
                    result_text += f"  - {name}: {stock} 件\n"
                    
            else:
                result_text += "支持的查询: 销售额、订单、产品、客户、库存\n"
            
            close_conn('order.db')
            self.query_result.setText(result_text)
            
        except Exception as e:
            self.query_result.setText(f"查询失败: {e}")
    
    def _show_sales_trend(self):
        """显示销售趋势"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # 最近7天销售
            cursor.execute("""
                SELECT date(created_at) as day, COUNT(*) as count, COALESCE(SUM(amount), 0) as revenue
                FROM orders
                WHERE created_at >= date('now', '-7 days')
                GROUP BY day
                ORDER BY day
            """)
            
            result = "最近7天销售趋势\n" + "="*50 + "\n\n"
            for day, count, revenue in cursor.fetchall():
                result += f"{day}: {count}单, {revenue:,.2f} CNY\n"
            
            close_conn('order.db')
            self.analysis_result.setText(result)
            
        except Exception as e:
            self.analysis_result.setText(f"分析失败: {e}")
    
    def _show_product_analysis(self):
        """显示产品销售分析"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT product, COUNT(*) as count, COALESCE(SUM(amount), 0) as revenue
                FROM orders
                GROUP BY product
                ORDER BY revenue DESC
                LIMIT 10
            """)
            
            result = "产品销售TOP10\n" + "="*50 + "\n\n"
            for i, (product, count, revenue) in enumerate(cursor.fetchall(), 1):
                result += f"{i}. {product}\n"
                result += f"   销量: {count}单, 销售额: {revenue:,.2f} CNY\n\n"
            
            close_conn('order.db')
            self.analysis_result.setText(result)
            
        except Exception as e:
            self.analysis_result.setText(f"分析失败: {e}")
    
    def _show_customer_analysis(self):
        """显示客户分析"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT customer, COUNT(*) as orders, COALESCE(SUM(amount), 0) as total
                FROM orders
                GROUP BY customer
                ORDER BY total DESC
                LIMIT 10
            """)
            
            result = "客户消费TOP10\n" + "="*50 + "\n\n"
            for i, (customer, orders, total) in enumerate(cursor.fetchall(), 1):
                result += f"{i}. {customer}\n"
                result += f"   订单: {orders}单, 消费: {total:,.2f} CNY\n\n"
            
            close_conn('order.db')
            self.analysis_result.setText(result)
            
        except Exception as e:
            self.analysis_result.setText(f"分析失败: {e}")
    
    def _show_inventory_alert(self):
        """显示库存预警"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("SELECT name, stock FROM products WHERE stock < 50 ORDER BY stock")
            
            result = "库存预警 (< 50件)\n" + "="*50 + "\n\n"
            for name, stock in cursor.fetchall():
                level = "严重" if stock < 20 else "警告"
                result += f"[{level}] {name}: {stock} 件\n"
            
            close_conn('order.db')
            self.analysis_result.setText(result)
            
        except Exception as e:
            self.analysis_result.setText(f"分析失败: {e}")
    
    def _generate_report(self):
        """生成报表"""
        report_type = self.report_type.currentText()
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            if report_type == "销售报表":
                cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM orders")
                count, total = cursor.fetchone()
                
                result = "销售报表\n" + "="*50 + "\n\n"
                result += f"订单总数: {count}\n"
                result += f"总销售额: {total:,.2f} CNY\n"
                result += f"平均订单: {total/count if count > 0 else 0:,.2f} CNY\n\n"
                
                cursor.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
                result += "订单状态分布:\n"
                for status, count in cursor.fetchall():
                    result += f"  {status}: {count}\n"
                    
            elif report_type == "产品报表":
                cursor.execute("SELECT COUNT(*), COALESCE(SUM(stock), 0) FROM products")
                count, stock = cursor.fetchone()
                
                result = "产品报表\n" + "="*50 + "\n\n"
                result += f"产品种类: {count}\n"
                result += f"总库存: {stock} 件\n\n"
                
                cursor.execute("SELECT category, COUNT(*) FROM products GROUP BY category")
                result += "分类分布:\n"
                for cat, count in cursor.fetchall():
                    result += f"  {cat}: {count}个\n"
                    
            elif report_type == "客户报表":
                cursor.execute("SELECT COUNT(*) FROM customers")
                count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM customers WHERE is_vip=1")
                vip = cursor.fetchone()[0]
                
                result = "客户报表\n" + "="*50 + "\n\n"
                result += f"客户总数: {count}\n"
                result += f"VIP客户: {vip}\n"
                result += f"VIP比例: {vip/count*100 if count > 0 else 0:.1f}%\n"
                
            else:  # 综合报表
                result = "综合报表\n" + "="*50 + "\n\n"
                
                cursor.execute("SELECT COUNT(*) FROM orders")
                orders = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM products")
                products = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM customers")
                customers = cursor.fetchone()[0]
                
                result += f"订单: {orders}\n"
                result += f"产品: {products}\n"
                result += f"客户: {customers}\n"
            
            close_conn('order.db')
            self.report_result.setText(result)
            
        except Exception as e:
            self.report_result.setText(f"生成报表失败: {e}")
    
    def _show_hot_products(self):
        """显示热销产品"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT product, COUNT(*) as count, COALESCE(SUM(amount), 0) as revenue
                FROM orders
                GROUP BY product
                ORDER BY count DESC
                LIMIT 5
            """)
            
            result = "热销产品TOP5\n" + "="*50 + "\n\n"
            for i, (product, count, revenue) in enumerate(cursor.fetchall(), 1):
                result += f"{i}. {product}\n"
                result += f"   销量: {count}单\n"
                result += f"   销售额: {revenue:,.2f} CNY\n\n"
            
            close_conn('order.db')
            self.insights_result.setText(result)
            
        except Exception as e:
            self.insights_result.setText(f"分析失败: {e}")
    
    def _show_churn_risk(self):
        """显示流失风险客户"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # 30天无订单的客户
            cursor.execute("""
                SELECT c.name, c.phone, MAX(o.created_at) as last_order
                FROM customers c
                LEFT JOIN orders o ON c.name = o.customer
                GROUP BY c.name
                HAVING last_order IS NULL OR last_order < date('now', '-30 days')
            """)
            
            result = "流失风险客户 (30天无订单)\n" + "="*50 + "\n\n"
            for name, phone, last_order in cursor.fetchall():
                result += f"客户: {name}\n"
                result += f"电话: {phone or 'N/A'}\n"
                result += f"最近订单: {last_order or '从未下单'}\n\n"
            
            close_conn('order.db')
            self.insights_result.setText(result)
            
        except Exception as e:
            self.insights_result.setText(f"分析失败: {e}")
    
    def _show_stock_suggestions(self):
        """显示库存建议"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name, stock, 
                       CASE WHEN stock < 20 THEN '紧急补货'
                            WHEN stock < 50 THEN '建议补货'
                            ELSE '库存充足' END as status
                FROM products
                ORDER BY stock
            """)
            
            result = "库存建议\n" + "="*50 + "\n\n"
            for name, stock, status in cursor.fetchall():
                result += f"[{status}] {name}: {stock} 件\n"
            
            close_conn('order.db')
            self.insights_result.setText(result)
            
        except Exception as e:
            self.insights_result.setText(f"分析失败: {e}")
    
    def _show_revenue_forecast(self):
        """显示营收预测"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # 最近30天平均日销售额
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) / 30.0 
                FROM orders 
                WHERE created_at >= date('now', '-30 days')
            """)
            avg_daily = cursor.fetchone()[0] or 0
            
            result = "营收预测\n" + "="*50 + "\n\n"
            result += f"最近30天平均日销售额: {avg_daily:,.2f} CNY\n\n"
            result += f"预测下月销售额: {avg_daily * 30:,.2f} CNY\n"
            result += f"预测下季度销售额: {avg_daily * 90:,.2f} CNY\n"
            result += f"预测下年销售额: {avg_daily * 365:,.2f} CNY\n"
            
            close_conn('order.db')
            self.insights_result.setText(result)
            
        except Exception as e:
            self.insights_result.setText(f"预测失败: {e}")


def open_ai_center(parent=None, db_path=None):
    """打开智能中心窗口"""
    window = AICenterWindow(parent)
    if db_path:
        window.db_path = db_path
        window._load_data()
    window.show()
    return window


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = AICenterWindow()
    window.show()
    sys.exit(app.exec_())

```
