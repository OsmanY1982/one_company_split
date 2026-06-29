# `iqra/core/task_decomposer.py`

> 路径：`iqra/core/task_decomposer.py` | 行数：318


---


```python
# -*- coding: utf-8 -*-
"""
TaskDecomposer — LLM 驱动的任务步骤拆解器

将用户自然语言任务拆解为原子工具调用步骤列表。
与 agent_delegate.py 中的 LLMDecomposer 不同：
  - agent_delegate.py 的分解是基于 handler（业务处理器）粒度的
  - 本模块的分解是基于 tool（底层工具）粒度的，直接生成步骤序列

用法:
    from iqra.core.task_decomposer import TaskDecomposer, SubTaskStep

    decomposer = TaskDecomposer(backend)
    steps = decomposer.decompose(
        task="读取合同 PDF，提取关键条款，写 200 字摘要",
        available_tools=tool_schemas,
    )
    # → [SubTaskStep(step_id=1, tool_name="read_file", ...),
    #    SubTaskStep(step_id=2, tool_name="write_file", ...)]
"""

import json
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from .iqra_logging import logger
from .prompts.task_decompose import format_decompose_messages


# ═══════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════

@dataclass
class SubTaskStep:
    """单个子任务步骤"""
    step_id: int
    tool_name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SubTaskStep":
        return cls(
            step_id=int(d.get("step_id", 0)),
            tool_name=str(d.get("tool_name", "")),
            arguments=d.get("arguments", {}) if isinstance(d.get("arguments"), dict) else {},
            reason=str(d.get("reason", "")),
        )


# ═══════════════════════════════════════════
# 机械规则回退（LLM 不可用时）
# ═══════════════════════════════════════════

# 简单关键词 → 工具映射
_KEYWORD_TOOL_MAP = [
    (r"列出|查看.*文件|ls |dir |list", "list_directory"),
    (r"读取|read|查看.*内容|打开.*看", "read_file"),
    (r"写入|write|保存|另存为|输出到", "write_file"),
    (r"编辑|修改|替换.*内容|edit", "edit_file"),
    (r"搜索.*文件|查找.*文件|找.*文件|search.*file", "search_files"),
    (r"搜索.*代码|grep|find.*code", "search_code"),
    (r"执行|运行|shell|命令|终端", "execute_shell"),
    (r"删除|移除|delete|remove", "delete_file"),
    (r"git|提交|commit|push|pull", "git_operation"),
    (r"合并.*PDF|merge.*pdf", "merge_pdf"),
    (r"转换成|convert|格式转换", "convert_file"),
    (r"测试|test|pytest", "run_tests"),
]


def _fallback_decompose(task: str, tool_schemas: list) -> List[SubTaskStep]:
    """
    LLM 不可用时使用机械规则拆解任务

    策略：
      1. 匹配关键词确定工具
      2. 尝试从任务描述中提取参数（文件路径、搜索词等）
      3. 返回单步 SubTaskStep

    Args:
        task: 用户任务描述
        tool_schemas: 可用工具 schema 列表

    Returns:
        单步 SubTaskStep 列表
    """
    tool_names = {s.get("name", "") for s in tool_schemas} if tool_schemas else set()

    matched_tool = None
    for pattern, tool_name in _KEYWORD_TOOL_MAP:
        if re.search(pattern, task, re.IGNORECASE):
            if tool_name in tool_names:
                matched_tool = tool_name
                break

    if not matched_tool:
        # 默认使用第一个可用工具，或 read_file
        matched_tool = "read_file" if "read_file" in tool_names else (tool_names.pop() if tool_names else "execute_shell")

    # 尝试提取文件路径
    file_path = ""
    path_match = re.search(r'["\']?([/\w.\\-]+\.\w{2,5})["\']?', task)
    if path_match:
        file_path = path_match.group(1)

    args = {}
    if matched_tool in ("read_file", "write_file", "edit_file", "delete_file", "convert_file"):
        if file_path:
            args["file_path"] = file_path
    elif matched_tool == "search_files":
        # 提取搜索关键词
        query_match = re.search(r'["\']([^"\']+)["\']', task)
        if query_match:
            args["query"] = query_match.group(1)
        else:
            # 用任务描述去掉动词部分
            clean = re.sub(r'^(搜索|查找|找|search)\s*', '', task, flags=re.IGNORECASE)
            args["query"] = clean.strip()
    elif matched_tool == "execute_shell":
        args["command"] = task

    step = SubTaskStep(
        step_id=1,
        tool_name=matched_tool,
        arguments=args,
        reason=f"机械规则回退: 匹配关键词 '{matched_tool}'",
    )

    logger.info("TaskDecomposer: LLM 不可用，回退到机械规则，匹配工具 '%s'", matched_tool)
    return [step]


# ═══════════════════════════════════════════
# LLM 驱动的 TaskDecomposer
# ═══════════════════════════════════════════

class TaskDecomposer:
    """
    LLM 驱动的任务步骤拆解器

    调用 LLM 将自然语言任务拆解为有序的工具调用步骤列表。
    LLM 不可用时自动降级到机械关键词匹配。

    用法:
        decomposer = TaskDecomposer(backend)
        steps = decomposer.decompose(
            task="读取 15-优化工作流.md，提取第四档的 4 项任务，存为 summary.txt",
            available_tools=tool_schemas,
        )
        for step in steps:
            print(f"步骤 {step.step_id}: {step.tool_name} — {step.reason}")
    """

    # 最大 LLM 响应长度（字符）
    MAX_RESPONSE_CHARS = 4000

    def __init__(self, backend=None):
        """
        Args:
            backend: BaseLLMBackend 实例。为 None 时始终走机械规则回退。
        """
        self._backend = backend
        self._available = backend is not None

    @property
    def is_available(self) -> bool:
        """LLM 后端是否可用"""
        return self._available and self._backend is not None

    def decompose(
        self,
        task: str,
        available_tools: list = None,
        context: str = "",
    ) -> List[SubTaskStep]:
        """
        将用户任务拆解为有序的 SubTaskStep 列表

        Args:
            task: 用户任务描述（自然语言）
            available_tools: 可用工具的 schema 列表，每项为 {name, description, parameters}
            context: 额外上下文（暂未使用，预留）

        Returns:
            有序的 SubTaskStep 列表。LLM 不可用时返回单步回退列表。
        """
        tool_schemas = available_tools or []

        if not self.is_available:
            return _fallback_decompose(task, tool_schemas)

        try:
            messages = format_decompose_messages(task, tool_schemas)
            response = self._backend.chat(messages)
            content = response.content.strip() if hasattr(response, 'content') else str(response).strip()

            steps = self._parse_response(content)
            if steps:
                logger.info("TaskDecomposer: LLM 拆解成功，共 %d 步", len(steps))
                return steps

        except Exception as e:
            logger.warning("TaskDecomposer: LLM 拆解失败: %s", e)

        # 回退
        return _fallback_decompose(task, tool_schemas)

    def _parse_response(self, content: str) -> Optional[List[SubTaskStep]]:
        """
        解析 LLM 响应，提取并校验 JSON 步骤列表

        Args:
            content: LLM 原始响应文本

        Returns:
            校验后的 SubTaskStep 列表，解析失败返回 None
        """
        if not content:
            return None

        # 去除可能的 markdown 代码块标记
        json_str = content
        if "```" in json_str:
            parts = json_str.split("```")
            # 取第一个代码块的内容
            for i, part in enumerate(parts):
                if i % 2 == 1:  # 奇数索引是代码块内容
                    if part.startswith("json"):
                        part = part[4:]
                    json_str = part.strip()
                    break

        # 尝试提取 JSON 数组
        try:
            raw = json.loads(json_str)
        except json.JSONDecodeError:
            # 尝试用正则提取 JSON 数组
            match = re.search(r'\[.*\]', json_str, re.DOTALL)
            if match:
                try:
                    raw = json.loads(match.group(0))
                except json.JSONDecodeError:
                    return None
            else:
                return None

        if not isinstance(raw, list) or len(raw) == 0:
            return None

        # 校验并构建 SubTaskStep
        steps = []
        for item in raw:
            if not isinstance(item, dict):
                continue

            step_id = item.get("step_id", len(steps) + 1)
            tool_name = item.get("tool_name", "")
            reason = item.get("reason", "")
            arguments = item.get("arguments", {})

            if not tool_name:
                continue
            if not isinstance(arguments, dict):
                arguments = {}

            steps.append(SubTaskStep(
                step_id=int(step_id) if isinstance(step_id, (int, float)) else len(steps) + 1,
                tool_name=str(tool_name),
                arguments=arguments,
                reason=str(reason),
            ))

        if not steps:
            return None

        # 按 step_id 排序
        steps.sort(key=lambda s: s.step_id)

        # 修正 step_id 保证连续
        for i, s in enumerate(steps):
            s.step_id = i + 1

        return steps


# ═══════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════

def decompose_task(
    task: str,
    backend=None,
    available_tools: list = None,
) -> List[SubTaskStep]:
    """
    便捷函数：一行调用拆解任务

    Args:
        task: 用户任务描述
        backend: BaseLLMBackend 实例（可选）
        available_tools: 可用工具 schema 列表

    Returns:
        SubTaskStep 列表
    """
    decomposer = TaskDecomposer(backend)
    return decomposer.decompose(task, available_tools)

```
