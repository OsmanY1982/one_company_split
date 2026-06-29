# -*- coding: utf-8 -*-
"""
钱包 CRUD 与查询
"""
import os
import sys

# ── 路径：wallet_service/_wallet_crud.py → 项目根目录（4层dirname）──
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datetime import datetime, timedelta
from typing import Optional

from ._db import init_db, _connect
from ._cloud import _sync_wallet_cloud


def get_wallet(user_id: str) -> Optional[dict]:
    """获取用户钱包，不存在则返回 None"""
    init_db()
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM wallet WHERE user_id = ?", (str(user_id),)
    ).fetchone()
    return dict(row) if row else None


def get_or_create_wallet(user_id: str) -> dict:
    """获取或创建用户钱包（首次创建自动同步云端）"""
    w = get_wallet(user_id)
    if w:
        return w
    init_db()
    conn = _connect()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute(
            "INSERT INTO wallet (user_id, balance, frozen_amount, total_income, "
            "total_withdraw, created_at, updated_at) "
            "VALUES (?, 0, 0, 0, 0, ?, ?)",
            (str(user_id), now, now)
        )
        conn.commit()
    except Exception:
        pass
    row = conn.execute(
        "SELECT * FROM wallet WHERE user_id = ?", (str(user_id),)
    ).fetchone()
    wallet = dict(row) if row else {}
    if wallet:
        _sync_wallet_cloud(wallet)
    return wallet


def get_balance(user_id: str) -> float:
    """快捷方法：获取用户余额"""
    w = get_wallet(user_id)
    return w.get("balance", 0) if w else 0


def get_all_wallets(search: str = "") -> list[dict]:
    """获取所有钱包（支持搜索）"""
    init_db()
    conn = _connect()
    if search:
        rows = conn.execute(
            "SELECT * FROM wallet WHERE user_id LIKE ? ORDER BY id DESC",
            (f"%{search}%",)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM wallet ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_wallet_stats() -> dict:
    """获取全局钱包统计"""
    init_db()
    conn = _connect()
    row = conn.execute(
        "SELECT COUNT(*) as count, "
        "COALESCE(SUM(balance), 0) as total_balance, "
        "COALESCE(SUM(frozen_amount), 0) as total_frozen, "
        "COALESCE(SUM(total_income), 0) as total_income, "
        "COALESCE(SUM(total_withdraw), 0) as total_withdraw "
        "FROM wallet WHERE status='active'"
    ).fetchone()
    return dict(row)


def get_top_wallets(limit: int = 10, by: str = "balance") -> list[dict]:
    """
    获取余额最高的钱包。
    by: balance | total_income | total_withdraw
    """
    allowed = {"balance", "total_income", "total_withdraw"}
    col = by if by in allowed else "balance"
    init_db()
    conn = _connect()
    rows = conn.execute(
        f"SELECT * FROM wallet WHERE status='active' "
        f"ORDER BY {col} DESC LIMIT ?",
        (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


def update_wallet_status(user_id: str, status: str) -> dict:
    """更新钱包状态（封禁/激活）"""
    w = get_wallet(user_id)
    if not w:
        return {"ok": False, "error": "钱包不存在"}
    init_db()
    conn = _connect()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE wallet SET status=?, updated_at=? WHERE user_id=?",
        (status, now, str(user_id))
    )
    conn.commit()
    updated_w = get_wallet(user_id)
    _sync_wallet_cloud(updated_w)
    return {"ok": True}


def get_wallet_detail(user_id: str) -> dict:
    """获取钱包完整详情（包含最近10条交易）"""
    # 延迟导入避免循环依赖
    from ._transactions import get_transactions, get_balance_trend

    w = get_wallet(user_id)
    if not w:
        return {}
    txns = get_transactions(w["id"], limit=10)
    trend = get_balance_trend(7)  # 7天趋势
    return {
        **w,
        "recent_transactions": txns,
        "balance_trend": trend,
        "available": w.get("balance", 0) - w.get("frozen_amount", 0),
    }


def delete_wallet(user_id: str, force: bool = False) -> dict:
    """删除钱包（慎用！）。"""
    # 延迟导入避免循环依赖
    from ._withdrawal_queue import get_pending_withdrawals

    w = get_wallet(user_id)
    if not w:
        return {"ok": False, "error": "钱包不存在"}

    balance = w.get("balance", 0)
    frozen = w.get("frozen_amount", 0)

    pending = get_pending_withdrawals()
    has_pending = any(p["user_id"] == user_id for p in pending)

    if has_pending:
        return {"ok": False, "error": "有待审批的提现申请，请先处理后再删除"}

    if not force and (balance != 0 or frozen != 0):
        return {
            "ok": False,
            "error": f"钱包余额≠0（{balance:.2f}）或冻结≠0（{frozen:.2f}），"
                      "请先清零后再删除，或使用 force=True 强制删除"
        }

    conn = _connect()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute("BEGIN")
        if force and (balance != 0 or frozen != 0):
            conn.execute(
                "UPDATE wallet SET balance=0, frozen_amount=0, status='deleted', "
                "updated_at=? WHERE user_id=?",
                (now, user_id)
            )
        conn.execute("DELETE FROM wallet_transactions WHERE wallet_id=?", (w["id"],))
        conn.execute("DELETE FROM withdrawal_queue WHERE wallet_id=? AND status='pending'", (w["id"],))
        conn.execute("DELETE FROM wallet WHERE id=?", (w["id"],))
        conn.commit()
        return {"ok": True, "user_id": user_id, "force": force}
    except Exception as e:
        conn.execute("ROLLBACK")
        return {"ok": False, "error": str(e)}
