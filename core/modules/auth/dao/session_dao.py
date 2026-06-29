#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话数据访问层 (SessionDAO)
管理 sessions.db 中的会话记录，供 sync_auth_service 同步到 Supabase。
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "data"
)
SESSIONS_DB = os.path.join(DATA_DIR, "sessions.db")


class SessionDAO:
    """会话数据访问对象"""

    def __init__(self, db_path: str = SESSIONS_DB):
        self.db_path = db_path
        self._ensure_table()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self):
        conn = self._conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                device_info TEXT DEFAULT '',
                ip_address TEXT DEFAULT '',
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT (datetime('now')),
                expires_at TEXT DEFAULT (datetime('now', '+7 days')),
                last_active TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        conn.close()

    def create_session(self, session_id: str, username: str,
                       device_info: str = "", ip_address: str = "") -> bool:
        try:
            conn = self._conn()
            conn.execute("""
                INSERT OR REPLACE INTO sessions
                (session_id, username, device_info, ip_address, status, created_at, expires_at, last_active)
                VALUES (?, ?, ?, ?, 'active', datetime('now'), datetime('now', '+7 days'), datetime('now'))
            """, (session_id, username, device_info, ip_address))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[SessionDAO] 创建会话失败: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[Dict]:
        conn = self._conn()
        cursor = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def validate_session(self, session_id: str) -> bool:
        conn = self._conn()
        cursor = conn.execute(
            "SELECT expires_at FROM sessions WHERE session_id = ? AND status = 'active'",
            (session_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
        expires = row["expires_at"]
        if expires and expires < datetime.now().strftime("%Y-%m-%d %H:%M:%S"):
            conn.execute("UPDATE sessions SET status='expired' WHERE session_id=?", (session_id,))
            conn.commit()
            conn.close()
            return False
        conn.execute("UPDATE sessions SET last_active=datetime('now') WHERE session_id=?", (session_id,))
        conn.commit()
        conn.close()
        return True

    def destroy_session(self, session_id: str) -> bool:
        try:
            conn = self._conn()
            conn.execute(
                "UPDATE sessions SET status='destroyed' WHERE session_id=?",
                (session_id,)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[SessionDAO] 销毁会话失败: {e}")
            return False

    def list_active_sessions(self, username: Optional[str] = None) -> List[Dict]:
        conn = self._conn()
        if username:
            cursor = conn.execute(
                "SELECT * FROM sessions WHERE status='active' AND username=? ORDER BY created_at DESC",
                (username,)
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM sessions WHERE status='active' ORDER BY created_at DESC"
            )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def cleanup_expired(self) -> int:
        conn = self._conn()
        cursor = conn.execute(
            "UPDATE sessions SET status='expired' WHERE status='active' AND expires_at < datetime('now')"
        )
        conn.commit()
        count = cursor.rowcount
        conn.close()
        return count

    def destroy_all_for_user(self, username: str) -> int:
        conn = self._conn()
        cursor = conn.execute(
            "UPDATE sessions SET status='destroyed' WHERE username=? AND status='active'",
            (username,)
        )
        conn.commit()
        count = cursor.rowcount
        conn.close()
        return count


if __name__ == "__main__":
    dao = SessionDAO()
    print(f"SessionDAO 初始化完成，数据库: {dao.db_path}")
    print(f"活跃会话数: {len(dao.list_active_sessions())}")
