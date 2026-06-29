"""
授权服务
软件授权验证、激活
"""

import os
import json
import time
import hashlib
from typing import Dict, Optional
from datetime import datetime


class LicenseService:
    """授权服务"""

    def __init__(self, license_dir: str = "config"):
        self.license_dir = license_dir
        self.license_file = os.path.join(license_dir, "license.json")

    def check_license(self) -> Dict:
        """检查授权状态"""
        if not os.path.exists(self.license_file):
            return {
                "valid": False,
                "type": "trial",
                "remaining_days": 0,
                "message": "未找到授权文件，请激活",
            }

        try:
            with open(self.license_file, "r", encoding="utf-8") as f:
                license_data = json.load(f)

            expired_at = license_data.get("expired_at")
            if expired_at:
                expired_date = datetime.fromisoformat(expired_at)
                now = datetime.now()

                if now > expired_date:
                    return {
                        "valid": False,
                        "type": license_data.get("type", "unknown"),
                        "expired_at": expired_at,
                        "message": "授权已过期",
                    }

                remaining = (expired_date - now).days
                return {
                    "valid": True,
                    "type": license_data.get("type", "unknown"),
                    "expired_at": expired_at,
                    "remaining_days": remaining,
                    "message": f"授权有效，剩余 {remaining} 天",
                }

            return {
                "valid": True,
                "type": license_data.get("type", "permanent"),
                "message": "永久授权",
            }

        except Exception as e:
            return {"valid": False, "message": f"授权文件损坏: {e}"}

    def activate_license(self, license_key: str) -> Dict:
        """激活授权"""
        # 验证授权密钥格式
        if not license_key or len(license_key) < 16:
            return {"success": False, "message": "无效的授权密钥"}

        try:
            # 解密并验证密钥
            license_info = self._parse_license_key(license_key)

            # 保存授权文件
            os.makedirs(self.license_dir, exist_ok=True)
            with open(self.license_file, "w", encoding="utf-8") as f:
                json.dump(license_info, f, ensure_ascii=False, indent=2)

            return {
                "success": True,
                "message": "激活成功",
                "type": license_info.get("type"),
                "expired_at": license_info.get("expired_at"),
            }

        except Exception as e:
            return {"success": False, "message": f"激活失败: {e}"}

    def _parse_license_key(self, key: str) -> Dict:
        """解析授权密钥"""
        # 简单的密钥验证逻辑
        # 实际应用中应使用RSA等非对称加密

        segments = key.split("-")
        if len(segments) >= 5:
            # 试算版: TRIAL-XXXXX-XXXXX-XXXXX-CREATED_AT-EXPIRED_AT
            # 商业版: PRO-XXXXX-XXXXX-XXXXX-EXPIRED_AT
            # 永久版: PRO-XXXXX-XXXXX-XXXXX-PERMANENT

            license_type = segments[0].upper()

            if license_type == "TRIAL":
                return {
                    "type": "trial",
                    "key_hash": hashlib.sha256(key.encode()).hexdigest(),
                    "activated_at": datetime.now().isoformat(),
                    "expired_at": segments[-1] if len(segments) >= 5 else None,
                }
            elif license_type == "PRO":
                if segments[-1] == "PERMANENT":
                    return {
                        "type": "permanent",
                        "key_hash": hashlib.sha256(key.encode()).hexdigest(),
                        "activated_at": datetime.now().isoformat(),
                    }
                else:
                    return {
                        "type": "professional",
                        "key_hash": hashlib.sha256(key.encode()).hexdigest(),
                        "activated_at": datetime.now().isoformat(),
                        "expired_at": segments[-1],
                    }

        # 回退
        return {
            "type": "trial",
            "key_hash": hashlib.sha256(key.encode()).hexdigest(),
            "activated_at": datetime.now().isoformat(),
            "expired_at": datetime.now().replace(year=datetime.now().year + 1).isoformat(),
        }

    def revoke_license(self) -> Dict:
        """撤销授权"""
        if os.path.exists(self.license_file):
            os.remove(self.license_file)
            return {"success": True, "message": "授权已撤销"}
        return {"success": False, "message": "授权文件不存在"}

    def get_license_info(self) -> Dict:
        """获取授权详情"""
        status = self.check_license()

        info = {
            "valid": status["valid"],
            "type": status.get("type", "unknown"),
            "message": status.get("message", ""),
        }

        if os.path.exists(self.license_file):
            try:
                with open(self.license_file, "r", encoding="utf-8") as f:
                    license_data = json.load(f)
                info.update({
                    "activated_at": license_data.get("activated_at"),
                    "expired_at": license_data.get("expired_at"),
                    "machine_code": license_data.get("machine_code"),
                })
            except Exception:
                pass

        return info

    def generate_machine_code(self) -> str:
        """生成机器码"""
        import platform
        import uuid

        info = f"{platform.node()}-{platform.processor()}-{uuid.getnode()}"
        return hashlib.sha256(info.encode()).hexdigest()[:16].upper()

