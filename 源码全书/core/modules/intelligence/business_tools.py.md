# `core/modules/intelligence/business_tools.py`

> 路径：`core/modules/intelligence/business_tools.py` | 行数：486


---


```python
"""
Iqra 业务工具 — 一人公司数据库查询

提供 AI 助手查询公司业务数据的能力。

Usage:
    from business_tools import register_business_tools
    register_business_tools(registry, data_dir="path/to/data")
"""

from core.database import get_conn, close_conn
import os
from datetime import datetime


def _connect(db_dir: str, db_name: str):
    path = os.path.join(db_dir, db_name)
    return get_conn(db_name)


def _dict_rows(cursor) -> list[dict]:
    return [dict(r) for r in cursor.fetchall()]


# ═══════════════════════════════════════════
# 产品查询
# ═══════════════════════════════════════════

def query_products(data_dir: str, keyword: str = "") -> dict:
    db_path = os.path.join(data_dir, "product.db")
    if not os.path.exists(db_path):
        return {"message": "无产品数据", "data": []}
    db = _connect(data_dir, "product.db")
    try:
        if keyword:
            rows = _dict_rows(db.execute(
                "SELECT name,price,stock,category,description FROM product WHERE name LIKE ? LIMIT 50",
                (f"%{keyword}%",)
            ))
        else:
            rows = _dict_rows(db.execute(
                "SELECT name,price,stock,category,description FROM product LIMIT 50"
            ))
        prods = [{"名称": r["name"], "单价": r["price"], "库存": r["stock"],
                  "类别": r["category"], "描述": r["description"] or ""} for r in rows]
        return {"message": f"{len(prods)} 件产品", "data": prods}
    finally:
        close_conn('product.db')


# ═══════════════════════════════════════════
# 订单查询
# ═══════════════════════════════════════════

def query_orders(data_dir: str, month: str = "") -> dict:
    db_path = os.path.join(data_dir, "order.db")
    if not os.path.exists(db_path):
        return {"message": "无订单数据", "data": []}
    db = _connect(data_dir, "order.db")
    try:
        if month:
            rows = _dict_rows(db.execute(
                "SELECT order_no,customer_name,total_amount,status,created_at,payment_method "
                "FROM orders WHERE created_at LIKE ? ORDER BY created_at DESC LIMIT 50",
                (f"{month}%",)
            ))
        else:
            rows = _dict_rows(db.execute(
                "SELECT order_no,customer_name,total_amount,status,created_at,payment_method "
                "FROM orders ORDER BY created_at DESC LIMIT 30"
            ))
        orders = [{"订单号": r["order_no"], "客户": r["customer_name"],
                   "金额": r["total_amount"], "状态": r["status"],
                   "时间": r["created_at"], "付款方式": r["payment_method"] or ""}
                  for r in rows]
        total = sum(float(o["金额"]) for o in orders if o["金额"])
        return {"message": f"{len(orders)} 笔订单, 总额 {total:.2f}", "data": orders}
    finally:
        close_conn('order.db')


# ═══════════════════════════════════════════
# 客户查询 ✨ NEW
# ═══════════════════════════════════════════

def query_customers(data_dir: str, name: str = "") -> dict:
    db_path = os.path.join(data_dir, "customer.db")
    if not os.path.exists(db_path):
        return {"message": "无客户数据", "data": []}
    db = _connect(data_dir, "customer.db")
    try:
        if name:
            rows = _dict_rows(db.execute(
                "SELECT name,company,phone,email,level,note,created_at "
                "FROM customer WHERE name LIKE ? OR company LIKE ? ORDER BY created_at DESC LIMIT 50",
                (f"%{name}%", f"%{name}%")
            ))
        else:
            rows = _dict_rows(db.execute(
                "SELECT name,company,phone,email,level,note,created_at "
                "FROM customer ORDER BY created_at DESC LIMIT 50"
            ))
        custs = [{"姓名": r["name"], "公司": r["company"] or "", "电话": r["phone"] or "",
                  "邮箱": r["email"] or "", "等级": r["level"] or "",
                  "备注": r["note"] or "", "创建时间": r["created_at"] or ""}
                 for r in rows]
        return {"message": f"{len(custs)} 位客户", "data": custs}
    finally:
        close_conn('customer.db')


# ═══════════════════════════════════════════
# 会员查询
# ═══════════════════════════════════════════

def query_members(data_dir: str, expiring_soon: bool = False) -> dict:
    db_path = os.path.join(data_dir, "users.db")
    if not os.path.exists(db_path):
        return {"message": "无会员数据", "data": []}
    db = _connect(data_dir, "users.db")
    try:
        sql = ("SELECT u.username,um.membership_type,um.expires_at "
               "FROM users u LEFT JOIN user_memberships um ON u.username=um.username "
               "WHERE um.membership_type IS NOT NULL")
        if expiring_soon:
            sql += " AND date(um.expires_at) <= date('now','+7 days')"
        sql += " ORDER BY um.expires_at ASC LIMIT 50"
        try:
            rows = _dict_rows(db.execute(sql))
        except Exception:
            rows = _dict_rows(db.execute(
                "SELECT username,role,created_at FROM users LIMIT 50"
            ))
        mems = [{"用户名": r.get("username", ""), "会员类型": r.get("membership_type", r.get("role", "")),
                 "到期时间": r.get("expires_at", r.get("created_at", ""))}
                for r in rows]
        return {"message": f"{len(mems)} 位会员", "data": mems}
    finally:
        close_conn('users.db')


# ═══════════════════════════════════════════
# 用户查询 ✨ NEW
# ═══════════════════════════════════════════

def query_users(data_dir: str) -> dict:
    db_path = os.path.join(data_dir, "users.db")
    if not os.path.exists(db_path):
        return {"message": "无用户数据", "data": []}
    db = _connect(data_dir, "users.db")
    try:
        rows = _dict_rows(db.execute(
            "SELECT username,user_id,role,license_type,created_at FROM users LIMIT 50"
        ))
        users = [{"用户名": r["username"], "ID": r["user_id"], "角色": r["role"],
                  "授权类型": r["license_type"] or "", "创建": r["created_at"] or ""}
                 for r in rows]
        return {"message": f"{len(users)} 位用户", "data": users}
    finally:
        close_conn('users.db')


# ═══════════════════════════════════════════
# 财务查询
# ═══════════════════════════════════════════

def query_finance(data_dir: str, month: str = "") -> dict:
    db_path = os.path.join(data_dir, "finance.db")
    if not os.path.exists(db_path):
        return {"message": "无财务数据", "data": []}
    db = _connect(data_dir, "finance.db")
    try:
        if month:
            rows = _dict_rows(db.execute(
                "SELECT type,category,amount,date,description FROM finance WHERE date LIKE ?",
                (f"{month}%",)
            ))
        else:
            rows = _dict_rows(db.execute(
                "SELECT type,category,amount,date,description FROM finance LIMIT 30"
            ))
        recs = [{"类型": r["type"], "分类": r["category"] or "", "金额": r["amount"],
                 "日期": r["date"], "说明": r["description"] or ""}
                for r in rows]
        income = sum(float(r["金额"]) for r in recs if r["类型"] in ("收入", "income"))
        expense = sum(float(r["金额"]) for r in recs if r["类型"] in ("支出", "expense"))
        return {"message": f"收入:{income:.2f} 支出:{expense:.2f} 利润:{income-expense:.2f}",
                "data": recs}
    finally:
        close_conn('finance.db')


# ═══════════════════════════════════════════
# 员工查询
# ═══════════════════════════════════════════

def query_staff(data_dir: str) -> dict:
    db_path = os.path.join(data_dir, "staff.db")
    if not os.path.exists(db_path):
        return {"message": "无员工数据", "data": []}
    db = _connect(data_dir, "staff.db")
    try:
        rows = _dict_rows(db.execute(
            "SELECT name,position,department,hire_date,phone,salary,status FROM staff LIMIT 50"
        ))
        staff = [{"姓名": r["name"], "职位": r["position"] or "", "部门": r["department"] or "",
                  "入职": r["hire_date"] or "", "电话": r["phone"] or "",
                  "薪资": r["salary"], "状态": r["status"] or ""}
                 for r in rows]
        return {"message": f"{len(staff)} 位员工", "data": staff}
    finally:
        close_conn('staff.db')


# ═══════════════════════════════════════════
# 统计概览 ✨ NEW
# ═══════════════════════════════════════════

def get_summary_stats(data_dir: str) -> dict:
    """获取公司数据概览统计"""
    stats = {}

    # 订单
    if os.path.exists(os.path.join(data_dir, "order.db")):
        db = _connect(data_dir, "order.db")
        try:
            stats["总订单数"] = db.execute("SELECT COUNT(*) as c FROM orders").fetchone()["c"]
            stats["总营收"] = round(
                db.execute("SELECT COALESCE(SUM(total_amount),0) as s FROM orders").fetchone()["s"], 2
            )
        finally:
            close_conn('order.db')

    # 客户
    if os.path.exists(os.path.join(data_dir, "customer.db")):
        db = _connect(data_dir, "customer.db")
        try:
            stats["客户数"] = db.execute("SELECT COUNT(*) as c FROM customer").fetchone()["c"]
        finally:
            close_conn('customer.db')

    # 产品
    if os.path.exists(os.path.join(data_dir, "product.db")):
        db = _connect(data_dir, "product.db")
        try:
            stats["产品数"] = db.execute("SELECT COUNT(*) as c FROM product").fetchone()["c"]
        finally:
            close_conn('product.db')

    # 员工
    if os.path.exists(os.path.join(data_dir, "staff.db")):
        db = _connect(data_dir, "staff.db")
        try:
            stats["员工数"] = db.execute("SELECT COUNT(*) as c FROM staff").fetchone()["c"]
        finally:
            close_conn('staff.db')

    # 会员
    if os.path.exists(os.path.join(data_dir, "member.db")):
        db = _connect(data_dir, "member.db")
        try:
            stats["会员数"] = db.execute("SELECT COUNT(*) as c FROM member").fetchone()["c"]
        finally:
            close_conn('member.db')

    # 用户
    if os.path.exists(os.path.join(data_dir, "users.db")):
        db = _connect(data_dir, "users.db")
        try:
            stats["用户数"] = db.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
            stats["激活会员数"] = db.execute(
                "SELECT COUNT(*) as c FROM user_memberships WHERE membership_type IS NOT NULL"
            ).fetchone()["c"]
        finally:
            close_conn('users.db')

    return {"message": "公司数据概览", "data": stats}


# ═══════════════════════════════════════════
# 批量注册入口
# ═══════════════════════════════════════════

def register_business_tools(registry, data_dir: str):
    """将全部业务工具注册到 ToolRegistry"""
    from core.modules.intelligence.tool_registry import ToolDefinition
    
    # 使用闭包绑定 data_dir
    registry.add_tool(ToolDefinition(
        name="query_products",
        description="查询产品：名称/价格/库存",
        parameters={"type": "object", "properties": {"keyword": {"type": "string", "description": "搜索关键词"}}},
        handler=lambda keyword="": query_products(data_dir, keyword),
    ))

    registry.add_tool(ToolDefinition(
        name="query_orders",
        description="查询订单：订单号/金额/状态",
        parameters={"type": "object", "properties": {"month": {"type": "string", "description": "月份，如 2026-05"}}},
        handler=lambda month="": query_orders(data_dir, month),
    ))

    registry.add_tool(ToolDefinition(
        name="query_customers",
        description="查询客户信息：姓名/公司/电话/等级",
        parameters={"type": "object", "properties": {"name": {"type": "string", "description": "客户姓名或公司名"}}},
        handler=lambda name="": query_customers(data_dir, name),
    ))

    registry.add_tool(ToolDefinition(
        name="query_members",
        description="查询会员：会员类型/到期时间",
        parameters={"type": "object", "properties": {"expiring_soon": {"type": "boolean", "description": "只查即将到期会员"}}},
        handler=lambda expiring_soon=False: query_members(data_dir, expiring_soon),
    ))

    registry.add_tool(ToolDefinition(
        name="query_users",
        description="查询系统用户列表",
        parameters={"type": "object", "properties": {}},
        handler=lambda: query_users(data_dir),
    ))

    registry.add_tool(ToolDefinition(
        name="query_finance",
        description="查询财务：收入/支出/利润",
        parameters={"type": "object", "properties": {"month": {"type": "string", "description": "月份，如 2026-05"}}},
        handler=lambda month="": query_finance(data_dir, month),
    ))

    registry.add_tool(ToolDefinition(
        name="query_staff",
        description="查询员工信息",
        parameters={"type": "object", "properties": {}},
        handler=lambda: query_staff(data_dir),
    ))

    registry.add_tool(ToolDefinition(
        name="get_summary_stats",
        description="获取公司数据概览：总订单/营收/客户/产品/员工/会员统计",
        parameters={"type": "object", "properties": {}},
        handler=lambda: get_summary_stats(data_dir),
    ))


# ═══════════════════════════════════════════
# 便捷函数：注册所有工具（包括高级分析和自动化）
# ═══════════════════════════════════════════

def register_all_tools(registry, data_dir: str):
    """
    注册所有可用的工具：基础业务 + 高级分析 + 自动化 + 营销推广
    
    Usage:
        from core.modules.intelligence.tools.main_tools import register_all_tools
        register_all_tools(registry, "/path/to/data")
    """
    register_business_tools(registry, data_dir)
    
    # 注册高级分析工具
    try:
        from analysis_tools import register_analysis_tools
        register_analysis_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 analysis_tools: {e}")
    
    # 注册自动化工具
    try:
        from core.modules.intelligence.tools.automation_tools import register_automation_tools
        register_automation_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 automation_tools: {e}")
    
    # 注册营销推广工具
    try:
        from marketing_tools import register_marketing_tools
        register_marketing_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 marketing_tools: {e}")
    
    # 注册HR管理工具
    try:
        from hr_tools import register_hr_tools
        register_hr_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 hr_tools: {e}")
    
    # 注册采购供应链工具
    try:
        from core.modules.intelligence.tools.procurement_tools import register_procurement_tools
        register_procurement_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 procurement_tools: {e}")
    
    # 注册文档处理工具
    try:
        from core.modules.intelligence.tools.doc_tools import register_doc_tools
        register_doc_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 doc_tools: {e}")
    
    # 注册日程管理工具
    try:
        from core.modules.intelligence.tools.scheduling_tools import register_scheduling_tools
        register_scheduling_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 scheduling_tools: {e}")
    
    # 注册AI自检工具
    try:
        from self_monitor import register_monitor_tools
        register_monitor_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 self_monitor: {e}")
    
    # 注册模板库工具
    try:
        from core.modules.intelligence.tools.template_tools import register_template_tools
        register_template_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 template_tools: {e}")
    
    # 注册财务分析工具
    try:
        from core.modules.intelligence.tools.finance_analysis import register_finance_tools
        register_finance_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 finance_analysis: {e}")
    
    # 注册项目管理工具
    try:
        from core.modules.intelligence.tools.project_management import register_project_management_tools
        register_project_management_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 project_management: {e}")
    
    # 注册网络搜索工具
    try:
        from core.modules.intelligence.tools.web_search_tools import register_web_search_tools
        register_web_search_tools(registry)
    except ImportError as e:
        print(f"⚠️ 无法加载 web_search_tools: {e}")
    
    # 注册智能报告工具
    try:
        from smart_report_tools import register_smart_report_tools
        register_smart_report_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 smart_report_tools: {e}")
    
    # 注册数据导入工具
    try:
        from data_import_tools import register_data_import_tools
        register_data_import_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 data_import_tools: {e}")
    
    # 注册智能提醒工具
    try:
        from core.modules.intelligence.tools.alert_tools import register_alert_tools
        register_alert_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 alert_tools: {e}")
    
    # 注册库存管理工具
    try:
        from inventory_tools import register_inventory_tools
        register_inventory_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 inventory_tools: {e}")
    
    # 注册 CRM 增强工具
    try:
        from crm_tools import register_crm_tools
        register_crm_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 crm_tools: {e}")
    
    # 注册报表导出工具
    try:
        from core.modules.intelligence.tools.export_tools import register_export_tools
        register_export_tools(registry, data_dir)
    except ImportError as e:
        print(f"⚠️ 无法加载 export_tools: {e}")
    
    print(f"✅ 工具注册完成，共 {registry.count()} 个可用工具")
```
