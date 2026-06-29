"""
BI商业智能服务
数据分析、可视化报表、数据看板
"""

import json
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class BIService:
    """BI商业智能服务"""

    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path

    def get_kpi_dashboard(self) -> Dict:
        """获取KPI看板数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # 今日订单
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                cursor = conn.execute(
                    "SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total FROM orders WHERE created_at >= ?",
                    (int(today_start.timestamp()),)
                )
                today_orders = dict(cursor.fetchone())

                # 本月订单
                month_start = today_start.replace(day=1)
                cursor = conn.execute(
                    "SELECT COUNT(*) as count, COALESCE(SUM(total_amount), 0) as total FROM orders WHERE created_at >= ?",
                    (int(month_start.timestamp()),)
                )
                month_orders = dict(cursor.fetchone())

                # 产品数量
                cursor = conn.execute("SELECT COUNT(*) as count FROM products")
                product_count = cursor.fetchone()[0]

                # 客户数量
                cursor = conn.execute("SELECT COUNT(*) as count FROM customers")
                customer_count = cursor.fetchone()[0]

            return {
                "success": True,
                "today": {
                    "order_count": today_orders["count"],
                    "revenue": today_orders["total"],
                },
                "this_month": {
                    "order_count": month_orders["count"],
                    "revenue": month_orders["total"],
                },
                "products_count": product_count,
                "customers_count": customer_count,
            }

        except Exception as e:
            return {"success": False, "message": f"获取KPI失败: {e}"}

    def get_sales_trend(self, days: int = 30) -> Dict:
        """获取销售趋势"""
        try:
            start_date = datetime.now() - timedelta(days=days)

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """SELECT DATE(created_at, 'unixepoch') as date,
                              COUNT(*) as count, 
                              COALESCE(SUM(total_amount), 0) as total
                       FROM orders 
                       WHERE created_at >= ?
                       GROUP BY DATE(created_at, 'unixepoch')
                       ORDER BY date""",
                    (int(start_date.timestamp()),)
                )
                trend_data = [dict(row) for row in cursor.fetchall()]

            return {"success": True, "trend": trend_data}
        except Exception as e:
            return {"success": False, "message": f"获取趋势失败: {e}"}

    def get_top_products(self, limit: int = 10) -> Dict:
        """获取热销产品排名"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """SELECT oi.product_id, p.name as product_name,
                              SUM(oi.quantity) as total_quantity,
                              SUM(oi.quantity * oi.price) as total_revenue
                       FROM order_items oi
                       LEFT JOIN products p ON oi.product_id = p.id
                       GROUP BY oi.product_id
                       ORDER BY total_revenue DESC
                       LIMIT ?""",
                    (limit,)
                )
                products = [dict(row) for row in cursor.fetchall()]

            return {"success": True, "products": products}
        except Exception as e:
            return {"success": False, "message": f"获取排名失败: {e}"}

    def get_customer_analysis(self) -> Dict:
        """获取客户分析"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                cursor = conn.execute(
                    """SELECT c.id, c.name,
                              COUNT(o.id) as order_count,
                              COALESCE(SUM(o.total_amount), 0) as total_spent
                       FROM customers c
                       LEFT JOIN orders o ON c.id = o.customer_id
                       GROUP BY c.id
                       ORDER BY total_spent DESC
                       LIMIT 20"""
                )
                customers = [dict(row) for row in cursor.fetchall()]

            return {"success": True, "customers": customers}
        except Exception as e:
            return {"success": False, "message": f"获取分析失败: {e}"}

    def export_dashboard(self, format: str = "json") -> Dict:
        """导出看板数据"""
        dashboard = self.get_kpi_dashboard()

        if format == "json":
            output_path = f"exports/dashboard_{datetime.now().strftime('%Y%m%d')}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(dashboard, f, ensure_ascii=False, indent=2)
            return {"success": True, "file_path": output_path}

        return {"success": False, "message": f"不支持的格式: {format}"}

