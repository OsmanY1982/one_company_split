# `planetarium/core/modules/supabase/updater.py`

> 路径：`planetarium/core/modules/supabase/updater.py` | 行数：66


---


```python
# -*- coding: utf-8 -*-
"""
Supabase 云端同步客户端 - APP 版本更新检查
"""
import json
from urllib.request import urlopen, Request
from ._core import SSL_CTX, SUPABASE_URL


class UpdateChecker:
    """从云端 Storage 检查 APP 更新（读 version.json）"""

    VERSION_URL = f"{SUPABASE_URL}/storage/v1/object/public/updates/version.json"

    @classmethod
    def get_latest(cls) -> dict:
        """
        获取最新版本信息
        返回: {latest_version, download_url, release_notes, released_at, file_size, file_hash, min_version} 或 None
        """
        try:
            req = Request(cls.VERSION_URL, method="GET")
            with urlopen(req, context=SSL_CTX, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                return data
        except Exception as e:
            print(f"[UpdateChecker] get_latest failed: {e}")
            return None

    @classmethod
    def compare_version(cls, current: str, latest: str) -> bool:
        """
        比较版本号，返回 True 表示有新版本
        支持格式: 1.0.0, 2.0.1, 2.1.0 等
        """
        def parse(v):
            parts = v.lstrip("vV").split(".")
            return tuple(int(p) for p in parts if p.isdigit())
        try:
            return parse(latest) > parse(current)
        except Exception:
            return False

    @classmethod
    def check_update(cls, current_version: str) -> dict:
        """
        检查更新，返回 {has_update, version, download_url, changelog}
        """
        data = cls.get_latest()
        if not data:
            return {"has_update": False}

        latest = data.get("latest_version", "")
        has_update = cls.compare_version(current_version, latest)

        # 选择下载链接：优先 Gitee（直链），备选百度网盘
        downloads = data.get("downloads", {})
        win = downloads.get("windows", {})
        download_url = win.get("gitee", "") or win.get("baidu", "")

        return {
            "has_update": has_update,
            "version": latest,
            "download_url": download_url,
            "changelog": data.get("release_notes", "")
        }

```
