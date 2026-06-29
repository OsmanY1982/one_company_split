"""
导入导出服务
批量导入导出数据
"""

import os
import json
import csv
import sqlite3
from typing import Dict, List, Optional, Callable
from datetime import datetime


class ImportExportService:
    """导入导出服务"""

    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path

    def import_csv(self,
                   file_path: str,
                   table_name: str,
                   mapping: Optional[Dict[str, str]] = None,
                   skip_header: bool = True,
                   progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict:
        """从CSV导入"""
        if not os.path.exists(file_path):
            return {"success": False, "message": "文件不存在"}

        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            if not rows:
                return {"success": False, "message": "CSV无数据"}

            total = len(rows)
            success_count = 0
            error_count = 0
            errors = []

            with sqlite3.connect(self.db_path) as conn:
                for i, row in enumerate(rows):
                    try:
                        # 字段映射
                        if mapping:
                            mapped_row = {}
                            for target_field, source_field in mapping.items():
                                if source_field in row:
                                    mapped_row[target_field] = row[source_field]
                            row = mapped_row

                        # 构建INSERT语句
                        columns = list(row.keys())
                        placeholders = ["?" for _ in columns]
                        values = [row.get(col, "") for col in columns]

                        conn.execute(
                            f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})",
                            values,
                        )
                        success_count += 1

                    except Exception as e:
                        error_count += 1
                        errors.append({"row": i + 1, "error": str(e)})

                    if progress_callback:
                        progress_callback(i + 1, total)

                conn.commit()

            return {
                "success": True,
                "total": total,
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors[:10],
            }

        except Exception as e:
            return {"success": False, "message": f"导入失败: {e}"}

    def import_json(self,
                    file_path: str,
                    table_name: str,
                    progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict:
        """从JSON导入"""
        if not os.path.exists(file_path):
            return {"success": False, "message": "文件不存在"}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                data = [data] if isinstance(data, dict) else []

            total = len(data)
            success_count = 0
            error_count = 0

            with sqlite3.connect(self.db_path) as conn:
                for i, item in enumerate(data):
                    try:
                        columns = list(item.keys())
                        placeholders = ["?" for _ in columns]
                        values = list(item.values())

                        conn.execute(
                            f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})",
                            values,
                        )
                        success_count += 1

                    except Exception:
                        error_count += 1

                    if progress_callback:
                        progress_callback(i + 1, total)

                conn.commit()

            return {
                "success": True,
                "total": total,
                "success_count": success_count,
                "error_count": error_count,
            }

        except Exception as e:
            return {"success": False, "message": f"导入失败: {e}"}

    def export_data(self,
                    table_name: str,
                    format: str = "csv",
                    output_path: Optional[str] = None,
                    where: Optional[str] = None,
                    params: Optional[List] = None) -> Dict:
        """导出数据"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"exports/{table_name}_{timestamp}.{format}"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                query = f"SELECT * FROM {table_name}"
                if where:
                    query += f" WHERE {where}"

                cursor = conn.execute(query, params or [])
                rows = [dict(row) for row in cursor.fetchall()]

            if format == "csv":
                if rows:
                    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
                        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                        writer.writeheader()
                        writer.writerows(rows)

            elif format == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(rows, f, ensure_ascii=False, indent=2)

            return {
                "success": True,
                "file_path": output_path,
                "row_count": len(rows),
            }

        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_table_schema(self, table_name: str) -> Dict:
        """获取表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                columns = [
                    {"name": row[1], "type": row[2], "nullable": not row[3], "primary_key": bool(row[5])}
                    for row in cursor.fetchall()
                ]

            return {"success": True, "table": table_name, "columns": columns}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def validate_import(self,
                        file_path: str,
                        table_name: str) -> Dict:
        """验证导入文件"""
        if not os.path.exists(file_path):
            return {"success": False, "message": "文件不存在"}

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".csv":
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                rows = list(reader)
        elif ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                rows = data if isinstance(data, list) else ([data] if isinstance(data, dict) else [])
                headers = list(rows[0].keys()) if rows else []
        else:
            return {"success": False, "message": "不支持的文件格式"}

        # 获取表结构
        schema = self.get_table_schema(table_name)
        table_columns = [col["name"] for col in schema.get("columns", [])]

        # 检查匹配的列
        matching_columns = [h for h in headers if h in table_columns]
        extra_columns = [h for h in headers if h not in table_columns]
        missing_columns = [c for c in table_columns if c not in headers]

        return {
            "success": True,
            "file_columns": headers,
            "table_columns": table_columns,
            "matching_columns": matching_columns,
            "extra_columns": extra_columns,
            "missing_columns": missing_columns,
            "row_count": len(rows),
            "match_rate": round(len(matching_columns) / len(table_columns) * 100, 1) if table_columns else 0,
        }

