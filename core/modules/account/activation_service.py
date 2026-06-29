# -*- coding: utf-8 -*-
from __future__ import annotations
"""
激活码管理 — Service 层
所有数据库操作集中在此，UI 层只负责展示和交互。

数据库: DATA_DIR/activation_admin.db
表: admin_codes (管理员台账), admin_users (管理员账号)
"""

from core.database import get_conn
import secrets
from datetime import datetime, timedelta
from core.paths import DATA_DIR


# 用户激活库（本地定义，原来自 license_service）
import os as _os
from core.paths import DATA_DIR

DB_FILE = _os.path.join(DATA_DIR, "activation.db")

def _normalize(code: str) -> str:
    return code.upper().replace("-", "").replace(" ", "")

CODE_TYPES = {
    "TRIAL": {"name": "体验会员",  "days": 7,   "price": 0,  "features": ["basic"]},
    "PRO":   {"name": "VIP会员",  "days": 365, "price": 49, "features": ["basic"]},
    "VIP":   {"name": "钻石会员",  "days": 0,   "price": 99, "features": ["basic", "quant", "cloud"]},
}

def init_activation_db():
    """初始化用户激活码数据库"""
    _os.makedirs(_os.path.dirname(DB_FILE), exist_ok=True)
    conn = get_conn("activation.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS activation_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL,
            status TEXT DEFAULT 'unused',
            bound_account TEXT,
            bound_machine TEXT,
            created_at TEXT,
            used_at TEXT,
            expires_at TEXT,
            _sig TEXT
        )
    """)
    conn.commit()


def _connect():
    """连接管理员数据库（统一连接管理器）"""
    return get_conn("activation_admin.db")


# ──────────────────────────────────────────
#  数据库初始化
# ──────────────────────────────────────────

def init_admin_db():
    """初始化管理员激活码数据库（admin_codes + admin_users）"""
    conn = _connect()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS admin_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            user_type TEXT DEFAULT 'month',
            status TEXT DEFAULT 'unused',
            note TEXT DEFAULT '',
            bound_account TEXT DEFAULT '',
            bound_machine TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used_at TIMESTAMP,
            used_by TEXT,
            expires_at TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'admin'
        )
    ''')
    conn.commit()

# ──────────────────────────────────────────
#  激活码 CRUD
# ──────────────────────────────────────────

def generate_codes(count: int, user_type: str, note: str = "") -> list[dict]:
    """批量生成激活码，同时写入管理员库和用户激活库
    返回: [{"code": ..., "user_type": ..., "expires_at": ...}, ...]
    """
    info = CODE_TYPES.get(user_type)
    if not info:
        raise ValueError(f"未知激活码类型: {user_type}")
    days = info["days"]
    results = []
    conn = _connect()
    # 用户激活库
    init_activation_db()
    user_conn = get_conn("license.db")
    for _ in range(count):
        raw = secrets.token_hex(6)
        code = f"{user_type}-{raw[:4].upper()}-{raw[4:8].upper()}-{raw[8:12].upper()}"
        expires_at = None if days == 0 else (
            datetime.now() + timedelta(days=days)
        ).strftime("%Y-%m-%d %H:%M")
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        try:
            conn.execute(
                "INSERT OR IGNORE INTO admin_codes (code, user_type, status, note, created_at, expires_at) "
                "VALUES (?, ?, 'unused', ?, ?, ?)",
                (code, user_type, note, now, expires_at)
            )
            user_conn.execute(
                "INSERT OR REPLACE INTO activation_codes (code, type, status, created_at, expires_at) "
                "VALUES (?, ?, 'unused', ?, ?)",
                (code, user_type, now, expires_at)
            )
            results.append({"code": code, "user_type": user_type, "expires_at": expires_at})
        except Exception as e:
            print(f"生成码失败: {code} - {e}")
    conn.commit()

    user_conn.commit()

    return results


def get_codes(keyword: str = "", status_filter: str = None) -> tuple[list[dict], dict]:
    """获取激活码列表 + 状态统计
    返回: (codes_list, stats_dict)
    """
    conn = _connect()
    sql = ("SELECT id, code, user_type, status, bound_account, bound_machine, "
           "created_at, expires_at, note FROM admin_codes WHERE 1=1")
    params = []
    if keyword:
        sql += " AND (code LIKE ? OR bound_account LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if status_filter == "未使用":
        sql += " AND status='unused'"
    elif status_filter == "已激活":
        sql += " AND status='used'"
    elif status_filter == "已过期":
        sql += " AND status='expired'"
    sql += " ORDER BY id DESC"
    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    # 统计
    stats = {}
    for r in conn.execute("SELECT status, COUNT(*) as cnt FROM admin_codes GROUP BY status").fetchall():
        stats[r["status"]] = r["cnt"]

    return rows, stats


def get_code_by_raw(raw_code: str) -> dict | None:
    """按原始激活码（带连字符或不带）查询"""
    code_clean = raw_code.replace("-", "")
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM admin_codes WHERE code=? OR code=?",
        (raw_code, code_clean)
    ).fetchone()

    return dict(row) if row else None


def update_code_status(code: str, status: str = None, bound_account: str = None,
                       bound_machine: str = None) -> dict:
    """更新激活码状态/绑定信息
    code 支持原始格式(含-) 或 纯码格式
    """
    code_clean = code.replace("-", "")
    conn = _connect()
    fields, vals = [], []
    if status:
        fields.append("status=?")
        vals.append(status)
    if bound_account is not None:
        fields.append("bound_account=?")
        vals.append(bound_account)
    if bound_machine is not None:
        fields.append("bound_machine=?")
        vals.append(bound_machine)
    if not fields:

        return {"ok": False, "error": "没有需要更新的字段"}
    vals.extend([code, code_clean])
    conn.execute(
        f"UPDATE admin_codes SET {', '.join(fields)} WHERE code=? OR code=?",
        vals
    )
    conn.commit()
    # 同步更新用户激活库
    try:
        user_conn = get_conn("license.db")
        u_fields, u_vals = [], []
        if bound_account is not None:
            u_fields.append("bound_account=?")
            u_vals.append(bound_account)
        if bound_machine is not None:
            u_fields.append("bound_machine=?")
            u_vals.append(bound_machine)
        if u_fields:
            u_vals.append(_normalize(code))
            user_conn.execute(
                f"UPDATE activation_codes SET {', '.join(u_fields)} WHERE code=?",
                u_vals
            )
            user_conn.commit()

    except Exception as e:
        print(f"同步用户激活库失败: {e}")

    return {"ok": True}


def bind_account(code: str, account: str) -> dict:
    """绑定激活码到指定账号"""
    return update_code_status(code, bound_account=account)


def unbind_account(code: str) -> dict:
    """清空激活码账号绑定"""
    return update_code_status(code, bound_account="")


def mark_used(code: str, username: str, machine_code: str = "") -> dict:
    """标记激活码为已使用"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    code_clean = code.replace("-", "")
    conn = _connect()
    conn.execute(
        "UPDATE admin_codes SET status='used', bound_account=?, bound_machine=?, used_at=? WHERE code=? OR code=?",
        (username, machine_code, now, code, code_clean)
    )
    conn.commit()

    # 同步用户库
    try:
        user_conn = get_conn("license.db")
        user_conn.execute(
            "UPDATE activation_codes SET status='used', bound_account=?, bound_machine=? WHERE code=?",
            (username, machine_code, _normalize(code))
        )
        user_conn.commit()

    except Exception as e:
        print(f"同步用户库失败: {e}")
    return {"ok": True}


def unbind_machine(code: str) -> dict:
    """解绑设备"""
    code_clean = code.replace("-", "")
    conn = _connect()
    conn.execute(
        "UPDATE admin_codes SET bound_machine='' WHERE code=? OR code=?",
        (code, code_clean)
    )
    conn.commit()

    # 同步用户库
    try:
        user_conn = get_conn("license.db")
        user_conn.execute(
            "UPDATE activation_codes SET bound_machine='' WHERE code=?",
            (_normalize(code),)
        )
        user_conn.commit()

    except Exception as e:
        print(f"同步用户库失败: {e}")
    # 云端解绑
    try:
        from core.supabase_client import CloudActivation
        CloudActivation.unbind_device(code)
    except Exception as e:
        print(f"云端解绑失败: {e}")
    return {"ok": True}


def delete_codes(ids: list[int]) -> dict:
    """批量删除激活码"""
    conn = _connect()
    for cid in ids:
        conn.execute("DELETE FROM admin_codes WHERE id=?", (cid,))
    conn.commit()

    return {"ok": True, "deleted": len(ids)}


def get_unused_codes() -> list[dict]:
    """获取未使用的激活码（用于导出）"""
    conn = _connect()
    rows = conn.execute(
        "SELECT code, user_type, created_at FROM admin_codes WHERE status='unused' ORDER BY id DESC"
    ).fetchall()

    return [dict(r) for r in rows]


def get_all_codes_raw() -> list[dict]:
    """获取所有激活码原始数据（用于云端同步）"""
    conn = _connect()
    rows = conn.execute(
        "SELECT code, user_type, status, bound_account, bound_machine, created_at, expires_at "
        "FROM admin_codes"
    ).fetchall()

    return [dict(r) for r in rows]


# ──────────────────────────────────────────
#  管理员账号
# ──────────────────────────────────────────

def reset_admin_password(password_hash: str) -> dict:
    """重置管理员密码"""
    conn = _connect()
    conn.execute("DELETE FROM admin_users")
    conn.execute(
        "INSERT INTO admin_users (username, password, role) VALUES (?, ?, ?)",
        ("admin", password_hash, "superadmin")
    )
    conn.commit()

    return {"ok": True}