# -*- coding: utf-8 -*-
from core.paths import DATA_DIR

import sqlite3
import os
from datetime import datetime

USER_DB = os.path.join(DATA_DIR, "users.db")


class DataSync:
    
    @staticmethod
    def record_user_login(username, role, license_type):
        from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
        try:
            conn = sqlite3.connect(USER_DB)
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("SELECT id FROM users WHERE username=?", (username,))
            exists = cursor.fetchone()
            if exists:
                cursor.execute(
                    "UPDATE users SET role=?, license_type=?, updated_at=? WHERE username=?",
                    (role, license_type, now, username)
                )
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"Record user login error: {e}")
    
    @staticmethod
    def record_membership(username, membership_type, activation_code=None):
        from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
        try:
            conn = sqlite3.connect(USER_DB)
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute("SELECT membership_type FROM user_memberships WHERE username=?", (username,))
            existing = cursor.fetchone()
            if existing and existing[0] and not membership_type:
                conn.close()
                return
            cursor.execute(
                "INSERT OR REPLACE INTO user_memberships (username, membership_type, activation_code, activated_at) VALUES (?, ?, ?, ?)",
                (username, membership_type, activation_code, now)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Record membership error: {e}")
    
    @staticmethod
    def get_user_info(username):
        from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
        try:
            conn = sqlite3.connect(USER_DB)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            user = cursor.fetchone()
            conn.close()
            return user
        except Exception:
            return None
    
    @staticmethod
    def get_user_membership(username):
        from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
        try:
            conn = sqlite3.connect(USER_DB)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_memberships WHERE username=?", (username,))
            membership = cursor.fetchone()
            conn.close()
            return membership
        except Exception:
            return None
    
    @staticmethod
    def list_all_users():
        from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
        try:
            conn = sqlite3.connect(USER_DB)
            cursor = conn.cursor()
            cursor.execute("SELECT username, role, license_type FROM users")
            users = cursor.fetchall()
            conn.close()
            return users
        except Exception:
            return []
