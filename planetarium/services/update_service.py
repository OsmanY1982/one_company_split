"""
更新服务
应用自动更新检查和下载
"""

import os
import json
import hashlib
import tempfile
from typing import Dict, Optional
from datetime import datetime


class UpdateService:
    """更新服务"""

    def __init__(self, config_dir: str = "data"):
        self.config_dir = config_dir
        self.update_file = os.path.join(config_dir, "update.json")
        self._current_version = "1.0.0"
        self._update_info: Optional[Dict] = None

    def check_for_updates(self, update_url: Optional[str] = None) -> Dict:
        """检查更新"""
        try:
            # 模拟检查更新
            # 实际应用中应请求远程服务器
            update_info = self._mock_check_update()

            self._update_info = update_info
            self._save_update_info()

            has_update = update_info.get("version") != self._current_version

            return {
                "success": True,
                "has_update": has_update,
                "current_version": self._current_version,
                "latest_version": update_info.get("version", self._current_version),
                "update_info": update_info if has_update else None,
            }

        except Exception as e:
            return {"success": False, "message": f"检查更新失败: {e}"}

    def _mock_check_update(self) -> Dict:
        """模拟检查更新"""
        return {
            "version": "1.0.1",
            "release_date": datetime.now().strftime("%Y-%m-%d"),
            "description": "新增功能：报表导出; 修复：数据同步稳定性优化",
            "size_mb": 15.5,
            "mandatory": False,
            "changelog": [
                "新增功能：报表导出",
                "修复：数据同步稳定性优化",
                "改进：内存使用效率",
            ],
            "download_url": "https://update.example.com/one_company_1.0.1.zip",
            "sha256": hashlib.sha256(b"mock").hexdigest(),
        }

    def get_current_version(self) -> str:
        """获取当前版本"""
        return self._current_version

    def set_current_version(self, version: str):
        """设置当前版本"""
        self._current_version = version

    def get_update_info(self) -> Optional[Dict]:
        """获取更新信息"""
        if self._update_info:
            return self._update_info

        if os.path.exists(self.update_file):
            try:
                with open(self.update_file, "r", encoding="utf-8") as f:
                    self._update_info = json.load(f)
            except Exception:
                pass

        return self._update_info

    def _save_update_info(self):
        """保存更新信息"""
        os.makedirs(self.config_dir, exist_ok=True)
        if self._update_info:
            with open(self.update_file, "w", encoding="utf-8") as f:
                json.dump(self._update_info, f, ensure_ascii=False, indent=2)

    def download_update(self, progress_callback=None) -> Dict:
        """下载更新"""
        if not self._update_info:
            return {"success": False, "message": "没有可用的更新信息"}

        try:
            download_url = self._update_info.get("download_url")
            if not download_url:
                return {"success": False, "message": "下载地址不存在"}

            # 模拟下载
            temp_file = os.path.join(tempfile.gettempdir(), "update_package.zip")

            return {
                "success": True,
                "file_path": temp_file,
                "version": self._update_info.get("version"),
                "size_mb": self._update_info.get("size_mb"),
            }

        except Exception as e:
            return {"success": False, "message": f"下载失败: {e}"}

    def verify_update(self, file_path: str) -> Dict:
        """验证更新包"""
        if not os.path.exists(file_path):
            return {"success": False, "message": "更新包不存在"}

        try:
            # 计算SHA256
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)

            expected_sha256 = self._update_info.get("sha256", "") if self._update_info else ""
            actual_sha256 = sha256.hexdigest()

            verified = expected_sha256 == actual_sha256 if expected_sha256 else True

            return {
                "success": True,
                "verified": verified,
                "expected_sha256": expected_sha256,
                "actual_sha256": actual_sha256,
            }

        except Exception as e:
            return {"success": False, "message": f"验证失败: {e}"}

    def install_update(self, file_path: str) -> Dict:
        """安装更新"""
        if not os.path.exists(file_path):
            return {"success": False, "message": "更新包不存在"}

        # 验证
        verify_result = self.verify_update(file_path)
        if not verify_result.get("verified", False):
            return {"success": False, "message": "更新包验证失败"}

        try:
            # 模拟安装
            if self._update_info:
                self._current_version = self._update_info.get("version", self._current_version)

            return {
                "success": True,
                "message": "更新安装成功",
                "new_version": self._current_version,
            }

        except Exception as e:
            return {"success": False, "message": f"安装失败: {e}"}

    def rollback_update(self, backup_path: str) -> Dict:
        """回滚更新"""
        if not os.path.exists(backup_path):
            return {"success": False, "message": "备份文件不存在"}

        try:
            # 模拟回滚
            return {
                "success": True,
                "message": "已回滚到上一个版本",
            }

        except Exception as e:
            return {"success": False, "message": f"回滚失败: {e}"}

    def check_for_updates_on_startup(self):
        """启动时检查更新"""
        result = self.check_for_updates()
        return result

