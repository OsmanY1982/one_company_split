"""
星空版 → 宇宙版 兼容桩（Stubs）

为依赖 iqra 或星空版特有基础设施的模块提供最小化替代实现。
"""

import os
import json
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional


# ═══════════════════════════════════════════
# EnhancedAIAssistant 桩（替代 iqra 依赖）
# ═══════════════════════════════════════════

class EnhancedAIAssistant:
    """桩实现：替代星空版 enhanced/enhanced_tools.py 中的 EnhancedAIAssistant
    
    原版依赖 iqra.core.tool_registry（ToolRegistry/ToolDefinition），
    宇宙版暂不引入完整 iqra 框架。
    """
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir
        self.sessions: Dict[str, Dict] = {}
        self.memory: Dict[str, Any] = {}
        self.scheduled_tasks: List[Dict] = []

    def execute(self, action: str, params: dict = None) -> dict:
        return {"status": "stub", "action": action, "params": params}

    def get_registry(self):
        return {"tools": [], "count": 0}


# ═══════════════════════════════════════════
# AppState 桩（替代星空版 core/app_state）
# ═══════════════════════════════════════════

class AppState:
    """桩实现：替代星空版 core/app_state.AppState
    
    原版有完整的登录/登出/踢出/序列化机制，这里提供最小化替代。
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self.user_id = None
        self.username = "admin"
        self.role = "admin"
        self.session_token = None
        self.device_type = "desktop"
        self.current_module = "intelligence"
        self._kicked = False

    def login(self, user_id, username, role="user", session_token=None, device_type="desktop"):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.session_token = session_token
        self.device_type = device_type

    def logout(self):
        self.user_id = None
        self.username = None
        self.session_token = None

    def mark_kicked(self):
        self._kicked = True

    def is_kicked(self):
        return self._kicked

    def is_admin(self):
        return self.role == "admin"

    def save(self):
        pass


# ═══════════════════════════════════════════
# ConfigManager 桩（替代 iqra.modules.chat_window.ConfigManager）
# ═══════════════════════════════════════════

class OpcConfigManager:
    """桩实现：替代星空版 iqra.modules.chat_window.ConfigManager"""
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self._config = {}

    def get_active_provider(self):
        return None  # cosmic uses its own LLM config

    def get(self, key, default=None):
        return self._config.get(key, default)

    def set(self, key, value):
        self._config[key] = value

    def save(self):
        pass


# ═══════════════════════════════════════════
# SecureStorage 桩（替代 iqra.modules.chat_window.SecureStorage）
# ═══════════════════════════════════════════

class OpcSecureStorage:
    """桩实现：替代星空版 iqra 的 SecureStorage"""
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self._store: Dict[str, str] = {}

    def get(self, key: str, default: str = "") -> str:
        return self._store.get(key, default)

    def set(self, key: str, value: str):
        self._store[key] = value

    def delete(self, key: str):
        self._store.pop(key, None)

    def exists(self, key: str) -> bool:
        return key in self._store


# 全局单例
app_state = AppState()
