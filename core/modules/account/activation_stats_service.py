# -*- coding: utf-8 -*-
"""
激活数据统计 — Service 层
"""
import os
from core.database import get_conn

ADMIN_DB = "activation_admin.db"
LOG_DB = "activation_log.db"


def get_kpi_stats() -> dict:
    """获取 KPI 卡片统计: total, used, unused, trial, pro, vip"""
    stats = {"total": 0, "used": 0, "unused": 0, "trial": 0, "pro": 0, "vip": 0}
    try:
        conn = get_conn(ADMIN_DB)
    except Exception:
        return stats
    for key, cond in [
        ("total", "SELECT COUNT(*) as c FROM admin_codes"),
        ("used", "SELECT COUNT(*) as c FROM admin_codes WHERE status='used'"),
        ("unused", "SELECT COUNT(*) as c FROM admin_codes WHERE status='unused'"),
        ("trial", "SELECT COUNT(*) as c FROM admin_codes WHERE user_type='TRIAL'"),
        ("pro", "SELECT COUNT(*) as c FROM admin_codes WHERE user_type='PRO'"),
        ("vip", "SELECT COUNT(*) as c FROM admin_codes WHERE user_type='VIP'"),
    ]:
        stats[key] = conn.execute(cond).fetchone()["c"]
    return stats


def get_activated_users() -> list[dict]:
    """获取已激活用户列表"""
    try:
        conn = get_conn(ADMIN_DB)
    except Exception:
        return []
    rows = conn.execute(
        "SELECT bound_account, user_type, code, bound_machine, used_at "
        "FROM admin_codes WHERE status='used' ORDER BY used_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_activation_logs(limit: int = 20) -> list[dict]:
    """获取最近激活记录"""
    try:
        conn = get_conn(LOG_DB)
    except Exception:
        return []
    rows = conn.execute(
        "SELECT account, machine_code, code, code_type, result, created_at "
        "FROM activation_log ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    return [dict(r) for r in rows]