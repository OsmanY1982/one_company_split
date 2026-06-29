"""
自然语言查询服务
支持中文自然语言转SQL查询
"""

import json
import sqlite3
import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class NLQueryService:
    """自然语言查询服务"""

    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path

    def query(self, question: str) -> Dict:
        """自然语言查询"""
        try:
            sql, params = self._nl_to_sql(question)

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(sql, params)
                rows = [dict(row) for row in cursor.fetchall()]

            return {
                "success": True,
                "question": question,
                "sql": sql,
                "params": params,
                "results": rows,
                "count": len(rows),
            }

        except Exception as e:
            return {"success": False, "message": f"查询失败: {e}"}

    def _nl_to_sql(self, question: str) -> tuple:
        """自然语言转SQL"""
        question_upper = question.upper()

        # 今日订单
        if any(w in question for w in ["今日", "今天", "今日的"]):
            if any(w in question for w in ["订单", "销售"]):
                today_start = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
                return (
                    "SELECT * FROM orders WHERE created_at >= ? ORDER BY created_at DESC",
                    (today_start,)
                )

        # 本月订单
        if any(w in question for w in ["本月", "这个月"]):
            if any(w in question for w in ["订单", "销售"]):
                month_start = int(datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).timestamp())
                return (
                    "SELECT * FROM orders WHERE created_at >= ? ORDER BY created_at DESC",
                    (month_start,)
                )

        # 订单总额
        if any(w in question for w in ["总额", "总收入", "销售额"]):
            if any(w in question for w in ["今日", "今天"]):
                today_start = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
                return (
                    "SELECT COALESCE(SUM(total_amount), 0) as total_revenue FROM orders WHERE created_at >= ?",
                    (today_start,)
                )
            else:
                return ("SELECT COALESCE(SUM(total_amount), 0) as total_revenue FROM orders", ())

        # 客户列表
        if any(w in question for w in ["客户", "顾客"]):
            return ("SELECT * FROM customers ORDER BY name", ())

        # 产品列表
        if any(w in question for w in ["产品", "商品"]):
            if any(w in question for w in ["库存", "缺货"]):
                return ("SELECT * FROM products WHERE stock = 0", ())
            else:
                return ("SELECT * FROM products ORDER BY name", ())

        # 待处理
        if any(w in question for w in ["待处理", "未完成"]):
            return ("SELECT * FROM orders WHERE status = 'pending'", ())

        # 今天日期相关
        date_match = re.search(r'(\d{4})[年-](\d{1,2})[月-](\d{1,2})', question)
        if date_match:
            year, month, day = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
            target_date = datetime(year, month, day)
            start_ts = int(target_date.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
            end_ts = int(target_date.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp())
            return (
                "SELECT * FROM orders WHERE created_at BETWEEN ? AND ?",
                (start_ts, end_ts)
            )

        # 默认：全量表
        return ("SELECT * FROM orders ORDER BY created_at DESC LIMIT 20", ())

    def analyze(self, question: str) -> Dict:
        """分析自然语言查询意图"""
        analysis = {
            "question": question,
            "intent": "unknown",
            "target_table": None,
            "time_range": None,
            "filters": [],
            "aggregations": [],
        }

        question_lower = question.lower()

        # 识别目标表
        if any(w in question_lower for w in ["客户", "顾客", "customer"]):
            analysis["target_table"] = "customers"
        elif any(w in question_lower for w in ["产品", "商品", "product"]):
            analysis["target_table"] = "products"
        elif any(w in question_lower for w in ["订单", "order", "销售"]):
            analysis["target_table"] = "orders"
        elif any(w in question_lower for w in ["库存", "stock"]):
            analysis["target_table"] = "products"

        # 识别时间范围
        if any(w in question_lower for w in ["今日", "今天"]):
            analysis["time_range"] = "today"
        elif any(w in question_lower for w in ["昨日", "昨天"]):
            analysis["time_range"] = "yesterday"
        elif any(w in question_lower for w in ["本月", "这个月"]):
            analysis["time_range"] = "this_month"
        elif any(w in question_lower for w in ["上月", "上个月"]):
            analysis["time_range"] = "last_month"

        # 识别聚合
        if any(w in question_lower for w in ["总额", "总和", "总金额"]):
            analysis["aggregations"].append("sum_amount")
        if any(w in question_lower for w in ["平均", "均值"]):
            analysis["aggregations"].append("avg")
        if any(w in question_lower for w in ["数量", "个数"]):
            analysis["aggregations"].append("count")

        # 识别意图
        if analysis["aggregations"]:
            analysis["intent"] = "aggregation"
        elif any(w in question_lower for w in ["趋势", "变化"]):
            analysis["intent"] = "trend"
        elif any(w in question_lower for w in ["排行", "排名", "top"]):
            analysis["intent"] = "ranking"
        else:
            analysis["intent"] = "query"

        return analysis

    def get_supported_queries(self) -> List[Dict]:
        """获取支持的查询类型"""
        return [
            {"query": "今日订单", "description": "查询今日所有订单"},
            {"query": "本月销售额", "description": "查询本月销售总额"},
            {"query": "客户列表", "description": "获取所有客户信息"},
            {"query": "产品库存", "description": "查询产品库存情况"},
            {"query": "待处理订单", "description": "查看未完成订单"},
            {"query": "热销产品排行", "description": "按销量排序产品"},
            {"query": "今日总收入", "description": "查询今日订单总金额"},
        ]

