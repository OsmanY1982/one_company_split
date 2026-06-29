# `intelligence/mcp_client.py`

> 路径：`intelligence/mcp_client.py` | 行数：363


---


```python
"""
MCP Client（纯 stdio + JSON-RPC 实现）

避免 mcp SDK 的 async context manager 与 asyncio.run() 兼容性问题，
直接通过子进程 stdio + JSON-RPC 2.0 协议与 MCP 服务器通信。
兼容标准 MCP 协议（initialize / tools/list / tools/call）。
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── 配置 ──

@dataclass
class McpServerConfig:
    command: str
    args: List[str] = field(default_factory=list)
    env: Optional[Dict[str, str]] = None
    cwd: Optional[str] = None
    prefix: str = ""
    timeout: float = 30.0

# ── JSON-RPC 2.0 消息 ──

def _make_request(method: str, params: dict = None, req_id: int = 1) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": method,
        "params": params or {},
    }

def _make_notification(method: str, params: dict = None) -> dict:
    return {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
    }

# ── 连接 ──

class McpConnection:
    """管理单个 MCP 服务器的 stdio 连接和 JSON-RPC 通信"""

    def __init__(self, name: str, config: McpServerConfig):
        self.name = name
        self.config = config
        self._proc: Optional[subprocess.Popen] = None
        self._tools: Dict[str, dict] = {}
        self._connected = False
        self._lock = threading.Lock()
        self._next_id = 1
        self._error_count = 0
        self._last_error: Optional[str] = None
        self._server_info: dict = {}

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def tools(self) -> Dict[str, dict]:
        return self._tools.copy()

    # ── 连接 ──

    def connect(self) -> bool:
        with self._lock:
            if self._connected:
                return True
            try:
                self._do_connect()
                self._connected = True
                self._error_count = 0
                logger.info("MCP[%s]: 连接成功，%d 个工具", self.name, len(self._tools))
                return True
            except Exception as e:
                self._connected = False
                self._error_count += 1
                self._last_error = f"{type(e).__name__}: {e}"
                logger.error("MCP[%s]: 连接失败 - %s", self.name, self._last_error)
                self._cleanup()
                return False

    def _do_connect(self) -> None:
        env = os.environ.copy()
        if self.config.env:
            env.update(self.config.env)
        env.setdefault("PYTHONUNBUFFERED", "1")

        self._proc = subprocess.Popen(
            [self.config.command] + self.config.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=self.config.cwd,
            text=True,
            bufsize=1,
        )
        self._next_id = 1

        # MCP 握手：initialize
        init_rsp = self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "iqra-mcp-client", "version": "1.0"},
        })
        self._server_info = init_rsp.get("result", {}).get("serverInfo", {})

        # 发送 initialized 通知
        self._send_notification("notifications/initialized")

        # 获取工具列表
        tools_rsp = self._send_request("tools/list")
        tool_list = tools_rsp.get("result", {}).get("tools", [])
        for t in tool_list:
            self._tools[t["name"]] = {
                "name": t["name"],
                "description": t.get("description", ""),
                "inputSchema": t.get("inputSchema", {"type": "object", "properties": {}}),
            }

    def disconnect(self) -> None:
        with self._lock:
            self._connected = False
            self._tools.clear()
            self._cleanup()

    def _cleanup(self) -> None:
        if self._proc:
            try:
                self._proc.stdin.close()
                self._proc.stdout.close()
                self._proc.stderr.close()
                self._proc.terminate()
                self._proc.wait(timeout=3)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None

    # ── JSON-RPC 通信 ──

    def _send_request(self, method: str, params: dict = None, timeout: float = None) -> dict:
        req_id = self._next_id
        self._next_id += 1
        return self._rpc_call(_make_request(method, params, req_id), timeout or self.config.timeout)

    def _send_notification(self, method: str, params: dict = None) -> None:
        """发送 JSON-RPC 通知（无 id，不等待响应）"""
        msg = _make_notification(method, params)
        if self._proc is None or self._proc.poll() is not None:
            raise RuntimeError(f"MCP[{self.name}]: 进程未运行")
        payload = json.dumps(msg, ensure_ascii=False) + "\n"
        self._proc.stdin.write(payload)
        self._proc.stdin.flush()

    def _rpc_call(self, msg: dict, timeout: float) -> dict:
        if self._proc is None or self._proc.poll() is not None:
            raise RuntimeError(f"MCP[{self.name}]: 进程未运行")

        payload = json.dumps(msg, ensure_ascii=False) + "\n"
        try:
            self._proc.stdin.write(payload)
            self._proc.stdin.flush()
        except BrokenPipeError:
            raise RuntimeError(f"MCP[{self.name}]: stdin 已关闭（进程可能已崩溃）")

        # 读取响应（单行 JSON）
        try:
            line = self._proc.stdout.readline()
            if not line:
                raise RuntimeError(f"MCP[{self.name}]: stdout 关闭（进程退出码 {self._proc.poll()}）")
        except Exception as e:
            raise RuntimeError(f"MCP[{self.name}]: 读取响应失败 - {e}")

        try:
            rsp = json.loads(line)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"MCP[{self.name}]: JSON 解析失败 - {e}，原始数据: {line[:200]}")

        if "error" in rsp:
            err = rsp["error"]
            raise RuntimeError(f"MCP[{self.name}]: 服务器错误 [{err.get('code', '?')}] {err.get('message', '?')}")

        return rsp

    # ── 工具调用 ──

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        try:
            rsp = self._send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments,
            })
            content = rsp.get("result", {}).get("content", [])
            texts = []
            for item in content:
                texts.append(item.get("text", str(item)))

            return {
                "success": not rsp.get("result", {}).get("isError", False),
                "result": "\n".join(texts) if len(texts) == 1 else texts,
                "tool": tool_name,
                "server": self.name,
            }
        except Exception as e:
            logger.error("MCP[%s]: 调用 %s 失败 - %s", self.name, tool_name, e)
            return {
                "success": False,
                "error": f"MCP 工具调用失败: {e}",
                "tool": tool_name,
            }


# ── 管理器 ──

class McpClientManager:
    """多 MCP 服务器管理器"""

    def __init__(self):
        self._servers: Dict[str, McpServerConfig] = {}
        self._connections: Dict[str, McpConnection] = {}
        self._tool_map: Dict[str, str] = {}

    def configure(self, servers: Dict[str, dict]) -> None:
        for name, cfg in servers.items():
            self._servers[name] = McpServerConfig(**cfg) if isinstance(cfg, dict) else cfg

    def configure_server(self, name: str, config: McpServerConfig | dict) -> None:
        self._servers[name] = McpServerConfig(**config) if isinstance(config, dict) else config

    def connect_all(self) -> Dict[str, bool]:
        results = {}
        for name in self._servers:
            conn = McpConnection(name, self._servers[name])
            self._connections[name] = conn
            results[name] = conn.connect()
        return results

    def connect_server(self, name: str) -> bool:
        if name not in self._servers:
            return False
        conn = McpConnection(name, self._servers[name])
        self._connections[name] = conn
        return conn.connect()

    def register_all(self, registry: Any) -> Dict[str, int]:
        results = {}
        for name, conn in self._connections.items():
            count = self._register_server_tools(name, conn, registry)
            results[name] = count
        return results

    def _register_server_tools(self, server_name: str, conn: McpConnection, registry: Any) -> int:
        prefix = conn.config.prefix or f"mcp_{server_name}_"
        count = 0

        from iqra.core._backend_models import ToolDefinition

        for mcp_name, mcp_tool in conn.tools.items():
            iqra_name = f"{prefix}{mcp_name}"
            desc = mcp_tool["description"] or f"MCP 工具: {mcp_name}（{server_name}）"

            tool_def = ToolDefinition(
                name=iqra_name,
                description=desc,
                parameters=mcp_tool["inputSchema"],
                handler=self._make_handler(server_name, mcp_name),
                category="mcp",
            )
            registry.add_tool(tool_def, category="mcp")
            self._tool_map[iqra_name] = server_name
            count += 1

        logger.info("MCP[%s]: 注册 %d 个工具", server_name, count)
        return count

    def _make_handler(self, server_name: str, tool_name: str):
        def handler(**kwargs):
            return self.call_tool(f"{self._servers[server_name].prefix or f'mcp_{server_name}_'}{tool_name}", kwargs)
        return handler

    def call_tool(self, iqra_name: str, arguments: dict) -> dict:
        server_name = self._tool_map.get(iqra_name)
        if not server_name:
            return {"success": False, "error": f"MCP 工具未找到: {iqra_name}"}
        conn = self._connections.get(server_name)
        if not conn or not conn.is_connected:
            if not self.connect_server(server_name):
                return {"success": False, "error": f"MCP 服务器 {server_name} 不可用"}
            conn = self._connections[server_name]
        prefix = self._servers[server_name].prefix or f"mcp_{server_name}_"
        return conn.call_tool(iqra_name[len(prefix):], arguments)

    def disconnect_all(self) -> None:
        for conn in self._connections.values():
            conn.disconnect()
        self._connections.clear()
        self._tool_map.clear()

    def get_status(self) -> Dict[str, Any]:
        return {
            name: {
                "configured": True,
                "connected": self._connections[name].is_connected if name in self._connections else False,
                "tool_count": len(self._connections[name].tools) if name in self._connections else 0,
                "registered": sum(1 for t, s in self._tool_map.items() if s == name),
                "last_error": self._connections[name]._last_error if name in self._connections else None,
                "server_info": self._connections[name]._server_info if name in self._connections else {},
            }
            for name in self._servers
        }

    def list_tools(self) -> Dict[str, List[str]]:
        result = {}
        for name, conn in self._connections.items():
            prefix = conn.config.prefix or f"mcp_{name}_"
            result[name] = [f"{prefix}{t}" for t in conn.tools]
        return result


# ── 预设配置 ──

def create_default_config() -> Dict[str, dict]:
    return {
        "filesystem": {
            "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
            "prefix": "fs_",
        },
        "github": {
            "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "<YOUR_TOKEN>"},
            "prefix": "github_",
        },
        "postgres": {
            "command": "npx", "args": ["-y", "@modelcontextprotocol/server-postgres"],
            "env": {"DATABASE_URL": "<YOUR_DB_URL>"},
            "prefix": "pg_",
        },
        "sqlite": {
            "command": "uvx", "args": ["mcp-server-sqlite", "--db-path", "./data.db"],
            "prefix": "sqlite_",
        },
        "brave_search": {
            "command": "npx", "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env": {"BRAVE_API_KEY": "<YOUR_KEY>"},
            "prefix": "brave_",
        },
    }

```
