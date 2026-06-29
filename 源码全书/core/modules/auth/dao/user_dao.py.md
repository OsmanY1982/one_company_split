# `core/modules/auth/dao/user_dao.py`

> 路径：`core/modules/auth/dao/user_dao.py` | 行数：200


---


```python
# -*- coding: utf-8 -*-
import sys
import os

# Use core.paths for consistent DB location (same as AdminUserWidget)
from sqlite3 import IntegrityError
from datetime import datetime
from core.database import get_conn, close_conn

# ── P0 bcrypt 密码哈希（2026-06-28）──
try:
    import bcrypt
    _BCRYPT_AVAILABLE = True
except ImportError:
    _BCRYPT_AVAILABLE = False
    import hashlib

try:
    from core.paths import DATA_DIR
    DB_FILE = os.path.join(DATA_DIR, "users.db")
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    DB_FILE = os.path.join(BASE_DIR, "data", "users.db")


# ── 密码工具 ───────────────────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """对明文密码进行哈希（bcrypt 优先，fallback sha256）"""
    if _BCRYPT_AVAILABLE:
        return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    return hashlib.sha256(plain_password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed: str) -> bool:
    """验证明文密码是否匹配哈希值。自动识别 bcrypt / sha256 / 明文。"""
    if not plain_password or not hashed:
        return False
    # bcrypt 哈希以 $2 开头
    if hashed.startswith("$2"):
        if _BCRYPT_AVAILABLE:
            try:
                return bcrypt.checkpw(plain_password.encode("utf-8"), hashed.encode("utf-8"))
            except Exception:
                return False
        return False
    # sha256 哈希为 64 位十六进制
    if len(hashed) == 64 and all(c in "0123456789abcdef" for c in hashed):
        return hashlib.sha256(plain_password.encode("utf-8")).hexdigest() == hashed
    # 明文兜底（兼容旧数据）
    return plain_password == hashed


def needs_rehash(hashed: str) -> bool:
    """判断密码哈希是否需要升级到 bcrypt"""
    if not _BCRYPT_AVAILABLE:
        return False
    return not hashed.startswith("$2")


def _ensure_db():
    """Ensure the users database and tables exist, with schema migration."""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = get_conn('users.db')
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
                pass

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
    close_conn('users.db')


class UserDAO:
    """Data Access Object for user operations."""

    def get_user(self, username):
        _ensure_db()
        conn = get_conn('users.db')
        cursor = conn.cursor()
        # Use 'password' column (actual production schema, not 'password_hash')
        cursor.execute(
            "SELECT id, username, password, role, created_at FROM users WHERE username=?",
            (username,)
        )
        row = cursor.fetchone()
        close_conn('users.db')
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
        """添加用户。password_hash 应为明文密码，内部自动 bcrypt 哈希。"""
        _ensure_db()
        conn = get_conn('users.db')
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # P0: 密码自动哈希
        hashed = hash_password(password_hash)
        try:
            cursor.execute(
                "INSERT INTO users (username, password, role, created_at, updated_at) VALUES (?,?,?,?,?)",
                (username, hashed, role, now, now)
            )
            conn.commit()
            close_conn('users.db')
            return True
        except sqlite3.IntegrityError:
            close_conn('users.db')
            return False

    def update_password(self, username, new_password_hash):
        """更新密码。new_password_hash 应为明文，内部自动 bcrypt 哈希。"""
        _ensure_db()
        conn = get_conn('users.db')
        cursor = conn.cursor()
        hashed = hash_password(new_password_hash)
        cursor.execute(
            "UPDATE users SET password=?, updated_at=? WHERE username=?",
            (hashed, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username)
        )
        conn.commit()
        affected = cursor.rowcount
        close_conn('users.db')
        return affected > 0

    def verify_password(self, username, plain_password):
        """验证用户密码。返回 (bool, user_dict_or_None)"""
        user = self.get_user(username)
        if not user:
            return False, None
        stored = user.get("password", "")
        if verify_password(plain_password, stored):
            # P0: 密码哈希自动升级到 bcrypt
            if needs_rehash(stored):
                self.update_password(username, plain_password)
            return True, user
        return False, None

    def user_exists(self, username):
        _ensure_db()
        conn = get_conn('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username=?", (username,))
        exists = cursor.fetchone() is not None
        close_conn('users.db')
        return exists


# ── Module-level helpers (used by other parts of the system) ──────────────────

def create_user(username, password_hash, role='user'):
    dao = UserDAO()
    return dao.add_user(username, password_hash, role)


def get_user(username):
    dao = UserDAO()
    return dao.get_user(username)

```
