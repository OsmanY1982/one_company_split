"""全局会话上下文 — 统一悬浮球/智能中心/语音的AI对话状态"""
from datetime import datetime
from typing import Optional, Callable, List
import threading


class SessionContext:
    """
    全局单例：维护当前活跃的AI对话会话和窗口注册。
    悬浮球、智能中心、语音三个入口可各自独立打开AI对话窗口，各自维护独立会话。
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._current_session_id: str = "default"
        self._current_title: str = "对话"
        self._agent_bridge = None            # AgentBridge 引用
        self._active_windows: list = []       # 活跃的 AIChatWindow 列表
        self._listeners: List[Callable] = [] # 会话切换监听器
        self._message_listeners: List[Callable] = []  # 消息新增监听器
        
    def set_agent_bridge(self, bridge):
        """设置引擎引用（由悬浮球或智能中心初始化时注入）"""
        self._agent_bridge = bridge
        
    @property
    def agent_bridge(self):
        return self._agent_bridge
    
    @property
    def current_session_id(self) -> str:
        return self._current_session_id
    
    @property
    def current_title(self) -> str:
        return self._current_title
    
    def switch_session(self, session_id: str, title: str = "对话"):
        """切换当前活跃会话（全局生效）"""
        self._current_session_id = session_id
        self._current_title = title
        self._notify_listeners(session_id, title)
    
    def new_session(self) -> str:
        """创建新会话并设为当前"""
        sid = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.switch_session(sid, "新对话")
        return sid
    
    def register_window(self, window):
        """注册活跃的对话窗口"""
        if window not in self._active_windows:
            self._active_windows.append(window)
        
    def unregister_window(self, window):
        """注销对话窗口"""
        if window in self._active_windows:
            self._active_windows.remove(window)
    
    def add_listener(self, callback: Callable):
        """添加会话切换监听器"""
        if callback not in self._listeners:
            self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable):
        """移除监听器"""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self, session_id: str, title: str):
        """通知所有监听器会话已切换"""
        for cb in self._listeners:
            try:
                cb(session_id, title)
            except Exception as e:
                print(f"[SessionContext] 监听器异常: {e}")

    def add_message_listener(self, callback: Callable):
        """添加消息新增监听器，callback(session_id, role, content)"""
        if callback not in self._message_listeners:
            self._message_listeners.append(callback)

    def remove_message_listener(self, callback: Callable):
        """移除消息新增监听器"""
        if callback in self._message_listeners:
            self._message_listeners.remove(callback)

    def notify_message_added(self, session_id: str, role: str, content: str):
        """通知所有消息监听器有新消息"""
        for cb in self._message_listeners:
            try:
                cb(session_id, role, content)
            except Exception as e:
                print(f"[SessionContext] 消息监听器异常: {e}")


# 全局单例实例
session_ctx = SessionContext()
