# `modules/auth/auth_service_membership.py`

> 路径：`modules/auth/auth_service_membership.py` | 行数：200


---


```python
import logging

logger = logging.getLogger(__name__)

"""
认证服务 — 会员管理 Mixin
含升级会员、激活码激活、密码重置、会员信息查询
"""
import traceback
import os
import sqlite3
from datetime import datetime, timedelta


class MembershipMixin:
    """会员管理，作为 AuthService 的 Mixin 使用"""

    def upgrade_membership(self, username: str, target_membership: str) -> tuple:
        """
        升级会员
        target_membership: vip / permanent
        返回: (ok: bool, msg: str)
        """
        self._reload()
        user = self._users.get(username)
        if not user:
            return False, "用户不存在"

        current = user.get("membership", self.MEMBERSHIP_TRIAL)

        if target_membership == self.MEMBERSHIP_PERMANENT:
            if current == self.MEMBERSHIP_PERMANENT:
                return False, "已是永久会员，无需升级"
            user["membership"] = self.MEMBERSHIP_PERMANENT
            user["expire_at"] = None
            self._save_users(self._users)
            self._sync_user_to_sqlite(username)
            self._sync_membership_to_sqlite(username)
            self._trigger_cloud_sync()
            try:
                from core.operation_log import log_action
                log_action(username, "升级会员", "membership", "升级为永久会员")
            except Exception:
                logger.exception("异常详情")
            return True, "升级为永久会员成功"

        if target_membership == self.MEMBERSHIP_VIP:
            if current == self.MEMBERSHIP_VIP:
                return False, "已是VIP会员"
            if current == self.MEMBERSHIP_PERMANENT:
                return False, "永久会员无需降级"
            user["membership"] = self.MEMBERSHIP_VIP
            user["expire_at"] = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
            self._save_users(self._users)
            self._sync_user_to_sqlite(username)
            self._sync_membership_to_sqlite(username)
            self._trigger_cloud_sync()
            try:
                from core.operation_log import log_action
                log_action(username, "升级会员", "membership", "升级为VIP会员（有效期1年）")
            except Exception:
                logger.exception("异常详情")
            return True, "升级为VIP会员成功（有效期1年）"

        return False, "未知的会员类型"

    def activate_member(self, username: str, code: str) -> tuple:
        """
        通过激活码升级会员
        返回: (ok: bool, msg: str)
        """
        self._reload()
        user = self._users.get(username)
        if not user:
            return False, "用户不存在"

        if not os.path.exists(self.ACTIVATION_DB):
            return False, "激活码系统未初始化"

        conn = sqlite3.connect(self.ACTIVATION_DB)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM activation WHERE code = ?", (code,)
        ).fetchone()

        if not row:
            conn.close()
            return False, "激活码无效"

        if row["is_used"]:
            conn.close()
            return False, "该激活码已被使用"

        code_type = row["code_type"]
        duration = row["duration_days"]

        if code_type == "永久" or duration >= 9999:
            target = self.MEMBERSHIP_PERMANENT
        elif duration >= 365:
            target = self.MEMBERSHIP_VIP
        elif duration > 0:
            target = self.MEMBERSHIP_VIP
        else:
            conn.close()
            return False, "无效的激活码时长"

        current = user.get("membership", self.MEMBERSHIP_TRIAL)
        if current == self.MEMBERSHIP_PERMANENT:
            conn.close()
            return False, "已是永久会员，无需激活"

        if target == self.MEMBERSHIP_PERMANENT:
            user["membership"] = self.MEMBERSHIP_PERMANENT
            user["expire_at"] = None
        else:
            if current == self.MEMBERSHIP_VIP:
                old_expire = user.get("expire_at")
                if old_expire:
                    try:
                        old_dt = datetime.strptime(old_expire, "%Y-%m-%d %H:%M:%S")
                        new_dt = max(old_dt, datetime.now()) + timedelta(days=duration)
                    except ValueError:
                        new_dt = datetime.now() + timedelta(days=duration)
                else:
                    new_dt = datetime.now() + timedelta(days=duration)
                user["expire_at"] = new_dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                user["membership"] = self.MEMBERSHIP_VIP
                user["expire_at"] = (datetime.now() + timedelta(days=duration)).strftime("%Y-%m-%d %H:%M:%S")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE activation SET is_used = 1, used_by = ?, used_at = ? WHERE code = ?",
            (username, now, code)
        )
        conn.commit()
        conn.close()

        self._save_users(self._users)
        self._sync_user_to_sqlite(username)
        self._sync_membership_to_sqlite(username)
        self._trigger_cloud_sync()
        try:
            from core.operation_log import log_action
            log_action(username, "激活会员", "membership", f"激活码激活，类型={code_type}")
        except Exception:
            logger.exception("异常详情")
        return True, "激活成功"

    def get_membership_info(self, username: str) -> dict:
        """获取会员信息摘要"""
        user = self._users.get(username)
        if not user:
            return {"username": username, "membership": self.MEMBERSHIP_TRIAL, "label": "体验会员",
                    "expire_at": None, "days_left": 0, "role": "member"}

        membership = user.get("membership", self.MEMBERSHIP_TRIAL)
        expire_at = user.get("expire_at")
        days_left = -1

        if expire_at:
            try:
                expire_dt = datetime.strptime(expire_at, "%Y-%m-%d %H:%M:%S")
                delta = (expire_dt - datetime.now()).days
                days_left = max(delta, 0)
            except ValueError:
                days_left = 0

        return {
            "username": username,
            "membership": membership,
            "label": self.MEMBERSHIP_LABELS.get(membership, "体验会员"),
            "expire_at": expire_at,
            "days_left": days_left,
            "role": user.get("role", "member"),
        }

    def admin_reset_password(self, username: str, new_password: str) -> tuple:
        """
        管理员重置用户密码（明文存储）
        返回: (ok: bool, msg: str)
        """
        self._reload()
        user = self._users.get(username)
        if not user:
            return False, "用户不存在"

        if not new_password or len(new_password) < 3:
            return False, "密码至少3个字符"

        user["password"] = new_password
        self._save_users(self._users)
        self._sync_user_to_sqlite(username)
        self._trigger_cloud_sync()
        try:
            from core.operation_log import log_action
            log_action("admin", "重置密码", "admin", f"重置用户 {username} 的密码")
        except Exception:
            logger.exception("异常详情")
        return True, f"用户 {username} 的密码已重置"

```
