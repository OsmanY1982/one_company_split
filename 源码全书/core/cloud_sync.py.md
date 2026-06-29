# `core/cloud_sync.py`

> 路径：`core/cloud_sync.py` | 行数：710


---


```python
# -*- coding: utf-8 -*-
"""
云端同步服务（扩展版 - 覆盖全部 10 张业务表）
策略：本地 SQLite → Supabase（UPSERT by 冲突列）
与 Flutter 端 cloud_sync_service.dart 保持字段映射一致
"""
import sqlite3
import logging
import os as _os
from core.supabase_client import _request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── 项目根目录 ──
BASE_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

# ── 本地 DB 文件路径（key = Supabase 表名） ──
DB_PATHS = {
    "products":           _os.path.join(BASE_DIR, "data", "product.db"),
    "orders":             _os.path.join(BASE_DIR, "data", "order.db"),
    "staff":              _os.path.join(BASE_DIR, "data", "staff.db"),
    "finance":            _os.path.join(BASE_DIR, "data", "finance.db"),
    "customers":          _os.path.join(BASE_DIR, "data", "customer.db"),
    "users":              _os.path.join(BASE_DIR, "data", "users.db"),
    "user_memberships":   _os.path.join(BASE_DIR, "data", "users.db"),
    "distribution_links": _os.path.join(BASE_DIR, "data", "distribution.db"),
    "commissions":        _os.path.join(BASE_DIR, "data", "distribution.db"),
    "team_members":       _os.path.join(BASE_DIR, "data", "distribution.db"),
    "wallet":             _os.path.join(BASE_DIR, "data", "wallet.db"),
    "wallet_transactions": _os.path.join(BASE_DIR, "data", "wallet.db"),
    "activation_codes":   _os.path.join(BASE_DIR, "data", "activation_admin.db"),
    "admin_config":       _os.path.join(BASE_DIR, "data", "admin.db"),
    "permissions":        _os.path.join(BASE_DIR, "data", "permissions.db"),
    "activation_records": _os.path.join(BASE_DIR, "data", "activation.db"),
    "activation_logs":    _os.path.join(BASE_DIR, "data", "activation_log.db"),
    "admins":             _os.path.join(BASE_DIR, "data", "admin.db"),
    "audit_logs":         _os.path.join(BASE_DIR, "data", "audit.db"),
    "members":            _os.path.join(BASE_DIR, "data", "member.db"),
    "operation_logs":     _os.path.join(BASE_DIR, "data", "operation_log.db"),
    "orders_backup":      _os.path.join(BASE_DIR, "data", "orders.db"),
    "personnel":          _os.path.join(BASE_DIR, "data", "personnel_db.sqlite"),
    "schedules":          _os.path.join(BASE_DIR, "data", "scheduler.db"),
    "sessions":           _os.path.join(BASE_DIR, "data", "sessions.db"),
    "sync_logs":          _os.path.join(BASE_DIR, "data", "sync_log.db"),
    "system_logs":        _os.path.join(BASE_DIR, "data", "system_logs.db"),
    "todos":              _os.path.join(BASE_DIR, "data", "todos.db"),
    "app_config":         _os.path.join(BASE_DIR, "data", "app.db"),
    "cache_data":         _os.path.join(BASE_DIR, "data", "cache.db"),
}

# ── 本地表名映射（当本地 SQLite 表名 ≠ Supabase 表名时） ──
LOCAL_TABLE_NAMES = {
    "customers": "customer",       # customer.db 里的表叫 customer（单数）
    "activation_codes": "admin_codes",  # activation_admin.db 里的表叫 admin_codes
    "activation_records": "activation_codes",  # activation.db 里的表叫 activation_codes
    "admins": "admin_logs",        # admin.db 里的表叫 admin_logs
    "schedules": "tasks",          # scheduler.db 里的表叫 tasks
    "sync_logs": "sync_records",   # sync_log.db 里的表叫 sync_records
    "system_logs": "sync_logs",    # system_logs.db 里的表叫 sync_logs
    "admin_config": "admin_logs",        # admin.db 里的表叫 admin_logs（与 admins 同表）
    "permissions": "permissions",        # permissions.db 里的表叫 permissions
}

# ── 字段映射：{本地列名 → Supabase 列名} ──
# 与 Flutter 端 _columnMappings 保持一致
COLUMN_MAPPING = {
    "products": {
        # 本地 product.db/products: name, category, price, description, stock, status, created_at
        # 云端 products: name, category, unit_price, stock, status, note, created_at
        "name":        "name",
        "category":    "category",
        "price":       "unit_price",   # 本地 price → 云端 unit_price
        "stock":       "stock",
        "status":      "status",
        "description": "note",         # 本地 description → 云端 note
        "created_at":  "created_at",
    },
    "orders": {
        # 本地 order.db/orders: customer_name, product_name, unit_price, total_amount, quantity, status, note, created_at
        # 云端 orders: customer, product, unit_price, total_price, quantity, status, note, created_at
        "order_no":      "order_no",
        "customer_name": "customer",     # 本地 customer_name → 云端 customer
        "product_name":  "product",      # 本地 product_name → 云端 product
        "quantity":      "quantity",
        "unit_price":    "unit_price",
        "total_amount":  "total_price",  # 本地 total_amount → 云端 total_price
        "status":        "status",
        "note":          "note",
        "created_at":    "created_at",
    },
    "customers": {
        # 本地 customer.db/customer: name, company, phone, email, address, level, note
        # 云端 customers: name, company, phone, email, address, note
        "name":    "name",
        "company": "company",
        "phone":   "phone",
        "email":   "email",
        "address": "address",
        "note":    "note",
        "created_at": "created_at",
        # 注：本地 level 列云端 customers 表没有，不同步
    },
    "staff": {
        "name":      "name",
        "phone":     "phone",
        "email":     "email",
        "position":  "position",
        "department":"department",
        "salary":    "salary",
        "status":    "status",
        "created_at":"created_at",
    },
    "finance": {
        "type":       "type",
        "category":   "category",
        "amount":     "amount",
        "date":       "date",
        "description":"description",
        "order_no":   "order_no",
        "created_at": "created_at",
    },
    "wallet": {
        "user_id":        "user_id",
        "balance":        "balance",
        "frozen_amount":  "frozen_amount",
        "total_income":   "total_income",
        "total_withdraw": "total_withdraw",
        "status":         "status",
        "created_at":     "created_at",
        "updated_at":     "updated_at",
    },
    "wallet_transactions": {
        "wallet_id":     "wallet_id",
        "type":          "type",
        "amount":        "amount",
        "balance_after":  "balance_after",
        "description":   "description",
        "related_id":    "related_id",
        "created_at":    "created_at",
    },
    "distribution_links": {
        # 云端无 user_name 列，本地 user_name 不同步
        "user_id":          "user_id",
        "code":             "code",
        "url":              "url",
        "click_count":      "click_count",
        "register_count":   "register_count",
        "total_commission": "total_commission",
        "status":           "status",
        "created_at":       "created_at",
    },
    "commissions": {
        # 云端无 user_name 列，本地 user_name 不同步
        "user_id":    "user_id",
        "from_user_id":"from_user_id",
        "amount":     "amount",
        "type":       "type",
        "status":     "status",
        "description":"description",
        "created_at": "created_at",
    },
    "team_members": {
        # 云端无 user_name/parent_name 列，本地这两个字段不同步
        "user_id":           "user_id",
        "parent_id":         "parent_id",
        "username":          "username",
        "level":             "level",
        "total_contribution":"total_contribution",
        "created_at":        "created_at",
    },
    "users": {
        "username":      "username",
        "password":      "password",
        "user_id":      "user_id",
        "role":         "role",
        "license_type": "license_type",
        "created_at":  "created_at",
        "updated_at":  "updated_at",
    },
    "user_memberships": {
        "username":       "username",
        "membership_type":"membership_type",
        "activated_at":   "activated_at",
        "expires_at":     "expires_at",
        "activation_code":"activation_code",
    },
    "activation_codes": {
        "code":          "code",
        "user_type":     "user_type",
        "status":        "status",
        "bound_account": "bound_account",
        "bound_machine": "bound_machine",
        "note":          "note",
        "created_at":    "created_at",
        "used_at":       "used_at",
        "expires_at":    "expires_at",
    },

    # ── 激活记录（activation.db/activation_codes → Supabase activation_records）──
    "activation_records": {
        "code":          "code",
        "type":          "type",
        "status":        "status",
        "bound_account": "bound_account",
        "bound_machine": "bound_machine",
        "created_at":    "created_at",
        "used_at":       "used_at",
        "expires_at":    "expires_at",
    },

    # ── 激活日志（activation_log.db → Supabase activation_logs） ──
    "activation_logs": {
        "code":       "code",
        "action":     "action",
        "detail":     "detail",
        "status":     "status",
        "created_at": "created_at",
    },

    # ── 管理员（admin.db/admin_logs → Supabase admins） ──
    "admins": {
        "admin_user":  "admin_user",
        "action":      "action",
        "target":      "target",
        "details":     "details",
        "ip_address":  "ip_address",
        "created_at":  "created_at",
    },

    # ── admin_config（完整版保留，映射到 admin.db/admin_logs，管理员操作日志视图）──
    "admin_config": {
        "admin_user": "admin_user",
        "action":     "action",
        "target":     "target",
        "details":    "details",
        "ip_address": "ip_address",
        "created_at": "created_at",
    },

    # ── 审计日志（audit.db/audit_logs → Supabase audit_logs） ──
    "audit_logs": {
        "user_id":       "user_id",
        "user_name":     "user_name",
        "action":        "action",
        "level":         "level",
        "resource_type": "resource_type",
        "resource_id":   "resource_id",
        "status":        "status",
        "ip_address":    "ip_address",
        "timestamp":     "timestamp",
    },

    # ── 会员（member.db/member → Supabase members） ──
    "members": {
        "name":       "name",
        "phone":      "phone",
        "email":      "email",
        "level":      "level",
        "points":     "points",
        "rights":     "rights",
        "vip_expire": "vip_expire",
        "status":     "status",
        "created_at": "created_at",
    },

    # ── 操作日志（operation_log.db/operation_logs → Supabase operation_logs） ──
    "operation_logs": {
        "username":    "username",
        "action":      "action",
        "module":      "module",
        "detail":      "detail",
        "created_at":  "created_at",
    },

    # ── 订单备份（orders.db/orders → Supabase orders_backup） ──
    "orders_backup": {
        "order_no":      "order_no",
        "customer_name": "customer",
        "product_name":  "product",
        "quantity":      "quantity",
        "unit_price":    "unit_price",
        "total_amount":  "total_price",
        "status":        "status",
        "note":          "note",
        "created_at":    "created_at",
    },

    # ── 人事档案（personnel_db.sqlite/personnel → Supabase personnel） ──
    "personnel": {
        "name":       "name",
        "phone":      "phone",
        "email":      "email",
        "position":   "position",
        "department": "department",
        "status":     "status",
        "created_at": "created_at",
    },

    # ── 定时任务（scheduler.db/tasks → Supabase schedules） ──
    "schedules": {
        "task_id":     "task_id",
        "name":        "name",
        "schedule":    "schedule",
        "handler":     "handler",
        "params":      "params",
        "enabled":     "enabled",
        "last_run":    "last_run",
        "next_run":    "next_run",
        "run_count":   "run_count",
        "last_result": "last_result",
    },

    # ── 会话（sessions.db/sessions → Supabase sessions） ──
    "sessions": {
        "id":               "id",
        "title":            "title",
        "summary":          "summary",
        "message_count":    "message_count",
        "tags":             "tags",
        "content_snapshot": "content_snapshot",
        "created_at":       "created_at",
        "updated_at":       "updated_at",
    },

    # ── 同步日志（sync_log.db/sync_records → Supabase sync_logs） ──
    "sync_logs": {
        "sync_type":    "sync_type",
        "status":       "status",
        "detail":       "detail",
        "files_synced": "files_synced",
        "created_at":   "created_at",
    },

    # ── 系统日志（system_logs.db/sync_logs → Supabase system_logs） ──
    "system_logs": {
        "table_name":   "table_name",
        "direction":    "direction",
        "record_count": "record_count",
        "status":       "status",
        "created_at":   "created_at",
    },

    # ── permissions（完整版保留，权限表）──
    "permissions": {
        "code":            "code",
        "name":            "name",
        "description":     "description",
        "resource_type":   "resource_type",
        "permission_type": "permission_type",
        "created_at":      "created_at",
    },

    # ── 待办事项（todos.db/todos → Supabase todos） ──
    "todos": {
        "id":         "id",
        "content":    "content",
        "status":     "status",
        "priority":   "priority",
        "created_at": "created_at",
        "updated_at": "updated_at",
    },

    # ── 应用配置（app.db/app_config → Supabase app_config） ──
    "app_config": {
        "key":         "key",
        "value":       "value",
        "description": "description",
        "updated_at":  "updated_at",
    },

    # ── 缓存数据（cache.db/cache_data → Supabase cache_data） ──
    "cache_data": {
        "key":        "key",
        "value":      "value",
        "expire_at":  "expire_at",
        "created_at": "created_at",
    },
}

# ── 冲突列（upsert on_conflict 用） ──
CONFLICT_COLUMNS = {
    "products":            "name",
    "orders":              "order_no",
    "customers":           "name",
    "staff":               "name",
    "finance":             None,
    "wallet":              None,
    "wallet_transactions": None,
    "distribution_links":  "code",
    "commissions":         None,
    "team_members":        None,
    "users":              "username",
    "user_memberships":   "username",
    "activation_codes":   "code",
    "activation_records": "code",
    "activation_logs":    None,
    "admins":             "username",
    "audit_logs":         None,
    "members":            "name",
    "operation_logs":     None,
    "orders_backup":      "order_no",
    "personnel":          "name",
    "schedules":          "name",
    "sessions":           "user_id",
    "sync_logs":          None,
    "system_logs":        None,
    "todos":              "title",
    "app_config":         "key",
    "cache_data":         "key",
    "admin_config":       None,
    "permissions":        "code",
}


def sync_table(sqlite_path, supabase_table):
    """同步单个表：本地SQLite → Supabase（UPSERT by 冲突列）"""
    try:
        mapping = COLUMN_MAPPING.get(supabase_table)
        if not mapping:
            raise ValueError(f"未配置字段映射: {supabase_table}")

        local_table = LOCAL_TABLE_NAMES.get(supabase_table, supabase_table)

        if not _os.path.exists(sqlite_path):
            logger.warning(f"本地数据库不存在：{sqlite_path}，跳过 {supabase_table}")
            return

        conn = sqlite3.connect(sqlite_path)
        conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM [{local_table}]")
        rows = cursor.fetchall()
        conflict_col = CONFLICT_COLUMNS.get(supabase_table)

        if not rows:
            logger.info(f"本地表 {local_table}（→{supabase_table}）无数据，跳过")
            conn.close()
            return

        # 重命名字段匹配云端
        data = []
        for row in rows:
            item = {}
            for local_col, cloud_col in mapping.items():
                if local_col in row.keys():
                    item[cloud_col] = row[local_col]
            data.append(item)

        logger.info(f"准备同步 {len(data)} 条数据到 {supabase_table}，字段: {list(mapping.values())}")

        # 先查询云端现有记录，构建 key → id 索引
        cloud_ids = {}
        if conflict_col:
            ok, existing = _request("GET",
                f"/rest/v1/{supabase_table}?select=id,{conflict_col}",
                service_key=True)
            if ok and isinstance(existing, list):
                for rec in existing:
                    val = rec.get(conflict_col)
                    if val:
                        cloud_ids[str(val)] = rec.get("id")

        # 逐条 upsert
        for item in data:
            if conflict_col:
                key_val = str(item.get(conflict_col, ""))
                cloud_id = cloud_ids.get(key_val)
                if cloud_id:
                    ok, result = _request("PATCH",
                        f"/rest/v1/{supabase_table}?id=eq.{cloud_id}",
                        data=item, service_key=True)
                else:
                    ok, result = _request("POST",
                        f"/rest/v1/{supabase_table}",
                        data=item, service_key=True)
            else:
                ok, result = _request("POST",
                    f"/rest/v1/{supabase_table}",
                    data=item, service_key=True)

            if not ok:
                logger.warning(f"同步 {supabase_table} 单条异常：{result}")

        conn.close()

        # 构建本地 key 集合（用于对比云端多余记录）
        local_key_set = set()
        if conflict_col:
            for item in data:
                key_val = str(item.get(conflict_col, ""))
                if key_val:
                    local_key_set.add(key_val)

            # 删除云端多余记录（本地没有 = 管理员已删除 → 云端也要删）
            ok, existing = _request("GET",
                f"/rest/v1/{supabase_table}?select=id,{conflict_col}",
                service_key=True)
            if ok and isinstance(existing, list):
                deleted = 0
                for rec in existing:
                    cloud_key = str(rec.get(conflict_col, ""))
                    if cloud_key and cloud_key not in local_key_set:
                        _request("DELETE", f"/rest/v1/{supabase_table}?id=eq.{rec['id']}", service_key=True)
                        deleted += 1
                if deleted:
                    logger.info(f"已删除云端多余记录 {deleted} 条（{supabase_table}）")

        logger.info(f"同步完成：{supabase_table}（{len(data)} 条）")

    except Exception as e:
        logger.error(f"同步 {supabase_table} 失败：{str(e)}")
        import traceback
        traceback.print_exc()
        raise


def sync_products():
    sync_table(DB_PATHS["products"], "products")

def sync_orders():
    sync_table(DB_PATHS["orders"], "orders")

def sync_customers():
    sync_table(DB_PATHS["customers"], "customers")

def sync_staff():
    sync_table(DB_PATHS["staff"], "staff")

def sync_finance():
    sync_table(DB_PATHS["finance"], "finance")

def sync_wallet():
    sync_table(DB_PATHS["wallet"], "wallet")

def sync_wallet_transactions():
    sync_table(DB_PATHS["wallet_transactions"], "wallet_transactions")

def sync_distribution_links():
    sync_table(DB_PATHS["distribution_links"], "distribution_links")

def sync_commissions():
    sync_table(DB_PATHS["commissions"], "commissions")

def sync_team_members():
    sync_table(DB_PATHS["team_members"], "team_members")


def sync_users():
    """同步用户表（不含 password）"""
    sync_table(DB_PATHS["users"], "users")


def sync_user_memberships():
    """同步会员信息表"""
    sync_table(DB_PATHS["user_memberships"], "user_memberships")


def sync_activation_codes():
    """同步激活码表 → Supabase"""
    sync_table(DB_PATHS["activation_codes"], "activation_codes")


def sync_activation_records():
    """同步激活记录表 → Supabase"""
    sync_table(DB_PATHS["activation_records"], "activation_records")


def sync_activation_logs():
    """同步激活日志表 → Supabase"""
    sync_table(DB_PATHS["activation_logs"], "activation_logs")


def sync_admins():
    """同步管理员表 → Supabase"""
    sync_table(DB_PATHS["admins"], "admins")


def sync_audit_logs():
    """同步审计日志表 → Supabase"""
    sync_table(DB_PATHS["audit_logs"], "audit_logs")


def sync_members():
    """同步会员表 → Supabase"""
    sync_table(DB_PATHS["members"], "members")


def sync_operation_logs():
    """同步操作日志表 → Supabase"""
    sync_table(DB_PATHS["operation_logs"], "operation_logs")


def sync_orders_backup():
    """同步订单备份表 → Supabase"""
    sync_table(DB_PATHS["orders_backup"], "orders_backup")


def sync_personnel():
    """同步人事档案表 → Supabase"""
    sync_table(DB_PATHS["personnel"], "personnel")


def sync_schedules():
    """同步定时任务表 → Supabase"""
    sync_table(DB_PATHS["schedules"], "schedules")


def sync_sessions():
    """同步会话表 → Supabase"""
    sync_table(DB_PATHS["sessions"], "sessions")


def sync_sync_logs():
    """同步同步日志表 → Supabase"""
    sync_table(DB_PATHS["sync_logs"], "sync_logs")


def sync_permissions():
    """同步权限表"""
    return sync_table(DB_PATHS["permissions"], "permissions")


def sync_system_logs():
    """同步系统日志表 → Supabase"""
    sync_table(DB_PATHS["system_logs"], "system_logs")


def sync_todos():
    """同步待办事项表 → Supabase"""
    sync_table(DB_PATHS["todos"], "todos")


def sync_admin_config():
    """同步 admin_config（别名，映射到 admin_logs 表）"""
    return sync_table(DB_PATHS["admin_config"], "admin_config")


def sync_app_config():
    """同步应用配置表 → Supabase"""
    sync_table(DB_PATHS["app_config"], "app_config")


def sync_cache_data():
    """同步缓存数据表 → Supabase"""
    sync_table(DB_PATHS["cache_data"], "cache_data")


def sync_all():
    """同步所有业务表到 Supabase（共 28 表）"""
    logger.info("=" * 50)
    logger.info("开始同步所有业务表...")
    logger.info("=" * 50)

    tables = [
        ("产品", sync_products),
        ("订单", sync_orders),
        ("客户", sync_customers),
        ("员工", sync_staff),
        ("财务", sync_finance),
        ("用户", sync_users),
        ("会员", sync_user_memberships),
        ("激活码", sync_activation_codes),
        ("激活记录", sync_activation_records),
        ("激活日志", sync_activation_logs),
        ("管理员", sync_admins),
        ("管理配置", sync_admin_config),
        ("审计日志", sync_audit_logs),
        ("会员资料", sync_members),
        ("操作日志", sync_operation_logs),
        ("订单备份", sync_orders_backup),
        ("人事档案", sync_personnel),
        ("定时任务", sync_schedules),
        ("会话", sync_sessions),
        ("同步日志", sync_sync_logs),
        ("系统日志", sync_system_logs),
        ("权限", sync_permissions),
        ("待办事项", sync_todos),
        ("应用配置", sync_app_config),
        ("缓存数据", sync_cache_data),
        ("钱包", sync_wallet),
        ("钱包交易", sync_wallet_transactions),
        ("分销链接", sync_distribution_links),
        ("佣金", sync_commissions),
        ("团队成员", sync_team_members),
    ]

    results = {}
    for name, fn in tables:
        try:
            fn()
            results[name] = "✅"
        except Exception as e:
            results[name] = f"❌ {e}"

    logger.info("=" * 50)
    for name, status in results.items():
        logger.info(f"  {name}: {status}")
    logger.info("=" * 50)

    return results


if __name__ == "__main__":
    sync_all()

# agent_bridge forwarding
from iqra.core.cloud_sync import CloudSyncService

```
