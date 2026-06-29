# `iqra/core/smart_context_selector.py`

> 路径：`iqra/core/smart_context_selector.py` | 行数：238


---


```python
"""
SmartContextSelector — 智能上下文选择器。

基于用户输入，综合利用项目知识库、模块依赖图和语义记忆，
智能检索并合并相关上下文片段，注入 LLM 提示词。

用法:
    selector = SmartContextSelector(project_knowledge=kb, dep_graph=graph)
    fragments = selector.select_context("agent_loop 怎么处理工具调用失败")
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from iqra.core.project_knowledge import ProjectKnowledge
    from iqra.core.module_dependency_graph import ModuleDependencyGraph
    from iqra.core.semantic_memory import SemanticMemory


@dataclass
class ContextFragment:
    """上下文片段。"""
    source: str       # 'project_knowledge' / 'dependency_graph' / 'semantic_memory'
    content: str      # 片段文本
    file_path: str    # 来源文件路径（如有）
    score: float      # 相关性评分 0-1

    def _content_hash(self) -> str:
        return hashlib.md5(self.content.encode("utf-8")).hexdigest()


# 模块名/类名提取模式
_RE_MODULE_PATH = re.compile(r'\b([a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)+)\b')
_RE_SNAKE_CASE = re.compile(r'\b([a-z][a-z0-9]*(?:_[a-z0-9]+)+)\b')
_RE_CAMEL_CASE = re.compile(r'\b([A-Z][a-zA-Z0-9]*(?:[A-Z][a-z0-9]+)+)\b')


class SmartContextSelector:
    """智能上下文选择器 — 多源检索 + 合并去重 + 截断。"""

    def __init__(
        self,
        project_knowledge: "ProjectKnowledge",
        dep_graph: "ModuleDependencyGraph",
        semantic_memory: "Optional[SemanticMemory]" = None,
    ):
        self._kb = project_knowledge
        self._graph = dep_graph
        self._sem = semantic_memory

    # ── 核心方法 ────────────────────────────────────────────

    def select_context(
        self, query: str, max_fragments: int = 5, max_chars: int = 4000
    ) -> List[ContextFragment]:
        """主入口：接收用户输入，返回 Top-K 上下文片段。"""
        fragments: List[ContextFragment] = []

        # a-b. 项目知识库 BM25 检索
        fragments.extend(self._from_project_knowledge(query))

        # c. 模块依赖分析
        fragments.extend(self._from_dependency_graph(query))

        # d. 语义记忆检索
        if self._sem is not None:
            fragments.extend(self._from_semantic_memory(query))

        # e. 合并去重、排序、截断
        fragments = self._merge_dedup(fragments)
        fragments = self._truncate(fragments, max_chars)
        return fragments[:max_fragments]

    def _extract_module_names(self, query: str) -> List[str]:
        """从用户输入提取可能的模块名。"""
        names: List[str] = []
        # 1. 点分隔路径（如 iqra.core.agent_loop）
        for m in _RE_MODULE_PATH.finditer(query):
            names.append(m.group(0))
        # 2. snake_case（如 agent_loop, _config_helpers）
        for m in _RE_SNAKE_CASE.finditer(query):
            names.append(m.group(0))
        # 3. CamelCase（如 AgentLoop, ChatEngine）
        for m in _RE_CAMEL_CASE.finditer(query):
            names.append(m.group(0))
        return names

    def _merge_dedup(self, fragments: List[ContextFragment]) -> List[ContextFragment]:
        """按 content hash 去重，按 score 降序排序。"""
        seen: Dict[str, ContextFragment] = {}
        for frag in fragments:
            h = frag._content_hash()
            if h not in seen or frag.score > seen[h].score:
                seen[h] = frag
        return sorted(seen.values(), key=lambda x: -x.score)

    def _truncate(
        self, fragments: List[ContextFragment], max_chars: int
    ) -> List[ContextFragment]:
        """截断为总字符数不超过 max_chars，优先保留高分片段。"""
        result: List[ContextFragment] = []
        total = 0
        for frag in fragments:
            if total + len(frag.content) <= max_chars:
                result.append(frag)
                total += len(frag.content)
            else:
                break
        return result

    # ── 数据源适配 ──────────────────────────────────────────

    def _from_project_knowledge(self, query: str) -> List[ContextFragment]:
        """从 ProjectKnowledge 检索相关文档块。"""
        try:
            results = self._kb.search(query, top_k=3)
        except Exception:
            return []
        fragments: List[ContextFragment] = []
        for r in results:
            fragments.append(ContextFragment(
                source="project_knowledge",
                content=r.get("snippet", ""),
                file_path=r.get("source_file", ""),
                score=min(r.get("score", 0.0), 1.0),
            ))
        return fragments

    def _from_dependency_graph(self, query: str) -> List[ContextFragment]:
        """从 ModuleDependencyGraph 获取模块依赖链上下文。"""
        module_names = self._extract_module_names(query)
        if not module_names:
            return []

        fragments: List[ContextFragment] = []
        seen_modules: set = set()

        for raw_name in module_names:
            # 尝试匹配为项目内模块
            matched = self._match_module(raw_name)
            if not matched:
                continue

            for mod_name in matched:
                if mod_name in seen_modules:
                    continue
                seen_modules.add(mod_name)

                # 获取依赖链
                deps = self._graph.get_dependencies(mod_name)
                dependents = self._graph.get_dependents(mod_name)

                lines = [f"模块 {mod_name}:",
                         f"  依赖 ({len(deps)}): {', '.join(deps[:8])}" if deps else "  依赖: 无"]
                if dependents:
                    lines.append(f"  被依赖 ({len(dependents)}): {', '.join(dependents[:8])}")
                content = "\n".join(lines)

                file_path = self._graph.module_paths.get(mod_name, "")
                score = 0.6 + 0.1 * min(len(deps) + len(dependents), 4)

                fragments.append(ContextFragment(
                    source="dependency_graph",
                    content=content,
                    file_path=file_path,
                    score=min(score, 1.0),
                ))

        return fragments

    def _from_semantic_memory(self, query: str) -> List[ContextFragment]:
        """从 SemanticMemory 检索相关实体。"""
        try:
            results = self._sem.search(query, top_k=3)
        except Exception:
            return []
        fragments: List[ContextFragment] = []
        for r in results:
            name = r.get("name", "")
            content = f"实体: {name}"
            if "type" in r:
                content += f" (类型: {r['type']})"
            # 附加上下文（子图摘要等）
            subgraph = r.get("subgraph", {})
            if subgraph:
                entities = subgraph.get("entities", [])
                rels = subgraph.get("relations", [])
                if entities or rels:
                    content += f"\n  关联实体: {len(entities)} 个, 关系: {len(rels)} 条"
            fragments.append(ContextFragment(
                source="semantic_memory",
                content=content,
                file_path="",
                score=0.4,  # 语义记忆基础分较低
            ))
        return fragments

    # ── 模块名匹配 ──────────────────────────────────────────

    def _match_module(self, raw_name: str) -> List[str]:
        """将提取的模块名/类名匹配为项目内实际模块名。

        - 剔除常见后缀（.py）
        - 对 CamelCase 尝试转换为 snake_case（如 AgentLoop → agent_loop）
        - 对所有候选在 graph.module_paths 中查找
        """
        clean = raw_name.rstrip(".py").strip(".")
        candidates = [clean]

        # CamelCase → snake_case 转换
        if _RE_CAMEL_CASE.fullmatch(clean):
            snake = re.sub(r'([A-Z]+)', r'_\1', clean).lower().lstrip("_")
            # 去掉连续下划线并重试
            snake = re.sub(r'_+', '_', snake)
            candidates.append(snake)

        module_paths = self._graph.module_paths

        # 精确匹配
        for cand in candidates:
            if cand in module_paths:
                return [cand]

        # 后缀匹配（如提取的是类名，模块文件名为对应 snake_case）
        for cand in candidates:
            suffix = f".{cand}"
            matched = [m for m in module_paths if m.endswith(suffix)]
            if matched:
                return matched[:2]

        # 包含匹配
        matched = [m for m in module_paths if cand in m]
        return matched[:2] if matched else []

```
