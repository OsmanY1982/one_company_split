# -*- coding: utf-8 -*-
import sys
import os
import logging

logger = logging.getLogger(__name__)

# Use core.paths for consistent DB location (same as AdminUserWidget)
import sqlite3
from datetime import datetime

try:
    from core.paths import DATA_DIR
    DB_FILE = os.path.join(DATA_DIR, "users.db")
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    DB_FILE = os.path.join(BASE_DIR, "data", "users.db")


def _ensure_db():
    """Ensure the users database and tables exist, with schema migration."""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create users table matching the actual production schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            user_id TEXT,
            password TEXT DEFAULT '',
            role TEXT DEFAULT 'user',
            license_type TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')

    # Schema migration: add any columns missing from older tables
    existing = [r[1] for r in cursor.execute("PRAGMA table_info('users')").fetchall()]
    for col_name, col_type in [
        ('user_id', 'TEXT'), ('password', "TEXT DEFAULT ''"),
        ('license_type', 'TEXT'), ('created_at', 'TEXT'), ('updated_at', 'TEXT')
    ]:
        if col_name not in existing:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            except Exception:
                logger.exception("异常详情")

    # Create user_memberships table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_memberships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            membership_type TEXT,
            activated_at TEXT,
            expires_at TEXT,
            activation_code TEXT
        )
    ''')

    conn.commit()
    conn.close()


class UserDAO:
    """Data Access Object for user operations."""

    def get_user(self, username):
        _ensure_db()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Use 'password' column (actual production schema, not 'password_hash')
        cursor.execute(
            "SELECT id, username, password, role, created_at FROM users WHERE username=?",
            (username,)
        )
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        return {
            'id': row[0],
            'username': row[1],
            'password': row[2],
            'role': row[3],
            'created_at': row[4],
        }

    def add_user(self, username, password_hash, role='user'):
        _ensure_db()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor.execute(
                "INSERT INTO users (username, password, role, created_at, updated_at) VALUES (?,?,?,?,?)",
                (username, password_hash, role, now, now)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False

    def update_password(self, username, new_password_hash):
        _ensure_db()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password=?, updated_at=? WHERE username=?",
            (new_password_hash, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username)
        )
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def user_exists(self, username):
        _ensure_db()
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username=?", (username,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists


# ── Module-level helpers (used by other parts of the system) ──────────────────

def create_user(username, password_hash, role='user'):
    dao = UserDAO()
    return dao.add_user(username, password_hash, role)


def get_user(username):
    dao = UserDAO()
    return dao.get_user(username)
