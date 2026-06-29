# `management-system/core/modules/supabase/admin_log.py`

> 路径：`management-system/core/modules/supabase/admin_log.py` | 行数：48


---


```python
# -*- coding: utf-8 -*-
"""
Supabase 云端同步客户端 - 管理日志云端同步
"""
from ._core import _request


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
