"""
内存监控服务
系统内存使用监控和优化
"""

import psutil
import gc
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import deque


@dataclass
class MemorySnapshot:
    """内存快照"""
    timestamp: float
    total_mb: float
    available_mb: float
    used_mb: float
    percent: float


class MemoryService:
    """内存监控服务"""

    def __init__(self, threshold_percent: float = 85.0, history_size: int = 60):
        self.threshold_percent = threshold_percent
        self._history: deque = deque(maxlen=history_size)
        self._warnings: List[str] = []
        self._is_monitoring = False

    def start_monitoring(self):
        """开始监控"""
        self._is_monitoring = True

    def stop_monitoring(self):
        """停止监控"""
        self._is_monitoring = False

    def get_current_usage(self) -> Dict:
        """获取当前内存使用"""
        mem = psutil.virtual_memory()

        snapshot = MemorySnapshot(
            timestamp=time.time(),
            total_mb=mem.total / (1024 * 1024),
            available_mb=mem.available / (1024 * 1024),
            used_mb=mem.used / (1024 * 1024),
            percent=mem.percent,
        )

        self._history.append(snapshot)

        # 检查阈值
        if mem.percent > self.threshold_percent:
            self._warnings.append(
                f"内存使用率 {mem.percent}% 超过阈值 {self.threshold_percent}%"
            )

        return {
            "total_mb": round(snapshot.total_mb, 2),
            "available_mb": round(snapshot.available_mb, 2),
            "used_mb": round(snapshot.used_mb, 2),
            "percent": snapshot.percent,
            "timestamp": snapshot.timestamp,
        }

    def get_history(self, limit: Optional[int] = None) -> List[Dict]:
        """获取历史记录"""
        snapshots = list(self._history)
        if limit:
            snapshots = snapshots[-limit:]

        return [
            {
                "timestamp": s.timestamp,
                "used_mb": round(s.used_mb, 2),
                "percent": s.percent,
            }
            for s in snapshots
        ]

    def get_average_usage(self, last_n: int = 10) -> Dict:
        """获取平均使用率"""
        snapshots = list(self._history)[-last_n:]
        if not snapshots:
            return {"error": "没有数据"}

        avg_percent = sum(s.percent for s in snapshots) / len(snapshots)
        avg_used_mb = sum(s.used_mb for s in snapshots) / len(snapshots)

        return {
            "avg_percent": round(avg_percent, 2),
            "avg_used_mb": round(avg_used_mb, 2),
            "samples": len(snapshots),
        }

    def get_warnings(self, clear: bool = False) -> List[str]:
        """获取警告列表"""
        warnings = list(self._warnings)
        if clear:
            self._warnings.clear()
        return warnings

    def force_garbage_collection(self) -> Dict:
        """强制垃圾回收"""
        gc.collect()

        before = self.get_current_usage()
        gc.collect(2)  # 全量回收
        after = self.get_current_usage()

        freed_mb = round(before["used_mb"] - after["used_mb"], 2)

        return {
            "success": True,
            "before_mb": before["used_mb"],
            "after_mb": after["used_mb"],
            "freed_mb": freed_mb,
        }

    def get_optimization_suggestions(self) -> List[str]:
        """获取优化建议"""
        suggestions = []

        if not self._history:
            return ["暂无内存数据"]

        avg = self.get_average_usage()
        current = self.get_current_usage()

        if avg.get("avg_percent", 0) > 70:
            suggestions.append("平均内存使用率较高，建议关闭不必要的应用")

        if current.get("percent", 0) > 90:
            suggestions.append("内存严重不足，建议立即清理")

        suggestions.append("定期重启应用可释放内存碎片")

        return suggestions

    def clear_history(self):
        """清除历史"""
        self._history.clear()
        self._warnings.clear()

