# -*- coding: utf-8 -*-
"""
Supabase 云端同步客户端 - 激活码管理 & 激活日志
"""
from datetime import datetime
from ._core import _request, SSL_CTX


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
