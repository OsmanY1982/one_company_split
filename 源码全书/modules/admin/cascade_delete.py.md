# `modules/admin/cascade_delete.py`

> 路径：`modules/admin/cascade_delete.py` | 行数：283


---


```python
# -*- coding: utf-8 -*-
"""
级联删除模块
删除用户/产品时自动清理关联数据（订单、会员、财务、设备等）
支持本地 SQLite 数据库和 Supabase 云端数据库的级联删除
"""

import logging
from typing import Dict, Any
from core.database import get_conn

# 尝试导入云端同步（可选）
try:
    from core.simple_sync import push_to_cloud, delete_from_cloud
except ImportError:
    push_to_cloud = None
    delete_from_cloud = None

logger = logging.getLogger(__name__)


# ==================== 本地级联删除 ====================

def delete_user_cascade_local(username: str) -> Dict[str, Any]:
    """
    级联删除用户所有本地数据：
    - users.db 中的用户记录
    - users.db 中的会员记录 (user_memberships)
    - order.db 中的订单记录
    - finance.db 中的财务记录
    - admin.db 中的激活码（bound_account = username）
    返回 {success: bool, deleted: dict, errors: list}
    """
    result = {
        "success": True,
        "deleted": {},
        "errors": []
    }

    try:
        # 1. 删除会员记录
        conn = get_conn("users.db")
        cur = conn.cursor()
        cur.execute("DELETE FROM user_memberships WHERE username = ?", (username,))
        deleted_memberships = cur.rowcount
        conn.commit()
        conn.close()
        result["deleted"]["memberships"] = deleted_memberships
        logger.info(f"已删除 {username} 的 {deleted_memberships} 条会员记录")

    except Exception as e:
        result["errors"].append(f"删除会员记录失败: {str(e)}")
        logger.error(f"删除会员记录失败: {e}")

    try:
        # 2. 删除订单记录
        conn = get_conn("order.db")
        cur = conn.cursor()
        cur.execute("DELETE FROM orders WHERE customer_name = ?", (username,))
        deleted_orders = cur.rowcount
        conn.commit()
        conn.close()
        result["deleted"]["orders"] = deleted_orders
        logger.info(f"已删除 {username} 的 {deleted_orders} 条订单记录")

    except Exception as e:
        result["errors"].append(f"删除订单失败: {str(e)}")
        logger.error(f"删除订单失败: {e}")

    try:
        # 3. 删除财务记录
        conn = get_conn("finance.db")
        cur = conn.cursor()
        # 财务记录可能通过订单号关联，也可能通过描述包含用户名
        cur.execute("DELETE FROM finance WHERE order_no IN (SELECT order_no FROM orders WHERE customer_name = ?)", (username,))
        deleted_finance_by_order = cur.rowcount
        cur.execute("DELETE FROM finance WHERE description LIKE ?", (f"%{username}%",))
        deleted_finance_by_desc = cur.rowcount
        conn.commit()
        conn.close()
        total_finance = deleted_finance_by_order + deleted_finance_by_desc
        result["deleted"]["finance"] = total_finance
        logger.info(f"已删除 {username} 相关的 {total_finance} 条财务记录")

    except Exception as e:
        result["errors"].append(f"删除财务记录失败: {str(e)}")
        logger.error(f"删除财务记录失败: {e}")

    try:
        # 4. 删除激活码绑定
        conn = get_conn("activation_admin.db")
        cur = conn.cursor()
        cur.execute("UPDATE admin_codes SET status='unused', bound_account=NULL, bound_machine=NULL, used_at=NULL WHERE bound_account=?", (username,))
        released_codes = cur.rowcount
        conn.commit()
        conn.close()
        result["deleted"]["activation_codes"] = released_codes
        logger.info(f"已释放 {username} 的 {released_codes} 个激活码")

    except Exception as e:
        result["errors"].append(f"释放激活码失败: {str(e)}")
        logger.error(f"释放激活码失败: {e}")

    try:
        # 5. 删除用户主记录
        conn = get_conn("users.db")
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE username = ?", (username,))
        deleted_user = cur.rowcount
        conn.commit()
        conn.close()
        result["deleted"]["user"] = deleted_user
        logger.info(f"已删除用户 {username}")

    except Exception as e:
        result["errors"].append(f"删除用户失败: {str(e)}")
        logger.error(f"删除用户失败: {e}")

    result["success"] = len(result["errors"]) == 0
    return result


def delete_product_cascade_local(product_name: str) -> Dict[str, Any]:
    """
    级联删除产品所有本地数据：
    - product.db 中的产品记录
    - order.db 中引用该产品的订单
    - finance.db 中关联订单的财务记录
    返回 {success: bool, deleted: dict, errors: list}
    """
    result = {
        "success": True,
        "deleted": {},
        "errors": []
    }

    try:
        # 1. 先查找关联订单
        conn = get_conn("order.db")
        cur = conn.cursor()
        cur.execute("SELECT order_no FROM orders WHERE product_name = ?", (product_name,))
        order_nos = [row[0] for row in cur.fetchall()]
        conn.close()

        # 2. 删除关联的财务记录
        if order_nos:
            conn = get_conn("finance.db")
            cur = conn.cursor()
            for order_no in order_nos:
                cur.execute("DELETE FROM finance WHERE order_no = ?", (order_no,))
            deleted_finance = cur.rowcount
            conn.commit()
            conn.close()
            result["deleted"]["finance"] = deleted_finance
            logger.info(f"已删除 {product_name} 相关的 {deleted_finance} 条财务记录")

    except Exception as e:
        result["errors"].append(f"删除关联财务记录失败: {str(e)}")
        logger.error(f"删除关联财务记录失败: {e}")

    try:
        # 3. 删除订单
        conn = get_conn("order.db")
        cur = conn.cursor()
        cur.execute("DELETE FROM orders WHERE product_name = ?", (product_name,))
        deleted_orders = cur.rowcount
        conn.commit()
        conn.close()
        result["deleted"]["orders"] = deleted_orders
        logger.info(f"已删除 {product_name} 相关的 {deleted_orders} 条订单")

    except Exception as e:
        result["errors"].append(f"删除订单失败: {str(e)}")
        logger.error(f"删除订单失败: {e}")

    try:
        # 4. 删除产品记录
        conn = get_conn("product.db")
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE name = ?", (product_name,))
        deleted_product = cur.rowcount
        conn.commit()
        conn.close()
        result["deleted"]["product"] = deleted_product
        logger.info(f"已删除产品 {product_name}")

    except Exception as e:
        result["errors"].append(f"删除产品失败: {str(e)}")
        logger.error(f"删除产品失败: {e}")

    result["success"] = len(result["errors"]) == 0
    return result


# ==================== 云端级联删除 ====================

def delete_user_cascade_cloud(username: str) -> Dict[str, Any]:
    """
    级联删除用户所有云端数据（Supabase）
    """
    if delete_from_cloud is None:
        return {"success": False, "error": "云端同步模块不可用"}

    result = {"success": True, "tables": {}, "errors": []}

    tables = [
        ("user_memberships", "username"),
        ("orders", "customer_name"),
        ("device_bindings", "username"),
    ]

    for table, column in tables:
        try:
            count = delete_from_cloud(table, column, username)
            result["tables"][table] = count
            logger.info(f"云端 {table} 已删除 {count} 条记录")
        except Exception as e:
            result["errors"].append(f"云端 {table}: {str(e)}")
            logger.error(f"云端删除 {table} 失败: {e}")

    try:
        from core.supabase_client import _request
        ok, _ = _request("DELETE", f"/rest/v1/users?username=eq.{username}", service_key=True)
        if ok:
            result["tables"]["users"] = 1
        else:
            result["errors"].append(f"云端 users: 删除失败")
    except Exception as e:
        result["errors"].append(f"云端 users: {str(e)}")

    result["success"] = len(result["errors"]) == 0
    return result


# ==================== 组合接口 ====================

def delete_user_full(username: str) -> Dict[str, Any]:
    """
    完全删除用户：本地 + 云端
    """
    logger.info(f"开始完全删除用户: {username}")

    local_result = delete_user_cascade_local(username)
    cloud_result = delete_user_cascade_cloud(username)

    return {
        "username": username,
        "local": local_result,
        "cloud": cloud_result,
        "success": local_result["success"] and cloud_result["success"]
    }


def delete_product_full(product_name: str) -> Dict[str, Any]:
    """
    完全删除产品：本地 + 云端
    """
    logger.info(f"开始完全删除产品: {product_name}")

    local_result = delete_product_cascade_local(product_name)

    cloud_result = {"success": True, "tables": {}, "errors": []}
    if delete_from_cloud:
        try:
            count = delete_from_cloud("orders", "product_name", product_name)
            cloud_result["tables"]["orders"] = count
        except Exception as e:
            cloud_result["errors"].append(f"云端 orders: {str(e)}")

        try:
            count = delete_from_cloud("products", "name", product_name)
            cloud_result["tables"]["products"] = count
        except Exception as e:
            cloud_result["errors"].append(f"云端 products: {str(e)}")

    cloud_result["success"] = len(cloud_result["errors"]) == 0

    return {
        "product": product_name,
        "local": local_result,
        "cloud": cloud_result,
        "success": local_result["success"] and cloud_result["success"]
    }

```
