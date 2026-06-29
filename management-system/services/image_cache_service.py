"""
图片缓存服务
本地图片缓存管理
"""

import os
import json
import hashlib
import time
from typing import Dict, Optional, List
from datetime import datetime


class ImageCacheService:
    """图片缓存服务"""

    def __init__(self, cache_dir: str = "cache/images", max_size_mb: int = 100):
        self.cache_dir = cache_dir
        self.max_size_mb = max_size_mb
        self._index_file = os.path.join(cache_dir, "index.json")
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_key(self, source_url: str) -> str:
        """获取缓存键"""
        return hashlib.md5(source_url.encode()).hexdigest()

    def get_cached(self, source_url: str) -> Optional[str]:
        """获取缓存的图片路径"""
        cache_key = self._get_cache_key(source_url)
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.cache")

        if os.path.exists(cache_path):
            # 更新索引中的最后访问时间
            self._update_index(cache_key, "access", time.time())
            return cache_path

        return None

    def cache_image(self, source_url: str, image_data: bytes, extension: str = "png") -> str:
        """缓存图片"""
        cache_key = self._get_cache_key(source_url)
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.cache")

        with open(cache_path, "wb") as f:
            f.write(image_data)

        # 更新索引
        self._update_index(cache_key, "create", time.time(), {
            "source": source_url,
            "size": len(image_data),
            "extension": extension,
        })

        return cache_path

    def _update_index(self, cache_key: str, action: str, timestamp: float, metadata: Optional[Dict] = None):
        """更新索引"""
        index = self._load_index()

        if cache_key not in index:
            index[cache_key] = {
                "created_at": timestamp,
                "last_access": timestamp,
                "access_count": 0,
            }

        if action == "access":
            index[cache_key]["last_access"] = timestamp
            index[cache_key]["access_count"] += 1

        if metadata:
            index[cache_key].update(metadata)

        self._save_index(index)

    def _load_index(self) -> Dict:
        """加载索引"""
        if os.path.exists(self._index_file):
            try:
                with open(self._index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_index(self, index: Dict):
        """保存索引"""
        with open(self._index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def clear_cache(self, older_than_days: Optional[int] = None):
        """清除缓存"""
        index = self._load_index()
        now = time.time()

        keys_to_remove = []
        for key, info in index.items():
            if older_than_days:
                age_days = (now - info["last_access"]) / 86400
                if age_days > older_than_days:
                    keys_to_remove.append(key)
            else:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            cache_path = os.path.join(self.cache_dir, f"{key}.cache")
            if os.path.exists(cache_path):
                os.remove(cache_path)
            index.pop(key, None)

        self._save_index(index)

    def get_cache_size(self) -> Dict:
        """获取缓存大小"""
        total_size = 0
        file_count = 0

        for file in os.listdir(self.cache_dir):
            if file.endswith(".cache"):
                file_path = os.path.join(self.cache_dir, file)
                total_size += os.path.getsize(file_path)
                file_count += 1

        return {
            "file_count": file_count,
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "max_size_mb": self.max_size_mb,
            "usage_percent": round(total_size / (self.max_size_mb * 1024 * 1024) * 100, 1),
        }

    def optimize_cache(self):
        """优化缓存，删除超过大小限制的文件"""
        stats = self.get_cache_size()
        if stats["total_size"] < self.max_size_mb * 1024 * 1024:
            return

        # 按最后访问时间排序，删除最旧的
        index = self._load_index()
        sorted_keys = sorted(index.keys(), key=lambda k: index[k]["last_access"])

        while stats["total_size"] >= self.max_size_mb * 1024 * 1024 * 0.8:
            if not sorted_keys:
                break

            oldest_key = sorted_keys.pop(0)
            cache_path = os.path.join(self.cache_dir, f"{oldest_key}.cache")
            if os.path.exists(cache_path):
                os.remove(cache_path)
                index.pop(oldest_key, None)

            stats = self.get_cache_size()

        self._save_index(index)

