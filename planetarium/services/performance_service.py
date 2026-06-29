"""
性能监控服务
应用性能指标收集和分析
"""

import time
import threading
from typing import Dict, List, Optional, Callable
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    value: float
    unit: str
    timestamp: float = field(default_factory=time.time)


class PerformanceService:
    """性能监控服务"""

    def __init__(self, history_size: int = 100):
        self._metrics: Dict[str, deque] = {}
        self._timers: Dict[str, float] = {}
        self._counters: Dict[str, int] = {}
        self._watchers: Dict[str, Callable] = {}
        self._history_size = history_size
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None

    def start_monitoring(self, interval: float = 5.0):
        """开始监控"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True,
        )
        self._monitor_thread.start()

    def stop_monitoring(self):
        """停止监控"""
        self._monitoring = False

    def _monitor_loop(self, interval: float):
        """监控循环"""
        while self._monitoring:
            for name, watcher in self._watchers.items():
                try:
                    value = watcher()
                    self.record(name, value)
                except Exception:
                    pass
            time.sleep(interval)

    def register_watcher(self, name: str, watcher: Callable):
        """注册监控器"""
        self._watchers[name] = watcher

    def record(self, name: str, value: float, unit: str = ""):
        """记录指标"""
        if name not in self._metrics:
            self._metrics[name] = deque(maxlen=self._history_size)

        metric = PerformanceMetric(name=name, value=value, unit=unit)
        self._metrics[name].append(metric)

    def start_timer(self, name: str):
        """开始计时"""
        self._timers[name] = time.time()

    def stop_timer(self, name: str) -> float:
        """停止计时"""
        if name in self._timers:
            elapsed = time.time() - self._timers[name]
            self.record(name, elapsed * 1000, "ms")
            del self._timers[name]
            return elapsed
        return 0

    def increment_counter(self, name: str, value: int = 1):
        """增加计数"""
        self._counters[name] = self._counters.get(name, 0) + value
        self.record(f"{name}_total", self._counters[name], "count")

    def get_counter(self, name: str) -> int:
        """获取计数"""
        return self._counters.get(name, 0)

    def get_metric_stats(self, name: str) -> Optional[Dict]:
        """获取指标统计"""
        metrics = self._metrics.get(name)
        if not metrics:
            return None

        values = [m.value for m in metrics]
        n = len(values)

        if n == 0:
            return None

        avg = sum(values) / n

        return {
            "name": name,
            "count": n,
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "avg": round(avg, 2),
            "latest": round(values[-1], 2),
            "unit": metrics[-1].unit if metrics else "",
        }

    def get_all_stats(self) -> Dict:
        """获取所有指标统计"""
        stats = {}
        for name in self._metrics:
            stat = self.get_metric_stats(name)
            if stat:
                stats[name] = stat

        return stats

    def get_recent_metrics(self, name: str, limit: int = 20) -> List[Dict]:
        """获取最近指标"""
        metrics = self._metrics.get(name)
        if not metrics:
            return []

        items = list(metrics)[-limit:]
        return [
            {
                "value": m.value,
                "unit": m.unit,
                "timestamp": m.timestamp,
            }
            for m in items
        ]

    def measure_execution_time(self, func: Callable) -> Callable:
        """装饰器：测量函数执行时间"""
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = (time.time() - start) * 1000
            self.record(f"func.{func.__name__}", elapsed, "ms")
            return result

        return wrapper

    def get_slow_operations(self, threshold_ms: float = 100) -> List[Dict]:
        """获取慢操作"""
        slow = []
        for name, metrics in self._metrics.items():
            for m in metrics:
                if m.unit == "ms" and m.value > threshold_ms:
                    slow.append({
                        "name": name,
                        "duration_ms": round(m.value, 2),
                        "timestamp": m.timestamp,
                    })

        slow.sort(key=lambda x: x["duration_ms"], reverse=True)
        return slow[:20]

    def get_performance_report(self) -> Dict:
        """生成性能报告"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "metrics": {},
            "counters": dict(self._counters),
            "slow_operations": [],
        }

        # 所有指标统计
        for name in sorted(self._metrics.keys()):
            stat = self.get_metric_stats(name)
            if stat:
                report["metrics"][name] = stat

        # 慢操作
        report["slow_operations"] = self.get_slow_operations(threshold_ms=200)

        return report

    def clear_metrics(self, name: Optional[str] = None):
        """清除指标"""
        if name:
            self._metrics.pop(name, None)
            self._counters.pop(name, None)
        else:
            self._metrics.clear()
            self._counters.clear()

    def get_active_timers(self) -> List[str]:
        """获取活跃计时器"""
        return list(self._timers.keys())

