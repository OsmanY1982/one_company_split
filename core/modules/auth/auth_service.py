"""
认证服务模块 — 用户注册/登录/会员管理
数据持久化到 modules/auth/users.json + data/users.db (SQLite)
注册时双写：JSON（本地登录） + SQLite（云端同步）
登录时双读：JSON 优先，SQLite 兜底（跨机注册用户）

拆分说明：SQLite 桥接 → auth_service_sync.py；会员管理 → auth_service_membership.py

── 版本功能地图 ──
  项目：core
  窗口尺寸：N/A（非 GUI 模块）
  主题引用：N/A
  类型标注：是（from __future__ import annotations）
  拖拽支持：N/A
  关闭按钮：N/A
  辉光效果：N/A
  统一基准：同步自 iqra 版（移除死导入 sqlite3，保留类型标注）
"""
from __future__ import annotations

import traceback
import json
import os
from datetime import datetime, timedelta
from typing import Any, Optional

from core.operation_log import log_action
from core.modules.auth.auth_service_sync import SyncMixin
from core.modules.auth.auth_service_membership import MembershipMixin
# ── P0 bcrypt 密码哈希（2026-06-28）──
from core.modules.auth.dao.user_dao import hash_password, verify_password, needs_rehash

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
ADMIN_PASSWORD = "admin"


def _now() -> Any:
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
            pass
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


def _save_users(users: dict) -> None:
    os.makedirs(os.path.dirname(USER_DB), exist_ok=True)
    tmp_path = USER_DB + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, USER_DB)


class AuthService(SyncMixin, MembershipMixin):
    """认证服务 — 核心认证 + Mixin(SQLite桥接 + 会员管理)"""

    MEMBERSHIP_TRIAL = MEMBERSHIP_TRIAL
    MEMBERSHIP_VIP = MEMBERSHIP_VIP
    MEMBERSHIP_PERMANENT = MEMBERSHIP_PERMANENT
    MEMBERSHIP_LABELS = MEMBERSHIP_LABELS
    MEMBERSHIP_PRICES = MEMBERSHIP_PRICES
    ACTIVATION_DB = ACTIVATION_DB
    USERS_SQLITE_DB = USERS_SQLITE_DB

    def __init__(self) -> None:
        self._users = _load_users()

    def _reload(self) -> None:
        self._users = _load_users()

    @staticmethod
    def _now() -> Any:
        return _now()

    @staticmethod
    def _save_users(users: dict) -> None:
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
        # P0: bcrypt 哈希存储
        self._users[username] = {
            "password": hash_password(password), "role": "member",
            "membership": MEMBERSHIP_TRIAL, "expire_at": expire_at,
            "created_at": now,
        }
        _save_users(self._users)
        self._sync_user_to_sqlite(username)
        self._sync_membership_to_sqlite(username)
        # P0: 注册后自动触发云端全量同步
        self._trigger_cloud_sync()
        try:
            log_action(username, "注册", "login", "新用户注册")
        except Exception:
            pass
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

        # P0: bcrypt 验证密码（自动兼容明文/sha256 旧数据）
        stored_pw = user.get("password", "")
        if not verify_password(password, stored_pw):
            return {"ok": False, "msg": "用户名或密码错误", "user": None}

        # P0: 密码自动升级到 bcrypt
        if needs_rehash(stored_pw):
            user["password"] = hash_password(password)
            _save_users(self._users)
            self._sync_user_to_sqlite(username)

        if user["role"] == "admin":
            try:
                log_action(username, "登录", "login", "管理员登录成功")
            except Exception:
                pass
            # P0: 管理员登录后触发全量云端拉取
            self._trigger_cloud_sync_on_login()
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
            pass
        # P0: 普通用户登录也触发全量云端拉取
        self._trigger_cloud_sync_on_login()
        return {"ok": True, "msg": "登录成功", "user": user}

    def _trigger_cloud_sync_on_login(self):
        """P0: 登录成功后从云端拉取全部数据"""
        try:
            from core.simple_sync import auto_sync_on_login
            auto_sync_on_login()
        except Exception:
            pass

    def admin_login(self, password: str) -> dict:
        return self.login(ADMIN_USERNAME, password)

    def modify_password(self, username: str, old_password: str,
                        new_password: str, confirm_password: str) -> tuple:
        self._reload()
        user = self._users.get(username)
        if not user:
            return False, "用户不存在"
        # P0: bcrypt 验证旧密码
        if not verify_password(old_password, user.get("password", "")):
            return False, "原密码错误"
        if not new_password or len(new_password) < 6:
            return False, "新密码至少6位"
        if new_password != confirm_password:
            return False, "两次输入的新密码不一致"
        if new_password == old_password:
            return False, "新密码不能与原密码相同"

        # P0: bcrypt 哈希新密码
        user["password"] = hash_password(new_password)
        _save_users(self._users)
        self._sync_user_to_sqlite(username)
        self._trigger_cloud_sync()
        try:
            log_action(username, "修改密码", "account", "密码修改成功")
        except Exception:
            pass
        return True, "密码修改成功，请重新登录"

    # ── P0 管理员重置密码（2026-06-28）──
    def admin_reset_password(self, username: str, new_password: str) -> tuple:
        """管理员重置任意用户密码，无需旧密码验证，bcrypt 加密存储"""
        self._reload()
        if not new_password or len(new_password) < 6:
            return False, "新密码至少6位"
        user = self._users.get(username)
        if not user:
            return False, f"用户 {username} 不存在"
        user["password"] = hash_password(new_password)
        _save_users(self._users)
        self._sync_user_to_sqlite(username)
        self._trigger_cloud_sync()
        try:
            log_action(username, "管理员重置密码", "admin", "密码已被管理员重置")
        except Exception:
            pass
        return True, f"用户 {username} 密码已重置"

    def get_user_info(self, username: str) -> Optional[dict]:
        self._reload()
        return self._users.get(username)

    def is_admin(self, username: str) -> bool:
        user = self._users.get(username)
        return user is not None and user.get("role") == "admin"
