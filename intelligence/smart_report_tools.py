"""
Iqra 智能报告工具 — 补充已有模块未覆盖的报告能力

注意：以下功能在已有模块中已存在，此文件不重复：
- 销售趋势分析 → analysis_tools.analyze_sales_trend
- 每日简报 → automation_tools.generate_daily_summary
- 数据导出 → automation_tools.export_data_to_csv
- 业务综合报告 → analysis_tools.generate_business_report

此文件只补充：客户消费排行、产品库存预警报告
"""

import os
from core.database import get_conn, close_conn
from datetime import datetime


def generate_customer_ranking(data_dir: str) -> dict:
    """生成客户消费排行榜（已有模块未覆盖）"""
    db_path = os.path.join(data_dir, "order.db")
    if not os.path.exists(db_path):
        return {"message": "无订单数据", "data": []}
    
    db = get_conn('order.db')
    try:
        rows = [dict(r) for r in db.execute(
            "SELECT customer_name, COUNT(*) as order_count, "
            "SUM(total_amount) as total_spent "
            "FROM orders GROUP BY customer_name "
            "ORDER BY total_spent DESC LIMIT 10"
        ).fetchall()]
        
        ranking = [{"排名": i+1, "客户": r["customer_name"],
                    "订单数": r["order_count"], "总消费": round(r["total_spent"], 2)}
                   for i, r in enumerate(rows)]
        
        return {"message": f"客户排行 TOP {len(ranking)}", "data": ranking}
    finally:
        close_conn('order.db')


def generate_product_performance(data_dir: str) -> dict:
    """生成产品库存预警报告（已有query_products只查数据，无预警）"""
    db_path = os.path.join(data_dir, "product.db")
    if not os.path.exists(db_path):
        return {"message": "无产品数据", "data": []}
    
    db = get_conn('product.db')
    try:
        rows = [dict(r) for r in db.execute(
            "SELECT name, price, stock, category FROM product "
            "ORDER BY stock ASC LIMIT 20"
        ).fetchall()]
        
        results = []
        for r in rows:
            stock = r["stock"]
            status = "库存充足" if stock > 50 else "库存偏低" if stock > 10 else "库存告急"
            results.append({
                "产品": r["name"], "价格": r["price"], "库存": stock,
                "类别": r["category"], "状态": status
            })
        
        alert_count = sum(1 for r in results if r["状态"] == "库存告急")
        return {"message": f"产品报告 {len(results)} 件，{alert_count} 件库存告急", "data": results}
    finally:
        close_conn('product.db')


def register_smart_report_tools(registry, data_dir: str):
    """注册智能报告工具（仅补充已有模块未覆盖的功能）"""
    from core.modules.intelligence.tool_registry import ToolDefinition
    
    registry.add_tool(ToolDefinition(
        name="customer_ranking",
        description="客户消费排行榜 TOP10（按总消费排序）",
        parameters={"type": "object", "properties": {}},
        handler=lambda: generate_customer_ranking(data_dir),
    ))
    
    registry.add_tool(ToolDefinition(
        name="product_performance",
        description="产品库存预警报告：标记库存充足/偏低/告急状态",
        parameters={"type": "object", "properties": {}},
        handler=lambda: generate_product_performance(data_dir),
    ))