# -*- coding: utf-8 -*-
"""
应用全局状态管理 — 单例模式
管理登录状态、用户信息、系统配置等
"""

import os
from typing import Dict, Optional


class AppState:
    """应用全局状态（单例）"""

    _instance: Optional['AppState'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 登录状态
        self._logged_in = False
        self._username: Optional[str] = None
        self._role: Optional[str] = None
        self._license_type: Optional[str] = None
        self._machine_code: Optional[str] = None
        self._remember: Dict = {}
        self._permissions: list = []  # P0: 当前用户的权限列表

    # ── P0 角色-权限映射（2026-06-28）──
    ROLE_PERMISSIONS = {
        "admin": ["*"],  # 超级管理员：一切权限
        "super_admin": ["*"],
        "user": [
            "dashboard.view", "profile.edit", "password.change",
            "wallet.view", "wallet.recharge",
        ],
        "member": [
            "dashboard.view", "profile.edit", "password.change",
        ],
    }

    @property
    def is_logged_in(self) -> bool:
        return self._logged_in

    @property
    def username(self) -> Optional[str]:
        return self._username

    @property
    def is_admin(self) -> bool:
        return self._role in ('admin', 'super_admin')

    @property
    def is_super_admin(self) -> bool:
        """P0: 超级管理员（拥有所有权限）"""
        return self._role == "super_admin" or (
            self._role == "admin" and self._username == "admin"
        )

    @property
    def permissions(self) -> list:
        """P0: 当前用户的权限列表"""
        if not self._permissions:
            self._permissions = self.ROLE_PERMISSIONS.get(
                self._role or "user", []
            )
        return self._permissions

    def has_permission(self, perm: str) -> bool:
        """P0: 检查是否有某个权限"""
        if self.is_super_admin or "*" in self.permissions:
            return True
        return perm in self.permissions

    def login(self, username: str, role: str = 'user', license_type: str = 'basic',
              machine_code: str = '', permissions: list = None):
        """登录"""
        self._logged_in = True
        self._username = username
        self._role = role
        self._license_type = license_type
        self._machine_code = machine_code
        self._permissions = permissions or self.ROLE_PERMISSIONS.get(role, [])

    def logout(self):
        """登出"""
        self._logged_in = False
        self._username = None
        self._role = None
        self._license_type = None
        self._permissions = []


# 全局单例
app_state = AppState()
