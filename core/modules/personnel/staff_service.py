# -*- coding: utf-8 -*-
from __future__ import annotations
"""
人员管理 — Service 层
"""
import os
from datetime import datetime
from core.database import get_conn

# GBK/UTF-8 混合编码解码器（兼容历史数据）
def _decode(b):
    if isinstance(b, str):
        return b
    try:
        r = b.decode('utf-8')
        if '\ufffd' in r:
            try:
                return b.decode('gbk')
            except UnicodeDecodeError:
                return r
        return r
    except UnicodeDecodeError:
        try:
            return b.decode('gbk')
        except UnicodeDecodeError:
            return b.decode('utf-8', errors='ignore')


def _get_conn():
    conn = get_conn("staff.db")
    conn.text_factory = _decode
    return conn


def init_db():
    conn = _get_conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, phone TEXT, email TEXT,
        position TEXT, salary REAL DEFAULT 0,
        status TEXT DEFAULT '在职', note TEXT,
        department TEXT DEFAULT '', hire_date TEXT DEFAULT '',
        created_at TEXT DEFAULT '', updated_at TEXT DEFAULT '',
        sync_version INTEGER DEFAULT 0,
        last_modified_by TEXT DEFAULT 'desktop',
        last_sync_at TIMESTAMP
    )""")
    # 兼容列
    existing = [r[1] for r in conn.execute("PRAGMA table_info('staff')").fetchall()]
    for col, coltype in [
        ('department', 'TEXT DEFAULT ""'),
        ('hire_date', 'TEXT DEFAULT ""'),
        ('created_at', 'TEXT DEFAULT ""'),
        ('updated_at', 'TEXT DEFAULT ""'),
    ]:
        if col not in existing:
            try:
                conn.execute(f"ALTER TABLE staff ADD COLUMN {col} {coltype}")
            except Exception:
                pass
    conn.commit()


def add_staff(name: str, phone: str = "", email: str = "",
              position: str = "", salary: float = 0,
              status: str = "在职") -> int:
    conn = _get_conn()
    c = conn.execute(
        "INSERT INTO staff (name, phone, email, position, salary, status, department, hire_date) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (name, phone, email, position, salary, status, "",
         datetime.now().strftime("%Y-%m-%d"))
    )
    conn.commit()
    return c.lastrowid


def get_staff(keyword: str = "") -> list[dict]:
    conn = _get_conn()
    if keyword:
        rows = conn.execute(
            "SELECT id, name, phone, email, position, salary, status "
            "FROM staff WHERE name LIKE ? OR position LIKE ? ORDER BY id DESC",
            (f"%{keyword}%", f"%{keyword}%")
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, name, phone, email, position, salary, status "
            "FROM staff ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_staff_by_id(sid: int) -> dict | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT id, name, phone, email, position, salary, status FROM staff WHERE id=?",
        (sid,)
    ).fetchone()
    return dict(row) if row else None


def update_staff(sid: int, name: str, phone: str = "", email: str = "",
                 position: str = "", salary: float = 0, status: str = "在职"):
    conn = _get_conn()
    conn.execute(
        "UPDATE staff SET name=?, phone=?, email=?, position=?, salary=?, status=? WHERE id=?",
        (name, phone, email, position, salary, status, sid)
    )
    conn.commit()


def delete_staff(sid: int):
    conn = _get_conn()
    conn.execute("DELETE FROM staff WHERE id=?", (sid,))
    conn.commit()


def get_all_staff() -> list[dict]:
    """导出用：全量查询"""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, name, phone, email, position, salary, status FROM staff ORDER BY id"
    ).fetchall()
    return [dict(r) for r in rows]


def import_staff_csv(path: str) -> int:
    """导入CSV批量人员，返回导入条数"""
    import csv
    count = 0
    conn = _get_conn()
    with open(path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('姓名', row.get('name', '')).strip()
            if not name:
                continue
            phone = row.get('电话', row.get('phone', '')).strip()
            email = row.get('邮箱', row.get('email', '')).strip()
            position = row.get('职位', row.get('position', '')).strip()
            try:
                salary = float(row.get('薪资', row.get('salary', '0')).strip() or 0)
            except ValueError:
                salary = 0
            status = row.get('状态', row.get('status', '在职')).strip() or '在职'
            department = row.get('部门', row.get('department', '')).strip()
            hire_date = row.get('入职日期', row.get('hire_date',
                              datetime.now().strftime("%Y-%m-%d"))).strip()
            conn.execute(
                "INSERT INTO staff (name, phone, email, position, salary, status, department, hire_date) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (name, phone, email, position, salary, status, department, hire_date)
            )
            count += 1
    conn.commit()
    return count


def import_staff_validated(path: str):
    """带校验的批量导入，返回 (valid_rows, errors)"""
    import csv
    errors = []
    valid_rows = []
    valid_statuses = ["在职", "离职", "休假"]

    with open(path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows_data = list(reader)

    for idx, row in enumerate(rows_data):
        line = idx + 2
        name = row.get("姓名", "").strip()
        phone = row.get("电话", "").strip()
        email = row.get("邮箱", "").strip()
        position = row.get("职位", "").strip()
        salary_str = row.get("薪资", "0").strip()
        status = row.get("状态", "在职").strip()

        if not name:
            errors.append(f"第{line}行: 姓名为空")
            continue
        try:
            salary = float(salary_str) if salary_str else 0
        except ValueError:
            errors.append(f"第{line}行: 薪资 '{salary_str}' 不是数字")
            continue
        if status not in valid_statuses:
            errors.append(f"第{line}行: 状态 '{status}' 非法")
            continue
        valid_rows.append((name, phone, email, position, salary, status))

    return valid_rows, errors


def batch_insert_staff(rows_data: list):
    """批量插入已验证的行"""
    conn = _get_conn()
    for name, phone, email, position, salary, status in rows_data:
        conn.execute(
            "INSERT INTO staff (name, phone, email, position, salary, status, department, hire_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, phone, email, position, salary, status, "",
             datetime.now().strftime("%Y-%m-%d"))
        )
    conn.commit()


# ── 云端同步 ──
def _sync_to_cloud(action: str, payload: dict) -> dict:
    """同步员工记录到云端"""
    try:
        # staff 表暂无 CloudStaff 类，使用通用方式
        from core.supabase_client import _request
        if action == "upsert":
            ok, result = _request(
                "POST",
                "/rest/v1/staff?on_conflict=id",
                payload,
                service_key=True,
                prefer="resolution=merge-duplicates",
            )
            return {"ok": ok, "msg": "已同步" if ok else str(result)}
        return {"ok": False, "msg": "未知操作"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}
