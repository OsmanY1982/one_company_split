# -*- coding: utf-8 -*-

import os
import traceback
from datetime import datetime
from core.paths import DATA_DIR
from core.database import get_conn, close_conn, execute, query_rows, query_one

LOG_DB = os.path.join(DATA_DIR, "operation_log.db")
AUDIT_DB = os.path.join(DATA_DIR, "audit.db")
SYNC_LOG_DB = os.path.join(DATA_DIR, "sync_log.db")
ADMIN_DB = os.path.join(DATA_DIR, "admin.db")

def _ensure_db():
    os.makedirs(os.path.dirname(LOG_DB), exist_ok=True)
    conn = get_conn('operation_log')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            module TEXT,
            detail TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

_ensure_db()


def _ensure_audit_db():
    """确保 audit.db 的 audit_logs 表存在（如果 AuditService 尚未初始化）"""
    conn = get_conn('audit')
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT NOT NULL,
            user_name TEXT,
            action TEXT NOT NULL,
            level TEXT DEFAULT 'INFO',
            resource_type TEXT NOT NULL DEFAULT '',
            resource_id TEXT,
            resource_name TEXT,
            old_values TEXT,
            new_values TEXT,
            changes TEXT,
            ip_address TEXT,
            user_agent TEXT,
            session_id TEXT,
            status TEXT DEFAULT 'SUCCESS',
            error_message TEXT,
            duration_ms INTEGER,
            checksum TEXT,
            metadata TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_logs(timestamp)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)")
    conn.commit()


def _ensure_error_db():
    """确保 sync_log.db 的 error_logs 表存在"""
    conn = get_conn('sync_log')
    conn.execute("""
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module TEXT DEFAULT '',
            error_type TEXT DEFAULT '',
            message TEXT NOT NULL,
            traceback TEXT DEFAULT '',
            resolved INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def log_action(username: str, action: str, module: str = "", detail: str = ""):
    """记录操作日志，同时写入 operation_log.db + audit.db"""
    try:
        conn = get_conn('operation_log')
        conn.execute(
            "INSERT INTO operation_logs (username, action, module, detail) VALUES (?, ?, ?, ?)",
            (username, action, module, detail)
        )
        conn.commit()
    except Exception as e:
        _write_error("core.operation_log", "DBWriteError", f"操作日志写入失败: {e}", traceback.format_exc())

    # 同时写入审计日志
    try:
        _ensure_audit_db()
        conn = get_conn('audit')
        conn.execute(
            """INSERT INTO audit_logs (user_id, user_name, action, level, resource_type, resource_name, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (username, username, action.upper(), 'INFO', module, detail, 'SUCCESS')
        )
        conn.commit()
    except Exception as e:
        _write_error("core.operation_log", "AuditWriteError", f"审计日志写入失败: {e}", traceback.format_exc())

    # 管理操作同时写入 admin_logs
    if module == "admin":
        try:
            conn = get_conn('admin')
            conn.execute(
                "INSERT INTO admin_logs (admin_user, action, target, details) VALUES (?, ?, ?, ?)",
                (username, action, module, detail)
            )
            conn.commit()
        except Exception:
            pass


def _write_error(module: str, error_type: str, message: str, tb: str = ""):
    """写入错误日志到 sync_log.db"""
    try:
        _ensure_error_db()
        conn = get_conn('sync_log')
        conn.execute(
            "INSERT INTO error_logs (module, error_type, message, traceback) VALUES (?,?,?,?)",
            (module, error_type, message, tb)
        )
        conn.commit()
    except Exception:
        pass

def get_logs(username=None, module=None, limit=200):
    try:
        conn = get_conn('operation_log')
        
        conditions = []
        params = []
        if username:
            conditions.append("username = ?")
            params.append(username)
        if module:
            conditions.append("module = ?")
            params.append(module)
        
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT id, username, action, module, detail, created_at FROM operation_logs {where} ORDER BY id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return rows
    except Exception as e:
        print(f"查询日志失败: {e}")
        return []

def clear_old_logs(days=30):
    try:
        conn = get_conn('operation_log')
        conn.execute(
            "DELETE FROM operation_logs WHERE created_at < datetime('now', '-' || ? || ' days')",
            (days,)
        )
        deleted = conn.rowcount if hasattr(conn, 'rowcount') else conn.execute("SELECT changes()").fetchone()[0]
        conn.commit()
        return deleted
    except Exception as e:
        print(f"清理日志失败: {e}")
        return 0
