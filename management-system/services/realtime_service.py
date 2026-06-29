"""
实时消息服务
WebSocket实时通信
"""

import json
import threading
import time
from typing import Dict, List, Optional, Callable
from collections import defaultdict
from datetime import datetime


class RealtimeService:
    """实时消息服务"""

    def __init__(self):
        self._connections: Dict[str, "_Connection"] = {}
        self._channels: Dict[str, List[str]] = defaultdict(list)
        self._message_handlers: Dict[str, Callable] = {}
        self._is_running = False
        self._heartbeat_thread: Optional[threading.Thread] = None

    def start(self, host: str = "localhost", port: int = 9000):
        """启动服务"""
        self._is_running = True
        self._start_heartbeat()

    def stop(self):
        """停止服务"""
        self._is_running = False
        self._connections.clear()
        self._channels.clear()

    def register_handler(self, event: str, handler: Callable):
        """注册消息处理器"""
        self._message_handlers[event] = handler

    def connect(self, client_id: str) -> Dict:
        """客户端连接"""
        connection = _Connection(client_id)
        self._connections[client_id] = connection
        return {"success": True, "client_id": client_id}

    def disconnect(self, client_id: str):
        """客户端断开"""
        self._connections.pop(client_id, None)

        # 从所有频道移除
        for channel in self._channels.values():
            if client_id in channel:
                channel.remove(client_id)

    def subscribe(self, client_id: str, channel: str):
        """订阅频道"""
        self._channels[channel].append(client_id)

    def unsubscribe(self, client_id: str, channel: str):
        """取消订阅"""
        if channel in self._channels:
            self._channels[channel] = [c for c in self._channels[channel] if c != client_id]

    def broadcast(self, event: str, data: Dict, channel: Optional[str] = None):
        """广播消息"""
        message = {
            "event": event,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        if channel:
            clients = self._channels.get(channel, [])
        else:
            clients = list(self._connections.keys())

        for client_id in clients:
            self._send_to_client(client_id, message)

    def send_to_client(self, client_id: str, event: str, data: Dict):
        """发送给指定客户端"""
        message = {
            "event": event,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        self._send_to_client(client_id, message)

    def _send_to_client(self, client_id: str, message: Dict):
        """发送消息给客户端"""
        connection = self._connections.get(client_id)
        if connection:
            connection.send(message)

    def handle_message(self, client_id: str, raw_message: str):
        """处理收到的消息"""
        try:
            message = json.loads(raw_message)
            event = message.get("event")

            if event and event in self._message_handlers:
                handler = self._message_handlers[event]
                handler(client_id, message.get("data", {}))
        except Exception:
            pass

    def _start_heartbeat(self):
        """启动心跳"""
        def heartbeat():
            while self._is_running:
                self.broadcast("heartbeat", {}, channel=None)
                time.sleep(30)

        self._heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        self._heartbeat_thread.start()

    def get_status(self) -> Dict:
        """获取服务状态"""
        return {
            "running": self._is_running,
            "connections": len(self._connections),
            "channels": len(self._channels),
            "channels_detail": {
                channel: len(clients)
                for channel, clients in self._channels.items()
            },
        }

    def get_connected_clients(self) -> List[str]:
        """获取已连接客户端"""
        return list(self._connections.keys())


class _Connection:
    """连接封装"""

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.connected_at = datetime.now()
        self.messages: List[Dict] = []

    def send(self, message: Dict):
        self.messages.append(message)


# 全局实例
realtime_service = RealtimeService()

