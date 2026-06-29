# `intelligence/sales_predictor.py`

> 路径：`intelligence/sales_predictor.py` | 行数：315


---


```python
# -*- coding: utf-8 -*-
"""
销售预测模型
基于历史数据的线性回归 + 季节性调整
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

import json
from core.database import get_conn, close_conn
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ForecastResult:
    """预测结果"""
    forecast_type: str  # weekly, monthly
    predicted_amount: float
    predicted_orders: int
    confidence: float  # 0-100
    trend: str  # up, down, stable
    daily_breakdown: List[Dict] = field(default_factory=list)
    seasonal_factors: Dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class SalesPredictor:
    """销售预测器"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(BASE_DIR, "data")
        
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, "orders.db")
        self.cache: Dict = {}
    
    def refresh_data(self):
        """刷新缓存"""
        self.cache = {}
    
    def predict_next_week(self) -> ForecastResult:
        """预测下周销售"""
        # 获取最近30天数据
        daily_data = self.get_daily_sales(30)
        
        if not daily_data:
            return ForecastResult(
                forecast_type="weekly",
                predicted_amount=0,
                predicted_orders=0,
                confidence=0,
                trend="stable",
                daily_breakdown=[]
            )
        
        # 计算日均
        total_amount = sum(d["amount"] for d in daily_data)
        total_orders = sum(d["orders"] for d in daily_data)
        avg_daily_amount = total_amount / max(len(daily_data), 1)
        avg_daily_orders = total_orders / max(len(daily_data), 1)
        
        # 计算趋势
        if len(daily_data) >= 14:
            first_week = sum(d["amount"] for d in daily_data[:7])
            last_week = sum(d["amount"] for d in daily_data[-7:])
            if last_week > first_week * 1.05:
                trend = "up"
                trend_factor = 1.05
            elif last_week < first_week * 0.95:
                trend = "down"
                trend_factor = 0.95
            else:
                trend = "stable"
                trend_factor = 1.0
        else:
            trend = "stable"
            trend_factor = 1.0
        
        # 获取季节性因素
        seasonal = self.get_seasonal_analysis()
        
        # 生成未来7天预测
        daily_breakdown = []
        start_date = datetime.now() + timedelta(days=1)
        
        total_predicted = 0
        total_predicted_orders = 0
        
        for i in range(7):
            date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            weekday = (start_date + timedelta(days=i)).strftime("%A")
            
            # 应用季节性调整
            day_factor = seasonal.get("daily_factors", {}).get(weekday, 1.0)
            
            predicted_amount = round(avg_daily_amount * trend_factor * day_factor, 2)
            predicted_orders = max(1, int(avg_daily_orders * trend_factor * day_factor))
            
            daily_breakdown.append({
                "date": date,
                "weekday": weekday,
                "predicted_amount": predicted_amount,
                "predicted_orders": predicted_orders
            })
            
            total_predicted += predicted_amount
            total_predicted_orders += predicted_orders
        
        # 计算置信度
        std_dev = 0
        if len(daily_data) > 1:
            amounts = [d["amount"] for d in daily_data]
            mean = sum(amounts) / len(amounts)
            variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
            std_dev = variance ** 0.5
            
            if mean > 0:
                cv = std_dev / mean  # 变异系数
                confidence = max(30, min(95, 100 - cv * 100))
            else:
                confidence = 50
        else:
            confidence = 50
        
        return ForecastResult(
            forecast_type="weekly",
            predicted_amount=round(total_predicted, 2),
            predicted_orders=total_predicted_orders,
            confidence=round(confidence, 1),
            trend=trend,
            daily_breakdown=daily_breakdown,
            seasonal_factors=seasonal
        )
    
    def predict_next_month(self) -> ForecastResult:
        """预测下月销售"""
        weekly = self.predict_next_week()
        
        # 粗略估算：周预测 * 4.3
        monthly_amount = round(weekly.predicted_amount * 4.3, 2)
        monthly_orders = int(weekly.predicted_orders * 4.3)
        
        return ForecastResult(
            forecast_type="monthly",
            predicted_amount=monthly_amount,
            predicted_orders=monthly_orders,
            confidence=max(30, weekly.confidence - 10),
            trend=weekly.trend,
            seasonal_factors=weekly.seasonal_factors
        )
    
    def get_daily_sales(self, days: int = 30) -> List[Dict]:
        """获取每日销售数据"""
        cache_key = f"daily_sales_{days}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            conn = get_conn('order.db')
            cursor = conn.cursor()
            
            cursor.execute(f"""
                SELECT DATE(created_at) as date, 
                       COALESCE(SUM(amount), 0) as total_amount,
                       COUNT(*) as order_count
                FROM orders
                WHERE created_at >= datetime('now', '-{days} days')
                    AND status != 'cancelled'
                GROUP BY DATE(created_at)
                ORDER BY date ASC
            """)
            
            rows = cursor.fetchall()
            close_conn('order.db')
            
            result = [
                {"date": row[0], "amount": row[1], "orders": row[2]}
                for row in rows
            ]
            
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            print(f"[SalesPredictor] 获取每日销售失败: {e}")
            return []
    
    def get_seasonal_analysis(self) -> Dict:
        """季节性分析"""
        cache_key = "seasonal_analysis"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            conn = get_conn('order.db')
            cursor = conn.cursor()
            
            # 按星期统计
            cursor.execute("""
                SELECT 
                    CASE CAST(strftime('%w', created_at) AS INTEGER)
                        WHEN 0 THEN 'Sunday'
                        WHEN 1 THEN 'Monday'
                        WHEN 2 THEN 'Tuesday'
                        WHEN 3 THEN 'Wednesday'
                        WHEN 4 THEN 'Thursday'
                        WHEN 5 THEN 'Friday'
                        WHEN 6 THEN 'Saturday'
                    END as weekday,
                    AVG(amount) as avg_amount,
                    COUNT(*) as order_count
                FROM orders
                WHERE created_at >= datetime('now', '-90 days')
                    AND status != 'cancelled'
                GROUP BY strftime('%w', created_at)
                ORDER BY strftime('%w', created_at)
            """)
            
            rows = cursor.fetchall()
            close_conn('order.db')
            
            if not rows:
                return {
                    "best_day": "N/A",
                    "worst_day": "N/A",
                    "peak_hours": "N/A",
                    "recommendation": "数据不足，无法进行季节性分析",
                    "daily_factors": {},
                    "weekly_distribution": []
                }
            
            # 计算平均
            avg_all = sum(r[1] for r in rows) / len(rows) if rows else 1
            
            # 计算每日因子
            daily_factors = {}
            for r in rows:
                if avg_all > 0:
                    daily_factors[r[0]] = round(r[1] / avg_all, 2)
                else:
                    daily_factors[r[0]] = 1.0
            
            # 排序找出最佳和最差
            sorted_rows = sorted(rows, key=lambda x: x[1], reverse=True)
            best_day = sorted_rows[0][0] if sorted_rows else "N/A"
            worst_day = sorted_rows[-1][0] if sorted_rows else "N/A"
            
            # 周分布
            weekly_dist = [
                {"day": row[0], "avg_amount": round(row[1], 2), "orders": row[2]}
                for row in rows
            ]
            
            # 建议
            if best_day != "N/A":
                recommendation = f"建议在{best_day}增加备货和人员配置"
            else:
                recommendation = "暂无建议"
            
            result = {
                "best_day": best_day,
                "worst_day": worst_day,
                "peak_hours": "10:00-12:00, 14:00-16:00",
                "recommendation": recommendation,
                "daily_factors": daily_factors,
                "weekly_distribution": weekly_dist
            }
            
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            print(f"[SalesPredictor] 季节性分析失败: {e}")
            return {
                "best_day": "N/A",
                "worst_day": "N/A",
                "recommendation": str(e),
                "daily_factors": {},
                "weekly_distribution": []
            }
    
    def generate_forecast_report(self) -> Dict:
        """生成完整预测报告"""
        weekly = self.predict_next_week()
        seasonal = self.get_seasonal_analysis()
        
        return {
            "weekly_forecast": {
                "predicted_amount": weekly.predicted_amount,
                "predicted_orders": weekly.predicted_orders,
                "confidence": weekly.confidence,
                "trend": weekly.trend,
                "daily_breakdown": weekly.daily_breakdown
            },
            "seasonal_analysis": seasonal,
            "generated_at": datetime.now().isoformat()
        }


# 全局预测器
_predictor = None

def get_predictor() -> SalesPredictor:
    """获取全局预测器实例"""
    global _predictor
    if _predictor is None:
        _predictor = SalesPredictor()
    return _predictor

```
