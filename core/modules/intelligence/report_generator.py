# -*- coding: utf-8 -*-
"""
智能报表生成器
功能：
1. 销售报表（日报/周报/月报）
2. 库存报表
3. 财务报表
4. 综合仪表板
"""

import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from core.modules.intelligence._compat import get_conn


class ReportGenerator:
    """报表生成器"""
    
    def __init__(self):
        self.reports_cache = {}
    
    # ═══════════════════════════════════════════
    # 1. 销售报表
    # ═══════════════════════════════════════════
    
    def generate_sales_report(self, period: str = 'daily') -> Dict:
        """生成销售报表
        
        Args:
            period: 报表周期 - daily/weekly/monthly/yearly
        """
        conn = get_conn('order.db')
        
        # 确定时间范围
        now = datetime.now()
        if period == 'daily':
            start_date = now.strftime('%Y-%m-%d')
            title = '销售日报'
        elif period == 'weekly':
            start_date = (now - timedelta(days=7)).strftime('%Y-%m-%d')
            title = '销售周报'
        elif period == 'monthly':
            start_date = now.strftime('%Y-%m-01')
            title = '销售月报'
        elif period == 'yearly':
            start_date = now.strftime('%Y-01-01')
            title = '销售年报'
        else:
            start_date = now.strftime('%Y-%m-%d')
            title = '销售报表'
        
        # 查询订单数据
        cursor = conn.execute(
            "SELECT COUNT(*), SUM(amount), AVG(amount) "
            "FROM orders WHERE date(created_at) >= date(?)",
            (start_date,)
        )
        total_orders, total_amount, avg_amount = cursor.fetchone()
        
        # 按产品统计
        cursor = conn.execute(
            "SELECT product, SUM(quantity), SUM(amount) "
            "FROM orders WHERE date(created_at) >= date(?) "
            "GROUP BY product ORDER BY SUM(amount) DESC",
            (start_date,)
        )
        product_sales = []
        for row in cursor.fetchall():
            product_sales.append({
                'product': row[0],
                'quantity': row[1] or 0,
                'amount': round(row[2] or 0, 2)
            })
        
        # 按客户统计
        cursor = conn.execute(
            "SELECT customer, COUNT(*), SUM(amount) "
            "FROM orders WHERE date(created_at) >= date(?) "
            "GROUP BY customer ORDER BY SUM(amount) DESC LIMIT 10",
            (start_date,)
        )
        customer_sales = []
        for row in cursor.fetchall():
            customer_sales.append({
                'customer': row[0],
                'orders': row[1] or 0,
                'amount': round(row[2] or 0, 2)
            })
        
        # 趋势数据（最近30天）
        cursor = conn.execute(
            "SELECT date(created_at) as date, COUNT(*), SUM(amount) "
            "FROM orders WHERE date(created_at) >= date('now', '-30 days') "
            "GROUP BY date(created_at) ORDER BY date"
        )
        trend = []
        for row in cursor.fetchall():
            trend.append({
                'date': row[0],
                'orders': row[1] or 0,
                'amount': round(row[2] or 0, 2)
            })
        
        return {
            'title': title,
            'period': period,
            'generated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_orders': total_orders or 0,
                'total_amount': round(total_amount or 0, 2),
                'avg_order_amount': round(avg_amount or 0, 2)
            },
            'product_sales': product_sales,
            'top_customers': customer_sales,
            'trend': trend
        }
    
    # ═══════════════════════════════════════════
    # 2. 库存报表
    # ═══════════════════════════════════════════
    
    def generate_inventory_report(self) -> Dict:
        """生成库存报表"""
        conn = get_conn('product.db')
        
        # 整体库存统计
        cursor = conn.execute(
            "SELECT COUNT(*), SUM(stock), SUM(stock * price) "
            "FROM product"
        )
        total_products, total_stock, total_value = cursor.fetchone()
        
        # 低库存产品
        cursor = conn.execute(
            "SELECT name, stock, min_stock, price, category "
            "FROM product WHERE stock < COALESCE(min_stock, 10) "
            "ORDER BY stock ASC"
        )
        low_stock = []
        for row in cursor.fetchall():
            low_stock.append({
                'product': row[0],
                'current_stock': row[1] or 0,
                'min_stock': row[2] or 10,
                'unit_price': row[3] or 0,
                'category': row[4],
                'status': '缺货' if (row[1] or 0) == 0 else '低库存'
            })
        
        # 按分类统计
        cursor = conn.execute(
            "SELECT category, COUNT(*), SUM(stock), SUM(stock * price) "
            "FROM product GROUP BY category"
        )
        category_stats = []
        for row in cursor.fetchall():
            category_stats.append({
                'category': row[0] or '未分类',
                'product_count': row[1] or 0,
                'total_stock': row[2] or 0,
                'inventory_value': round(row[3] or 0, 2)
            })
        
        # 库存周转率估算（基于最近30天销售）
        conn_order = get_conn('order.db')
        cursor = conn_order.execute(
            "SELECT product, SUM(quantity) FROM orders "
            "WHERE date(created_at) >= date('now', '-30 days') "
            "GROUP BY product"
        )
        sales_30d = {row[0]: row[1] or 0 for row in cursor.fetchall()}
        
        turnover = []
        cursor = conn.execute("SELECT name, stock FROM product")
        for row in cursor.fetchall():
            name, stock = row[0], row[1] or 0
            sold = sales_30d.get(name, 0)
            if stock > 0:
                turnover_rate = sold / stock
                turnover.append({
                    'product': name,
                    'current_stock': stock,
                    'sold_30d': sold,
                    'turnover_rate': round(turnover_rate, 2),
                    'suggestion': '补货' if turnover_rate > 2 else '正常' if turnover_rate > 0.5 else '滞销'
                })
        
        return {
            'title': '库存报表',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_products': total_products or 0,
                'total_stock': total_stock or 0,
                'total_inventory_value': round(total_value or 0, 2),
                'low_stock_count': len(low_stock)
            },
            'low_stock_items': low_stock,
            'category_breakdown': category_stats,
            'turnover_analysis': sorted(turnover, key=lambda x: x['turnover_rate'], reverse=True)[:20]
        }
    
    # ═══════════════════════════════════════════
    # 3. 财务报表
    # ═══════════════════════════════════════════
    
    def generate_finance_report(self, period: str = 'monthly') -> Dict:
        """生成财务报表"""
        conn = get_conn('finance.db')
        
        now = datetime.now()
        if period == 'daily':
            start_date = now.strftime('%Y-%m-%d')
            title = '财务日报'
        elif period == 'weekly':
            start_date = (now - timedelta(days=7)).strftime('%Y-%m-%d')
            title = '财务周报'
        elif period == 'monthly':
            start_date = now.strftime('%Y-%m-01')
            title = '财务月报'
        elif period == 'yearly':
            start_date = now.strftime('%Y-01-01')
            title = '财务年报'
        else:
            start_date = now.strftime('%Y-%m-01')
            title = '财务报表'
        
        # 收支汇总
        cursor = conn.execute(
            "SELECT "
            "SUM(CASE WHEN type='income' THEN amount ELSE 0 END) as income, "
            "SUM(CASE WHEN type='expense' THEN ABS(amount) ELSE 0 END) as expense, "
            "COUNT(CASE WHEN type='income' THEN 1 END) as income_count, "
            "COUNT(CASE WHEN type='expense' THEN 1 END) as expense_count "
            "FROM finance WHERE date(created_at) >= date(?)",
            (start_date,)
        )
        income, expense, income_count, expense_count = cursor.fetchone()
        
        # 按类别统计
        cursor = conn.execute(
            "SELECT type, category, SUM(amount), COUNT(*) "
            "FROM finance WHERE date(created_at) >= date(?) "
            "GROUP BY type, category ORDER BY SUM(amount) DESC",
            (start_date,)
        )
        category_breakdown = []
        for row in cursor.fetchall():
            type_, category, amount, count = row
            category_breakdown.append({
                'type': type_,
                'category': category or '其他',
                'amount': round(abs(amount) if type_ == 'expense' else amount, 2),
                'count': count or 0
            })
        
        # 每日趋势
        cursor = conn.execute(
            "SELECT date(created_at) as date, "
            "SUM(CASE WHEN type='income' THEN amount ELSE 0 END) as income, "
            "SUM(CASE WHEN type='expense' THEN ABS(amount) ELSE 0 END) as expense "
            "FROM finance WHERE date(created_at) >= date(?) "
            "GROUP BY date(created_at) ORDER BY date",
            (start_date,)
        )
        daily_trend = []
        for row in cursor.fetchall():
            daily_trend.append({
                'date': row[0],
                'income': round(row[1] or 0, 2),
                'expense': round(row[2] or 0, 2),
                'balance': round((row[1] or 0) - (row[2] or 0), 2)
            })
        
        return {
            'title': title,
            'period': period,
            'generated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_income': round(income or 0, 2),
                'total_expense': round(expense or 0, 2),
                'net_profit': round((income or 0) - (expense or 0), 2),
                'income_transactions': income_count or 0,
                'expense_transactions': expense_count or 0
            },
            'category_breakdown': category_breakdown,
            'daily_trend': daily_trend
        }
    
    # ═══════════════════════════════════════════
    # 4. 综合仪表板
    # ═══════════════════════════════════════════
    
    def generate_dashboard(self) -> Dict:
        """生成综合仪表板数据"""
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        
        # 今日销售
        conn_order = get_conn('order.db')
        cursor = conn_order.execute(
            "SELECT COUNT(*), SUM(amount) FROM orders WHERE date(created_at) = date('now')"
        )
        today_orders, today_sales = cursor.fetchone()
        
        # 本月销售
        cursor = conn_order.execute(
            "SELECT COUNT(*), SUM(amount) FROM orders WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
        )
        month_orders, month_sales = cursor.fetchone()
        
        # 库存状态
        conn_product = get_conn('product.db')
        cursor = conn_product.execute(
            "SELECT COUNT(*), SUM(stock) FROM product"
        )
        total_products, total_stock = cursor.fetchone()
        
        cursor = conn_product.execute(
            "SELECT COUNT(*) FROM product WHERE stock < COALESCE(min_stock, 10)"
        )
        low_stock_count = cursor.fetchone()[0]
        
        # 财务状态
        conn_finance = get_conn('finance.db')
        cursor = conn_finance.execute(
            "SELECT SUM(CASE WHEN type='income' THEN amount ELSE 0 END), "
            "SUM(CASE WHEN type='expense' THEN ABS(amount) ELSE 0 END) "
            "FROM finance WHERE date(created_at) = date('now')"
        )
        today_income, today_expense = cursor.fetchone()
        
        # 客户统计
        conn_customer = get_conn('customer.db')
        cursor = conn_customer.execute("SELECT COUNT(*) FROM customer")
        total_customers = cursor.fetchone()[0]
        
        # 最近订单
        cursor = conn_order.execute(
            "SELECT customer, product, amount, created_at "
            "FROM orders ORDER BY created_at DESC LIMIT 5"
        )
        recent_orders = []
        for row in cursor.fetchall():
            recent_orders.append({
                'customer': row[0],
                'product': row[1],
                'amount': round(row[2] or 0, 2),
                'time': row[3]
            })
        
        return {
            'title': '综合仪表板',
            'generated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
            'kpis': {
                'today_sales': {
                    'value': round(today_sales or 0, 2),
                    'orders': today_orders or 0,
                    'label': '今日销售额'
                },
                'month_sales': {
                    'value': round(month_sales or 0, 2),
                    'orders': month_orders or 0,
                    'label': '本月销售额'
                },
                'inventory': {
                    'total_products': total_products or 0,
                    'total_stock': total_stock or 0,
                    'low_stock_alert': low_stock_count or 0,
                    'label': '库存状态'
                },
                'finance': {
                    'today_income': round(today_income or 0, 2),
                    'today_expense': round(today_expense or 0, 2),
                    'today_balance': round((today_income or 0) - (today_expense or 0), 2),
                    'label': '今日收支'
                },
                'customers': {
                    'total': total_customers or 0,
                    'label': '客户总数'
                }
            },
            'recent_orders': recent_orders
        }


# ═══════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════

def get_report_generator() -> ReportGenerator:
    """获取报表生成器实例"""
    return ReportGenerator()


# 测试
if __name__ == '__main__':
    gen = ReportGenerator()
    
    print("=" * 50)
    print("智能报表生成器测试")
    print("=" * 50)
    
    print("\n1. 销售日报:")
    report = gen.generate_sales_report('daily')
    print(f"  订单数: {report['summary']['total_orders']}")
    print(f"  销售额: ¥{report['summary']['total_amount']}")
    
    print("\n2. 库存报表:")
    report = gen.generate_inventory_report()
    print(f"  产品总数: {report['summary']['total_products']}")
    print(f"  库存总值: ¥{report['summary']['total_inventory_value']}")
    
    print("\n3. 财务报表:")
    report = gen.generate_finance_report('monthly')
    print(f"  收入: ¥{report['summary']['total_income']}")
    print(f"  支出: ¥{report['summary']['total_expense']}")
    print(f"  净利润: ¥{report['summary']['net_profit']}")
    
    print("\n4. 综合仪表板:")
    report = gen.generate_dashboard()
    print(f"  今日销售: ¥{report['kpis']['today_sales']['value']}")
    print(f"  客户总数: {report['kpis']['customers']['total']}")
    
    print("\n测试完成!")
