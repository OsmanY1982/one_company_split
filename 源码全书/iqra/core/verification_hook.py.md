# `iqra/core/verification_hook.py`

> 路径：`iqra/core/verification_hook.py` | 行数：298


---


```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VerificationHook — 执行后正确性自检

AgentLoop 在 tool_calls 结束 → COMPLETE 前，插入角色切换 review：
用独立 system prompt（"严苛 Code Reviewer"视角）检查本轮所有操作的正确性。

与 tool_guardrails.py 的职责边界：
  guardrails  → 管"有没有重复调同一个工具、有没有非法工具组合"
  verification → 管"干的事对不对"（正确的文件？正确的参数？符合规范？）

架构：
  VerificationHook 是纯函数式模块，不依赖 AgentLoop 内部状态。
  输入本轮对话消息 + 工具调用记录，输出 Findings 列表。
  AgentLoop 负责决定是否将 findings 注入最终回复。

用法:
    from iqra.core.verification_hook import VerificationHook

    hook = VerificationHook(chat_fn=engine.backend.chat)
    findings = hook.review(
        messages=messages,
        tools_called=["read_file", "write_file"],
        tool_results=[{"tool": "write_file", "success": True, "output": "..."}],
        user_query="帮我重构登录模块",
    )
    # → [Finding(severity="warning", desc="修改了 3 个文件但未检查调用方"), ...]
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════


class FindingSeverity(Enum):
    INFO = "info"           # 建议性提示
    WARNING = "warning"     # 潜在问题
    ERROR = "error"         # 明确错误
    CRITICAL = "critical"   # 可能导致数据丢失/系统异常


@dataclass
class Finding:
    """审查发现"""
    severity: FindingSeverity = FindingSeverity.INFO
    desc: str = ""
    file_path: str = ""     # 涉及的文件路径（可选）
    suggestion: str = ""    # 修复建议


@dataclass
class ReviewResult:
    """审查结果汇总"""
    findings: List[Finding] = field(default_factory=list)
    verdict: str = ""       # "pass" / "warn" / "fail"
    summary: str = ""       # 一句话总结


# ═══════════════════════════════════════════
# 审查 System Prompt
# ═══════════════════════════════════════════


REVIEW_SYSTEM_PROMPT = """你是资深 Code Reviewer，专门审查 AI Agent 的执行结果。

## 你的职责
检查 Agent 刚才调用的每个工具，判断操作是否正确、完整、安全。

## 审查维度（逐一检查）
1. **文件选择**：操作的文件路径是否正确？有没有遗漏应该处理的相关文件？
2. **操作正确性**：工具调用参数是否合理？写入的内容是否符合用户需求？
3. **副作用检查**：是否修改了不该改的文件？是否可能破坏已有功能？
4. **完整性**：用户的需求是否被完全覆盖？有没有遗留未完成的部分？
5. **安全风险**：是否涉及敏感路径、凭证泄露、破坏性操作？
6. **规范遵守**：是否违反 AI 设计规范中的铁律（如擅自备份/推送、修改受保护文件等）？

## 输出格式（严格 JSON）
{
  "verdict": "pass" | "warn" | "fail",
  "summary": "一句话总结审查结果",
  "findings": [
    {
      "severity": "info" | "warning" | "error" | "critical",
      "desc": "问题描述",
      "file_path": "涉及的文件路径（无则空字符串）",
      "suggestion": "修复建议"
    }
  ]
}

## 重要原则
- 不要为了凑数而编造问题——只在确实发现问题时才标记 warning/error
- verdict "pass" = 操作正确，无需修复
- verdict "warn" = 有小问题但不影响功能
- verdict "fail" = 有明确错误或遗漏，必须修复
- 只输出 JSON，不要加解释"""


# ═══════════════════════════════════════════
# 审查钩子
# ═══════════════════════════════════════════


class VerificationHook:
    """
    执行后正确性自检钩子。

    在 AgentLoop 完成 tool_calls 后、COMPLETE 前调用，
    用独立的 system prompt 对执行结果做冷审查。

    chat_fn: 函数签名 (messages, tools=None) → response_object
             response_object 需要有 .content (str) 属性
    """

    def __init__(self, chat_fn: Callable, enabled: bool = True):
        self._chat = chat_fn
        self._enabled = enabled
        self._review_count: int = 0
        self._total_findings: int = 0

    # ── 公共 API ──────────────────────────

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    def review(
        self,
        messages: List[dict],
        tools_called: List[str],
        tool_results: List[dict],
        user_query: str = "",
    ) -> ReviewResult:
        """
        执行审查。

        Args:
            messages:     完整的 LLM 对话消息列表
            tools_called: 本轮调用的工具名列表
            tool_results: 每个工具调用的结果 [{"tool": ..., "success": ..., "output": ...}, ...]
            user_query:   用户的原始提问

        Returns:
            ReviewResult
        """
        if not self._enabled or not self._chat:
            return ReviewResult(verdict="pass", summary="审查未启用")

        # 构建审查上下文
        context = self._build_review_context(tools_called, tool_results, user_query)

        try:
            review_messages = [
                {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ]
            response = self._chat(review_messages)
            content = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.warning("VerificationHook review failed: %s", e)
            return ReviewResult(verdict="pass", summary=f"审查调用失败: {e}")

        result = self._parse_review_response(content)
        self._review_count += 1
        self._total_findings += len(result.findings)
        return result

    # ── 内部 ──────────────────────────────

    def _build_review_context(
        self,
        tools_called: List[str],
        tool_results: List[dict],
        user_query: str,
    ) -> str:
        """构建发给 reviewer 的上下文"""
        parts = []

        if user_query:
            parts.append(f"## 用户需求\n{user_query[:500]}")

        parts.append(f"\n## 调用的工具 ({len(tools_called)} 个)\n{', '.join(tools_called)}")

        parts.append("\n## 工具执行结果")
        for i, tr in enumerate(tool_results):
            tool_name = tr.get("tool", f"tool_{i}")
            success = "✅" if tr.get("success", False) else "❌"
            output = str(tr.get("output", tr.get("error", "")))[:600]
            parts.append(f"\n### {i+1}. {success} {tool_name}")
            parts.append(f"```\n{output}\n```")

        return "\n".join(parts)

    def _parse_review_response(self, content: str) -> ReviewResult:
        """解析 LLM 返回的 JSON 审查结果"""
        result = ReviewResult()

        # 提取 JSON（可能在 markdown 代码块中）
        json_str = content
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                json_str = content[start:end]
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                json_str = content[start:end]

        try:
            data = json.loads(json_str.strip())
        except json.JSONDecodeError:
            logger.debug("VerificationHook: failed to parse JSON, raw: %s", content[:200])
            return ReviewResult(
                verdict="pass",
                summary="审查结果解析失败（非 JSON 输出）",
            )

        result.verdict = data.get("verdict", "pass")
        result.summary = data.get("summary", "")

        for f in data.get("findings", []):
            severity_str = f.get("severity", "info")
            try:
                severity = FindingSeverity(severity_str)
            except ValueError:
                severity = FindingSeverity.INFO
            result.findings.append(Finding(
                severity=severity,
                desc=f.get("desc", ""),
                file_path=f.get("file_path", ""),
                suggestion=f.get("suggestion", ""),
            ))

        return result

    @property
    def stats(self) -> dict:
        return {
            "enabled": self._enabled,
            "review_count": self._review_count,
            "total_findings": self._total_findings,
        }


# ═══════════════════════════════════════════
# 辅助：格式化 findings 为可注入 LLM 的文本
# ═══════════════════════════════════════════


def format_findings_context(findings: List[Finding], max_items: int = 5) -> str:
    """
    将 findings 格式化为可注入 Agent 回复的文本。

    用于 AgentLoop 在 COMPLETE 阶段将审查意见附加到最终回复中。
    """
    if not findings:
        return ""

    errors = [f for f in findings if f.severity in (FindingSeverity.CRITICAL, FindingSeverity.ERROR)]
    warnings = [f for f in findings if f.severity == FindingSeverity.WARNING]
    infos = [f for f in findings if f.severity == FindingSeverity.INFO]

    lines = []
    if errors:
        lines.append("## 执行审查发现严重问题")
        for f in errors[:max_items]:
            lines.append(f"- **{f.desc}**")
            if f.file_path:
                lines.append(f"  文件: `{f.file_path}`")
            if f.suggestion:
                lines.append(f"  建议: {f.suggestion}")

    if warnings:
        if errors:
            lines.append("")
        lines.append("## 潜在问题")
        for f in warnings[:max_items]:
            lines.append(f"- {f.desc}")
            if f.suggestion:
                lines.append(f"  建议: {f.suggestion}")

    return "\n".join(lines)

```
