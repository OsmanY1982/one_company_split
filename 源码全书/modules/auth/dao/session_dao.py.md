# `modules/auth/dao/session_dao.py`

> 路径：`modules/auth/dao/session_dao.py` | 行数：177


---


```python
# -*- coding: utf-8 -*-
"""
会话数据访问层 — SessionDAO
管理 sessions.db 中的用户登录会话记录，支持 CRUD + 过期清理。
"""
import os
import sqlite3
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    from core.paths import DATA_DIR
    DB_FILE = os.path.join(DATA_DIR, "sessions.db")
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    DB_FILE = os.path.join(BASE_DIR, "data", "sessions.db")

SESSION_EXPIRE_DAYS = 7


def _ensure_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            device_id TEXT NOT NULL,
            session_token TEXT NOT NULL,
            device_type TEXT DEFAULT 'desktop',
            ip_address TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            last_active_at TEXT,
            created_at TEXT,
            UNIQUE(username, device_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS session_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            device_id TEXT DEFAULT '',
            ip_address TEXT DEFAULT '',
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()


class SessionDAO:
    """Data Access Object for session operations."""

    def create_session(self, username: str, device_id: str,
                       session_token: str, device_type: str = "desktop",
                       ip_address: str = "") -> bool:
        _ensure_db()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(DB_FILE)
        try:
            conn.execute('''
                INSERT OR REPLACE INTO sessions
                (username, device_id, session_token, device_type, ip_address,
                 status, last_active_at, created_at)
                VALUES (?,?,?,?,?,'active',?,?)
            ''', (username, device_id, session_token, device_type, ip_address, now, now))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return False
        finally:
            conn.close()

    def get_session(self, username: str, device_id: str) -> dict:
        _ensure_db()
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM sessions WHERE username=? AND device_id=? AND status='active'",
            (username, device_id)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return dict(row)

    def get_user_sessions(self, username: str) -> list:
        _ensure_db()
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM sessions WHERE username=? AND status='active' ORDER BY last_active_at DESC",
            (username,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_activity(self, username: str, device_id: str) -> bool:
        _ensure_db()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(DB_FILE)
        try:
            conn.execute(
                "UPDATE sessions SET last_active_at=? WHERE username=? AND device_id=?",
                (now, username, device_id)
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"更新活动时间失败: {e}")
            return False
        finally:
            conn.close()

    def invalidate_session(self, username: str, device_id: str = None) -> int:
        _ensure_db()
        conn = sqlite3.connect(DB_FILE)
        try:
            if device_id:
                conn.execute(
                    "UPDATE sessions SET status='invalid' WHERE username=? AND device_id=?",
                    (username, device_id)
                )
            else:
                conn.execute(
                    "UPDATE sessions SET status='invalid' WHERE username=?",
                    (username,)
                )
            conn.commit()
            affected = conn.execute("SELECT CHANGES()").fetchone()[0]
            return affected
        except Exception as e:
            logger.error(f"失效会话失败: {e}")
            return 0
        finally:
            conn.close()

    def cleanup_expired_sessions(self) -> int:
        _ensure_db()
        cutoff = (datetime.now() - timedelta(days=SESSION_EXPIRE_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(DB_FILE)
        try:
            conn.execute(
                "UPDATE sessions SET status='expired' WHERE status='active' AND last_active_at < ?",
                (cutoff,)
            )
            conn.commit()
            affected = conn.execute("SELECT CHANGES()").fetchone()[0]
            return affected
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
            return 0
        finally:
            conn.close()

    def log_session_event(self, username: str, action: str,
                          device_id: str = "", ip_address: str = "") -> bool:
        _ensure_db()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(DB_FILE)
        try:
            conn.execute(
                "INSERT INTO session_log (username, action, device_id, ip_address, created_at) VALUES (?,?,?,?,?)",
                (username, action, device_id, ip_address, now)
            )
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"记录会话事件失败: {e}")
            return False
        finally:
            conn.close()

```
