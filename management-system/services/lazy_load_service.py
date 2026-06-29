"""
延迟加载服务
模块懒加载，减少启动时间
"""

import importlib
import threading
from typing import Any, Callable, Dict, Optional


class LazyLoadService:
    """延迟加载服务"""

    def __init__(self):
        self._modules: Dict[str, "_LazyModule"] = {}
        self._lock = threading.Lock()

    def register(self, name: str, import_path: str):
        """注册延迟加载模块"""
        with self._lock:
            self._modules[name] = _LazyModule(name, import_path)

    def get(self, name: str) -> Optional[Any]:
        """获取已加载的模块"""
        lm = self._modules.get(name)
        if lm:
            return lm.get()
        return None

    def load(self, name: str) -> Optional[Any]:
        """显式加载模块"""
        return self.get(name)

    def preload(self, names: list):
        """预加载一组模块（后台）"""
        def _preload():
            for name in names:
                self.get(name)

        thread = threading.Thread(target=_preload, daemon=True)
        thread.start()

    def is_loaded(self, name: str) -> bool:
        """检查是否已加载"""
        lm = self._modules.get(name)
        return lm.is_loaded() if lm else False

    def get_all_loaded(self) -> Dict[str, Any]:
        """获取所有已加载的模块"""
        return {name: lm.get() for name, lm in self._modules.items() if lm.is_loaded()}

    def unload(self, name: str):
        """卸载模块"""
        with self._lock:
            self._modules.pop(name, None)


class _LazyModule:
    """延迟模块包装"""

    def __init__(self, name: str, import_path: str):
        self.name = name
        self.import_path = import_path
        self._module: Optional[Any] = None
        self._error: Optional[str] = None

    def get(self) -> Optional[Any]:
        """获取模块，首次访问时加载"""
        if self._error:
            return None

        if self._module is not None:
            return self._module

        try:
            self._module = importlib.import_module(self.import_path)
        except ImportError as e:
            self._error = str(e)

        return self._module

    def is_loaded(self) -> bool:
        return self._module is not None


# 全局实例
lazy_loader = LazyLoadService()

