# -*- coding: utf-8 -*-
"""
财务服务模块
提供：收支记录管理、统计报表
数据库：data/finance.db (finance 表)
"""
from datetime import datetime
from typing import Optional

import os, sys

# ── 路径兼容 ──────────────────────────────────────────────
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.paths import DATA_DIR
from core.database import get_conn
from core.operation_log import log_action

DB_PATH = os.path.join(DATA_DIR, "finance.db")


def _connect():
    return get_conn("finance.db")


def init_db():
    """初始化财务数据库（兼容现有表结构）"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = _connect()
    # 实际表结构：id, type, category, amount, date, description, order_no, created_at
    conn.execute('''
        CREATE TABLE IF NOT EXISTS finance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            category TEXT DEFAULT '',
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            description TEXT DEFAULT '',
            order_no TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sync_version INTEGER DEFAULT 0,
            last_modified_by TEXT DEFAULT 'desktop',
            last_sync_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def add_record(date: str, record_type: str, category: str,
               amount: float, description: str = "",
               order_no: str = "") -> dict:
    """
    添加财务收支记录。
    record_type: "income" | "expense"
    category: 分类（如：充值、佣金、提现、转账、工资、补贴...）
    amount: 金额（收入为正，支出为负）
    description: 描述/备注
    order_no: 订单号（可选）
    """
    init_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _connect()
    try:
        cursor = conn.execute(
            "INSERT INTO finance (date, type, category, amount, description, order_no, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (date, record_type, category, amount, description, order_no, now)
        )
        conn.commit()
        record_id = cursor.lastrowid
        conn.close()
        
        # 同步到云端
        _sync_to_cloud("upsert", {
            "id": record_id,
            "date": date,
            "type": record_type,
            "category": category,
            "amount": amount,
            "description": description,
            "order_no": order_no,
            "created_at": now
        })
        
        try:
            log_action("system", f"财务{record_type}", "finance",
                       f"{category}: {amount}, {description}")
        except Exception:
            pass
        
        return {"ok": True, "id": record_id}
    except Exception as e:
        conn.close()
        return {"ok": False, "error": str(e)}


def get_records(start_date: str = None, end_date: str = None,
                record_type: str = None, category: str = None,
                keyword: str = None,
                limit: int = 500) -> list[dict]:
    """查询财务记录，支持过滤"""
    init_db()
    conn = _connect()
    sql = "SELECT * FROM finance WHERE 1=1"
    params = []
    if start_date:
        sql += " AND date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND date <= ?"
        params.append(end_date)
    if record_type:
        sql += " AND type = ?"
        params.append(record_type)
    if category:
        sql += " AND category = ?"
        params.append(category)
    if keyword:
        sql += " AND (description LIKE ? OR category LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    sql += " ORDER BY date DESC, id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_summary(start_date: str = None, end_date: str = None) -> dict:
    """获取收支汇总"""
    init_db()
    conn = _connect()
    sql = "SELECT type, COALESCE(SUM(amount), 0) as total FROM finance WHERE 1=1"
    params = []
    if start_date:
        sql += " AND date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND date <= ?"
        params.append(end_date)
    sql += " GROUP BY type"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    income = 0.0
    expense = 0.0
    for r in rows:
        if r["type"] == "income":
            income = r["total"]
        elif r["type"] == "expense":
            expense = r["total"]
    return {
        "income": income,
        "expense": expense,
        "net": income - expense
    }


def delete_record(record_id: int) -> dict:
    """删除财务记录"""
    init_db()
    conn = _connect()
    cursor = conn.execute("DELETE FROM finance WHERE id=?", (record_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    if deleted:
        try:
            log_action("system", "财务删除", "finance", f"删除记录 ID={record_id}")
        except Exception:
            pass
    return {"ok": deleted > 0, "deleted": deleted}


def update_record(record_id: int, date: str = None,
                  record_type: str = None, category: str = None,
                  amount: float = None, note: str = None) -> dict:
    """更新财务记录"""
    init_db()
    conn = _connect()
    fields = []
    params = []
    if date is not None:
        fields.append("date=?")
        params.append(date)
    if record_type is not None:
        fields.append("type=?")
        params.append(record_type)
    if category is not None:
        fields.append("category=?")
        params.append(category)
    if amount is not None:
        fields.append("amount=?")
        params.append(amount)
    if note is not None:
        fields.append("description=?")
        params.append(note)
    if not fields:
        conn.close()
        return {"ok": False, "error": "没有要更新的字段"}
    params.append(record_id)
    cursor = conn.execute(f"UPDATE finance SET {','.join(fields)} WHERE id=?", params)
    updated = cursor.rowcount
    conn.commit()
    conn.close()
    if updated:
        try:
            log_action("system", "财务更新", "finance", f"更新记录 ID={record_id}")
        except Exception:
            pass
    return {"ok": updated > 0, "updated": updated}


def export_records(start_date: str = None, end_date: str = None) -> list[dict]:
    """导出财务记录（支持日期过滤）"""
    return get_records(start_date=start_date, end_date=end_date, limit=10000)


def import_records(rows: list[list], dry_run: bool = False) -> dict:
    """
    批量导入财务记录。
    rows: [[类型, 分类, 金额, 备注, 日期], ...]（第一行是表头则自动跳过）
    dry_run: True 则只验证不写入
    返回: {"ok": True, "imported": N, "skipped": M, "errors": [...]}
    """
    init_db()
    imported = 0
    skipped = 0
    errors = []
    for i, row in enumerate(rows):
        if not row or not str(row[0] if row[0] else "").strip():
            skipped += 1
            continue
        type_str = str(row[0]).strip() if row[0] else ""
        if type_str not in ["收入", "支出", "income", "expense"]:
            skipped += 1
            continue
        category = str(row[1]).strip() if len(row) > 1 and row[1] else "其他"
        try:
            amount = float(row[2]) if len(row) > 2 and row[2] else 0
        except (ValueError, TypeError):
            errors.append(f"行{i+1}: 金额格式错误 → {row}")
            skipped += 1
            continue
        note = str(row[3]).strip() if len(row) > 3 and row[3] else ""
        date = str(row[4]).strip() if len(row) > 4 and row[4] else datetime.now().strftime("%Y-%m-%d")
        type_val = "income" if type_str in ["收入", "income"] else "expense"
        if dry_run:
            imported += 1
            continue
        result = add_record(date=date, record_type=type_val,
                            category=category, amount=amount,
                            description=note)
        if result["ok"]:
            imported += 1
        else:
            errors.append(f"行{i+1}: 写入失败 → {result.get('error')}")
    return {"ok": True, "imported": imported, "skipped": skipped, "errors": errors}



# ── 自动同步到云端 ──
def _sync_to_cloud(action: str, payload: dict) -> dict:
    """同步财务记录到云端"""
    try:
        from core.supabase_client import CloudFinance
        if action == "upsert":
            ok, msg = CloudFinance.create(
                date=payload.get("date", ""),
                type_=payload.get("type", ""),
                category=payload.get("category", ""),
                amount=payload.get("amount", 0),
                note=payload.get("description", ""),
            )
            return {"ok": ok, "msg": msg}
        return {"ok": False, "msg": "未知操作"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}
