# `iqra/core/prompts/task_decompose.py`

> 路径：`iqra/core/prompts/task_decompose.py` | 行数：99


---


```python
# -*- coding: utf-8 -*-
"""
任务分解 Prompt 模板

将用户自然语言任务拆解为原子工具调用步骤。
每个步骤对应一个工具调用，步骤间按顺序执行。
"""

TASK_DECOMPOSE_SYSTEM_PROMPT = """你是一个任务分解器。将用户任务拆解为原子工具调用步骤。

## 规则

1. 每个步骤必须是单个原子操作，对应一次工具调用
2. 步骤按执行顺序排列（上一步输出可能是下一步输入）
3. step_id 从 1 开始递增
4. tool_name 必须从可用工具列表中选择
5. arguments 必须是有效的 JSON 对象，包含该工具所需的参数
6. reason 用一句话解释为什么需要这一步
7. 简单任务（如"列出文件"）只需 1 步；复杂任务（如"读合同 + 提取信息 + 写摘要"）拆成 3-5 步
8. 输出纯 JSON 数组，无额外文字，无 markdown 代码块标记

## 可用工具

{tools_description}

## 输出格式

[
  {{
    "step_id": 1,
    "tool_name": "read_file",
    "arguments": {{"file_path": "/path/to/file.pdf"}},
    "reason": "读取合同文件获取原始内容"
  }},
  {{
    "step_id": 2,
    "tool_name": "write_file",
    "arguments": {{"file_path": "/path/to/output.txt", "content": "..."}},
    "reason": "将分析结果写入输出文件"
  }}
]
"""


def build_tools_description(tool_schemas: list) -> str:
    """
    从工具 schema 列表构建可读的工具描述字符串

    Args:
        tool_schemas: 工具 schema 列表，每项为 {name, description, parameters}

    Returns:
        格式化的工具描述文本
    """
    if not tool_schemas:
        return "（无可用工具）"

    lines = []
    for i, schema in enumerate(tool_schemas, 1):
        name = schema.get("name", f"tool_{i}")
        desc = schema.get("description", "无描述")
        params = schema.get("parameters", {})

        lines.append(f"### {i}. {name}")
        lines.append(f"描述: {desc}")

        props = params.get("properties", {})
        required = params.get("required", [])
        if props:
            lines.append("参数:")
            for pname, pinfo in props.items():
                req_mark = " (必需)" if pname in required else " (可选)"
                ptype = pinfo.get("type", "string")
                pdesc = pinfo.get("description", "")
                lines.append(f"  - {pname}: {ptype}{req_mark} — {pdesc}")

        lines.append("")

    return "\n".join(lines)


def format_decompose_messages(goal: str, tool_schemas: list) -> list:
    """
    构建完整的 LLM 消息列表用于任务分解

    Args:
        goal: 用户任务描述
        tool_schemas: 可用工具的 schema 列表

    Returns:
        messages 列表 [{"role": "system", "content": ...}, {"role": "user", "content": ...}]
    """
    tools_desc = build_tools_description(tool_schemas)
    system = TASK_DECOMPOSE_SYSTEM_PROMPT.format(tools_description=tools_desc)

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": f"请拆解以下任务：\n\n{goal}"},
    ]

```
