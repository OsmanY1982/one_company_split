"""
销售预测服务
基于历史数据进行销售预测
"""

import sqlite3
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class SalesPredictionService:
    """销售预测服务"""

    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path

    def predict_next_day(self) -> Dict:
        """预测明日销售"""
        history = self._get_daily_sales(30)

        if not history:
            return {"success": False, "message": "历史数据不足"}

        # 简单移动平均
        amounts = [d["total"] for d in history]
        avg = sum(amounts) / len(amounts)

        # 趋势分析
        trend = self._calculate_trend(amounts)

        prediction = avg + trend

        return {
            "success": True,
            "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "prediction": round(prediction, 2),
            "method": "移动平均 + 趋势",
            "confidence": min(round(len(history) / 30 * 100, 1), 100),
            "avg_recent_30d": round(avg, 2),
            "trend": round(trend, 2),
        }

    def predict_next_week(self) -> Dict:
        """预测下周销售"""
        history = self._get_daily_sales(90)

        if not history:
            return {"success": False, "message": "历史数据不足"}

        amounts = [d["total"] for d in history]

        # 周均值
        weekly_avg = sum(amounts) / max(len(amounts), 1) * 7

        predictions = []
        for i in range(7):
            date = datetime.now() + timedelta(days=i + 1)
            # 加权预测（近期权重更高）
            if len(amounts) >= 7:
                week_ago = amounts[-7:][i] if i < len(amounts[-7:]) else amounts[-1]
            else:
                week_ago = amounts[-1]

            day_name = date.strftime("%A")
            # 周末调整
            weekday_factor = 0.8 if day_name in ["Saturday", "Sunday", "星期六", "星期日"] else 1.0

            pred = (week_ago * 0.7 + (weekly_avg / 7) * 0.3) * weekday_factor
            predictions.append({
                "date": date.strftime("%Y-%m-%d"),
                "day": day_name,
                "prediction": round(pred, 2),
            })

        return {
            "success": True,
            "week_start": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "predictions": predictions,
            "total_weekly_prediction": round(sum(p["prediction"] for p in predictions), 2),
        }

    def predict_next_month(self) -> Dict:
        """预测下月销售"""
        history = self._get_monthly_sales(12)

        if not history:
            return {"success": False, "message": "历史数据不足"}

        amounts = [d["total"] for d in history]

        # 月均值
        monthly_avg = sum(amounts) / max(len(amounts), 1)

        # 趋势
        trend = self._calculate_trend(amounts)

        prediction = monthly_avg * (1 + trend / monthly_avg) if monthly_avg > 0 else monthly_avg

        next_month = datetime.now().month + 1
        next_year = datetime.now().year
        if next_month > 12:
            next_month = 1
            next_year += 1

        return {
            "success": True,
            "month": f"{next_year}-{next_month:02d}",
            "prediction": round(prediction, 2),
            "monthly_avg": round(monthly_avg, 2),
            "trend": round(trend, 2),
            "method": "月均值 + 趋势分析",
        }

    def predict_product_demand(self, days: int = 30) -> Dict:
        """预测产品需求"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            start_date = datetime.now() - timedelta(days=days * 2)

            cursor = conn.execute("""
                SELECT oi.product_id, p.name, oi.quantity, o.created_at
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                LEFT JOIN products p ON oi.product_id = p.id
                WHERE o.created_at >= ?
            """, (int(start_date.timestamp()),))

            rows = cursor.fetchall()

        if not rows:
            return {"success": False, "message": "没有足够数据"}

        # 按产品分组
        product_data = defaultdict(list)
        product_names = {}

        for row in rows:
            product_data[row["product_id"]].append(row["quantity"])
            product_names[row["product_id"]] = row["name"] or str(row["product_id"])

        predictions = []
        for product_id, quantities in product_data.items():
            if len(quantities) < 5:
                continue

            midpoint = len(quantities) // 2
            first_half_avg = sum(quantities[:midpoint]) / midpoint
            second_half_avg = sum(quantities[midpoint:]) / (len(quantities) - midpoint)

            growth_rate = (second_half_avg - first_half_avg) / first_half_avg if first_half_avg > 0 else 0

            recent_avg = sum(quantities[-min(7, len(quantities)):]) / min(7, len(quantities))
            prediction = recent_avg * (1 + growth_rate)

            predictions.append({
                "product_id": product_id,
                "product_name": product_names[product_id],
                "recent_avg_daily": round(recent_avg, 2),
                "growth_rate": round(growth_rate * 100, 1),
                "predicted_daily_demand": round(prediction, 2),
                "predicted_30d_demand": round(prediction * 30, 0),
            })

        # 按预测需求排序
        predictions.sort(key=lambda x: x["predicted_30d_demand"], reverse=True)

        return {
            "success": True,
            "predictions": predictions[:20],
            "method": "半期对比 + 近期加权",
        }

    def _get_daily_sales(self, days: int) -> List[Dict]:
        """获取每日销售数据"""
        start_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT DATE(created_at, 'unixepoch') as date,
                       COALESCE(SUM(total_amount), 0) as total,
                       COUNT(*) as count
                FROM orders
                WHERE created_at >= ?
                GROUP BY DATE(created_at, 'unixepoch')
                ORDER BY date
            """, (int(start_date.timestamp()),))
            return [dict(row) for row in cursor.fetchall()]

    def _get_monthly_sales(self, months: int) -> List[Dict]:
        """获取每月销售数据"""
        start_date = datetime.now() - timedelta(days=months * 30)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT strftime('%Y-%m', created_at, 'unixepoch') as month,
                       COALESCE(SUM(total_amount), 0) as total,
                       COUNT(*) as count
                FROM orders
                WHERE created_at >= ?
                GROUP BY strftime('%Y-%m', created_at, 'unixepoch')
                ORDER BY month
            """, (int(start_date.timestamp()),))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def _calculate_trend(values: List[float]) -> float:
        """计算趋势"""
        n = len(values)
        if n < 2:
            return 0

        x_mean = (n - 1) / 2
        y_mean = sum(values) / n

        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        return numerator / denominator if denominator != 0 else 0

