# `iqra/modules/intelligence/db_helper.py`

> 路径：`iqra/modules/intelligence/db_helper.py` | 行数：161


---


```python
# -*- coding: utf-8 -*-
"""
数据库辅助模块
适配一企通多数据库结构
"""
import os
import sqlite3
from typing import Dict, List, Optional


class DBHelper:
    """数据库辅助类"""
    
    # 所有表都在 orders.db 中
    MAIN_DB = "orders"
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(base_dir, "data")
        self.data_dir = data_dir
    
    def _get_db_path(self, db_name: str) -> str:
        """获取数据库路径"""
        return os.path.join(self.data_dir, f"{db_name}.db")
    
    def _connect(self, db_name: str = None) -> sqlite3.Connection:
        """连接数据库"""
        if db_name is None:
            db_name = self.MAIN_DB
        return sqlite3.connect(self._get_db_path(db_name))
    
    def query_orders(self, date_filter: str = None) -> Dict:
        """查询订单数据"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            
            if date_filter:
                cursor.execute(f"""
                    SELECT COUNT(*), COALESCE(SUM(amount), 0)
                    FROM orders
                    WHERE {date_filter}
                """)
            else:
                cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM orders")
            
            count, total = cursor.fetchone()
            conn.close()
            
            return {"count": count, "total_amount": float(total) if total else 0}
        except Exception as e:
            return {"error": str(e), "count": 0, "total_amount": 0}
    
    def query_products(self, stock_threshold: int = None) -> Dict:
        """查询产品数据"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(stock), 0) FROM products")
            total, stock = cursor.fetchone()
            
            result = {"total": total, "total_stock": stock or 0}
            
            if stock_threshold is not None:
                cursor.execute("SELECT name, stock FROM products WHERE stock <= ?", (stock_threshold,))
                result["low_stock"] = [{"name": row[0], "stock": row[1]} for row in cursor.fetchall()]
            
            conn.close()
            return result
        except Exception as e:
            return {"error": str(e), "total": 0, "total_stock": 0}
    
    def query_customers(self, date_filter: str = None) -> Dict:
        """查询客户数据"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM customers")
            total = cursor.fetchone()[0]
            
            result = {"total": total}
            
            if date_filter:
                cursor.execute(f"SELECT COUNT(*) FROM customers WHERE {date_filter}")
                result["new"] = cursor.fetchone()[0]
            
            conn.close()
            return result
        except Exception as e:
            return {"error": str(e), "total": 0}
    
    def query_staff(self) -> Dict:
        """查询员工数据"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM staff")
            total = cursor.fetchone()[0]
            
            conn.close()
            return {"total": total}
        except Exception as e:
            return {"error": str(e), "total": 0}
    
    def query_finance(self, date_filter: str = None) -> Dict:
        """查询财务数据"""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            
            if date_filter:
                cursor.execute(f"""
                    SELECT 
                        COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE 0 END), 0) as income,
                        COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END), 0) as expense
                    FROM finance
                    WHERE {date_filter}
                """)
            else:
                cursor.execute("""
                    SELECT 
                        COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE 0 END), 0) as income,
                        COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END), 0) as expense
                    FROM finance
                """)
            
            income, expense = cursor.fetchone()
            conn.close()
            
            return {
                "income": float(income) if income else 0,
                "expense": float(expense) if expense else 0,
                "profit": float(income or 0) - float(expense or 0)
            }
        except Exception as e:
            return {"error": str(e), "income": 0, "expense": 0, "profit": 0}
    
    def get_all_stats(self) -> Dict:
        """获取所有统计数据"""
        return {
            "orders": self.query_orders(),
            "products": self.query_products(),
            "customers": self.query_customers(),
            "staff": self.query_staff(),
            "finance": self.query_finance()
        }


# 全局实例
_helper = None

def get_db_helper() -> DBHelper:
    """获取全局数据库辅助实例"""
    global _helper
    if _helper is None:
        _helper = DBHelper()
    return _helper

```
