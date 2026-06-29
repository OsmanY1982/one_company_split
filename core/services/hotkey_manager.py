"""热键管理器

全局快捷键注册和管理
"""
from __future__ import annotations

import json
import os
from typing import Dict, Callable, Optional, List
from dataclasses import dataclass
@dataclass
class HotKey:
    """热键定义"""
    key: str
    modifiers: List[str]  # 'ctrl', 'alt', 'shift', 'cmd'
    action: str
    description: str
    enabled: bool = True
class HotkeyManager:
    """热键管理器"""
    def __init__(self, config_file: str = "data/hotkeys.json") -> None:
        self.config_file = config_file
        self._hotkeys: Dict[str, HotKey] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._load_config()
    def _load_config(self) -> None:
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                for item in config.get("hotkeys", []):
                    hk = HotKey(**item)
                    self._hotkeys[hk.action] = hk
            except Exception:
                pass
        # 默认热键
        if not self._hotkeys:
            self._init_defaults()
    def _init_defaults(self) -> None:
        """初始化默认热键"""
        defaults = [
            HotKey(key="N", modifiers=["ctrl"], action="new_order", description="新建订单"),
            HotKey(key="S", modifiers=["ctrl"], action="save", description="保存"),
            HotKey(key="F", modifiers=["ctrl"], action="search", description="搜索"),
            HotKey(key="P", modifiers=["ctrl"], action="print", description="打印"),
            HotKey(key="Z", modifiers=["ctrl"], action="undo", description="撤销"),
            HotKey(key="Y", modifiers=["ctrl"], action="redo", description="重做"),
            HotKey(key="F5", modifiers=[], action="refresh", description="刷新"),
            HotKey(key="Escape", modifiers=[], action="close", description="关闭"),
        ]
        for hk in defaults:
            self._hotkeys[hk.action] = hk
        self._save_config()
    def _save_config(self) -> None:
        """保存配置"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        config = {
            "hotkeys": [
                {
                    "key": hk.key,
                    "modifiers": hk.modifiers,
                    "action": hk.action,
                    "description": hk.description,
                    "enabled": hk.enabled,
                }
                for hk in self._hotkeys.values()
            ]
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    def register_hotkey(self,
                        action: str,
                        key: str,
                        modifiers: Optional[List[str]] = None,
                        description: str = "",
                        callback: Optional[Callable] = None) -> bool:
        """注册热键"""
        if action in self._hotkeys:
            return False
        hk = HotKey(
            key=key,
            modifiers=modifiers or [],
            action=action,
            description=description,
        )
        self._hotkeys[action] = hk
        if callback:
            self._callbacks[action] = callback
        self._save_config()
        return True
    def unregister_hotkey(self, action: str) -> bool:
        """取消注册热键"""
        if action in self._hotkeys:
            del self._hotkeys[action]
            self._callbacks.pop(action, None)
            self._save_config()
            return True
        return False
    def bind_callback(self, action: str, callback: Callable) -> None:
        """绑定回调"""
        self._callbacks[action] = callback
    def handle_key_event(self, key: str, modifiers: List[str]) -> Optional[str]:
        """处理按键事件，返回匹配的action"""
        for action, hk in self._hotkeys.items():
            if hk.enabled and hk.key.upper() == key.upper() and set(hk.modifiers) == set(modifiers):
                callback = self._callbacks.get(action)
                if callback:
                    callback()
                return action
        return None
    def get_hotkey_string(self, action: str) -> str:
        """获取热键字符串"""
        hk = self._hotkeys.get(action)
        if not hk:
            return ""
        parts = list(hk.modifiers) + [hk.key]
        return "+".join(parts).replace("ctrl", "Ctrl").replace("alt", "Alt").replace("shift", "Shift").replace("cmd", "Cmd")
    def get_all_hotkeys(self) -> List[Dict]:
        """获取所有热键"""
        return [
            {
                "action": hk.action,
                "key": hk.key,
                "modifiers": hk.modifiers,
                "description": hk.description,
                "enabled": hk.enabled,
                "shortcut": self.get_hotkey_string(hk.action),
            }
            for hk in self._hotkeys.values()
        ]
    def set_enabled(self, action: str, enabled: bool) -> None:
        """启用/禁用热键"""
        if action in self._hotkeys:
            self._hotkeys[action].enabled = enabled
            self._save_config()
    def check_conflict(self, key: str, modifiers: List[str], exclude_action: Optional[str] = None) -> Optional[str]:
        """检查热键冲突"""
        for action, hk in self._hotkeys.items():
            if action == exclude_action:
                continue
            if hk.key.upper() == key.upper() and set(hk.modifiers) == set(modifiers):
                return action
        return None