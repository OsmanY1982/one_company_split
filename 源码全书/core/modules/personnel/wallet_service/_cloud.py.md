# `core/modules/personnel/wallet_service/_cloud.py`

> 路径：`core/modules/personnel/wallet_service/_cloud.py` | 行数：145


---


```python
# -*- coding: utf-8 -*-
"""
钱包云端同步与对账
"""
import os
import sys

# ── 路径：wallet_service/_cloud.py → 项目根目录（4层dirname）──
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _cloud_safe(fn, *args, **kwargs):
    """执行云端操作，失败时静默忽略（不影响本地）"""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        print(f"[CloudWallet] sync failed (non-blocking): {e}")
        return False, str(e)


def _sync_wallet_cloud(wallet: dict):
    """同步钱包到云端"""
    try:
        try:
            from supabase_client import CloudWallet
        except ImportError:
            from core.supabase_client import CloudWallet
        _cloud_safe(
            CloudWallet.upsert,
            user_id=wallet["user_id"],
            balance=wallet.get("balance", 0),
            frozen_amount=wallet.get("frozen_amount", 0),
            total_income=wallet.get("total_income", 0),
            total_withdraw=wallet.get("total_withdraw", 0),
            status=wallet.get("status", "active"),
        )
    except ImportError:
        pass  # core.supabase_client 不可用时跳过


def _sync_txn_cloud(txn: dict):
    """同步交易记录到云端"""
    try:
        try:
            from supabase_client import CloudWalletTxn
        except ImportError:
            from core.supabase_client import CloudWalletTxn
        _cloud_safe(
            CloudWalletTxn.log,
            wallet_id=txn["wallet_id"],
            txn_type=txn["type"],
            amount=txn["amount"],
            balance_after=txn["balance_after"],
            description=txn.get("description", ""),
            created_at=txn.get("created_at"),
        )
    except ImportError:
        pass


def reconcile(local_only: bool = False) -> dict:
    """
    本地与云端对账。
    返回：{in_cloud_not_local, in_local_not_cloud, mismatch, ok}
    """
    # 延迟导入避免循环依赖
    from ._wallet_crud import get_all_wallets

    try:
        try:
            from supabase_client import CloudWallet
        except ImportError:
            from core.supabase_client import CloudWallet
    except ImportError:
        return {
            "ok": False,
            "error": "Supabase 不可用，无法对账",
            "in_cloud_not_local": [],
            "in_local_not_cloud": [],
            "mismatch": [],
        }

    local_wallets = get_all_wallets()
    local_map = {str(w["user_id"]): w for w in local_wallets}

    ok_cloud, cloud_list = CloudWallet.get_recent(limit=1000)
    if not ok_cloud or not cloud_list:
        return {
            "ok": False,
            "error": "无法获取云端数据",
            "in_cloud_not_local": [],
            "in_local_not_cloud": list(local_map.keys()),
            "mismatch": [],
        }

    cloud_map = {str(c.get("user_id", "")): c for c in cloud_list}

    in_cloud_not_local = [
        c["user_id"] for c in cloud_list
        if str(c["user_id"]) not in local_map
    ]
    in_local_not_cloud = [
        uid for uid in local_map if uid not in cloud_map
    ]
    mismatch = []
    for uid, lw in local_map.items():
        if uid in cloud_map:
            cw = cloud_map[uid]
            if abs(float(lw.get("balance", 0)) - float(cw.get("balance", 0))) > 0.01:
                mismatch.append({
                    "user_id": uid,
                    "local_balance": lw.get("balance"),
                    "cloud_balance": cw.get("balance"),
                })

    return {
        "ok": len(mismatch) == 0 and len(in_cloud_not_local) == 0,
        "in_cloud_not_local": in_cloud_not_local,
        "in_local_not_cloud": in_local_not_cloud,
        "mismatch": mismatch,
    }


def force_sync_all_to_cloud() -> dict:
    """强制将所有本地钱包同步到云端（用于修复对账问题）"""
    # 延迟导入避免循环依赖
    from ._wallet_crud import get_all_wallets

    try:
        try:
            from supabase_client import CloudWallet
        except ImportError:
            from core.supabase_client import CloudWallet
    except ImportError:
        return {"ok": False, "error": "Supabase 不可用"}

    wallets = get_all_wallets()
    result = CloudWallet.sync_from_local(wallets)
    return {
        "ok": True,
        "synced": result.get("success", 0),
        "failed": result.get("fail", 0),
    }

```
