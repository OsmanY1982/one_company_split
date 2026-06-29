"""
缓存服务
基于内存和SQLite的轻量级缓存
"""

import json
import sqlite3
import time
import threading
from typing import Any, Dict, Optional
from functools import wraps


class CacheService:
    """缓存服务"""

    def __init__(self, db_path: str = "data/cache.db", max_memory_items: int = 1000):
        self.db_path = db_path
        self.max_memory_items = max_memory_items
        self._memory_cache: Dict[str, "_CacheEntry"] = {}
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL,
                    created_at REAL DEFAULT (julianday('now'))
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)")
            conn.commit()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        # 先查内存缓存
        with self._lock:
            entry = self._memory_cache.get(key)
            if entry and not entry.is_expired():
                return entry.value

        # 查数据库缓存
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT value, expires_at FROM cache WHERE key = ?",
                    (key,)
                )
                row = cursor.fetchone()
                if row:
                    value_str, expires_at = row
                    if expires_at is None or expires_at > time.time():
                        value = json.loads(value_str)
                        # 回填内存缓存
                        with self._lock:
                            self._memory_cache[key] = _CacheEntry(value, expires_at)
                        return value
                    else:
                        # 清除过期缓存
                        conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                        conn.commit()
        except Exception:
            pass

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        expires_at = (time.time() + ttl) if ttl else None

        # 更新内存缓存
        with self._lock:
            self._memory_cache[key] = _CacheEntry(value, expires_at)

            # 内存缓存淘汰
            if len(self._memory_cache) > self.max_memory_items:
                oldest_key = min(self._memory_cache, key=lambda k: self._memory_cache[k].created_at)
                del self._memory_cache[oldest_key]

        # 持久化到数据库
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                    (key, json.dumps(value), expires_at)
                )
                conn.commit()
        except Exception:
            pass

    def delete(self, key: str):
        """删除缓存"""
        with self._lock:
            self._memory_cache.pop(key, None)

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
        except Exception:
            pass

    def clear(self):
        """清除所有缓存"""
        with self._lock:
            self._memory_cache.clear()

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache")
                conn.commit()
        except Exception:
            pass

    def cleanup_expired(self):
        """清理过期缓存"""
        now = time.time()

        with self._lock:
            expired_keys = [k for k, v in self._memory_cache.items() if v.is_expired()]
            for k in expired_keys:
                del self._memory_cache[k]

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?", (now,))
                conn.commit()
        except Exception:
            pass

    def cached(self, ttl: Optional[int] = None):
        """缓存装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
                result = self.get(cache_key)
                if result is not None:
                    return result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result
            return wrapper
        return decorator


class _CacheEntry:
    """缓存条目"""

    def __init__(self, value: Any, expires_at: Optional[float] = None):
        self.value = value
        self.expires_at = expires_at
        self.created_at = time.time()

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


# 全局实例
cache_service = CacheService()

