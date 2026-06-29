# -*- coding: utf-8 -*-
"""
行业适配器 - 根据行业类型适配业务逻辑
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .industry_config import get_current_config, IndustryType


class IndustryAdapter:
    """行业适配器"""
    
    def __init__(self, db_path: str = None):
        self.config = get_current_config()
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), '..', 'data', 'orders.db')
    
    # ========== 术语转换 ==========
    def translate(self, key: str) -> str:
        """翻译术语"""
        return self.config.terminology.get(key, key)
    
    # ========== 报表适配 ==========
    def get_kpi_display_name(self, metric: str) -> str:
        """获取KPI显示名称"""
        kpi_map = {
            "sales": "销售额",
            "orders": "订单数",
            "customers": "客户数",
            "avg_order": "客单价",
            "inventory": "库存",
            "profit": "利润"
        }
        return kpi_map.get(metric, metric)
    
    def format_report_title(self, report_type: str) -> str:
        """格式化报告标题"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if report_type == "daily":
            return "%s %s日报" % (today, self.config.name.replace("行业", ""))
        elif report_type == "weekly":
            week_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            return "%s 至 %s %s周报" % (week_start, today, self.config.name.replace("行业", ""))
        elif report_type == "monthly":
            month = datetime.now().strftime("%Y-%m")
            return "%s %s月报" % (month, self.config.name.replace("行业", ""))
        
        return "%s 报告" % self.config.name
    
    # ========== 预警适配 ==========
    def get_alert_rules(self) -> Dict:
        """获取行业预警规则"""
        return self.config.alert_rules
    
    def check_alerts(self, data: Dict) -> List[Dict]:
        """检查数据是否触发预警"""
        alerts = []
        rules = self.config.alert_rules
        
        # 库存预警
        if "stock" in data and "low_stock" in rules:
            if data["stock"] < rules["low_stock"]["threshold"]:
                alerts.append({
                    "type": "low_stock",
                    "level": "warning",
                    "message": rules["low_stock"]["message"],
                    "value": data["stock"]
                })
        
        # 毛利率预警（批发）
        if "margin" in data and "low_margin" in rules:
            if data["margin"] < rules["low_margin"]["rate"]:
                alerts.append({
                    "type": "low_margin",
                    "level": "danger",
                    "message": rules["low_margin"]["message"],
                    "value": data["margin"]
                })
        
        # 制作超时（餐饮）
        if "cooking_time" in data and "slow_kitchen" in rules:
            if data["cooking_time"] > rules["slow_kitchen"]["minutes"]:
                alerts.append({
                    "type": "slow_kitchen",
                    "level": "warning",
                    "message": rules["slow_kitchen"]["message"],
                    "value": data["cooking_time"]
                })
        
        return alerts
    
    # ========== 角色适配 ==========
    def get_employee_roles(self) -> List[Dict]:
        """获取行业角色"""
        return self.config.employee_roles
    
    # ========== 工作流适配 ==========
    def get_workflow_templates(self) -> List[Dict]:
        """获取工作流模板"""
        return self.config.workflow_templates
    
    # ========== 查询适配 ==========
    def adapt_query(self, intent: str, params: Dict) -> Dict:
        """适配查询参数"""
        adapted = params.copy()
        
        if self.config.type == IndustryType.CATERING:
            # 餐饮特殊处理
            if intent == "query_sales":
                adapted["group_by"] = "dining_type"  # 按堂食/外卖分组
            elif intent == "query_inventory":
                adapted["type"] = "ingredient"  # 食材库存
        
        elif self.config.type == IndustryType.WHOLESALE:
            # 批发特殊处理
            if intent == "query_sales":
                adapted["include_credit"] = True  # 包含账期信息
            elif intent == "query_customers":
                adapted["include_outstanding"] = True  # 包含欠款
        
        elif self.config.type == IndustryType.RETAIL:
            # 零售特殊处理
            if intent == "query_sales":
                adapted["include_member"] = True  # 包含会员信息
            elif intent == "query_inventory":
                adapted["include_shelf_life"] = True  # 包含保质期
        
        return adapted
    
    # ========== 建议适配 ==========
    def get_recommendations(self, data: Dict) -> List[str]:
        """基于行业生成建议"""
        recommendations = []
        
        if self.config.type == IndustryType.RETAIL:
            # 零售建议
            if data.get("conversion_rate", 1) < 0.2:
                recommendations.append("转化率偏低，建议优化商品陈列和促销策略")
            if data.get("inventory_turnover", 100) < 30:
                recommendations.append("库存周转慢，建议清理滞销商品")
            if data.get("member_repeat_rate", 1) < 0.3:
                recommendations.append("会员复购率低，建议加强会员营销")
        
        elif self.config.type == IndustryType.CATERING:
            # 餐饮建议
            if data.get("table_turnover", 10) < 3:
                recommendations.append("翻台率偏低，建议优化上菜速度或推出套餐")
            if data.get("food_cost_rate", 0) > 0.4:
                recommendations.append("食材成本率过高，建议优化菜单结构")
            if data.get("bad_review_rate", 0) > 0.05:
                recommendations.append("差评率偏高，建议加强服务质量管控")
        
        elif self.config.type == IndustryType.WHOLESALE:
            # 批发建议
            if data.get("collection_rate", 1) < 0.8:
                recommendations.append("回款率偏低，建议加强账款催收")
            if data.get("order_fulfillment", 1) < 0.95:
                recommendations.append("订单履约率低，建议优化库存管理")
            if data.get("customer_churn", 0) > 0.1:
                recommendations.append("客户流失率高，建议加强客户维护")
        
        return recommendations


# 全局适配器
_adapter: Optional[IndustryAdapter] = None


def get_adapter() -> IndustryAdapter:
    """获取适配器实例"""
    global _adapter
    if _adapter is None:
        _adapter = IndustryAdapter()
    return _adapter


def set_industry_adapter(industry_type: str):
    """设置行业并创建适配器"""
    from .industry_config import set_industry
    global _adapter
    set_industry(industry_type)
    _adapter = IndustryAdapter()


if __name__ == "__main__":
    # 测试
    adapter = get_adapter()
    print("术语:", adapter.translate("product"))
    print("角色:", [r["name"] for r in adapter.get_employee_roles()])
    print("预警:", adapter.get_alert_rules())
