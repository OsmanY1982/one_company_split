# -*- coding: utf-8 -*-
from __future__ import annotations
"""
系统日志 — Service 层
管理操作日志(operation_log.db) 和 系统日志(system_logs.db)
"""
import os
from datetime import datetime, timedelta
from core.database import get_conn, commit, ensure_tables


# ──────────────────────────────────────────
#  数据库初始化
# ──────────────────────────────────────────

_ERROR_LOGS_DDL = """
CREATE TABLE IF NOT EXISTS error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level TEXT DEFAULT 'ERROR',
    module TEXT,
    message TEXT,
    stack_trace TEXT,
    handled INTEGER DEFAULT 0
)
"""


def init_error_logs_db():
    """创建错误日志表（如不存在）"""
    ensure_tables("system_logs.db", [_ERROR_LOGS_DDL])


# ──────────────────────────────────────────
#  操作日志 (operation_log.db)
# ──────────────────────────────────────────

def get_operation_logs(op_type: str = "全部", date_from: str = None,
                       date_to: str = None, limit: int = 100) -> list[dict]:
    """获取操作日志列表"""
    try:
        conn = get_conn("operation_log.db")
    except Exception:
        return []
    query = "SELECT id, created_at, username, action, target, details FROM operation_logs WHERE 1=1"
    params = []
    if op_type != "全部":
        query += " AND action LIKE ?"
        params.append(f"%{op_type}%")
    if date_from and date_to:
        query += " AND date(created_at) BETWEEN ? AND ?"
        params.extend([date_from, date_to])
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in conn.execute(query, params).fetchall()]


# ──────────────────────────────────────────
#  同步日志 (system_logs.db → sync_logs)
# ──────────────────────────────────────────

def get_last_sync() -> dict | None:
    """获取最近一次同步记录"""
    try:
        conn = get_conn("system_logs.db")
    except Exception:
        return None
    row = conn.execute(
        "SELECT created_at, status FROM sync_logs ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    return dict(row) if row else None


def get_sync_records(limit: int = 50) -> list[dict]:
    """获取同步记录列表"""
    try:
        conn = get_conn("system_logs.db")
    except Exception:
        return []
    rows = conn.execute(
        "SELECT created_at, table_name, direction, record_count, status "
        "FROM sync_logs ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────
#  错误日志 (system_logs.db → error_logs)
# ──────────────────────────────────────────

def get_error_stats() -> dict:
    """获取错误统计: {today, week, unhandled}"""
    try:
        conn = get_conn("system_logs.db")
    except Exception:
        return {"today": 0, "week": 0, "unhandled": 0}
    init_error_logs_db()
    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    today_cnt = conn.execute(
        "SELECT COUNT(*) as c FROM error_logs WHERE date(created_at) = ?", (today,)
    ).fetchone()["c"]
    week_cnt = conn.execute(
        "SELECT COUNT(*) as c FROM error_logs WHERE date(created_at) >= ?", (week_ago,)
    ).fetchone()["c"]
    unhandled_cnt = conn.execute(
        "SELECT COUNT(*) as c FROM error_logs WHERE handled = 0"
    ).fetchone()["c"]
    return {"today": today_cnt, "week": week_cnt, "unhandled": unhandled_cnt}


def get_error_logs(limit: int = 50) -> list[dict]:
    """获取错误日志列表"""
    try:
        conn = get_conn("system_logs.db")
    except Exception:
        return []
    init_error_logs_db()
    rows = conn.execute(
        "SELECT created_at, level, module, message, stack_trace "
        "FROM error_logs ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────
#  清理
# ──────────────────────────────────────────

def clear_old_logs(days: int = 30) -> dict:
    """清理 N 天前的所有日志"""
    deleted = {}
    # 操作日志
    try:
        conn = get_conn("operation_log.db")
        conn.execute("DELETE FROM operation_logs WHERE created_at < date('now', ?)", (f'-{days} days',))
        commit("operation_log.db")
        deleted["operation"] = conn.total_changes
    except Exception:
        pass
    # 同步日志 + 错误日志
    try:
        conn = get_conn("system_logs.db")
        conn.execute("DELETE FROM sync_logs WHERE created_at < date('now', ?)", (f'-{days} days',))
        commit("system_logs.db")
        deleted["sync"] = conn.total_changes
        conn.execute("DELETE FROM error_logs WHERE created_at < date('now', ?)", (f'-{days} days',))
        commit("system_logs.db")
        deleted["error"] = conn.total_changes
    except Exception:
        pass
    return {"ok": True, "deleted": deleted}


def check_cloud_connection() -> bool:
    """检查 Supabase 云端连接"""
    try:
        from core.supabase_client import supabase
        supabase.table("users").select("count", count="exact").limit(1).execute()
        return True
    except Exception:
        return False
