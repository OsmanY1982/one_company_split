# -*- coding: utf-8 -*-
"""
管理员后台 - 产品CRUD
由 admin 后台直接调用，操作本地 product.db 并触发云端同步
"""
import os, sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
from core.paths import DATA_DIR
from core.cloud_sync import sync_products

DB_FILE = os.path.join(DATA_DIR, "product.db")


def add_product(data: dict) -> dict:
    """新增产品"""
    try:
        import sqlite3
        conn = sqlite3.connect(DB_FILE)
        conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO products (name, category, price, cost, stock, unit, status, description,
               created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,datetime('now','localtime'),datetime('now','localtime'))""",
            (data.get("name", ""), data.get("category", ""),
             data.get("price", 0.0), data.get("cost", 0.0),
             data.get("stock", 0), data.get("unit", "个"),
             data.get("status", "在售"), data.get("description", ""))
        )
        conn.commit()
        conn.close()
        sync_products()
        return {"ok": True, "msg": "添加成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def update_product(product_id: int, data: dict) -> dict:
    """更新产品"""
    try:
        import sqlite3
        conn = sqlite3.connect(DB_FILE)
        conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
        cur = conn.cursor()
        sets = ", ".join([f"{k}=?" for k in data.keys()])
        vals = list(data.values()) + [product_id]
        cur.execute(f"UPDATE products SET {sets}, updated_at=datetime('now','localtime') WHERE id=?", vals)
        conn.commit()
        conn.close()
        sync_products()
        return {"ok": True, "msg": "更新成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def delete_product(product_id: int) -> dict:
    """删除产品"""
    try:
        import sqlite3
        conn = sqlite3.connect(DB_FILE)
        conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
        conn.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
        conn.close()
        sync_products()
        return {"ok": True, "msg": "删除成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}
