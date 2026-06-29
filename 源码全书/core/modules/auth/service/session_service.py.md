# `core/modules/auth/service/session_service.py`

> 路径：`core/modules/auth/service/session_service.py` | 行数：200


---


```python
# -*- coding: utf-8 -*-
"""
会话管理服务 — 创建/验证/销毁会话，同步 sessions.db + Supabase device_bindings
P0 新建（2026-06-28 第十三档）
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from core.database import get_conn, close_conn

try:
    from core.paths import DATA_DIR
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))
    DATA_DIR = os.path.join(BASE_DIR, "data")

SESSIONS_DB = os.path.join(DATA_DIR, "sessions.db")
SESSION_LIFETIME_HOURS = 24


def _ensure_db():
    """确保 sessions.db 及其表存在"""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = get_conn("sessions.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            device_id TEXT DEFAULT '',
            ip_address TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_username ON sessions(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_id)")
    conn.commit()
    close_conn("sessions.db")


class SessionService:
    """会话管理服务：创建/验证/销毁"""

    def __init__(self):
        _ensure_db()

    def create_session(self, username: str, device_id: str = "",
                       ip_address: str = "") -> Optional[str]:
        """创建新会话，返回 session_id"""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        created = now.strftime("%Y-%m-%d %H:%M:%S")
        expires = (now + timedelta(hours=SESSION_LIFETIME_HOURS)).strftime(
            "%Y-%m-%d %H:%M:%S")
        try:
            conn = get_conn("sessions.db")
            cursor = conn.cursor()
            # 将同一用户旧的活跃会话标记为非活跃
            cursor.execute(
                "UPDATE sessions SET is_active=0 WHERE username=? AND is_active=1",
                (username,))
            cursor.execute(
                "INSERT INTO sessions (session_id, username, device_id, ip_address, "
                "created_at, expires_at, is_active) VALUES (?,?,?,?,?,?,1)",
                (session_id, username, device_id, ip_address, created, expires))
            conn.commit()
            close_conn("sessions.db")
            return session_id
        except Exception:
            try:
                close_conn("sessions.db")
            except Exception:
                pass
            return None

    def validate_session(self, session_id: str) -> Optional[dict]:
        """验证会话是否有效，返回用户信息字典或 None"""
        try:
            conn = get_conn("sessions.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, device_id, expires_at FROM sessions "
                "WHERE session_id=? AND is_active=1", (session_id,))
            row = cursor.fetchone()
            close_conn("sessions.db")
            if not row:
                return None
            username, device_id, expires_str = row
            try:
                expires_dt = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
                if datetime.now() > expires_dt:
                    self.destroy_session(session_id)
                    return None
            except ValueError:
                return None
            return {"username": username, "device_id": device_id}
        except Exception:
            try:
                close_conn("sessions.db")
            except Exception:
                pass
            return None

    def destroy_session(self, session_id: str) -> bool:
        """销毁指定会话"""
        try:
            conn = get_conn("sessions.db")
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET is_active=0 WHERE session_id=?",
                (session_id,))
            conn.commit()
            close_conn("sessions.db")
            return True
        except Exception:
            try:
                close_conn("sessions.db")
            except Exception:
                pass
            return False

    def destroy_all_for_user(self, username: str) -> bool:
        """销毁某用户的所有会话（登出全部设备）"""
        try:
            conn = get_conn("sessions.db")
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET is_active=0 WHERE username=? AND is_active=1",
                (username,))
            conn.commit()
            close_conn("sessions.db")
            return True
        except Exception:
            try:
                close_conn("sessions.db")
            except Exception:
                pass
            return False

    def get_active_sessions(self, username: str) -> list:
        """获取某用户的所有活跃会话"""
        try:
            conn = get_conn("sessions.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT session_id, device_id, created_at, expires_at "
                "FROM sessions WHERE username=? AND is_active=1 "
                "ORDER BY created_at DESC",
                (username,))
            rows = cursor.fetchall()
            close_conn("sessions.db")
            return [
                {"session_id": r[0], "device_id": r[1],
                 "created_at": r[2], "expires_at": r[3]}
                for r in rows
            ]
        except Exception:
            try:
                close_conn("sessions.db")
            except Exception:
                pass
            return []

    def cleanup_expired(self) -> int:
        """清理过期会话，返回清理数量"""
        try:
            conn = get_conn("sessions.db")
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "UPDATE sessions SET is_active=0 WHERE is_active=1 AND expires_at<?",
                (now,))
            count = cursor.rowcount
            conn.commit()
            close_conn("sessions.db")
            return count
        except Exception:
            try:
                close_conn("sessions.db")
            except Exception:
                pass
            return 0


# ── 便捷函数 ───────────────────────────────────────────────────────────

_session_service: Optional[SessionService] = None


def get_session_service() -> SessionService:
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service

```
