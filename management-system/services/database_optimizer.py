"""
数据库优化器
索引优化、查询分析、性能调优
"""

import sqlite3
import time
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class QueryAnalysis:
    """查询分析结果"""
    sql: str
    execution_time_ms: float
    row_count: int
    suggested_indexes: List[str]
    complexity: str


class DatabaseOptimizer:
    """数据库优化器"""

    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path

    def analyze_query(self, sql: str, params: Optional[List] = None) -> QueryAnalysis:
        """分析查询性能"""
        start_time = time.time()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"EXPLAIN QUERY PLAN {sql}", params or [])
            plan = cursor.fetchall()

            cursor = conn.execute(sql, params or [])
            rows = cursor.fetchall()

        execution_time = (time.time() - start_time) * 1000

        suggested_indexes = self._suggest_indexes(sql, plan)

        complexity = "简单" if len(plan) <= 2 else ("中等" if len(plan) <= 5 else "复杂")

        return QueryAnalysis(
            sql=sql,
            execution_time_ms=round(execution_time, 2),
            row_count=len(rows),
            suggested_indexes=suggested_indexes,
            complexity=complexity,
        )

    def _suggest_indexes(self, sql: str, query_plan: List) -> List[str]:
        """建议索引"""
        suggestions = []

        sql_upper = sql.upper()

        # 检查WHERE子句
        if "WHERE" in sql_upper:
            if "product_id" in sql_upper and "products" in sql_upper:
                suggestions.append("CREATE INDEX idx_products_id ON products(id)")

            if "customer_id" in sql_upper and "customers" in sql_upper:
                suggestions.append("CREATE INDEX idx_customers_id ON customers(id)")

            if "created_at" in sql_upper:
                suggestions.append("CREATE INDEX idx_created_at ON orders(created_at)")

            if "status" in sql_upper and "orders" in sql_upper:
                suggestions.append("CREATE INDEX idx_orders_status ON orders(status)")

        return suggestions

    def create_index(self, index_sql: str) -> Dict:
        """创建索引"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(index_sql)
                conn.commit()
            return {"success": True, "message": "索引创建成功"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_table_stats(self) -> Dict:
        """获取表统计"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

        stats = {}
        for table in tables:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]

                cursor = conn.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]

                cursor = conn.execute(f"PRAGMA index_list({table})")
                indexes = [row[1] for row in cursor.fetchall()]

                stats[table] = {
                    "row_count": row_count,
                    "column_count": len(columns),
                    "columns": columns,
                    "indexes": indexes,
                }

        return {"success": True, "tables": stats}

    def vacuum_database(self) -> Dict:
        """压缩数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")
                conn.commit()
            return {"success": True, "message": "数据库压缩完成"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def optimize_database(self) -> Dict:
        """优化数据库"""
        results = []

        # 分析
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA analysis_limit=400")
            conn.execute("PRAGMA optimize")
            conn.commit()
        results.append("PRAGMA optimize 执行完成")

        # 重建索引
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("REINDEX")
            conn.commit()
        results.append("索引重建完成")

        return {"success": True, "results": results}

    def get_query_suggestions(self) -> List[str]:
        """获取优化建议"""
        suggestions = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]

                if row_count > 10000:
                    suggestions.append(f"表 {table} 数据量较大 ({row_count}行)，确保常用查询字段有索引")

                cursor = conn.execute(f"PRAGMA index_list({table})")
                indexes = cursor.fetchall()
                if not indexes and row_count > 1000:
                    suggestions.append(f"表 {table} ({row_count}行) 没有索引，建议对常用查询字段创建索引")

            cursor = conn.execute("PRAGMA freelist_count")
            freelist = cursor.fetchone()[0]
            if freelist > 100:
                suggestions.append(f"数据库有 {freelist} 个空闲页，建议执行 VACUUM")

        return suggestions

