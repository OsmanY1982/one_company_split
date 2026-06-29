# -*- coding: utf-8 -*-
from __future__ import annotations
"""
统一数据库连接管理器
所有 service 层统一通过此处获取 SQLite 连接，替代分散的 sqlite3.connect()
"""

import os
import sqlite3
import threading
from contextlib import contextmanager
from core.paths import DATA_DIR


# ──────────── 连接注册表 ────────────
_connections: dict[str, sqlite3.Connection] = {}
_lock = threading.Lock()


def get_conn(db_name: str) -> sqlite3.Connection:
    """
    获取数据库连接（线程本地，自动复用）
    :param db_name: 数据库文件名（如 'wallet.db'），会自动拼接 DATA_DIR
    """
    tid = threading.get_ident()
    key = f"{tid}:{db_name}"

    with _lock:
        if key in _connections:
            try:
                _connections[key].execute("SELECT 1")
            except sqlite3.ProgrammingError:
                del _connections[key]

    if key not in _connections:
        db_path = os.path.join(DATA_DIR, db_name)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        with _lock:
            _connections[key] = conn

    return _connections[key]


def close_conn(db_name: str) -> None:
    """关闭当前线程的某个数据库连接"""
    tid = threading.get_ident()
    key = f"{tid}:{db_name}"
    with _lock:
        if key in _connections:
            try:
                _connections[key].close()
            except Exception:
                pass
            del _connections[key]


def close_all() -> None:
    """关闭所有连接（程序退出时调用）"""
    with _lock:
        for key, conn in list(_connections.items()):
            try:
                conn.close()
            except Exception:
                pass
        _connections.clear()


# ──────────── 数据库注册中心 ────────────
# 注册所有业务数据库，提供标准化查询接口

# 核心数据库映射：模块名 → 数据库文件
DB_REGISTRY = {
    "wallet":       "wallet.db",
    "finance":      "finance.db",
    "customer":     "customer.db",
    "distribution": "distribution.db",
    "order":        "order.db",
    "product":      "product.db",
    "member":       "member.db",
    "staff":        "staff.db",
    "users":        "users.db",
    "admin":        "admin.db",
    "activation":   "activation.db",
    "activation_admin": "activation_admin.db",
    "activation_log":   "activation_log.db",
    "license":      "license.db",
    "system_logs":  "system_logs.db",
    "operation_log": "operation_log.db",
    "scheduler":    "scheduler.db",
    "sync_queue":   "sync_queue.db",
    "sessions":     "sessions.db",
    "todos":        "todos.db",
    "memory":       "memory.db",
}


def get_db_path(module: str) -> str:
    """获取模块对应的完整数据库路径"""
    db_file = DB_REGISTRY.get(module, f"{module}.db")
    return os.path.join(DATA_DIR, db_file)


def list_databases() -> dict[str, dict]:
    """列出所有数据库及其状态"""
    result = {}
    for name, db_file in DB_REGISTRY.items():
        path = os.path.join(DATA_DIR, db_file)
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        result[name] = {
            "file": db_file,
            "exists": exists,
            "size_kb": size // 1024,
        }
    return result


def ensure_tables(db_name: str, ddl_list: list[str]) -> None:
    """
    确保数据库中存在指定的表（幂等）
    :param db_name: 数据库文件名
    :param ddl_list: CREATE TABLE IF NOT EXISTS 语句列表
    """
    conn = get_conn(db_name)
    for ddl in ddl_list:
        conn.execute(ddl)
    conn.commit()


# ──────────── 辅助函数 ────────────


def query_scalar(db_name: str, sql: str, params: tuple = (), default=0):
    """执行查询，返回单个标量值"""
    try:
        conn = get_conn(db_name)
        r = conn.execute(sql, params).fetchone()
        return r[0] if r and r[0] is not None else default
    except sqlite3.OperationalError:
        return default


def query_rows(db_name: str, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    """执行查询，返回全部行"""
    try:
        conn = get_conn(db_name)
        return conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        return []


def query_one(db_name: str, sql: str, params: tuple = ()) -> sqlite3.Row | None:
    """执行查询，返回第一行或 None"""
    try:
        conn = get_conn(db_name)
        return conn.execute(sql, params).fetchone()
    except sqlite3.OperationalError:
        return None


def execute(db_name: str, sql: str, params: tuple = ()) -> sqlite3.Cursor:
    """执行写入语句，返回 cursor（可通过 lastrowid 获取自增ID）"""
    conn = get_conn(db_name)
    return conn.execute(sql, params)


def execute_many(db_name: str, sql: str, seq: list[tuple]) -> None:
    """批量执行"""
    conn = get_conn(db_name)
    conn.executemany(sql, seq)
    conn.commit()


def commit(db_name: str) -> None:
    """手动提交"""
    get_conn(db_name).commit()


@contextmanager
def transaction(db_name: str):
    """事务上下文管理器"""
    conn = get_conn(db_name)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise