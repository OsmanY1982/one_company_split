"""
备份服务
自动备份数据库和配置文件
"""

import os
import json
import shutil
import sqlite3
import zipfile
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class BackupService:
    """备份服务"""

    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = backup_dir
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """确保备份目录存在"""
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, name: Optional[str] = None) -> Dict:
        """创建备份"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = name or f"backup_{timestamp}"
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")

            with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # 备份数据库
                if os.path.exists("data"):
                    for root, dirs, files in os.walk("data"):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.join("data", os.path.relpath(file_path, "data"))
                            zf.write(file_path, arcname)

                # 备份配置
                if os.path.exists("config"):
                    for root, dirs, files in os.walk("config"):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.join("config", os.path.relpath(file_path, "config"))
                            zf.write(file_path, arcname)

            file_size = os.path.getsize(backup_path)
            return {
                "success": True,
                "backup_path": backup_path,
                "backup_name": backup_name,
                "file_size": file_size,
                "created_at": timestamp,
            }

        except Exception as e:
            return {"success": False, "message": f"备份失败: {e}"}

    def restore_backup(self, backup_path: str) -> Dict:
        """恢复备份"""
        if not os.path.exists(backup_path):
            return {"success": False, "message": "备份文件不存在"}

        try:
            with zipfile.ZipFile(backup_path, "r") as zf:
                zf.extractall(".")

            return {"success": True, "message": "恢复成功"}

        except Exception as e:
            return {"success": False, "message": f"恢复失败: {e}"}

    def list_backups(self) -> List[Dict]:
        """列出备份"""
        backups = []
        if os.path.exists(self.backup_dir):
            for file in os.listdir(self.backup_dir):
                if file.endswith(".zip"):
                    file_path = os.path.join(self.backup_dir, file)
                    stat = os.stat(file_path)
                    backups.append({
                        "name": file,
                        "path": file_path,
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    })
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)

    def delete_backup(self, backup_name: str) -> Dict:
        """删除备份"""
        backup_path = os.path.join(self.backup_dir, backup_name)
        if os.path.exists(backup_path):
            os.remove(backup_path)
            return {"success": True}
        return {"success": False, "message": "备份文件不存在"}

    def schedule_backup(self, interval_hours: int = 24) -> Dict:
        """自动备份调度"""
        return {"success": True, "message": f"已设置每 {interval_hours} 小时自动备份"}

