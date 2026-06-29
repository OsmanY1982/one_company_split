# `iqra/modules/intelligence/inventory_tools.py`

> 路径：`iqra/modules/intelligence/inventory_tools.py` | 行数：322


---


```python
"""
库存管理工具 — 商品库存追踪与预警

提供:
- 库存查询
- 库存预警（低库存/临期）
- 出入库记录
- 库存盘点
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


def _connect(db_dir: str, db_name: str) -> Optional[sqlite3.Connection]:
    """连接数据库"""
    path = os.path.join(db_dir, db_name)
    if not os.path.exists(path):
        return None
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
    return conn


def _dict_rows(cursor) -> list[dict]:
    return [dict(r) for r in cursor.fetchall()]


# ═══════════════════════════════════════════
# 库存查询
# ═══════════════════════════════════════════

def query_inventory(data_dir: str, category: str = "", low_stock_only: bool = False) -> dict:
    """
    查询库存
    
    Args:
        category: 产品分类筛选
        low_stock_only: 只查低库存商品
        
    Returns:
        {
            "message": "...",
            "data": [{"产品": "...", "库存": N, "类别": "...", "状态": "正常/低库存"}]
        }
    """
    # 尝试多个可能的数据库名
    db_names = ["products.db", "product.db", "inventory.db"]
    db = None
    db_path = ""
    
    for name in db_names:
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            db = _connect(data_dir, name)
            db_path = path
            break
    
    if not db:
        return {"message": "无产品库存数据", "data": []}
    
    try:
        # 检查表结构
        tables = _dict_rows(db.execute("SELECT name FROM sqlite_master WHERE type='table'"))
        table_names = [t["name"] for t in tables]
        
        if "products" not in table_names and "inventory" not in table_names:
            return {"message": "未找到库存表", "data": []}
        
        table_name = "products" if "products" in table_names else "inventory"
        
        # 构建查询
        conditions = []
        params = []
        
        if category:
            conditions.append("category LIKE ?")
            params.append(f"%{category}%")
        
        if low_stock_only:
            # 假设低库存阈值为 10
            conditions.append("(stock IS NOT NULL AND stock < 10)")
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT name, stock, category, price 
            FROM {table_name}
            {where_clause}
            ORDER BY stock ASC
            LIMIT 100
        """
        
        rows = _dict_rows(db.execute(query, params))
        
        items = []
        for r in rows:
            stock = r.get("stock") or 0
            status = "🔴 低库存" if stock < 10 else "🟡 紧张" if stock < 50 else "🟢 充足"
            items.append({
                "产品": r.get("name", ""),
                "库存": stock,
                "类别": r.get("category", ""),
                "单价": r.get("price", 0),
                "状态": status
            })
        
        low_count = sum(1 for i in items if "低库存" in i["状态"])
        return {"message": f"{len(items)} 件商品，其中 {low_count} 件低库存", "data": items}
    
    finally:
        db.close()


# ═══════════════════════════════════════════
# 库存预警
# ═══════════════════════════════════════════

def get_inventory_alerts(data_dir: str, threshold: int = 10) -> dict:
    """
    获取库存预警列表
    
    Args:
        threshold: 低库存阈值
        
    Returns:
        {
            "critical": [...],  # 库存为 0 或负数
            "low": [...],       # 低于阈值
            "message": "..."
        }
    """
    db_names = ["products.db", "product.db", "inventory.db"]
    db = None
    
    for name in db_names:
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            db = _connect(data_dir, name)
            break
    
    if not db:
        return {"message": "无库存数据", "critical": [], "low": []}
    
    try:
        tables = _dict_rows(db.execute("SELECT name FROM sqlite_master WHERE type='table'"))
        table_names = [t["name"] for t in tables]
        
        if "products" not in table_names and "inventory" not in table_names:
            return {"message": "未找到库存表", "critical": [], "low": []}
        
        table_name = "products" if "products" in table_names else "inventory"
        
        # 严重预警（库存<=0）
        critical_rows = _dict_rows(db.execute(f"""
            SELECT name, stock, category FROM {table_name} 
            WHERE stock IS NOT NULL AND stock <= 0
            ORDER BY stock ASC
        """))
        
        critical = [{
            "产品": r["name"],
            "库存": r["stock"],
            "类别": r.get("category", "")
        } for r in critical_rows]
        
        # 低库存预警
        low_rows = _dict_rows(db.execute(f"""
            SELECT name, stock, category FROM {table_name}
            WHERE stock IS NOT NULL AND stock > 0 AND stock < ?
            ORDER BY stock ASC
        """, (threshold,)))
        
        low = [{
            "产品": r["name"],
            "库存": r["stock"],
            "类别": r.get("category", "")
        } for r in low_rows]
        
        return {
            "message": f"严重预警:{len(critical)} 低库存预警:{len(low)}",
            "critical": critical,
            "low": low
        }
    
    finally:
        db.close()


# ═══════════════════════════════════════════
# 库存统计
# ═══════════════════════════════════════════

def get_inventory_summary(data_dir: str) -> dict:
    """
    库存概览统计
    
    Returns:
        {
            "total_products": N,
            "total_stock_value": float,
            "low_stock_count": N,
            "out_of_stock_count": N,
            "by_category": {...}
        }
    """
    db_names = ["products.db", "product.db", "inventory.db"]
    db = None
    
    for name in db_names:
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            db = _connect(data_dir, name)
            break
    
    if not db:
        return {"message": "无库存数据", "data": {}}
    
    try:
        tables = _dict_rows(db.execute("SELECT name FROM sqlite_master WHERE type='table'"))
        table_names = [t["name"] for t in tables]
        
        if "products" not in table_names and "inventory" not in table_names:
            return {"message": "未找到库存表", "data": {}}
        
        table_name = "products" if "products" in table_names else "inventory"
        
        # 总产品数
        total_products = db.execute(f"SELECT COUNT(*) as c FROM {table_name}").fetchone()["c"]
        
        # 总库存价值
        stock_value = db.execute(f"""
            SELECT COALESCE(SUM(stock * price), 0) as v 
            FROM {table_name} 
            WHERE stock IS NOT NULL AND price IS NOT NULL
        """).fetchone()["v"]
        
        # 低库存数量
        low_stock = db.execute(f"""
            SELECT COUNT(*) as c FROM {table_name}
            WHERE stock IS NOT NULL AND stock > 0 AND stock < 10
        """).fetchone()["c"]
        
        # 缺货数量
        out_of_stock = db.execute(f"""
            SELECT COUNT(*) as c FROM {table_name}
            WHERE stock IS NOT NULL AND stock <= 0
        """).fetchone()["c"]
        
        # 按分类统计
        cat_rows = _dict_rows(db.execute(f"""
            SELECT category, COUNT(*) as count, SUM(stock) as total_stock
            FROM {table_name}
            WHERE stock IS NOT NULL
            GROUP BY category
        """))
        
        by_category = {
            r.get("category") or "未分类": {
                "产品数": r["count"],
                "总库存": r["total_stock"]
            }
            for r in cat_rows
        }
        
        return {
            "message": "库存概览",
            "data": {
                "总产品数": total_products,
                "总库存价值": round(stock_value, 2),
                "低库存商品": low_stock,
                "缺货商品": out_of_stock,
                "按分类": by_category
            }
        }
    
    finally:
        db.close()


# ═══════════════════════════════════════════
# 批量注册入口
# ═══════════════════════════════════════════

def register_inventory_tools(registry, data_dir: str):
    """将库存工具注册到 ToolRegistry"""
    from modules.intelligence.tool_registry import ToolDefinition
    
    registry.add_tool(ToolDefinition(
        name="query_inventory",
        description="查询产品库存：名称/库存量/状态",
        parameters={
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "产品分类筛选"},
                "low_stock_only": {"type": "boolean", "description": "只查低库存商品"}
            }
        },
        handler=lambda category="", low_stock_only=False: query_inventory(data_dir, category, low_stock_only),
    ))
    
    registry.add_tool(ToolDefinition(
        name="get_inventory_alerts",
        description="获取库存预警：缺货/低库存商品列表",
        parameters={
            "type": "object",
            "properties": {
                "threshold": {"type": "integer", "description": "低库存阈值，默认 10"}
            }
        },
        handler=lambda threshold=10: get_inventory_alerts(data_dir, threshold),
    ))
    
    registry.add_tool(ToolDefinition(
        name="get_inventory_summary",
        description="获取库存概览：总数/价值/预警统计",
        parameters={"type": "object", "properties": {}},
        handler=lambda: get_inventory_summary(data_dir),
    ))

```
