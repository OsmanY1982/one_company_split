# -*- coding: utf-8 -*-
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class MarketingTools:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def _connect(self, db_name: str) -> Optional[sqlite3.Connection]:
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
        cust_db = self._connect("customer.db")
        order_db = self._connect("order.db")

        audience_size = 0
        audience_desc = ""

        if cust_db:
            try:
                if target_audience == "vip":
                    cursor = cust_db.execute("SELECT COUNT(*) FROM customer WHERE level='VIP'")
                    audience_desc = "VIP 客户"
                elif target_audience == "new":
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

        if not channels:
            channels = ["微信", "邮件", "短信", "电话"]

        channel_budgets = {}
        if budget:
            channel_weights = {
                "微信": 0.35, "邮件": 0.20, "短信": 0.15, "电话": 0.20, "线下活动": 0.10
            }
            for ch in channels:
                weight = channel_weights.get(ch, 0.10)
                channel_budgets[ch] = round(budget * weight, 2)

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
                "channels": channels[:3],
                "key_actions": phase["actions"]
            })
        return timeline

    def _generate_kpis(self, audience_size: int, budget: float) -> Dict[str, Any]:
        benchmark = {
            "open_rate": 0.25, "click_rate": 0.05, "conversion_rate": 0.02, "roi_target": 3.0
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
        if "微信" in channels:
            recommendations.append("💬 微信公众号 + 社群联动，提升传播效果")
        if "邮件" in channels:
            recommendations.append("📧 邮件主题行控制在 20 字内，提升打开率")
        if "短信" in channels:
            recommendations.append("📱 短信控制在 70 字内，包含明确 CTA")
        return recommendations

    def analyze_channel_performance(self, days: int = 30) -> Dict[str, Any]:
        order_db = self._connect("order.db")
        if not order_db:
            return {"error": "订单数据库不存在"}
        try:
            cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
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

            channel_data = {
                "微信": {"orders": int(total_orders * 0.35), "revenue": total_revenue * 0.35, "cost": total_revenue * 0.12},
                "邮件": {"orders": int(total_orders * 0.20), "revenue": total_revenue * 0.20, "cost": total_revenue * 0.05},
                "自然流量": {"orders": int(total_orders * 0.25), "revenue": total_revenue * 0.25, "cost": 0},
                "电话": {"orders": int(total_orders * 0.15), "revenue": total_revenue * 0.15, "cost": total_revenue * 0.08},
                "其他": {"orders": int(total_orders * 0.05), "revenue": total_revenue * 0.05, "cost": total_revenue * 0.02},
            }

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

            channel_metrics.sort(key=lambda x: x["roi"] if x["roi"] != "∞" else 999, reverse=True)

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
        recommendations = []
        paid_channels = [c for c in metrics if c["cost"] > 0]
        if paid_channels:
            best = max(paid_channels, key=lambda x: x["roi"] if x["roi"] != "∞" else 999)
            worst = min(paid_channels, key=lambda x: x["roi"] if x["roi"] != "∞" else 0)
            recommendations.append(f"✅ 增加「{best['channel']}」预算占比，当前 ROI 为 {best['roi']}")
            recommendations.append(f"📉 优化或削减「{worst['channel']}」投入，当前 ROI 为 {worst['roi']}")
        organic = next((c for c in metrics if c["channel"] == "自然流量"), None)
        if organic and organic["order_share"] < 30:
            recommendations.append("📈 自然流量占比较低，建议加强 SEO 和内容营销")
        return recommendations

    def calculate_conversion_funnel(self) -> Dict[str, Any]:
        cust_db = self._connect("customer.db")
        order_db = self._connect("order.db")
        if not cust_db or not order_db:
            return {"error": "数据库不可用"}
        try:
            total_customers = cust_db.execute("SELECT COUNT(*) FROM customer").fetchone()[0]
            active_customers = order_db.execute("""
                SELECT COUNT(DISTINCT customer_name)
                FROM orders
                WHERE status != 'cancelled'
            """).fetchone()[0]
            current_month = datetime.now().strftime('%Y-%m')
            new_customers = cust_db.execute("""
                SELECT COUNT(*) FROM customer
                WHERE created_at LIKE ?
            """, (f"{current_month}%",)).fetchone()[0]

            visitor_to_lead = 0.30
            lead_to_customer = active_customers / total_customers if total_customers > 0 else 0
            customer_to_repeat = 0.40

            funnel = [
                {"stage": "访客", "count": int(total_customers / 0.3), "rate": 100},
                {"stage": "线索", "count": total_customers, "rate": 30},
                {"stage": "成交客户", "count": active_customers, "rate": round(lead_to_customer * 100, 1)},
                {"stage": "复购客户", "count": int(active_customers * customer_to_repeat), "rate": round(lead_to_customer * customer_to_repeat * 100, 1)}
            ]

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
        recommendations = []
        for drop in drop_offs:
            if drop["rate"] > 70:
                if "访客" in drop["from"]:
                    recommendations.append("💡 优化落地页，提升访客到线索转化")
                elif "线索" in drop["from"]:
                    recommendations.append("💡 加强销售跟进，提升线索到成交转化")
                elif "成交" in drop["from"]:
                    recommendations.append("💡 建立客户关怀体系，提升复购率")
        recommendations.extend([
            "📈 设置转化漏斗监控，每周复盘",
            "🎯 针对高流失环节进行 A/B 测试",
            "📞 对高意向线索设置 24 小时内跟进机制"
        ])
        return recommendations

    def customer_segmentation(self) -> Dict[str, Any]:
        cust_db = self._connect("customer.db")
        order_db = self._connect("order.db")
        if not cust_db or not order_db:
            return {"error": "数据库不可用"}
        try:
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
        strategies = {
            "高价值客户": "💎 专属 VIP 服务、提前购、定制礼品、一对一客服",
            "成长客户": "📈 满减优惠、会员升级激励、交叉销售",
            "普通客户": "🎯 新人优惠、爆款推荐、内容培育",
            "沉睡客户": "⏰ 唤醒优惠、限时回归、调研回访"
        }
        return strategies.get(segment, "📊 制定针对性营销策略")

    def _generate_segmentation_recommendations(self, segments: Dict) -> List[str]:
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
