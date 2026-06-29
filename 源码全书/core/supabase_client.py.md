# `core/supabase_client.py`

> 路径：`core/supabase_client.py` | 行数：1319


---


```python
# -*- coding: utf-8 -*-
from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
"""
Supabase 云端同步客户端
负责与 Supabase 后端通信：激活码管理、用户注册/激活、云端数据同步
"""
import sys, os
# BASE_DIR 由 core.paths 统一定义，不再重复定义

import json
import socket
import sqlite3
import hashlib
import threading
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
import ssl

from config.supabase_config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY

# ── 全局 SSL 上下文 ──
# 默认启用证书验证，仅在内网/测试环境禁用
SSL_VERIFY = os.environ.get("SUPABASE_SSL_VERIFY", "true").lower() == "true"
SSL_CTX = ssl.create_default_context()
if not SSL_VERIFY:
    SSL_CTX.check_hostname = False
    SSL_CTX.verify_mode = ssl.CERT_NONE


# ══════════════════════════════════════════════════════
#  HTTP 基础请求
# ══════════════════════════════════════════════════════
# ── DNS 预检缓存 ──
_dns_reachable = None  # None=未检, True=可达, False=不可达


def _dns_precheck():
    """快速 DNS 预检：用独立线程 + 3秒 join 超时判断 SUPABASE_URL 主机名是否可达。
    结果缓存到 _dns_reachable，避免每次 _request 都重复解析。
    """
    global _dns_reachable
    if _dns_reachable is not None:
        return _dns_reachable
    try:
        hostname = urlparse(SUPABASE_URL).hostname
        if not hostname:
            _dns_reachable = False
            return False

        result = {"ok": False}

        def _resolve():
            try:
                socket.getaddrinfo(hostname, None)
                result["ok"] = True
            except Exception:
                pass

        t = threading.Thread(target=_resolve, daemon=True)
        t.start()
        t.join(timeout=3)
        _dns_reachable = result["ok"]
    except Exception:
        _dns_reachable = False
    return _dns_reachable


def _request(method, path, data=None, service_key=False, prefer="return=representation"):
    """统一 HTTP 请求
    
    prefer: Prefer header value. Use 'resolution=merge-duplicates' for upsert.
    """
    # 快速 DNS 预检：域名不可达时直接短路，避免 urlopen 漫长的 DNS 超时阻塞
    if not _dns_precheck():
        return False, {"error": "dns_unreachable"}

    url = f"{SUPABASE_URL}{path}"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY if service_key else SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY if service_key else SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": prefer
    }
    body = json.dumps(data, ensure_ascii=False).encode() if data else None
    try:
        req = Request(url, data=body, headers=headers, method=method)
        with urlopen(req, context=SSL_CTX, timeout=15) as resp:
            raw = resp.read()
            if not raw:
                return True, {}
            result = json.loads(raw.decode())
            # Supabase 返回格式：{"data": [...]} 或单个对象
            return True, result
    except HTTPError as e:
        try:
            err_body = json.loads(e.read().decode())
            return False, err_body
        except Exception:
            return False, {"message": f"HTTP {e.code}: {e.reason}"}
    except URLError as e:
        return False, {"message": f"网络错误：{e.reason}"}
    except Exception as e:
        return False, {"message": str(e)}


# ══════════════════════════════════════════════════════
#  激活码云端操作
# ══════════════════════════════════════════════════════
class CloudActivation:
    """激活码云端管理"""

    TABLE = "activation_codes"

    @classmethod
    def upload_code(cls, code_display: str, user_type: str, created_by: str = "admin",
                     expires_at: str = None, note: str = "") -> tuple:
        """
        上传激活码到云端
        code_display: 带格式（如 PRO-ABCD-1234-EFGH）
        返回 (bool, message)
        """
        code_normal = code_display.upper().replace("-", "").replace(" ", "")
        payload = {
            "code": code_normal,
            "code_display": code_display,
            "user_type": user_type,
            "status": "unused",
            "created_by": created_by,
            "note": note,
            "expires_at": expires_at
        }
        ok, result = _request("POST", f"/rest/v1/{cls.TABLE}", payload, service_key=True)
        if ok:
            return True, f"已同步到云端"
        # 可能是重复键（412），转成更新
        if isinstance(result, dict) and "message" in result and "duplicate" in result.get("message", "").lower():
            return cls._upsert_code(code_normal, code_display, user_type, created_by, expires_at, note)
        return False, str(result)

    @classmethod
    def _upsert_code(cls, code_normal, code_display, user_type, created_by, expires_at, note):
        ok, result = _request(
            "PATCH",
            f"/rest/v1/{cls.TABLE}?code=eq.{code_normal}",
            {"status": "unused", "code_display": code_display,
             "user_type": user_type, "created_by": created_by,
             "note": note, "expires_at": expires_at, "used_at": None},
            service_key=True
        )
        return ok, "云端已更新" if ok else str(result)

    @classmethod
    def upload_batch(cls, codes: list) -> tuple:
        """批量上传激活码"""
        records = []
        for item in codes:
            code_normal = item["code_display"].upper().replace("-", "").replace(" ", "")
            records.append({
                "code": code_normal,
                "code_display": item["code_display"],
                "user_type": item["user_type"],
                "status": "unused",
                "created_by": item.get("created_by", "admin"),
                "note": item.get("note", ""),
                "expires_at": item.get("expires_at")
            })
        ok, result = _request("POST", f"/rest/v1/{cls.TABLE}", records, service_key=True)
        return ok, result

    @classmethod
    def check_code(cls, code: str) -> dict:
        """查询激活码在云端的状态"""
        code_normal = code.upper().replace("-", "").replace(" ", "")
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?code=eq.{code_normal}&select=*",
            service_key=False
        )
        if ok and isinstance(result, list) and len(result) > 0:
            return result[0]
        return None

    @classmethod
    def use_code(cls, code: str, username: str, machine_code: str) -> tuple:
        """
        云端核销激活码（用户激活时调用）
        返回 (bool, message)
        """
        code_normal = code.upper().replace("-", "").replace(" ", "")
        # 先查当前状态
        existing = cls.check_code(code)
        if existing and existing.get("status") == "used" and existing.get("bound_account"):
            if existing["bound_account"] != username:
                return False, f"激活码已被账号 {existing['bound_account']} 使用"

        payload = {
            "status": "used",
            "bound_account": username,
            "bound_machine": machine_code,
            "used_at": datetime.now().isoformat()
        }
        ok, result = _request(
            "PATCH",
            f"/rest/v1/{cls.TABLE}?code=eq.{code_normal}",
            payload,
            service_key=True
        )
        if ok:
            return True, "云端核销成功"
        return False, str(result)

    @classmethod
    def get_all_codes(cls, status_filter: str = None) -> list:
        """获取云端所有激活码"""
        filters = "status=eq.used" if status_filter == "used" else ""
        if status_filter == "unused":
            filters = "status=eq.unused"
        path = f"/rest/v1/{cls.TABLE}?select=*"
        if filters:
            path += f"&{filters}"
        path += "&order=created_at.desc"
        ok, result = _request("GET", path, service_key=True)
        if ok and isinstance(result, list):
            return result
        return []

    @classmethod
    def delete_code(cls, code: str) -> tuple:
        """云端删除激活码"""
        code_normal = code.upper().replace("-", "").replace(" ", "")
        ok, result = _request(
            "DELETE",
            f"/rest/v1/{cls.TABLE}?code=eq.{code_normal}",
            service_key=True
        )
        return ok, "已删除" if ok else str(result)

    @classmethod
    def sync_code(cls, code: str, code_type: str = None, status: str = None,
                   bound_account: str = None, bound_machine: str = None,
                   created_at: str = None, expires_at: str = None) -> tuple:
        """
        同步本地激活码到云端（存在则更新，不存在则插入）
        返回 (bool, message)
        """
        import json
        code_normal = code.upper().replace("-", "").replace(" ", "")
        payload = {
            "code": code_normal,
            "code_display": code,
            "user_type": code_type or "pro",
            "status": status or "unused",
        }
        if bound_account:
            payload["bound_account"] = bound_account
        if bound_machine:
            payload["bound_machine"] = bound_machine
        if expires_at:
            payload["expires_at"] = expires_at

        # 先查是否存在
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?code=eq.{code_normal}&select=id",
            service_key=True
        )
        if ok and isinstance(result, list) and len(result) > 0:
            # 存在 → 更新
            ok2, result2 = _request(
                "PATCH",
                f"/rest/v1/{cls.TABLE}?code=eq.{code_normal}",
                payload,
                service_key=True
            )
            return ok2, "云端已更新" if ok2 else str(result2)
        else:
            # 不存在 → 插入
            payload["created_by"] = "admin"
            ok2, result2 = _request(
                "POST",
                f"/rest/v1/{cls.TABLE}",
                payload,
                service_key=True
            )
            return ok2, "云端已新增" if ok2 else str(result2)

    @classmethod
    def unbind_device(cls, code: str) -> tuple:
        """
        云端解绑设备
        返回 (bool, message)
        """
        code_normal = code.upper().replace("-", "").replace(" ", "")
        payload = {
            "bound_machine": "",
            "bound_account": None
        }
        ok, result = _request(
            "PATCH",
            f"/rest/v1/{cls.TABLE}?code=eq.{code_normal}",
            payload,
            service_key=True
        )
        return ok, "云端已解绑" if ok else str(result)


# ══════════════════════════════════════════════════════
#  用户云端操作
# ══════════════════════════════════════════════════════
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


# ══════════════════════════════════════════════════════
#  激活日志
# ══════════════════════════════════════════════════════
class CloudLog:
    """激活日志云端写入"""

    TABLE = "activation_logs"

    @classmethod
    def log(cls, username: str, machine_code: str, activation_code: str,
            action: str, result: str, detail: str = "", ip_address: str = "") -> bool:
        payload = {
            "username": username,
            "machine_code": machine_code,
            "activation_code": activation_code,
            "action": action,
            "result": result,
            "detail": detail,
            "ip_address": ip_address
        }
        ok, _ = _request("POST", f"/rest/v1/{cls.TABLE}", payload, service_key=True)
        return ok


# ══════════════════════════════════════════════════════
#  APP 版本更新检查
# ══════════════════════════════════════════════════════
class UpdateChecker:
    """从云端 Storage 检查 APP 更新（读 version.json）"""

    VERSION_URL = f"{SUPABASE_URL}/storage/v1/object/public/updates/version.json"

    @classmethod
    def get_latest(cls) -> dict:
        """
        获取最新版本信息
        返回: {latest_version, download_url, release_notes, released_at, file_size, file_hash, min_version} 或 None
        """
        try:
            req = Request(cls.VERSION_URL, method="GET")
            with urlopen(req, context=SSL_CTX, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                return data
        except Exception as e:
            print(f"[UpdateChecker] get_latest failed: {e}")
            return None

    @classmethod
    def compare_version(cls, current: str, latest: str) -> bool:
        """
        比较版本号，返回 True 表示有新版本
        支持格式: 1.0.0, 2.0.1, 2.1.0 等
        """
        def parse(v):
            parts = v.lstrip("vV").split(".")
            return tuple(int(p) for p in parts if p.isdigit())
        try:
            return parse(latest) > parse(current)
        except Exception:
            return False

    @classmethod
    def check_update(cls, current_version: str) -> dict:
        """
        检查更新，返回 {has_update, version, download_url, changelog}
        """
        data = cls.get_latest()
        if not data:
            return {"has_update": False}

        latest = data.get("latest_version", "")
        has_update = cls.compare_version(current_version, latest)

        # 选择下载链接：优先 Gitee（直链），备选百度网盘
        downloads = data.get("downloads", {})
        win = downloads.get("windows", {})
        download_url = win.get("gitee", "") or win.get("baidu", "")

        return {
            "has_update": has_update,
            "version": latest,
            "download_url": download_url,
            "changelog": data.get("release_notes", "")
        }


# ══════════════════════════════════════════════════════
#  会话管理（双设备登录：1电脑+1手机）
# ══════════════════════════════════════════════════════
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


# ══════════════════════════════════════════════════════
#  用户云端状态检查
# ══════════════════════════════════════════════════════
def check_user_cloud_status(username: str) -> tuple:
    """
    检查用户是否仍在云端存在（用户被管理员删除 → 云端查无此人）
    Returns: (ok, exists)
      - ok:      API 调用是否成功（网络通不通）
      - exists:  用户是否还存在云端 (True / False / None=未知)
    """
    # 1. 查 users 表
    ok1, result1 = _request("GET", f"/rest/v1/users?username=eq.{username}&select=id")
    if ok1 and isinstance(result1, list) and len(result1) > 0:
        return True, True

    # 2. 查 user_memberships 表（可能用户记录在这里）
    ok2, result2 = _request("GET", f"/rest/v1/user_memberships?username=eq.{username}&select=id")
    if ok2 and isinstance(result2, list) and len(result2) > 0:
        return True, True

    # 两个表都没找到此用户
    if ok1 or ok2:
        return True, False   # 至少一次查询成功 → 确认用户不存在
    return False, None      # 两次都失败（网络错误）


# ══════════════════════════════════════════════════════
#  云端连接测试
# ══════════════════════════════════════════════════════
def test_connection() -> tuple:
    """测试 Supabase 连接是否正常"""
    ok, result = _request("GET", "/rest/v1/activation_codes?select=id&limit=1", service_key=True)
    if ok:
        return True, "✅ 云端连接正常"
    return False, f"❌ 云端连接失败：{result.get('message', result)}"


# ══════════════════════════════════════════════════════
#  CloudMembership - 会员云端管理
# ══════════════════════════════════════════════════════
class CloudMembership:
    TABLE = "user_memberships"

    @classmethod
    def upsert(cls, username: str, membership_type: str, machine_code: str = None,
               activation_code: str = None, expires_at: str = None) -> tuple:
        """写入或更新用户会员信息（upsert by username）"""
        payload = {
            "username": username,
            "membership_type": membership_type,
        }
        if machine_code:
            payload["machine_code"] = machine_code
        if activation_code:
            payload["activation_code"] = activation_code
        if expires_at:
            payload["expires_at"] = expires_at
        if expires_at is None and membership_type in ("PRO", "VIP"):
            # 永久会员expires_at为None
            payload["expires_at"] = None

        ok, result = _request("POST", f"/rest/v1/{cls.TABLE}", payload, service_key=True)
        return ok, result

    @classmethod
    def get(cls, username: str) -> tuple:
        """查询用户会员信息"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?username=eq.{username}&select=*",
            service_key=True
        )
        if ok and isinstance(result, list) and len(result) > 0:
            return True, result[0]
        return False, None


# ══════════════════════════════════════════════════════
#  CloudOrder - 订单云端管理
# ══════════════════════════════════════════════════════
class CloudOrder:
    TABLE = "orders"

    @classmethod
    def create(cls, order_no: str, customer: str, product: str,
               amount: float, quantity: int = 1, status: str = "已完成",
               sync_version: int = 1, last_modified_by: str = "desktop") -> tuple:
        """创建云端订单记录"""
        payload = {
            "order_no": order_no,
            "customer": customer,
            "product": product,
            "total_price": amount,
            "quantity": quantity,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "sync_version": sync_version,
            "last_modified_by": last_modified_by,
        }
        ok, result = _request("POST", f"/rest/v1/{cls.TABLE}", payload, service_key=True)
        if ok:
            return True, "订单已同步云端"
        # 忽略唯一约束冲突（订单号已存在）
        if "23505" in str(result) or "duplicate" in str(result).lower():
            return True, "订单已存在"
        return False, str(result)

    @classmethod
    def upsert(cls, order_no: str, customer: str, product: str,
               amount: float, quantity: float = 1, status: str = "pending",
               created_at: str = None, updated_at: str = None,
               sync_version: int = 1, last_modified_by: str = "desktop") -> tuple:
        """更新或插入云端订单记录"""
        payload = {
            "order_no": order_no,
            "customer": customer,
            "product": product,
            "total_price": amount,
            "quantity": quantity,
            "status": status,
            "sync_version": sync_version,
            "last_modified_by": last_modified_by,
            "last_sync_at": updated_at or datetime.now().isoformat(),
        }
        if created_at:
            payload["created_at"] = created_at
        
        # 使用 upsert（存在则更新，不存在则插入）
        ok, result = _request(
            "POST",
            f"/rest/v1/{cls.TABLE}",
            payload,
            service_key=True,
            prefer="resolution=merge-duplicates"
        )
        if ok:
            return True, "订单已同步云端"
        # 忽略唯一约束冲突
        if "23505" in str(result) or "duplicate" in str(result).lower():
            return True, "订单已存在"
        return False, str(result)

    @classmethod
    def list(cls, limit: int = 50) -> tuple:
        """查询最近订单"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?order=created_at.desc&limit={limit}",
            service_key=True
        )
        return ok, result if ok else []


# ══════════════════════════════════════════════════════
#  CloudFinance - 财务云端管理
# ══════════════════════════════════════════════════════
class CloudFinance:
    TABLE = "finance"

    @classmethod
    def create(cls, date: str, type_: str, category: str,
               amount: float, note: str = None) -> tuple:
        """创建云端财务记录"""
        payload = {
            "date": date,
            "type": type_,
            "category": category,
            "amount": amount,
        }
        if note:
            payload["note"] = note
        ok, result = _request("POST", f"/rest/v1/{cls.TABLE}", payload, service_key=True)
        if ok:
            return True, "财务记录已同步云端"
        return False, str(result)

    @classmethod
    def list(cls, type_: str = None, limit: int = 50) -> tuple:
        """查询财务记录"""
        url = f"/rest/v1/{cls.TABLE}?order=date.desc&limit={limit}"
        if type_:
            url = f"/rest/v1/{cls.TABLE}?type=eq.{type_}&order=date.desc&limit={limit}"
        ok, result = _request("GET", url, service_key=True)
        return ok, result if ok else []

    @classmethod
    def get_stats(cls) -> tuple:
        """获取收入/支出统计"""
        ok, result = _request(
            f"""SELECT type, SUM(amount) as total FROM {cls.TABLE} GROUP BY type""",
            service_key=True
        )
        if not ok:
            return False, {"收入": 0, "支出": 0}
        stats = {}
        for row in result:
            stats[row.get("type", "")] = row.get("total", 0)
        return True, stats


# ══════════════════════════════════════════════
#  钱包云端同步
# ══════════════════════════════════════════════


class CloudWallet:
    """钱包云端同步"""
    TABLE = "wallets"

    @classmethod
    def upsert(cls, user_id: str, balance: float, frozen_amount: float = 0,
               total_income: float = 0, total_withdraw: float = 0,
               status: str = "active") -> tuple:
        """
        创建或更新云端钱包记录（upsert）。
        返回 (ok, message_or_data)
        """
        payload = {
            "user_id": str(user_id),
            "balance": balance,
            "frozen_amount": frozen_amount,
            "total_income": total_income,
            "total_withdraw": total_withdraw,
            "status": status,
        }
        ok, result = _request(
            "POST",
            f"/rest/v1/{cls.TABLE}?on_conflict=user_id",
            payload,
            service_key=True,
            prefer="resolution=merge-duplicates",
        )
        if not ok:
            return False, str(result)
        return True, "钱包已同步云端"

    @classmethod
    def get(cls, user_id: str) -> tuple:
        """获取云端钱包"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?user_id=eq.{user_id}&select=*",
            service_key=True,
        )
        if not ok or not result:
            return False, None
        return True, result[0] if isinstance(result, list) else result

    @classmethod
    def get_recent(cls, limit: int = 100) -> tuple:
        """获取云端钱包列表（按 ID 倒序）"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?order=id.desc&limit={limit}",
            service_key=True,
        )
        if not ok or not result:
            return False, []
        return True, result if isinstance(result, list) else []

    @classmethod
    def delete(cls, user_id: str) -> tuple:
        """删除云端钱包（慎用）"""
        ok, result = _request(
            "DELETE",
            f"/rest/v1/{cls.TABLE}?user_id=eq.{user_id}",
            service_key=True,
        )
        if ok:
            return True, "已从云端删除"
        return False, str(result)

    @classmethod
    def sync_from_local(cls, wallets: list[dict]) -> dict:
        """
        批量同步本地钱包到云端（用于手动对账）。
        wallets: [{user_id, balance, frozen_amount, total_income, total_withdraw, status}, ...]
        返回 {success_count, fail_count}
        """
        success = fail = 0
        for w in wallets:
            ok, _ = cls.upsert(
                user_id=w["user_id"],
                balance=w.get("balance", 0),
                frozen_amount=w.get("frozen_amount", 0),
                total_income=w.get("total_income", 0),
                total_withdraw=w.get("total_withdraw", 0),
                status=w.get("status", "active"),
            )
            if ok:
                success += 1
            else:
                fail += 1
        return {"success": success, "fail": fail}


class CloudWalletTxn:
    """钱包交易记录云端同步"""
    TABLE = "wallet_transactions"

    @classmethod
    def log(cls, wallet_id: int, txn_type: str, amount: float,
            balance_after: float, description: str = "",
            created_at: str = None) -> tuple:
        """
        同步一条交易记录到云端。
        """
        payload = {
            "wallet_id": wallet_id,
            "type": txn_type,
            "amount": amount,
            "balance_after": balance_after,
            "description": description,
        }
        if created_at:
            payload["created_at"] = created_at
        ok, result = _request(
            "POST", f"/rest/v1/{cls.TABLE}", payload, service_key=True
        )
        if not ok:
            return False, str(result)
        return True, "交易已同步云端"

    @classmethod
    def get_recent(cls, user_id: str = None, limit: int = 50) -> tuple:
        """查询云端交易记录"""
        url = f"/rest/v1/{cls.TABLE}?order=id.desc&limit={limit}"
        ok, result = _request("GET", url, service_key=True)
        if not ok:
            return False, []
        return True, result if isinstance(result, list) else []


# ══════════════════════════════════════════════════════
#  CloudCustomer - 客户云端同步（新增）
# ══════════════════════════════════════════════════════
class CloudCustomer:
    """客户云端同步"""
    TABLE = "customers"

    @classmethod
    def upsert(cls, name: str, phone: str = None, email: str = None,
               address: str = None, company: str = None,
               level: str = "普通", note: str = None) -> tuple:
        """创建或更新云端客户记录"""
        payload = {"name": name}
        if phone: payload["phone"] = phone
        if email: payload["email"] = email
        if address: payload["address"] = address
        if company: payload["company"] = company
        if level: payload["level"] = level
        if note: payload["note"] = note

        ok, result = _request(
            "POST",
            f"/rest/v1/{cls.TABLE}?on_conflict=name",
            payload,
            service_key=True,
            prefer="resolution=merge-duplicates",
        )
        if not ok:
            return False, str(result)
        return True, "客户已同步云端"

    @classmethod
    def get(cls, name: str) -> tuple:
        """获取云端客户"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?name=eq.{name}&select=*",
            service_key=True,
        )
        if not ok or not result:
            return False, None
        return True, result[0] if isinstance(result, list) else result

    @classmethod
    def get_recent(cls, limit: int = 100) -> tuple:
        """获取云端客户列表"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?order=id.desc&limit={limit}",
            service_key=True,
        )
        if not ok or not result:
            return False, []
        return True, result if isinstance(result, list) else []

    @classmethod
    def delete(cls, name: str) -> tuple:
        """删除云端客户"""
        ok, result = _request(
            "DELETE",
            f"/rest/v1/{cls.TABLE}?name=eq.{name}",
            service_key=True,
        )
        if ok:
            return True, "已从云端删除"
        return False, str(result)


# ══════════════════════════════════════════════════════
#  CloudDistribution - 分销云端同步（新增）
# ══════════════════════════════════════════════════════
class CloudDistribution:
    """分销链接云端同步"""
    TABLE = "distribution_links"

    @classmethod
    def upsert(cls, user_id: int, code: str, url: str = None,
               click_count: int = 0, register_count: int = 0,
               total_commission: float = 0, status: str = "active") -> tuple:
        """创建或更新云端分销链接"""
        payload = {
            "user_id": user_id,
            "code": code,
            "click_count": click_count,
            "register_count": register_count,
            "total_commission": total_commission,
            "status": status,
        }
        if url: payload["url"] = url

        ok, result = _request(
            "POST",
            f"/rest/v1/{cls.TABLE}?on_conflict=code",
            payload,
            service_key=True,
            prefer="resolution=merge-duplicates",
        )
        if not ok:
            return False, str(result)
        return True, "分销链接已同步云端"

    @classmethod
    def get(cls, code: str) -> tuple:
        """获取云端分销链接"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?code=eq.{code}&select=*",
            service_key=True,
        )
        if not ok or not result:
            return False, None
        return True, result[0] if isinstance(result, list) else result

    @classmethod
    def get_recent(cls, limit: int = 100) -> tuple:
        """获取云端分销链接列表"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?order=id.desc&limit={limit}",
            service_key=True,
        )
        if not ok or not result:
            return False, []
        return True, result if isinstance(result, list) else []


# ══════════════════════════════════════════════════════
#  CloudCommission - 佣金云端同步（新增）
# ══════════════════════════════════════════════════════
class CloudCommission:
    """佣金记录云端同步"""
    TABLE = "commissions"

    @classmethod
    def upsert(cls, user_id: int, amount: float, from_user_id: int = None,
               type_: str = None, status: str = "pending",
               description: str = None) -> tuple:
        """创建或更新云端佣金记录"""
        payload = {
            "user_id": user_id,
            "amount": amount,
            "status": status,
        }
        if from_user_id: payload["from_user_id"] = from_user_id
        if type_: payload["type"] = type_
        if description: payload["description"] = description

        ok, result = _request(
            "POST",
            f"/rest/v1/{cls.TABLE}",
            payload,
            service_key=True,
        )
        if not ok:
            return False, str(result)
        return True, "佣金已同步云端"

    @classmethod
    def get_recent(cls, limit: int = 100) -> tuple:
        """获取云端佣金列表"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?order=id.desc&limit={limit}",
            service_key=True,
        )
        if not ok or not result:
            return False, []
        return True, result if isinstance(result, list) else []


# ══════════════════════════════════════════════════════
#  CloudProduct - 产品云端同步（新增）
# ══════════════════════════════════════════════════════
class CloudProduct:
    """产品云端同步"""
    TABLE = "products"

    @classmethod
    def upsert(cls, id: int, name: str = None, specs: str = None,
               category: str = None, unit_price: float = 0,
               stock: int = 0, status: str = "上架",
               note: str = None, created_at: str = None,
               updated_at: str = None) -> tuple:
        """创建或更新云端产品"""
        payload = {
            "id": id,
            "name": name or "",
            "unit_price": unit_price,
            "stock": stock,
            "status": status,
        }
        if specs: payload["specs"] = specs
        if category: payload["category"] = category
        if note: payload["note"] = note
        if created_at: payload["created_at"] = created_at
        if updated_at: payload["updated_at"] = updated_at

        ok, result = _request(
            "POST",
            f"/rest/v1/{cls.TABLE}?on_conflict=id",
            payload,
            service_key=True,
            prefer="resolution=merge-duplicates",
        )
        if not ok:
            return False, str(result)
        return True, "产品已同步云端"

    @classmethod
    def get(cls, product_id: int) -> tuple:
        """获取云端产品"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?id=eq.{product_id}&select=*",
            service_key=True,
        )
        if not ok or not result:
            return False, None
        return True, result[0] if isinstance(result, list) else result

    @classmethod
    def get_recent(cls, limit: int = 100) -> tuple:
        """获取云端产品列表"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?order=id.desc&limit={limit}",
            service_key=True,
        )
        if not ok or not result:
            return False, []
        return True, result if isinstance(result, list) else []

    @classmethod
    def delete(cls, product_id: int) -> tuple:
        """删除云端产品"""
        ok, result = _request(
            "DELETE",
            f"/rest/v1/{cls.TABLE}?id=eq.{product_id}",
            service_key=True,
        )
        if not ok:
            return False, str(result)
        return True, "云端产品已删除"


# ══════════════════════════════════════════════════════
#  CloudMember - 会员云端同步（新增）
# ══════════════════════════════════════════════════════
class CloudMember:
    """会员云端同步"""
    TABLE = "members"

    @classmethod
    def upsert(cls, id: int, name: str = None, phone: str = None,
               email: str = None, level: str = "体验", points: int = 0,
               rights: str = None, vip_expire: str = None,
               status: str = "正常", created_at: str = None,
               updated_at: str = None) -> tuple:
        """创建或更新云端会员"""
        payload = {
            "id": id,
            "name": name or "",
            "level": level,
            "points": points,
            "status": status,
        }
        if phone: payload["phone"] = phone
        if email: payload["email"] = email
        if rights: payload["rights"] = rights
        if vip_expire: payload["vip_expire"] = vip_expire
        if created_at: payload["created_at"] = created_at
        if updated_at: payload["updated_at"] = updated_at

        ok, result = _request(
            "POST",
            f"/rest/v1/{cls.TABLE}?on_conflict=id",
            payload,
            service_key=True,
            prefer="resolution=merge-duplicates",
        )
        if not ok:
            return False, str(result)
        return True, "会员已同步云端"

    @classmethod
    def get(cls, member_id: int) -> tuple:
        """获取云端会员"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?id=eq.{member_id}&select=*",
            service_key=True,
        )
        if not ok or not result:
            return False, None
        return True, result[0] if isinstance(result, list) else result

    @classmethod
    def get_recent(cls, limit: int = 100) -> tuple:
        """获取云端会员列表"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?order=id.desc&limit={limit}",
            service_key=True,
        )
        if not ok or not result:
            return False, []
        return True, result if isinstance(result, list) else []

    @classmethod
    def delete(cls, member_id: int) -> tuple:
        """删除云端会员"""
        ok, result = _request(
            "DELETE",
            f"/rest/v1/{cls.TABLE}?id=eq.{member_id}",
            service_key=True,
        )
        if not ok:
            return False, str(result)
        return True, "云端会员已删除"


# ══════════════════════════════════════════════════════
#  CloudAdminLog - 管理日志云端同步（新增）
# ══════════════════════════════════════════════════════
class CloudAdminLog:
    """管理日志云端同步"""
    TABLE = "admin_logs"

    @classmethod
    def upsert(cls, id: int, admin_user: str, action: str,
               target: str = None, details: str = None,
               ip_address: str = None, created_at: str = None) -> tuple:
        """创建或更新云端管理日志"""
        payload = {
            "id": id,
            "admin_user": admin_user or "",
            "action": action or "",
        }
        if target: payload["target"] = target
        if details: payload["details"] = details
        if ip_address: payload["ip_address"] = ip_address
        if created_at: payload["created_at"] = created_at

        ok, result = _request(
            "POST",
            f"/rest/v1/{cls.TABLE}?on_conflict=id",
            payload,
            service_key=True,
            prefer="resolution=merge-duplicates",
        )
        if not ok:
            return False, str(result)
        return True, "管理日志已同步云端"

    @classmethod
    def get_recent(cls, limit: int = 100) -> tuple:
        """获取云端管理日志列表"""
        ok, result = _request(
            "GET",
            f"/rest/v1/{cls.TABLE}?order=id.desc&limit={limit}",
            service_key=True,
        )
        if not ok or not result:
            return False, []
        return True, result if isinstance(result, list) else []

```
