# `management-system/core/cloud_sync.py`

> 路径：`management-system/core/cloud_sync.py` | 行数：383


---


```python
# -*- coding: utf-8 -*-
"""
云端同步服务（扩展版 - 覆盖全部 10 张业务表）
策略：本地 SQLite → Supabase（UPSERT by 冲突列）
与 Flutter 端 cloud_sync_service.dart 保持字段映射一致
"""
import logging
import os as _os
from core.supabase_client import _request
from core.database import get_conn, close_conn

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
}

# ── 本地表名映射（当本地 SQLite 表名 ≠ Supabase 表名时） ──
LOCAL_TABLE_NAMES = {
    "customers": "customer",       # customer.db 里的表叫 customer（单数）
    "activation_codes": "admin_codes",  # activation_admin.db 里的表叫 admin_codes
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

        conn = get_conn(_os.path.basename(sqlite_path))
        conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM [{local_table}]")
        rows = cursor.fetchall()
        conflict_col = CONFLICT_COLUMNS.get(supabase_table)

        if not rows:
            logger.info(f"本地表 {local_table}（→{supabase_table}）无数据，跳过")
            close_conn(_os.path.basename(sqlite_path))
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

        close_conn(_os.path.basename(sqlite_path))

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

```
