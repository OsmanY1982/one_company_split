"""
图表服务
支持多种图表类型的数据可视化
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from core.database import get_conn, close_conn, execute, query_rows, query_one


class ChartService:
    """图表服务"""

    def __init__(self, db_name: str = "order"):
        self.db_name = db_name

    def get_bar_chart_data(self,
                            query: str,
                            x_field: str,
                            y_field: str,
                            params: Optional[List] = None,
                            db_name: Optional[str] = None) -> Dict:
        """获取柱状图数据"""
        try:
            with get_conn(db_name or self.db_name) as conn:
                cursor = conn.execute(query, params or [])
                rows = cursor.fetchall()

            labels = []
            values = []

            for row in rows:
                d = dict(row)
                labels.append(str(d.get(x_field, "")))
                values.append(float(d.get(y_field, 0)))

            return {
                "success": True,
                "chart_type": "bar",
                "labels": labels,
                "values": values,
            }

        except Exception as e:
            return {"success": False, "message": f"获取数据失败: {e}"}

    def get_pie_chart_data(self,
                            query: str,
                            label_field: str,
                            value_field: str,
                            params: Optional[List] = None,
                            db_name: Optional[str] = None) -> Dict:
        """获取饼图数据"""
        try:
            with get_conn(db_name or self.db_name) as conn:
                cursor = conn.execute(query, params or [])
                rows = cursor.fetchall()

            data = []
            for row in rows:
                d = dict(row)
                data.append({
                    "label": str(d.get(label_field, "")),
                    "value": float(d.get(value_field, 0)),
                })

            return {
                "success": True,
                "chart_type": "pie",
                "data": data,
            }

        except Exception as e:
            return {"success": False, "message": f"获取数据失败: {e}"}

    def get_line_chart_data(self,
                             query: str,
                             x_field: str,
                             y_field: str,
                             params: Optional[List] = None,
                             db_name: Optional[str] = None) -> Dict:
        """获取折线图数据"""
        try:
            with get_conn(db_name or self.db_name) as conn:
                cursor = conn.execute(query, params or [])
                rows = cursor.fetchall()

            labels = []
            values = []

            for row in rows:
                d = dict(row)
                labels.append(str(d.get(x_field, "")))
                values.append(float(d.get(y_field, 0)))

            return {
                "success": True,
                "chart_type": "line",
                "labels": labels,
                "values": values,
            }

        except Exception as e:
            return {"success": False, "message": f"获取数据失败: {e}"}

    def get_sales_chart(self, year: Optional[int] = None, month: Optional[int] = None) -> Dict:
        """获取销售图表数据"""
        if year is None:
            year = datetime.now().year

        params = [year]
        query = """SELECT strftime('%m', created_at, 'unixepoch') as month,
                          COALESCE(SUM(total_amount), 0) as total,
                          COUNT(*) as count
                   FROM orders 
                   WHERE strftime('%Y', created_at, 'unixepoch') = ?
                   GROUP BY month ORDER BY month"""

        if month:
            query = query.replace("WHERE strftime('%Y',", "WHERE CAST(strftime('%m', created_at, 'unixepoch') AS INTEGER) = ? AND CAST(strftime('%Y',")
            params = [month, year]

        return self.get_bar_chart_data(query, "month", "total", params)

    def get_inventory_chart(self) -> Dict:
        """获取库存图表数据"""
        query = """SELECT name, stock 
                   FROM products 
                   WHERE stock > 0 
                   ORDER BY stock DESC 
                   LIMIT 20"""

        return self.get_bar_chart_data(query, "name", "stock", db_name="product")

    def generate_chart_js(self, chart_data: Dict) -> str:
        """生成Chart.js配置"""
        chart_type = chart_data.get("chart_type", "bar")
        labels = json.dumps(chart_data.get("labels", []))
        values = json.dumps(chart_data.get("values", []))

        return f"""
var ctx = document.getElementById('chart').getContext('2d');
new Chart(ctx, {{
    type: '{chart_type}',
    data: {{
        labels: {labels},
        datasets: [{{
            label: '数据',
            data: {values},
            backgroundColor: 'rgba(54, 162, 235, 0.5)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false
    }}
}});
"""


    # ── ChartWindow 所需的数据接口 ──

    def get_dashboard_data(self) -> Dict:
        """获取仪表盘汇总数据"""
        try:
            today_orders, today_revenue = self._get_period_metrics(0)
            week_orders, week_revenue = self._get_period_metrics(7)
            month_orders, month_revenue = self._get_period_metrics(30)

            with get_conn('customer') as conn:
                cur = conn.execute("SELECT COUNT(*) FROM customers")
                total_customers = cur.fetchone()[0]

            with get_conn('product') as conn:
                cur = conn.execute("SELECT COUNT(*) FROM products")
                total_products = cur.fetchone()[0]

            return {
                "today": {"orders": today_orders, "revenue": today_revenue},
                "week": {"orders": week_orders, "revenue": week_revenue},
                "month": {"orders": month_orders, "revenue": month_revenue},
                "total_customers": total_customers,
                "total_products": total_products,
            }
        except Exception:
            return {
                "today": {"orders": 0, "revenue": 0},
                "week": {"orders": 0, "revenue": 0},
                "month": {"orders": 0, "revenue": 0},
                "total_customers": 0,
                "total_products": 0,
            }

    def get_sales_trend(self, days: int = 30) -> Dict:
        """获取销售趋势数据（折线图）"""
        try:
            with get_conn('order') as conn:
                cursor = conn.execute(
                    """SELECT DATE(created_at, 'unixepoch') as date_label,
                              COALESCE(SUM(total_amount), 0) as amount,
                              COUNT(*) as cnt
                       FROM orders
                       WHERE created_at >= CAST(strftime('%s', 'now') AS INTEGER) - ?
                       GROUP BY date_label ORDER BY date_label""",
                    (days * 86400,),
                )
                rows = cursor.fetchall()

            labels = [row["date_label"] for row in rows]
            values = [float(row["amount"]) for row in rows]

            return {
                "title": f"近{days}天销售趋势",
                "labels": labels or [f"第{i+1}天" for i in range(days)],
                "datasets": [{"label": "销售额", "data": values or [0]*days, "borderColor": "#2196F3"}],
            }
        except Exception:
            return {
                "title": f"近{days}天销售趋势",
                "labels": [f"第{i+1}天" for i in range(days)],
                "datasets": [{"label": "销售额", "data": [0]*days, "borderColor": "#2196F3"}],
            }

    def get_product_category_distribution(self) -> Dict:
        """获取产品分类分布（饼图）"""
        try:
            with get_conn('product') as conn:
                cursor = conn.execute(
                    """SELECT category, COUNT(*) as cnt
                       FROM products GROUP BY category ORDER BY cnt DESC"""
                )
                rows = cursor.fetchall()

            labels = [row["category"] or "未分类" for row in rows] if rows else ["示例A", "示例B", "示例C"]
            values = [row["cnt"] for row in rows] if rows else [40, 35, 25]
            colors = ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"]

            return {
                "title": "产品分类分布",
                "labels": labels,
                "datasets": [{"label": "数量", "data": values, "backgroundColor": colors[:len(labels)]}],
            }
        except Exception:
            return {
                "title": "产品分类分布",
                "labels": ["暂无数据"],
                "datasets": [{"label": "数量", "data": [1], "backgroundColor": ["#CCCCCC"]}],
            }

    def get_monthly_comparison(self, months: int = 6) -> Dict:
        """获取月度对比数据（柱状图）"""
        try:
            with get_conn('order') as conn:
                cursor = conn.execute(
                    """SELECT strftime('%Y-%m', created_at, 'unixepoch') as ym,
                              COALESCE(SUM(total_amount), 0) as amount,
                              COUNT(*) as cnt
                       FROM orders
                       GROUP BY ym ORDER BY ym DESC LIMIT ?""",
                    (months,),
                )
                rows = list(cursor.fetchall())
                rows.reverse()

            labels = [row["ym"] for row in rows]
            values = [float(row["amount"]) for row in rows]

            return {
                "title": f"近{months}月销售对比",
                "labels": labels or [f"第{i+1}月" for i in range(months)],
                "datasets": [{"label": "销售额", "data": values or [0]*months, "backgroundColor": "#FF9800"}],
            }
        except Exception:
            return {
                "title": f"近{months}月销售对比",
                "labels": [f"第{i+1}月" for i in range(months)],
                "datasets": [{"label": "销售额", "data": [0]*months, "backgroundColor": "#FF9800"}],
            }

    def get_top_products(self, limit: int = 10) -> Dict:
        """获取热销产品排行（柱状图）"""
        try:
            with get_conn('order') as conn:
                cursor = conn.execute(
                    """SELECT p.name, COUNT(o.id) as cnt, COALESCE(SUM(o.total_amount), 0) as total
                       FROM products p LEFT JOIN orders o ON p.id = o.product_id
                       GROUP BY p.id ORDER BY cnt DESC LIMIT ?""",
                    (limit,),
                )
                rows = cursor.fetchall()

            labels = [row["name"] for row in rows]
            values = [row["cnt"] for row in rows]

            return {
                "title": f"热销产品 TOP{limit}",
                "labels": labels or [f"产品{i+1}" for i in range(limit)],
                "datasets": [{"label": "销量", "data": values or [0]*limit, "backgroundColor": "#4CAF50"}],
            }
        except Exception:
            return {
                "title": f"热销产品 TOP{limit}",
                "labels": [f"产品{i+1}" for i in range(limit)],
                "datasets": [{"label": "销量", "data": [0]*limit, "backgroundColor": "#4CAF50"}],
            }

    def get_customer_analysis(self) -> Dict:
        """获取客户分析数据（饼图）"""
        try:
            with get_conn('customer') as conn:
                cursor = conn.execute(
                    """SELECT level, COUNT(*) as cnt
                       FROM customers GROUP BY level ORDER BY cnt DESC"""
                )
                rows = cursor.fetchall()

            labels = [row["level"] or "普通" for row in rows] if rows else ["普通客户", "VIP客户", "潜在客户"]
            values = [row["cnt"] for row in rows] if rows else [60, 25, 15]
            colors = ["#36A2EB", "#FFCE56", "#4BC0C0", "#FF6384", "#9966FF"]

            return {
                "title": "客户价值分布",
                "labels": labels,
                "datasets": [{"label": "数量", "data": values, "backgroundColor": colors[:len(labels)]}],
            }
        except Exception:
            return {
                "title": "客户价值分布",
                "labels": ["暂无数据"],
                "datasets": [{"label": "数量", "data": [1], "backgroundColor": ["#CCCCCC"]}],
            }

    def _get_period_metrics(self, days: int = 0):
        """内部辅助：获取指定天数内的订单数和营收"""
        try:
            if days == 0:
                where = "DATE(created_at, 'unixepoch') = DATE('now')"
            else:
                where = f"created_at >= CAST(strftime('%s', 'now') AS INTEGER) - {days * 86400}"
            with get_conn('order') as conn:
                cur = conn.execute(
                    f"SELECT COUNT(*), COALESCE(SUM(total_amount), 0) FROM orders WHERE {where}"
                )
                row = cur.fetchone()
                return row[0], float(row[1] or 0)
        except Exception:
            return 0, 0.0
