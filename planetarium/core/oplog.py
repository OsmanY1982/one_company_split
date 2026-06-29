# -*- coding: utf-8 -*-
"""
操作日志管理
记录用户关键操作，支持日志轮转和清理
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from core.paths import LOG_DIR


class OpLog:
    """操作日志管理"""
    
    MAX_SIZE_MB = 5
    MAX_AGE_DAYS = 30
    
    def __init__(self, log_dir: str = None):
        self.log_dir = log_dir or LOG_DIR
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self._log_file = os.path.join(self.log_dir, "operation_log.jsonl")
    
    def log(self, action: str, module: str = "", user: str = "", 
            details: Dict[str, Any] = None, success: bool = True):
        """记录一条操作日志"""
        entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "module": module,
            "user": user or "system",
            "success": success,
            "details": details or {}
        }
        try:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self._check_rotate()
        except Exception as e:
            print(f"[OpLog] 写入失败: {e}")
    
    def _check_rotate(self):
        """检查是否需要轮转"""
        if not os.path.exists(self._log_file):
            return
        size_mb = os.path.getsize(self._log_file) / (1024 * 1024)
        if size_mb > self.MAX_SIZE_MB:
            self._rotate()
        if not self._is_fresh():
            self._rotate()
    
    def _rotate(self):
        """轮转日志"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive = self._log_file.replace(".jsonl", f"_{ts}.jsonl")
        os.rename(self._log_file, archive)
        self._cleanup_old()
    
    def _cleanup_old(self):
        """清理旧日志"""
        cutoff = datetime.now() - timedelta(days=self.MAX_AGE_DAYS)
        for fname in os.listdir(self.log_dir):
            if fname.startswith("operation_log_") and fname.endswith(".jsonl"):
                fpath = os.path.join(self.log_dir, fname)
                mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                if mtime < cutoff:
                    os.remove(fpath)
    
    def _is_fresh(self) -> bool:
        """检查日志是否还新鲜（不超过最大天数）"""
        mtime = datetime.fromtimestamp(os.path.getmtime(self._log_file))
        return (datetime.now() - mtime).days < self.MAX_AGE_DAYS
    
    def query(self, limit: int = 100, module: str = "", action: str = "",
              user: str = "") -> List[Dict]:
        """查询日志"""
        if not os.path.exists(self._log_file):
            return []
        results = []
        with open(self._log_file, "r", encoding="utf-8") as f:
            for line in f:
                if len(results) >= limit:
                    break
                try:
                    entry = json.loads(line.strip())
                    if module and entry.get("module") != module:
                        continue
                    if action and entry.get("action") != action:
                        continue
                    if user and entry.get("user") != user:
                        continue
                    results.append(entry)
                except Exception:
                    continue
        return results


_oplog: Optional[OpLog] = None


def get_oplog() -> OpLog:
    global _oplog
    if _oplog is None:
        _oplog = OpLog()
    return _oplog
