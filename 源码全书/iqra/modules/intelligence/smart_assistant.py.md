# `iqra/modules/intelligence/smart_assistant.py`

> 路径：`iqra/modules/intelligence/smart_assistant.py` | 行数：423


---


```python
# -*- coding: utf-8 -*-
"""
智能助手核心
基于规则的智能问答和业务操作
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

import re
import json
from core.database import get_conn, close_conn
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class AssistantResponse:
    """助手响应"""
    question: str
    answer: str
    action: Optional[str] = None
    data: Optional[Dict] = None
    suggestions: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SmartAssistant:
    """智能助手"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(BASE_DIR, "data")
        
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "orders.db")
        
        # 预定义问答规则
        self.intents = {
            "sales_query": {
                "patterns": [
                    r"今天.*卖.*多少", r"今日.*销售",
                    r"(sales|revenue|销售|营收).*(today|今天|今日)",
                    r"今天.*收入", r"今日.*营业额",
                    r"今天.*订单"
                ],
                "handler": self._handle_sales_query
            },
            "inventory_query": {
                "patterns": [
                    r"库存.*多少", r"还有.*多少.*货",
                    r"(inventory|stock|库存).*(query|查询|how many)",
                    r"哪些.*缺货", r"库存不足",
                    r"低库存"
                ],
                "handler": self._handle_inventory_query
            },
            "customer_query": {
                "patterns": [
                    r"多少.*客户", r"客户.*数量",
                    r"(customer|client|客户).*(count|数量|how many)",
                    r"会员.*多少"
                ],
                "handler": self._handle_customer_query
            },
            "order_status": {
                "patterns": [
                    r"订单.*状态", r"查.*订单",
                    r"(order|订单).*(status|状态)",
                    r"订单号", r"待处理.*订单"
                ],
                "handler": self._handle_order_status
            },
            "report_request": {
                "patterns": [
                    r"生成.*报告", r"生成.*报表",
                    r"(generate|create|生成).*(report|报告|报表)",
                    r"给我.*报告", r"今日.*报告"
                ],
                "handler": self._handle_report_request
            },
            "prediction_request": {
                "patterns": [
                    r"预测.*销售", r"未来.*销售",
                    r"(predict|forecast|预测).*(sales|销售)",
                    r"下周.*卖.*多少"
                ],
                "handler": self._handle_prediction_request
            },
            "help": {
                "patterns": [
                    r"帮助", r"能.*做什么", r"功能",
                    r"(help|what can you do|功能).*",
                    r"怎么用"
                ],
                "handler": self._handle_help
            },
            "greeting": {
                "patterns": [
                    r"你好", r"hi", r"hello", r"早上好",
                    r"下午好", r"晚上好"
                ],
                "handler": self._handle_greeting
            }
        }
    
    def process(self, question: str) -> AssistantResponse:
        """处理用户问题"""
        question = question.strip()
        
        # 匹配意图
        for intent_name, intent_config in self.intents.items():
            for pattern in intent_config["patterns"]:
                if re.search(pattern, question, re.IGNORECASE):
                    return intent_config["handler"](question)
        
        # 默认回答
        return self._default_response(question)
    
    def _handle_sales_query(self, question: str) -> AssistantResponse:
        """处理销售查询"""
        try:
            conn = get_conn("orders.db")
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 今日销售
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(amount), 0)
                FROM orders
                WHERE DATE(created_at) = ? AND status != 'cancelled'
            """, (today,))
            count, total = cursor.fetchone()
            
            # 本月销售
            month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(amount), 0)
                FROM orders
                WHERE DATE(created_at) >= ? AND status != 'cancelled'
            """, (month_start,))
            month_count, month_total = cursor.fetchone()
            
            close_conn("orders.db")
            
            answer = f"""今日销售概况:
- 订单数: {count} 笔
- 销售额: ${total or 0:,.2f}
- 客单价: ${((total or 0) / count):,.2f} (共{count}笔)

本月累计:
- 订单数: {month_count} 笔
- 销售额: ${month_total or 0:,.2f}"""
            
            return AssistantResponse(
                question=question,
                answer=answer,
                action="sales_query",
                data={
                    "today": {"orders": count, "amount": total or 0},
                    "month": {"orders": month_count, "amount": month_total or 0}
                },
                suggestions=["查看库存状态", "生成销售报告", "查看客户统计"]
            )
        except Exception as e:
            return self._error_response(question, str(e))
    
    def _handle_inventory_query(self, question: str) -> AssistantResponse:
        """处理库存查询"""
        try:
            conn = get_conn("orders.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(stock), 0) FROM products")
            total, total_stock = cursor.fetchone()
            
            cursor.execute("SELECT name, stock, price FROM products WHERE stock <= 10 ORDER BY stock ASC")
            low_stock = [{"name": row[0], "stock": row[1], "price": row[2]} for row in cursor.fetchall()]
            
            close_conn("orders.db")
            
            answer = f"""库存概况:
- 商品种类: {total} 种
- 库存总量: {total_stock or 0} 件"""

            if low_stock:
                items = "\n".join([f"  - {item['name']}: {item['stock']}件 (建议补货)" for item in low_stock[:5]])
                answer += f"\n\n低库存预警 ({len(low_stock)}项):\n{items}"
            
            return AssistantResponse(
                question=question,
                answer=answer,
                action="inventory_query",
                data={"total": total, "total_stock": total_stock, "low_stock": low_stock},
                suggestions=["生成补货清单", "查看销售趋势", "查询客户"]
            )
        except Exception as e:
            return self._error_response(question, str(e))
    
    def _handle_customer_query(self, question: str) -> AssistantResponse:
        """处理客户查询"""
        try:
            conn = get_conn("orders.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM customers")
            total = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(DISTINCT customer_id) FROM orders 
                WHERE created_at >= datetime('now', '-7 days')
            """)
            active_week = cursor.fetchone()[0]
            
            close_conn("orders.db")
            
            answer = f"""客户统计:
- 总客户数: {total} 人
- 近7天活跃: {active_week} 人"""
            
            return AssistantResponse(
                question=question,
                answer=answer,
                action="customer_query",
                data={"total": total, "active_week": active_week},
                suggestions=["查看客户详情", "会员分析", "销售报告"]
            )
        except Exception as e:
            return self._error_response(question, str(e))
    
    def _handle_order_status(self, question: str) -> AssistantResponse:
        """处理订单状态查询"""
        try:
            conn = get_conn("orders.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT status, COUNT(*) FROM orders 
                GROUP BY status
            """)
            status_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            close_conn("orders.db")
            
            pending = status_counts.get('pending', 0)
            processing = status_counts.get('processing', 0)
            completed = status_counts.get('completed', 0)
            cancelled = status_counts.get('cancelled', 0)
            
            answer = f"""订单状态统计:
- 待处理: {pending} 笔
- 处理中: {processing} 笔
- 已完成: {completed} 笔
- 已取消: {cancelled} 笔"""
            
            if pending > 0:
                answer += f"\n\n注意: 有 {pending} 笔待处理订单，请及时处理！"
            
            return AssistantResponse(
                question=question,
                answer=answer,
                action="order_status",
                data=status_counts,
                suggestions=["查看待处理订单", "查看今日销售", "查看库存"]
            )
        except Exception as e:
            return self._error_response(question, str(e))
    
    def _handle_report_request(self, question: str) -> AssistantResponse:
        """处理报告请求"""
        try:
            if "今日" in question or "daily" in question.lower():
                report_type = "daily"
                report_name = "日报"
            elif "周" in question or "weekly" in question.lower():
                report_type = "weekly"
                report_name = "周报"
            elif "月" in question or "monthly" in question.lower():
                report_type = "monthly"
                report_name = "月报"
            else:
                report_type = "daily"
                report_name = "日报"
            
            from .report_generator import get_generator
            gen = get_generator()
            
            if report_type == "daily":
                report = gen.generate_daily_report()
            elif report_type == "weekly":
                report = gen.generate_weekly_report()
            elif report_type == "monthly":
                report = gen.generate_monthly_report()
            else:
                report = gen.generate_daily_report()
            
            answer = f"{report_name}已生成！\n\n标题: {report.title}\n摘要: {report.summary}\n\n包含: 销售统计、订单分析、库存状态等"
            
            return AssistantResponse(
                question=question,
                answer=answer,
                action="generate_report",
                data={"report_id": report.id, "title": report.title, "type": report_type},
                suggestions=["查看报告详情", "导出报告", "发送给团队成员"]
            )
        except Exception as e:
            return self._error_response(question, str(e))
    
    def _handle_prediction_request(self, question: str) -> AssistantResponse:
        """处理预测请求"""
        try:
            from .sales_predictor import get_predictor
            predictor = get_predictor()
            
            if "月" in question or "month" in question.lower():
                forecast = predictor.predict_next_month()
                period = "下月"
            else:
                forecast = predictor.predict_next_week()
                period = "下周"
            
            answer = f"""{period}销售预测:
- 预测销售额: ${forecast.predicted_amount:,.2f}
- 预测订单数: {forecast.predicted_orders} 笔
- 置信度: {forecast.confidence:.0f}%
- 趋势: {forecast.trend}

基于历史数据的分析预测，实际结果可能有偏差。"""
            
            if forecast.daily_breakdown:
                days_info = "\n".join([
                    f"  {d['date']} ({d.get('weekday', '')}): ${d['predicted_amount']:,.2f}"
                    for d in forecast.daily_breakdown[:5]
                ])
                answer += f"\n\n前5天预测:\n{days_info}"
            
            return AssistantResponse(
                question=question,
                answer=answer,
                action="prediction",
                data={
                    "predicted_amount": forecast.predicted_amount,
                    "predicted_orders": forecast.predicted_orders,
                    "confidence": forecast.confidence,
                    "trend": forecast.trend,
                    "daily_breakdown": forecast.daily_breakdown
                },
                suggestions=["查看详细预测", "查看销售趋势", "调整库存计划"]
            )
        except Exception as e:
            return self._error_response(question, str(e))
    
    def _handle_help(self, question: str) -> AssistantResponse:
        """处理帮助请求"""
        answer = """我是一企通智能助手，可以帮你:

查询功能:
- "今天卖了多少钱" - 查询今日销售
- "库存还有多少" - 查看库存状态
- "有多少客户" - 查看客户统计
- "查订单状态" - 查看订单处理进度

分析功能:
- "生成报告" - 生成经营报告
- "预测下周销售" - 销售预测

操作建议:
- 及时处理库存不足的预警
- 定期查看销售报告了解经营状况
- 关注销售预测，提前做好准备"""
        
        return AssistantResponse(
            question=question,
            answer=answer,
            action="help",
            suggestions=["查询今日销售", "查看库存", "生成报告"]
        )
    
    def _handle_greeting(self, question: str) -> AssistantResponse:
        """处理问候"""
        answer = f"你好！我是一企通智能助手。请问有什么可以帮你的？\n\n你可以尝试问我:\n- 今天卖了多少钱？\n- 库存还有多少？\n- 生成今天的报告"
        
        return AssistantResponse(
            question=question,
            answer=answer,
            action="greeting",
            suggestions=["查询今日销售", "查看库存", "生成报告"]
        )
    
    def _default_response(self, question: str) -> AssistantResponse:
        """默认响应"""
        answer = "抱歉，我不太明白你的问题。你可以尝试问我:\n\n- 今天卖了多少钱？\n- 库存还有多少？\n- 生成报告\n- 预测下周销售"
        
        return AssistantResponse(
            question=question,
            answer=answer,
            suggestions=["查询今日销售", "查看库存", "生成报告"]
        )
    
    def _error_response(self, question: str, error: str) -> AssistantResponse:
        """错误响应"""
        answer = f"处理你的问题'{question}'时出现错误: {error}\n\n请稍后重试或联系技术支持。"
        
        return AssistantResponse(
            question=question,
            answer=answer,
            suggestions=["查询今日销售", "查看库存", "帮助"]
        )


# 全局助手实例
_assistant = None

def get_assistant() -> SmartAssistant:
    """获取全局助手实例"""
    global _assistant
    if _assistant is None:
        _assistant = SmartAssistant()
    return _assistant

```
