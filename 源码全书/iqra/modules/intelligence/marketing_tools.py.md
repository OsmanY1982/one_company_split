# `iqra/modules/intelligence/marketing_tools.py`

> 路径：`iqra/modules/intelligence/marketing_tools.py` | 行数：608


---


```python
"""
营销推广工具 — 营销策划、渠道分析、转化优化

提供:
- 营销活动策划
- 推广渠道效果分析
- 转化率计算与优化建议
- ROI 投资回报率分析
- 客户分群与精准营销
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json


class MarketingTools:
    """营销推广工具集"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
    
    def _connect(self, db_name: str) -> Optional[sqlite3.Connection]:
        """连接数据库"""
        path = os.path.join(self.data_dir, db_name)
        if not os.path.exists(path):
            return None
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        conn.text_factory = lambda x: str(x, 'utf-8', 'replace')
        return conn
    
    def create_campaign_plan(
        self, 
        campaign_name: str,
        target_audience: str = "all",
        budget: float = None,
        duration_days: int = 30,
        channels: List[str] = None
    ) -> Dict[str, Any]:
        """
        创建营销活动策划方案
        
        Args:
            campaign_name: 活动名称
            target_audience: 目标受众 (all/vip/new/potential)
            budget: 预算金额
            duration_days: 活动天数
            channels: 推广渠道列表
        
        Returns:
            完整的营销策划方案
        """
        # 获取客户数据用于分析
        cust_db = self._connect("customer.db")
        order_db = self._connect("order.db")
        
        # 分析目标受众规模
        audience_size = 0
        audience_desc = ""
        
        if cust_db:
            try:
                if target_audience == "vip":
                    cursor = cust_db.execute("SELECT COUNT(*) FROM customer WHERE level='VIP'")
                    audience_desc = "VIP 客户"
                elif target_audience == "new":
                    # 最近 30 天新增
                    cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    cursor = cust_db.execute("SELECT COUNT(*) FROM customer WHERE created_at >= ?", (cutoff,))
                    audience_desc = "近 30 天新增客户"
                elif target_audience == "potential":
                    cursor = cust_db.execute("SELECT COUNT(*) FROM customer WHERE level='潜在'")
                    audience_desc = "潜在客户"
                else:
                    cursor = cust_db.execute("SELECT COUNT(*) FROM customer")
                    audience_desc = "全部客户"
                
                audience_size = cursor.fetchone()[0]
            finally:
                cust_db.close()
        
        # 默认渠道配置
        if not channels:
            channels = ["微信", "邮件", "短信", "电话"]
        
        # 生成渠道预算分配
        channel_budgets = {}
        if budget:
            channel_weights = {
                "微信": 0.35,
                "邮件": 0.20,
                "短信": 0.15,
                "电话": 0.20,
                "线下活动": 0.10
            }
            for ch in channels:
                weight = channel_weights.get(ch, 0.10)
                channel_budgets[ch] = round(budget * weight, 2)
        
        # 生成策划方案
        plan = {
            "campaign_name": campaign_name,
            "target_audience": {
                "type": target_audience,
                "description": audience_desc,
                "estimated_size": audience_size
            },
            "duration": {
                "days": duration_days,
                "start_date": datetime.now().strftime('%Y-%m-%d'),
                "end_date": (datetime.now() + timedelta(days=duration_days)).strftime('%Y-%m-%d')
            },
            "budget": {
                "total": budget,
                "allocation": channel_budgets
            },
            "channels": channels,
            "timeline": self._generate_timeline(duration_days, channels),
            "kpis": self._generate_kpis(audience_size, budget),
            "recommendations": self._generate_recommendations(target_audience, channels)
        }
        
        return plan
    
    def _generate_timeline(self, days: int, channels: List[str]) -> List[Dict]:
        """生成活动时间线"""
        phases = [
            {"name": "预热期", "progress": 0.2, "actions": ["发布预告", "社交媒体造势"]},
            {"name": "爆发期", "progress": 0.5, "actions": ["全渠道推广", "限时优惠"]},
            {"name": "持续期", "progress": 0.2, "actions": ["跟进转化", "口碑传播"]},
            {"name": "收尾期", "progress": 0.1, "actions": ["最后冲刺", "数据复盘"]},
        ]
        
        timeline = []
        for phase in phases:
            phase_days = int(days * phase["progress"])
            timeline.append({
                "phase": phase["name"],
                "duration": f"{phase_days}天",
                "channels": channels[:3],  # 每个阶段重点 3 个渠道
                "key_actions": phase["actions"]
            })
        
        return timeline
    
    def _generate_kpis(self, audience_size: int, budget: float) -> Dict[str, Any]:
        """生成关键绩效指标"""
        # 基于行业基准的估算
        benchmark = {
            "open_rate": 0.25,      # 打开率 25%
            "click_rate": 0.05,     # 点击率 5%
            "conversion_rate": 0.02, # 转化率 2%
            "roi_target": 3.0       # ROI 目标 3:1
        }
        
        estimated_reach = int(audience_size * benchmark["open_rate"])
        estimated_conversions = int(estimated_reach * benchmark["conversion_rate"])
        estimated_revenue = estimated_conversions * (budget / audience_size * 10) if audience_size > 0 else 0
        
        return {
            "触达人数": estimated_reach,
            "预期转化": estimated_conversions,
            "预期收入": f"¥{estimated_revenue:.2f}",
            "ROI 目标": f"{benchmark['roi_target']}:1",
            "基准指标": benchmark
        }
    
    def _generate_recommendations(self, audience: str, channels: List[str]) -> List[str]:
        """生成营销建议"""
        recommendations = []
        
        if audience == "vip":
            recommendations.extend([
                "💡 VIP 客户重视专属感，建议提供定制化优惠",
                "📞 电话跟进转化率通常更高，建议增加电话渠道投入",
                "🎁 考虑设置 VIP 专属礼品或提前购权限"
            ])
        elif audience == "new":
            recommendations.extend([
                "💡 新客户需要建立信任，建议突出品牌故事和用户评价",
                "📧 邮件营销适合新客户培育，建议设置欢迎序列",
                "🎯 首单优惠能有效提升转化，建议设置新人专享价"
            ])
        elif audience == "potential":
            recommendations.extend([
                "💡 潜在客户需要培育，建议提供有价值的内容而非硬广",
                "📱 微信适合长期培育，建议建立私域流量池",
                "📊 设置线索评分机制，优先跟进高意向客户"
            ])
        else:
            recommendations.extend([
                "💡 全量客户建议分层运营，不同群体使用不同策略",
                "📈 A/B 测试不同渠道和文案，持续优化效果",
                "🔄 设置再营销策略，对未转化客户进行二次触达"
            ])
        
        # 渠道特定建议
        if "微信" in channels:
            recommendations.append("💬 微信公众号 + 社群联动，提升传播效果")
        if "邮件" in channels:
            recommendations.append("📧 邮件主题行控制在 20 字内，提升打开率")
        if "短信" in channels:
            recommendations.append("📱 短信控制在 70 字内，包含明确 CTA")
        
        return recommendations
    
    def analyze_channel_performance(self, days: int = 30) -> Dict[str, Any]:
        """
        分析各推广渠道的效果
        
        Returns:
            渠道效果分析报告
        """
        # 模拟渠道数据（实际应从营销数据表读取）
        # 这里基于订单数据进行推算
        
        order_db = self._connect("order.db")
        if not order_db:
            return {"error": "订单数据库不存在"}
        
        try:
            cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # 获取订单总量和金额
            cursor = order_db.execute("""
                SELECT 
                    COUNT(*) as total_orders,
                    COALESCE(SUM(total_amount), 0) as total_revenue
                FROM orders 
                WHERE created_at >= ? AND status != 'cancelled'
            """, (cutoff,))
            
            stats = cursor.fetchone()
            total_orders = int(stats["total_orders"])
            total_revenue = float(stats["total_revenue"])
            
            # 模拟渠道分布（实际应记录每个订单的来源渠道）
            channel_data = {
                "微信": {"orders": int(total_orders * 0.35), "revenue": total_revenue * 0.35, "cost": total_revenue * 0.12},
                "邮件": {"orders": int(total_orders * 0.20), "revenue": total_revenue * 0.20, "cost": total_revenue * 0.05},
                "自然流量": {"orders": int(total_orders * 0.25), "revenue": total_revenue * 0.25, "cost": 0},
                "电话": {"orders": int(total_orders * 0.15), "revenue": total_revenue * 0.15, "cost": total_revenue * 0.08},
                "其他": {"orders": int(total_orders * 0.05), "revenue": total_revenue * 0.05, "cost": total_revenue * 0.02},
            }
            
            # 计算各渠道指标
            channel_metrics = []
            for channel, data in channel_data.items():
                if data["cost"] > 0:
                    roi = (data["revenue"] - data["cost"]) / data["cost"]
                else:
                    roi = float('inf')
                
                avg_order_value = data["revenue"] / data["orders"] if data["orders"] > 0 else 0
                
                channel_metrics.append({
                    "channel": channel,
                    "orders": data["orders"],
                    "revenue": round(data["revenue"], 2),
                    "cost": round(data["cost"], 2),
                    "roi": round(roi, 2) if roi != float('inf') else "∞",
                    "avg_order_value": round(avg_order_value, 2),
                    "order_share": round(data["orders"] / total_orders * 100, 1) if total_orders > 0 else 0
                })
            
            # 排序
            channel_metrics.sort(key=lambda x: x["roi"] if x["roi"] != "∞" else 999, reverse=True)
            
            # 生成洞察
            insights = []
            if channel_metrics:
                best_channel = channel_metrics[0]
                insights.append(f"🏆 ROI 最高渠道：{best_channel['channel']} (ROI: {best_channel['roi']})")
                
                low_performers = [c for c in channel_metrics if c["roi"] != "∞" and c["roi"] < 2]
                if low_performers:
                    insights.append(f"⚠️ 需优化渠道：{', '.join([c['channel'] for c in low_performers])}")
                
                insights.append(f"💡 建议增加高 ROI 渠道的预算投入")
            
            return {
                "period": f"近{days}天",
                "total_orders": total_orders,
                "total_revenue": round(total_revenue, 2),
                "channel_breakdown": channel_metrics,
                "insights": insights,
                "recommendations": self._generate_channel_recommendations(channel_metrics)
            }
        finally:
            order_db.close()
    
    def _generate_channel_recommendations(self, metrics: List[Dict]) -> List[str]:
        """生成渠道优化建议"""
        recommendations = []
        
        # 找出表现最好的渠道
        paid_channels = [c for c in metrics if c["cost"] > 0]
        if paid_channels:
            best = max(paid_channels, key=lambda x: x["roi"] if x["roi"] != "∞" else 999)
            worst = min(paid_channels, key=lambda x: x["roi"] if x["roi"] != "∞" else 0)
            
            recommendations.append(f"✅ 增加「{best['channel']}」预算占比，当前 ROI 为 {best['roi']}")
            recommendations.append(f"📉 优化或削减「{worst['channel']}」投入，当前 ROI 为 {worst['roi']}")
        
        # 自然流量建议
        organic = next((c for c in metrics if c["channel"] == "自然流量"), None)
        if organic and organic["order_share"] < 30:
            recommendations.append("📈 自然流量占比较低，建议加强 SEO 和内容营销")
        
        return recommendations
    
    def calculate_conversion_funnel(self) -> Dict[str, Any]:
        """
        计算转化漏斗
        
        Returns:
            转化漏斗数据和建议
        """
        cust_db = self._connect("customer.db")
        order_db = self._connect("order.db")
        
        if not cust_db or not order_db:
            return {"error": "数据库不可用"}
        
        try:
            # 获取各阶段数据
            total_customers = cust_db.execute("SELECT COUNT(*) FROM customer").fetchone()[0]
            
            # 有订单的客户数
            active_customers = order_db.execute("""
                SELECT COUNT(DISTINCT customer_name) 
                FROM orders 
                WHERE status != 'cancelled'
            """).fetchone()[0]
            
            # 本月新增客户
            current_month = datetime.now().strftime('%Y-%m')
            new_customers = cust_db.execute("""
                SELECT COUNT(*) FROM customer 
                WHERE created_at LIKE ?
            """, (f"{current_month}%",)).fetchone()[0]
            
            # 计算转化率
            visitor_to_lead = 0.30  # 假设访客到线索转化率
            lead_to_customer = active_customers / total_customers if total_customers > 0 else 0
            customer_to_repeat = 0.40  # 假设复购率
            
            funnel = [
                {"stage": "访客", "count": int(total_customers / 0.3), "rate": 100},
                {"stage": "线索", "count": total_customers, "rate": 30},
                {"stage": "成交客户", "count": active_customers, "rate": round(lead_to_customer * 100, 1)},
                {"stage": "复购客户", "count": int(active_customers * customer_to_repeat), "rate": round(lead_to_customer * customer_to_repeat * 100, 1)}
            ]
            
            # 计算流失
            drop_offs = []
            for i in range(1, len(funnel)):
                prev = funnel[i-1]
                curr = funnel[i]
                lost = prev["count"] - curr["count"]
                rate = ((prev["count"] - curr["count"]) / prev["count"]) * 100 if prev["count"] > 0 else 0
                drop_offs.append({
                    "from": prev["stage"],
                    "to": curr["stage"],
                    "lost": lost,
                    "rate": round(rate, 1)
                })
            
            # 找出最大流失点
            max_drop = max(drop_offs, key=lambda x: x["rate"])
            
            insights = [
                f"📊 整体转化率：{funnel[-1]['rate']}%",
                f"⚠️ 最大流失点：{max_drop['from']} → {max_drop['to']} (流失{max_drop['rate']}%)",
            ]
            
            recommendations = self._generate_funnel_recommendations(drop_offs)
            
            return {
                "funnel": funnel,
                "drop_offs": drop_offs,
                "insights": insights,
                "recommendations": recommendations
            }
        finally:
            cust_db.close()
            order_db.close()
    
    def _generate_funnel_recommendations(self, drop_offs: List[Dict]) -> List[str]:
        """生成漏斗优化建议"""
        recommendations = []
        
        for drop in drop_offs:
            if drop["rate"] > 70:
                if "访客" in drop["from"]:
                    recommendations.append(f"💡 优化落地页，提升访客到线索转化")
                elif "线索" in drop["from"]:
                    recommendations.append(f"💡 加强销售跟进，提升线索到成交转化")
                elif "成交" in drop["from"]:
                    recommendations.append(f"💡 建立客户关怀体系，提升复购率")
        
        recommendations.extend([
            "📈 设置转化漏斗监控，每周复盘",
            "🎯 针对高流失环节进行 A/B 测试",
            "📞 对高意向线索设置 24 小时内跟进机制"
        ])
        
        return recommendations
    
    def customer_segmentation(self) -> Dict[str, Any]:
        """
        客户分群分析 (RFM 模型简化版)
        
        Returns:
            客户分群结果和每群特征
        """
        cust_db = self._connect("customer.db")
        order_db = self._connect("order.db")
        
        if not cust_db or not order_db:
            return {"error": "数据库不可用"}
        
        try:
            # 获取客户订单数据
            cursor = order_db.execute("""
                SELECT 
                    customer_name,
                    COUNT(*) as order_count,
                    SUM(total_amount) as total_spent,
                    MAX(created_at) as last_order
                FROM orders 
                WHERE status != 'cancelled'
                GROUP BY customer_name
            """)
            
            customer_stats = {row["customer_name"]: dict(row) for row in cursor}
            
            # 简化分群：按消费金额
            segments = {
                "高价值客户": [],
                "成长客户": [],
                "普通客户": [],
                "沉睡客户": []
            }
            
            cutoff_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            
            for name, stats in customer_stats.items():
                total_spent = float(stats["total_spent"] or 0)
                last_order = stats["last_order"] or ""
                
                if total_spent >= 5000:
                    segments["高价值客户"].append(name)
                elif total_spent >= 1000:
                    segments["成长客户"].append(name)
                elif total_spent > 0:
                    if last_order < cutoff_date:
                        segments["沉睡客户"].append(name)
                    else:
                        segments["普通客户"].append(name)
            
            # 生成每群特征和建议
            segment_insights = {}
            for seg_name, customers in segments.items():
                segment_insights[seg_name] = {
                    "count": len(customers),
                    "percentage": round(len(customers) / len(customer_stats) * 100, 1) if customer_stats else 0,
                    "sample": customers[:5],
                    "strategy": self._get_segment_strategy(seg_name)
                }
            
            return {
                "total_customers": len(customer_stats),
                "segments": segment_insights,
                "recommendations": self._generate_segmentation_recommendations(segment_insights)
            }
        finally:
            cust_db.close()
            order_db.close()
    
    def _get_segment_strategy(self, segment: str) -> str:
        """获取分群营销策略"""
        strategies = {
            "高价值客户": "💎 专属 VIP 服务、提前购、定制礼品、一对一客服",
            "成长客户": "📈 满减优惠、会员升级激励、交叉销售",
            "普通客户": "🎯 新人优惠、爆款推荐、内容培育",
            "沉睡客户": "⏰ 唤醒优惠、限时回归、调研回访"
        }
        return strategies.get(segment, "📊 制定针对性营销策略")
    
    def _generate_segmentation_recommendations(self, segments: Dict) -> List[str]:
        """生成分群营销建议"""
        recommendations = []
        
        high_value = segments.get("高价值客户", {})
        if high_value.get("count", 0) > 0:
            recommendations.append(f"💎 高价值客户 {high_value['count']} 人，贡献大部分收入，建议重点维护")
        
        sleeping = segments.get("沉睡客户", {})
        if sleeping.get("count", 0) > 0:
            recommendations.append(f"⏰ {sleeping['count']} 位沉睡客户，建议启动唤醒计划")
        
        growing = segments.get("成长客户", {})
        if growing.get("count", 0) > 0:
            recommendations.append(f"📈 {growing['count']} 位成长客户，有潜力升级为高价值客户")
        
        recommendations.extend([
            "📊 定期更新客户分群，动态调整策略",
            "🎯 针对不同分群设计差异化营销内容"
        ])
        
        return recommendations


def register_marketing_tools(registry, data_dir: str):
    """注册营销工具到 ToolRegistry"""
    from modules.intelligence.tool_registry import ToolDefinition
    
    marketer = MarketingTools(data_dir)
    
    registry.add_tool(ToolDefinition(
        name="create_campaign_plan",
        description="创建营销活动策划方案：包含目标受众、渠道选择、预算分配、时间线、KPI 等",
        parameters={
            "type": "object",
            "properties": {
                "campaign_name": {"type": "string", "description": "活动名称"},
                "target_audience": {"type": "string", "description": "目标受众：all(全部)|vip|new(新客户)|potential(潜在)", "enum": ["all", "vip", "new", "potential"]},
                "budget": {"type": "number", "description": "预算金额（可选）"},
                "duration_days": {"type": "integer", "description": "活动天数", "default": 30},
                "channels": {"type": "array", "items": {"type": "string"}, "description": "推广渠道列表（可选）"}
            },
            "required": ["campaign_name"]
        },
        handler=lambda campaign_name, target_audience="all", budget=None, duration_days=30, channels=None: 
            marketer.create_campaign_plan(campaign_name, target_audience, budget, duration_days, channels),
    ))
    
    registry.add_tool(ToolDefinition(
        name="analyze_channel_performance",
        description="分析推广渠道效果：各渠道的订单、收入、ROI 对比",
        parameters={
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "分析天数", "default": 30}
            }
        },
        handler=lambda days=30: marketer.analyze_channel_performance(days),
    ))
    
    registry.add_tool(ToolDefinition(
        name="calculate_conversion_funnel",
        description="计算转化漏斗：分析各阶段转化率和流失点",
        parameters={
            "type": "object",
            "properties": {}
        },
        handler=lambda: marketer.calculate_conversion_funnel(),
    ))
    
    registry.add_tool(ToolDefinition(
        name="customer_segmentation",
        description="客户分群分析：RFM 模型分群，高价值/成长/普通/沉睡客户",
        parameters={
            "type": "object",
            "properties": {}
        },
        handler=lambda: marketer.customer_segmentation(),
    ))


if __name__ == "__main__":
    # 测试
    import sys
    # Test block only — path not used in production
    
    from modules.intelligence.tool_registry import ToolRegistry
    
    registry = ToolRegistry()
    import os
    _test_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
    register_marketing_tools(registry, _test_data_dir)
    
    print(f"✅ 已注册 {registry.count()} 个营销工具")
    print("可用工具:", registry.list_tools())
    
    # 测试活动策划
    print("\n=== 测试：创建营销活动方案 ===")
    result = registry.execute(type('ToolCall', (), {
        "name": "create_campaign_plan",
        "arguments": {
            "campaign_name": "618 年中大促",
            "target_audience": "all",
            "budget": 10000,
            "duration_days": 15
        },
        "id": "test1"
    })())
    
    if result["success"]:
        plan = result["result"]
        print(f"活动：{plan['campaign_name']}")
        print(f"目标受众：{plan['target_audience']['description']} ({plan['target_audience']['estimated_size']}人)")
        print(f"预算分配：{plan['budget']['allocation']}")
        print(f"预期 KPI: {plan['kpis']}")

```
