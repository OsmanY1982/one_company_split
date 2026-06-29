# `intelligence/crm_tools.py`

> 路径：`intelligence/crm_tools.py` | 行数：355


---


```python
"""
CRM 增强工具 — 客户关系管理

提供:
- 客户跟进记录
- 客户价值分析
- 客户分层管理
- 联系提醒
"""

from core.database import get_conn, close_conn
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


def _connect(db_dir: str, db_name: str) -> Optional:
    """连接数据库（使用连接池）"""
    path = os.path.join(db_dir, db_name)
    if not os.path.exists(path):
        return None
    return get_conn(db_name)


def _dict_rows(cursor) -> list[dict]:
    return [dict(r) for r in cursor.fetchall()]


# ═══════════════════════════════════════════
# 客户价值分析
# ═══════════════════════════════════════════

def analyze_customer_value(data_dir: str, days: int = 90) -> dict:
    """
    分析客户价值（RFM 简化版）
    
    Args:
        days: 分析时间范围（天）
        
    Returns:
        {
            "top_customers": [...],  # 高价值客户
            "at_risk": [...],        # 流失风险客户
            "new_customers": [...],  # 新客户
            "summary": {...}
        }
    """
    result = {
        "top_customers": [],
        "at_risk": [],
        "new_customers": [],
        "summary": {}
    }
    
    # 检查订单数据库
    order_db_names = ["orders.db", "order.db"]
    order_db = None
    
    for name in order_db_names:
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            order_db = _connect(data_dir, name)
            break
    
    if not order_db:
        return {"message": "无订单数据，无法分析客户价值", "data": result}
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_str = start_date.strftime('%Y-%m-%d')
        
        # 检查 customer_name 字段是否存在
        tables = _dict_rows(order_db.execute("SELECT name FROM sqlite_master WHERE type='table'"))
        if "orders" not in [t["name"] for t in tables]:
            return {"message": "未找到订单表", "data": result}
        
        # 获取客户消费统计
        customer_stats = _dict_rows(order_db.execute(f"""
            SELECT 
                customer_name,
                COUNT(*) as order_count,
                SUM(total_amount) as total_spent,
                MAX(created_at) as last_order,
                MIN(created_at) as first_order
            FROM orders
            WHERE created_at >= ? AND status != 'cancelled'
            GROUP BY customer_name
            ORDER BY total_spent DESC
            LIMIT 50
        """, (start_str,)))
        
        # 高价值客户（总消费前 10）
        top_customers = []
        for r in customer_stats[:10]:
            top_customers.append({
                "客户": r["customer_name"],
                "订单数": r["order_count"],
                "总消费": round(float(r["total_spent"] or 0), 2),
                "最后购买": r["last_order"],
                "等级": "💎 VIP" if float(r["total_spent"] or 0) > 10000 else "⭐ 优质"
            })
        
        result["top_customers"] = top_customers
        
        # 流失风险客户（有历史订单但最近 N 天未购买）
        risk_days = 60
        risk_threshold = (end_date - timedelta(days=risk_days)).strftime('%Y-%m-%d')
        
        all_customers = _dict_rows(order_db.execute("""
            SELECT 
                customer_name,
                MAX(created_at) as last_order,
                SUM(total_amount) as total_spent
            FROM orders
            WHERE status != 'cancelled'
            GROUP BY customer_name
            HAVING last_order < ?
            ORDER BY total_spent DESC
            LIMIT 20
        """, (risk_threshold,)))
        
        at_risk = []
        for r in all_customers:
            if float(r["total_spent"] or 0) > 500:  # 只关注有消费的
                at_risk.append({
                    "客户": r["customer_name"],
                    "最后购买": r["last_order"],
                    "历史消费": round(float(r["total_spent"] or 0), 2),
                    "风险": "⚠️ 可能流失"
                })
        
        result["at_risk"] = at_risk
        
        # 新客户（首次购买在最近 30 天内）
        new_days = 30
        new_threshold = (end_date - timedelta(days=new_days)).strftime('%Y-%m-%d')
        
        new_custs = _dict_rows(order_db.execute(f"""
            SELECT 
                customer_name,
                MIN(created_at) as first_order,
                COUNT(*) as order_count
            FROM orders
            WHERE status != 'cancelled'
            GROUP BY customer_name
            HAVING first_order >= ?
            ORDER BY first_order DESC
            LIMIT 20
        """, (new_threshold,)))
        
        result["new_customers"] = [{
            "客户": r["customer_name"],
            "首次购买": r["first_order"],
            "订单数": r["order_count"]
        } for r in new_custs]
        
        # 汇总
        result["summary"] = {
            "分析周期": f"{days}天",
            "高价值客户数": len(top_customers),
            "流失风险客户数": len(at_risk),
            "新客户数": len(result["new_customers"])
        }
        
        return {"message": "客户价值分析完成", "data": result}
    
    finally:
        close_conn('order.db')


# ═══════════════════════════════════════════
# 客户分层
# ═══════════════════════════════════════════

def get_customer_segments(data_dir: str) -> dict:
    """
    获取客户分层信息
    
    Returns:
        {
            "vip": [...],      # VIP 客户
            "regular": [...],  # 普通客户
            "inactive": [...], # 不活跃客户
            "summary": {...}
        }
    """
    # 尝试客户数据库
    cust_db_names = ["customer.db", "customers.db"]
    cust_db = None
    
    for name in cust_db_names:
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            cust_db = _connect(data_dir, name)
            break
    
    if not cust_db:
        return {"message": "无客户数据", "data": {}}
    
    try:
        tables = _dict_rows(cust_db.execute("SELECT name FROM sqlite_master WHERE type='table'"))
        if "customer" not in [t["name"] for t in tables]:
            return {"message": "未找到客户表", "data": {}}
        
        # 获取所有客户
        all_customers = _dict_rows(cust_db.execute("""
            SELECT name, company, phone, email, level, created_at
            FROM customer
            ORDER BY created_at DESC
            LIMIT 100
        """))
        
        vip = []
        regular = []
        inactive = []
        
        for r in all_customers:
            customer_info = {
                "姓名": r["name"],
                "公司": r.get("company") or "",
                "电话": r.get("phone") or "",
                "等级": r.get("level") or "普通"
            }
            
            level = (r.get("level") or "").lower()
            if level in ["vip", "钻石", "金牌", "premium"]:
                vip.append(customer_info)
            elif level in [" inactive", "休眠", "流失"]:
                inactive.append(customer_info)
            else:
                regular.append(customer_info)
        
        return {
            "message": f"VIP:{len(vip)} 普通:{len(regular)} 不活跃:{len(inactive)}",
            "data": {
                "vip": vip[:20],
                "regular": regular[:20],
                "inactive": inactive[:20],
                "summary": {
                    "VIP 客户数": len(vip),
                    "普通客户数": len(regular),
                    "不活跃客户数": len(inactive),
                    "总客户数": len(all_customers)
                }
            }
        }
    
    finally:
        close_conn('customer.db')


# ═══════════════════════════════════════════
# 联系提醒
# ═══════════════════════════════════════════

def get_contact_reminders(data_dir: str, days: int = 7) -> dict:
    """
    获取需要联系的客户提醒
    
    Args:
        days: 多少天未联系需要提醒
        
    Returns:
        {
            "need_contact": [...],
            "message": "..."
        }
    """
    cust_db_names = ["customer.db", "customers.db"]
    cust_db = None
    
    for name in cust_db_names:
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            cust_db = _connect(data_dir, name)
            break
    
    if not cust_db:
        return {"message": "无客户数据", "need_contact": []}
    
    try:
        tables = _dict_rows(cust_db.execute("SELECT name FROM sqlite_master WHERE type='table'"))
        if "customer" not in [t["name"] for t in tables]:
            return {"message": "未找到客户表", "need_contact": []}
        
        # 获取所有客户（假设没有 last_contact 字段时返回全部）
        all_customers = _dict_rows(cust_db.execute("""
            SELECT name, company, phone, level, note, created_at
            FROM customer
            ORDER BY created_at DESC
            LIMIT 100
        """))
        
        need_contact = []
        for r in all_customers:
            # 简单规则：VIP 客户或重要客户优先
            level = (r.get("level") or "").lower()
            if level in ["vip", "钻石", "金牌", "重要"]:
                need_contact.append({
                    "姓名": r["name"],
                    "公司": r.get("company") or "",
                    "电话": r.get("phone") or "",
                    "等级": r.get("level") or "",
                    "备注": r.get("note") or "",
                    "优先级": "🔴 高"
                })
        
        return {
            "message": f"{len(need_contact)} 位客户需要关注",
            "need_contact": need_contact[:30]
        }
    
    finally:
        close_conn('customer.db')


# ══════════════════════════════════════════
# 批量注册入口
# ═══════════════════════════════════════════

def register_crm_tools(registry, data_dir: str):
    """将 CRM 工具注册到 ToolRegistry"""
    from core.modules.intelligence.tool_registry import ToolDefinition
    
    registry.add_tool(ToolDefinition(
        name="analyze_customer_value",
        description="分析客户价值：高价值/流失风险/新客户",
        parameters={
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "分析时间范围（天），默认 90"}
            }
        },
        handler=lambda days=90: analyze_customer_value(data_dir, days),
    ))
    
    registry.add_tool(ToolDefinition(
        name="get_customer_segments",
        description="获取客户分层：VIP/普通/不活跃客户列表",
        parameters={"type": "object", "properties": {}},
        handler=lambda: get_customer_segments(data_dir),
    ))
    
    registry.add_tool(ToolDefinition(
        name="get_contact_reminders",
        description="获取需要联系的客户提醒",
        parameters={
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "多少天未联系需要提醒，默认 7"}
            }
        },
        handler=lambda days=7: get_contact_reminders(data_dir, days),
    ))

```
