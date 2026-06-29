# `planetarium/core/modules/supabase/auth.py`

> 路径：`planetarium/core/modules/supabase/auth.py` | 行数：227


---


```python
# -*- coding: utf-8 -*-
"""
Supabase 云端同步客户端 - 用户管理 & 会话管理
"""
from datetime import datetime
from ._core import _request


class CloudUser:
    """用户云端管理"""

    TABLE = "users"

    @classmethod
    def register(cls, username: str, password_hash: str) -> tuple:
        """云端注册用户"""
        import uuid
        payload = {
            "username": username,
            "user_id": str(uuid.uuid4()),
            "password": password_hash,
            "role": "user",
        }
        ok, result = _request("POST", f"/rest/v1/{cls.TABLE}", payload, service_key=False)
        if ok:
            return True, "注册成功"
        # 处理唯一约束冲突
        msg = str(result)
        if "23505" in msg or "duplicate" in msg.lower() or "already" in msg.lower():
            return False, "账号已存在"
        return False, msg

    @classmethod
    def login(cls, username: str, password: str) -> tuple:
        """云端登录验证"""
        # 先查用户
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?username=eq.{username}&select=*",
            service_key=False
        )
        if not ok or not isinstance(result, list) or len(result) == 0:
            return False, "账号不存在"
        user = result[0]
        stored_password = user.get("password", "")
        if not stored_password:
            return False, "密码错误"
        # 使用 bcrypt.checkpw 验证密码（不能用直接比较，因为每次hash结果不同）
        try:
            import bcrypt
            if not bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                return False, "密码错误"
        except ImportError:
            # 如果 bcrypt 不可用，降级为直接比较（兼容性考虑）
            if stored_password != password:
                return False, "密码错误"
        if not user.get("is_active", True):
            return False, "账号已被禁用"
        # 登录成功：更新 last_login_at（如果列存在）
        try:
            _request(
                "PATCH",
                f"/rest/v1/{cls.TABLE}?username=eq.{username}",
                {"last_login_at": datetime.now().isoformat()},
                service_key=True
            )
        except Exception as e:
            # 如果 last_login_at 列不存在，忽略错误
            if "42703" not in str(e):
                print(f"[CloudUser] 更新 last_login_at 失败: {e}")
        return True, user

    @classmethod
    def update_password(cls, username: str, password_hash: str) -> bool:
        """更新云端用户密码"""
        ok, _ = _request(
            "PATCH",
            f"/rest/v1/{cls.TABLE}?username=eq.{username}",
            {"password": password_hash},
            service_key=True
        )
        return ok

    @classmethod
    def get_info(cls, username: str) -> tuple:
        """获取云端用户信息"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?username=eq.{username}&select=*",
            service_key=False
        )
        if ok and isinstance(result, list) and len(result) > 0:
            return True, result[0]
        return False, None

    @classmethod
    def sync_membership(cls, username: str, membership_type: str,
                        machine_code: str, activation_code: str = None,
                        expires_at: str = None) -> tuple:
        """云端同步用户会员信息"""
        from config.supabase_config import SUPABASE_URL, SUPABASE_SERVICE_KEY

        # 先 upsert 用户
        payload = {
            "username": username,
            "membership_type": membership_type,
            "machine_code": machine_code,
            "activated_at": datetime.now().isoformat(),
            "expires_at": expires_at,
            "activation_code": activation_code
        }
        ok, _ = _request(
            "POST",
            "/rest/v1/user_memberships",
            payload,
            service_key=True
        )
        return ok, "云端会员已同步" if ok else str(_)


class CloudSession:
    """双设备登录管理：同一账号允许 1电脑 + 1手机 同时在线，同类型互踢"""

    TABLE = "device_bindings"

    # 设备类型：desktop / mobile
    DEVICE_TYPE_DESKTOP = "desktop"
    DEVICE_TYPE_MOBILE  = "mobile"

    @classmethod
    def register_login(cls, username: str, device_id: str,
                       device_type: str = "desktop") -> str:
        """
        注册登录会话。返回 session_token。
        规则：
          - 同一账号允许 1台电脑 + 1台手机 同时在线
          - 第2台电脑登录 → 踢掉第1台电脑
          - 第2台手机登录 → 踢掉第1台手机
          - 电脑和手机互不影响
        """
        import uuid
        session_token = uuid.uuid4().hex

        # 1. 踢掉同类型的旧设备（只踢同 type）
        _request(
            "PATCH",
            f"/rest/v1/{cls.TABLE}?username=eq.{username}&machine_code=like.{device_type}*",
            {"is_current": False},
            service_key=True
        )

        # 2. 插入新会话记录（machine_code 存为 "desktop::DEVICE_ID" 或 "mobile::DEVICE_ID"）
        composite_id = f"{device_type}::{device_id}"
        _request(
            "POST",
            f"/rest/v1/{cls.TABLE}",
            {
                "username": username,
                "machine_code": composite_id,
                "is_current": True
            },
            service_key=True
        )

        # 3. 更新 users 表（如果字段存在）
        try:
            _request(
                "PATCH",
                f"/rest/v1/users?username=eq.{username}",
                {"active_session_token": session_token, "active_device_id": composite_id},
                service_key=True
            )
        except Exception:
            pass

        return session_token

    @classmethod
    def check_session(cls, username: str, device_id: str,
                      session_token: str, device_type: str = "desktop") -> bool:
        """
        检查当前会话是否仍然有效。
        只跟同类型的活跃设备比较：电脑只跟电脑比，手机只跟手机比。
        """
        composite_id = f"{device_type}::{device_id}"

        # 查询此用户当前活跃的同类型设备
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?username=eq.{username}"
            f"&is_current=eq.true"
            f"&machine_code=like.{device_type}*"
            f"&select=*&order=last_seen_at.desc&limit=1",
            service_key=True
        )

        if not ok or not isinstance(result, list) or len(result) == 0:
            # 没有同类型活跃记录 → 可能被清理了，重新注册
            cls.register_login(username, device_id, device_type)
            return True

        active_binding = result[0]

        if active_binding.get("machine_code") == composite_id:
            # 同一设备，更新 last_seen_at
            _request(
                "PATCH",
                f"/rest/v1/{cls.TABLE}?id=eq.{active_binding['id']}",
                {"last_seen_at": datetime.now().isoformat()},
                service_key=True
            )
            return True

        # 同类型不同设备 = 被踢了
        return False

    @classmethod
    def logout(cls, username: str, device_id: str,
               device_type: str = "desktop"):
        """用户主动退出时，清除设备绑定"""
        composite_id = f"{device_type}::{device_id}"
        _request(
            "PATCH",
            f"/rest/v1/{cls.TABLE}?username=eq.{username}&machine_code=eq.{composite_id}",
            {"is_current": False},
            service_key=True
        )

```
