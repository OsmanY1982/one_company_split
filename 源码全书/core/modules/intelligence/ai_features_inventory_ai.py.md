# `core/modules/intelligence/ai_features_inventory_ai.py`

> 路径：`core/modules/intelligence/ai_features_inventory_ai.py` | 行数：286


---


```python
# -*- coding: utf-8 -*-
"""
智能库存预测模块
- 基于历史销售数据预测未来需求
- 自动计算安全库存和补货点
- 识别滞销商品
"""

from core.database import get_conn, close_conn
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from core.modules.intelligence._compat import DATA_DIR
import os

PRODUCT_DB = os.path.join(DATA_DIR, "product.db")
ORDER_DB = os.path.join(DATA_DIR, "order.db")


class InventoryAI:
    """AI 库存助手"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        
    def _get_product_sales_history(self, product_name: str, days: int = 30) -> List[Dict]:
        """获取商品历史销售数据"""
        conn = get_conn('order.db')
        # row_factory removed — get_conn() already sets Row
        c = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        c.execute('''
            SELECT created_at, quantity, unit_price 
            FROM orders 
            WHERE product_name = ? AND created_at >= ? AND status = '已完成'
            ORDER BY created_at
        ''', (product_name, start_date))
        
        results = [dict(row) for row in c.fetchall()]
        close_conn('order.db')
        return results
    
    def predict_demand(self, product_name: str, forecast_days: int = 7) -> Dict:
        """
        预测未来需求量
        
        Returns:
            {
                'predicted_daily': 预测日均销量,
                'predicted_weekly': 预测周销量,
                'confidence': 置信度 (0-1),
                'trend': '上升'/'下降'/'平稳',
                'suggestion': 建议文本
            }
        """
        history = self._get_product_sales_history(product_name, days=60)
        
        if len(history) < 3:
            return {
                'predicted_daily': 0,
                'predicted_weekly': 0,
                'confidence': 0,
                'trend': '数据不足',
                'suggestion': '销售数据不足，无法预测。建议积累至少一周的数据。'
            }
        
        # 计算日均销量（最近30天）
        recent_sales = self._get_product_sales_history(product_name, days=30)
        daily_quantities = {}
        for sale in recent_sales:
            date = sale['created_at'][:10] if sale['created_at'] else datetime.now().strftime("%Y-%m-%d")
            daily_quantities[date] = daily_quantities.get(date, 0) + sale['quantity']
        
        daily_values = list(daily_quantities.values())
        avg_daily = statistics.mean(daily_values) if daily_values else 0
        
        # 计算趋势（最近7天 vs 前7天）
        recent_7 = self._get_product_sales_history(product_name, days=7)
        previous_7 = self._get_product_sales_history(product_name, days=14)
        previous_7 = [s for s in previous_7 if s not in recent_7]
        
        recent_total = sum(s['quantity'] for s in recent_7)
        previous_total = sum(s['quantity'] for s in previous_7)
        
        if previous_total > 0:
            trend_ratio = (recent_total - previous_total) / previous_total
            if trend_ratio > 0.2:
                trend = '上升'
            elif trend_ratio < -0.2:
                trend = '下降'
            else:
                trend = '平稳'
        else:
            trend = '新品'
        
        # 预测未来销量（考虑趋势）
        if trend == '上升':
            predicted_daily = avg_daily * 1.2
        elif trend == '下降':
            predicted_daily = avg_daily * 0.8
        else:
            predicted_daily = avg_daily
        
        # 置信度（数据越多越准）
        confidence = min(len(history) / 30, 1.0)
        
        # 生成建议
        suggestion = self._generate_suggestion(product_name, predicted_daily, forecast_days, trend)
        
        return {
            'predicted_daily': round(predicted_daily, 1),
            'predicted_weekly': round(predicted_daily * 7, 1),
            'confidence': round(confidence, 2),
            'trend': trend,
            'suggestion': suggestion
        }
    
    def _generate_suggestion(self, product_name: str, predicted_daily: float, 
                            forecast_days: int, trend: str) -> str:
        """生成库存建议"""
        # 获取当前库存
        conn = get_conn('product.db')
        c = conn.cursor()
        c.execute('SELECT stock, min_stock FROM product WHERE name = ?', (product_name,))
        result = c.fetchone()
        close_conn('product.db')
        
        if not result:
            return f"未找到商品 '{product_name}' 的库存信息"
        
        current_stock, min_stock = result
        predicted_need = predicted_daily * forecast_days
        
        suggestions = []
        
        if current_stock <= (min_stock or 0):
            suggestions.append(f"🚨 库存告急！当前库存 {current_stock}，已低于安全库存 {min_stock}")
            suggestions.append(f"建议立即补货至少 {int(predicted_need * 2)} 件")
        elif current_stock < predicted_need:
            suggestions.append(f"⚠️ 库存偏低。当前 {current_stock}，预测{forecast_days}天需要 {int(predicted_need)} 件")
            suggestions.append(f"建议补货 {int(predicted_need * 1.5 - current_stock)} 件")
        elif current_stock > predicted_need * 3:
            suggestions.append(f"📦 库存充足。当前 {current_stock}，预计可售 {int(current_stock / predicted_daily)} 天")
            if trend == '下降':
                suggestions.append("销量趋势下降，建议控制进货量避免积压")
        else:
            suggestions.append(f"✅ 库存合理。当前 {current_stock}，预计可售 {int(current_stock / predicted_daily)} 天")
        
        if trend == '上升':
            suggestions.append("📈 销量上升趋势，建议适当增加库存")
        elif trend == '下降':
            suggestions.append("📉 销量下降趋势，注意控制库存避免积压")
        
        return "\n".join(suggestions)
    
    def get_reorder_suggestions(self) -> List[Dict]:
        """
        获取所有需要补货的商品建议
        
        Returns:
            [
                {
                    'product_name': 商品名,
                    'current_stock': 当前库存,
                    'suggested_qty': 建议补货量,
                    'urgency': '紧急'/'建议'/'正常',
                    'reason': 原因
                }
            ]
        """
        conn = get_conn('product.db')
        # row_factory removed — get_conn() already sets Row
        c = conn.cursor()
        c.execute('SELECT name, stock, min_stock FROM product WHERE stock > 0')
        products = [dict(row) for row in c.fetchall()]
        close_conn('product.db')
        
        suggestions = []
        for product in products:
            name = product['name']
            stock = product['stock'] or 0
            min_stock = product['min_stock'] or 0
            
            prediction = self.predict_demand(name, forecast_days=7)
            predicted_weekly = prediction['predicted_weekly']
            
            if stock <= min_stock:
                urgency = '紧急'
                reason = f"库存({stock})低于安全库存({min_stock})"
                suggested_qty = int(predicted_weekly * 2)
            elif stock < predicted_weekly:
                urgency = '建议'
                reason = f"库存({stock})低于周预测销量({predicted_weekly:.0f})"
                suggested_qty = int(predicted_weekly * 1.5 - stock)
            else:
                continue
            
            suggestions.append({
                'product_name': name,
                'current_stock': stock,
                'suggested_qty': max(suggested_qty, 1),
                'urgency': urgency,
                'reason': reason
            })
        
        # 按紧急程度排序
        urgency_order = {'紧急': 0, '建议': 1}
        suggestions.sort(key=lambda x: urgency_order.get(x['urgency'], 2))
        
        return suggestions
    
    def get_slow_moving_products(self, days: int = 30) -> List[Dict]:
        """
        识别滞销商品
        
        Returns:
            [
                {
                    'product_name': 商品名,
                    'current_stock': 当前库存,
                    'days_since_last_sale': 距上次销售天数,
                    'suggestion': 建议
                }
            ]
        """
        conn = get_conn('product.db')
        # row_factory removed — get_conn() already sets Row
        c = conn.cursor()
        c.execute('SELECT name, stock FROM product WHERE stock > 0')
        products = [dict(row) for row in c.fetchall()]
        close_conn('product.db')
        
        slow_moving = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for product in products:
            name = product['name']
            stock = product['stock']
            
            # 查询最近销售记录
            conn = get_conn('order.db')
            c = conn.cursor()
            c.execute('''
                SELECT MAX(created_at) as last_sale 
                FROM orders 
                WHERE product_name = ? AND status = '已完成'
            ''', (name,))
            result = c.fetchone()
            close_conn('order.db')
            
            if result and result[0]:
                # 处理 ISO 格式时间
                date_str = result[0]
                if 'T' in date_str:
                    last_sale = datetime.fromisoformat(date_str.replace('Z', '+00:00').replace('+00:00', ''))
                else:
                    last_sale = datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
                days_since = (datetime.now() - last_sale).days
                
                if days_since > days:
                    slow_moving.append({
                        'product_name': name,
                        'current_stock': stock,
                        'days_since_last_sale': days_since,
                        'suggestion': f"已{days_since}天未售出，建议促销清仓或下架"
                    })
            else:
                # 从未销售过
                slow_moving.append({
                    'product_name': name,
                    'current_stock': stock,
                    'days_since_last_sale': -1,
                    'suggestion': "从未售出，建议检查是否上架或调整定价"
                })
        
        # 按滞销天数排序
        slow_moving.sort(key=lambda x: x['days_since_last_sale'], reverse=True)
        return slow_moving


# 便捷函数
def get_inventory_ai() -> InventoryAI:
    """获取库存 AI 实例"""
    return InventoryAI()

```
