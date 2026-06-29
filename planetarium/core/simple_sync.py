#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版三端同步
规则：任何一端增删改 → 云端同步 → 其他端登录后自动同步
"""

import sqlite3
import json
import logging
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
sys.path.insert(0, BASE_DIR)

from core.supabase_client import _request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 表映射：云端表名 → {本地数据库, 本地表名}
# 2026-06-01 更新：新增 withdrawal_queue, user_memberships 等表
TABLE_MAP = {
    "customers":     {"db": "customer.db", "table": "customer"},
    "finance":       {"db": "finance.db", "table": "finance"},
    "staff":         {"db": "staff.db", "table": "staff"},
    "products":      {"db": "product.db", "table": "products"},
    "orders":        {"db": "order.db", "table": "orders"},
    "users":         {"db": "users.db", "table": "users"},
    "wallet":        {"db": "wallet.db", "table": "wallet"},
    "activation_codes": {"db": "activation_admin.db", "table": "admin_codes"},
    "wallet_transactions": {"db": "wallet.db", "table": "wallet_transactions"},
    "distribution_links": {"db": "distribution.db", "table": "distribution_links"},
    "commissions":   {"db": "distribution.db", "table": "commissions"},
    "team_members":  {"db": "distribution.db", "table": "team_members"},
    "withdrawal_queue": {"db": "wallet.db", "table": "withdrawal_queue"},
    "user_memberships": {"db": "users.db", "table": "user_memberships"},
}


def get_conn(table_name):
    """获取本地数据库连接"""
    meta = TABLE_MAP.get(table_name)
    if not meta:
        return None, None
    db_path = os.path.join(DATA_DIR, meta["db"])
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn, meta["table"]


def push_to_cloud(table_name):
    """推送本地数据到云端（全量推送，覆盖云端）"""
    conn, local_table = get_conn(table_name)
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {local_table}")
        rows = cursor.fetchall()
        
        if not rows:
            logger.info(f"[{table_name}] 本地无数据")
            return True
        
        # 获取本地表字段
        cursor.execute(f"PRAGMA table_info({local_table})")
        columns = [row[1] for row in cursor.fetchall()]
        
        # 先清空云端表
        ok, _ = _request("DELETE", f"/rest/v1/{table_name}?id=not.is.null", service_key=True)
        if not ok:
            logger.warning(f"[{table_name}] 清空云端表失败，尝试直接插入")
        
        # 批量插入云端（只包含云端存在的字段）
        success_count = 0
        for row in rows:
            row_dict = dict(row)
            # 移除本地特有字段
            row_dict.pop('sync_version', None)
            row_dict.pop('last_modified_by', None)
            row_dict.pop('last_modified_at', None)
            row_dict.pop('sync_checksum', None)
            row_dict.pop('last_sync_at', None)
            
            # 移除本地 id 字段（云端使用 UUID，自动生成）
            row_dict.pop('id', None)
            
            # 移除云端不存在的字段（根据错误信息动态调整）
            # 这些字段在云端 schema 中不存在
            cloud_only_fields = {
                'customers': ['last_sync_at', 'total_spent', 'sync_version', 'last_modified_by', 'last_modified_at', 'sync_checksum'],
                'finance': ['last_sync_at', 'sync_version', 'last_modified_by', 'last_modified_at', 'sync_checksum'],
                'staff': ['hire_date', 'updated_at', 'sync_version', 'last_modified_by', 'last_sync_at', 'last_modified_at', 'sync_checksum'],
                'products': ['cost', 'unit', 'updated_at', 'cost_price', 'description', 'min_stock', 'price', 'sync_version', 'last_modified_by', 'last_sync_at', 'last_modified_at', 'sync_checksum', 'status', 'specs'],
                'orders': ['amount', 'note', 'updated_at', 'sync_version', 'last_modified_by', 'last_sync_at'],
                'users': ['is_admin', 'updated_at', 'sync_version', 'last_modified_by', 'last_sync_at', 'last_modified_at', 'sync_checksum'],
                'wallet': ['updated_at', 'sync_version', 'last_modified_by', 'last_sync_at', 'last_modified_at', 'sync_checksum'],
                'activation_codes': ['user_type', 'bound_account', 'bound_machine', 'note', 'expires_at', 'sync_version', 'last_modified_by', 'last_sync_at', 'last_modified_at', 'sync_checksum'],
                'wallet_transactions': ['wallet_id', 'related_id', 'sync_version', 'last_modified_by', 'last_sync_at', 'last_modified_at', 'sync_checksum'],
                'distribution_links': ['url', 'click_count', 'register_count', 'total_commission', 'status', 'sync_version', 'last_modified_by', 'last_sync_at', 'last_modified_at', 'sync_checksum'],
                'commissions': ['from_user_id', 'type', 'description', 'sync_version', 'last_modified_by', 'last_sync_at', 'last_modified_at', 'sync_checksum'],
                'team_members': ['username', 'total_contribution', 'sync_version', 'last_modified_by', 'last_sync_at', 'last_modified_at', 'sync_checksum'],
                'withdrawal_queue': ['wallet_id', 'reviewed_by', 'reviewed_at', 'note', 'sync_version', 'last_modified_by', 'last_modified_at', 'sync_checksum'],
                'user_memberships': ['username', 'membership_type', 'activated_at', 'expires_at', 'activation_code', 'sync_version', 'last_modified_by', 'last_sync_at', 'last_modified_at', 'sync_checksum'],
            }
            
            if table_name in cloud_only_fields:
                for field in cloud_only_fields[table_name]:
                    row_dict.pop(field, None)
            
            # 特殊处理：为 users 表生成 user_id（使用 username 作为 user_id）
            if table_name == 'users':
                if 'user_id' not in row_dict or row_dict['user_id'] is None:
                    row_dict['user_id'] = row_dict.get('username', 'unknown')
            
            # 特殊处理：为 withdrawal_queue 表生成 id（使用唯一整数 ID）
            if table_name == 'withdrawal_queue':
                if 'id' not in row_dict or row_dict['id'] is None:
                    import time
                    row_dict['id'] = int(time.time() * 1000) % 100000000 + hash(row_dict.get('description', '')) % 1000
            
            # 类型转换：浮点数转整数（针对 orders 表的 quantity 字段）
            if table_name == 'orders' and 'quantity' in row_dict:
                try:
                    row_dict['quantity'] = int(float(row_dict['quantity']))
                except:
                    pass
            
            ok, result = _request("POST", f"/rest/v1/{table_name}", 
                                data=row_dict, service_key=True)
            if ok:
                success_count += 1
            else:
                logger.error(f"插入失败: {result}")
        
        logger.info(f"[{table_name}] 推送完成: {success_count}/{len(rows)} 条")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"推送异常 [{table_name}]: {e}")
        return False
    finally:
        conn.close()


def _convert_value(value, col_type, col_name=None):
    """转换字段值类型以匹配本地数据库"""
    if value is None:
        return None
    
    col_type = col_type.upper() if col_type else 'TEXT'
    
    # id 字段特殊处理：云端 UUID → 本地 INTEGER（使用哈希映射）
    if col_name == 'id' and 'INT' in col_type:
        if isinstance(value, str) and '-' in value:
            # UUID 转整数：取最后一段转 int
            try:
                return int(value.split('-')[-1], 16) % 2147483647
            except:
                return hash(value) % 2147483647
        try:
            return int(value)
        except:
            return hash(str(value)) % 2147483647
    
    # INTEGER 类型
    if 'INT' in col_type:
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    
    # REAL/FLOAT 类型
    if 'REAL' in col_type or 'FLOAT' in col_type or 'DOUBLE' in col_type:
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    # TEXT 类型
    if 'TEXT' in col_type or 'CHAR' in col_type or 'VARCHAR' in col_type:
        return str(value)
    
    # TIMESTAMP/DATETIME 类型
    if 'TIMESTAMP' in col_type or 'DATETIME' in col_type:
        if isinstance(value, str):
            return value
        return str(value)
    
    # 默认转字符串
    return str(value)


def pull_from_cloud(table_name):
    """从云端拉取数据到本地（全量拉取，覆盖本地）"""
    conn, local_table = get_conn(table_name)
    if not conn:
        return False
    
    try:
        # 获取云端数据
        ok, cloud_rows = _request("GET", f"/rest/v1/{table_name}?limit=10000", service_key=True)
        if not ok:
            logger.error(f"[{table_name}] 拉取失败: {cloud_rows}")
            return False
        
        if not cloud_rows:
            logger.info(f"[{table_name}] 云端无数据")
            return True
        
        cursor = conn.cursor()
        
        # 获取本地表字段和类型
        cursor.execute(f"PRAGMA table_info({local_table})")
        local_schema = {row[1]: row[2] for row in cursor.fetchall()}
        local_columns = list(local_schema.keys())
        
        # 清空本地表
        cursor.execute(f"DELETE FROM {local_table}")
        
        # 插入云端数据
        inserted = 0
        for row in cloud_rows:
            # 只插入本地存在的字段，并转换类型
            valid_data = {}
            for k, v in row.items():
                if k in local_columns:
                    col_type = local_schema.get(k, 'TEXT')
                    valid_data[k] = _convert_value(v, col_type, k)
            
            if not valid_data:
                continue
            
            columns = ', '.join(valid_data.keys())
            placeholders = ', '.join(['?' for _ in valid_data])
            sql = f"INSERT INTO {local_table} ({columns}) VALUES ({placeholders})"
            
            try:
                cursor.execute(sql, list(valid_data.values()))
                inserted += 1
            except Exception as e:
                logger.warning(f"插入失败: {e}, 数据: {valid_data}")
        
        conn.commit()
        logger.info(f"[{table_name}] 拉取完成: {inserted}/{len(cloud_rows)} 条")
        return True
        
    except Exception as e:
        logger.error(f"拉取异常 [{table_name}]: {e}")
        return False
    finally:
        conn.close()


def sync_table(table_name, direction="bidirectional"):
    """
    同步单个表
    direction: push(本地→云端), pull(云端→本地), bidirectional(双向)
    """
    logger.info(f"[{table_name}] 开始同步 ({direction})...")
    
    if direction == "push":
        return push_to_cloud(table_name)
    elif direction == "pull":
        return pull_from_cloud(table_name)
    else:
        # 双向：先推后拉，或根据数据量决定
        # 简化：先推送本地到云端，再拉取云端到本地
        # 实际应该根据时间戳判断，这里简化处理
        push_ok = push_to_cloud(table_name)
        pull_ok = pull_from_cloud(table_name)
        return push_ok and pull_ok


def sync_all(direction="bidirectional"):
    """同步所有表"""
    logger.info("=" * 60)
    logger.info(f"开始同步所有表 ({direction})")
    logger.info("=" * 60)
    
    results = {}
    for table_name in TABLE_MAP.keys():
        try:
            ok = sync_table(table_name, direction)
            results[table_name] = "✅ 成功" if ok else "❌ 失败"
        except Exception as e:
            results[table_name] = f"❌ {e}"
    
    logger.info("=" * 60)
    for table, status in results.items():
        logger.info(f"  {table}: {status}")
    logger.info("=" * 60)
    
    return results


def auto_sync_after_change(table_name):
    """数据变更后自动同步到云端"""
    logger.info(f"[{table_name}] 数据变更，自动同步到云端...")
    return push_to_cloud(table_name)


def auto_sync_on_login():
    """登录后自动从云端同步"""
    logger.info("登录成功，自动从云端同步数据...")
    return sync_all("pull")


def get_sync_summary():
    """获取同步状态摘要"""
    summary = {}
    for table_name in TABLE_MAP.keys():
        conn, local_table = get_conn(table_name)
        if not conn:
            summary[table_name] = {"local": 0, "cloud": 0}
            continue
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {local_table}")
            local_count = cursor.fetchone()[0]
            summary[table_name] = {"local": local_count, "cloud": 0}
        except Exception as e:
            logger.warning(f"获取 {table_name} 本地数量失败: {e}")
            summary[table_name] = {"local": 0, "cloud": 0}
        finally:
            conn.close()
    
    # 获取云端数量
    for table_name in TABLE_MAP.keys():
        try:
            ok, cloud_rows = _request("GET", f"/rest/v1/{table_name}?select=id&limit=1000", service_key=True)
            if ok and isinstance(cloud_rows, list):
                summary[table_name]["cloud"] = len(cloud_rows)
        except Exception as e:
            logger.warning(f"获取 {table_name} 云端数量失败: {e}")
    
    return summary


# ══════════════════════════════════════════════════════
# 自动同步装饰器（用于业务代码集成）
# ══════════════════════════════════════════════════════

def sync_after(table_name):
    """
    装饰器：数据变更后自动同步到云端
    
    用法：
        @sync_after("customers")
        def add_customer(data):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # 操作成功后同步
            if result:  # 假设返回 truthy 表示成功
                logger.info(f"[{table_name}] 操作完成，准备同步...")
                try:
                    push_to_cloud(table_name)
                except Exception as e:
                    logger.error(f"同步失败: {e}")
            return result
        return wrapper
    return decorator


def sync_on_login(func):
    """
    装饰器：登录后自动从云端同步
    
    用法：
        @sync_on_login
        def login(username, password):
            ...
    """
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        # 登录成功后同步
        if result:  # 假设返回 truthy 表示登录成功
            logger.info("登录成功，准备同步数据...")
            try:
                auto_sync_on_login()
            except Exception as e:
                logger.error(f"同步失败: {e}")
        return result
    return wrapper


# ══════════════════════════════════════════════════════
# 便捷函数
# ══════════════════════════════════════════════════════

def push(table_name=None):
    """推送到云端"""
    if table_name:
        return push_to_cloud(table_name)
    return sync_all("push")


def pull(table_name=None):
    """从云端拉取"""
    if table_name:
        return pull_from_cloud(table_name)
    return sync_all("pull")


def sync(table_name=None):
    """双向同步"""
    if table_name:
        return sync_table(table_name, "bidirectional")
    return sync_all("bidirectional")


# ══════════════════════════════════════════════════════
# 测试
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("简化版三端同步测试")
    print("=" * 60)
    
    # 测试拉取
    print("\n测试拉取 customers...")
    pull("customers")
    
    print("\n测试拉取 finance...")
    pull("finance")
    
    print("\n测试拉取 staff...")
    pull("staff")
    
    print("\n完成!")
