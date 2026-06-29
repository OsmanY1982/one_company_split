# `modules/auth/auth_service_sync.py`

> 路径：`modules/auth/auth_service_sync.py` | 行数：101


---


```python
"""
认证服务 — SQLite 双向桥接 Mixin
注册/修改密码后双写 JSON → SQLite → 触发 cloud_sync 上传
登录时 JSON 优先 → SQLite 兜底（跨机 cloud_pull 拉取的用户）
"""
import traceback
import os
import sqlite3
import threading


class SyncMixin:
    """SQLite 同步桥接，作为 AuthService 的 Mixin 使用"""

    def _sync_user_to_sqlite(self, username: str):
        """将 users.json 中的用户同步到 data/users.db（SQLite），供 cloud_sync 上传"""
        user = self._users.get(username)
        if not user:
            return
        try:
            os.makedirs(os.path.dirname(self.USERS_SQLITE_DB), exist_ok=True)
            conn = sqlite3.connect(self.USERS_SQLITE_DB)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT DEFAULT '',
                user_id TEXT,
                role TEXT DEFAULT 'user',
                license_type TEXT,
                created_at TEXT,
                updated_at TEXT
            )''')
            c.execute('''INSERT OR REPLACE INTO users
                (username, password, role, license_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, datetime('now','localtime'))''',
                (username, user.get("password", ""),
                 user.get("role", "member"),
                 user.get("membership", "trial"),
                 user.get("created_at", self._now())))
            conn.commit()
            conn.close()
        except Exception:
            traceback.print_exc()

    def _sync_membership_to_sqlite(self, username: str):
        """将 users.json 中的会员信息同步到 data/users.db 的 user_memberships"""
        user = self._users.get(username)
        if not user:
            return
        try:
            conn = sqlite3.connect(self.USERS_SQLITE_DB)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS user_memberships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                membership_type TEXT,
                activated_at TEXT,
                expires_at TEXT,
                activation_code TEXT
            )''')
            c.execute('''INSERT OR REPLACE INTO user_memberships
                (username, membership_type, expires_at, activated_at)
                VALUES (?, ?, ?, ?)''',
                (username, user.get("membership", "trial"),
                 user.get("expire_at", None),
                 self._now()))
            conn.commit()
            conn.close()
        except Exception:
            traceback.print_exc()

    def _trigger_cloud_sync(self):
        """异步触发云端同步（不阻塞 UI）"""
        try:
            from core.cloud_sync import sync_users
            t = threading.Thread(target=sync_users, daemon=True)
            t.start()
        except Exception:
            traceback.print_exc()

    def _find_user_in_sqlite(self, username: str):
        """在 data/users.db 中查找用户（跨机注册兜底）"""
        if not os.path.exists(self.USERS_SQLITE_DB):
            return None
        try:
            conn = sqlite3.connect(self.USERS_SQLITE_DB)
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            conn.close()
            if row:
                return {
                    "password": row["password"] or "",
                    "role": row["role"] or "member",
                    "membership": row["license_type"] or self.MEMBERSHIP_TRIAL,
                    "expire_at": None,
                    "created_at": row["created_at"] or self._now(),
                }
        except Exception:
            traceback.print_exc()
        return None

```
