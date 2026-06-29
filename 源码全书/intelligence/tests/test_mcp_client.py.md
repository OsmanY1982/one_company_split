# `intelligence/tests/test_mcp_client.py`

> 路径：`intelligence/tests/test_mcp_client.py` | 行数：74


---


```python
"""
集成测试 — 验证 McpClientManager 完整工作流
  1. 配置测试 MCP 服务器
  2. 连接并验证握手
  3. 注册工具到 ToolRegistry
  4. 调用工具验证端到端通路
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from intelligence.mcp_client import McpClientManager, McpServerConfig
from iqra.core.tool_registry import ToolRegistry


def test_mcp_manager():
    # ── 1. 配置测试服务器 ──
    manager = McpClientManager()
    test_server = os.path.join(os.path.dirname(__file__), 'mcp_test_server.py')

    manager.configure({
        "test": {
            "command": sys.executable,
            "args": [test_server],
            "prefix": "t_",
            "timeout": 10.0,
        }
    })

    # ── 2. 连接 ──
    results = manager.connect_all()
    assert results["test"], f"连接失败: {manager._connections['test']._last_error}"
    print(f"[PASS] 连接成功，{manager._connections['test'].tools.__len__()} 个工具")

    # ── 3. 注册到 ToolRegistry ──
    registry = ToolRegistry()
    count = manager.register_all(registry)
    assert count["test"] == 3, f"应注册 3 个工具，实际 {count['test']}"
    print(f"[PASS] 注册成功: {count}")

    # ── 4. 调用工具 ──
    # echo
    r = manager.call_tool("t_echo", {"text": "Hello!"})
    assert r["success"], f"echo 失败: {r.get('error')}"
    assert "ECHO: Hello!" in r["result"], f"echo 结果不对: {r['result']}"
    print(f"[PASS] echo: {r['result']}")

    # add
    r = manager.call_tool("t_add", {"a": 10, "b": 25})
    assert r["success"], f"add 失败: {r.get('error')}"
    assert "35" in r["result"], f"add 结果不对: {r['result']}"
    print(f"[PASS] add: {r['result']}")

    # list_files（测试目录）
    r = manager.call_tool("t_list_files", {"path": "."})
    assert r["success"], f"list_files 失败: {r.get('error')}"
    assert len(r["result"]) > 0, f"应该能列出文件"
    print(f"[PASS] list_files: 成功列出文件")

    # ── 5. 查看状态 ──
    status = manager.get_status()
    assert status["test"]["connected"], "应显示已连接"
    print(f"[PASS] 状态: {status}")

    # ── 6. 断开 ──
    manager.disconnect_all()
    status = manager.get_status()
    assert not status["test"]["connected"], "应显示已断开"
    print(f"[PASS] 断开成功")

    print("\n✅ 全部测试通过")


if __name__ == "__main__":
    test_mcp_manager()

```
