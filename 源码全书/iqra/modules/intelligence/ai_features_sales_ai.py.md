# `iqra/modules/intelligence/ai_features_sales_ai.py`

> 路径：`iqra/modules/intelligence/ai_features_sales_ai.py` | 行数：384


---


```python
# -*- coding: utf-8 -*-
"""
销售分析 AI 模块
- 自动分析销售趋势
- 识别热销/滞销商品
- 预测未来销售
- 发现销售机会
"""

import sqlite3
from core.database import get_conn, close_conn
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
from modules.intelligence._compat import DATA_DIR
import os

ORDER_DB = os.path.join(DATA_DIR, "order.db")
PRODUCT_DB = os.path.join(DATA_DIR, "product.db")


class SalesAI:
    """AI 销售分析助手"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
    
    def get_sales_summary(self, days: int = 30) -> Dict:
        """
        获取销售概况
        
        Returns:
            {
                'total_revenue': 总营收,
                'total_orders': 总订单数,
                'total_items': 总商品数,
                'avg_order_value': 客单价,
                'daily_avg': 日均销售,
                'trend': '上升'/'下降'/'平稳',
                'top_products': [...],
                'comparison': 与上期对比
            }
        """
        # 本期数据
        current_period = self._get_period_sales(days)
        # 上期数据（同样天数）
        previous_period = self._get_period_sales(days, offset_days=days)
        
        # 计算趋势
        if previous_period['total_revenue'] > 0:
            revenue_change = (current_period['total_revenue'] - previous_period['total_revenue']) / previous_period['total_revenue']
            if revenue_change > 0.1:
                trend = '上升'
            elif revenue_change < -0.1:
                trend = '下降'
            else:
                trend = '平稳'
        else:
            trend = '新品期'
        
        # 热销商品
        top_products = self._get_top_products(days, limit=5)
        
        return {
            'total_revenue': round(current_period['total_revenue'], 2),
            'total_orders': current_period['total_orders'],
            'total_items': current_period['total_items'],
            'avg_order_value': round(current_period['avg_order_value'], 2),
            'daily_avg': round(current_period['total_revenue'] / days, 2),
            'trend': trend,
            'top_products': top_products,
            'comparison': {
                'revenue_change': f"{revenue_change*100:.1f}%" if 'revenue_change' in dir() else "N/A",
                'previous_revenue': round(previous_period['total_revenue'], 2)
            }
        }
    
    def _get_period_sales(self, days: int, offset_days: int = 0) -> Dict:
        """获取指定时间段销售数据"""
        end_date = datetime.now() - timedelta(days=offset_days)
        start_date = end_date - timedelta(days=days)
        
        conn = get_conn("order.db")
        c = conn.cursor()
        
        # 总营收和订单数
        c.execute('''
            SELECT COUNT(*), COALESCE(SUM(total_amount), 0), COALESCE(SUM(quantity), 0)
            FROM orders 
            WHERE created_at >= ? AND created_at <= ? AND status = '已完成'
        ''', (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        
        result = c.fetchone()
        close_conn("order.db")
        
        total_orders = result[0] or 0
        total_revenue = result[1] or 0
        total_items = result[2] or 0
        
        return {
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'total_items': total_items,
            'avg_order_value': total_revenue / total_orders if total_orders > 0 else 0
        }
    
    def _get_top_products(self, days: int, limit: int = 5) -> List[Dict]:
        """获取热销商品"""
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        conn = get_conn("order.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''
            SELECT product_name, 
                   SUM(quantity) as total_qty,
                   SUM(total_amount) as total_revenue,
                   COUNT(*) as order_count
            FROM orders 
            WHERE created_at >= ? AND status = '已完成'
            GROUP BY product_name
            ORDER BY total_qty DESC
            LIMIT ?
        ''', (start_date, limit))
        
        results = [dict(row) for row in c.fetchall()]
        close_conn("order.db")
        return results
    
    def get_sales_forecast(self, days: int = 7) -> Dict:
        """
        销售预测
        
        Returns:
            {
                'forecast_revenue': 预测营收,
                'forecast_orders': 预测订单数,
                'confidence': 置信度,
                'daily_breakdown': [...],
                'suggestion': 建议
            }
        """
        # 获取历史数据（最近90天）
        history = self._get_daily_sales(90)
        
        if len(history) < 7:
            return {
                'forecast_revenue': 0,
                'forecast_orders': 0,
                'confidence': 0,
                'daily_breakdown': [],
                'suggestion': '数据不足，需要至少一周的历史数据'
            }
        
        # 计算平均日销售
        revenues = [day['revenue'] for day in history]
        orders = [day['orders'] for day in history]
        
        avg_revenue = statistics.mean(revenues)
        avg_orders = statistics.mean(orders)
        
        # 计算趋势（最近7天 vs 前7天）
        if len(history) >= 14:
            recent_revenue = sum(day['revenue'] for day in history[:7])
            previous_revenue = sum(day['revenue'] for day in history[7:14])
            trend_factor = recent_revenue / previous_revenue if previous_revenue > 0 else 1
        else:
            trend_factor = 1
        
        # 预测
        forecast_revenue = avg_revenue * days * trend_factor
        forecast_orders = int(avg_orders * days * trend_factor)
        
        # 置信度
        confidence = min(len(history) / 30, 1.0)
        
        # 生成每日明细（考虑周内波动）
        daily_breakdown = []
        for i in range(days):
            date = datetime.now() + timedelta(days=i)
            weekday_factor = self._get_weekday_factor(date.weekday(), history)
            daily_revenue = avg_revenue * trend_factor * weekday_factor
            daily_breakdown.append({
                'date': date.strftime("%Y-%m-%d"),
                'weekday': date.strftime("%A"),
                'predicted_revenue': round(daily_revenue, 2),
                'predicted_orders': max(1, int(avg_orders * trend_factor * weekday_factor))
            })
        
        # 建议
        if trend_factor > 1.1:
            suggestion = "销售趋势向好，建议适当增加库存"
        elif trend_factor < 0.9:
            suggestion = "销售趋势下滑，建议开展促销活动"
        else:
            suggestion = "销售平稳，保持当前策略"
        
        return {
            'forecast_revenue': round(forecast_revenue, 2),
            'forecast_orders': forecast_orders,
            'confidence': round(confidence, 2),
            'daily_breakdown': daily_breakdown,
            'suggestion': suggestion
        }
    
    def _get_daily_sales(self, days: int) -> List[Dict]:
        """获取每日销售数据"""
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        conn = get_conn("order.db")
        c = conn.cursor()
        c.execute('''
            SELECT 
                DATE(created_at) as sale_date,
                COUNT(*) as orders,
                COALESCE(SUM(total_amount), 0) as revenue,
                COALESCE(SUM(quantity), 0) as items
            FROM orders 
            WHERE created_at >= ? AND status = '已完成'
            GROUP BY DATE(created_at)
            ORDER BY sale_date DESC
        ''', (start_date,))
        
        results = []
        for row in c.fetchall():
            results.append({
                'date': row[0],
                'orders': row[1],
                'revenue': row[2],
                'items': row[3]
            })
        
        close_conn("order.db")
        return results
    
    def _get_weekday_factor(self, weekday: int, history: List[Dict]) -> float:
        """计算星期几的销售因子"""
        if not history:
            return 1.0
        
        # 按星期几分组
        weekday_sales = defaultdict(list)
        for day in history:
            date = datetime.strptime(day['date'], "%Y-%m-%d")
            weekday_sales[date.weekday()].append(day['revenue'])
        
        if weekday not in weekday_sales or not weekday_sales[weekday]:
            return 1.0
        
        avg_all = statistics.mean([day['revenue'] for day in history])
        avg_weekday = statistics.mean(weekday_sales[weekday])
        
        return avg_weekday / avg_all if avg_all > 0 else 1.0
    
    def get_sales_opportunities(self) -> List[Dict]:
        """
        发现销售机会
        
        Returns:
            [
                {
                    'type': '关联销售'/'复购提醒'/'新品推荐',
                    'description': 描述,
                    'potential_revenue': 预计增收,
                    'action': 行动建议
                }
            ]
        """
        opportunities = []
        
        # 1. 关联销售机会（经常一起买的商品）
        associations = self._find_product_associations()
        for assoc in associations[:3]:
            opportunities.append({
                'type': '关联销售',
                'description': f"购买 '{assoc['product1']}' 的客户也常买 '{assoc['product2']}'",
                'potential_revenue': assoc['potential_revenue'],
                'action': f"在 '{assoc['product1']}' 页面推荐 '{assoc['product2']}'"
            })
        
        # 2. 复购提醒（客户上次购买距今较长）
        repurchase = self._find_repurchase_opportunities()
        for opp in repurchase[:3]:
            opportunities.append({
                'type': '复购提醒',
                'description': f"客户 '{opp['customer']}' 已 {opp['days_since']} 天未购买",
                'potential_revenue': opp['avg_order_value'],
                'action': f"联系客户推荐 '{opp['last_product']}'"
            })
        
        return opportunities
    
    def _find_product_associations(self) -> List[Dict]:
        """发现商品关联（购物篮分析）"""
        # 获取所有订单的商品组合
        conn = get_conn("order.db")
        c = conn.cursor()
        c.execute('''
            SELECT order_no, product_name
            FROM orders
            WHERE status = '已完成'
            ORDER BY order_no
        ''')
        
        orders = defaultdict(list)
        for row in c.fetchall():
            orders[row[0]].append(row[1])
        
        close_conn("order.db")
        
        # 统计商品共现
        co_occurrence = defaultdict(lambda: defaultdict(int))
        for products in orders.values():
            if len(products) > 1:
                for i, p1 in enumerate(products):
                    for p2 in products[i+1:]:
                        if p1 != p2:
                            co_occurrence[p1][p2] += 1
        
        # 找出最强关联
        associations = []
        for p1, related in co_occurrence.items():
            for p2, count in related.items():
                if count >= 2:  # 至少共同出现2次
                    associations.append({
                        'product1': p1,
                        'product2': p2,
                        'co_occurrence': count,
                        'potential_revenue': count * 50  # 估算
                    })
        
        associations.sort(key=lambda x: x['co_occurrence'], reverse=True)
        return associations
    
    def _find_repurchase_opportunities(self) -> List[Dict]:
        """发现复购机会"""
        conn = get_conn("order.db")
        c = conn.cursor()
        
        # 获取每个客户最近购买记录
        c.execute('''
            SELECT 
                customer_name,
                MAX(created_at) as last_purchase,
                AVG(total_amount) as avg_order
            FROM orders
            WHERE customer_name IS NOT NULL AND customer_name != ''
            GROUP BY customer_name
            HAVING last_purchase < date('now', '-30 days')
            ORDER BY last_purchase
            LIMIT 10
        ''')
        
        opportunities = []
        for row in c.fetchall():
            customer = row[0]
            last_date = datetime.strptime(row[1][:10], "%Y-%m-%d")
            days_since = (datetime.now() - last_date).days
            avg_value = row[2] or 0
            
            # 获取上次购买的商品
            c.execute('''
                SELECT product_name FROM orders
                WHERE customer_name = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (customer,))
            last_product = c.fetchone()[0] if c.fetchone() else ""
            
            opportunities.append({
                'customer': customer,
                'days_since': days_since,
                'avg_order_value': round(avg_value, 2),
                'last_product': last_product
            })
        
        close_conn("order.db")
        return opportunities


def get_sales_ai() -> SalesAI:
    """获取销售 AI 实例"""
    return SalesAI()

```
