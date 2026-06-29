# `core/event_bus.py`

> 路径：`core/event_bus.py` | 行数：49


---


```python
# -*- coding: utf-8 -*-
"""
事件总线
模块间通过事件通信，避免直接互相调用
"""
from typing import Callable, Dict, List, Optional
from PyQt5.QtCore import QObject, pyqtSignal


class EventBus(QObject):
    """事件总线单例"""

    _instance: Optional['EventBus'] = None

    user_logged_in = pyqtSignal(str)
    user_logged_out = pyqtSignal()
    module_switched = pyqtSignal(str)
    data_updated = pyqtSignal(str, object)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_name: str, callback: Callable):
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable):
        if event_name in self._subscribers:
            if callback in self._subscribers[event_name]:
                self._subscribers[event_name].remove(callback)

    def emit_custom(self, event_name: str, *args, **kwargs):
        if event_name in self._subscribers:
            for callback in self._subscribers[event_name]:
                callback(*args, **kwargs)


event_bus = EventBus()

```
