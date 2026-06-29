"""
备份工具
数据库备份、导出、恢复
"""

import os
import json
import shutil
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime


class BackupTool:
    """备份工具"""

    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path

    def export_database(self, output_path: Optional[str] = None) -> Dict:
        """导出数据库为SQL"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"exports/db_export_{timestamp}.sql"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            with sqlite3.connect(self.db_path) as conn:
                with open(output_path, "w", encoding="utf-8") as f:
                    for line in conn.iterdump():
                        f.write(f"{line}\n")

            return {
                "success": True,
                "file_path": output_path,
                "file_size": os.path.getsize(output_path),
            }
        except Exception as e:
            return {"success": False, "message": f"导出失败: {e}"}

    def import_database(self, sql_path: str) -> Dict:
        """从SQL导入数据库"""
        if not os.path.exists(sql_path):
            return {"success": False, "message": "SQL文件不存在"}

        try:
            with sqlite3.connect(self.db_path) as conn:
                with open(sql_path, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())

            return {"success": True, "message": "导入成功"}
        except Exception as e:
            return {"success": False, "message": f"导入失败: {e}"}

    def export_table(self, table_name: str, output_path: Optional[str] = None) -> Dict:
        """导出单个表为CSV"""
        import csv

        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"exports/{table_name}_{timestamp}.csv"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()

                if rows:
                    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
                        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                        writer.writeheader()
                        writer.writerows([dict(row) for row in rows])

            return {
                "success": True,
                "file_path": output_path,
                "row_count": len(rows),
            }
        except Exception as e:
            return {"success": False, "message": f"导出失败: {e}"}

    def get_backup_stats(self) -> Dict:
        """获取备份统计"""
        stats = {
            "backups": [],
            "total_size": 0,
            "count": 0,
        }

        backup_dir = "backups"
        if os.path.exists(backup_dir):
            for file in os.listdir(backup_dir):
                file_path = os.path.join(backup_dir, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    stats["backups"].append({
                        "name": file,
                        "size": size,
                        "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    })
                    stats["total_size"] += size
            stats["count"] = len(stats["backups"])

        return stats

