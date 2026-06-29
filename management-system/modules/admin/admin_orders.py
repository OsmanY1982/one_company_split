# -*- coding: utf-8 -*-
"""
管理员后台 - 订单CRUD
由 admin 后台直接调用，操作本地 order.db 并触发云端同步
"""
import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
from core.paths import DATA_DIR
from core.cloud_sync import sync_orders

DB_FILE = os.path.join(DATA_DIR, "order.db")


def add_order(data: dict) -> dict:
    """新增订单"""
    try:
        import sqlite3
        conn = sqlite3.connect(DB_FILE)
        conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO orders (order_no, customer_name, product_name, quantity, unit_price,
               total_amount, status, payment_method, note, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,datetime('now','localtime'),datetime('now','localtime'))""",
            (data.get("order_no", ""), data.get("customer_name", ""),
             data.get("product_name", ""), data.get("quantity", 1),
             data.get("unit_price", 0.0), data.get("total_amount", 0.0),
             data.get("status", "待处理"), data.get("payment_method", ""),
             data.get("note", ""))
        )
        conn.commit()
        conn.close()
        sync_orders()
        return {"ok": True, "msg": "添加成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def update_order(order_id: int, data: dict) -> dict:
    """更新订单"""
    try:
        import sqlite3
        conn = sqlite3.connect(DB_FILE)
        conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
        cur = conn.cursor()
        sets = ", ".join([f"{k}=?" for k in data.keys()])
        vals = list(data.values()) + [order_id]
        cur.execute(f"UPDATE orders SET {sets}, updated_at=datetime('now','localtime') WHERE id=?", vals)
        conn.commit()
        conn.close()
        sync_orders()
        return {"ok": True, "msg": "更新成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def delete_order(order_id: int) -> dict:
    """删除订单"""
    try:
        import sqlite3
        conn = sqlite3.connect(DB_FILE)
        conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
        conn.execute("DELETE FROM orders WHERE id=?", (order_id,))
        conn.commit()
        conn.close()
        sync_orders()
        return {"ok": True, "msg": "删除成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}
