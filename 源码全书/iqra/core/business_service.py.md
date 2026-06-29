# `iqra/core/business_service.py`

> 路径：`iqra/core/business_service.py` | 行数：426


---


```python
# -*- coding: utf-8 -*-
"""
业务数据库初始化与核心服务
统一管理所有业务数据库的创建、表结构初始化
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from core.paths import DATA_DIR


class BusinessService:
    """业务核心服务"""

    # 所有数据库定义
    DATABASES = {
        "customer.db": {
            "tables": {
                "customers": """
                    CREATE TABLE IF NOT EXISTS customers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        company TEXT DEFAULT '',
                        phone TEXT DEFAULT '',
                        email TEXT DEFAULT '',
                        address TEXT DEFAULT '',
                        note TEXT DEFAULT '',
                        level TEXT DEFAULT '普通',
                        total_spent REAL DEFAULT 0,
                        last_order TEXT DEFAULT '',
                        created_at TEXT DEFAULT '',
                        updated_at TEXT DEFAULT '',
                        sync_version INTEGER DEFAULT 0
                    )
                """
            }
        },
        "product.db": {
            "tables": {
                "products": """
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        category TEXT DEFAULT '',
                        price REAL DEFAULT 0,
                        cost REAL DEFAULT 0,
                        stock INTEGER DEFAULT 0,
                        unit TEXT DEFAULT '个',
                        supplier TEXT DEFAULT '',
                        description TEXT DEFAULT '',
                        created_at TEXT DEFAULT '',
                        updated_at TEXT DEFAULT '',
                        sync_version INTEGER DEFAULT 0
                    )
                """,
                "product_categories": """
                    CREATE TABLE IF NOT EXISTS product_categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        parent_id INTEGER DEFAULT 0,
                        sort_order INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT ''
                    )
                """
            }
        },
        "order.db": {
            "tables": {
                "orders": """
                    CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_no TEXT NOT NULL UNIQUE,
                        customer_id INTEGER DEFAULT 0,
                        customer_name TEXT DEFAULT '',
                        total_amount REAL DEFAULT 0,
                        discount REAL DEFAULT 0,
                        paid_amount REAL DEFAULT 0,
                        status TEXT DEFAULT '待处理',
                        payment_method TEXT DEFAULT '',
                        note TEXT DEFAULT '',
                        created_at TEXT DEFAULT '',
                        updated_at TEXT DEFAULT '',
                        sync_version INTEGER DEFAULT 0
                    )
                """,
                "order_items": """
                    CREATE TABLE IF NOT EXISTS order_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_id INTEGER NOT NULL,
                        product_id INTEGER DEFAULT 0,
                        product_name TEXT DEFAULT '',
                        quantity INTEGER DEFAULT 1,
                        price REAL DEFAULT 0,
                        amount REAL DEFAULT 0,
                        created_at TEXT DEFAULT '',
                        sync_version INTEGER DEFAULT 0
                    )
                """
            }
        },
        "finance.db": {
            "tables": {
                "finance_records": """
                    CREATE TABLE IF NOT EXISTS finance_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT DEFAULT 'expense',
                        amount REAL DEFAULT 0,
                        category TEXT DEFAULT '',
                        description TEXT DEFAULT '',
                        date TEXT DEFAULT '',
                        created_at TEXT DEFAULT '',
                        updated_at TEXT DEFAULT '',
                        sync_version INTEGER DEFAULT 0
                    )
                """,
                "finance_categories": """
                    CREATE TABLE IF NOT EXISTS finance_categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        type TEXT DEFAULT 'expense',
                        is_default INTEGER DEFAULT 0,
                        sort_order INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT ''
                    )
                """
            }
        },
        "staff.db": {
            "tables": {
                "staff": """
                    CREATE TABLE IF NOT EXISTS staff (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        phone TEXT DEFAULT '',
                        email TEXT DEFAULT '',
                        department TEXT DEFAULT '',
                        position TEXT DEFAULT '',
                        salary REAL DEFAULT 0,
                        status TEXT DEFAULT '在职',
                        join_date TEXT DEFAULT '',
                        note TEXT DEFAULT '',
                        created_at TEXT DEFAULT '',
                        updated_at TEXT DEFAULT '',
                        sync_version INTEGER DEFAULT 0
                    )
                """,
                "departments": """
                    CREATE TABLE IF NOT EXISTS departments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        parent_id INTEGER DEFAULT 0,
                        manager TEXT DEFAULT '',
                        sort_order INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT ''
                    )
                """
            }
        },
        "member.db": {
            "tables": {
                "members": """
                    CREATE TABLE IF NOT EXISTS members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        phone TEXT DEFAULT '',
                        email TEXT DEFAULT '',
                        level TEXT DEFAULT '普通',
                        points INTEGER DEFAULT 0,
                        total_spent REAL DEFAULT 0,
                        created_at TEXT DEFAULT '',
                        updated_at TEXT DEFAULT '',
                        sync_version INTEGER DEFAULT 0
                    )
                """,
                "member_points_log": """
                    CREATE TABLE IF NOT EXISTS member_points_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        member_id INTEGER NOT NULL,
                        points_change INTEGER DEFAULT 0,
                        reason TEXT DEFAULT '',
                        created_at TEXT DEFAULT ''
                    )
                """
            }
        },
        "supplier.db": {
            "tables": {
                "suppliers": """
                    CREATE TABLE IF NOT EXISTS suppliers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        contact TEXT DEFAULT '',
                        phone TEXT DEFAULT '',
                        email TEXT DEFAULT '',
                        address TEXT DEFAULT '',
                        note TEXT DEFAULT '',
                        created_at TEXT DEFAULT '',
                        updated_at TEXT DEFAULT ''
                    )
                """
            }
        },
        "inventory.db": {
            "tables": {
                "inventory_log": """
                    CREATE TABLE IF NOT EXISTS inventory_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER NOT NULL,
                        product_name TEXT DEFAULT '',
                        change_amount INTEGER DEFAULT 0,
                        before_stock INTEGER DEFAULT 0,
                        after_stock INTEGER DEFAULT 0,
                        type TEXT DEFAULT '',
                        note TEXT DEFAULT '',
                        created_at TEXT DEFAULT ''
                    )
                """
            }
        },
        "users.db": {
            "tables": {
                "users": """
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT DEFAULT '',
                        role TEXT DEFAULT 'user',
                        license_type TEXT DEFAULT 'basic',
                        created_at TEXT DEFAULT '',
                        updated_at TEXT DEFAULT ''
                    )
                """,
                "user_memberships": """
                    CREATE TABLE IF NOT EXISTS user_memberships (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        membership_type TEXT DEFAULT '',
                        activation_code TEXT DEFAULT '',
                        activated_at TEXT DEFAULT ''
                    )
                """,
                "login_history": """
                    CREATE TABLE IF NOT EXISTS login_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        login_time TEXT DEFAULT '',
                        logout_time TEXT DEFAULT '',
                        machine_code TEXT DEFAULT '',
                        ip_address TEXT DEFAULT ''
                    )
                """
            }
        },
        "distribution.db": {
            "tables": {
                "distribution_links": """
                    CREATE TABLE IF NOT EXISTS distribution_links (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code TEXT NOT NULL UNIQUE,
                        creator TEXT DEFAULT '',
                        type TEXT DEFAULT 'product',
                        target_id INTEGER DEFAULT 0,
                        target_name TEXT DEFAULT '',
                        created_at TEXT DEFAULT '',
                        updated_at TEXT DEFAULT '',
                        sync_version INTEGER DEFAULT 0
                    )
                """,
                "commissions": """
                    CREATE TABLE IF NOT EXISTS commissions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        link_code TEXT DEFAULT '',
                        amount REAL DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        from_user TEXT DEFAULT '',
                        created_at TEXT DEFAULT '',
                        updated_at TEXT DEFAULT '',
                        sync_version INTEGER DEFAULT 0
                    )
                """
            }
        },
        "wallet.db": {
            "tables": {
                "wallets": """
                    CREATE TABLE IF NOT EXISTS wallets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL UNIQUE,
                        balance REAL DEFAULT 0,
                        frozen REAL DEFAULT 0,
                        created_at TEXT DEFAULT '',
                        updated_at TEXT DEFAULT '',
                        sync_version INTEGER DEFAULT 0
                    )
                """,
                "wallet_transactions": """
                    CREATE TABLE IF NOT EXISTS wallet_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT DEFAULT '',
                        type TEXT DEFAULT '',
                        amount REAL DEFAULT 0,
                        balance_before REAL DEFAULT 0,
                        balance_after REAL DEFAULT 0,
                        description TEXT DEFAULT '',
                        created_at TEXT DEFAULT '',
                        sync_version INTEGER DEFAULT 0
                    )
                """
            }
        },
        "task.db": {
            "tables": {
                "tasks": """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT DEFAULT '',
                        status TEXT DEFAULT 'pending',
                        priority TEXT DEFAULT 'medium',
                        assignee TEXT DEFAULT '',
                        due_date TEXT DEFAULT '',
                        created_at TEXT DEFAULT '',
                        updated_at TEXT DEFAULT '',
                        sync_version INTEGER DEFAULT 0
                    )
                """
            }
        }
    }

    @classmethod
    def init_all_databases(cls) -> Dict[str, bool]:
        """初始化所有业务数据库"""
        results = {}
        for db_name, config in cls.DATABASES.items():
            db_path = os.path.join(DATA_DIR, db_name)
            try:
                conn = sqlite3.connect(db_path)
                for table_name, create_sql in config["tables"].items():
                    conn.execute(create_sql)
                conn.commit()
                conn.close()
                results[db_name] = True
                print(f"[BusinessService] 数据库初始化成功: {db_name}")
            except Exception as e:
                results[db_name] = False
                print(f"[BusinessService] 数据库初始化失败 {db_name}: {e}")
        return results

    @classmethod
    def get_table_list(cls) -> Dict[str, List[str]]:
        """获取所有数据库的表列表"""
        result = {}
        for db_name, config in cls.DATABASES.items():
            result[db_name] = list(config["tables"].keys())
        return result

    @classmethod
    def register_user(cls, username: str, password: str, role: str = 'user', license_type: str = 'basic') -> Tuple[bool, str]:
        """注册用户"""
        try:
            conn = sqlite3.connect(os.path.join(DATA_DIR, "users.db"))
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT OR REPLACE INTO users (username, password, role, license_type, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (username, password, role, license_type, now, now)
            )
            conn.commit()
            conn.close()
            return True, "注册成功"
        except Exception as e:
            return False, str(e)

    @classmethod
    def activate_membership(cls, username: str, membership_type: str, activation_code: str) -> Tuple[bool, str]:
        """激活会员"""
        try:
            conn = sqlite3.connect(os.path.join(DATA_DIR, "users.db"))
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT OR REPLACE INTO user_memberships (username, membership_type, activation_code, activated_at) VALUES (?, ?, ?, ?)",
                (username, membership_type, activation_code, now)
            )
            conn.commit()
            conn.close()
            return True, f"会员激活成功: {membership_type}"
        except Exception as e:
            return False, str(e)

    @classmethod
    def on_product_sale(cls, product_id: int, quantity: int) -> bool:
        """产品销售后联动：扣库存、更新销量"""
        try:
            conn = sqlite3.connect(os.path.join(DATA_DIR, "product.db"))
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE products SET stock = stock - ?, updated_at = ? WHERE id = ? AND stock >= ?",
                (quantity, datetime.now().isoformat(), product_id, quantity)
            )
            affected = cursor.rowcount
            conn.commit()
            conn.close()
            return affected > 0
        except Exception as e:
            print(f"[BusinessService] 扣库存失败: {e}")
            return False


if __name__ == "__main__":
    print("=" * 50)
    print("业务数据库初始化")
    print("=" * 50)
    results = BusinessService.init_all_databases()
    for db, ok in results.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {db}")
    print("\n所有表:")
    tables = BusinessService.get_table_list()
    for db, tbl_list in tables.items():
        print(f"\n{db}:")
        for tbl in tbl_list:
            print(f"  - {tbl}")

```
