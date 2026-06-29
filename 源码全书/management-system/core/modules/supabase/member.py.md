# `management-system/core/modules/supabase/member.py`

> 路径：`management-system/core/modules/supabase/member.py` | 行数：78


---


```python
# -*- coding: utf-8 -*-
"""
Supabase 云端同步客户端 - 会员云端同步
"""
from ._core import _request


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

```
