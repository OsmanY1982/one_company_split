#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三端同步集成示例
展示如何在业务代码中使用自动同步
"""

import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.simple_sync import sync_after, sync_on_login, auto_sync_on_login

# ══════════════════════════════════════════════════════
# 示例1：添加客户后自动同步
# ══════════════════════════════════════════════════════

@sync_after("customers")
def add_customer(name, company, phone, email="", address="", level="普通"):
    """添加客户（自动同步到云端）"""
    db_path = os.path.join(BASE_DIR, "data", "customer.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO customer (name, company, phone, email, address, level, created_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
    """, (name, company, phone, email, address, level))
    
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    
    print(f"✅ 客户添加成功: {name} (ID: {new_id})")
    return new_id


@sync_after("customers")
def update_customer(customer_id, **kwargs):
    """更新客户（自动同步到云端）"""
    db_path = os.path.join(BASE_DIR, "data", "customer.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 构建更新语句
    fields = []
    values = []
    for key, value in kwargs.items():
        fields.append(f"{key} = ?")
        values.append(value)
    values.append(customer_id)
    
    sql = f"UPDATE customer SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(sql, values)
    
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    
    if updated:
        print(f"✅ 客户更新成功 (ID: {customer_id})")
    return updated


@sync_after("customers")
def delete_customer(customer_id):
    """删除客户（自动同步到云端）"""
    db_path = os.path.join(BASE_DIR, "data", "customer.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM customer WHERE id = ?", (customer_id,))
    
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    
    if deleted:
        print(f"✅ 客户删除成功 (ID: {customer_id})")
    return deleted


# ══════════════════════════════════════════════════════
# 示例2：添加员工后自动同步
# ══════════════════════════════════════════════════════

@sync_after("staff")
def add_staff(name, phone, email, department, position, salary, status="在职"):
    """添加员工（自动同步到云端）"""
    db_path = os.path.join(BASE_DIR, "data", "staff.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO staff (name, phone, email, department, position, salary, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (name, phone, email, department, position, salary, status))
    
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    
    print(f"✅ 员工添加成功: {name} (ID: {new_id})")
    return new_id


# ══════════════════════════════════════════════════════
# 示例3：登录后自动同步
# ══════════════════════════════════════════════════════

@sync_on_login
def login(username, password):
    """登录（登录后自动从云端拉取数据）"""
    # 这里写你的登录逻辑
    # 简化示例：假设验证成功
    print(f"✅ 登录成功: {username}")
    return True  # 返回 True 表示登录成功，会触发同步


# ══════════════════════════════════════════════════════
# 示例4：手动同步按钮
# ══════════════════════════════════════════════════════

def manual_sync_all():
    """手动同步所有数据（用于同步按钮）"""
    from core.simple_sync import sync_all
    print("🔄 开始手动同步...")
    results = sync_all("bidirectional")
    print("✅ 同步完成")
    return results


# ══════════════════════════════════════════════════════
# 测试
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("三端同步集成测试")
    print("=" * 60)
    
    # 测试登录同步
    print("\n1. 测试登录后同步...")
    login("admin", "password")
    
    # 测试添加客户
    print("\n2. 测试添加客户...")
    # add_customer("测试客户", "测试公司", "13800138000")
    
    # 测试手动同步
    print("\n3. 测试手动同步...")
    # manual_sync_all()
    
    print("\n完成!")
