# `core/modules/auth/service/sync_auth_service.py`

> 路径：`core/modules/auth/service/sync_auth_service.py` | 行数：204


---


```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证同步服务 — 统一管理员增删用户 → 云端 → 用户端三端同步通道
P1: 整合 login/register/logout 后的全量同步 + 管理员增删改用户时触发三端同步。
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncAuthService:
    """认证同步服务：封装认证相关表（sessions/permissions/admin_config/users）的同步操作"""

    @staticmethod
    def sync_on_login(username: str) -> Dict[str, Any]:
        """登录后触发：拉取云端最新数据到本地"""
        results = {}
        try:
            from core.cloud_pull import pull_users
            results["users"] = pull_users()
        except Exception as e:
            results["users"] = f"pull_failed:{e}"
            logger.error(f"[sync_auth] 登录同步 users 失败: {e}")

        try:
            from core.cloud_pull import pull_user_memberships
            results["user_memberships"] = pull_user_memberships()
        except Exception as e:
            results["user_memberships"] = f"pull_failed:{e}"

        logger.info(f"[sync_auth] 登录同步完成（{username}）: {results}")
        return results

    @staticmethod
    def sync_on_register(username: str) -> Dict[str, Any]:
        """注册后触发：将新用户推送到云端"""
        results = {}
        try:
            from core.cloud_sync import sync_users
            sync_users()
            results["users"] = "pushed"
        except Exception as e:
            results["users"] = f"push_failed:{e}"
            logger.error(f"[sync_auth] 注册同步 users 失败: {e}")
        logger.info(f"[sync_auth] 注册同步完成（{username}）: {results}")
        return results

    @staticmethod
    def sync_on_admin_user_change(action: str, username: str) -> Dict[str, Any]:
        """管理员增删用户后触发全量三端同步（users + memberships + sessions + permissions）"""
        results = {}
        try:
            from core.cloud_sync import sync_users
            sync_users()
            results["users"] = "synced"
        except Exception as e:
            results["users"] = f"failed:{e}"

        try:
            from core.cloud_sync import sync_user_memberships
            sync_user_memberships()
            results["user_memberships"] = "synced"
        except Exception as e:
            results["user_memberships"] = f"failed:{e}"

        try:
            SyncAuthService.sync_sessions()
            results["sessions"] = "synced"
        except Exception as e:
            results["sessions"] = f"failed:{e}"

        try:
            SyncAuthService.sync_permissions()
            results["permissions"] = "synced"
        except Exception as e:
            results["permissions"] = f"failed:{e}"

        try:
            SyncAuthService.sync_admin_config()
            results["admin_config"] = "synced"
        except Exception as e:
            results["admin_config"] = f"failed:{e}"

        logger.info(f"[sync_auth] 管理员操作同步完成（{action} {username}）: {results}")
        return results

    @staticmethod
    def sync_all_auth_tables() -> Dict[str, Any]:
        """同步所有认证相关表（sessions + permissions + admin_config + users）"""
        results = {}
        for table, fn_name in [
            ("sessions", "sync_sessions"),
            ("permissions", "sync_permissions"),
            ("admin_config", "sync_admin_config"),
        ]:
            try:
                from core.cloud_sync import sync_table
                from core.cloud_sync import DB_PATHS
                if table in DB_PATHS:
                    sync_table(DB_PATHS[table], table)
                    results[table] = "synced"
                else:
                    results[table] = "no_db_path"
            except Exception as e:
                results[table] = f"failed:{e}"

        try:
            from core.cloud_sync import sync_users
            sync_users()
            results["users"] = "synced"
        except Exception as e:
            results["users"] = f"failed:{e}"

        logger.info(f"[sync_auth] 全量认证表同步: {results}")
        return results

    @staticmethod
    def sync_sessions() -> None:
        """单独同步 sessions 表"""
        from core.cloud_sync import sync_table, DB_PATHS
        if "sessions" in DB_PATHS:
            sync_table(DB_PATHS["sessions"], "sessions")

    @staticmethod
    def sync_permissions() -> None:
        """单独同步 permissions 表"""
        from core.cloud_sync import sync_table, DB_PATHS
        if "permissions" in DB_PATHS:
            sync_table(DB_PATHS["permissions"], "permissions")

    @staticmethod
    def sync_admin_config() -> None:
        """单独同步 admin_config 表（同步前自动桥接 admin.json）"""
        SyncAuthService._init_admin_db()
        from core.cloud_sync import sync_table, DB_PATHS
        if "admin_config" in DB_PATHS:
            sync_table(DB_PATHS["admin_config"], "admin_config")
    
    # ── P1: admin.json → admin.db 桥接（2026-06-28 第十三档）──
    @staticmethod
    def _init_admin_db(admin_json_path: str = None) -> None:
        """
        读取 admin.json 并同步到 admin.db → admin_config 表（key-value 桥接）。
        cloud_sync 通过 admin_config 表将管理员配置同步到 Supabase。
        """
        import json
        import sqlite3
        from datetime import datetime
        
        if admin_json_path is None:
            from core.paths import CONFIG_DIR
            admin_json_path = os.path.join(CONFIG_DIR, "admin.json")
        
        if not os.path.exists(admin_json_path):
            logger.warning(f"[SyncAuth] admin.json 不存在: {admin_json_path}")
            return
        
        with open(admin_json_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # admin.db 路径（与项目 DB 目录同）
        from core.paths import DATA_DIR
        admin_db_path = os.path.join(DATA_DIR, "admin.db")
        
        conn = sqlite3.connect(admin_db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT '',
                description TEXT DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT ''
            )
        """)
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mappings = [
            ("admin_name", config.get("admin_name", ""), "管理员用户名"),
            ("machine_code", config.get("machine_code", ""), "当前设备机器码"),
            ("set_at", config.get("set_at", ""), "管理员密码设置时间"),
            ("pwd_updated", "true" if config.get("pwd_updated") else "false", "密码是否已更新"),
            # 密码 bcypt hash 不同步到云端（安全原因，仅保留占位标记）
            ("has_admin_pwd", "true" if config.get("password") else "false", "管理员密码是否已设置"),
        ]
        
        for key, value, desc in mappings:
            conn.execute(
                "INSERT OR REPLACE INTO admin_config (key, value, description, updated_at) VALUES (?, ?, ?, ?)",
                (key, str(value) if value is not None else "", desc, now)
            )
        
        conn.commit()
        conn.close()
        logger.info(f"[SyncAuth] admin.json → admin.db 桥接完成 ({len(mappings)} 条)")


if __name__ == "__main__":
    print("SyncAuthService 模块加载成功")
    print("可用方法: sync_on_login / sync_on_register / sync_on_admin_user_change / sync_all_auth_tables")

```
