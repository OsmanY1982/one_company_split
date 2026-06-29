#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户数据访问对象 (DAO)
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

from core.paths import DATA_DIR


USER_DB = os.path.join(DATA_DIR, "users.db")


class UserDAO:
    """用户数据访问对象"""
    
    def __init__(self):
        self.db_path = USER_DB
        self._ensure_tables()
    
    def _ensure_tables(self):
        """确保数据库表存在"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT '普通用户',
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
        conn.close()
    
    def create_user(self, username: str, password_hash: str = "",
                   role: str = "普通用户", license_type: str = "free") -> bool:
        """创建用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT INTO users (username, password_hash, role, license_type) VALUES (?, ?, ?, ?)",
                (username, password_hash, role, license_type)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"创建用户失败: {e}")
            return False
    
    def get_user(self, username: str) -> Optional[Dict]:
        """获取用户信息"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """通过ID获取用户"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_user(self, username: str, updates: Dict[str, Any]) -> bool:
        """更新用户信息"""
        if not updates:
            return False
        
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [username]
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                f"UPDATE users SET {set_clause}, updated_at = datetime('now') WHERE username = ?",
                values
            )
            conn.commit()
            conn.close()
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
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM users ORDER BY created_at DESC")
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users
    
    def delete_user(self, username: str) -> bool:
        """删除用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.execute("DELETE FROM user_memberships WHERE username = ?", (username,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"删除用户失败: {e}")
            return False
    
    def get_membership(self, username: str) -> Optional[Dict]:
        """获取会员信息"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM user_memberships WHERE username = ?", (username,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def set_membership(self, username: str, membership_type: str,
                      activation_code: str = "", expires_at: str = "") -> bool:
        """设置会员"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT OR REPLACE INTO user_memberships 
                (username, membership_type, activation_code, expires_at, activated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (username, membership_type, activation_code, expires_at, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"设置会员失败: {e}")
            return False
    
    def user_exists(self, username: str) -> bool:
        """检查用户是否存在"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def get_user_count(self) -> int:
        """获取用户总数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def is_admin(self, username: str) -> bool:
        """检查是否为管理员"""
        user = self.get_user(username)
        return user.get("role") == "管理员" if user else False
