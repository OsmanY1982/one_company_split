# `core/modules/personnel/wallet_service/_transactions.py`

> 路径：`core/modules/personnel/wallet_service/_transactions.py` | 行数：458


---


```python
# -*- coding: utf-8 -*-
"""
钱包交易操作（充值/提现/转账/佣金/查询/导出/报表/趋势）
"""
import os
import sys

# ── 路径：wallet_service/_transactions.py → 项目根目录（4层dirname）──
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import csv
from datetime import datetime, timedelta

try:
    from paths import DATA_DIR
except ImportError:
    try:
        from paths import DATA_DIR
    except ImportError:
        from core.paths import DATA_DIR

from ._db import init_db, _connect
from ._cloud import _sync_wallet_cloud, _sync_txn_cloud
from ._wallet_crud import get_wallet, get_or_create_wallet

# 财务同步（失败不影响本地操作）
try:
    from core.modules.business.finance_service import add_record as _fin_add
    _FINANCE_ENABLED = True
except Exception:
    _FINANCE_ENABLED = False


def recharge(user_id: str, amount: float, description: str = "充值",
             operator: str = "system") -> dict:
    """充值（自动同步云端）"""
    if amount <= 0:
        return {"ok": False, "error": "充值金额必须大于 0"}
    w = get_or_create_wallet(user_id)
    init_db()
    conn = _connect()
    try:
        conn.execute("BEGIN")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE wallet SET balance = balance + ?, "
            "total_income = total_income + ?, updated_at = ? WHERE id = ?",
            (amount, amount, now, w["id"])
        )
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'recharge', ?, ?, ?, ?)",
            (w["id"], amount, w["balance"] + amount,
             f"{description}（{operator}）", now)
        )
        conn.commit()
        new_balance = w["balance"] + amount

        updated_w = get_wallet(user_id)
        txn = {"wallet_id": w["id"], "type": "recharge",
               "amount": amount, "balance_after": new_balance,
               "description": f"{description}（{operator}）", "created_at": now}
        _sync_wallet_cloud(updated_w)
        _sync_txn_cloud(txn)
        if _FINANCE_ENABLED:
            _fin_add(date=now[:10], record_type="income",
                     category="充值", amount=amount,
                     description=f"钱包充值 → {user_id}（{operator}）")
        return {"ok": True, "balance": new_balance, "amount": amount}
    except Exception as e:
        conn.execute("ROLLBACK")
        return {"ok": False, "error": str(e)}


def withdraw(user_id: str, amount: float,
             description: str = "提现申请") -> dict:
    """提现（直接扣减余额）"""
    if amount <= 0:
        return {"ok": False, "error": "提现金额必须大于 0"}
    w = get_wallet(user_id)
    if not w:
        return {"ok": False, "error": "钱包不存在"}
    available = w["balance"] - w.get("frozen_amount", 0)
    if available < amount:
        return {"ok": False, "error": f"可用余额不足（{available:.2f}）"}
    init_db()
    conn = _connect()
    try:
        conn.execute("BEGIN")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE wallet SET balance = balance - ?, "
            "total_withdraw = total_withdraw + ?, updated_at = ? WHERE id = ?",
            (amount, amount, now, w["id"])
        )
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'withdraw', ?, ?, ?, ?)",
            (w["id"], -amount, w["balance"] - amount, description, now)
        )
        conn.commit()
        updated_w = get_wallet(user_id)
        txn = {"wallet_id": w["id"], "type": "withdraw",
               "amount": -amount, "balance_after": w["balance"] - amount,
               "description": description, "created_at": now}
        _sync_wallet_cloud(updated_w)
        _sync_txn_cloud(txn)
        if _FINANCE_ENABLED:
            _fin_add(date=now[:10], record_type="expense",
                     category="提现", amount=-amount,
                     description=f"提现 {user_id}（{description}）")
        return {"ok": True, "balance": w["balance"] - amount, "amount": amount}
    except Exception as e:
        conn.execute("ROLLBACK")
        return {"ok": False, "error": str(e)}


def transfer(from_user: str, to_user: str, amount: float,
             description: str = "") -> dict:
    """转账（原子操作，一方失败则全部回滚）"""
    if amount <= 0:
        return {"ok": False, "error": "转账金额必须大于 0"}
    if from_user == to_user:
        return {"ok": False, "error": "不能给自己转账"}
    w_from = get_wallet(from_user)
    w_to = get_or_create_wallet(to_user)
    if not w_from:
        return {"ok": False, "error": f"转出用户 {from_user} 不存在"}
    available = w_from["balance"] - w_from.get("frozen_amount", 0)
    if available < amount:
        return {"ok": False, "error": f"可用余额不足（{available:.2f}）"}
    init_db()
    conn = _connect()
    try:
        conn.execute("BEGIN")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 扣款
        conn.execute(
            "UPDATE wallet SET balance = balance - ?, updated_at = ? WHERE id = ?",
            (amount, now, w_from["id"])
        )
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'transfer_out', ?, ?, ?, ?)",
            (w_from["id"], -amount, w_from["balance"] - amount,
             f"转出至 {to_user}" + (f"（{description}）" if description else ""), now)
        )
        # 到账
        conn.execute(
            "UPDATE wallet SET balance = balance + ?, updated_at = ? WHERE id = ?",
            (amount, now, w_to["id"])
        )
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'transfer_in', ?, ?, ?, ?)",
            (w_to["id"], amount, w_to["balance"] + amount,
             f"由 {from_user} 转入" + (f"（{description}）" if description else ""), now)
        )
        conn.commit()
        from_wallet = get_wallet(from_user)
        to_wallet = get_wallet(to_user)
        _sync_wallet_cloud(from_wallet)
        _sync_wallet_cloud(to_wallet)
        _sync_txn_cloud({
            "wallet_id": w_from["id"], "type": "transfer_out",
            "amount": -amount, "balance_after": w_from["balance"] - amount,
            "description": f"转出至 {to_user}" + (f"（{description}）" if description else ""),
            "created_at": now
        })
        _sync_txn_cloud({
            "wallet_id": w_to["id"], "type": "transfer_in",
            "amount": amount, "balance_after": w_to["balance"] + amount,
            "description": f"由 {from_user} 转入" + (f"（{description}）" if description else ""),
            "created_at": now
        })
        if _FINANCE_ENABLED:
            _fin_add(date=now[:10], record_type="expense",
                     category="转账", amount=-amount,
                     description=f"转账 → {to_user}（{description}）")
            _fin_add(date=now[:10], record_type="income",
                     category="转账", amount=amount,
                     description=f"转账 ← {from_user}（{description}）")
        return {
            "ok": True,
            "from_balance": w_from["balance"] - amount,
            "to_balance": w_to["balance"] + amount,
            "amount": amount,
        }
    except Exception as e:
        conn.execute("ROLLBACK")
        return {"ok": False, "error": str(e)}


def add_commission(user_id: str, amount: float,
                   description: str = "佣金收入") -> dict:
    """发放佣金（自动同步云端）"""
    if amount <= 0:
        return {"ok": False, "error": "金额必须大于 0"}
    w = get_or_create_wallet(user_id)
    init_db()
    conn = _connect()
    try:
        conn.execute("BEGIN")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE wallet SET balance = balance + ?, "
            "total_income = total_income + ?, updated_at = ? WHERE id = ?",
            (amount, amount, now, w["id"])
        )
        conn.execute(
            "INSERT INTO wallet_transactions "
            "(wallet_id, type, amount, balance_after, description, created_at) "
            "VALUES (?, 'commission', ?, ?, ?, ?)",
            (w["id"], amount, w["balance"] + amount, description, now)
        )
        conn.commit()
        new_balance = w["balance"] + amount
        updated_w = get_wallet(user_id)
        txn = {"wallet_id": w["id"], "type": "commission",
               "amount": amount, "balance_after": new_balance,
               "description": description, "created_at": now}
        _sync_wallet_cloud(updated_w)
        _sync_txn_cloud(txn)
        if _FINANCE_ENABLED:
            _fin_add(date=now[:10], record_type="income",
                     category="佣金", amount=amount,
                     description=f"佣金发放 → {user_id}（{description}）")
        return {"ok": True, "balance": new_balance, "amount": amount}
    except Exception as e:
        conn.execute("ROLLBACK")
        return {"ok": False, "error": str(e)}


def get_transactions(wallet_id: int = None,
                     txn_type: str = "",
                     start_date: str = "",
                     end_date: str = "",
                     min_amount: float = None,
                     max_amount: float = None,
                     keyword: str = "",
                     limit: int = 200,
                     offset: int = 0) -> list[dict]:
    """
    获取交易记录（支持多维过滤）。
    wallet_id=None 表示全局（所有钱包）。
    """
    init_db()
    conn = _connect()
    sql = "SELECT * FROM wallet_transactions WHERE 1=1"
    params = []
    if wallet_id is not None:
        sql += " AND wallet_id=?"
        params.append(wallet_id)
    if txn_type:
        sql += " AND type=?"
        params.append(txn_type)
    if start_date:
        sql += " AND date(created_at) >= date(?)"
        params.append(start_date)
    if end_date:
        sql += " AND date(created_at) <= date(?)"
        params.append(end_date)
    if min_amount is not None:
        sql += " AND ABS(amount) >= ?"
        params.append(min_amount)
    if max_amount is not None:
        sql += " AND ABS(amount) <= ?"
        params.append(max_amount)
    if keyword:
        sql += " AND description LIKE ?"
        params.append(f"%{keyword}%")
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_income_expense_report(days: int = 30) -> dict:
    """
    获取收支报表（最近 N 天）。
    返回 {income, expense, net, transactions}
    """
    init_db()
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    conn = _connect()
    rows = conn.execute(
        "SELECT type, SUM(amount) as total, COUNT(*) as count "
        "FROM wallet_transactions WHERE created_at >= ? "
        "GROUP BY type",
        (since,)
    ).fetchall()

    income = expense = 0
    detail = {}
    for r in rows:
        t, total, count = r["type"], r["total"], r["count"]
        detail[t] = {"total": total, "count": count}
        if t in ("recharge", "commission", "transfer_in"):
            income += total
        elif t in ("withdraw", "transfer_out"):
            expense += abs(total)

    return {
        "income": income,
        "expense": expense,
        "net": income - expense,
        "since_days": days,
        "detail": detail,
    }


def get_balance_trend(days: int = 30) -> list[dict]:
    """
    获取每日余额趋势（最近 N 天）。
    返回: [{date: "2026-05-01", balance: 1000.0, income: 500, expense: 200}, ...]
    """
    init_db()
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    conn = _connect()
    income_rows = conn.execute(
        "SELECT DATE(created_at) as date, SUM(amount) as total "
        "FROM wallet_transactions "
        "WHERE DATE(created_at) >= ? AND type IN ('recharge','commission','transfer_in') "
        "GROUP BY DATE(created_at) ORDER BY date",
        (since,)
    ).fetchall()
    expense_rows = conn.execute(
        "SELECT DATE(created_at) as date, SUM(ABS(amount)) as total "
        "FROM wallet_transactions "
        "WHERE DATE(created_at) >= ? AND type IN ('withdraw','transfer_out') "
        "GROUP BY DATE(created_at) ORDER BY date",
        (since,)
    ).fetchall()

    income_map = {r["date"]: r["total"] for r in income_rows}
    expense_map = {r["date"]: r["total"] for r in expense_rows}

    result = []
    running = 0.0
    for i in range(days, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        inc = income_map.get(d, 0)
        exp = expense_map.get(d, 0)
        running += inc - exp
        result.append({
            "date": d,
            "income": inc,
            "expense": exp,
            "balance": running,
        })
    return result


def export_transactions_to_csv(filepath: str = None,
                                wallet_id: int = None,
                                days: int = 90) -> str:
    """
    导出交易记录为 CSV 文件。
    - filepath: 输出路径，默认 data/wallet_export_YYYYMMDD.csv
    - wallet_id: 指定钱包，不指定则导出全部
    - days: 导出最近 N 天
    """
    init_db()
    if filepath is None:
        date_str = datetime.now().strftime("%Y%m%d")
        filepath = os.path.join(DATA_DIR, f"wallet_export_{date_str}.csv")

    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    conn = _connect()
    if wallet_id:
        rows = conn.execute(
            "SELECT t.*, w.user_id FROM wallet_transactions t "
            "JOIN wallet w ON t.wallet_id = w.id "
            "WHERE t.wallet_id = ? AND t.created_at >= ? "
            "ORDER BY t.id DESC",
            (wallet_id, since)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT t.*, w.user_id FROM wallet_transactions t "
            "JOIN wallet w ON t.wallet_id = w.id "
            "WHERE t.created_at >= ? ORDER BY t.id DESC",
            (since,)
        ).fetchall()

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "用户ID", "钱包ID", "类型", "金额", "余额后",
            "描述", "创建时间"
        ])
        type_labels = {
            "recharge": "充值", "withdraw": "提现",
            "transfer_in": "转入", "transfer_out": "转出",
            "commission": "佣金", "freeze": "冻结", "unfreeze": "解冻",
        }
        for r in rows:
            label = type_labels.get(r["type"], r["type"])
            writer.writerow([
                r["id"], r["user_id"], r["wallet_id"], label,
                f"{r['amount']:.2f}", f"{r['balance_after']:.2f}",
                r["description"] or "", r["created_at"]
            ])
    return filepath


def delete_transaction(txn_id: int, operator: str = "admin") -> dict:
    """删除一条错误交易记录（慎用！）。"""
    init_db()
    conn = _connect()
    txn = conn.execute(
        "SELECT * FROM wallet_transactions WHERE id=?", (txn_id,)
    ).fetchone()
    if not txn:
        return {"ok": False, "error": "交易记录不存在"}

    wallet_id = txn["wallet_id"]
    amount = txn["amount"]
    txn_type = txn["type"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn.execute("BEGIN")
        reverse_amount = -amount
        conn.execute(
            "UPDATE wallet SET balance = balance + ?, updated_at=? WHERE id=?",
            (reverse_amount, now, wallet_id)
        )
        if txn_type == "freeze":
            conn.execute(
                "UPDATE wallet SET frozen_amount = frozen_amount - ? WHERE id=?",
                (abs(amount), wallet_id)
            )
        elif txn_type == "unfreeze":
            conn.execute(
                "UPDATE wallet SET frozen_amount = frozen_amount + ? WHERE id=?",
                (abs(amount), wallet_id)
            )
        conn.execute("DELETE FROM wallet_transactions WHERE id=?", (txn_id,))
        conn.commit()
        w_row = conn.execute("SELECT * FROM wallet WHERE id=?", (wallet_id,)).fetchone()
        if w_row:
            _sync_wallet_cloud(dict(w_row))
        return {
            "ok": True,
            "txn_id": txn_id,
            "corrected_amount": reverse_amount,
            "wallet_id": wallet_id
        }
    except Exception as e:
        conn.execute("ROLLBACK")
        return {"ok": False, "error": str(e)}

```
