# -*- coding: utf-8 -*-
from __future__ import annotations
"""
客户管理服务层（从 customer_window.py 提取的数据库逻辑）。
所有数据库操作委托给本模块，窗口文件只负责 UI 展示和交互。
"""
import os
import csv
from datetime import datetime
from core.paths import DATA_DIR
from core.database import get_conn
from core.operation_log import log_action

DB_FILE = os.path.join(DATA_DIR, "customer.db")


def _connect():
    return get_conn("customer.db")


def init_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = _connect()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS customer (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    NOT NULL,
            company      TEXT,
            phone        TEXT,
            email        TEXT,
            address      TEXT,
            level        TEXT    DEFAULT '普通',
            note         TEXT,
            created_at   TEXT    NOT NULL,
            sync_version INTEGER DEFAULT 0,
            last_modified_by TEXT DEFAULT 'desktop',
            last_sync_at TIMESTAMP
        )"""
    )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
#  CRUD
# ─────────────────────────────────────────────

def add_customer(name: str,
                 company: str = "",
                 phone: str = "",
                 email: str = "",
                 address: str = "",
                 level: str = "普通",
                 note: str = "") -> dict:
    """添加客户（返回 {"ok": True} 或 {"ok": False, "error": ...}）"""
    init_db()
    if not name.strip():
        return {"ok": False, "error": "客户名称不能为空"}
    conn = _connect()
    try:
        conn.execute(
            """INSERT INTO customer
               (name, company, phone, email, address, level, note, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name.strip(), company.strip(), phone.strip(), email.strip(),
             address.strip(), level, note.strip(),
             datetime.now().strftime("%Y-%m-%d"))
        )
        conn.commit()

        # 同步到云端
        try:
            from core.supabase_client import CloudCustomer
            CloudCustomer.upsert(
                name=name.strip(), phone=phone.strip(), email=email.strip(),
                address=address.strip(), company=company.strip(),
                level=level, note=note.strip()
            )
        except Exception:
            pass

        try:
            log_action("system", "添加客户", "customer", name.strip())
        except Exception:
            pass

        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def get_customers(keyword: str = "") -> list[dict]:
    """获取客户列表（支持名称/公司关键字搜索）"""
    init_db()
    conn = _connect()
    if keyword:
        rows = conn.execute(
            """SELECT id,name,company,phone,email,address,level,note,created_at
               FROM customer
               WHERE name LIKE ? OR company LIKE ?
               ORDER BY id DESC""",
            (f"%{keyword}%", f"%{keyword}%")
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id,name,company,phone,email,address,level,note,created_at "
            "FROM customer ORDER BY id DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_customer_by_id(customer_id: int) -> dict | None:
    """根据 ID 获取单个客户"""
    init_db()
    conn = _connect()
    row = conn.execute(
        "SELECT id,name,company,phone,email,address,level,note,created_at "
        "FROM customer WHERE id=?",
        (customer_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_customer(customer_id: int,
                    name: str,
                    company: str = "",
                    phone: str = "",
                    email: str = "",
                    address: str = "",
                    level: str = "普通",
                    note: str = "") -> dict:
    """更新客户信息"""
    init_db()
    if not name.strip():
        return {"ok": False, "error": "客户名称不能为空"}
    conn = _connect()
    try:
        conn.execute(
            """UPDATE customer
               SET name=?,company=?,phone=?,email=?,address=?,level=?,note=?
               WHERE id=?""",
            (name.strip(), company.strip(), phone.strip(), email.strip(),
             address.strip(), level, note.strip(), customer_id)
        )
        conn.commit()
        try:
            log_action("system", "更新客户", "customer", f"ID={customer_id}, {name.strip()}")
        except Exception:
            pass
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def delete_customer(customer_id: int) -> dict:
    """删除客户"""
    init_db()
    conn = _connect()
    try:
        conn.execute("DELETE FROM customer WHERE id=?", (customer_id,))
        conn.commit()
        try:
            log_action("system", "删除客户", "customer", f"ID={customer_id}")
        except Exception:
            pass
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        conn.close()


def get_customer_count() -> int:
    """获取客户总数"""
    init_db()
    conn = _connect()
    row = conn.execute("SELECT COUNT(*) as cnt FROM customer").fetchone()
    conn.close()
    return row["cnt"] if row else 0


# ─────────────────────────────────────────────
#  导入 / 导出
# ─────────────────────────────────────────────

def import_csv(file_path: str) -> dict:
    """
    从 CSV 文件批量导入客户。
    支持列名：名称/name, 公司/company, 电话/phone, 邮箱/email,
              地址/address, 等级/level, 备注/note
    返回 {"ok": True, "count": N} 或 {"ok": False, "error": ...}
    """
    init_db()
    if not os.path.exists(file_path):
        return {"ok": False, "error": f"文件不存在: {file_path}"}
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            conn = _connect()
            count = 0
            for row in reader:
                name = row.get("名称", row.get("name", "")).strip()
                if not name:
                    continue
                company = row.get("公司", row.get("company", "")).strip()
                phone = row.get("电话", row.get("phone", "")).strip()
                email = row.get("邮箱", row.get("email", "")).strip()
                address = row.get("地址", row.get("address", "")).strip()
                level = row.get("等级", row.get("level", "普通")).strip() or "普通"
                note = row.get("备注", row.get("note", "")).strip()
                conn.execute(
                    """INSERT INTO customer
                       (name,company,phone,email,address,level,note,created_at)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (name, company, phone, email, address, level, note,
                     datetime.now().strftime("%Y-%m-%d"))
                )
                count += 1
            conn.commit()
            conn.close()
        return {"ok": True, "count": count}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def export_customers() -> list[dict]:
    """导出所有客户数据（返回列表，供外部写入 Excel）"""
    init_db()
    conn = _connect()
    rows = conn.execute(
        "SELECT id,name,company,phone,email,address,level,note,created_at "
        "FROM customer ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
