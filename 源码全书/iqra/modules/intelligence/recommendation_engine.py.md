# `iqra/modules/intelligence/recommendation_engine.py`

> 路径：`iqra/modules/intelligence/recommendation_engine.py` | 行数：458


---


```python
# -*- coding: utf-8 -*-
"""
智能推荐引擎 V1
功能：
1. 基于购买历史的商品推荐
2. 关联规则推荐（买了A的人也买了B）
3. 热销商品推荐
4. 会员个性化推荐
5. 季节性/趋势推荐
"""

import sys
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.intelligence._compat import get_conn


class RecommendationEngine:
    """智能推荐引擎"""
    
    def __init__(self):
        self._cache = {}
        self._cache_time = None
        
    def _get_orders_data(self) -> List[Dict]:
        """获取订单数据"""
        try:
            conn = get_conn('order.db')
            cursor = conn.execute(
                "SELECT id, customer, product, quantity, amount, created_at "
                "FROM orders ORDER BY created_at DESC"
            )
            orders = []
            for row in cursor.fetchall():
                orders.append({
                    'id': row[0],
                    'customer': row[1],
                    'product': row[2],
                    'quantity': row[3],
                    'amount': row[4],
                    'created_at': row[5]
                })
            return orders
        except Exception as e:
            print(f"[RecommendationEngine] 获取订单数据失败: {e}")
            return []
    
    def _get_products_data(self) -> List[Dict]:
        """获取产品数据"""
        try:
            conn = get_conn('product.db')
            cursor = conn.execute(
                "SELECT id, name, price, category, stock, description FROM product"
            )
            products = []
            for row in cursor.fetchall():
                products.append({
                    'id': row[0],
                    'name': row[1],
                    'price': row[2],
                    'category': row[3],
                    'stock': row[4],
                    'description': row[5]
                })
            return products
        except Exception as e:
            print(f"[RecommendationEngine] 获取产品数据失败: {e}")
            return []
    
    # ═══════════════════════════════════════════
    # 1. 基于购买历史的推荐
    # ═══════════════════════════════════════════
    
    def recommend_by_history(self, customer_name: str, limit: int = 5) -> List[Dict]:
        """基于客户购买历史推荐商品"""
        orders = self._get_orders_data()
        products = self._get_products_data()
        
        if not orders or not products:
            return []
        
        # 获取该客户购买过的商品类别
        customer_categories = set()
        customer_products = set()
        
        for order in orders:
            if order['customer'] == customer_name:
                customer_products.add(order['product'])
                # 找到商品类别
                for p in products:
                    if p['name'] == order['product']:
                        customer_categories.add(p['category'])
                        break
        
        if not customer_categories:
            # 新客户，返回热销商品
            return self.recommend_hot_products(limit)
        
        # 推荐同类别但未购买过的商品
        recommendations = []
        for p in products:
            if (p['category'] in customer_categories and 
                p['name'] not in customer_products and
                p['stock'] > 0):
                recommendations.append({
                    'product': p['name'],
                    'price': p['price'],
                    'category': p['category'],
                    'reason': f"与您购买的{p['category']}类商品相关",
                    'score': 0.8
                })
        
        # 按价格相近排序
        if customer_products:
            avg_price = sum(o['amount'] for o in orders if o['customer'] == customer_name) / \
                       max(1, len([o for o in orders if o['customer'] == customer_name]))
            recommendations.sort(key=lambda x: abs(x['price'] - avg_price))
        
        return recommendations[:limit]
    
    # ═══════════════════════════════════════════
    # 2. 关联规则推荐（买了A的人也买了B）
    # ═══════════════════════════════════════════
    
    def recommend_by_association(self, product_name: str, limit: int = 5) -> List[Dict]:
        """关联规则推荐 - 买了A的人也买了B"""
        orders = self._get_orders_data()
        products = self._get_products_data()
        
        if not orders:
            return []
        
        # 构建购物篮
        baskets = defaultdict(set)
        for order in orders:
            baskets[order['customer']].add(order['product'])
        
        # 统计同时购买
        co_occurrence = defaultdict(int)
        product_count = defaultdict(int)
        
        for basket in baskets.values():
            if product_name in basket:
                for p in basket:
                    if p != product_name:
                        co_occurrence[p] += 1
            for p in basket:
                product_count[p] += 1
        
        # 计算置信度
        recommendations = []
        for p, co_count in co_occurrence.items():
            confidence = co_count / product_count[product_name]
            if confidence > 0.1:  # 最小置信度阈值
                # 获取商品信息
                product_info = next((prod for prod in products if prod['name'] == p), None)
                if product_info and product_info['stock'] > 0:
                    recommendations.append({
                        'product': p,
                        'price': product_info['price'] if product_info else 0,
                        'category': product_info['category'] if product_info else '',
                        'reason': f"购买{product_name}的客户中有{confidence*100:.0f}%也购买了此商品",
                        'confidence': round(confidence, 2),
                        'score': confidence
                    })
        
        # 按置信度排序
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:limit]
    
    # ═══════════════════════════════════════════
    # 3. 热销商品推荐
    # ═══════════════════════════════════════════
    
    def recommend_hot_products(self, limit: int = 5, days: int = 30) -> List[Dict]:
        """热销商品推荐"""
        orders = self._get_orders_data()
        products = self._get_products_data()
        
        if not orders:
            return []
        
        # 统计最近N天销量
        cutoff_date = datetime.now() - timedelta(days=days)
        product_sales = defaultdict(lambda: {'quantity': 0, 'revenue': 0})
        
        for order in orders:
            try:
                order_date = datetime.strptime(order['created_at'], '%Y-%m-%d %H:%M:%S')
            except Exception:
                try:
                    order_date = datetime.strptime(order['created_at'], '%Y-%m-%d')
                except Exception:
                    continue
            
            if order_date >= cutoff_date:
                product_sales[order['product']]['quantity'] += order['quantity']
                product_sales[order['product']]['revenue'] += order['amount'] * order['quantity']
        
        # 构建推荐列表
        recommendations = []
        for p_name, sales in product_sales.items():
            product_info = next((p for p in products if p['name'] == p_name), None)
            if product_info and product_info['stock'] > 0:
                recommendations.append({
                    'product': p_name,
                    'price': product_info['price'],
                    'category': product_info['category'],
                    'quantity_sold': sales['quantity'],
                    'revenue': sales['revenue'],
                    'reason': f"最近{days}天热销{sales['quantity']}件",
                    'score': min(1.0, sales['quantity'] / 10)  # 归一化分数
                })
        
        # 按销量排序
        recommendations.sort(key=lambda x: x['quantity_sold'], reverse=True)
        return recommendations[:limit]
    
    # ═══════════════════════════════════════════
    # 4. 会员个性化推荐
    # ═══════════════════════════════════════════
    
    def recommend_for_member(self, member_id: str, limit: int = 5) -> List[Dict]:
        """会员个性化推荐"""
        try:
            # 获取会员信息
            conn = get_conn('member.db')
            cursor = conn.execute(
                "SELECT name, level, points, preferences FROM member WHERE id = ?",
                (member_id,)
            )
            member = cursor.fetchone()
            
            if not member:
                return self.recommend_hot_products(limit)
            
            member_name, level, points, preferences = member
            
            # 基于会员等级提供不同推荐
            recommendations = []
            
            # 先获取基于历史的推荐
            history_recs = self.recommend_by_history(member_name, limit=limit)
            recommendations.extend(history_recs)
            
            # 高等级会员额外推荐高价值商品
            if level in ['gold', 'platinum', '钻石']:
                products = self._get_products_data()
                high_value = [p for p in products if p['price'] > 500 and p['stock'] > 0]
                high_value.sort(key=lambda x: x['price'], reverse=True)
                
                for p in high_value[:2]:
                    recommendations.append({
                        'product': p['name'],
                        'price': p['price'],
                        'category': p['category'],
                        'reason': f"{level}会员专享推荐",
                        'score': 0.9
                    })
            
            # 积分兑换推荐
            if points > 1000:
                products = self._get_products_data()
                redeemable = [p for p in products if p['price'] <= points / 100 and p['stock'] > 0]
                if redeemable:
                    p = redeemable[0]
                    recommendations.append({
                        'product': p['name'],
                        'price': p['price'],
                        'category': p['category'],
                        'reason': f"可用{int(p['price'] * 100)}积分兑换",
                        'score': 0.85
                    })
            
            # 去重并排序
            seen = set()
            unique_recs = []
            for r in recommendations:
                if r['product'] not in seen:
                    seen.add(r['product'])
                    unique_recs.append(r)
            
            return unique_recs[:limit]
            
        except Exception as e:
            print(f"[RecommendationEngine] 会员推荐失败: {e}")
            return self.recommend_hot_products(limit)
    
    # ═══════════════════════════════════════════
    # 5. 季节性/趋势推荐
    # ═══════════════════════════════════════════
    
    def recommend_by_trend(self, limit: int = 5) -> List[Dict]:
        """基于当前季节/趋势的推荐"""
        month = datetime.now().month
        products = self._get_products_data()
        
        # 季节性分类
        season_categories = {
            'spring': [3, 4, 5],
            'summer': [6, 7, 8],
            'autumn': [9, 10, 11],
            'winter': [12, 1, 2]
        }
        
        current_season = next(
            (s for s, months in season_categories.items() if month in months),
            'spring'
        )
        
        # 季节性商品关键词
        seasonal_keywords = {
            'spring': ['春', '户外', '运动'],
            'summer': ['夏', '清凉', '防晒', '泳'],
            'autumn': ['秋', '保暖', '外套'],
            'winter': ['冬', '暖', '羽绒服', '保暖']
        }
        
        keywords = seasonal_keywords.get(current_season, [])
        
        recommendations = []
        for p in products:
            if p['stock'] > 0:
                # 检查是否匹配季节性关键词
                match_score = 0
                for kw in keywords:
                    if kw in p['name'] or (p['description'] and kw in p['description']):
                        match_score += 0.3
                
                if match_score > 0:
                    recommendations.append({
                        'product': p['name'],
                        'price': p['price'],
                        'category': p['category'],
                        'reason': f"{current_season}季热门",
                        'score': match_score
                    })
        
        # 如果没有季节性匹配，返回热销商品
        if not recommendations:
            return self.recommend_hot_products(limit)
        
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:limit]
    
    # ═══════════════════════════════════════════
    # 综合推荐
    # ═══════════════════════════════════════════
    
    def get_recommendations(self, customer_name: Optional[str] = None, 
                           product_name: Optional[str] = None,
                           member_id: Optional[str] = None,
                           limit: int = 5) -> Dict:
        """获取综合推荐"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'recommendations': []
        }
        
        all_recs = []
        
        # 1. 会员个性化推荐
        if member_id:
            member_recs = self.recommend_for_member(member_id, limit=limit)
            for r in member_recs:
                r['source'] = 'member'
            all_recs.extend(member_recs)
        
        # 2. 基于购买历史
        if customer_name:
            history_recs = self.recommend_by_history(customer_name, limit=limit)
            for r in history_recs:
                r['source'] = 'history'
            all_recs.extend(history_recs)
        
        # 3. 关联推荐
        if product_name:
            assoc_recs = self.recommend_by_association(product_name, limit=limit)
            for r in assoc_recs:
                r['source'] = 'association'
            all_recs.extend(assoc_recs)
        
        # 4. 热销推荐
        hot_recs = self.recommend_hot_products(limit=limit)
        for r in hot_recs:
            r['source'] = 'hot'
        all_recs.extend(hot_recs)
        
        # 5. 趋势推荐
        trend_recs = self.recommend_by_trend(limit=limit)
        for r in trend_recs:
            r['source'] = 'trend'
        all_recs.extend(trend_recs)
        
        # 去重并排序
        seen = set()
        unique_recs = []
        for r in all_recs:
            if r['product'] not in seen:
                seen.add(r['product'])
                unique_recs.append(r)
        
        # 按分数排序
        unique_recs.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        results['recommendations'] = unique_recs[:limit]
        results['count'] = len(results['recommendations'])
        
        return results


# ═══════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════

def get_recommendation_engine() -> RecommendationEngine:
    """获取推荐引擎实例"""
    return RecommendationEngine()


# 测试
if __name__ == '__main__':
    engine = RecommendationEngine()
    
    print("=" * 50)
    print("智能推荐引擎测试")
    print("=" * 50)
    
    # 测试热销推荐
    print("\n1. 热销商品推荐:")
    hot = engine.recommend_hot_products(3)
    for r in hot:
        print(f"  - {r['product']} (¥{r['price']}) - {r['reason']}")
    
    # 测试关联推荐
    print("\n2. 关联规则推荐:")
    if hot:
        assoc = engine.recommend_by_association(hot[0]['product'], 3)
        for r in assoc:
            print(f"  - {r['product']} (¥{r['price']}) - {r['reason']}")
    
    # 测试趋势推荐
    print("\n3. 趋势推荐:")
    trend = engine.recommend_by_trend(3)
    for r in trend:
        print(f"  - {r['product']} (¥{r['price']}) - {r['reason']}")
    
    # 测试综合推荐
    print("\n4. 综合推荐:")
    results = engine.get_recommendations(limit=5)
    for r in results['recommendations']:
        print(f"  - {r['product']} (¥{r['price']}) [{r['source']}] - {r['reason']}")

```
