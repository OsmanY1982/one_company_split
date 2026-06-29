# `core/modules/intelligence/data_import_tools.py`

> 路径：`core/modules/intelligence/data_import_tools.py` | 行数：222


---


```python
"""
Iqra 数据导入工具 — 从CSV/JSON导入数据到数据库

已有模块只能导出，此文件补充导入能力。
"""

import os, csv, json
from core.database import get_conn, close_conn
from datetime import datetime


def import_csv_to_db(data_dir: str, csv_path: str, db_name: str, table: str, mode: str = "append") -> dict:
    """
    导入CSV文件到数据库表
    mode: append(追加) / replace(清空后写入)
    """
    if not os.path.exists(csv_path):
        return {"message": f"CSV文件不存在: {csv_path}", "data": {}}

    db_path = os.path.join(data_dir, db_name)
    if not os.path.exists(db_path):
        return {"message": f"数据库不存在: {db_name}", "data": {}}

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if not rows:
            return {"message": "CSV无数据行", "data": {}}
        columns = list(rows[0].keys())

    registry = db_name.replace(".db", "")
    db = get_conn(registry)
    try:
        if mode == "replace":
            db.execute(f"DELETE FROM {table}")

        # 动态构建INSERT
        cols_str = ",".join(columns)
        placeholders = ",".join(["?"] * len(columns))
        insert_sql = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"

        inserted = 0
        errors = 0
        for row in rows:
            try:
                values = [row.get(c, "") for c in columns]
                db.execute(insert_sql, values)
                inserted += 1
            except Exception:
                errors += 1

        db.commit()
        return {"message": f"导入完成: 成功{inserted}条, 失败{errors}条", "data": {
            "csv": csv_path, "db": db_name, "table": table,
            "inserted": inserted, "errors": errors, "mode": mode
        }}
    except Exception as e:
        return {"message": f"导入失败: {e}", "data": {}}
    finally:
        close_conn(registry)


def import_json_to_db(data_dir: str, json_path: str, db_name: str, table: str, mode: str = "append") -> dict:
    """导入JSON文件到数据库表"""
    if not os.path.exists(json_path):
        return {"message": f"JSON文件不存在: {json_path}", "data": {}}

    db_path = os.path.join(data_dir, db_name)
    if not os.path.exists(db_path):
        return {"message": f"数据库不存在: {db_name}", "data": {}}

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = data if isinstance(data, list) else [data]
    if not rows:
        return {"message": "JSON无数据", "data": {}}
    columns = list(rows[0].keys())

    registry = db_name.replace(".db", "")
    db = get_conn(registry)
    try:
        if mode == "replace":
            db.execute(f"DELETE FROM {table}")

        cols_str = ",".join(columns)
        placeholders = ",".join(["?"] * len(columns))
        insert_sql = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"

        inserted, errors = 0, 0
        for row in rows:
            try:
                values = [row.get(c, "") for c in columns]
                db.execute(insert_sql, values)
                inserted += 1
            except Exception:
                errors += 1

        db.commit()
        return {"message": f"导入完成: 成功{inserted}条, 失败{errors}条", "data": {
            "json": json_path, "db": db_name, "table": table,
            "inserted": inserted, "errors": errors
        }}
    except Exception as e:
        return {"message": f"导入失败: {e}", "data": {}}
    finally:
        close_conn(registry)


def validate_db_integrity(data_dir: str, db_name: str) -> dict:
    """校验数据库完整性"""
    db_path = os.path.join(data_dir, db_name)
    if not os.path.exists(db_path):
        return {"message": f"数据库不存在: {db_name}", "data": {}}

    registry = db_name.replace(".db", "")
    db = get_conn(registry)
    try:
        # 获取所有表
        tables = [r["name"] for r in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()]

        results = {}
        for t in tables:
            count = db.execute(f"SELECT COUNT(*) as c FROM {t}").fetchone()["c"]
            integrity = db.execute(f"PRAGMA integrity_check").fetchone()["integrity_check"]
            results[t] = {"行数": count, "完整性": integrity}

        # 整体完整性
        overall = db.execute("PRAGMA integrity_check").fetchone()["integrity_check"]
        return {"message": f"校验完成: {overall}, {len(tables)}个表", "data": results}
    finally:
        close_conn(registry)


def clean_duplicate_records(data_dir: str, db_name: str, table: str, unique_fields: str) -> dict:
    """
    清理重复记录
    unique_fields: 用于判断重复的字段列表，逗号分隔，如 "name,email"
    """
    db_path = os.path.join(data_dir, db_name)
    if not os.path.exists(db_path):
        return {"message": f"数据库不存在: {db_name}", "data": {}}

    registry = db_name.replace(".db", "")
    db = get_conn(registry)
    try:
        fields = [f.strip() for f in unique_fields.split(",")]
        where_clause = " AND " + " AND ".join([f"a.{f}=b.{f}" for f in fields])

        # 找重复数量
        dup_count = db.execute(
            f"SELECT COUNT(*) FROM {table} a INNER JOIN {table} b ON a.rowid<b.rowid {where_clause}"
        ).fetchone()[0]

        if dup_count == 0:
            return {"message": "无重复记录", "data": {"duplicates": 0}}

        # 删除重复（保留rowid最小的）
        db.execute(
            f"DELETE FROM {table} WHERE rowid IN "
            f"(SELECT b.rowid FROM {table} a INNER JOIN {table} b ON a.rowid<b.rowid {where_clause})"
        )
        db.commit()

        remaining = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return {"message": f"清理完成: 删除{dup_count}条重复, 剩余{remaining}条", "data": {
            "deleted": dup_count, "remaining": remaining
        }}
    except Exception as e:
        return {"message": f"清理失败: {e}", "data": {}}
    finally:
        close_conn(registry)


def register_data_import_tools(registry, data_dir: str):
    from core.modules.intelligence.tool_registry import ToolDefinition

    registry.add_tool(ToolDefinition(
        name="import_csv",
        description="导入CSV文件到数据库（append追加/replace替换）",
        parameters={"type": "object", "properties": {
            "csv_path": {"type": "string", "description": "CSV文件路径"},
            "db_name": {"type": "string", "description": "目标数据库文件名"},
            "table": {"type": "string", "description": "目标表名"},
            "mode": {"type": "string", "description": "append或replace"}
        }},
        handler=lambda csv_path="", db_name="", table="", mode="append": import_csv_to_db(data_dir, csv_path, db_name, table, mode),
    ))

    registry.add_tool(ToolDefinition(
        name="import_json",
        description="导入JSON文件到数据库",
        parameters={"type": "object", "properties": {
            "json_path": {"type": "string", "description": "JSON文件路径"},
            "db_name": {"type": "string", "description": "目标数据库文件名"},
            "table": {"type": "string", "description": "目标表名"},
            "mode": {"type": "string", "description": "append或replace"}
        }},
        handler=lambda json_path="", db_name="", table="", mode="append": import_json_to_db(data_dir, json_path, db_name, table, mode),
    ))

    registry.add_tool(ToolDefinition(
        name="validate_db",
        description="校验数据库完整性：行数统计+完整性检查",
        parameters={"type": "object", "properties": {
            "db_name": {"type": "string", "description": "数据库文件名"}
        }},
        handler=lambda db_name="": validate_db_integrity(data_dir, db_name),
    ))

    registry.add_tool(ToolDefinition(
        name="clean_duplicates",
        description="清理数据库表中的重复记录",
        parameters={"type": "object", "properties": {
            "db_name": {"type": "string", "description": "数据库文件名"},
            "table": {"type": "string", "description": "表名"},
            "unique_fields": {"type": "string", "description": "判断重复的字段，逗号分隔，如name,email"}
        }},
        handler=lambda db_name="", table="", unique_fields="": clean_duplicate_records(data_dir, db_name, table, unique_fields),
    ))
```
