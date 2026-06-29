# `iqra/tools/a2a_tool.py`

> 路径：`iqra/tools/a2a_tool.py` | 行数：881


---


```python
#!/usr/bin/env python3
"""
A2A (Agent-to-Agent) Protocol Client & Server

Implements the A2A 0.2.1 open standard (Linux Foundation, contributed by
Google) for inter-agent communication. Enables iqra to:
  - Publish an Agent Card so other agents can discover its capabilities
  - Discover remote A2A agents and delegate tasks to them
  - Manage task lifecycle: create, poll status, cancel, get artifacts

Protocol: JSON-RPC 2.0 over HTTP(S) + SSE for streaming.
No external dependencies -- pure stdlib (http.server, urllib, json, threading).

Configuration in iqra config (config/a2a.json or env vars)::

    {
      "server": {
        "enabled": true,
        "host": "0.0.0.0",
        "port": 9100,
        "name": "Iqra Agent",
        "description": "AI-powered coding, file management, and system agent",
        "version": "3.0.0"
      },
      "remote_agents": {
        "file_helper": {
          "card_url": "https://file-agent.example.com/.well-known/agent.json",
          "timeout": 300
        }
      }
    }

Registered tools in iqra ToolRegistry:
  - a2a_discover_agents: list configured remote A2A agents
  - a2a_send_task: delegate a task to a remote A2A agent
  - a2a_get_task: check task status and get results
  - a2a_cancel_task: cancel a running remote task

Integration:
  - With tools/sub_agent.py: remote A2A agents act as external SubAgents
  - With tools/delegate_tool.py: shared blocking/timeout patterns
  - Agent Card auto-populated from iqra ToolRegistry + skill_loader
"""

import json
import logging
import os
import socket
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────
# 常量
# ──────────────────────────────────────────────────────

A2A_SPEC_VERSION = "0.2.1"
JSONRPC_VERSION = "2.0"
DEFAULT_PORT = 9100
DEFAULT_TIMEOUT = 300  # 远程任务默认超时（秒）
MAX_POLL_INTERVAL = 10  # 轮询远程任务最大间隔（秒）
AGENT_CARD_PATH = "/.well-known/agent.json"

# ──────────────────────────────────────────────────────
# 数据类：A2A 核心类型
# ──────────────────────────────────────────────────────


@dataclass
class AgentProvider:
    """智能体服务提供商信息"""
    organization: str
    url: str


@dataclass
class AgentCapabilities:
    """A2A 协议可选能力"""
    streaming: bool = False
    pushNotifications: bool = False
    stateTransitionHistory: bool = False


@dataclass
class AgentSkill:
    """智能体技能描述"""
    id: str
    name: str
    description: str
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    inputModes: List[str] = field(default_factory=lambda: ["text"])
    outputModes: List[str] = field(default_factory=lambda: ["text"])


@dataclass
class AgentCard:
    """A2A Agent Card -- 智能体数字名片"""
    name: str
    description: str
    url: str
    version: str
    capabilities: AgentCapabilities
    defaultInputModes: List[str] = field(default_factory=lambda: ["text"])
    defaultOutputModes: List[str] = field(default_factory=lambda: ["text", "application/json"])
    skills: List[AgentSkill] = field(default_factory=list)
    provider: Optional[AgentProvider] = None
    iconUrl: Optional[str] = None
    documentationUrl: Optional[str] = None
    supportsAuthenticatedExtendedCard: bool = False

    def to_dict(self) -> dict:
        return _dataclass_to_dict(self)


@dataclass
class TaskStatus:
    """A2A 任务状态"""
    state: str  # "working" | "input-required" | "completed" | "failed" | "cancelled"
    message: Optional[Dict[str, Any]] = None
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class A2ATask:
    """本地跟踪的 A2A 任务"""
    task_id: str
    agent_url: str
    status: str = "working"  # working/input-required/completed/failed/cancelled
    message: Optional[str] = None
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    poll_count: int = 0


# ──────────────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────────────


def _dataclass_to_dict(obj) -> Any:
    """将 dataclass 递归转为 dict，去除 None 值"""
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for f in obj.__dataclass_fields__:
            val = getattr(obj, f)
            if val is not None:
                result[f] = _dataclass_to_dict(val)
        return result
    if isinstance(obj, list):
        return [_dataclass_to_dict(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    return obj


def _make_jsonrpc_request(method: str, params: dict = None, request_id: str = None) -> dict:
    """构建 JSON-RPC 2.0 请求"""
    return {
        "jsonrpc": JSONRPC_VERSION,
        "method": method,
        "params": params or {},
        "id": request_id or str(uuid.uuid4()),
    }


def _send_jsonrpc(url: str, method: str, params: dict = None, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """发送 JSON-RPC 2.0 请求并返回结果"""
    req_body = json.dumps(_make_jsonrpc_request(method, params)).encode("utf-8")
    http_req = Request(
        url,
        data=req_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    try:
        resp = urlopen(http_req, timeout=timeout)
        elapsed = time.monotonic() - started
        logger.debug("A2A rpc %s → %s (%.1fs)", method, url, elapsed)
        result = json.loads(resp.read().decode("utf-8"))
        if "error" in result:
            raise RuntimeError(
                f"A2A RPC error [{result['error'].get('code', -1)}]: "
                f"{result['error'].get('message', 'unknown')}"
            )
        return result.get("result", {})
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"A2A HTTP {e.code}: {body[:500]}")
    except URLError as e:
        raise RuntimeError(f"A2A connection failed: {e.reason}")
    except (TimeoutError, OSError) as e:
        raise RuntimeError(f"A2A timeout/network error: {e}")


def _find_free_port() -> int:
    """查找可用端口"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


# ──────────────────────────────────────────────────────
# Agent Card 构建器
# ──────────────────────────────────────────────────────


class AgentCardBuilder:
    """从 iqra 运行时状态构建 A2A Agent Card"""

    def __init__(self, tool_registry=None, skill_loader=None):
        self._tool_registry = tool_registry
        self._skill_loader = skill_loader

    def build(self, name: str, description: str, url: str, version: str = "1.0.0") -> AgentCard:
        """构建 Agent Card"""
        skills = self._collect_skills()
        return AgentCard(
            name=name,
            description=description,
            url=url,
            version=version,
            capabilities=AgentCapabilities(streaming=False),
            defaultInputModes=["text"],
            defaultOutputModes=["text", "application/json"],
            skills=skills,
            provider=AgentProvider(organization="Iqra", url="https://github.com/iqra"),
        )

    def _collect_skills(self) -> List[AgentSkill]:
        """从 tool_registry 和 skill_loader 收集技能描述"""
        skills = []

        # 从工具注册表收集工具技能
        if self._tool_registry:
            try:
                tools = self._tool_registry.list_tools()
                categorized = {}
                for t in tools:
                    cat = getattr(t, "category", "general")
                    categorized.setdefault(cat, []).append(t)
                for cat, cat_tools in categorized.items():
                    skills.append(AgentSkill(
                        id=f"tools.{cat}",
                        name=f"{cat}工具集",
                        description=f"{len(cat_tools)} 个工具: "
                                    f"{', '.join(getattr(t, 'name', str(t)) for t in cat_tools[:8])}",
                        tags=[cat, "tools"],
                    ))
            except Exception:
                pass

        # 从技能加载器收集
        if self._skill_loader:
            try:
                loaded = getattr(self._skill_loader, "loaded_skills", {})
                for name, skill in loaded.items():
                    skills.append(AgentSkill(
                        id=f"skill.{name}",
                        name=str(name),
                        description=getattr(skill, "description", str(skill))[:200],
                        tags=["skill"],
                    ))
            except Exception:
                pass

        # 始终包含核心技能
        skills.append(AgentSkill(
            id="core.agent_loop",
            name="自主Agent循环",
            description="Think→Plan→Act→Observe→Reflect 五阶段自主执行，支持多步推理与错误恢复",
            tags=["core", "agent"],
            examples=["重构 src/ 下所有 Python 文件", "排查 API 500 错误根因"],
        ))
        skills.append(AgentSkill(
            id="core.mcp",
            name="MCP工具调用",
            description="通过 Model Context Protocol 连接外部工具服务器（52,700+ 已注册）",
            tags=["core", "mcp", "tools"],
        ))

        return skills


# ──────────────────────────────────────────────────────
# A2A HTTP 请求处理（Agent Card 端点）
# ──────────────────────────────────────────────────────


class A2ACardHandler(BaseHTTPRequestHandler):
    """处理 Agent Card 请求的 HTTP handler"""

    agent_card_json: str = "{}"  # 类变量，由 server 注入

    def do_GET(self):
        if self.path == AGENT_CARD_PATH or self.path == "/agent-card":
            self._send_json(self.agent_card_json)
        elif self.path == "/health":
            self._send_json(json.dumps({"status": "ok"}))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "not found"}')

    def do_HEAD(self):
        if self.path == AGENT_CARD_PATH:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """处理 JSON-RPC 任务请求"""
        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            request = json.loads(body)
        except json.JSONDecodeError:
            self._send_error(-32700, "Parse error")
            return

        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params", {})

        try:
            result = self._route_rpc(method, params)
            response = {"jsonrpc": JSONRPC_VERSION, "result": result, "id": req_id}
        except Exception as e:
            response = {
                "jsonrpc": JSONRPC_VERSION,
                "error": {"code": -32603, "message": str(e)},
                "id": req_id,
            }
        self._send_json(json.dumps(response))

    def _route_rpc(self, method: str, params: dict) -> dict:
        """路由 JSON-RPC 方法到处理器"""
        handler = getattr(self.server, "_task_handler", None)
        if handler is None:
            raise RuntimeError("A2A server has no task handler configured")

        if method == "tasks/send":
            return handler.create_task(params)
        if method == "tasks/get":
            return handler.get_task(params.get("id", ""))
        if method == "tasks/cancel":
            return handler.cancel_task(params.get("id", ""))
        if method == "message/send":
            return handler.send_message(params)
        raise RuntimeError(f"Method not found: {method}")

    def _send_json(self, json_str: str):
        data = json_str.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _send_error(self, code: int, message: str):
        err = json.dumps({"jsonrpc": JSONRPC_VERSION, "error": {"code": code, "message": message}, "id": None})
        data = err.encode("utf-8")
        self.send_response(400)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        logger.debug("A2A HTTP: %s", fmt % args)


# ──────────────────────────────────────────────────────
# A2A 任务处理器（服务端）
# ──────────────────────────────────────────────────────


class A2ATaskHandler:
    """
    处理远程 agent 发来的 A2A 任务请求。
    将 A2A 任务桥接到 iqra 的 AgentLoop 执行。
    """

    def __init__(self, agent_loop_factory: Callable = None):
        """
        agent_loop_factory: 无参调用，返回一个可执行的 agent_loop 实例，
                           必须有 run(message) → AgentResult 方法
        """
        self._agent_loop_factory = agent_loop_factory
        self._tasks: Dict[str, A2ATask] = {}
        self._lock = threading.Lock()

    def create_task(self, params: dict) -> dict:
        """处理 tasks/send 请求"""
        task_id = params.get("id") or str(uuid.uuid4())
        message = params.get("message", {})
        # 提取消息文本
        text_parts = []
        for part in message.get("parts", []):
            if part.get("type") == "text":
                text_parts.append(part.get("text", ""))
        task_text = "\n".join(text_parts)

        task = A2ATask(task_id=task_id, agent_url="incoming", status="working")
        with self._lock:
            self._tasks[task_id] = task

        # 异步执行
        threading.Thread(
            target=self._execute_task, args=(task_id, task_text), daemon=True
        ).start()

        return {
            "id": task_id,
            "status": {"state": "working"},
        }

    def get_task(self, task_id: str) -> dict:
        """处理 tasks/get 请求"""
        with self._lock:
            task = self._tasks.get(task_id)
        if task is None:
            raise RuntimeError(f"Task not found: {task_id}")
        return {
            "id": task.task_id,
            "status": {"state": task.status, "message": task.message},
            "artifacts": task.artifacts,
        }

    def cancel_task(self, task_id: str) -> dict:
        """处理 tasks/cancel 请求"""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = "cancelled"
        return {"id": task_id, "status": {"state": "cancelled"}}

    def send_message(self, params: dict) -> dict:
        """处理 message/send 请求"""
        task_id = params.get("id", "")
        message = params.get("message", {})
        with self._lock:
            task = self._tasks.get(task_id)
        if task is None:
            raise RuntimeError(f"Task not found: {task_id}")
        # 追加消息到现有任务（简化实现：创建新子任务）
        text_parts = []
        for part in message.get("parts", []):
            if part.get("type") == "text":
                text_parts.append(part.get("text", ""))
        task.message = "\n".join(text_parts)
        return {"id": task_id, "status": {"state": task.status}}

    def _execute_task(self, task_id: str, message: str):
        """在后台线程执行任务"""
        try:
            if self._agent_loop_factory:
                agent = self._agent_loop_factory()
                result = agent.run(message)
                status = "completed" if result.success else "failed"
                summary = result.summary
            else:
                status = "failed"
                summary = "No agent loop factory configured"
        except Exception as e:
            status = "failed"
            summary = str(e)

        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.status = status
                task.message = summary
                task.artifacts = [{
                    "name": "result",
                    "parts": [{"type": "text", "text": summary}],
                }]

    def list_active_tasks(self) -> List[dict]:
        with self._lock:
            return [
                {"id": t.task_id, "status": t.status, "agent_url": t.agent_url}
                for t in self._tasks.values()
            ]


# ──────────────────────────────────────────────────────
# A2A 服务器
# ──────────────────────────────────────────────────────


class A2AServer:
    """
    轻量 HTTP 服务器，暴露 Agent Card 和 JSON-RPC 任务端点。
    在后台线程运行，不阻塞主线程。
    """

    def __init__(self):
        self._httpd: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._agent_card: Dict[str, Any] = {}
        self._task_handler: Optional[A2ATaskHandler] = None

    @property
    def port(self) -> Optional[int]:
        if self._httpd:
            return self._httpd.server_port
        return None

    @property
    def url(self) -> Optional[str]:
        if self._httpd and self.port:
            return f"http://localhost:{self.port}"
        return None

    def start(
        self,
        agent_card: AgentCard,
        task_handler: A2ATaskHandler = None,
        host: str = "0.0.0.0",
        port: int = None,
    ):
        """启动 A2A 服务器"""
        if self._running:
            return

        self._agent_card = agent_card.to_dict()
        self._task_handler = task_handler

        port = port or DEFAULT_PORT
        try:
            self._httpd = HTTPServer((host, port), A2ACardHandler)
        except OSError:
            port = _find_free_port()
            self._httpd = HTTPServer((host, port), A2ACardHandler)

        A2ACardHandler.agent_card_json = json.dumps(self._agent_card, ensure_ascii=False)
        self._httpd._task_handler = task_handler

        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        self._running = True
        logger.info("A2A server started on http://%s:%d", host, self._httpd.server_port)

    def stop(self):
        if self._httpd:
            self._httpd.shutdown()
            self._running = False
            logger.info("A2A server stopped")


# ──────────────────────────────────────────────────────
# A2A 客户端
# ──────────────────────────────────────────────────────


class A2AClient:
    """
    发现远程 A2A 智能体并委托任务。
    每个远程 agent 由一个 card_url 标识。
    """

    def __init__(self):
        self._remote_agents: Dict[str, Dict[str, Any]] = {}  # name → {card_url, card, timeout}
        self._active_tasks: Dict[str, A2ATask] = {}
        self._lock = threading.Lock()

    def configure_agent(self, name: str, card_url: str, timeout: int = DEFAULT_TIMEOUT):
        """注册一个远程 A2A 智能体"""
        self._remote_agents[name] = {"card_url": card_url, "card": None, "timeout": timeout}

    def discover_agent(self, name: str) -> Optional[AgentCard]:
        """获取远程智能体的 Agent Card（带缓存）"""
        agent = self._remote_agents.get(name)
        if not agent:
            return None
        if agent["card"]:
            return agent["card"]

        try:
            url = agent["card_url"]
            resp_data = _send_jsonrpc(url, "agent/card", timeout=10)
            # 如果直接 HTTP GET 拿到的是原始 card，_send_jsonrpc 可能失败
            # 改用简单 GET
            req = Request(url)
            resp = urlopen(req, timeout=10)
            data = json.loads(resp.read().decode("utf-8"))
            agent["card"] = AgentCard(**{k: v for k, v in data.items() if k in AgentCard.__dataclass_fields__})
            return agent["card"]
        except Exception as e:
            logger.warning("Failed to fetch Agent Card for '%s': %s", name, e)
            return None

    def list_agents(self) -> List[dict]:
        """列出所有已配置的远程智能体"""
        return [
            {
                "name": name,
                "card_url": a["card_url"],
                "timeout": a["timeout"],
                "connected": a["card"] is not None,
            }
            for name, a in self._remote_agents.items()
        ]

    def send_task(self, agent_name: str, message: str) -> dict:
        """
        向远程智能体发送任务，阻塞等待完成。

        返回:
          {"success": bool, "task_id": str, "result": str, "elapsed_seconds": float}
        """
        agent = self._remote_agents.get(agent_name)
        if not agent:
            return {"success": False, "error": f"Unknown remote agent: {agent_name}"}

        # 获取 Agent Card 以确认端点 URL
        card = self.discover_agent(agent_name)
        if not card:
            return {"success": False, "error": f"Cannot discover agent: {agent_name}"}

        base_url = card.url
        task_url = urljoin(base_url.rstrip("/") + "/", "")

        # 构造 A2A 消息
        params = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": message}],
            }
        }

        try:
            # 发送任务
            result = _send_jsonrpc(task_url, "tasks/send", params, timeout=agent["timeout"])
            task_id = result.get("id", "")

            # 轮询直到完成
            task = A2ATask(task_id=task_id, agent_url=base_url)
            started = time.monotonic()
            while True:
                poll_result = _send_jsonrpc(task_url, "tasks/get", {"id": task_id}, timeout=30)
                state = (poll_result.get("status") or {}).get("state", "working")
                task.poll_count += 1

                if state in ("completed", "failed", "cancelled"):
                    break
                if time.monotonic() - started > agent["timeout"]:
                    return {
                        "success": False,
                        "task_id": task_id,
                        "error": f"Task timed out after {agent['timeout']}s",
                    }
                time.sleep(min(2 ** task.poll_count, MAX_POLL_INTERVAL))

            elapsed = time.monotonic() - started
            artifacts = poll_result.get("artifacts", [])
            text_result = ""
            for art in artifacts:
                for part in art.get("parts", []):
                    if part.get("type") == "text":
                        text_result += part.get("text", "") + "\n"

            return {
                "success": state == "completed",
                "task_id": task_id,
                "result": text_result.strip() or poll_result.get("status", {}).get("message", ""),
                "elapsed_seconds": round(elapsed, 1),
                "poll_count": task.poll_count,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_task_async(self, agent_name: str, message: str, callback: Callable = None) -> str:
        """异步发送任务，立即返回 task_id，通过 callback 通知结果"""
        task_id = str(uuid.uuid4())
        threading.Thread(
            target=self._async_runner,
            args=(task_id, agent_name, message, callback),
            daemon=True,
        ).start()
        return task_id

    def _async_runner(self, task_id: str, agent_name: str, message: str, callback: Callable):
        result = self.send_task(agent_name, message)
        if callback:
            try:
                callback(task_id, result)
            except Exception as e:
                logger.error("A2A async callback error: %s", e)

    def get_task_status(self, agent_name: str, task_id: str) -> dict:
        """查询远程任务状态"""
        agent = self._remote_agents.get(agent_name)
        if not agent:
            return {"error": f"Unknown agent: {agent_name}"}
        card = self.discover_agent(agent_name)
        if not card:
            return {"error": f"Cannot discover: {agent_name}"}
        try:
            result = _send_jsonrpc(card.url, "tasks/get", {"id": task_id}, timeout=30)
            return {"id": task_id, "state": result.get("status", {}).get("state", "unknown")}
        except Exception as e:
            return {"error": str(e)}

    def cancel_task(self, agent_name: str, task_id: str) -> dict:
        """取消远程任务"""
        agent = self._remote_agents.get(agent_name)
        if not agent:
            return {"error": f"Unknown agent: {agent_name}"}
        card = self.discover_agent(agent_name)
        if not card:
            return {"error": f"Cannot discover: {agent_name}"}
        try:
            result = _send_jsonrpc(card.url, "tasks/cancel", {"id": task_id}, timeout=30)
            return {"cancelled": True, "task_id": task_id}
        except Exception as e:
            return {"error": str(e)}


# ──────────────────────────────────────────────────────
# 工具注册（供 iqra ToolRegistry 调用）
# ──────────────────────────────────────────────────────

# 模块级单例
_server: Optional[A2AServer] = None
_client: Optional[A2AClient] = None
_card_builder: Optional[AgentCardBuilder] = None


def get_client() -> A2AClient:
    global _client
    if _client is None:
        _client = A2AClient()
    return _client


def get_server() -> A2AServer:
    global _server
    if _server is None:
        _server = A2AServer()
    return _server


def register_a2a_tools(registry):
    """
    向 iqra ToolRegistry 注册 A2A 工具。

    Usage: 在 tools/business_tools.py 或 main.py 中调用:
        from tools.a2a_tool import register_a2a_tools
        register_a2a_tools(registry)
    """
    client = get_client()

    registry.register(
        name="a2a_discover_agents",
        description="发现并列出所有已配置的远程 A2A 智能体及其能力",
        parameters={
            "type": "object",
            "properties": {},
        },
        handler=lambda **kw: {"success": True, "agents": client.list_agents()},
        category="a2a",
    )

    registry.register(
        name="a2a_send_task",
        description="向指定的远程 A2A 智能体发送任务，阻塞等待完成。"
                    "agent_name 是已配置的智能体名，message 是任务描述文本。",
        parameters={
            "type": "object",
            "properties": {
                "agent_name": {"type": "string", "description": "远程智能体名称"},
                "message": {"type": "string", "description": "任务描述"},
            },
            "required": ["agent_name", "message"],
        },
        handler=lambda agent_name, message, **kw: client.send_task(agent_name, message),
        category="a2a",
    )

    registry.register(
        name="a2a_get_task",
        description="查询远程 A2A 智能体上的任务状态",
        parameters={
            "type": "object",
            "properties": {
                "agent_name": {"type": "string"},
                "task_id": {"type": "string"},
            },
            "required": ["agent_name", "task_id"],
        },
        handler=lambda agent_name, task_id, **kw: client.get_task_status(agent_name, task_id),
        category="a2a",
    )

    registry.register(
        name="a2a_cancel_task",
        description="取消远程 A2A 智能体上正在运行的任务",
        parameters={
            "type": "object",
            "properties": {
                "agent_name": {"type": "string"},
                "task_id": {"type": "string"},
            },
            "required": ["agent_name", "task_id"],
        },
        handler=lambda agent_name, task_id, **kw: client.cancel_task(agent_name, task_id),
        category="a2a",
    )

    logger.info("A2A tools registered (a2a_discover_agents, a2a_send_task, a2a_get_task, a2a_cancel_task)")


# ──────────────────────────────────────────────────────
# 启动/停止入口
# ──────────────────────────────────────────────────────


def start_a2a_server(
    name: str = "Iqra Agent",
    description: str = "AI-powered coding and system agent",
    version: str = "3.0.0",
    host: str = "0.0.0.0",
    port: int = None,
    tool_registry=None,
    skill_loader=None,
    agent_loop_factory: Callable = None,
) -> A2AServer:
    """
    启动 A2A 服务器：发布 Agent Card + JSON-RPC 任务端点。

    调用时机：iqra main.py 初始化完成后。
    """
    server = get_server()
    if server._running:
        return server

    port = port or DEFAULT_PORT
    url = f"http://localhost:{port}"

    builder = AgentCardBuilder(tool_registry=tool_registry, skill_loader=skill_loader)
    card = builder.build(name=name, description=description, url=url, version=version)

    task_handler = A2ATaskHandler(agent_loop_factory=agent_loop_factory)
    server.start(agent_card=card, task_handler=task_handler, host=host, port=port)
    return server


def configure_remote_agents(agents_config: dict):
    """
    配置远程 A2A 智能体。

    agents_config = {
        "file_helper": {"card_url": "https://.../agent.json", "timeout": 300},
        ...
    }
    """
    client = get_client()
    for name, cfg in agents_config.items():
        client.configure_agent(
            name=name,
            card_url=cfg.get("card_url", ""),
            timeout=cfg.get("timeout", DEFAULT_TIMEOUT),
        )
    logger.info("Configured %d remote A2A agent(s)", len(agents_config))

```
