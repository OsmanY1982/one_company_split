# -*- coding: utf-8 -*-
"""
数据报表 — Service 层
"""
import os
from core.database import get_conn


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