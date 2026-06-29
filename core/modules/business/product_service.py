# -*- coding: utf-8 -*-
"""
产品服务层
提供产品的增删改查、导入导出、库存管理、云端同步
"""
import csv
from datetime import datetime
from pathlib import Path
from core.paths import DATA_DIR
from core.database import get_conn
from core.operation_log import log_action

DB_FILE = Path(DATA_DIR) / "product.db"


def _get_conn():
    """获取数据库连接"""
    return get_conn("product.db")


def init_db():
    """初始化数据库表"""
    conn = _get_conn()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specs TEXT,
            category TEXT,
            unit_price REAL DEFAULT 0,
            price REAL DEFAULT 0,
            cost REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            unit TEXT,
            status TEXT DEFAULT '上架',
            note TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sync_version INTEGER DEFAULT 0,
            last_modified_by TEXT DEFAULT 'desktop',
            last_sync_at TIMESTAMP
        )
    ''')
    # 兼容已存在的 products 表：补充缺失列（cloud_pull 映射所需）
    for col, col_def in [
        ("price", "REAL DEFAULT 0"),
        ("cost", "REAL DEFAULT 0"),
        ("description", "TEXT"),
        ("unit", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE products ADD COLUMN {col} {col_def}")
        except Exception:
            pass
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)
    ''')
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)
    ''')
    conn.commit()
    conn.close()


def add_product(name: str, specs: str = "", category: str = "",
                unit_price: float = 0, stock: int = 0,
                status: str = "上架", note: str = "") -> dict:
    """创建产品"""
    if not name:
        return {"ok": False, "msg": "产品名称不能为空"}

    try:
        conn = _get_conn()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.execute(
            """INSERT INTO products 
               (name, specs, category, unit_price, stock, status, note, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, specs, category, unit_price, stock, status, note, now, now)
        )
        product_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # 云端同步
        _sync_to_cloud("upsert", {
            "id": product_id,
            "name": name,
            "specs": specs,
            "category": category,
            "unit_price": unit_price,
            "stock": stock,
            "status": status,
            "note": note,
            "created_at": now,
            "updated_at": now
        })

        try:
            log_action("system", "添加产品", "product", name)
        except Exception:
            pass

        return {"ok": True, "msg": "产品创建成功", "id": product_id}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def get_products(keyword: str = "", category: str = "", status: str = "",
                 limit: int = 1000) -> list:
    """查询产品列表"""
    conn = _get_conn()
    sql = """SELECT id, name, specs, category, unit_price, stock, status, note, created_at
             FROM products"""
    params = []
    conditions = []

    if keyword:
        conditions.append("(name LIKE ? OR category LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if category:
        conditions.append("category = ?")
        params.append(category)
    if status:
        conditions.append("status = ?")
        params.append(status)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_product_by_id(product_id: int) -> dict:
    """根据ID查询产品"""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_product(product_id: int, name: str = None, specs: str = None,
                   category: str = None, unit_price: float = None,
                   stock: int = None, status: str = None,
                   note: str = None) -> dict:
    """更新产品"""
    try:
        conn = _get_conn()
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if specs is not None:
            updates.append("specs = ?")
            params.append(specs)
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if unit_price is not None:
            updates.append("unit_price = ?")
            params.append(unit_price)
        if stock is not None:
            updates.append("stock = ?")
            params.append(stock)
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if note is not None:
            updates.append("note = ?")
            params.append(note)

        if not updates:
            return {"ok": False, "msg": "没有要更新的字段"}

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updates.append("updated_at = ?")
        params.append(now)
        params.append(product_id)

        sql = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
        conn.execute(sql, params)
        conn.commit()
        conn.close()

        # 云端同步
        _sync_to_cloud("upsert", {"id": product_id, "updated_at": now})

        try:
            log_action("system", "更新产品", "product", f"ID={product_id}, {name or ''}")
        except Exception:
            pass

        return {"ok": True, "msg": "产品更新成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def delete_product(product_id: int) -> dict:
    """删除产品"""
    try:
        conn = _get_conn()
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        conn.close()

        # 云端同步
        _sync_to_cloud("delete", {"id": product_id})

        try:
            log_action("system", "删除产品", "product", f"ID={product_id}")
        except Exception:
            pass

        return {"ok": True, "msg": "产品删除成功"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def update_stock(product_id: int, delta: int) -> dict:
    """更新库存（正数增加，负数减少）"""
    try:
        conn = _get_conn()
        conn.execute(
            "UPDATE products SET stock = stock + ?, updated_at = ? WHERE id = ?",
            (delta, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), product_id)
        )
        conn.commit()
        conn.close()
        return {"ok": True, "msg": f"库存更新成功 ({delta:+d})"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def get_product_stats() -> dict:
    """获取产品统计"""
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    total_stock = conn.execute("SELECT COALESCE(SUM(stock), 0) FROM products").fetchone()[0]
    total_value = conn.execute(
        "SELECT COALESCE(SUM(unit_price * stock), 0) FROM products"
    ).fetchone()[0]
    status_counts = conn.execute(
        "SELECT status, COUNT(*) as count FROM products GROUP BY status"
    ).fetchall()
    conn.close()

    return {
        "total": total,
        "total_stock": total_stock,
        "total_value": total_value,
        "by_status": {r[0]: r[1] for r in status_counts}
    }


def export_products() -> tuple:
    """导出所有产品 (headers, rows)"""
    conn = _get_conn()
    rows = conn.execute(
        """SELECT id, name, specs, category, unit_price, stock, status, note, created_at
           FROM products ORDER BY id DESC"""
    ).fetchall()
    conn.close()

    headers = ["ID", "名称", "规格", "分类", "单价", "库存", "状态", "备注", "创建时间"]
    return headers, rows


def import_products(data_list: list) -> dict:
    """批量导入产品"""
    try:
        conn = _get_conn()
        count = 0
        errors = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for idx, item in enumerate(data_list, 1):
            try:
                name = item.get("name", "").strip()
                if not name:
                    errors.append(f"第{idx}行: 产品名称不能为空")
                    continue

                specs = item.get("specs", "").strip()
                category = item.get("category", "").strip()
                unit_price = float(item.get("unit_price", 0) or 0)
                stock = int(item.get("stock", 0) or 0)
                status = item.get("status", "上架").strip() or "上架"
                note = item.get("note", "").strip()

                conn.execute(
                    """INSERT INTO products 
                       (name, specs, category, unit_price, stock, status, note, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (name, specs, category, unit_price, stock, status, note, now, now)
                )
                count += 1
            except Exception as e:
                errors.append(f"第{idx}行: {e}")

        conn.commit()
        conn.close()

        return {
            "ok": True,
            "msg": f"成功导入 {count} 条产品" + (f"，{len(errors)} 条失败" if errors else ""),
            "count": count,
            "errors": errors
        }
    except Exception as e:
        return {"ok": False, "msg": f"导入失败: {e}"}


# ══════════════════════════════════════════════════════
#  云端同步
# ══════════════════════════════════════════════════════

def _sync_to_cloud(action: str, payload: dict):
    """同步到云端（非阻塞）"""
    try:
        from core.supabase_client import CloudProduct
        if action == "upsert":
            CloudProduct.upsert(**payload)
        elif action == "delete":
            CloudProduct.delete(payload.get("id"))
    except Exception as e:
        print(f"[ProductService] 云端同步失败 (non-blocking): {e}")


if __name__ == "__main__":
    init_db()
    print("产品服务测试")
    stats = get_product_stats()
    print(f"产品统计: {stats}")
