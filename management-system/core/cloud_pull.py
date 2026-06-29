# -*- coding: utf-8 -*-
"""
云端 → 本地 数据拉取模块（完整版）
将 Supabase 所有表数据同步到本地 SQLite，实现管理员后台 = 云端镜像
与 cloud_sync.py 字段映射完全对应（反向：CLOUD_TO_LOCAL）
"""
import logging
import json
import os as _os
import sys
import socket
import threading
import time
from urllib.parse import urlparse
from core.database import get_conn, close_conn

BASE_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
DATA_DIR = _os.path.join(BASE_DIR, "data")
sys.path.insert(0, BASE_DIR)

from core.supabase_client import _request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# DNS 预检
# ============================================================
def _dns_check():
    """快速 DNS 预检：用独立线程 + 3秒 join 超时判断 Supabase 主机名是否可达。
    返回 True=可达, False=不可达。
    """
    from config.supabase_config import SUPABASE_URL
    try:
        hostname = urlparse(SUPABASE_URL).hostname
        if not hostname:
            return False

        result = {"ok": False}

        def _resolve():
            try:
                socket.getaddrinfo(hostname, None)
                result["ok"] = True
            except Exception:
                pass

        t = threading.Thread(target=_resolve, daemon=True)
        t.start()
        t.join(timeout=3)
        return result["ok"]
    except Exception:
        return False

# ============================================================
# 云端 → 本地 字段映射（反向 = cloud_sync.py COLUMN_MAPPING）
# key = 云端列表名，value = {云端列名 → 本地列名}
# ============================================================
CLOUD_TO_LOCAL = {
    # ── 用户 & 会员 ──
    "users": {
        "username":      "username",
        "password":      "password",
        "user_id":       "user_id",
        "role":          "role",
        "license_type":  "license_type",
        "created_at":   "created_at",
        "updated_at":   "updated_at",
    },
    "user_memberships": {
        "username":        "username",
        "membership_type": "membership_type",
        "activated_at":    "activated_at",
        "expires_at":      "expires_at",
        "activation_code": "activation_code",
    },
    "activation_codes": {
        # 云端 activation_codes → 本地 activation_admin.db admin_codes
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

    # ── 会员 ──
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

    # ── 产品 & 订单 & 客户 ──
    "products": {
        "name":        "name",
        "category":    "category",
        "unit_price":  "price",        # 云端 unit_price → 本地 price
        "stock":       "stock",
        "status":      "status",
        "note":        "description",  # 云端 note → 本地 description
        "created_at":  "created_at",
    },
    "orders": {
        "order_no":     "order_no",
        "customer":     "customer_name",  # 云端 customer → 本地 customer_name
        "product":      "product_name",   # 云端 product → 本地 product_name
        "quantity":     "quantity",
        "unit_price":   "unit_price",
        "total_price":  "total_amount",   # 云端 total_price → 本地 total_amount
        "status":       "status",
        "note":         "note",
        "created_at":   "created_at",
    },
    "customers": {
        "name":       "name",
        "company":    "company",
        "phone":      "phone",
        "email":      "email",
        "address":    "address",
        "note":       "note",
        "created_at": "created_at",
    },
    "staff": {
        "name":       "name",
        "phone":      "phone",
        "email":      "email",
        "position":   "position",
        "department": "department",
        "salary":     "salary",
        "status":     "status",
        "created_at": "created_at",
    },

    # ── 财务 ──
    "finance": {
        "type":        "type",
        "category":    "category",
        "amount":      "amount",
        "date":        "date",
        "description": "description",
        "order_no":    "order_no",
        "created_at":  "created_at",
    },

    # ── 钱包 & 交易 ──
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
        "balance_after": "balance_after",
        "description":   "description",
        "related_id":    "related_id",
        "created_at":    "created_at",
    },

    # ── 分销 ──
    "distribution_links": {
        # 云端无 user_name 列
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
        # 云端无 user_name 列
        "user_id":     "user_id",
        "from_user_id":"from_user_id",
        "amount":      "amount",
        "type":        "type",
        "status":      "status",
        "description": "description",
        "created_at":  "created_at",
    },
    "team_members": {
        # 云端无 user_name/parent_name 列
        "user_id":            "user_id",
        "parent_id":          "parent_id",
        "username":           "username",
        "level":              "level",
        "total_contribution": "total_contribution",
        "created_at":         "created_at",
    },
}

# ============================================================
# 各表对应的本地数据库文件（cloud_table → local db / local table）
# ============================================================
TABLE_META = {
    "users":               {"db": "users.db",             "table": "users"},
    "user_memberships":   {"db": "users.db",             "table": "user_memberships"},
    "activation_codes":    {"db": "activation_admin.db",  "table": "admin_codes"},
    "members":             {"db": "member.db",           "table": "member"},
    "products":           {"db": "product.db",           "table": "products"},
    "orders":             {"db": "order.db",             "table": "orders"},
    "customers":          {"db": "customer.db",          "table": "customer"},
    "staff":              {"db": "staff.db",             "table": "staff"},
    "finance":            {"db": "finance.db",           "table": "finance"},
    "wallet":             {"db": "wallet.db",            "table": "wallet"},
    "wallet_transactions": {"db": "wallet.db",           "table": "wallet_transactions"},
    "distribution_links": {"db": "distribution.db",      "table": "distribution_links"},
    "commissions":        {"db": "distribution.db",     "table": "commissions"},
    "team_members":       {"db": "distribution.db",     "table": "team_members"},
}

# 需要保护不被覆盖的本地管理员数据
PRESERVE_ADMIN = {
    "username": "admin",
    "password": "$2b$12$3wTB3CNyc9Fp8m4NBXAlWOMvvvQ95crWaz6QqKp2L64rX3oa8s7JO",
    "role": "admin",
    "license_type": "admin",
}


def _get_conn(cloud_table):
    """获取本地 SQLite 连接"""
    meta = TABLE_META[cloud_table]
    conn = get_conn(meta["db"])
    conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
    return conn, meta["table"], meta["db"]


def _pull_simple(cloud_table):
    """通用 pull：DELETE + INSERT 全量替换"""
    mapping = CLOUD_TO_LOCAL[cloud_table]
    conn, local_table, db_name = _get_conn(cloud_table)

    ok, cloud_rows = _request("GET", f"/rest/v1/{cloud_table}?select=*", service_key=True)
    if not ok or not isinstance(cloud_rows, list):
        logger.warning(f"拉取 {cloud_table} 失败: {cloud_rows}")
        close_conn(db_name)
        return 0

    local_rows = []
    for row in cloud_rows:
        local_row = {}
        for cloud_col, local_col in mapping.items():
            if cloud_col in row:
                local_row[local_col] = row[cloud_col]
        local_rows.append(local_row)

    cur = conn.cursor()
    cur.execute(f"DELETE FROM {local_table}")
    cols = list(mapping.values())
    placeholders = ",".join(["?"] * len(cols))
    sql = f"INSERT OR REPLACE INTO {local_table} ({','.join(cols)}) VALUES ({placeholders})"
    for lr in local_rows:
        cur.execute(sql, [lr.get(c) for c in cols])

    conn.commit()
    close_conn(db_name)
    logger.info(f"✅ 拉取 {cloud_table}: {len(local_rows)} 条")
    return len(local_rows)


def pull_users():
    """拉取云端 users → 本地 users.db（保护 admin）"""
    return _pull_with_preserve("users")


def pull_activation_codes():
    """拉取云端 activation_codes → 本地 activation_admin.db"""
    return _pull_simple("activation_codes")


def pull_products():
    return _pull_simple("products")


def pull_orders():
    return _pull_simple("orders")


def pull_customers():
    return _pull_simple("customers")


def pull_staff():
    return _pull_simple("staff")


def pull_finance():
    return _pull_simple("finance")


def pull_wallet():
    return _pull_simple("wallet")


def pull_wallet_transactions():
    """拉取云端 wallet_transactions → 本地 wallet.db（含锁保护）"""
    time.sleep(0.5)
    result = _pull_simple("wallet_transactions")
    time.sleep(0.5)
    return result


def pull_distribution_links():
    return _pull_simple("distribution_links")


def pull_commissions():
    return _pull_simple("commissions")


def pull_team_members():
    return _pull_simple("team_members")


def pull_user_memberships():
    return _pull_simple("user_memberships")


def pull_member():
    """拉取云端 members → 本地 member.db（含锁保护）"""
    time.sleep(0.5)
    result = _pull_simple("members")
    time.sleep(0.5)
    return result


def pull_activation_records():
    """拉取云端 activation_records → 本地 activation.db"""
    return _pull_simple("activation_records")


def pull_activation_logs():
    """拉取云端 activation_logs → 本地 activation_log.db"""
    return _pull_simple("activation_logs")


def pull_admins():
    """拉取云端 admins → 本地 admin.db"""
    return _pull_simple("admins")


def pull_audit_logs():
    """拉取云端 audit_logs → 本地 audit.db"""
    return _pull_simple("audit_logs")


def pull_operation_logs():
    """拉取云端 operation_logs → 本地 operation_log.db"""
    return _pull_simple("operation_logs")


def pull_orders_backup():
    """拉取云端 orders_backup → 本地 orders.db"""
    return _pull_simple("orders_backup")


def pull_personnel():
    """拉取云端 personnel → 本地 personnel_db.sqlite"""
    return _pull_simple("personnel")


def pull_schedules():
    """拉取云端 schedules → 本地 scheduler.db"""
    return _pull_simple("schedules")


def pull_sessions():
    """拉取云端 sessions → 本地 sessions.db"""
    return _pull_simple("sessions")


def pull_sync_logs():
    """拉取云端 sync_logs → 本地 sync_log.db"""
    return _pull_simple("sync_logs")


def pull_system_logs():
    """拉取云端 system_logs → 本地 system_logs.db"""
    return _pull_simple("system_logs")


def pull_todos():
    """拉取云端 todos → 本地 todos.db"""
    return _pull_simple("todos")


def pull_app_config():
    """拉取云端 app_config → 本地 app.db"""
    return _pull_simple("app_config")


def pull_cache_data():
    """拉取云端 cache_data → 本地 cache.db"""
    return _pull_simple("cache_data")


def _pull_with_preserve(cloud_table):
    """带 admin 保护的全量拉取（用于 users 表）"""
    mapping = CLOUD_TO_LOCAL[cloud_table]
    conn, local_table, db_name = _get_conn(cloud_table)

    ok, cloud_rows = _request("GET", f"/rest/v1/{cloud_table}?select=*", service_key=True)
    if not ok or not isinstance(cloud_rows, list):
        logger.warning(f"拉取 {cloud_table} 失败: {cloud_rows}")
        close_conn(db_name)
        return 0

    local_rows = []
    for row in cloud_rows:
        local_row = {}
        for cloud_col, local_col in mapping.items():
            if cloud_col in row:
                local_row[local_col] = row[cloud_col]
        local_rows.append(local_row)

    cur = conn.cursor()
    cur.execute(f"DELETE FROM {local_table}")
    cols = list(mapping.values())
    placeholders = ",".join(["?"] * len(cols))
    sql = f"INSERT OR REPLACE INTO {local_table} ({','.join(cols)}) VALUES ({placeholders})"
    for lr in local_rows:
        cur.execute(sql, [lr.get(c) for c in cols])

    # 确保 admin 账号不被云端覆盖
    adm_cols = [c for c in cols if c in PRESERVE_ADMIN]
    if adm_cols:
        adm_vals = [PRESERVE_ADMIN.get(c) for c in adm_cols]
        cur.execute(
            f"INSERT OR IGNORE INTO {local_table} ({','.join(adm_cols)}) "
            f"VALUES ({','.join(['?']*len(adm_cols))})",
            adm_vals
        )

    conn.commit()
    close_conn(db_name)
    logger.info(f"✅ 拉取 {cloud_table}: {len(local_rows)} 条（含admin保护）")
    return len(local_rows)


def pull_all_from_cloud():
    """一键拉取全部云端数据 → 本地（子线程异步执行，不阻塞 UI）
    
    - DNS 预检失败 → 跳过所有拉取，打印 warning，立即返回
    - DNS 可达 → 启动 daemon 子线程执行拉取，主线程立即返回
    - 子线程内异常不会导致崩溃或静默失败，均会写入日志
    """
    # DNS 预检：不可达则直接跳过，不阻塞
    if not _dns_check():
        logger.warning("⚠️ DNS 不可达，跳过本次云端拉取")
        return {"total": 0, "details": {}, "errors": [("dns", "dns_unreachable")],
                "status": "skipped_dns_unreachable"}

    logger.info("=" * 50)
    logger.info("🔄 开始从云端拉取全部数据...")
    logger.info("=" * 50)

    def _pull_worker():
        """子线程执行实际的串行拉取逻辑，异常全部捕获写入日志"""
        try:
            tasks = [
                ("用户",             pull_users),
                ("激活码",           pull_activation_codes),
                ("产品",             pull_products),
                ("订单",             pull_orders),
                ("客户",             pull_customers),
                ("员工",             pull_staff),
                ("财务",             pull_finance),
                ("会员",             pull_member),
                ("会员记录",         pull_user_memberships),
                ("钱包",             pull_wallet),
                ("钱包交易",         pull_wallet_transactions),
                ("分销链接",         pull_distribution_links),
                ("佣金",             pull_commissions),
                ("团队成员",         pull_team_members),
            ]

            results = {}
            total = 0
            for name, fn in tasks:
                try:
                    cnt = fn()
                    results[name] = {"count": cnt, "error": None}
                    total += cnt
                except Exception as e:
                    results[name] = {"count": 0, "error": str(e)[:120]}
                    logger.error(f"❌ 拉取 {name} 失败: {e}")

                # wallet 和 wallet_transactions 共用 wallet.db，中间留锁释放窗口
                if name in ("钱包",):
                    time.sleep(0.5)

                # distribution 三表共用 distribution.db，快速连续写入易触发 database locked
                if name in ("分销链接", "佣金"):
                    time.sleep(0.3)

            parts = [f"{k}:{v['count']}条" for k, v in results.items()]
            logger.info(f"📊 总计拉取 {total} 条")
            logger.info(f"📋 {'   '.join(parts)}")

            errors = [(k, r["error"]) for k, r in results.items() if r.get("error")]
            if errors:
                logger.warning(f"⚠️ 拉取异常明细: {errors}")
        except Exception as e:
            logger.error(f"❌ 云端拉取子线程崩溃: {e}", exc_info=True)

    thread = threading.Thread(target=_pull_worker, daemon=True, name="cloud_pull_worker")
    thread.start()
    # 立即返回，不等待子线程完成 → UI 不再阻塞
    return {"total": -1, "details": {}, "errors": [],
            "status": "async_pull_started"}


if __name__ == "__main__":
    info = pull_all_from_cloud()
    print(json.dumps(info, ensure_ascii=False, indent=2))
