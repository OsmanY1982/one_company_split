# `iqra/core/_test_llm_decompose.py`

> 路径：`iqra/core/_test_llm_decompose.py` | 行数：328


---


```python
# -*- coding: utf-8 -*-
"""
第 4 步验证：LLM 任务拆解 vs 机械规则回退

测试三个不同复杂度任务，每个跑两遍：
  - 一遍开启 LLM 拆解（use_llm_decompose=True）
  - 一遍关闭 LLM 拆解（回退机械规则）

运行方式:
    cd /Volumes/D盘工作区/一人公司
    python -m iqra.core._test_llm_decompose
"""

import sys
import os
import json
import time
import uuid
from pathlib import Path

# 确保项目根目录在 path 中
_PROJECT_ROOT = Path("/Volumes/D盘工作区/一人公司")
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def create_dummy_tool_registry():
    """创建包含基本工具的模拟 ToolRegistry"""
    from iqra.core.tool_registry import ToolRegistry
    from iqra.core.llm_backend import ToolDefinition

    registry = ToolRegistry("test_registry")

    # 手动注册 7 个基础工具（ToolRegistry.register 是装饰器，我们用 add_tool）
    tools_defs = [
        ToolDefinition(
            name="read_file",
            description="读取文本文件内容",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "limit": {"type": "integer", "description": "最大读取行数", "default": 100},
                },
                "required": ["path"],
            },
            handler=lambda path, limit=100: {"content": f"mock read {path}"},
        ),
        ToolDefinition(
            name="write_file",
            description="写入内容到文件",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "文件内容"},
                },
                "required": ["path", "content"],
            },
            handler=lambda path, content: {"success": True, "path": path},
        ),
        ToolDefinition(
            name="edit_file",
            description="编辑文件",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "old_text": {"type": "string", "description": "原始文本"},
                    "new_text": {"type": "string", "description": "新文本"},
                },
                "required": ["path", "old_text", "new_text"],
            },
            handler=lambda path, old_text, new_text: {"success": True},
        ),
        ToolDefinition(
            name="execute_shell",
            description="执行 Shell 命令",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的命令"},
                },
                "required": ["command"],
            },
            handler=lambda command: {"stdout": f"mock exec: {command}"},
        ),
        ToolDefinition(
            name="execute_code",
            description="执行 Python 代码",
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python 代码"},
                    "timeout": {"type": "integer", "description": "超时秒数", "default": 30},
                },
                "required": ["code"],
            },
            handler=lambda code, timeout=30: {"stdout": "mock result"},
        ),
        ToolDefinition(
            name="search_files",
            description="搜索文件",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                },
                "required": ["query"],
            },
            handler=lambda query: {"results": [], "query": query},
        ),
        ToolDefinition(
            name="list_directory",
            description="列出目录下的文件",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "目录路径"},
                },
                "required": ["path"],
            },
            handler=lambda path: {"files": [], "path": path},
        ),
    ]

    for td in tools_defs:
        registry.add_tool(td)

    return registry


def create_dummy_engine():
    """创建模拟 ChatEngine（用于测试）"""
    from iqra.core.chat_engine import ChatEngine
    from iqra.core.llm_backend import create_backend, BackendFactory

    registry = create_dummy_tool_registry()

    # 尝试创建 Ollama 后端
    try:
        config = BackendFactory.create_for_ollama(
            model="qwen2.5:7b",
            base_url="http://localhost:11434",
        )
        backend = create_backend(config)
        print("  LLM 后端: Ollama qwen2.5:7b (可用)")
    except Exception:
        backend = None
        print("  LLM 后端: 不可用（将走机械规则回退）")

    engine = ChatEngine(backend=backend, registry=registry) if backend else None
    return engine, backend


# ═══════════════════════════════════════════
# 测试用例
# ═══════════════════════════════════════════

TEST_CASES = [
    {
        "name": "简单: 列出 /tmp 下的文件",
        "task": "列出 /tmp 下的文件",
        "expected_steps": 1,
        "expected_tools": ["list_directory", "execute_shell"],
    },
    {
        "name": "中等: 读取 MD 提取任务存为摘要",
        "task": "读取 15-优化工作流.md，提取第四档的 4 项任务，存为 summary.txt",
        "expected_steps": 3,
        "expected_tools": ["read_file", "write_file"],
    },
    {
        "name": "复杂: 读取合同 PDF 提取关键条款写摘要",
        "task": "读取合同 PDF，提取关键条款（金额、期限、违约责任），写 200 字中文摘要",
        "expected_steps": 3,
        "expected_tools": ["read_file", "write_file", "execute_code"],
    },
]


def run_decompose_test(case: dict, engine, backend):
    """对单个测试用例执行 LLM 拆解"""

    from iqra.core.task_decomposer import TaskDecomposer

    start = time.time()

    tool_schemas = []
    try:
        tools = engine.registry.to_openai_tools()
        for t in tools:
            tool_schemas.append({
                "name": t.get("function", {}).get("name", ""),
                "description": t.get("function", {}).get("description", ""),
                "parameters": t.get("function", {}).get("parameters", {}),
            })
    except Exception:
        pass

    decomposer = TaskDecomposer(backend)
    steps = decomposer.decompose(case["task"], available_tools=tool_schemas)

    elapsed = time.time() - start
    step_count = len(steps)

    print(f"\n  {'='*50}")
    print(f"  任务: {case['name']}")
    print(f"  描述: {case['task'][:80]}...")
    print(f"  耗时: {elapsed:.2f}s")
    print(f"  拆解步数: {step_count} (期望: ~{case['expected_steps']})")

    tools_used = [s.tool_name for s in steps]
    matched = any(t in tools_used for t in case.get("expected_tools", []))
    print(f"  工具: {tools_used} (期望含: {case['expected_tools']})")

    if matched and 0.5 * case["expected_steps"] <= step_count <= 3 * case["expected_steps"]:
        print(f"  质量: OK ({'LLM 语义' if backend else '机械规则回退'})")
    else:
        print(f"  质量: 偏差 (步数 {step_count} vs 期望 ~{case['expected_steps']})")

    for s in steps:
        print(f"    [{s.step_id}] {s.tool_name}: {s.reason[:60]}")

    return {
        "case": case["name"],
        "task": case["task"],
        "elapsed": elapsed,
        "steps": step_count,
        "tools": tools_used,
        "matched": matched,
        "backend_available": backend is not None,
    }


def run_fallback_test(case: dict, backend):
    """强制走机械规则回退"""
    from iqra.core.task_decomposer import _fallback_decompose
    from iqra.core.llm_backend import ToolDefinition

    # 构建模拟 tool_schemas（不含 LLM，纯机械匹配）
    registry = create_dummy_tool_registry()
    tools = registry.to_openai_tools()
    tool_schemas = []
    for t in tools:
        name = t.get("function", {}).get("name", "")
        if name:  # 只取名字，机械规则只需要名字集合
            tool_schemas.append({"name": name, "description": "", "parameters": {}})

    start = time.time()
    steps = _fallback_decompose(case["task"], tool_schemas)
    elapsed = time.time() - start

    print(f"\n  回退模式 — {case['name']}")
    print(f"  耗时: {elapsed:.2f}s")
    print(f"  拆解步数: {len(steps)} (机械规则总是 1 步)")
    for s in steps:
        print(f"    [{s.step_id}] {s.tool_name}: {s.reason[:60]}")

    return {
        "case": case["name"],
        "elapsed": elapsed,
        "steps": len(steps),
        "mode": "fallback",
    }


# ═══════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════

def main():
    print("=" * 60)
    print("LLM 任务拆解 vs 机械规则回退 — 对比验证")
    print("=" * 60)

    # 1. 准备引擎
    print("\n[准备] 创建测试引擎...")
    engine, backend = create_dummy_engine()

    if engine is None:
        print("  ERROR: 无法创建 ChatEngine（需要至少一个可用 LLM 后端）")
        print("  降级为纯机械规则测试...")

    # 2. LLM 拆解
    llm_results = []
    if engine and backend:
        print("\n\n[阶段 1] LLM 语义拆解测试")
        print("-" * 40)
        for case in TEST_CASES:
            result = run_decompose_test(case, engine, backend)
            llm_results.append(result)
    else:
        print("\n\n[阶段 1] LLM 语义拆解 — 跳过（无可用后端）")

    # 3. 机械规则回退
    print("\n\n[阶段 2] 机械规则回退测试")
    print("-" * 40)
    fallback_results = []
    for case in TEST_CASES:
        result = run_fallback_test(case, backend)
        fallback_results.append(result)

    # 4. 汇总
    print("\n\n" + "=" * 60)
    print("汇总对比")
    print("=" * 60)

    print(f"\n{'任务':<30} {'LLM步数':>8} {'回退步数':>8} {'期望步数':>8}")
    print("-" * 60)
    for i, case in enumerate(TEST_CASES):
        llm_steps = llm_results[i]["steps"] if i < len(llm_results) else "N/A"
        fb_steps = fallback_results[i]["steps"]
        exp = case["expected_steps"]
        print(f"{case['name']:<30} {str(llm_steps):>8} {fb_steps:>8} {exp:>8}")

    # 输出完整 JSON 结果供调度者参考
    output_path = Path("/Volumes/D盘工作区/一人公司拆分版/one_company_split/iqra/core/_test_llm_decompose_results.json")
    full_results = {"llm": llm_results, "fallback": fallback_results, "test_cases": TEST_CASES}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(full_results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n完整结果已写入: {output_path}")

    print("\n完成。")


if __name__ == "__main__":
    main()

```
