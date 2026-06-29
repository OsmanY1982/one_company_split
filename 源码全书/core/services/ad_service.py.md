# `core/services/ad_service.py`

> 路径：`core/services/ad_service.py` | 行数：205


---


```python
"""广告服务
管理激励广告观看、验证、时长延期
"""
from __future__ import annotations

from __future__ import annotations

import os
import json
import time
import hashlib
import hmac
from datetime import datetime, date
from typing import Dict

# 工作目录下的广告数据目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ads")
AD_RECORDS_FILE = os.path.join(DATA_DIR, "ad_records.json")
SECRET_KEY = "one_company_ad_2026"  # 生产环境应替换为更复杂的密钥

# 配置
MAX_WATCHES_PER_DAY = 5          # 每天最多看广告次数
REWARD_SECONDS = 3600            # 每次看广告延长 1 小时
MIN_WATCH_RATIO = 0.85           # 至少看完 85% 才算有效观看


class AdService:
    """广告服务"""

    def __init__(self, user_id: str = "default") -> None:
        self.user_id = user_id
        os.makedirs(DATA_DIR, exist_ok=True)

    def _load_records(self) -> Dict:
        if os.path.exists(AD_RECORDS_FILE):
            try:
                with open(AD_RECORDS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_records(self, records: Dict) -> None:
        with open(AD_RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    def can_watch_ad(self) -> Dict:
        """检查用户是否可以看广告"""
        records = self._load_records()
        user_records = records.get(self.user_id, {})
        today = date.today().isoformat()

        today_watches = [r for r in user_records.get("history", [])
                         if r["date"] == today and r.get("rewarded", False)]

        if len(today_watches) >= MAX_WATCHES_PER_DAY:
            return {
                "can_watch": False,
                "message": f"今日已观看 {len(today_watches)}/{MAX_WATCHES_PER_DAY} 次广告，明天再来吧",
                "remaining": 0,
            }

        return {
            "can_watch": True,
            "message": f"观看完整广告可延长 {REWARD_SECONDS // 3600} 小时使用时间",
            "remaining": MAX_WATCHES_PER_DAY - len(today_watches),
        }

    def verify_watch(self, ad_id: str, watch_duration: float,
                     ad_duration: float, checksum: str) -> Dict:
        """
        验证广告观看是否有效，有效则延长授权时间

        Args:
            ad_id: 广告标识
            watch_duration: 实际观看秒数
            ad_duration: 广告总时长秒数
            checksum: 客户端提交的校验码
        """
        # 1. 校验 checksum（防止客户端伪造）
        expected = self._make_checksum(ad_id, watch_duration, ad_duration)
        if checksum != expected:
            return {
                "success": False,
                "message": "验证失败，请勿作弊",
                "rewarded": False,
            }

        # 2. 校验观看时长
        if ad_duration <= 0:
            return {"success": False, "message": "广告时长异常", "rewarded": False}

        ratio = watch_duration / ad_duration
        if ratio < MIN_WATCH_RATIO:
            return {
                "success": False,
                "message": f"观看时长不足（{ratio:.0%}），需要至少{MIN_WATCH_RATIO:.0%}",
                "rewarded": False,
            }

        # 3. 检查今日次数
        status = self.can_watch_ad()
        if not status["can_watch"]:
            return {
                "success": False,
                "message": status["message"],
                "rewarded": False,
            }

        # 4. 记录观看
        records = self._load_records()
        user_records = records.setdefault(self.user_id, {})

        watch_record = {
            "ad_id": ad_id,
            "date": date.today().isoformat(),
            "timestamp": datetime.now().isoformat(),
            "watch_duration": watch_duration,
            "ad_duration": ad_duration,
            "rewarded": True,
        }

        history = user_records.setdefault("history", [])
        history.append(watch_record)

        # 累计延长秒数
        total_extend = user_records.get("total_extend_seconds", 0)
        total_extend += REWARD_SECONDS
        user_records["total_extend_seconds"] = total_extend

        self._save_records(records)

        # 5. 延长授权
        extend_result = self._extend_license(REWARD_SECONDS)

        return {
            "success": True,
            "message": f"观看完成！已延长 {REWARD_SECONDS // 3600} 小时使用时间",
            "rewarded": True,
            "extend_seconds": REWARD_SECONDS,
            "total_extend_seconds": total_extend,
            "new_expire": extend_result.get("new_expire", ""),
            "today_remaining": MAX_WATCHES_PER_DAY - self._today_watch_count(records),
        }

    def _extend_license(self, seconds: int) -> Dict:
        """延长授权文件过期时间"""
        license_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config", "license.json"
        )

        try:
            if os.path.exists(license_file):
                with open(license_file, "r", encoding="utf-8") as f:
                    lic = json.load(f)

                expired_at = lic.get("expired_at")
                if expired_at:
                    expire_dt = datetime.fromisoformat(expired_at)
                    new_expire = expire_dt.timestamp() + seconds
                    lic["expired_at"] = datetime.fromtimestamp(new_expire).isoformat()

                    with open(license_file, "w", encoding="utf-8") as f:
                        json.dump(lic, f, ensure_ascii=False, indent=2)

                    return {"new_expire": lic["expired_at"]}
        except Exception:
            pass

        return {}

    def _today_watch_count(self, records: Dict) -> int:
        today = date.today().isoformat()
        user_records = records.get(self.user_id, {})
        return sum(1 for r in user_records.get("history", [])
                   if r["date"] == today and r.get("rewarded", False))

    def _make_checksum(self, ad_id: str, watch_duration: float,
                       ad_duration: float) -> str:
        """生成校验码"""
        raw = f"{ad_id}|{watch_duration:.2f}|{ad_duration:.2f}|{SECRET_KEY}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get_stats(self) -> Dict:
        """获取观看统计"""
        records = self._load_records()
        user_records = records.get(self.user_id, {})
        history = user_records.get("history", [])
        today = date.today().isoformat()

        today_count = sum(1 for r in history if r["date"] == today and r.get("rewarded"))
        total_count = sum(1 for r in history if r.get("rewarded"))
        total_seconds = user_records.get("total_extend_seconds", 0)

        return {
            "today_watches": today_count,
            "today_remaining": MAX_WATCHES_PER_DAY - today_count,
            "total_watches": total_count,
            "total_extend_hours": total_seconds / 3600,
        }


def get_ad_service(user_id: str = "default") -> AdService:
    return AdService(user_id)

```
