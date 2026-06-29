"""
MCP 测试服务器 — 提供 echo / add / list_files 三个示例工具，
用于验证 MCP Client 的 stdio 传输和工具调用通路。
（兼容 mcp >= 1.28.0）
"""
import json
import os
import sys
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

server = Server("test-mcp-server")


@server.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="echo",
            description="回显输入文本",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "要回显的文本"}
                },
                "required": ["text"],
            },
        ),
        types.Tool(
            name="add",
            description="计算两数之和",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "第一个数"},
                    "b": {"type": "number", "description": "第二个数"},
                },
                "required": ["a", "b"],
            },
        ),
        types.Tool(
            name="list_files",
            description="列出目录下的文件",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "目录路径"}
                },
                "required": ["path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "echo":
        text = arguments.get("text", "")
        return [{"type": "text", "text": f"ECHO: {text}"}]
    
    elif name == "add":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        return [{"type": "text", "text": f"SUM: {a} + {b} = {a + b}"}]
    
    elif name == "list_files":
        path = arguments.get("path", ".")
        try:
            files = os.listdir(path)
            return [{"type": "text", "text": json.dumps(files[:20], indent=2, ensure_ascii=False)}]
        except Exception as e:
            return [{"type": "text", "text": f"ERROR: {e}"}]

    else:
        return [{"type": "text", "text": f"Unknown tool: {name}"}]


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
