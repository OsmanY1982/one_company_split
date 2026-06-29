# `iqra/core/collaboration_client.py`

> 路径：`iqra/core/collaboration_client.py` | 行数：495


---


```python
"""
Iqra × Hermes Collaboration Client
实现 Iqra 与 Hermes 的协作协议
"""

import json
import uuid
import requests
import socket
import threading
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum
import os


class MessageType(Enum):
    """消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    HEARTBEAT = "heartbeat"


class PayloadType(Enum):
    """载荷类型"""
    TASK = "task"
    DATA = "data"
    QUERY = "query"
    COMMAND = "command"
    ERROR = "error"


@dataclass
class CollaborationMessage:
    """协作消息"""
    protocol_version: str = "1.0"
    message_type: str = "request"
    sender: str = "iqra"
    receiver: str = "hermes"
    timestamp: str = None
    session_id: str = None
    request_id: str = None
    payload: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.session_id is None:
            self.session_id = str(uuid.uuid4())
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())
        if self.payload is None:
            self.payload = {}


@dataclass
class CollaborationResponse:
    """协作响应"""
    success: bool
    data: Any = None
    error: str = None
    error_code: str = None
    execution_time: float = 0.0


class IqraHermesClient:
    """
    Iqra-Hermes 协作客户端
    实现协作协议，支持任务分发、数据交换、状态同步
    """
    
    def __init__(self, hermes_endpoint: str = None, use_local_socket: bool = True):
        """
        初始化协作客户端
        
        Args:
            hermes_endpoint: Hermes API 端点
            use_local_socket: 是否使用本地 Socket 通信
        """
        self.hermes_endpoint = hermes_endpoint or "http://localhost:8080"
        self.use_local_socket = use_local_socket
        self.session_id = str(uuid.uuid4())
        self.message_handlers: Dict[str, Callable] = {}
        self.pending_requests: Dict[str, threading.Event] = {}
        self.responses: Dict[str, CollaborationResponse] = {}
        self.socket_thread: Optional[threading.Thread] = None
        self.running = False
        
        # 注册默认消息处理器
        self._register_default_handlers()
        
        # 如果使用本地 Socket，启动监听
        if use_local_socket:
            self._start_socket_listener()
    
    def _register_default_handlers(self):
        """注册默认消息处理器"""
        self.message_handlers["task_complete"] = self._handle_task_complete
        self.message_handlers["data_response"] = self._handle_data_response
        self.message_handlers["error"] = self._handle_error
    
    def _start_socket_listener(self):
        """启动 Socket 监听线程"""
        self.running = True
        self.socket_thread = threading.Thread(target=self._socket_listener, daemon=True)
        self.socket_thread.start()
    
    def _socket_listener(self):
        """Socket 监听循环"""
        socket_path = "/tmp/iqra_hermes.sock"
        
        try:
            # 删除旧的 socket 文件
            if os.path.exists(socket_path):
                os.remove(socket_path)
            
            # 创建 Unix Socket
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(socket_path)
            server.listen(5)
            
            while self.running:
                try:
                    conn, addr = server.accept()
                    data = conn.recv(4096)
                    if data:
                        message = json.loads(data.decode('utf-8'))
                        self._process_message(message)
                    conn.close()
                except Exception as e:
                    print(f"Socket 错误: {e}")
        except Exception as e:
            print(f"Socket 监听错误: {e}")
    
    def _process_message(self, message: Dict[str, Any]):
        """处理接收到的消息"""
        message_type = message.get("payload", {}).get("type")
        request_id = message.get("request_id")
        
        if message_type in self.message_handlers:
            self.message_handlers[message_type](message)
        
        # 通知等待的线程
        if request_id and request_id in self.pending_requests:
            self.pending_requests[request_id].set()
    
    def _handle_task_complete(self, message: Dict[str, Any]):
        """处理任务完成消息"""
        request_id = message.get("request_id")
        payload = message.get("payload", {})
        
        self.responses[request_id] = CollaborationResponse(
            success=True,
            data=payload.get("content"),
            execution_time=payload.get("metadata", {}).get("execution_time", 0)
        )
    
    def _handle_data_response(self, message: Dict[str, Any]):
        """处理数据响应消息"""
        request_id = message.get("request_id")
        payload = message.get("payload", {})
        
        self.responses[request_id] = CollaborationResponse(
            success=True,
            data=payload.get("content", {}).get("data")
        )
    
    def _handle_error(self, message: Dict[str, Any]):
        """处理错误消息"""
        request_id = message.get("request_id")
        payload = message.get("payload", {})
        content = payload.get("content", {})
        
        self.responses[request_id] = CollaborationResponse(
            success=False,
            error=content.get("error_message"),
            error_code=content.get("error_code")
        )
    
    def send_task(self, task_type: str, description: str,
                  parameters: Dict[str, Any] = None,
                  priority: int = 1,
                  timeout: int = 300) -> CollaborationResponse:
        """
        发送任务请求到 Hermes
        
        Args:
            task_type: 任务类型 (analysis|execution|query|generation)
            description: 任务描述
            parameters: 任务参数
            priority: 优先级 (1-5)
            timeout: 超时时间（秒）
            
        Returns:
            CollaborationResponse
        """
        message = CollaborationMessage(
            message_type="request",
            sender="iqra",
            receiver="hermes",
            session_id=self.session_id,
            payload={
                "type": "task",
                "content": {
                    "task_id": str(uuid.uuid4()),
                    "task_type": task_type,
                    "description": description,
                    "parameters": parameters or {},
                    "priority": priority,
                    "timeout": timeout
                }
            }
        )
        
        return self._send_and_wait(message, timeout)
    
    def send_data(self, data_type: str, operation: str,
                  path: str, data: Any = None,
                  format: str = "json") -> CollaborationResponse:
        """
        发送数据交换请求
        
        Args:
            data_type: 数据类型 (database|file|memory|context)
            operation: 操作类型 (read|write|update|delete)
            path: 数据路径
            data: 数据内容
            format: 数据格式
            
        Returns:
            CollaborationResponse
        """
        message = CollaborationMessage(
            message_type="request",
            sender="iqra",
            receiver="hermes",
            session_id=self.session_id,
            payload={
                "type": "data",
                "content": {
                    "data_type": data_type,
                    "operation": operation,
                    "path": path,
                    "data": data,
                    "format": format
                }
            }
        )
        
        return self._send_and_wait(message, timeout=60)
    
    def send_query(self, query_type: str, query: str,
                   filters: Dict[str, Any] = None) -> CollaborationResponse:
        """
        发送查询请求
        
        Args:
            query_type: 查询类型 (skill|agent|status|capability)
            query: 查询内容
            filters: 过滤条件
            
        Returns:
            CollaborationResponse
        """
        message = CollaborationMessage(
            message_type="request",
            sender="iqra",
            receiver="hermes",
            session_id=self.session_id,
            payload={
                "type": "query",
                "content": {
                    "query_type": query_type,
                    "query": query,
                    "filters": filters or {}
                }
            }
        )
        
        return self._send_and_wait(message, timeout=30)
    
    def send_command(self, command: str, script: str,
                     args: List[str] = None,
                     env: Dict[str, str] = None,
                     sandbox: bool = True,
                     timeout: int = 60) -> CollaborationResponse:
        """
        发送命令执行请求
        
        Args:
            command: 命令类型 (python_code|shell|sql)
            script: 脚本内容
            args: 命令参数
            env: 环境变量
            sandbox: 是否使用沙箱
            timeout: 超时时间
            
        Returns:
            CollaborationResponse
        """
        message = CollaborationMessage(
            message_type="request",
            sender="iqra",
            receiver="hermes",
            session_id=self.session_id,
            payload={
                "type": "command",
                "content": {
                    "command": command,
                    "script": script,
                    "args": args or [],
                    "env": env or {},
                    "sandbox": sandbox,
                    "timeout": timeout
                }
            }
        )
        
        return self._send_and_wait(message, timeout)
    
    def _send_and_wait(self, message: CollaborationMessage, timeout: int) -> CollaborationResponse:
        """发送消息并等待响应"""
        request_id = message.request_id
        
        # 创建等待事件
        event = threading.Event()
        self.pending_requests[request_id] = event
        
        try:
            # 发送消息
            if self.use_local_socket:
                self._send_via_socket(message)
            else:
                self._send_via_http(message)
            
            # 等待响应
            if event.wait(timeout):
                # 收到响应
                response = self.responses.pop(request_id, None)
                if response:
                    return response
                else:
                    return CollaborationResponse(
                        success=False,
                        error="未收到响应数据",
                        error_code="E002"
                    )
            else:
                # 超时
                return CollaborationResponse(
                    success=False,
                    error=f"请求超时（{timeout}秒）",
                    error_code="E002"
                )
        finally:
            # 清理
            self.pending_requests.pop(request_id, None)
            self.responses.pop(request_id, None)
    
    def _send_via_socket(self, message: CollaborationMessage):
        """通过 Socket 发送消息"""
        socket_path = "/tmp/hermes_iqra.sock"
        
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(socket_path)
            client.send(json.dumps(asdict(message)).encode('utf-8'))
            client.close()
        except Exception as e:
            print(f"Socket 发送失败: {e}")
            raise
    
    def _send_via_http(self, message: CollaborationMessage):
        """通过 HTTP 发送消息"""
        try:
            response = requests.post(
                f"{self.hermes_endpoint}/api/v1/collaborate",
                json=asdict(message),
                timeout=10
            )
            
            if response.status_code == 200:
                # 异步处理响应
                self._process_message(response.json())
            else:
                raise Exception(f"HTTP 错误: {response.status_code}")
        except Exception as e:
            print(f"HTTP 发送失败: {e}")
            raise
    
    def register_handler(self, message_type: str, handler: Callable):
        """注册自定义消息处理器"""
        self.message_handlers[message_type] = handler
    
    def get_status(self) -> Dict[str, Any]:
        """获取客户端状态"""
        return {
            "session_id": self.session_id,
            "hermes_endpoint": self.hermes_endpoint,
            "use_local_socket": self.use_local_socket,
            "running": self.running,
            "pending_requests": len(self.pending_requests),
            "registered_handlers": list(self.message_handlers.keys())
        }
    
    def close(self):
        """关闭客户端"""
        self.running = False
        if self.socket_thread and self.socket_thread.is_alive():
            self.socket_thread.join(timeout=2)


# ═══════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════

def analyze_with_hermes(data_source: str, analysis_type: str,
                        parameters: Dict[str, Any] = None) -> CollaborationResponse:
    """使用 Hermes 进行数据分析"""
    client = IqraHermesClient()
    return client.send_task(
        task_type="analysis",
        description=f"分析 {data_source} 的 {analysis_type}",
        parameters={
            "data_source": data_source,
            "analysis_type": analysis_type,
            **(parameters or {})
        }
    )


def generate_with_hermes(prompt: str, content_type: str = "text",
                         parameters: Dict[str, Any] = None) -> CollaborationResponse:
    """使用 Hermes 生成内容"""
    client = IqraHermesClient()
    return client.send_task(
        task_type="generation",
        description=f"生成 {content_type}: {prompt}",
        parameters={
            "prompt": prompt,
            "content_type": content_type,
            **(parameters or {})
        }
    )


def query_hermes_capability(query: str) -> CollaborationResponse:
    """查询 Hermes 能力"""
    client = IqraHermesClient()
    return client.send_query(
        query_type="capability",
        query=query
    )


# ═══════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════

if __name__ == "__main__":
    print("Iqra × Hermes Collaboration Client")
    print("=" * 50)
    
    # 创建客户端（不使用 Socket，仅 HTTP）
    client = IqraHermesClient(use_local_socket=False)
    
    print(f"客户端状态: {client.get_status()}")
    print()
    
    # 示例：发送查询请求
    print("示例：查询 Hermes 能力")
    response = client.send_query(
        query_type="capability",
        query="支持哪些数据分析功能"
    )
    print(f"响应: {response}")
    print()
    
    # 示例：发送任务请求
    print("示例：发送分析任务")
    response = client.send_task(
        task_type="analysis",
        description="分析销售数据趋势",
        parameters={
            "data_source": "sales.db",
            "time_range": "last_30_days"
        },
        timeout=60
    )
    print(f"响应: {response}")
    
    client.close()
    print("\n客户端已关闭")
```
