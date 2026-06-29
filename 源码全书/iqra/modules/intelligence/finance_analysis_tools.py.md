# `iqra/modules/intelligence/finance_analysis_tools.py`

> 路径：`iqra/modules/intelligence/finance_analysis_tools.py` | 行数：146


---


```python
"""财务分析工具 — 利润分析、现金流、预算对比、财务健康度"""

import os, sqlite3
from datetime import datetime, timedelta

class FinanceAnalysisTools:
    def __init__(self, data_dir): self.data_dir = data_dir
    
    def _connect(self, db_name):
        path = os.path.join(self.data_dir, db_name)
        if not os.path.exists(path): return None
        conn = sqlite3.connect(path); conn.row_factory = sqlite3.Row; conn.text_factory = lambda x: str(x,'utf-8','replace')
        return conn

    def profit_analysis(self, months=3) -> dict:
        """利润趋势分析"""
        db = self._connect("finance.db")
        if not db: return {"error": "财务数据库不存在"}
        
        try:
            # 获取最近N个月数据
            results = []
            for i in range(months):
                target_month = (datetime.now() - timedelta(days=30*i)).strftime("%Y-%m")
                row = db.execute("""SELECT 
                    COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE 0 END),0) as income,
                    COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END),0) as expense
                    FROM finance WHERE date LIKE ?""", (f"{target_month}%",)).fetchone()
                
                if row:
                    income = float(row["income"])
                    expense = float(row["expense"])
                    profit = income - expense
                    margin = (profit / income * 100) if income > 0 else 0
                    results.append({
                        "month": target_month,
                        "income": round(income, 2),
                        "expense": round(expense, 2),
                        "profit": round(profit, 2),
                        "margin_pct": round(margin, 2)
                    })
            
            # 计算趋势
            if len(results) >= 2:
                latest = results[0]
                prev = results[1]
                profit_growth = ((latest["profit"] - prev["profit"]) / abs(prev["profit"])) * 100 if prev["profit"] != 0 else 0
            else:
                profit_growth = 0
            
            return {
                "period": f"近{months}个月",
                "monthly_data": results,
                "profit_trend": "📈 上升" if profit_growth > 5 else "📉 下降" if profit_growth < -5 else "➡️ 平稳",
                "profit_growth_rate": round(profit_growth, 2),
                "avg_profit_margin": round(sum(r["margin_pct"] for r in results)/len(results), 2) if results else 0,
                "recommendations": self._profit_recommendations(results)
            }
        finally: db.close()
    
    def _profit_recommendations(self, monthly_data):
        recs = []
        if not monthly_data: return ["📊 暂无财务数据"]
        
        # 成本控制建议
        avg_expense_ratio = sum(r["expense"]/r["income"] if r["income"]>0 else 0 for r in monthly_data)/len(monthly_data)
        if avg_expense_ratio > 0.7:
            recs.append("⚠️ 成本占比过高（>70%），建议优化支出结构")
        
        # 利润率建议
        avg_margin = sum(r["margin_pct"] for r in monthly_data)/len(monthly_data)
        if avg_margin < 20:
            recs.append(f"💡 平均利润率{avg_margin:.1f}%偏低，考虑提价或降低成本")
        elif avg_margin > 40:
            recs.append(f"✅ 平均利润率{avg_margin:.1f}%优秀，可考虑扩大规模")
        
        # 现金流建议
        recent = monthly_data[0] if monthly_data else {}
        if recent.get("profit", 0) < 0:
            recs.append("🚨 近期亏损，需紧急关注现金流")
        
        recs.append("📊 建议每月进行财务复盘，及时调整经营策略")
        return recs
    
    def cash_flow_forecast(self, days=30) -> dict:
        """现金流预测"""
        # 基于历史数据的简单预测
        db = self._connect("finance.db")
        if not db: return {"error": "财务数据库不存在"}
        
        try:
            # 获取历史平均日收入/支出
            cursor = db.execute("""SELECT 
                AVG(CASE WHEN type='income' THEN amount ELSE 0 END) as avg_income,
                AVG(CASE WHEN type='expense' THEN amount ELSE 0 END) as avg_expense,
                COUNT(*) as record_count
                FROM finance""")
            stats = cursor.fetchone()
            
            avg_daily_income = float(stats["avg_income"] or 0)
            avg_daily_expense = float(stats["avg_expense"] or 0)
            
            forecast = []
            current_balance = 10000  # 假设起始余额
            
            for day in range(1, days+1):
                daily_income = avg_daily_income
                daily_expense = avg_daily_expense
                net_change = daily_income - daily_expense
                current_balance += net_change
                
                forecast.append({
                    "day": day,
                    "date": (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d"),
                    "income": round(daily_income, 2),
                    "expense": round(daily_expense, 2),
                    "net": round(net_change, 2),
                    "balance": round(current_balance, 2)
                })
            
            # 风险预警
            risk_days = [f for f in forecast if f["balance"] < 5000]
            
            return {
                "forecast_period": f"未来{days}天",
                "starting_balance": 10000,
                "daily_avg_income": round(avg_daily_income, 2),
                "daily_avg_expense": round(avg_daily_expense, 2),
                "ending_balance": forecast[-1]["balance"],
                "risk_days_count": len(risk_days),
                "cash_flow_health": "🟢 健康" if forecast[-1]["balance"] > 8000 else "🟡 警告" if forecast[-1]["balance"] > 3000 else "🔴 危险",
                "recommendations": [
                    f"💰 预计{days}天后余额：¥{forecast[-1]['balance']:.2f}",
                    f"⚠️ 有{len(risk_days)}天余额低于安全线" if risk_days else "✅ 现金流充足",
                    "📈 建议建立3个月应急资金储备"
                ]
            }
        finally: db.close()


def register_finance_analysis_tools(registry, data_dir):
    from modules.intelligence.tool_registry import ToolDefinition
    f = FinanceAnalysisTools(data_dir)
    registry.add_tool(ToolDefinition(name="profit_analysis", description="利润趋势分析：近几个月收入/支出/利润率变化及建议", parameters={"type":"object","properties":{"months":{"type":"integer","default":3}}}, handler=lambda months=3: f.profit_analysis(months)))
    registry.add_tool(ToolDefinition(name="cash_flow_forecast", description="现金流预测：未来30天每日收支预测和风险预警", parameters={"type":"object","properties":{"days":{"type":"integer","default":30}}}, handler=lambda days=30: f.cash_flow_forecast(days)))


```
