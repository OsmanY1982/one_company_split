# `iqra/services/chart_service.py`

> 路径：`iqra/services/chart_service.py` | 行数：162


---


```python
"""
图表服务
支持多种图表类型的数据可视化
"""

import json
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime


class ChartService:
    """图表服务"""

    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path

    def get_bar_chart_data(self,
                            query: str,
                            x_field: str,
                            y_field: str,
                            params: Optional[List] = None) -> Dict:
        """获取柱状图数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
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
                            params: Optional[List] = None) -> Dict:
        """获取饼图数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
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
                             params: Optional[List] = None) -> Dict:
        """获取折线图数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
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

        return self.get_bar_chart_data(query, "name", "stock")

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


```
