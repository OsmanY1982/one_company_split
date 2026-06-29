# -*- coding: utf-8 -*-
"""
行业专属报告生成器
根据行业类型生成定制化报告
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from core.modules.industry.industry_adapter import get_adapter


@dataclass
class IndustryReport:
    """行业报告"""
    id: str
    title: str
    industry: str
    report_type: str  # daily, weekly, monthly
    summary: str
    kpis: Dict = field(default_factory=dict)
    alerts: List = field(default_factory=list)
    recommendations: List = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class IndustryReportGenerator:
    """行业报告生成器"""
    
    def __init__(self):
        self.adapter = get_adapter()
        self.reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports', 'industry')
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate_daily_report(self) -> IndustryReport:
        """生成行业日报"""
        adapter = self.adapter
        config = adapter.config
        
        # 获取数据
        data = self._fetch_daily_data()
        
        # 生成ID
        report_id = "IND-%s-%s" % (config.type.value, datetime.now().strftime("%Y%m%d-%H%M%S"))
        
        # 格式化标题
        title = adapter.format_report_title("daily")
        
        # 计算KPI
        kpis = self._calculate_kpis(data)
        
        # 检查预警
        alerts = []
        for item in data.get('items', []):
            alerts.extend(adapter.check_alerts(item))
        
        # 生成建议
        recommendations = adapter.get_recommendations(kpis)
        
        # 生成摘要
        summary = self._generate_summary(kpis, config.type.value)
        
        report = IndustryReport(
            id=report_id,
            title=title,
            industry=config.name,
            report_type="daily",
            summary=summary,
            kpis=kpis,
            alerts=alerts,
            recommendations=recommendations
        )
        
        # 保存
        self._save_report(report)
        
        return report
    
    def _fetch_daily_data(self) -> Dict:
        """获取日报数据"""
        try:
            from core.modules.intelligence.db_helper import get_db_helper
            helper = get_db_helper()
            
            # 今日订单
            orders = helper.query_orders("DATE(created_at) = DATE('now')")
            
            # 库存
            products = helper.query_products()
            
            return {
                'orders': orders,
                'products': products,
                'items': products.get('products', [])
            }
        except Exception as e:
            return {'error': str(e), 'items': []}
    
    def _calculate_kpis(self, data: Dict) -> Dict:
        """计算KPI"""
        kpis = {}
        
        orders = data.get('orders', {})
        products = data.get('products', {})
        
        # 基础KPI
        kpis['sales'] = orders.get('total_amount', 0)
        kpis['order_count'] = orders.get('count', 0)
        kpis['avg_order'] = kpis['sales'] / kpis['order_count'] if kpis['order_count'] > 0 else 0
        
        # 行业特定KPI
        config_type = self.adapter.config.type.value
        
        if config_type == 'retail':
            # 零售：库存周转、会员复购
            kpis['inventory_turnover'] = len(products.get('products', []))
            kpis['conversion_rate'] = 0.15  # 示例
            kpis['member_repeat_rate'] = 0.25  # 示例
        
        elif config_type == 'catering':
            # 餐饮：翻台率、食材成本
            kpis['table_turnover'] = 3.5  # 示例
            kpis['food_cost_rate'] = 0.35  # 示例
            kpis['bad_review_rate'] = 0.02  # 示例
        
        elif config_type == 'wholesale':
            # 批发：回款率、履约率
            kpis['collection_rate'] = 0.85  # 示例
            kpis['order_fulfillment'] = 0.92  # 示例
            kpis['customer_churn'] = 0.08  # 示例
        
        return kpis
    
    def _generate_summary(self, kpis: Dict, industry_type: str) -> str:
        """生成摘要"""
        parts = []
        
        parts.append("销售额: $%.2f" % kpis.get('sales', 0))
        parts.append("订单: %d笔" % kpis.get('order_count', 0))
        parts.append("客单价: $%.2f" % kpis.get('avg_order', 0))
        
        if industry_type == 'retail':
            parts.append("库存周转: %d" % kpis.get('inventory_turnover', 0))
        elif industry_type == 'catering':
            parts.append("翻台率: %.1f" % kpis.get('table_turnover', 0))
        elif industry_type == 'wholesale':
            parts.append("回款率: %.1f%%" % (kpis.get('collection_rate', 0) * 100))
        
        return " | ".join(parts)
    
    def _save_report(self, report: IndustryReport):
        """保存报告"""
        filepath = os.path.join(self.reports_dir, "%s.json" % report.id)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'id': report.id,
                'title': report.title,
                'industry': report.industry,
                'type': report.report_type,
                'summary': report.summary,
                'kpis': report.kpis,
                'alerts': report.alerts,
                'recommendations': report.recommendations,
                'created_at': report.created_at
            }, f, ensure_ascii=False, indent=2)
    
    def list_reports(self) -> List[Dict]:
        """列出报告"""
        reports = []
        if os.path.exists(self.reports_dir):
            for filename in os.listdir(self.reports_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.reports_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        reports.append(json.load(f))
        return sorted(reports, key=lambda x: x['created_at'], reverse=True)


# 全局实例
_generator: Optional[IndustryReportGenerator] = None


def get_industry_report_generator() -> IndustryReportGenerator:
    """获取生成器实例"""
    global _generator
    if _generator is None:
        _generator = IndustryReportGenerator()
    return _generator


if __name__ == "__main__":
    gen = get_industry_report_generator()
    report = gen.generate_daily_report()
    print("Report:", report.title)
    print("KPIs:", report.kpis)
    print("Alerts:", report.alerts)
