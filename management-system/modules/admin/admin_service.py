# -*- coding: utf-8 -*-
"""
管理员服务层
提供日志记录、统计查询、备份管理等通用管理功能
"""
from datetime import datetime
from pathlib import Path
from core.paths import DATA_DIR
from core.database import get_conn

DB_FILE = Path(DATA_DIR) / "admin.db"


def _get_conn():
    """获取数据库连接"""
    return get_conn("admin.db")


def init_db():
    """初始化数据库表"""
    conn = _get_conn()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_user TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_admin_logs_user ON admin_logs(admin_user)
    ''')
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_admin_logs_action ON admin_logs(action)
    ''')
    conn.commit()
    conn.close()


def add_log(admin_user: str, action: str, target: str = "",
            details: str = "", ip_address: str = "") -> dict:
    """记录管理日志"""
    try:
        conn = _get_conn()
        conn.execute(
            """INSERT INTO admin_logs (admin_user, action, target, details, ip_address)
               VALUES (?, ?, ?, ?, ?)""",
            (admin_user, action, target, details, ip_address)
        )
        conn.commit()
        conn.close()
        return {"ok": True, "msg": "日志已记录"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def get_logs(admin_user: str = "", action: str = "",
             limit: int = 1000) -> list:
    """查询管理日志"""
    conn = _get_conn()
    sql = """SELECT id, admin_user, action, target, details, ip_address, created_at
             FROM admin_logs"""
    params = []
    conditions = []

    if admin_user:
        conditions.append("admin_user = ?")
        params.append(admin_user)
    if action:
        conditions.append("action = ?")
        params.append(action)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_log_stats() -> dict:
    """获取日志统计"""
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) FROM admin_logs").fetchone()[0]
    today = conn.execute(
        "SELECT COUNT(*) FROM admin_logs WHERE date(created_at) = date('now')"
    ).fetchone()[0]
    action_counts = conn.execute(
        "SELECT action, COUNT(*) as count FROM admin_logs GROUP BY action"
    ).fetchall()
    conn.close()

    return {
        "total": total,
        "today": today,
        "by_action": {r[0]: r[1] for r in action_counts}
    }


def clear_logs() -> dict:
    """清空所有日志"""
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM admin_logs")
        conn.commit()
        conn.close()
        return {"ok": True, "msg": "日志已清空"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


# ══════════════════════════════════════════════════════
#  云端同步
# ══════════════════════════════════════════════════════

def _sync_to_cloud(action: str, payload: dict):
    """同步到云端（非阻塞）"""
    try:
        from core.supabase_client import CloudAdminLog
        if action == "upsert":
            CloudAdminLog.upsert(**payload)
    except Exception as e:
        print(f"[AdminService] 云端同步失败 (non-blocking): {e}")


if __name__ == "__main__":
    init_db()
    print("管理员服务测试")
    stats = get_log_stats()
    print(f"日志统计: {stats}")
