# -*- coding: utf-8 -*-
"""激活码数据库操作"""
import os
from core.database import get_conn
from datetime import datetime

from core.paths import DATA_DIR

DB_FILE   = os.path.join(DATA_DIR, "activation.db")
ADMIN_DB  = os.path.join(DATA_DIR, "activation_admin.db")
LOG_FILE  = os.path.join(DATA_DIR, "activation_log.db")


def init_activation_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
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


def init_admin_db():
    os.makedirs(os.path.dirname(ADMIN_DB), exist_ok=True)
    conn = get_conn("activation_admin.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS admin_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            user_type TEXT DEFAULT 'month',
            status TEXT DEFAULT 'unused',
            bound_account TEXT,
            bound_machine TEXT,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used_at TIMESTAMP,
            expires_at TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def _init_log_db():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    conn = get_conn("activation_log.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS activation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT,
            machine_code TEXT,
            code TEXT,
            code_type TEXT,
            action TEXT,
            result TEXT,
            detail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def _write_log(account, machine_code, code, code_type, action, result, detail=""):
    try:
        _init_log_db()
        conn = get_conn("activation_log.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO activation_log (account, machine_code, code, code_type, action, result, detail, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (account, machine_code, code, code_type, action, result, detail, datetime.now().isoformat())
        )
        conn.commit()
    except Exception as e:
        print(f"[log] write failed: {e}")
