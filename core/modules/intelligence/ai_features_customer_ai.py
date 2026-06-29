# -*- coding: utf-8 -*-
"""
客户洞察 AI 模块
- 客户分层（RFM模型）
- 流失预警
- 高价值客户识别
- 客户行为分析
"""

from core.database import get_conn, close_conn
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
from core.modules.intelligence._compat import DATA_DIR
import os

ORDER_DB = os.path.join(DATA_DIR, "order.db")
MEMBER_DB = os.path.join(DATA_DIR, "member.db")


class CustomerAI:
    """AI 客户洞察助手"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
    
    def analyze_customer(self, customer_name: str) -> Dict:
        """
        分析单个客户
        
        Returns:
            {
                'customer_name': 客户名,
                'total_orders': 总订单数,
                'total_spent': 总消费,
                'avg_order_value': 客单价,
                'last_purchase': 最近购买,
                'days_since_last': 距今天数,
                'favorite_products': 偏好商品,
                'customer_segment': 客户分层,
                'churn_risk': 流失风险,
                'suggestion': 建议
            }
        """
        conn = get_conn('order.db')
        # row_factory removed — get_conn() already sets Row
        c = conn.cursor()
        
        # 客户购买历史
        c.execute('''
            SELECT * FROM orders
            WHERE customer_name = ? AND status = '已完成'
            ORDER BY created_at DESC
        ''', (customer_name,))
        
        orders = [dict(row) for row in c.fetchall()]
        close_conn('order.db')
        
        if not orders:
            return {'error': f'未找到客户 {customer_name} 的购买记录'}
        
        total_orders = len(orders)
        total_spent = sum(o['total_amount'] or 0 for o in orders)
        avg_order = total_spent / total_orders if total_orders > 0 else 0
        
        last_purchase = orders[0]['created_at']
        # 处理 ISO 格式时间
        if 'T' in last_purchase:
            last_date = datetime.fromisoformat(last_purchase.replace('Z', '').replace('+00:00', ''))
        else:
            last_date = datetime.strptime(last_purchase[:19], "%Y-%m-%d %H:%M:%S")
        days_since = (datetime.now() - last_date).days
        
        # 偏好商品
        product_counts = defaultdict(int)
        for order in orders:
            product_counts[order['product_name']] += order['quantity'] or 0
        
        favorite_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # RFM 分析
        rfm = self._calculate_rfm(customer_name, orders)
        segment = self._segment_customer(rfm)
        churn_risk = self._assess_churn_risk(days_since, total_orders, rfm['frequency'])
        
        # 建议
        suggestion = self._generate_customer_suggestion(
            customer_name, segment, churn_risk, days_since, favorite_products
        )
        
        return {
            'customer_name': customer_name,
            'total_orders': total_orders,
            'total_spent': round(total_spent, 2),
            'avg_order_value': round(avg_order, 2),
            'last_purchase': last_purchase,
            'days_since_last': days_since,
            'favorite_products': [{'name': p[0], 'qty': p[1]} for p in favorite_products],
            'customer_segment': segment,
            'churn_risk': churn_risk,
            'rfm': rfm,
            'suggestion': suggestion
        }
    
    def _calculate_rfm(self, customer_name: str, orders: List[Dict]) -> Dict:
        """计算 RFM 指标"""
        if not orders:
            return {'recency': 0, 'frequency': 0, 'monetary': 0}
        
        # Recency: 距今天数（越小越好）
        created_at = orders[0]['created_at']
        if 'T' in created_at:
            last_date = datetime.fromisoformat(created_at.replace('Z', '').replace('+00:00', ''))
        else:
            last_date = datetime.strptime(created_at[:19], "%Y-%m-%d %H:%M:%S")
        recency = (datetime.now() - last_date).days
        
        # Frequency: 购买频率（90天内订单数）
        ninety_days_ago = datetime.now() - timedelta(days=90)
        recent_orders = []
        for o in orders:
            o_date = o['created_at']
            if 'T' in o_date:
                o_datetime = datetime.fromisoformat(o_date.replace('Z', '').replace('+00:00', ''))
            else:
                o_datetime = datetime.strptime(o_date[:19], "%Y-%m-%d %H:%M:%S")
            if o_datetime > ninety_days_ago:
                recent_orders.append(o)
        frequency = len(recent_orders)
        
        # Monetary: 消费金额
        monetary = sum(o['total_amount'] or 0 for o in orders)
        
        return {
            'recency': recency,
            'frequency': frequency,
            'monetary': round(monetary, 2)
        }
    
    def _segment_customer(self, rfm: Dict) -> str:
        """客户分层"""
        recency = rfm['recency']
        frequency = rfm['frequency']
        monetary = rfm['monetary']
        
        if recency <= 7 and frequency >= 3:
            return 'VIP客户'
        elif recency <= 30 and frequency >= 2:
            return '活跃客户'
        elif recency <= 60 and frequency >= 1:
            return '普通客户'
        elif recency <= 90:
            return '沉睡客户'
        else:
            return '流失风险'
    
    def _assess_churn_risk(self, days_since: int, total_orders: int, frequency: int) -> str:
        """评估流失风险"""
        if days_since > 90:
            return '高风险'
        elif days_since > 60 and frequency < 2:
            return '中风险'
        elif days_since > 30 and total_orders < 3:
            return '低风险'
        else:
            return '健康'
    
    def _generate_customer_suggestion(self, name: str, segment: str, 
                                     churn_risk: str, days_since: int,
                                     favorite_products: List) -> str:
        """生成客户维护建议"""
        suggestions = []
        
        if churn_risk == '高风险':
            suggestions.append(f"🚨 {name} 已 {days_since} 天未购买，流失风险高！")
            suggestions.append("建议：发送专属优惠券或电话回访")
        elif churn_risk == '中风险':
            suggestions.append(f"⚠️ {name} 有流失迹象，已 {days_since} 天未购买")
            suggestions.append("建议：推送偏好商品促销信息")
        
        if segment == 'VIP客户':
            suggestions.append("⭐ VIP客户，建议提供专属服务")
        elif segment == '活跃客户':
            suggestions.append("✅ 活跃客户，可推荐新品或升级服务")
        
        if favorite_products:
            fav_names = [p[0] for p in favorite_products[:2]]
            suggestions.append(f"偏好商品：{', '.join(fav_names)}")
        
        return "\n".join(suggestions) if suggestions else "客户状态正常"
    
    def get_customer_segments(self) -> Dict:
        """
        获取所有客户分层统计
        
        Returns:
            {
                'segments': {
                    'VIP客户': [...],
                    '活跃客户': [...],
                    '普通客户': [...],
                    '沉睡客户': [...],
                    '流失风险': [...]
                },
                'summary': {
                    'total_customers': 总数,
                    'vip_count': VIP数,
                    'at_risk_count': 风险数
                }
            }
        """
        # 获取所有客户
        conn = get_conn('order.db')
        c = conn.cursor()
        c.execute('''
            SELECT DISTINCT customer_name 
            FROM orders 
            WHERE customer_name IS NOT NULL AND customer_name != ''
        ''')
        
        customers = [row[0] for row in c.fetchall()]
        close_conn('order.db')
        
        segments = {
            'VIP客户': [],
            '活跃客户': [],
            '普通客户': [],
            '沉睡客户': [],
            '流失风险': []
        }
        
        for customer in customers:
            analysis = self.analyze_customer(customer)
            if 'error' not in analysis:
                segment = analysis['customer_segment']
                segments[segment].append({
                    'name': customer,
                    'total_spent': analysis['total_spent'],
                    'total_orders': analysis['total_orders'],
                    'last_purchase': analysis['last_purchase'],
                    'churn_risk': analysis['churn_risk']
                })
        
        # 排序
        for segment in segments:
            segments[segment].sort(key=lambda x: x['total_spent'], reverse=True)
        
        return {
            'segments': segments,
            'summary': {
                'total_customers': len(customers),
                'vip_count': len(segments['VIP客户']),
                'active_count': len(segments['活跃客户']),
                'at_risk_count': len(segments['流失风险']) + len(segments['沉睡客户'])
            }
        }
    
    def get_churn_alerts(self) -> List[Dict]:
        """
        获取流失预警列表
        
        Returns:
            [
                {
                    'customer_name': 客户名,
                    'risk_level': '高'/'中'/'低',
                    'days_since': 距今天数,
                    'last_purchase': 最近购买,
                    'total_spent': 总消费,
                    'suggested_action': 建议行动
                }
            ]
        """
        segments = self.get_customer_segments()
        alerts = []
        
        # 高风险：流失风险 + 沉睡客户
        for customer in segments['segments']['流失风险']:
            alerts.append({
                'customer_name': customer['name'],
                'risk_level': '高',
                'days_since': (datetime.now() - datetime.strptime(customer['last_purchase'][:10], "%Y-%m-%d")).days,
                'last_purchase': customer['last_purchase'],
                'total_spent': customer['total_spent'],
                'suggested_action': '立即联系，提供专属优惠或回访'
            })
        
        for customer in segments['segments']['沉睡客户']:
            alerts.append({
                'customer_name': customer['name'],
                'risk_level': '中',
                'days_since': (datetime.now() - datetime.strptime(customer['last_purchase'][:10], "%Y-%m-%d")).days,
                'last_purchase': customer['last_purchase'],
                'total_spent': customer['total_spent'],
                'suggested_action': '发送促销信息或新品推荐'
            })
        
        # 按风险等级和金额排序
        risk_order = {'高': 0, '中': 1, '低': 2}
        alerts.sort(key=lambda x: (risk_order.get(x['risk_level'], 3), -x['total_spent']))
        
        return alerts
    
    def get_high_value_customers(self, limit: int = 10) -> List[Dict]:
        """
        获取高价值客户
        
        Returns:
            [
                {
                    'name': 客户名,
                    'total_spent': 总消费,
                    'total_orders': 订单数,
                    'avg_order': 客单价,
                    'segment': 分层
                }
            ]
        """
        conn = get_conn('order.db')
        c = conn.cursor()
        c.execute('''
            SELECT 
                customer_name,
                COUNT(*) as orders,
                COALESCE(SUM(total_amount), 0) as total,
                COALESCE(AVG(total_amount), 0) as avg_order
            FROM orders
            WHERE customer_name IS NOT NULL AND customer_name != ''
            GROUP BY customer_name
            HAVING total > 0
            ORDER BY total DESC
            LIMIT ?
        ''', (limit,))
        
        customers = []
        for row in c.fetchall():
            customers.append({
                'name': row[0],
                'total_orders': row[1],
                'total_spent': round(row[2], 2),
                'avg_order': round(row[3], 2),
                'segment': '待分析'
            })
        
        close_conn('order.db')
        
        # 补充分层信息
        for customer in customers:
            analysis = self.analyze_customer(customer['name'])
            if 'error' not in analysis:
                customer['segment'] = analysis['customer_segment']
        
        return customers


def get_customer_ai() -> CustomerAI:
    """获取客户 AI 实例"""
    return CustomerAI()
