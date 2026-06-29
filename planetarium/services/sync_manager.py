"""
同步管理器
多端数据同步引擎
"""

import json
import hashlib
import threading
import time
from typing import Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum


class SyncDirection(Enum):
    PUSH = "push"      # 本地 → 远端
    PULL = "pull"      # 远端 → 本地
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(Enum):
    IDLE = "idle"
    SYNCING = "syncing"
    CONFLICT = "conflict"
    ERROR = "error"


class SyncManager:
    """同步管理器"""

    def __init__(self):
        self._status = SyncStatus.IDLE
        self._last_sync: Optional[datetime] = None
        self._current_sync: Optional[Dict] = None
        self._sync_handlers: Dict[str, Callable] = {}
        self._conflict_resolver: Optional[Callable] = None
        self._sync_interval: int = 300  # 5分钟
        self._auto_sync_enabled: bool = False
        self._sync_thread: Optional[threading.Thread] = None
        self._progress: Dict = {"total": 0, "completed": 0, "current": ""}

    def register_handler(self, data_type: str, handler: Callable):
        """注册同步处理器"""
        self._sync_handlers[data_type] = handler

    def set_conflict_resolver(self, resolver: Callable):
        """设置冲突解决器"""
        self._conflict_resolver = resolver

    def start_auto_sync(self, interval: int = 300):
        """启动自动同步"""
        self._sync_interval = interval
        self._auto_sync_enabled = True

        self._sync_thread = threading.Thread(target=self._auto_sync_loop, daemon=True)
        self._sync_thread.start()

    def stop_auto_sync(self):
        """停止自动同步"""
        self._auto_sync_enabled = False

    def _auto_sync_loop(self):
        """自动同步循环"""
        while self._auto_sync_enabled:
            self.sync()
            time.sleep(self._sync_interval)

    def sync(self, data_types: Optional[List[str]] = None, direction: SyncDirection = SyncDirection.BIDIRECTIONAL) -> Dict:
        """执行同步"""
        if self._status == SyncStatus.SYNCING:
            return {"success": False, "message": "同步正在进行中"}

        self._status = SyncStatus.SYNCING
        start_time = datetime.now()

        types_to_sync = data_types or list(self._sync_handlers.keys())

        results = {}
        conflicts = []

        for data_type in types_to_sync:
            handler = self._sync_handlers.get(data_type)
            if not handler:
                results[data_type] = {"status": "skipped", "reason": "未注册处理器"}
                continue

            try:
                result = handler(data_type, direction)
                results[data_type] = result

                if result.get("conflicts"):
                    conflicts.extend(result["conflicts"])

            except Exception as e:
                results[data_type] = {"status": "error", "error": str(e)}

        # 处理冲突
        if conflicts and self._conflict_resolver:
            for conflict in conflicts:
                try:
                    self._conflict_resolver(conflict)
                except Exception:
                    pass

        self._last_sync = datetime.now()
        self._status = SyncStatus.CONFLICT if conflicts else SyncStatus.IDLE

        return {
            "success": True,
            "synced_at": self._last_sync.isoformat(),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
            "types_synced": types_to_sync,
            "results": results,
            "conflict_count": len(conflicts),
        }

    def push(self, data: Dict, data_type: str) -> Dict:
        """推送数据"""
        return self._process_sync(data, data_type, SyncDirection.PUSH)

    def pull(self, data_type: str, filters: Optional[Dict] = None) -> Dict:
        """拉取数据"""
        return self._process_sync(filters or {}, data_type, SyncDirection.PULL)

    def _process_sync(self, data: Dict, data_type: str, direction: SyncDirection) -> Dict:
        """处理同步"""
        handler = self._sync_handlers.get(data_type)
        if not handler:
            return {"success": False, "message": f"未注册处理器: {data_type}"}

        try:
            result = handler(data_type, direction, data)
            return {"success": True, "data_type": data_type, "result": result}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def compare_versions(self, local_data: Dict, remote_data: Dict, keys: List[str]) -> Dict:
        """比较版本"""
        differences = []

        # 统一所有key
        all_keys = set(local_data.keys()) | set(remote_data.keys())

        for key in all_keys:
            local_val = local_data.get(key)
            remote_val = remote_data.get(key)

            if local_val != remote_val:
                differences.append({
                    "key": key,
                    "local": local_val,
                    "remote": remote_val,
                })

        return {
            "local_count": len(local_data),
            "remote_count": len(remote_data),
            "differences": differences,
            "has_conflicts": len(differences) > 0,
        }

    def resolve_conflict(self, key: str, strategy: str = "local_wins") -> bool:
        """解决冲突"""
        # local_wins / remote_wins / merge / manual
        pass

    def get_status(self) -> Dict:
        """获取同步状态"""
        return {
            "status": self._status.value,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "auto_sync": self._auto_sync_enabled,
            "sync_interval": self._sync_interval,
            "registered_types": list(self._sync_handlers.keys()),
        }

    def get_sync_history(self) -> List[Dict]:
        """获取同步历史"""
        # 返回简化的历史记录
        return [{"time": self._last_sync.isoformat(), "status": self._status.value}] if self._last_sync else []

    def calculate_data_hash(self, data: Dict) -> str:
        """计算数据哈希"""
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def detect_changes(self, old_hash: str, new_data: Dict) -> Dict:
        """检测变更"""
        new_hash = self.calculate_data_hash(new_data)

        return {
            "changed": old_hash != new_hash,
            "old_hash": old_hash,
            "new_hash": new_hash,
        }

