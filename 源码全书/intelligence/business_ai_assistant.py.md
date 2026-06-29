# `intelligence/business_ai_assistant.py`

> 路径：`intelligence/business_ai_assistant.py` | 行数：610


---


```python
# -*- coding: utf-8 -*-
"""
AI 智能助手 V2 - 业务场景专用
功能：
1. 智能客服 - 自动回复客户咨询
2. 销售预测 - 基于历史数据预测未来销量
3. 库存预警 - 智能补货建议
4. 数据洞察 - 自动分析业务数据
5. 自然语言查询 - "今年销售额最高的产品是什么？"
"""

import sys
import os
import json

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import threading
import time

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from core.modules.intelligence._compat import get_conn
from core.modules.intelligence._compat import DATA_DIR


class BusinessAIAssistant:
    """业务 AI 智能助手"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.context = {}
        self._load_context()
        
    def _load_context(self):
        """加载业务上下文"""
        self.context = {
            'business_name': '一企通',
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'modules': self._get_module_stats(),
        }
    
    def _get_module_stats(self) -> Dict:
        """获取各模块统计数据"""
        stats = {}
        
        # 订单统计
        try:
            conn = get_conn('order.db')
            cursor = conn.execute('SELECT COUNT(*), SUM(amount * quantity) FROM orders')
            row = cursor.fetchone()
            stats['orders'] = {'count': row[0], 'total_amount': row[1] or 0}
        except Exception:
            stats['orders'] = {'count': 0, 'total_amount': 0}
        
        # 产品统计
        try:
            conn = get_conn('product.db')
            cursor = conn.execute('SELECT COUNT(*), SUM(stock) FROM product')
            row = cursor.fetchone()
            stats['products'] = {'count': row[0], 'total_stock': row[1] or 0}
        except Exception:
            stats['products'] = {'count': 0, 'total_stock': 0}
        
        # 客户统计
        try:
            conn = get_conn('customer.db')
            cursor = conn.execute('SELECT COUNT(*) FROM customer')
            stats['customers'] = {'count': cursor.fetchone()[0]}
        except Exception:
            stats['customers'] = {'count': 0}
        
        # 会员统计
        try:
            conn = get_conn('member.db')
            cursor = conn.execute('SELECT COUNT(*) FROM member')
            stats['members'] = {'count': cursor.fetchone()[0]}
        except Exception:
            stats['members'] = {'count': 0}
        
        # 财务统计
        try:
            conn = get_conn('finance.db')
            cursor = conn.execute("SELECT SUM(amount) FROM finance WHERE type='income'")
            income = cursor.fetchone()[0] or 0
            cursor = conn.execute("SELECT SUM(ABS(amount)) FROM finance WHERE type='expense'")
            expense = cursor.fetchone()[0] or 0
            stats['finance'] = {'income': income, 'expense': expense, 'profit': income - expense}
        except Exception:
            stats['finance'] = {'income': 0, 'expense': 0, 'profit': 0}
        
        return stats
    
    # ═══════════════════════════════════════════
    # 1. 智能客服
    # ═══════════════════════════════════════════
    
    def customer_service(self, question: str) -> str:
        """智能客服 - 回答客户咨询"""
        question = question.lower().strip()
        
        # 常见问题匹配
        responses = {
            '价格': self._answer_price_question,
            '多少钱': self._answer_price_question,
            '优惠': self._answer_discount_question,
            '折扣': self._answer_discount_question,
            '库存': self._answer_stock_question,
            '有货': self._answer_stock_question,
            '发货': self._answer_shipping_question,
            '快递': self._answer_shipping_question,
            '售后': self._answer_aftersales_question,
            '退换': self._answer_aftersales_question,
            '会员': self._answer_membership_question,
            '积分': self._answer_membership_question,
        }
        
        for keyword, handler in responses.items():
            if keyword in question:
                return handler(question)
        
        # 默认回复
        return self._default_customer_service_response(question)
    
    def _answer_price_question(self, question: str) -> str:
        """回答价格相关问题"""
        try:
            conn = get_conn('product.db')
            cursor = conn.execute('SELECT name, price FROM product ORDER BY price DESC LIMIT 5')
            products = cursor.fetchall()
            
            if products:
                response = "我们的热门产品价格如下：\n\n"
                for name, price in products:
                    response += f"• {name}: ¥{price:.2f}\n"
                response += "\n如需了解具体产品的详细价格，请告诉我产品名称。"
                return response
            else:
                return "抱歉，目前产品信息暂时无法获取。请稍后再试或联系人工客服。"
        except Exception as e:
            return f"查询价格时出错，请稍后再试。"
    
    def _answer_stock_question(self, question: str) -> str:
        """回答库存相关问题"""
        try:
            conn = get_conn('product.db')
            cursor = conn.execute('SELECT name, stock FROM product WHERE stock > 0 ORDER BY stock DESC')
            products = cursor.fetchall()
            
            if products:
                response = "目前有货的产品：\n\n"
                for name, stock in products[:10]:
                    status = "充足" if stock > 20 else "紧张" if stock > 5 else "极少"
                    response += f"• {name}: 库存{stock}件 ({status})\n"
                return response
            else:
                return "抱歉，目前所有产品暂时缺货。新货预计3-5天内到达。"
        except Exception:
            return "库存查询暂时不可用，请稍后再试。"
    
    def _answer_discount_question(self, question: str) -> str:
        """回答优惠相关问题"""
        return "当前优惠活动：\n\n" \
               "🎉 新会员首单立减 ¥20\n" \
               "🎉 满 ¥199 减 ¥30\n" \
               "🎉 会员日（每月15日）全场8折\n\n" \
               "更多优惠请关注我们的公众号！"
    
    def _answer_shipping_question(self, question: str) -> str:
        """回答发货相关问题"""
        return "发货信息：\n\n" \
               "📦 下单后24小时内发货\n" \
               "📦 支持顺丰、圆通、中通\n" \
               "📦 满 ¥99 包邮\n" \
               "📦 一般3-5个工作日送达\n\n" \
               "您可以在订单管理中查看物流详情。"
    
    def _answer_aftersales_question(self, question: str) -> str:
        """回答售后相关问题"""
        return "售后服务政策：\n\n" \
               "✅ 7天无理由退换\n" \
               "✅ 15天质量问题包换\n" \
               "✅ 1年质保\n" \
               "✅ 终身技术支持\n\n" \
               "如需售后，请联系客服或提交售后申请。"
    
    def _answer_membership_question(self, question: str) -> str:
        """回答会员相关问题"""
        try:
            conn = get_conn('member.db')
            cursor = conn.execute('SELECT level, COUNT(*) FROM member GROUP BY level')
            levels = cursor.fetchall()
            
            response = "会员等级及权益：\n\n"
            for level, count in levels:
                response += f"🏅 {level}会员: {count}人\n"
            
            response += "\n会员权益：\n" \
                       "• 积分兑换\n" \
                       "• 专属折扣\n" \
                       "• 生日礼品\n" \
                       "• 优先客服\n\n" \
                       "消费满 ¥1000 自动升级银卡会员！"
            return response
        except Exception:
            return "会员系统暂时不可用，请稍后再试。"
    
    def _default_customer_service_response(self, question: str) -> str:
        """默认客服回复"""
        return f"感谢您的咨询！\n\n" \
               f"您的问题是：{question}\n\n" \
               f"我目前可以帮您解答：\n" \
               f"• 产品价格查询\n" \
               f"• 库存状态查询\n" \
               f"• 优惠活动咨询\n" \
               f"• 发货物流查询\n" \
               f"• 售后服务政策\n" \
               f"• 会员权益说明\n\n" \
               f"如需人工客服，请拨打：400-xxx-xxxx"
    
    # ═══════════════════════════════════════════
    # 2. 销售预测
    # ═══════════════════════════════════════════
    
    def sales_prediction(self, days: int = 7) -> Dict:
        """销售预测 - 基于历史数据预测未来销量"""
        try:
            # 获取历史销售数据
            conn = get_conn('order.db')
            cursor = conn.execute(
                "SELECT date(created_at) as d, SUM(amount * quantity) as total "
                "FROM orders GROUP BY d ORDER BY d DESC LIMIT 30"
            )
            history = cursor.fetchall()
            
            if not history or len(history) < 7:
                return {
                    'status': 'insufficient_data',
                    'message': '历史数据不足，需要至少7天的销售数据才能进行预测。',
                    'prediction': []
                }
            
            # 简单线性预测
            amounts = [row[1] for row in history]
            avg_amount = sum(amounts) / len(amounts)
            trend = (amounts[0] - amounts[-1]) / len(amounts)
            
            predictions = []
            for i in range(1, days + 1):
                predicted = avg_amount + trend * i
                predicted = max(predicted, 0)  # 不能为负数
                date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
                predictions.append({
                    'date': date,
                    'predicted_amount': round(predicted, 2),
                    'confidence': max(0.5, 1 - i * 0.05)  # 置信度随天数递减
                })
            
            return {
                'status': 'success',
                'message': f'基于过去{len(history)}天数据，预测未来{days}天销售额',
                'prediction': predictions,
                'avg_daily': round(avg_amount, 2),
                'trend': '上升' if trend > 0 else '下降' if trend < 0 else '平稳'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'预测失败: {str(e)}',
                'prediction': []
            }
    
    # ═══════════════════════════════════════════
    # 3. 库存预警
    # ═══════════════════════════════════════════
    
    def stock_alert(self) -> Dict:
        """库存预警 - 智能补货建议"""
        try:
            conn = get_conn('product.db')
            
            # 获取低库存产品
            cursor = conn.execute(
                'SELECT name, stock, price, category FROM product WHERE stock < 10 ORDER BY stock ASC'
            )
            low_stock = cursor.fetchall()
            
            # 获取销售速度（最近7天）
            try:
                order_conn = get_conn('order.db')
                cursor = order_conn.execute(
                    "SELECT product, SUM(quantity) as sold "
                    "FROM orders WHERE created_at >= date('now', '-7 days') "
                    "GROUP BY product"
                )
                sales_speed = {row[0]: row[1] for row in cursor.fetchall()}
            except Exception:
                sales_speed = {}
            
            alerts = []
            for name, stock, price, category in low_stock:
                sold = sales_speed.get(name, 0)
                
                # 计算建议补货量
                if sold > 0:
                    days_remaining = stock / (sold / 7)
                    suggested_restock = max(sold * 2, 20)  # 补2周销量或最低20件
                else:
                    days_remaining = 999
                    suggested_restock = 20
                
                urgency = 'high' if stock < 5 else 'medium' if stock < 10 else 'low'
                
                alerts.append({
                    'product': name,
                    'current_stock': stock,
                    'category': category,
                    'sold_7days': sold,
                    'days_remaining': round(days_remaining, 1),
                    'suggested_restock': int(suggested_restock),
                    'urgency': urgency,
                    'restock_cost': round(suggested_restock * price, 2)
                })
            
            return {
                'status': 'success',
                'alert_count': len(alerts),
                'alerts': alerts,
                'summary': {
                    'high_urgency': len([a for a in alerts if a['urgency'] == 'high']),
                    'medium_urgency': len([a for a in alerts if a['urgency'] == 'medium']),
                    'total_restock_cost': round(sum(a['restock_cost'] for a in alerts), 2)
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'库存预警失败: {str(e)}',
                'alerts': []
            }
    
    # ═══════════════════════════════════════════
    # 4. 数据洞察
    # ═══════════════════════════════════════════
    
    def data_insights(self) -> Dict:
        """数据洞察 - 自动分析业务数据"""
        insights = []
        
        try:
            # 1. 销售趋势分析
            conn = get_conn('order.db')
            cursor = conn.execute(
                "SELECT date(created_at) as d, SUM(amount * quantity) as total "
                "FROM orders GROUP BY d ORDER BY d DESC LIMIT 7"
            )
            weekly_sales = cursor.fetchall()
            
            if weekly_sales:
                amounts = [row[1] for row in weekly_sales]
                avg = sum(amounts) / len(amounts)
                latest = amounts[0]
                
                if latest > avg * 1.2:
                    insights.append({
                        'type': 'positive',
                        'title': '销售额增长',
                        'content': f'今日销售额 ¥{latest:.2f}，高于7日均值 ¥{avg:.2f}，增长 {(latest/avg-1)*100:.1f}%'
                    })
                elif latest < avg * 0.8:
                    insights.append({
                        'type': 'warning',
                        'title': '销售额下降',
                        'content': f'今日销售额 ¥{latest:.2f}，低于7日均值 ¥{avg:.2f}，下降 {(1-latest/avg)*100:.1f}%'
                    })
            
            # 2. 热销产品分析
            cursor = conn.execute(
                "SELECT product, SUM(quantity) as total_qty, SUM(amount * quantity) as total_amount "
                "FROM orders GROUP BY product ORDER BY total_qty DESC LIMIT 3"
            )
            top_products = cursor.fetchall()
            
            if top_products:
                insights.append({
                    'type': 'info',
                    'title': '热销产品 TOP3',
                    'content': '\n'.join([f'{i+1}. {p[0]}: 销量{p[1]}件，金额¥{p[2]:.2f}' 
                                         for i, p in enumerate(top_products)])
                })
            
            # 3. 库存预警
            stock_data = self.stock_alert()
            if stock_data['status'] == 'success' and stock_data['alert_count'] > 0:
                insights.append({
                    'type': 'warning',
                    'title': f'库存预警 ({stock_data["alert_count"]}个产品)',
                    'content': f'有{stock_data["summary"]["high_urgency"]}个产品库存紧急，建议及时补货。'
                })
            
            # 4. 会员分析
            try:
                member_conn = get_conn('member.db')
                cursor = member_conn.execute('SELECT level, COUNT(*) FROM member GROUP BY level')
                member_levels = cursor.fetchall()
                
                if member_levels:
                    total_members = sum(m[1] for m in member_levels)
                    insights.append({
                        'type': 'info',
                        'title': '会员概况',
                        'content': f'共有会员{total_members}人，' + 
                                  '，'.join([f'{m[0]}: {m[1]}人' for m in member_levels])
                    })
            except Exception as e:
                print(f"[business_ai_assistant] 获取会员概况失败: {e}")
            
            return {
                'status': 'success',
                'insight_count': len(insights),
                'insights': insights
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'数据洞察失败: {str(e)}',
                'insights': []
            }
    
    # ═══════════════════════════════════════════
    # 5. 自然语言查询
    # ═══════════════════════════════════════════
    
    def natural_language_query(self, query: str) -> str:
        """自然语言查询 - 用日常语言查询业务数据"""
        query = query.lower().strip()
        
        # 销售额查询
        if any(kw in query for kw in ['销售额', '收入', '卖了多少钱', '营收']):
            return self._query_sales(query)
        
        # 订单查询
        if any(kw in query for kw in ['订单', '多少单', '销量']):
            return self._query_orders(query)
        
        # 产品查询
        if any(kw in query for kw in ['产品', '商品', '库存']):
            return self._query_products(query)
        
        # 客户查询
        if any(kw in query for kw in ['客户', '顾客', '会员']):
            return self._query_customers(query)
        
        # 财务查询
        if any(kw in query for kw in ['利润', '盈利', '赚钱', '财务']):
            return self._query_finance(query)
        
        # 默认回复
        return self._default_query_response(query)
    
    def _query_sales(self, query: str) -> str:
        """查询销售额"""
        try:
            conn = get_conn('order.db')
            
            # 今日销售额
            if '今天' in query or '今日' in query:
                cursor = conn.execute(
                    "SELECT SUM(amount * quantity) FROM orders WHERE date(created_at) = date('now')"
                )
                amount = cursor.fetchone()[0] or 0
                return f"今日销售额：¥{amount:.2f}"
            
            # 本月销售额
            if '本月' in query or '这个月' in query:
                cursor = conn.execute(
                    "SELECT SUM(amount * quantity) FROM orders WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
                )
                amount = cursor.fetchone()[0] or 0
                return f"本月销售额：¥{amount:.2f}"
            
            # 总销售额
            cursor = conn.execute("SELECT SUM(amount * quantity) FROM orders")
            amount = cursor.fetchone()[0] or 0
            return f"总销售额：¥{amount:.2f}"
            
        except Exception:
            return "查询销售额失败，请稍后再试。"
    
    def _query_orders(self, query: str) -> str:
        """查询订单"""
        try:
            conn = get_conn('order.db')
            
            if '今天' in query or '今日' in query:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM orders WHERE date(created_at) = date('now')"
                )
                count = cursor.fetchone()[0]
                return f"今日订单数：{count}单"
            
            cursor = conn.execute("SELECT COUNT(*) FROM orders")
            count = cursor.fetchone()[0]
            return f"总订单数：{count}单"
            
        except Exception:
            return "查询订单失败，请稍后再试。"
    
    def _query_products(self, query: str) -> str:
        """查询产品"""
        try:
            conn = get_conn('product.db')
            
            if '库存' in query:
                cursor = conn.execute('SELECT COUNT(*), SUM(stock) FROM product')
                count, stock = cursor.fetchone()
                return f"共有{count}种产品，总库存{stock}件"
            
            cursor = conn.execute('SELECT COUNT(*) FROM product')
            count = cursor.fetchone()[0]
            return f"共有{count}种产品"
            
        except Exception:
            return "查询产品失败，请稍后再试。"
    
    def _query_customers(self, query: str) -> str:
        """查询客户"""
        try:
            conn = get_conn('customer.db')
            cursor = conn.execute('SELECT COUNT(*) FROM customer')
            count = cursor.fetchone()[0]
            return f"共有{count}位客户"
        except Exception:
            return "查询客户失败，请稍后再试。"
    
    def _query_finance(self, query: str) -> str:
        """查询财务"""
        try:
            conn = get_conn('finance.db')
            
            cursor = conn.execute("SELECT SUM(amount) FROM finance WHERE type='income'")
            income = cursor.fetchone()[0] or 0
            
            cursor = conn.execute("SELECT SUM(ABS(amount)) FROM finance WHERE type='expense'")
            expense = cursor.fetchone()[0] or 0
            
            profit = income - expense
            
            return f"财务概况：\n" \
                   f"总收入：¥{income:.2f}\n" \
                   f"总支出：¥{expense:.2f}\n" \
                   f"净利润：¥{profit:.2f}"
        except Exception:
            return "查询财务失败，请稍后再试。"
    
    def _default_query_response(self, query: str) -> str:
        """默认查询回复"""
        return f"抱歉，我暂时无法理解 '{query}'。\n\n" \
               f"您可以尝试以下查询：\n" \
               f"• 今天销售额多少？\n" \
               f"• 本月订单有多少？\n" \
               f"• 产品库存情况？\n" \
               f"• 客户总数？\n" \
               f"• 财务利润如何？"


# ═══════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════

def get_ai_assistant() -> BusinessAIAssistant:
    """获取 AI 助手实例"""
    return BusinessAIAssistant()


# 测试
if __name__ == '__main__':
    ai = BusinessAIAssistant()
    
    print("=" * 50)
    print("AI 智能助手 V2 测试")
    print("=" * 50)
    
    # 测试智能客服
    print("\n1. 智能客服测试:")
    print(ai.customer_service("你们产品价格多少？"))
    
    # 测试销售预测
    print("\n2. 销售预测测试:")
    prediction = ai.sales_prediction(7)
    print(json.dumps(prediction, ensure_ascii=False, indent=2))
    
    # 测试库存预警
    print("\n3. 库存预警测试:")
    alerts = ai.stock_alert()
    print(json.dumps(alerts, ensure_ascii=False, indent=2))
    
    # 测试数据洞察
    print("\n4. 数据洞察测试:")
    insights = ai.data_insights()
    print(json.dumps(insights, ensure_ascii=False, indent=2))
    
    # 测试自然语言查询
    print("\n5. 自然语言查询测试:")
    print(ai.natural_language_query("今天销售额多少？"))
    print(ai.natural_language_query("库存情况如何？"))

```
