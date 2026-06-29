# `core/user_dao.py`

> 路径：`core/user_dao.py` | 行数：174


---


```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户数据访问对象 (DAO)
—— 已池化：所有连接通过 get_conn('users') 统一管理
—— P1 (2026-06-28): 字段名统一 password_hash→password, role默认值 普通用户→user
"""

from sqlite3 import IntegrityError
from datetime import datetime
from typing import Dict, List, Optional, Any

from core.database import get_conn


class UserDAO:
    """用户数据访问对象"""

    def __init__(self):
        self._ensure_tables()

    def _ensure_tables(self):
        """确保数据库表存在"""
        conn = get_conn('users')
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT 'user',
                license_type TEXT DEFAULT 'free',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_memberships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                membership_type TEXT DEFAULT 'free',
                activation_code TEXT DEFAULT '',
                activated_at TEXT DEFAULT (datetime('now')),
                expires_at TEXT DEFAULT '',
                UNIQUE(username)
            )
        """)

        conn.commit()

    def create_user(self, username: str, password: str = "",
                   role: str = "user", license_type: str = "free") -> bool:
        """创建用户"""
        try:
            conn = get_conn('users')
            conn.execute(
                "INSERT INTO users (username, password, role, license_type) VALUES (?, ?, ?, ?)",
                (username, password, role, license_type)
            )
            conn.commit()
            return True
        except IntegrityError:
            return False
        except Exception as e:
            print(f"创建用户失败: {e}")
            return False

    def get_user(self, username: str) -> Optional[Dict]:
        """获取用户信息"""
        conn = get_conn('users')
        cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """通过ID获取用户"""
        conn = get_conn('users')
        cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_user(self, username: str, updates: Dict[str, Any]) -> bool:
        """更新用户信息"""
        if not updates:
            return False

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [username]

        try:
            conn = get_conn('users')
            conn.execute(
                f"UPDATE users SET {set_clause}, updated_at = datetime('now') WHERE username = ?",
                values
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"更新用户失败: {e}")
            return False

    def update_user_role(self, username: str, role: str) -> bool:
        """更新用户角色"""
        return self.update_user(username, {"role": role})

    def update_license(self, username: str, license_type: str) -> bool:
        """更新许可证类型"""
        return self.update_user(username, {"license_type": license_type})

    def list_users(self) -> List[Dict]:
        """列出所有用户"""
        conn = get_conn('users')
        cursor = conn.execute("SELECT * FROM users ORDER BY created_at DESC")
        users = [dict(row) for row in cursor.fetchall()]
        return users

    def delete_user(self, username: str) -> bool:
        """删除用户"""
        try:
            conn = get_conn('users')
            conn.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.execute("DELETE FROM user_memberships WHERE username = ?", (username,))
            conn.commit()
            return True
        except Exception as e:
            print(f"删除用户失败: {e}")
            return False

    def get_membership(self, username: str) -> Optional[Dict]:
        """获取会员信息"""
        conn = get_conn('users')
        cursor = conn.execute(
            "SELECT * FROM user_memberships WHERE username = ?", (username,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def set_membership(self, username: str, membership_type: str,
                      activation_code: str = "", expires_at: str = "") -> bool:
        """设置会员"""
        try:
            conn = get_conn('users')
            conn.execute("""
                INSERT OR REPLACE INTO user_memberships
                (username, membership_type, activation_code, expires_at, activated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (username, membership_type, activation_code, expires_at, datetime.now().isoformat()))
            conn.commit()
            return True
        except Exception as e:
            print(f"设置会员失败: {e}")
            return False

    def user_exists(self, username: str) -> bool:
        """检查用户是否存在"""
        conn = get_conn('users')
        cursor = conn.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
        count = cursor.fetchone()[0]
        return count > 0

    def get_user_count(self) -> int:
        """获取用户总数"""
        conn = get_conn('users')
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        return count

    def is_admin(self, username: str) -> bool:
        """检查是否为管理员（兼容旧 role 值）"""
        user = self.get_user(username)
        if not user:
            return False
        r = user.get("role", "")
        return r in ("admin", "管理员")

```
