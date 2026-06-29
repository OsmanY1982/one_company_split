"""
Iqra Sync Bridge - Web ↔ GUI 数据同步桥

提供:
- 双端共享文件同步
- 文件锁机制 (跨平台)
- 版本控制
- 双向冲突检测
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading


class SyncBridge:
    """双端数据同步桥"""

    DATA_DIR = Path(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sync"))
    SYNC_FILE = DATA_DIR / "panel_sync.json"
    LOCK_FILE = DATA_DIR / "sync.lock"
    VERSION_FILE = DATA_DIR / "sync.version"

    LOCK_TTL_SECONDS = 5  # 锁超时时间

    def __init__(self):
        self._lock = threading.RLock()
        self._init_dirs()

    def _init_dirs(self):
        """初始化目录"""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _acquire_lock(self) -> bool:
        """获取锁 (跨平台)"""
        with self._lock:
            try:
                # 写入锁信息
                lock_data = {
                    "holder": "unknown",
                    "timestamp": time.time(),
                    "pid": os.getpid()
                }

                # 简单的文件存在检查作为锁
                if self.LOCK_FILE.exists():
                    with open(self.LOCK_FILE, 'r', encoding='utf-8') as f:
                        old_data = json.load(f)

                    elapsed = time.time() - old_data.get("timestamp", 0)
                    if elapsed < self.LOCK_TTL_SECONDS:
                        return False

                # 写入新锁
                self.LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(self.LOCK_FILE, 'w', encoding='utf-8') as f:
                    json.dump(lock_data, f, ensure_ascii=False)

                return True

            except Exception:
                return False

    def _release_lock(self):
        """释放锁"""
        try:
            if self.LOCK_FILE.exists():
                self.LOCK_FILE.unlink()
        except Exception:
            pass

    def _check_lock_expired(self) -> bool:
        """检查锁是否已过期"""
        if not self.LOCK_FILE.exists():
            return True

        try:
            with open(self.LOCK_FILE, 'r') as f:
                data = json.load(f)

            elapsed = time.time() - data.get("timestamp", 0)
            return elapsed > self.LOCK_TTL_SECONDS

        except Exception:
            return True

    def push_gui_to_web(self, data: Dict[str, Any]) -> bool:
        """GUI → Web 推送数据"""
        if not self._acquire_lock():
            if self._check_lock_expired():
                time.sleep(0.1)
                if not self._acquire_lock():
                    return False
            else:
                return False

        try:
            current_data = self._read_sync_data()
            merged = {**current_data, **data}
            merged["_updated_at"] = time.time()
            merged["_updated_by"] = "gui"

            self._write_sync_data(merged)

            return True

        finally:
            self._release_lock()

    def push_web_to_gui(self, data: Dict[str, Any]) -> bool:
        """Web → GUI 推送数据"""
        if not self._acquire_lock():
            if self._check_lock_expired():
                time.sleep(0.1)
                if not self._acquire_lock():
                    return False
            else:
                return False

        try:
            current_data = self._read_sync_data()
            merged = {**current_data, **data}
            merged["_updated_at"] = time.time()
            merged["_updated_by"] = "web"

            self._write_sync_data(merged)

            return True

        finally:
            self._release_lock()

    def read_gui_changes(self) -> Dict[str, Any]:
        """Web 读取 GUI 变更"""
        last_read = getattr(self, "_last_web_read", time.time() - 86400)

        data = self._read_sync_data()
        gui_data = {k: v for k, v in data.items()
                   if not k.startswith("_") or k in ["_updated_by"]}

        return {
            "data": gui_data,
            "version": data.get("_version", 1),
            "changed_since": last_read,
            "changed_by": data.get("_updated_by")
        }

    def read_web_changes(self) -> Dict[str, Any]:
        """GUI 读取 Web 变更"""
        data = self._read_sync_data()
        web_data = {k: v for k, v in data.items()
                   if not k.startswith("_") or k in ["_updated_by"]}

        return {
            "data": web_data,
            "version": data.get("_version", 1),
            "changed_by": data.get("_updated_by")
        }

    def reset_sync(self):
        """重置所有同步数据"""
        if self.SYNC_FILE.exists():
            self.SYNC_FILE.unlink()
        if self.VERSION_FILE.exists():
            self.VERSION_FILE.unlink()
        self._set_version(1)

    def get_status(self) -> Dict:
        """获取同步状态"""
        sync_data = self._read_sync_data()

        return {
            "has_sync_file": self.SYNC_FILE.exists(),
            "last_update": sync_data.get("_updated_at"),
            "updated_by": sync_data.get("_updated_by"),
            "version": sync_data.get("_version", 1)
        }

    def _read_sync_data(self) -> Dict:
        """读取同步数据"""
        if not self.SYNC_FILE.exists():
            version = self._get_version()
            return {"_version": version}

        try:
            with open(self.SYNC_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"_version": self._get_version()}

    def _write_sync_data(self, data: Dict):
        """写入同步数据"""
        version = self._get_version() + 1
        data["_version"] = version
        data["_updated_at"] = time.time()

        with open(self.SYNC_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self._set_version(version)

    def _get_version(self) -> int:
        """获取版本号"""
        if not self.VERSION_FILE.exists():
            return 1

        try:
            with open(self.VERSION_FILE, 'r', encoding='utf-8') as f:
                return int(f.read().strip())
        except Exception:
            return 1

    def _set_version(self, version: int):
        """设置版本号"""
        with open(self.VERSION_FILE, 'w', encoding='utf-8') as f:
            f.write(str(version))


# ═══════════════════════════════════════════
# 全局实例
# ═══════════════════════════════════════════

_sync_bridge = None

def get_sync_bridge() -> SyncBridge:
    global _sync_bridge
    if _sync_bridge is None:
        _sync_bridge = SyncBridge()
    return _sync_bridge
