# `modules/auth/auth_service.py`

> 路径：`modules/auth/auth_service.py` | 行数：304


---


```python
import logging

logger = logging.getLogger(__name__)

"""
认证服务模块 — 用户注册/登录/会员管理
数据持久化到 modules/auth/users.json + data/users.db (SQLite)
注册时双写：JSON（本地登录） + SQLite（云端同步）
登录时双读：JSON 优先，SQLite 兜底（跨机注册用户）

拆分说明：SQLite 桥接 → auth_service_sync.py；会员管理 → auth_service_membership.py
"""
import traceback
import json
import os
import hashlib
import sqlite3
import bcrypt
from datetime import datetime, timedelta
from typing import Optional

from core.operation_log import log_action
from modules.auth.auth_service_sync import SyncMixin
from modules.auth.auth_service_membership import MembershipMixin

# ── 路径常量 ──
USER_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
ACTIVATION_DB = os.path.join(DATA_DIR, "activation.db")
USERS_SQLITE_DB = os.path.join(DATA_DIR, "users.db")

# ── 会员类型定义 ──
MEMBERSHIP_TRIAL = "trial"
MEMBERSHIP_VIP = "vip"
MEMBERSHIP_PERMANENT = "permanent"

MEMBERSHIP_PRICES = {
    MEMBERSHIP_TRIAL: 0,
    MEMBERSHIP_VIP: 49,
    MEMBERSHIP_PERMANENT: 99,
}

MEMBERSHIP_LABELS = {
    MEMBERSHIP_TRIAL: "体验会员",
    MEMBERSHIP_VIP: "VIP会员",
    MEMBERSHIP_PERMANENT: "永久会员",
}

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "$2b$12$yd1e1mRKXK1C6naNiD/WTuP1wkLCcVnfSBbj1OXdIPQiWGvHzorbq"


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _load_users() -> dict:
    """加载用户数据，兼容旧格式自动迁移"""
    if not os.path.exists(USER_DB):
        users = {
            ADMIN_USERNAME: {
                "password": ADMIN_PASSWORD, "role": "admin",
                "membership": MEMBERSHIP_PERMANENT, "expire_at": None,
                "created_at": "2026-01-01 00:00:00",
            }
        }
        _save_users(users)
        return users

    try:
        with open(USER_DB, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        corrupted = USER_DB + ".corrupted"
        try:
            os.rename(USER_DB, corrupted)
            print(f"[auth] users.json 损坏，已备份到 {corrupted}：{e}")
        except Exception:
            logger.exception("异常详情")
        users = {
            ADMIN_USERNAME: {
                "password": ADMIN_PASSWORD, "role": "admin",
                "membership": MEMBERSHIP_PERMANENT, "expire_at": None,
                "created_at": "2026-01-01 00:00:00",
            }
        }
        _save_users(users)
        return users

    if not data:
        data = {
            ADMIN_USERNAME: {
                "password": ADMIN_PASSWORD, "role": "admin",
                "membership": MEMBERSHIP_PERMANENT, "expire_at": None,
                "created_at": "2026-01-01 00:00:00",
            }
        }
        _save_users(data)
        return data

    first_val = next(iter(data.values()), None)
    if isinstance(first_val, str):
        migrated = {}
        for username, password in data.items():
            if username == ADMIN_USERNAME:
                migrated[username] = {
                    "password": password, "role": "admin",
                    "membership": MEMBERSHIP_PERMANENT, "expire_at": None,
                    "created_at": "2026-01-01 00:00:00",
                }
            else:
                migrated[username] = {
                    "password": password, "role": "member",
                    "membership": MEMBERSHIP_TRIAL,
                    "expire_at": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"),
                    "created_at": _now(),
                }
        _save_users(migrated)
        return migrated

    if ADMIN_USERNAME not in data:
        data[ADMIN_USERNAME] = {
            "password": ADMIN_PASSWORD, "role": "admin",
            "membership": MEMBERSHIP_PERMANENT, "expire_at": None,
            "created_at": "2026-01-01 00:00:00",
        }
        _save_users(data)

    return data


def _save_users(users: dict):
    os.makedirs(os.path.dirname(USER_DB), exist_ok=True)
    tmp_path = USER_DB + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, USER_DB)


# ── 密码哈希工具（bcrypt + sha256 + 明文 三重兼容）──

def _hash_password(password: str) -> str:
    """用 bcrypt 哈希密码。"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, stored: str) -> bool:
    """三重兼容密码验证：bcrypt → sha256 → 明文。"""
    if not password or not stored:
        return False
    # bcrypt ($2 前缀)
    if stored.startswith("$2"):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8"))
        except Exception:
            return False
    # sha256（64 位十六进制）
    if len(stored) == 64 and all(c in "0123456789abcdef" for c in stored):
        return hashlib.sha256(password.encode("utf-8")).hexdigest() == stored
    # 明文兜底
    return password == stored


def _needs_rehash(stored: str) -> bool:
    """判断是否需要升级为 bcrypt 哈希。"""
    return not (stored and stored.startswith("$2"))


class AuthService(SyncMixin, MembershipMixin):
    """认证服务 — 核心认证 + Mixin(SQLite桥接 + 会员管理)"""

    MEMBERSHIP_TRIAL = MEMBERSHIP_TRIAL
    MEMBERSHIP_VIP = MEMBERSHIP_VIP
    MEMBERSHIP_PERMANENT = MEMBERSHIP_PERMANENT
    MEMBERSHIP_LABELS = MEMBERSHIP_LABELS
    MEMBERSHIP_PRICES = MEMBERSHIP_PRICES
    ACTIVATION_DB = ACTIVATION_DB
    USERS_SQLITE_DB = USERS_SQLITE_DB

    def __init__(self):
        self._users = _load_users()

    def _reload(self):
        self._users = _load_users()

    @staticmethod
    def _now():
        return _now()

    @staticmethod
    def _save_users(users: dict):
        _save_users(users)

    # ── 核心认证 ──

    def register(self, username: str, password: str) -> tuple:
        self._reload()
        if not username or not password:
            return False, "用户名和密码不能为空"
        if len(username) < 2:
            return False, "用户名至少2个字符"
        if len(password) < 3:
            return False, "密码至少3个字符"
        if username in self._users:
            return False, "该用户名已被占用"

        now = _now()
        expire_at = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        self._users[username] = {
            "password": _hash_password(password), "role": "member",
            "membership": MEMBERSHIP_TRIAL, "expire_at": expire_at,
            "created_at": now,
        }
        _save_users(self._users)
        self._sync_user_to_sqlite(username)
        self._sync_membership_to_sqlite(username)
        self._trigger_cloud_sync()
        try:
            log_action(username, "注册", "login", "新用户注册")
        except Exception:
            logger.exception("异常详情")
        return True, "注册成功"

    def login(self, username: str, password: str) -> dict:
        self._reload()
        if not username or not password:
            return {"ok": False, "msg": "用户名和密码不能为空", "user": None}

        user = self._users.get(username)
        if not user:
            user = self._find_user_in_sqlite(username)

        if not user:
            return {"ok": False, "msg": "用户名或密码错误", "user": None}
        if not _verify_password(password, user.get("password", "")):
            return {"ok": False, "msg": "用户名或密码错误", "user": None}

        # 自动升级旧哈希到 bcrypt
        if _needs_rehash(user.get("password", "")):
            user["password"] = _hash_password(password)
            _save_users(self._users)
            self._sync_user_to_sqlite(username)

        if user["role"] == "admin":
            try:
                log_action(username, "登录", "login", "管理员登录成功")
            except Exception:
                logger.exception("异常详情")
            return {"ok": True, "msg": "管理员登录成功", "user": user}

        expire_str = user.get("expire_at")
        if expire_str:
            try:
                expire_dt = datetime.strptime(expire_str, "%Y-%m-%d %H:%M:%S")
                if datetime.now() > expire_dt:
                    return {
                        "ok": False,
                        "msg": f"会员已过期（{expire_str}），请续费后登录",
                        "user": user,
                    }
            except ValueError:
                traceback.print_exc()

        try:
            log_action(username, "登录", "login", "用户登录成功")
        except Exception:
            logger.exception("异常详情")
        return {"ok": True, "msg": "登录成功", "user": user}

    def admin_login(self, password: str) -> dict:
        return self.login(ADMIN_USERNAME, password)

    def modify_password(self, username: str, old_password: str,
                        new_password: str, confirm_password: str) -> tuple:
        self._reload()
        user = self._users.get(username)
        if not user:
            return False, "用户不存在"
        if not _verify_password(old_password, user.get("password", "")):
            return False, "原密码错误"
        if not new_password or len(new_password) < 6:
            return False, "新密码至少6位"
        if new_password != confirm_password:
            return False, "两次输入的新密码不一致"
        if _verify_password(new_password, user.get("password", "")):
            return False, "新密码不能与原密码相同"

        user["password"] = _hash_password(new_password)
        _save_users(self._users)
        self._sync_user_to_sqlite(username)
        self._trigger_cloud_sync()
        try:
            log_action(username, "修改密码", "account", "密码修改成功")
        except Exception:
            logger.exception("异常详情")
        return True, "密码修改成功，请重新登录"

    def get_user_info(self, username: str) -> Optional[dict]:
        self._reload()
        return self._users.get(username)

    def is_admin(self, username: str) -> bool:
        user = self._users.get(username)
        return user is not None and user.get("role") == "admin"

```
