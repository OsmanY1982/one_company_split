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

    @property
    def is_logged_in(self) -> bool:
        return self._logged_in

    @property
    def username(self) -> Optional[str]:
        return self._username

    @property
    def is_admin(self) -> bool:
        return self._role == 'admin'

    def login(self, username: str, role: str = 'user', license_type: str = 'basic', machine_code: str = ''):
        """登录"""
        self._logged_in = True
        self._username = username
        self._role = role
        self._license_type = license_type
        self._machine_code = machine_code

    def logout(self):
        """登出"""
        self._logged_in = False
        self._username = None
        self._role = None
        self._license_type = None


# 全局单例
app_state = AppState()
