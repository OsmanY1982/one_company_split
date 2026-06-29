# -*- coding: utf-8 -*-
"""
Supabase 云端同步客户端 - 分销 & 佣金
"""
from ._core import _request


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
