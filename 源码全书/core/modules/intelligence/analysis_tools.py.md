# `core/modules/intelligence/analysis_tools.py`

> 路径：`core/modules/intelligence/analysis_tools.py` | 行数：447


---


```python
"""
高级分析工具 — 数据洞察与决策支持

提供:
- 趋势分析
- 异常检测
- 预测建议  
- 智能报表生成
"""

from core.database import get_conn, close_conn
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json


class AnalysisTools:
    """数据分析工具集"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
    
    def _connect(self, db_name: str):
        """连接数据库（使用连接池）"""
        # registry_name extraction no longer needed — get_conn accepts .db names
        path = os.path.join(self.data_dir, db_name)
        if not os.path.exists(path):
            return None
        return get_conn(db_name)
    
    def analyze_sales_trend(self, days: int = 30) -> Dict[str, Any]:
        """
        销售趋势分析
        
        Returns:
            {
                "daily_revenue": [...],
                "avg_daily": float,
                "trend": "up|down|stable",
                "growth_rate": float,
                "peak_day": str,
                "insights": [...]
            }
        """
        db = self._connect("order.db")
        if not db:
            return {"error": "订单数据库不存在"}
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 获取每日销售额
            cursor = db.execute("""
                SELECT 
                    DATE(created_at) as date,
                    SUM(total_amount) as revenue,
                    COUNT(*) as order_count
                FROM orders 
                WHERE created_at >= ? AND status != 'cancelled'
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (start_date.strftime('%Y-%m-%d'),))
            
            daily_data = []
            for row in cursor:
                daily_data.append({
                    "date": row["date"],
                    "revenue": float(row["revenue"] or 0),
                    "orders": int(row["order_count"])
                })
            
            if not daily_data:
                return {"message": "暂无销售数据", "data": []}
            
            # 计算趋势
            revenues = [d["revenue"] for d in daily_data]
            avg_revenue = sum(revenues) / len(revenues) if revenues else 0
            
            # 简单趋势判断（前半段 vs 后半段）
            mid = len(daily_data) // 2
            if mid > 0:
                first_half_avg = sum(revenues[:mid]) / mid
                second_half_avg = sum(revenues[mid:]) / (len(revenues) - mid)
                
                if second_half_avg > first_half_avg * 1.1:
                    trend = "📈 上升"
                    growth_rate = ((second_half_avg - first_half_avg) / first_half_avg) * 100
                elif second_half_avg < first_half_avg * 0.9:
                    trend = "📉 下降"
                    growth_rate = ((second_half_avg - first_half_avg) / first_half_avg) * 100
                else:
                    trend = "➡️ 平稳"
                    growth_rate = 0
            else:
                trend = "➡️ 平稳"
                growth_rate = 0
            
            # 找出峰值日
            peak_day = max(daily_data, key=lambda x: x["revenue"]) if daily_data else None
            
            # 生成洞察
            insights = []
            if growth_rate > 10:
                insights.append(f"💡 销售增长强劲 ({growth_rate:.1f}%), 考虑增加库存或推广力度")
            elif growth_rate < -10:
                insights.append(f"⚠️ 销售下滑 ({abs(growth_rate):.1f}%), 建议检查市场因素或调整策略")
            
            if peak_day:
                insights.append(f"🎯 最佳销售日是 {peak_day['date']} (¥{peak_day['revenue']:.2f})")
            
            # 低峰预警
            if len(daily_data) > 7:
                last_week = daily_data[-7:]
                low_days = [d for d in last_week if d["revenue"] < avg_revenue * 0.5]
                if low_days:
                    insights.append(f"⚠️ 最近有 {len(low_days)} 天表现不佳，需关注")
            
            return {
                "period": f"近{days}天",
                "total_revenue": sum(revenues),
                "avg_daily": round(avg_revenue, 2),
                "total_orders": sum(d["orders"] for d in daily_data),
                "trend": trend,
                "growth_rate": round(growth_rate, 2),
                "peak_day": peak_day,
                "daily_data": daily_data,
                "insights": insights,
            }
        finally:
            close_conn('order.db')
    
    def detect_anomalies(self, db_name: str, table: str, amount_field: str) -> Dict[str, Any]:
        """
        检测异常数据（超出均值±2 标准差）
        
        Returns:
            {"anomalies": [...], "stats": {...}, "suggestions": [...]}
        """
        db = self._connect(db_name)
        if not db:
            return {"error": f"数据库 {db_name} 不存在"}
        
        try:
            # 获取统计数据
            stats_cursor = db.execute(f"""
                SELECT 
                    AVG({amount_field}) as avg_val,
                    COUNT(*) as total,
                    MIN({amount_field}) as min_val,
                    MAX({amount_field}) as max_val
                FROM {table}
            """)
            stats_row = stats_cursor.fetchone()
            
            if not stats_row:
                return {"error": f"表 {table} 不存在或为空"}
            
            avg_val = float(stats_row["avg_val"] or 0)
            total = int(stats_row["total"])
            min_val = float(stats_row["min_val"] or 0)
            max_val = float(stats_row["max_val"] or 0)
            
            # 简单估算标准差（用极差/4 近似）
            std_val = (max_val - min_val) / 4 if max_val > min_val else 0
            
            lower_bound = avg_val - 2 * std_val
            upper_bound = avg_val + 2 * std_val
            
            # 查询异常值
            anomaly_cursor = db.execute(f"""
                SELECT * FROM {table}
                WHERE {amount_field} < ? OR {amount_field} > ?
                ORDER BY {amount_field}
            """, (lower_bound, upper_bound))
            
            anomalies = [dict(row) for row in anomaly_cursor]
            
            # 生成建议
            suggestions = []
            if anomalies:
                suggestions.append(f"发现 {len(anomalies)} 条异常记录，建议人工审核")
                if len(anomalies) > total * 0.1:  # 超过 10%
                    suggestions.append("⚠️ 异常比例较高，可能存在系统性问题")
            else:
                suggestions.append("✅ 未发现明显异常")
            
            return {
                "anomalies": anomalies[:20],  # 限制返回数量
                "stats": {
                    "平均值": round(avg_val, 2),
                    "最小值": round(min_val, 2),
                    "最大值": round(max_val, 2),
                    "总数": total,
                    "异常阈值": f"[{round(lower_bound, 2)}, {round(upper_bound, 2)}]"
                },
                "suggestions": suggestions
            }
        finally:
            close_conn('order.db')
    
    def predict_inventory_needs(self, product_id: str = None, days_ahead: int = 30) -> Dict[str, Any]:
        """
        基于历史销量预测库存需求
        
        Returns:
            {"predictions": [...], "recommendations": [...]}
        """
        # 需要 products 和 orders 两个数据库
        prod_db = self._connect("product.db")
        order_db = self._connect("order.db")
        
        if not prod_db or not order_db:
            return {"error": "产品或订单数据库不可用"}
        
        try:
            # 获取所有产品
            if product_id:
                cursor = prod_db.execute("SELECT * FROM product WHERE id=?", (product_id,))
            else:
                cursor = prod_db.execute("SELECT * FROM product")
            products = [dict(row) for row in cursor]
            
            predictions = []
            recommendations = []
            
            for product in products:
                name = product.get("name", "未知产品")
                current_stock = int(product.get("stock", 0))
                price = float(product.get("price", 0))
                
                # 计算月均销量（简化版：假设均匀分布）
                order_cursor = order_db.execute("""
                    SELECT COALESCE(SUM(total_amount), 0) as total_revenue,
                           COUNT(*) as order_count
                    FROM orders 
                    WHERE status != 'cancelled'
                    AND strftime('%Y%m', created_at) = strftime('%Y%m', 'now')
                """)
                month_stats = order_cursor.fetchone()
                
                if month_stats:
                    avg_monthly_revenue = float(month_stats["total_revenue"])
                    estimated_monthly_units = avg_monthly_revenue / (price * len(products)) if price > 0 else 0
                    
                    predicted_demand = estimated_monthly_units * (days_ahead / 30)
                    safety_stock = predicted_demand * 0.2  # 20% 安全库存
                    reorder_point = predicted_demand * 0.5 + safety_stock
                    
                    needs_reorder = current_stock < reorder_point
                    
                    predictions.append({
                        "product": name,
                        "current_stock": current_stock,
                        "predicted_demand_30d": round(predicted_demand, 1),
                        "safety_stock": round(safety_stock, 1),
                        "reorder_point": round(reorder_point, 1),
                        "needs_reorder": needs_reorder,
                        "recommended_order_qty": max(0, int(reorder_point * 1.5 - current_stock)) if needs_reorder else 0
                    })
                    
                    if needs_reorder:
                        recommendations.append(
                            f"⚠️ [{name}] 库存不足，建议补货 {predictions[-1]['recommended_order_qty']} 件"
                        )
            
            if not recommendations:
                recommendations.append("✅ 当前库存充足")
            
            return {
                "predictions": predictions,
                "recommendations": recommendations
            }
        finally:
            close_conn('order.db')
            close_conn('order.db')
    
    def generate_business_report(self, report_type: str = "monthly") -> str:
        """
        生成业务报告（Markdown 格式）
        
        Args:
            report_type: daily|weekly|monthly|quarterly
        
        Returns:
            Markdown 格式的完整报告
        """
        sections = []
        sections.append("# 📊 业务分析报告")
        sections.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        sections.append("")
        
        # 1. 销售概览
        sections.append("## 1️⃣ 销售概况")
        db = self._connect("order.db")
        if db:
            try:
                cursor = db.execute("""
                    SELECT 
                        COUNT(*) as total_orders,
                        COALESCE(SUM(CASE WHEN status='paid' THEN total_amount ELSE 0 END), 0) as paid_revenue,
                        COALESCE(SUM(CASE WHEN status='pending' THEN total_amount ELSE 0 END), 0) as pending_revenue,
                        COUNT(DISTINCT customer_name) as unique_customers
                    FROM orders
                    WHERE strftime('%Y%m', created_at) = strftime('%Y%m', 'now')
                """)
                stats = cursor.fetchone()
                if stats:
                    sections.append(f"- ✅ **本月订单数**: {stats['total_orders']}")
                    sections.append(f"- 💰 **已收款**: ¥{stats['paid_revenue']:.2f}")
                    sections.append(f"- ⏳ **待收款**: ¥{stats['pending_revenue']:.2f}")
                    sections.append(f"- 👥 **独立客户**: {stats['unique_customers']}")
            finally:
                close_conn('order.db')
        sections.append("")
        
        # 2. 库存预警
        sections.append("## 2️⃣ 库存预警")
        prod_db = self._connect("product.db")
        if prod_db:
            try:
                low_stock = prod_db.execute("""
                    SELECT name, stock, price 
                    FROM product 
                    WHERE stock < 10 
                    ORDER BY stock ASC
                    LIMIT 10
                """).fetchall()
                
                if low_stock:
                    sections.append("| 产品 | 库存 | 单价 |")
                    sections.append("|------|------|------|")
                    for row in low_stock:
                        sections.append(f"| {row[0]} | {row[1]} | ¥{row[2]} |")
                else:
                    sections.append("✅ 库存充足")
            finally:
                close_conn('product.db')
        sections.append("")
        
        # 3. 客户分析
        sections.append("## 3️⃣ 客户分析")
        cust_db = self._connect("customer.db")
        if cust_db:
            try:
                level_stats = cust_db.execute("""
                    SELECT level, COUNT(*) as count
                    FROM customer
                    GROUP BY level
                """).fetchall()
                
                if level_stats:
                    sections.append("| 等级 | 人数 |")
                    sections.append("|------|------|")
                    for row in level_stats:
                        sections.append(f"| {row[0] or '未分级'} | {row[1]} |")
            finally:
                close_conn('customer.db')
        sections.append("")
        
        # 4. 财务摘要
        sections.append("## 4️⃣ 财务摘要")
        fin_db = self._connect("finance.db")
        if fin_db:
            try:
                fin_stats = fin_db.execute("""
                    SELECT 
                        SUM(CASE WHEN type='income' THEN amount ELSE 0 END) as income,
                        SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense
                    FROM finance
                    WHERE strftime('%Y%m', date) = strftime('%Y%m', 'now')
                """).fetchone()
                
                if fin_stats:
                    income = float(fin_stats["income"] or 0)
                    expense = float(fin_stats["expense"] or 0)
                    profit = income - expense
                    sections.append(f"- 💵 **本月收入**: ¥{income:.2f}")
                    sections.append(f"- 💸 **本月支出**: ¥{expense:.2f}")
                    sections.append(f"- 📈 **净利润**: ¥{profit:.2f}")
            finally:
                close_conn('finance.db')
        sections.append("")
        
        sections.append("---")
        sections.append("*本报告由 Iqra AI 自动生成*")
        
        return "\n".join(sections)


def register_analysis_tools(registry, data_dir: str):
    """注册分析工具到 ToolRegistry"""
    from core.modules.intelligence.tool_registry import ToolDefinition
    
    analyzer = AnalysisTools(data_dir)
    
    registry.add_tool(ToolDefinition(
        name="analyze_sales_trend",
        description="分析销售趋势：获取指定天数内的销售走势、增长率、峰值日等洞察",
        parameters={
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "分析天数，默认 30 天", "default": 30}
            }
        },
        handler=lambda days=30: analyzer.analyze_sales_trend(days),
    ))
    
    registry.add_tool(ToolDefinition(
        name="detect_anomalies",
        description="检测数据异常：自动识别超出正常范围的数据点",
        parameters={
            "type": "object",
            "properties": {
                "db_name": {"type": "string", "description": "数据库文件名，如 order.db"},
                "table": {"type": "string", "description": "表名"},
                "amount_field": {"type": "string", "description": "金额/数值字段名"}
            }
        },
        handler=lambda db_name, table, amount_field: analyzer.detect_anomalies(db_name, table, amount_field),
    ))
    
    registry.add_tool(ToolDefinition(
        name="predict_inventory_needs",
        description="预测库存需求：基于历史销量给出补货建议",
        parameters={
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "产品 ID（可选，留空则分析所有产品）"},
                "days_ahead": {"type": "integer", "description": "预测未来多少天，默认 30 天", "default": 30}
            }
        },
        handler=lambda product_id=None, days_ahead=30: analyzer.predict_inventory_needs(product_id, days_ahead),
    ))
    
    registry.add_tool(ToolDefinition(
        name="generate_business_report",
        description="生成业务报告：输出 Markdown 格式的综合业务分析报告",
        parameters={
            "type": "object",
            "properties": {
                "report_type": {"type": "string", "description": "报告类型：daily|weekly|monthly", "default": "monthly"}
            }
        },
        handler=lambda report_type="monthly": analyzer.generate_business_report(report_type),
    ))

```
