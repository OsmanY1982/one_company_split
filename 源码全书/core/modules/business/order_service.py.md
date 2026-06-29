# `core/modules/business/order_service.py`

> 路径：`core/modules/business/order_service.py` | 行数：287


---


```python
# -*- coding: utf-8 -*-
"""
订单服务层
提供订单的增删改查、导入导出、云端同步
"""
import csv
import io
from datetime import datetime
from pathlib import Path
from core.paths import DATA_DIR
from core.database import get_conn
from core.operation_log import log_action

DB_FILE = Path(DATA_DIR) / "order.db"


def _get_conn():
    return get_conn("order.db")


def init_db():
    conn = _get_conn()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT UNIQUE NOT NULL,
            customer_name TEXT,
            product_name TEXT,
            quantity INTEGER DEFAULT 1,
            unit_price REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            status TEXT DEFAULT '已完成',
            note TEXT,
            payment_method TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)
    ''')
    conn.commit()
    conn.close()


def add_order(order_no: str, customer_name: str = "", product_name: str = "",
              total_amount: float = 0, quantity: int = 1, unit_price: float = 0,
              status: str = "已完成", note: str = "", payment_method: str = "") -> dict:
    try:
        conn = _get_conn()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            """INSERT INTO orders
               (order_no, customer_name, product_name, quantity, unit_price,
                total_amount, status, note, payment_method, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_no, customer_name, product_name, quantity, unit_price,
             total_amount, status, note, payment_method, now)
        )

        # 扣减库存
        stock_msg = ""
        if product_name and status != "已取消":
            try:
                from core.modules.business import product_service as ps
                products = ps.get_products(keyword=product_name)
                if products:
                    pid = products[0]["id"]
                    current_stock = products[0].get("stock", 0)
                    if current_stock >= quantity:
                        result = ps.update_stock(pid, -int(quantity))
                        if result.get("ok"):
                            stock_msg = f"，已扣减 [{products[0]['name']}] 库存 {quantity}"
                    else:
                        stock_msg = f"（库存不足，当前: {current_stock}，需要: {quantity}）"
            except Exception as e:
                stock_msg = f"（库存扣减失败: {e}）"

        conn.commit()
        conn.close()
        msg = f"订单 {order_no} 创建成功{stock_msg}"
        try:
            log_action("system", "创建订单", "order",
                       f"{order_no}: {customer_name}, {product_name}, {total_amount}")
        except Exception:
            pass
        return {"ok": True, "msg": msg}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def get_orders(keyword: str = "", status: str = "全部", limit: int = 500) -> list:
    try:
        conn = _get_conn()
        conn.row_factory = lambda c, r: dict(
            zip([col[0] for col in c.description], r))

        sql = "SELECT * FROM orders WHERE 1=1"
        params = []

        if keyword:
            sql += (" AND (order_no LIKE ? OR customer_name LIKE ? "
                    "OR product_name LIKE ?)")
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw])

        if status and status != "全部":
            sql += " AND status = ?"
            params.append(status)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"[order_service] get_orders error: {e}")
        return []


def update_order(order_id: int, **kwargs) -> dict:
    try:
        conn = _get_conn()
        valid_fields = ["customer_name", "product_name", "quantity",
                        "unit_price", "total_amount", "status", "note",
                        "payment_method"]
        sets = []
        params = []
        for k, v in kwargs.items():
            if k in valid_fields:
                sets.append(f"{k} = ?")
                params.append(v)
        if not sets:
            return {"ok": False, "msg": "无有效字段"}
        params.append(order_id)
        conn.execute(f"UPDATE orders SET {', '.join(sets)} WHERE id = ?", params)
        conn.commit()
        conn.close()
        try:
            log_action("system", "更新订单", "order", f"订单 ID={order_id}")
        except Exception:
            pass
        return {"ok": True, "msg": "更新成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def delete_order(order_id: int) -> dict:
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        try:
            log_action("system", "删除订单", "order", f"订单 ID={order_id}")
        except Exception:
            pass
        return {"ok": True, "msg": "删除成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def get_order_stats() -> dict:
    try:
        conn = _get_conn()
        total = conn.execute("SELECT COUNT(*), COALESCE(SUM(total_amount),0) FROM orders").fetchone()
        pending = conn.execute("SELECT COUNT(*) FROM orders WHERE status='待处理'").fetchone()[0]
        completed = conn.execute("SELECT COUNT(*) FROM orders WHERE status='已完成'").fetchone()[0]
        conn.close()
        return {
            "total_count": total[0],
            "total_amount": total[1],
            "pending": pending,
            "completed": completed,
        }
    except Exception as e:
        return {"total_count": 0, "total_amount": 0, "pending": 0, "completed": 0}


def export_csv(filepath: str) -> dict:
    try:
        rows = get_orders(limit=99999)
        if not rows:
            return {"ok": False, "msg": "无数据可导出"}
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return {"ok": True, "msg": f"已导出 {len(rows)} 条到 {filepath}"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def import_csv(filepath: str) -> dict:
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                result = add_order(
                    order_no=row.get("order_no", datetime.now().strftime("%Y%m%d%H%M%S")),
                    customer_name=row.get("customer_name", ""),
                    product_name=row.get("product_name", ""),
                    total_amount=float(row.get("total_amount", 0)),
                    quantity=int(row.get("quantity", 1)),
                    status=row.get("status", "已完成"),
                    note=row.get("note", ""),
                    payment_method=row.get("payment_method", ""),
                )
                if result["ok"]:
                    count += 1
        return {"ok": True, "msg": f"成功导入 {count} 条订单"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}

def get_order_by_no(order_no: str) -> dict:
    """按订单号查找"""
    try:
        conn = _get_conn()
        conn.row_factory = lambda c, r: dict(
            zip([col[0] for col in c.description], r))
        row = conn.execute(
            "SELECT * FROM orders WHERE order_no = ?", (order_no,)).fetchone()
        conn.close()
        return row or {}
    except Exception as e:
        print(f"[order_service] get_order_by_no error: {e}")
        return {}


def _delete_order(order_no: str) -> dict:
    """按订单号删除"""
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM orders WHERE order_no = ?", (order_no,))
        conn.commit()
        conn.close()
        return {"ok": True, "msg": "删除成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def _update_order(order_no: str, **kwargs) -> dict:
    """按订单号更新"""
    try:
        conn = _get_conn()
        valid_fields = ["customer_name", "product_name", "quantity",
                        "unit_price", "total_amount", "status", "note",
                        "payment_method"]
        sets = []
        params = []
        for k, v in kwargs.items():
            if k in valid_fields:
                sets.append(f"{k} = ?")
                params.append(v)
        if not sets:
            return {"ok": False, "msg": "无有效字段"}
        params.append(order_no)
        conn.execute(
            f"UPDATE orders SET {', '.join(sets)} WHERE order_no = ?", params)
        conn.commit()
        conn.close()
        return {"ok": True, "msg": "更新成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def export_orders() -> tuple:
    """导出订单为 (表头列表, 数据行列表) 格式"""
    try:
        rows = get_orders(limit=99999)
        if not rows:
            return ([], [])
        headers = ["order_no", "customer_name", "product_name",
                   "total_amount", "quantity", "status", "created_at", "note"]
        data = []
        for r in rows:
            data.append([r.get(h, "") for h in headers])
        return (headers, data)
    except Exception as e:
        return ([], [])


def import_orders(filepath: str) -> dict:
    """从CSV导入订单"""
    return import_csv(filepath)

```
