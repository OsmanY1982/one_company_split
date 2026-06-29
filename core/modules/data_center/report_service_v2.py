# -*- coding: utf-8 -*-
"""
数据报表 Service V2 - 增强版
支持数据大屏、BI看板、实时数据
"""
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from core.database import get_conn
from core.paths import DATA_DIR


def _get_scalar(db_name: str, query: str, params: tuple = (), default=0):
    """查询单个标量值"""
    try:
        conn = get_conn(db_name)
        r = conn.execute(query, params).fetchone()
        return r[0] if r and r[0] is not None else default
    except Exception:
        return default


def _get_rows(db_name: str, query: str, params: tuple = ()) -> list:
    """查询多行"""
    try:
        conn = get_conn(db_name)
        return conn.execute(query, params).fetchall()
    except Exception:
        return []


class ReportServiceV2:
    """增强版报表服务"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        
    def get_dashboard_data(self) -> dict:
        """获取数据大屏全部数据"""
        return {
            # KPI 指标
            'today_sales': self._get_today_sales(),
            'today_orders': self._get_today_orders(),
            'active_members': self._get_active_members(),
            'stock_alerts': self._get_stock_alerts(),
            'profit_margin': self._get_profit_margin(),
            'satisfaction': self._get_satisfaction(),
            
            # 趋势数据
            'sales_trend': self._get_sales_trend(),
            'member_growth': self._get_member_growth(),
            'category_distribution': self._get_category_distribution(),
            
            # 详细数据
            'recent_orders': self._get_recent_orders(),
            'top_products': self._get_top_products(),
            'finance_summary': self._get_finance_summary(),
        }
    
    def _get_today_sales(self) -> float:
        """今日销售额"""
        today = datetime.now().strftime('%Y-%m-%d')
        return _get_scalar(
            "order.db",
            "SELECT SUM(amount * quantity) FROM orders WHERE date(created_at) = ?",
            (today,),
            0.0
        )
    
    def _get_today_orders(self) -> int:
        """今日订单数"""
        today = datetime.now().strftime('%Y-%m-%d')
        return _get_scalar(
            "order.db",
            "SELECT COUNT(*) FROM orders WHERE date(created_at) = ?",
            (today,),
            0
        )
    
    def _get_active_members(self) -> int:
        """活跃会员数"""
        return _get_scalar("member.db", "SELECT COUNT(*) FROM member WHERE status = '正常'")
    
    def _get_stock_alerts(self) -> int:
        """库存预警数"""
        return _get_scalar("product.db", "SELECT COUNT(*) FROM products WHERE stock < 10")
    
    def _get_profit_margin(self) -> float:
        """毛利率"""
        total_income = _get_scalar("finance.db", "SELECT SUM(amount) FROM finance WHERE type='income'")
        total_cost = _get_scalar("finance.db", "SELECT SUM(ABS(amount)) FROM finance WHERE type='expense'")
        if total_income > 0:
            return round((total_income - total_cost) / total_income * 100, 1)
        return 0.0
    
    def _get_satisfaction(self) -> float:
        """客户满意度（模拟）"""
        # 实际应从评价表获取，这里模拟
        return 4.8
    
    def _get_sales_trend(self) -> List[Dict]:
        """销售趋势（近7天）"""
        rows = _get_rows(
            "order.db",
            "SELECT date(created_at) as d, SUM(amount * quantity) as total "
            "FROM orders GROUP BY d ORDER BY d DESC LIMIT 7"
        )
        result = []
        for row in rows:
            result.append({
                'date': datetime.strptime(row[0], '%Y-%m-%d'),
                'amount': float(row[1] or 0)
            })
        return result
    
    def _get_member_growth(self) -> List[Dict]:
        """会员增长趋势（近30天）"""
        rows = _get_rows(
            "member.db",
            "SELECT date(created_at) as d, COUNT(*) as cnt "
            "FROM member GROUP BY d ORDER BY d DESC LIMIT 30"
        )
        result = []
        for row in rows:
            result.append({
                'date': datetime.strptime(row[0], '%Y-%m-%d') if row[0] else datetime.now(),
                'count': row[1]
            })
        return result
    
    def _get_category_distribution(self) -> Dict[str, float]:
        """产品分类分布"""
        rows = _get_rows(
            "product.db",
            "SELECT category, COUNT(*) FROM products GROUP BY category"
        )
        return {row[0]: row[1] for row in rows}
    
    def _get_recent_orders(self) -> List[Dict]:
        """最近订单"""
        rows = _get_rows(
            "order.db",
            "SELECT order_no, customer, product, amount, status, created_at "
            "FROM orders ORDER BY created_at DESC LIMIT 10"
        )
        result = []
        for row in rows:
            result.append({
                'order_no': row[0],
                'customer': row[1],
                'product': row[2],
                'amount': row[3],
                'status': row[4],
                'created_at': row[5]
            })
        return result
    
    def _get_top_products(self) -> List[Dict]:
        """热销产品"""
        rows = _get_rows(
            "order.db",
            "SELECT product, SUM(quantity) as total_qty, SUM(amount * quantity) as total_amount "
            "FROM orders GROUP BY product ORDER BY total_qty DESC LIMIT 5"
        )
        result = []
        for row in rows:
            result.append({
                'product': row[0],
                'quantity': row[1],
                'amount': float(row[2] or 0)
            })
        return result
    
    def _get_finance_summary(self) -> Dict:
        """财务汇总"""
        total_income = _get_scalar("finance.db", "SELECT SUM(amount) FROM finance WHERE type='income'")
        total_expense = _get_scalar("finance.db", "SELECT SUM(ABS(amount)) FROM finance WHERE type='expense'")
        return {
            'income': total_income,
            'expense': total_expense,
            'profit': total_income - total_expense
        }


# 兼容旧版接口
def get_report_data() -> dict:
    """获取全部报表数据"""
    return {
        "total_income": _get_scalar(
            "finance.db",
            "SELECT SUM(amount) FROM finance WHERE type='income'"),
        "total_expense": _get_scalar(
            "finance.db",
            "SELECT SUM(ABS(amount)) FROM finance WHERE type='expense'"),
        "total_members": _get_scalar(
            "member.db",
            "SELECT COUNT(*) FROM member"),
        "total_customers": _get_scalar(
            "customer.db",
            "SELECT COUNT(*) FROM customer"),
        "total_orders": _get_scalar(
            "order.db",
            "SELECT COUNT(*) FROM orders"),
        "total_order_amount": _get_scalar(
            "order.db",
            "SELECT SUM(amount * quantity) FROM orders"),
        "total_staff": _get_scalar(
            "staff.db",
            "SELECT COUNT(*) FROM staff"),
        "total_products": _get_scalar(
            "product.db",
            "SELECT COUNT(*) FROM products"),
    }


def get_chart_data() -> dict:
    """获取图表数据"""
    # 收支趋势（近7天）
    trend_rows = _get_rows(
        "finance.db",
        "SELECT date(date) as d, "
        "SUM(CASE WHEN type='income' THEN amount ELSE 0 END) as inc, "
        "SUM(CASE WHEN type='expense' THEN ABS(amount) ELSE 0 END) as exp "
        "FROM finance GROUP BY d ORDER BY d DESC LIMIT 7"
    )

    # 会员等级分布
    level_rows = _get_rows(
        "member.db",
        "SELECT level, COUNT(*) FROM member GROUP BY level"
    )

    return {
        "trend": trend_rows,
        "levels": level_rows,
    }
