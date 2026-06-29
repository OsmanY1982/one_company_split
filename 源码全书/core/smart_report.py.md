# `core/smart_report.py`

> 路径：`core/smart_report.py` | 行数：408


---


```python
# -*- coding: utf-8 -*-
"""
智能报表 — 自然语言生成报表
支持：一句话生成图表、自动SQL生成、智能图表推荐
"""
import json
import re
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from core.database import get_conn


class SmartReportGenerator:
    """智能报表生成器"""
    
    # 数据库表结构定义
    TABLE_SCHEMA = {
        "products": {
            "columns": ["id", "name", "category", "price", "cost", "stock", "supplier", "created_at"],
            "description": "产品表"
        },
        "orders": {
            "columns": ["id", "customer_id", "product_id", "quantity", "amount", "status", "created_at"],
            "description": "订单表"
        },
        "customers": {
            "columns": ["id", "name", "phone", "level", "total_spent", "last_order", "created_at"],
            "description": "客户表"
        },
        "finance": {
            "columns": ["id", "type", "amount", "category", "description", "created_at"],
            "description": "财务表"
        },
        "member": {
            "columns": ["id", "name", "phone", "level", "points", "created_at"],
            "description": "会员表"
        },
        "staff": {
            "columns": ["id", "name", "position", "salary", "department", "created_at"],
            "description": "员工表"
        }
    }
    
    # 时间关键词映射
    TIME_PATTERNS = {
        r"今天|今日": lambda: (datetime.now().date(), datetime.now().date()),
        r"昨天|昨日": lambda: (datetime.now().date() - timedelta(days=1), datetime.now().date() - timedelta(days=1)),
        r"最近7天|近7天|近一周": lambda: (datetime.now().date() - timedelta(days=6), datetime.now().date()),
        r"最近30天|近30天|近一月": lambda: (datetime.now().date() - timedelta(days=29), datetime.now().date()),
        r"最近90天|近90天|近三月": lambda: (datetime.now().date() - timedelta(days=89), datetime.now().date()),
        r"本月|这个月": lambda: (datetime.now().replace(day=1).date(), datetime.now().date()),
        r"上月|上个月": lambda: ((datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1).date(), 
                                  (datetime.now().replace(day=1) - timedelta(days=1)).date()),
        r"今年|本年度": lambda: (datetime.now().replace(month=1, day=1).date(), datetime.now().date()),
    }
    
    def __init__(self):
        self.query_history = []
    
    def parse_natural_language(self, query: str) -> Dict:
        """
        解析自然语言查询
        返回: {"intent": str, "table": str, "time_range": tuple, "metrics": list, "dimensions": list, "chart_type": str}
        """
        query = query.lower().strip()
        result = {
            "intent": "unknown",
            "table": None,
            "time_range": None,
            "metrics": [],
            "dimensions": [],
            "chart_type": "table",
            "filters": {},
            "original_query": query
        }
        
        # 1. 识别意图
        result["intent"] = self._detect_intent(query)
        
        # 2. 识别表
        result["table"] = self._detect_table(query)
        
        # 3. 识别时间范围
        result["time_range"] = self._detect_time_range(query)
        
        # 4. 识别指标
        result["metrics"] = self._detect_metrics(query)
        
        # 5. 识别维度
        result["dimensions"] = self._detect_dimensions(query)
        
        # 6. 推荐图表类型
        result["chart_type"] = self._recommend_chart(result)
        
        return result
    
    def _detect_intent(self, query: str) -> str:
        """检测查询意图"""
        intent_patterns = {
            "summary": r"汇总|总计|总共|合计|多少",
            "trend": r"趋势|变化|走势|增长|下降",
            "comparison": r"对比|比较|排名|top|前",
            "distribution": r"分布|占比|比例|构成",
            "detail": r"明细|详情|列表|记录"
        }
        
        for intent, pattern in intent_patterns.items():
            if re.search(pattern, query):
                return intent
        
        return "summary"
    
    def _detect_table(self, query: str) -> Optional[str]:
        """检测涉及的表"""
        table_keywords = {
            "products": r"产品|商品|库存|sku",
            "orders": r"订单|销售|销量|售卖",
            "customers": r"客户|顾客|买家|消费者",
            "finance": r"财务|收入|支出|利润|钱",
            "member": r"会员|vip|积分",
            "staff": r"员工|人员|人事|工资"
        }
        
        for table, pattern in table_keywords.items():
            if re.search(pattern, query):
                return table
        
        # 默认返回订单表
        return "orders"
    
    def _detect_time_range(self, query: str) -> Optional[Tuple]:
        """检测时间范围"""
        for pattern, func in self.TIME_PATTERNS.items():
            if re.search(pattern, query):
                return func()
        
        # 默认最近7天
        return (datetime.now().date() - timedelta(days=6), datetime.now().date())
    
    def _detect_metrics(self, query: str) -> List[str]:
        """检测指标"""
        metrics = []
        
        metric_patterns = {
            "amount": r"金额|销售额|收入|营业额",
            "quantity": r"数量|销量|件数|单数",
            "count": r"人数|客户数|订单数|笔数",
            "profit": r"利润|毛利|净利|盈利"
        }
        
        for metric, pattern in metric_patterns.items():
            if re.search(pattern, query):
                metrics.append(metric)
        
        if not metrics:
            metrics.append("amount")  # 默认金额
        
        return metrics
    
    def _detect_dimensions(self, query: str) -> List[str]:
        """检测维度"""
        dimensions = []
        
        dimension_patterns = {
            "date": r"按天|按日|每日|日期",
            "week": r"按周|每周|星期",
            "month": r"按月|每月|月份",
            "category": r"按分类|按类别|品类",
            "level": r"按等级|按级别|等级",
            "status": r"按状态|状态"
        }
        
        for dim, pattern in dimension_patterns.items():
            if re.search(pattern, query):
                dimensions.append(dim)
        
        return dimensions
    
    def _recommend_chart(self, parsed: Dict) -> str:
        """推荐图表类型"""
        intent = parsed["intent"]
        dimensions = parsed["dimensions"]
        
        if intent == "trend" or "date" in dimensions:
            return "line"  # 折线图
        elif intent == "comparison":
            return "bar"  # 柱状图
        elif intent == "distribution":
            return "pie"  # 饼图
        elif intent == "summary":
            return "kpi"  # KPI卡片
        else:
            return "table"  # 表格
    
    def generate_sql(self, parsed: Dict) -> str:
        """根据解析结果生成SQL"""
        table = parsed["table"]
        time_range = parsed["time_range"]
        metrics = parsed["metrics"]
        dimensions = parsed["dimensions"]
        
        # 构建SELECT
        selects = []
        
        # 维度字段
        for dim in dimensions:
            if dim == "date":
                selects.append("date(created_at) as dimension")
            elif dim == "month":
                selects.append("strftime('%Y-%m', created_at) as dimension")
            elif dim == "category":
                selects.append("category as dimension")
            elif dim == "level":
                selects.append("level as dimension")
            elif dim == "status":
                selects.append("status as dimension")
        
        # 指标字段
        for metric in metrics:
            if metric == "amount":
                selects.append("SUM(amount) as total_amount")
            elif metric == "quantity":
                selects.append("SUM(quantity) as total_quantity")
            elif metric == "count":
                selects.append("COUNT(*) as total_count")
            elif metric == "profit":
                selects.append("SUM(amount - cost) as total_profit")
        
        # 构建WHERE
        wheres = []
        if time_range:
            start, end = time_range
            wheres.append(f"date(created_at) BETWEEN '{start}' AND '{end}'")
        
        # 组装SQL
        sql = f"SELECT {', '.join(selects)} FROM {table}"
        if wheres:
            sql += f" WHERE {' AND '.join(wheres)}"
        if dimensions:
            sql += " GROUP BY dimension"
            sql += " ORDER BY total_amount DESC"
        
        return sql
    
    def execute_report(self, query: str) -> Dict:
        """
        执行自然语言报表查询
        返回: {"success": bool, "data": list, "chart_type": str, "title": str, "sql": str}
        """
        try:
            # 1. 解析查询
            parsed = self.parse_natural_language(query)
            
            # 2. 生成SQL
            sql = self.generate_sql(parsed)
            
            # 3. 执行查询
            db_name = f"{parsed['table']}.db"
            rows = self._execute_sql(db_name, sql)
            
            # 4. 生成标题
            title = self._generate_title(parsed)
            
            result = {
                "success": True,
                "data": rows,
                "chart_type": parsed["chart_type"],
                "title": title,
                "sql": sql,
                "parsed": parsed
            }
            
            # 记录历史
            self.query_history.append({
                "query": query,
                "result": result,
                "time": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def _execute_sql(self, db_name: str, sql: str) -> List[Dict]:
        """执行SQL查询"""
        try:
            conn = get_conn(db_name)
            cursor = conn.execute(sql)
            
            # 获取列名
            columns = [description[0] for description in cursor.description]
            
            # 转换为字典列表
            rows = []
            for row in cursor.fetchall():
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # 处理日期类型
                    if isinstance(value, str) and re.match(r'\d{4}-\d{2}-\d{2}', value):
                        row_dict[col] = value
                    else:
                        row_dict[col] = value
                rows.append(row_dict)
            
            return rows
            
        except Exception as e:
            print(f"SQL执行错误: {e}")
            return []
    
    def _generate_title(self, parsed: Dict) -> str:
        """生成报表标题"""
        table_names = {
            "products": "产品",
            "orders": "销售",
            "customers": "客户",
            "finance": "财务",
            "member": "会员",
            "staff": "员工"
        }
        
        table_name = table_names.get(parsed["table"], parsed["table"])
        
        if parsed["time_range"]:
            start, end = parsed["time_range"]
            if start == end:
                time_str = f"{start}"
            else:
                time_str = f"{start} 至 {end}"
        else:
            time_str = "全部时间"
        
        intent_names = {
            "summary": "汇总",
            "trend": "趋势",
            "comparison": "对比",
            "distribution": "分布",
            "detail": "明细"
        }
        
        intent_name = intent_names.get(parsed["intent"], "统计")
        
        return f"{table_name}{intent_name}报表 ({time_str})"
    
    def get_suggestions(self) -> List[str]:
        """获取查询建议"""
        return [
            "最近7天的销售额",
            "本月产品销售排名",
            "客户等级分布",
            "最近30天的收入趋势",
            "各品类销售占比",
            "今天的新订单",
            "会员积分排行",
            "本月的财务收支"
        ]


# 全局实例
_smart_report = None

def get_smart_report() -> SmartReportGenerator:
    """获取智能报表生成器实例"""
    global _smart_report
    if _smart_report is None:
        _smart_report = SmartReportGenerator()
    return _smart_report


# 便捷函数
def ask(query: str) -> Dict:
    """
    一句话生成报表
    示例:
        ask("最近7天的销售额")
        ask("本月产品销售排名")
        ask("客户等级分布")
    """
    generator = get_smart_report()
    return generator.execute_report(query)


if __name__ == "__main__":
    # 测试
    test_queries = [
        "最近7天的销售额",
        "本月产品销售排名",
        "客户等级分布",
        "最近30天的收入趋势"
    ]
    
    for q in test_queries:
        print(f"\n查询: {q}")
        result = ask(q)
        if result["success"]:
            print(f"图表类型: {result['chart_type']}")
            print(f"标题: {result['title']}")
            print(f"SQL: {result['sql']}")
            print(f"数据: {result['data'][:3]}...")  # 只显示前3条
        else:
            print(f"错误: {result.get('error', '未知错误')}")

```
