# `core/modules/intelligence/ai_features_pricing_ai.py`

> 路径：`core/modules/intelligence/ai_features_pricing_ai.py` | 行数：300


---


```python
# -*- coding: utf-8 -*-
"""
智能定价模块
- 基于成本、竞品、销量自动建议售价
- 识别定价过高/过低的商品
- 促销定价建议
"""

from core.database import get_conn, close_conn
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from core.modules.intelligence._compat import DATA_DIR
import os

PRODUCT_DB = os.path.join(DATA_DIR, "product.db")
ORDER_DB = os.path.join(DATA_DIR, "order.db")


class PricingAI:
    """AI 定价助手"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
    
    def analyze_pricing(self, product_name: str) -> Dict:
        """
        分析商品定价是否合理
        
        Returns:
            {
                'current_price': 当前售价,
                'cost_price': 成本价,
                'profit_margin': 当前利润率,
                'avg_market_price': 平均市场价（基于历史销售）,
                'suggested_price': 建议售价,
                'price_trend': 价格趋势,
                'suggestion': 建议文本
            }
        """
        conn = get_conn('product.db')
        # row_factory removed — get_conn() already sets Row
        c = conn.cursor()
        c.execute('''
            SELECT name, price, cost_price, stock 
            FROM product 
            WHERE name = ?
        ''', (product_name,))
        product = c.fetchone()
        close_conn('product.db')
        
        if not product:
            return {'error': f'未找到商品: {product_name}'}
        
        product = dict(product)
        current_price = product['price'] or 0
        cost_price = product['cost_price'] or 0
        
        # 获取历史销售价格
        conn = get_conn('order.db')
        c = conn.cursor()
        c.execute('''
            SELECT unit_price, quantity, created_at
            FROM orders 
            WHERE product_name = ? AND status = '已完成'
            ORDER BY created_at DESC
            LIMIT 100
        ''', (product_name,))
        sales = c.fetchall()
        close_conn('order.db')
        
        if not sales:
            return {
                'current_price': current_price,
                'cost_price': cost_price,
                'profit_margin': self._calc_margin(current_price, cost_price),
                'avg_market_price': current_price,
                'suggested_price': current_price,
                'price_trend': '无数据',
                'suggestion': '暂无销售数据，建议参考成本价和市场行情定价'
            }
        
        # 计算平均售价（加权）
        total_value = sum(s[0] * s[1] for s in sales)
        total_qty = sum(s[1] for s in sales)
        avg_price = total_value / total_qty if total_qty > 0 else current_price
        
        # 价格趋势（最近10笔 vs 之前10笔）
        prices = [s[0] for s in sales]
        if len(prices) >= 20:
            recent_avg = statistics.mean(prices[:10])
            previous_avg = statistics.mean(prices[10:20])
            if recent_avg > previous_avg * 1.05:
                price_trend = '上涨'
            elif recent_avg < previous_avg * 0.95:
                price_trend = '下降'
            else:
                price_trend = '稳定'
        else:
            price_trend = '数据不足'
        
        # 建议售价
        suggested_price = self._suggest_price(current_price, cost_price, avg_price, sales)
        
        # 生成建议
        suggestion = self._generate_pricing_suggestion(
            current_price, cost_price, avg_price, suggested_price, price_trend
        )
        
        return {
            'current_price': current_price,
            'cost_price': cost_price,
            'profit_margin': self._calc_margin(current_price, cost_price),
            'avg_market_price': round(avg_price, 2),
            'suggested_price': round(suggested_price, 2),
            'price_trend': price_trend,
            'suggestion': suggestion
        }
    
    def _calc_margin(self, price: float, cost: float) -> float:
        """计算利润率"""
        if cost <= 0:
            return 100.0
        return round((price - cost) / price * 100, 1)
    
    def _suggest_price(self, current: float, cost: float, avg_market: float, 
                      sales: List) -> float:
        """智能建议售价"""
        if cost <= 0:
            return current
        
        # 基础：成本 + 合理利润（30%毛利）
        base_price = cost / 0.7
        
        # 考虑市场平均价
        if avg_market > 0:
            # 取成本定价和市场价的加权平均
            suggested = base_price * 0.6 + avg_market * 0.4
        else:
            suggested = base_price
        
        # 考虑销量因素（如果最近销量下降，可能需要降价）
        if len(sales) >= 20:
            recent_qty = sum(s[1] for s in sales[:10])
            previous_qty = sum(s[1] for s in sales[10:20])
            if previous_qty > 0 and recent_qty < previous_qty * 0.7:
                # 销量下降明显，建议降价促销
                suggested *= 0.9
        
        # 确保不低于成本
        suggested = max(suggested, cost * 1.1)
        
        return round(suggested, 2)
    
    def _generate_pricing_suggestion(self, current: float, cost: float, 
                                    avg_market: float, suggested: float,
                                    trend: str) -> str:
        """生成定价建议文本"""
        suggestions = []
        
        margin = self._calc_margin(current, cost)
        
        if margin < 10:
            suggestions.append(f"⚠️ 利润率过低（{margin}%），建议涨价至 ¥{suggested}")
        elif margin > 80:
            suggestions.append(f"💰 利润率很高（{margin}%），但注意可能影响销量")
        
        if suggested > current * 1.1:
            suggestions.append(f"📈 建议涨价到 ¥{suggested}（当前 ¥{current}）")
        elif suggested < current * 0.9:
            suggestions.append(f"📉 建议降价到 ¥{suggested}（当前 ¥{current}）")
        else:
            suggestions.append(f"✅ 当前定价合理（¥{current}）")
        
        if trend == '上涨':
            suggestions.append("价格趋势上涨，市场接受度好")
        elif trend == '下降':
            suggestions.append("价格趋势下降，可能需要促销刺激")
        
        return "\n".join(suggestions)
    
    def get_pricing_opportunities(self) -> List[Dict]:
        """
        发现定价优化机会
        
        Returns:
            [
                {
                    'product_name': 商品名,
                    'opportunity': '涨价'/'降价'/'促销',
                    'current_price': 当前价,
                    'suggested_price': 建议价,
                    'potential_profit_increase': 预计利润提升,
                    'reason': 原因
                }
            ]
        """
        conn = get_conn('product.db')
        # row_factory removed — get_conn() already sets Row
        c = conn.cursor()
        c.execute('SELECT name, price, cost_price FROM product WHERE stock > 0')
        products = [dict(row) for row in c.fetchall()]
        close_conn('product.db')
        
        opportunities = []
        
        for product in products:
            name = product['name']
            analysis = self.analyze_pricing(name)
            
            if 'error' in analysis:
                continue
            
            current = analysis['current_price']
            suggested = analysis['suggested_price']
            cost = analysis['cost_price']
            
            if suggested > current * 1.15:
                opportunity = '涨价'
                potential = (suggested - current) * self._get_monthly_sales_qty(name)
                reason = f"建议涨价 {((suggested/current-1)*100):.0f}%，预计月增收 ¥{potential:.0f}"
            elif suggested < current * 0.85:
                opportunity = '降价'
                potential = (suggested - cost) * self._get_monthly_sales_qty(name) * 1.3 - (current - cost) * self._get_monthly_sales_qty(name)
                reason = f"建议降价促销，预计通过销量提升月增收 ¥{potential:.0f}"
            else:
                continue
            
            opportunities.append({
                'product_name': name,
                'opportunity': opportunity,
                'current_price': current,
                'suggested_price': suggested,
                'potential_profit_increase': round(potential, 2),
                'reason': reason
            })
        
        # 按潜在收益排序
        opportunities.sort(key=lambda x: x['potential_profit_increase'], reverse=True)
        return opportunities[:10]  # 返回前10个机会
    
    def _get_monthly_sales_qty(self, product_name: str) -> int:
        """获取商品近30天销量"""
        conn = get_conn('order.db')
        c = conn.cursor()
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        c.execute('''
            SELECT COALESCE(SUM(quantity), 0)
            FROM orders 
            WHERE product_name = ? AND created_at >= ? AND status = '已完成'
        ''', (product_name, start_date))
        result = c.fetchone()
        close_conn('order.db')
        return result[0] if result else 0
    
    def get_promotion_suggestions(self) -> List[Dict]:
        """
        获取促销建议
        
        Returns:
            [
                {
                    'product_name': 商品名,
                    'suggestion': 建议,
                    'discount_rate': 建议折扣,
                    'expected_effect': 预期效果
                }
            ]
        """
        # 滞销商品建议清仓
        from core.modules.intelligence.ai_features_inventory_ai import InventoryAI
        inventory_ai = InventoryAI()
        slow_moving = inventory_ai.get_slow_moving_products(days=30)
        
        suggestions = []
        for item in slow_moving[:5]:  # 前5个滞销品
            name = item['product_name']
            stock = item['current_stock']
            
            # 根据库存量建议折扣
            if stock > 50:
                discount = 0.7  # 7折
            elif stock > 20:
                discount = 0.8  # 8折
            else:
                discount = 0.85  # 85折
            
            suggestions.append({
                'product_name': name,
                'suggestion': f"{item['suggestion']}，建议{int(discount*10)}折清仓",
                'discount_rate': discount,
                'expected_effect': f"预计可清理 {stock} 件库存，回笼资金"
            })
        
        return suggestions


def get_pricing_ai() -> PricingAI:
    """获取定价 AI 实例"""
    return PricingAI()

```
