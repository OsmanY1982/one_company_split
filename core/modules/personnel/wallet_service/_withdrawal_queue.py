# -*- coding: utf-8 -*-
"""
提现审批队列
"""
import os
import sys

# ── 路径：wallet_service/_withdrawal_queue.py → 项目根目录（4层dirname）──
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datetime import datetime

try:
    from database import get_conn
except ImportError:
    try:
        from database import get_conn
    except ImportError:
        from core.database import get_conn

from ._db import _connect, init_withdrawal_queue
from ._cloud import _sync_wallet_cloud
from ._wallet_crud import get_wallet


def freeze_amount(user_id: str, amount: float, reason: str = "") -> dict:
    """冻结金额（如提现审核中）"""
    w = get_wallet(user_id)
    if not w:
        return {"ok": False, "error": "钱包不存在"}
    available = w["balance"] - w.get("frozen_amount", 0)
    if available < amount:
        return {"ok": False, "error": f"可用余额不足（{available:.2f}）"}

    # 延迟导入避免循环依赖
    from ._db import init_db
    from ._cloud import _sync_txn_cloud

    init_db()
    conn = _connect()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("BEGIN")
    conn.execute(
        "UPDATE wallet SET frozen_amount = frozen_amount + ?, updated_at = ? "
        "WHERE user_id = ?",
        (amount, now, str(user_id))
    )
    conn.execute(
        "INSERT INTO wallet_transactions "
        "(wallet_id, type, amount, balance_after, description, created_at) "
        "VALUES (?, 'freeze', ?, ?, ?, ?)",
        (w["id"], -amount, w["balance"], reason or "冻结", now)
    )
    conn.commit()
    updated_wallet = get_wallet(user_id)
    txn = {"wallet_id": w["id"], "type": "freeze",
           "amount": -amount, "balance_after": w["balance"],
           "description": reason or "冻结", "created_at": now}
    _sync_wallet_cloud(updated_wallet)
    _sync_txn_cloud(txn)
    return {"ok": True}


def unfreeze_amount(user_id: str, amount: float, reason: str = "") -> dict:
    """解冻金额"""
    w = get_wallet(user_id)
    if not w:
        return {"ok": False, "error": "钱包不存在"}
    if w.get("frozen_amount", 0) < amount:
        return {"ok": False, "error": "冻结金额不足"}

    from ._db import init_db
    from ._cloud import _sync_txn_cloud

    init_db()
    conn = _connect()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("BEGIN")
    conn.execute(
        "UPDATE wallet SET frozen_amount = frozen_amount - ?, updated_at = ? "
        "WHERE user_id = ?",
        (amount, now, str(user_id))
    )
    conn.execute(
        "INSERT INTO wallet_transactions "
        "(wallet_id, type, amount, balance_after, description, created_at) "
        "VALUES (?, 'unfreeze', ?, ?, ?, ?)",
        (w["id"], amount, w["balance"], reason or "解冻", now)
    )
    conn.commit()
    updated_wallet = get_wallet(user_id)
    txn = {"wallet_id": w["id"], "type": "unfreeze",
           "amount": amount, "balance_after": w["balance"],
           "description": reason or "解冻", "created_at": now}
    _sync_wallet_cloud(updated_wallet)
    _sync_txn_cloud(txn)
    return {"ok": True}


def submit_withdrawal_request(user_id: str, amount: float,
                               description: str = "提现申请") -> dict:
    """
    提交提现申请（自动冻结金额，状态=pending）。
    """
    if amount <= 0:
        return {"ok": False, "error": "金额必须大于 0"}
    w = get_wallet(user_id)
    if not w:
        return {"ok": False, "error": "钱包不存在"}
    available = w.get("balance", 0) - w.get("frozen_amount", 0)
    if available < amount:
        return {"ok": False, "error": f"可用余额不足（{available:.2f}）"}

    init_withdrawal_queue()
    conn = _connect()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute("BEGIN")
        conn.execute(
            "UPDATE wallet SET frozen_amount = frozen_amount + ?, "
            "updated_at = ? WHERE id = ?",
            (amount, now, w["id"])
        )
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'freeze', ?, ?, ?, ?)",
            (w["id"], -amount, w["balance"], f"提现冻结：{amount:.2f}", now)
        )
        conn.execute(
            "INSERT INTO withdrawal_queue "
            "(user_id, wallet_id, amount, description, status, created_at) "
            "VALUES (?, ?, ?, ?, 'pending', ?)",
            (str(user_id), w["id"], amount, description, now)
        )
        conn.commit()
        updated_w = get_wallet(user_id)
        _sync_wallet_cloud(updated_w)
        return {"ok": True, "frozen": amount, "message": f"申请已提交，冻结金额 {amount:.2f}"}
    except Exception as e:
        conn.execute("ROLLBACK")
        return {"ok": False, "error": str(e)}


def get_pending_withdrawals() -> list[dict]:
    """获取所有待审批的提现申请"""
    init_withdrawal_queue()
    conn = _connect()
    rows = conn.execute(
        "SELECT wq.*, wa.user_id, wa.balance as wallet_balance "
        "FROM withdrawal_queue wq "
        "JOIN wallet wa ON wq.wallet_id = wa.id "
        "WHERE wq.status = 'pending' "
        "ORDER BY wq.id DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_all_withdrawal_requests(status: str = "", limit: int = 100) -> list[dict]:
    """获取所有提现申请（可按状态筛选）"""
    init_withdrawal_queue()
    conn = _connect()
    if status:
        rows = conn.execute(
            "SELECT wq.*, wa.user_id "
            "FROM withdrawal_queue wq "
            "JOIN wallet wa ON wq.wallet_id = wa.id "
            "WHERE wq.status = ? ORDER BY wq.id DESC LIMIT ?",
            (status, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT wq.*, wa.user_id "
            "FROM withdrawal_queue wq "
            "JOIN wallet wa ON wq.wallet_id = wa.id "
            "ORDER BY wq.id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def approve_withdrawal(request_id: int, operator: str = "admin",
                       note: str = "") -> dict:
    """审批通过提现申请：正式扣款（从冻结中扣）、更新状态。"""
    init_withdrawal_queue()
    conn = _connect()
    req = conn.execute(
        "SELECT * FROM withdrawal_queue WHERE id = ? AND status='pending'",
        (request_id,)
    ).fetchone()
    if not req:
        return {"ok": False, "error": "申请不存在或已处理"}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute("BEGIN")
        conn.execute(
            "UPDATE wallet SET "
            "balance = balance - ?, "
            "frozen_amount = frozen_amount - ?, "
            "total_withdraw = total_withdraw + ?, "
            "updated_at = ? WHERE id = ?",
            (req["amount"], req["amount"], req["amount"],
             now, req["wallet_id"])
        )
        w_after = conn.execute(
            "SELECT balance FROM wallet WHERE id=?", (req["wallet_id"],)
        ).fetchone()["balance"]
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'withdraw', ?, ?, ?, ?)",
            (req["wallet_id"], -req["amount"], w_after,
             f"提现审批通过", now)
        )
        conn.execute(
            "UPDATE withdrawal_queue SET status='approved', "
            "reviewed_by=?, reviewed_at=?, note=? WHERE id=?",
            (operator, now, note or "", request_id)
        )
        conn.commit()
        wallet = get_wallet(req["user_id"])
        _sync_wallet_cloud(wallet)
        return {"ok": True, "amount": req["amount"], "user_id": req["user_id"]}
    except Exception as e:
        conn.execute("ROLLBACK")
        return {"ok": False, "error": str(e)}


def reject_withdrawal(request_id: int, operator: str = "admin",
                      note: str = "") -> dict:
    """审批拒绝提现申请：解冻金额、更新状态。"""
    init_withdrawal_queue()
    conn = _connect()
    req = conn.execute(
        "SELECT * FROM withdrawal_queue WHERE id = ? AND status='pending'",
        (request_id,)
    ).fetchone()
    if not req:
        return {"ok": False, "error": "申请不存在或已处理"}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute("BEGIN")
        conn.execute(
            "UPDATE wallet SET frozen_amount = frozen_amount - ?, "
            "updated_at = ? WHERE id = ?",
            (req["amount"], now, req["wallet_id"])
        )
        w_after = conn.execute(
            "SELECT balance FROM wallet WHERE id=?", (req["wallet_id"],)
        ).fetchone()["balance"]
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'unfreeze', ?, ?, ?, ?)",
            (req["wallet_id"], req["amount"], w_after,
             f"提现拒绝解冻", now)
        )
        conn.execute(
            "UPDATE withdrawal_queue SET status='rejected', "
            "reviewed_by=?, reviewed_at=?, note=? WHERE id=?",
            (operator, now, note or "", request_id)
        )
        conn.commit()
        wallet = get_wallet(req["user_id"])
        _sync_wallet_cloud(wallet)
        return {"ok": True, "amount": req["amount"], "user_id": req["user_id"]}
    except Exception as e:
        conn.execute("ROLLBACK")
        return {"ok": False, "error": str(e)}


def cancel_withdrawal_request(request_id: int) -> dict:
    """取消待审批的提现申请，自动解冻金额。"""
    init_withdrawal_queue()
    conn = _connect()
    req = conn.execute(
        "SELECT * FROM withdrawal_queue WHERE id=? AND status='pending'",
        (request_id,)
    ).fetchone()
    if not req:
        return {"ok": False, "error": "申请不存在或已处理，无法取消"}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute("BEGIN")
        conn.execute(
            "UPDATE wallet SET frozen_amount = frozen_amount - ?, updated_at=? WHERE id=?",
            (req["amount"], now, req["wallet_id"])
        )
        w_after = conn.execute(
            "SELECT balance FROM wallet WHERE id=?", (req["wallet_id"],)
        ).fetchone()["balance"]
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'unfreeze', ?, ?, ?, ?)",
            (req["wallet_id"], req["amount"], w_after,
             f"取消提现申请 #{request_id}，金额解冻", now)
        )
        conn.execute(
            "UPDATE withdrawal_queue SET status='cancelled', reviewed_by='system', "
            "reviewed_at=?, note='用户取消' WHERE id=?",
            (now, request_id)
        )
        conn.commit()
        wallet = get_wallet(req["user_id"])
        _sync_wallet_cloud(wallet)
        return {"ok": True, "amount": req["amount"], "user_id": req["user_id"]}
    except Exception as e:
        conn.execute("ROLLBACK")
        return {"ok": False, "error": str(e)}


def delete_withdrawal_request(request_id: int) -> dict:
    """删除一条提现申请记录（仅限终态）。"""
    init_withdrawal_queue()
    conn = _connect()
    req = conn.execute(
        "SELECT * FROM withdrawal_queue WHERE id=?", (request_id,)
    ).fetchone()
    if not req:
        return {"ok": False, "error": "记录不存在"}
    if req["status"] == "pending":
        return {
            "ok": False,
            "error": "pending 状态不能直接删除，请先「取消申请」"
        }
    try:
        conn.execute("DELETE FROM withdrawal_queue WHERE id=?", (request_id,))
        conn.commit()
        return {"ok": True, "id": request_id, "status": req["status"]}
    except Exception as e:
        conn.execute("ROLLBACK")
        return {"ok": False, "error": str(e)}


def clear_withdrawal_queue(status: str = "terminal") -> dict:
    """批量清理提现申请记录。"""
    init_withdrawal_queue()
    conn = _connect()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if status == "terminal" or status == "processed":
        deleted = conn.execute(
            "DELETE FROM withdrawal_queue WHERE status IN ('approved','rejected')"
        ).rowcount
    elif status == "cancelled":
        deleted = conn.execute(
            "DELETE FROM withdrawal_queue WHERE status='cancelled'"
        ).rowcount
    elif status == "all":
        rows = conn.execute(
            "SELECT wallet_id, amount FROM withdrawal_queue WHERE status='pending'"
        ).fetchall()
        for r in rows:
            conn.execute(
                "UPDATE wallet SET frozen_amount = frozen_amount - ?, updated_at=? WHERE id=?",
                (r["amount"], now, r["wallet_id"])
            )
        cursor = conn.execute("DELETE FROM withdrawal_queue")
        deleted = cursor.rowcount
    else:
        return {"ok": False, "error": f"未知状态: {status}"}

    conn.commit()
    return {"ok": True, "deleted": deleted}
