# `management-system/core/modules/supabase/wallet.py`

> 路径：`management-system/core/modules/supabase/wallet.py` | 行数：133


---


```python
# -*- coding: utf-8 -*-
"""
Supabase 云端同步客户端 - 钱包 & 交易记录
"""
from ._core import _request


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

```
