# -*- coding: utf-8 -*-
"""
Supabase 云端同步客户端 - 业务模块：会员 / 订单 / 财务 / 客户 / 产品
"""
from datetime import datetime
from ._core import _request


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
