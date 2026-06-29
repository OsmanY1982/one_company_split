# -*- coding: utf-8 -*-
"""
AI 智能看板 - 一企通 AI 版核心入口
整合所有 AI 功能，提供统一接口
"""

from core.modules.intelligence.ai_features_inventory_ai import InventoryAI
from core.modules.intelligence.ai_features_pricing_ai import PricingAI
from core.modules.intelligence.ai_features_sales_ai import SalesAI
from core.modules.intelligence.ai_features_customer_ai import CustomerAI
from typing import Dict, List
import json


class AIDashboard:
    """
    AI 智能看板
    
    提供一站式 AI 分析功能：
    - 库存智能预警
    - 定价优化建议
    - 销售趋势分析
    - 客户洞察报告
    """
    
    def __init__(self):
        self.inventory_ai = InventoryAI()
        self.pricing_ai = PricingAI()
        self.sales_ai = SalesAI()
        self.customer_ai = CustomerAI()
    
    def get_daily_report(self) -> Dict:
        """
        生成每日 AI 报告
        
        Returns:
            {
                'date': 日期,
                'inventory': 库存预警,
                'pricing': 定价机会,
                'sales': 销售概况,
                'customers': 客户动态,
                'actions': 今日行动建议
            }
        """
        from datetime import datetime
        
        report = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'inventory': self._get_inventory_summary(),
            'pricing': self._get_pricing_summary(),
            'sales': self._get_sales_summary(),
            'customers': self._get_customer_summary(),
            'actions': []
        }
        
        # 生成行动建议
        report['actions'] = self._generate_actions(report)
        
        return report
    
    def _get_inventory_summary(self) -> Dict:
        """库存摘要"""
        reorder = self.inventory_ai.get_reorder_suggestions()
        slow_moving = self.inventory_ai.get_slow_moving_products(days=30)
        
        urgent = [r for r in reorder if r['urgency'] == '紧急']
        
        return {
            'urgent_count': len(urgent),
            'reorder_suggestions': reorder[:5],
            'slow_moving_count': len(slow_moving),
            'slow_moving_top': slow_moving[:3]
        }
    
    def _get_pricing_summary(self) -> Dict:
        """定价摘要"""
        opportunities = self.pricing_ai.get_pricing_opportunities()
        promotions = self.pricing_ai.get_promotion_suggestions()
        
        return {
            'opportunity_count': len(opportunities),
            'top_opportunities': opportunities[:3],
            'promotion_suggestions': promotions[:3]
        }
    
    def _get_sales_summary(self) -> Dict:
        """销售摘要"""
        summary = self.sales_ai.get_sales_summary(days=7)
        forecast = self.sales_ai.get_sales_forecast(days=7)
        
        return {
            'week_revenue': summary['total_revenue'],
            'week_orders': summary['total_orders'],
            'trend': summary['trend'],
            'forecast_revenue': forecast['forecast_revenue'],
            'top_products': summary['top_products']
        }
    
    def _get_customer_summary(self) -> Dict:
        """客户摘要"""
        segments = self.customer_ai.get_customer_segments()
        churn_alerts = self.customer_ai.get_churn_alerts()
        
        return {
            'total_customers': segments['summary']['total_customers'],
            'vip_count': segments['summary']['vip_count'],
            'at_risk_count': segments['summary']['at_risk_count'],
            'churn_alerts': churn_alerts[:5]
        }
    
    def _generate_actions(self, report: Dict) -> List[str]:
        """生成行动建议"""
        actions = []
        
        # 库存行动
        if report['inventory']['urgent_count'] > 0:
            actions.append(f"🚨 紧急：{report['inventory']['urgent_count']} 个商品需要立即补货")
        
        if report['inventory']['slow_moving_count'] > 0:
            actions.append(f"📦 建议：处理 {report['inventory']['slow_moving_count']} 个滞销商品")
        
        # 定价行动
        if report['pricing']['opportunity_count'] > 0:
            actions.append(f"💰 发现 {report['pricing']['opportunity_count']} 个定价优化机会")
        
        # 销售行动
        if report['sales']['trend'] == '下降':
            actions.append("📉 警告：销售趋势下降，建议开展促销活动")
        elif report['sales']['trend'] == '上升':
            actions.append("📈 利好：销售趋势上升，建议增加库存")
        
        # 客户行动
        if report['customers']['at_risk_count'] > 0:
            actions.append(f"👥 注意：{report['customers']['at_risk_count']} 个客户有流失风险")
        
        if not actions:
            actions.append("✅ 今日一切正常，保持当前策略")
        
        return actions
    
    def get_product_insight(self, product_name: str) -> Dict:
        """
        获取商品全方位洞察
        
        Args:
            product_name: 商品名称
            
        Returns:
            综合洞察报告
        """
        inventory = self.inventory_ai.predict_demand(product_name)
        pricing = self.pricing_ai.analyze_pricing(product_name)
        
        return {
            'product_name': product_name,
            'inventory': inventory,
            'pricing': pricing,
            'overall_suggestion': self._generate_product_suggestion(inventory, pricing)
        }
    
    def _generate_product_suggestion(self, inventory: Dict, pricing: Dict) -> str:
        """生成商品综合建议"""
        suggestions = []
        
        # 库存建议
        if 'suggestion' in inventory:
            suggestions.append("【库存】" + inventory['suggestion'])
        
        # 定价建议
        if 'suggestion' in pricing:
            suggestions.append("【定价】" + pricing['suggestion'])
        
        return "\n\n".join(suggestions)
    
    def export_report(self, report: Dict, format: str = 'json') -> str:
        """
        导出报告
        
        Args:
            report: 报告数据
            format: 格式（json/text）
            
        Returns:
            格式化报告文本
        """
        if format == 'json':
            return json.dumps(report, ensure_ascii=False, indent=2)
        
        # 文本格式
        lines = [
            "=" * 50,
            f"一企通 AI 日报 - {report['date']}",
            "=" * 50,
            "",
            "📊 销售概况",
            f"  本周营收: ¥{report['sales']['week_revenue']}",
            f"  本周订单: {report['sales']['week_orders']}",
            f"  销售趋势: {report['sales']['trend']}",
            f"  下周预测: ¥{report['sales']['forecast_revenue']}",
            "",
            "📦 库存预警",
            f"  紧急补货: {report['inventory']['urgent_count']} 个商品",
            f"  滞销商品: {report['inventory']['slow_moving_count']} 个",
            "",
            "💰 定价机会",
            f"  优化机会: {report['pricing']['opportunity_count']} 个",
            "",
            "👥 客户动态",
            f"  总客户数: {report['customers']['total_customers']}",
            f"  VIP客户: {report['customers']['vip_count']}",
            f"  流失风险: {report['customers']['at_risk_count']}",
            "",
            "🎯 今日行动",
        ]
        
        for action in report['actions']:
            lines.append(f"  • {action}")
        
        lines.append("")
        lines.append("=" * 50)
        
        return "\n".join(lines)


# 便捷函数
def get_ai_dashboard() -> AIDashboard:
    """获取 AI 看板实例"""
    return AIDashboard()


def generate_daily_report() -> str:
    """生成每日报告（文本格式）"""
    dashboard = AIDashboard()
    report = dashboard.get_daily_report()
    return dashboard.export_report(report, format='text')
