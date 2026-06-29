# `intelligence/monitor_dashboard.py`

> 路径：`intelligence/monitor_dashboard.py` | 行数：348


---


```python
# -*- coding: utf-8 -*-
"""
监控仪表板
实时展示系统运行状态、业务指标和异常告警
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from core.database import get_conn, close_conn


@dataclass
class Metric:
    """监控指标"""
    name: str
    value: float
    unit: str = ""
    trend: str = "stable"  # up, down, stable
    min_value: float = 0
    max_value: float = 100
    alert_threshold: Optional[float] = None
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Alert:
    """告警信息"""
    id: str
    title: str
    message: str
    severity: str  # info, warning, error, critical
    source: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    acknowledged: bool = False
    resolved_at: Optional[str] = None


class MonitorDashboard:
    """监控仪表板"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(BASE_DIR, "data")
        
        self.data_dir = data_dir
        self.metrics: Dict[str, Metric] = {}
        self.alerts: List[Alert] = []
        self._history: Dict[str, List[Dict]] = {}
        self._running = False
        
        self._init_default_metrics()
    
    def _init_default_metrics(self):
        """初始化默认监控指标"""
        self.metrics = {
            "daily_sales": Metric(
                name="今日销售额",
                value=0,
                unit="元",
                trend="stable",
                alert_threshold=None
            ),
            "order_count": Metric(
                name="订单数",
                value=0,
                unit="笔",
                trend="stable",
                alert_threshold=None
            ),
            "avg_order_value": Metric(
                name="客单价",
                value=0,
                unit="元",
                trend="stable",
                alert_threshold=None
            ),
            "inventory_low_count": Metric(
                name="低库存商品",
                value=0,
                unit="个",
                trend="stable",
                alert_threshold=5
            ),
            "pending_orders": Metric(
                name="待处理订单",
                value=0,
                unit="笔",
                trend="stable",
                alert_threshold=20
            ),
            "member_count": Metric(
                name="活跃会员",
                value=0,
                unit="人",
                trend="stable"
            ),
            "month_revenue": Metric(
                name="本月营收",
                value=0,
                unit="元",
                trend="stable"
            ),
            "month_growth": Metric(
                name="环比增长",
                value=0,
                unit="%",
                trend="stable",
                alert_threshold=-10
            )
        }
    
    def refresh(self):
        """刷新所有指标"""
        try:
            db_path = os.path.join(BASE_DIR, "data", "orders.db")
            
            if not os.path.exists(db_path):
                return
            
            conn = get_conn('order.db')
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            
            # 今日销售额
            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM orders "
                "WHERE DATE(created_at) = ? AND status != 'cancelled'",
                (today,)
            )
            daily_sales, order_count = cursor.fetchone()
            
            # 客单价
            avg_order = round(daily_sales / order_count, 2) if order_count > 0 else 0
            
            # 低库存
            cursor.execute("SELECT COUNT(*) FROM products WHERE stock <= 10")
            low_stock = cursor.fetchone()[0]
            
            # 待处理订单
            cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
            pending = cursor.fetchone()[0]
            
            # 活跃会员
            cursor.execute(
                "SELECT COUNT(DISTINCT customer_id) FROM orders "
                "WHERE created_at >= date('now', '-30 days')"
            )
            active_members = cursor.fetchone()[0]
            
            # 本月营收
            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM orders "
                "WHERE DATE(created_at) >= ? AND status != 'cancelled'",
                (month_start,)
            )
            month_revenue = cursor.fetchone()[0]
            
            # 上月营收（计算环比）
            last_month_start = (datetime.now().replace(day=1) - timedelta(days=1)).replace(day=1).strftime('%Y-%m-%d')
            cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM orders "
                "WHERE DATE(created_at) >= ? AND DATE(created_at) < ? AND status != 'cancelled'",
                (last_month_start, month_start)
            )
            last_month_revenue = cursor.fetchone()[0]
            
            if last_month_revenue > 0:
                month_growth = round((month_revenue - last_month_revenue) / last_month_revenue * 100, 1)
            else:
                month_growth = 0 if month_revenue == 0 else 100
            
            close_conn('order.db')
            
            # 更新指标
            self._update_metric("daily_sales", daily_sales)
            self._update_metric("order_count", order_count)
            self._update_metric("avg_order_value", avg_order)
            self._update_metric("inventory_low_count", low_stock)
            self._update_metric("pending_orders", pending)
            self._update_metric("member_count", active_members)
            self._update_metric("month_revenue", month_revenue)
            self._update_metric("month_growth", month_growth)
            
            # 检查告警
            self._check_alerts()
            
            # 记录历史
            self._record_history()
            
        except Exception as e:
            print(f"[MonitorDashboard] 刷新失败: {e}")
    
    def _update_metric(self, name: str, value: float):
        """更新指标值"""
        if name in self.metrics:
            old_value = self.metrics[name].value
            self.metrics[name].value = value
            self.metrics[name].updated_at = datetime.now().isoformat()
            
            # 判断趋势
            if value > old_value * 1.1:
                self.metrics[name].trend = "up"
            elif value < old_value * 0.9 and old_value > 0:
                self.metrics[name].trend = "down"
            else:
                self.metrics[name].trend = "stable"
    
    def _check_alerts(self):
        """检查告警"""
        for name, metric in self.metrics.items():
            if metric.alert_threshold is not None:
                # 检查是否超出阈值
                if name in ["inventory_low_count", "pending_orders"]:
                    if metric.value > metric.alert_threshold:
                        self._add_alert(
                            title=f"{metric.name}异常",
                            message=f"{metric.name}当前值为 {metric.value}{metric.unit}，超过阈值 {metric.alert_threshold}{metric.unit}",
                            severity="warning" if metric.value > metric.alert_threshold * 1.5 else "info",
                            source="monitor"
                        )
                elif name == "month_growth":
                    if metric.value < metric.alert_threshold:
                        self._add_alert(
                            title="营收增长预警",
                            message=f"环比增长为 {metric.value}%，低于警戒线 {metric.alert_threshold}%",
                            severity="error" if metric.value < metric.alert_threshold * 2 else "warning",
                            source="monitor"
                        )
    
    def _add_alert(self, title: str, message: str, severity: str = "info", source: str = "monitor"):
        """添加告警"""
        import uuid
        alert = Alert(
            id=str(uuid.uuid4())[:8],
            title=title,
            message=message,
            severity=severity,
            source=source
        )
        self.alerts.append(alert)
    
    def _record_history(self):
        """记录历史数据"""
        now = datetime.now().isoformat()
        for name, metric in self.metrics.items():
            if name not in self._history:
                self._history[name] = []
            self._history[name].append({
                "value": metric.value,
                "time": now
            })
            # 只保留最近100条
            if len(self._history[name]) > 100:
                self._history[name] = self._history[name][-100:]
    
    def get_dashboard_data(self) -> Dict:
        """获取仪表板数据"""
        return {
            "metrics": {
                name: {
                    "value": m.value,
                    "unit": m.unit,
                    "trend": m.trend,
                    "updated_at": m.updated_at
                }
                for name, m in self.metrics.items()
            },
            "alerts": [
                {
                    "id": a.id,
                    "title": a.title,
                    "message": a.message,
                    "severity": a.severity,
                    "created_at": a.created_at,
                    "acknowledged": a.acknowledged
                }
                for a in self.alerts[-10:]
            ]
        }
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.resolved_at = datetime.now().isoformat()
                return True
        return False
    
    def get_alerts(self, severity: str = None, limit: int = 50) -> List[Alert]:
        """获取告警列表"""
        alerts = self.alerts
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts[-limit:]
    
    def start_monitoring(self, interval: int = 60):
        """启动监控"""
        if self._running:
            return
        
        self._running = True
        
        def _monitor_loop():
            while self._running:
                try:
                    self.refresh()
                except Exception as e:
                    print(f"[MonitorDashboard] 监控异常: {e}")
                time.sleep(interval)
        
        threading.Thread(target=_monitor_loop, daemon=True).start()
        print(f"[MonitorDashboard] 监控已启动，刷新间隔: {interval}秒")
    
    def stop_monitoring(self):
        """停止监控"""
        self._running = False
        print("[MonitorDashboard] 监控已停止")


# 全局仪表板实例
_dashboard = None

def get_dashboard() -> MonitorDashboard:
    """获取全局仪表板实例"""
    global _dashboard
    if _dashboard is None:
        _dashboard = MonitorDashboard()
    return _dashboard

```
