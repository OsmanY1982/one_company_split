# -*- coding: utf-8 -*-
"""
管理员后台 - 财务CRUD
由 admin 后台直接调用，操作本地 finance.db 并触发云端同步
与 src/core/finance_service.py 的 CRUD 功能一致，但走 sync_finance（增量同步）而非实时 push
"""

import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
from core.paths import DATA_DIR
from core.cloud_sync import sync_finance

DB_FILE = os.path.join(DATA_DIR, "finance.db")


def add_finance(data: dict) -> dict:
    """
    新增财务记录
    data: {type, category, amount, date, description, order_no}
    """
    try:
        import sqlite3
        conn = sqlite3.connect(DB_FILE)
        conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO finance (type, category, amount, date, description, order_no, created_at, updated_at)
               VALUES (?,?,?,?,?,?,datetime('now','localtime'),datetime('now','localtime'))""",
            (data.get("type", "支出"), data.get("category", ""),
             data.get("amount", 0), data.get("date", ""),
             data.get("description", ""), data.get("order_no", ""))
        )
        conn.commit()
        conn.close()
        # 触发云端同步
        sync_finance()
        return {"ok": True, "msg": "添加成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def update_finance(finance_id: int, data: dict) -> dict:
    """更新财务记录，自动触发同步"""
    try:
        import sqlite3
        conn = sqlite3.connect(DB_FILE)
        conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
        cur = conn.cursor()
        sets = ", ".join([f"{k}=?" for k in data.keys()])
        vals = list(data.values()) + [finance_id]
        cur.execute(
            f"UPDATE finance SET {sets}, updated_at=datetime('now','localtime') WHERE id=?",
            vals
        )
        conn.commit()
        conn.close()
        sync_finance()
        return {"ok": True, "msg": "更新成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def delete_finance(finance_id: int) -> dict:
    """删除财务记录，自动触发同步"""
    try:
        import sqlite3
        conn = sqlite3.connect(DB_FILE)
        conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
        conn.execute("DELETE FROM finance WHERE id=?", (finance_id,))
        conn.commit()
        conn.close()
        sync_finance()
        return {"ok": True, "msg": "删除成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}
