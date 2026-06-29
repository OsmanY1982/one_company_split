# `iqra/core/module_dependency_graph.py`

> 路径：`iqra/core/module_dependency_graph.py` | 行数：226


---


```python
"""
ModuleDependencyGraph — 项目模块依赖关系图。

通过 AST 解析所有 .py 文件的 import 语句构建 networkx.DiGraph，
支持正向/逆向依赖查询与变更影响分析。

用法:
    graph = ModuleDependencyGraph(project_root="/path/to/project")
    graph.build()
    deps = graph.get_dependencies("iqra.core.agent_loop")
    affected = graph.get_affected_modules(["iqra/core/chat_engine.py"])
    summary = graph.get_graph_summary()
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# 扫描时跳过的目录
_SKIP_DIRS: Set[str] = {
    ".venv", "venv", ".env", "env", "__pycache__",
    ".git", ".svn", ".hg", ".tox", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "node_modules",
    "dist", "build", ".eggs", "*.egg-info",
}


def _get_project_module_paths(project_root: str) -> Dict[str, str]:
    """扫描项目 .py 文件，返回 {模块名: 绝对路径}。跳过虚拟环境等非项目目录。"""
    module_map: Dict[str, str] = {}
    root = Path(project_root).resolve()
    for py_file in root.rglob("*.py"):
        rel = py_file.relative_to(root)
        parts = list(rel.parts)
        if any(p in _SKIP_DIRS or (p.startswith(".") and p not in (".", ".."))
               for p in parts[:-1]):
            continue
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].replace(".py", "")
        name = ".".join(parts)
        if name:
            module_map[name] = str(py_file)
    return module_map


def _resolve_relative(import_name: str, level: int, current_module: str) -> Optional[str]:
    """将相对导入解析为绝对模块名。"""
    if level == 0:
        return import_name
    parts = current_module.split(".")
    if level > len(parts):
        return None
    base = parts[:-level]
    return ".".join(base + [import_name]) if import_name else ".".join(base) if base else None


class ModuleDependencyGraph:
    """项目内 Python 模块导入依赖关系图。"""

    def __init__(self, project_root: str):
        self._project_root = str(Path(project_root).resolve())
        self._module_paths: Dict[str, str] = {}
        self._adj_out: Dict[str, List[str]] = {}  # 正向依赖
        self._adj_in: Dict[str, List[str]] = {}   # 逆向依赖
        self._graph: "networkx.DiGraph | None" = None
        self._has_networkx = False

    # ── 公共 API ──

    def build(self) -> None:
        """全量扫描并构建依赖图。"""
        self._module_paths = _get_project_module_paths(self._project_root)
        self._adj_out.clear()
        self._adj_in.clear()

        for mod_name, file_path in self._module_paths.items():
            deps = self._parse_deps(file_path, mod_name)
            self._adj_out[mod_name] = sorted(set(deps))
            self._adj_in.setdefault(mod_name, [])

        for src, targets in self._adj_out.items():
            for tgt in targets:
                self._adj_in.setdefault(tgt, [])
                if src not in self._adj_in[tgt]:
                    self._adj_in[tgt].append(src)

        self._build_networkx()

    def get_dependencies(self, module_path: str) -> List[str]:
        """获取指定模块依赖的所有模块。"""
        return sorted(set(self._adj_out.get(self._to_module(module_path), [])))

    def get_dependents(self, module_path: str) -> List[str]:
        """获取依赖指定模块的所有模块。"""
        return sorted(set(self._adj_in.get(self._to_module(module_path), [])))

    def get_affected_modules(self, changed_files: List[str]) -> List[str]:
        """输入变更文件列表，返回所有受影响的模块（文件路径）。

        沿逆向边 BFS：返回所有直接/间接依赖变更模块的模块。
        """
        start = {n for f in changed_files
                 if (n := self._to_module(f)) in self._module_paths}
        visited: Set[str] = set()
        queue = list(start)
        while queue:
            cur = queue.pop(0)
            if cur in visited:
                continue
            visited.add(cur)
            for dep in self._adj_in.get(cur, []):
                if dep not in visited:
                    queue.append(dep)
        return [self._module_paths.get(m, m)
                for m in sorted(visited - start)]

    def get_graph_summary(self) -> dict:
        """返回 {total_nodes, total_edges, most_depended, most_dependent}。"""
        in_deg = [(m, len(self._adj_in.get(m, []))) for m in self._adj_out]
        out_deg = [(m, len(self._adj_out.get(m, []))) for m in self._adj_out]
        return {
            "total_nodes": len(self._adj_out),
            "total_edges": sum(len(v) for v in self._adj_out.values()),
            "most_depended": [(m, c) for m, c in
                              sorted(in_deg, key=lambda x: -x[1])[:10] if c > 0],
            "most_dependent": [(m, c) for m, c in
                               sorted(out_deg, key=lambda x: -x[1])[:10] if c > 0],
        }

    @property
    def graph(self):
        """networkx.DiGraph 实例，不可用时为 None。"""
        return self._graph

    @property
    def module_paths(self) -> Dict[str, str]:
        """{模块名: 文件绝对路径} 映射。"""
        return dict(self._module_paths)

    # ── 内部方法 ──

    def _parse_deps(self, file_path: str, current_module: str) -> List[str]:
        """解析 .py 文件 import，返回项目内模块名列表。"""
        results: List[str] = []
        imports = self._extract_imports(file_path)
        for imp_name, level in imports:
            if level > 0:
                imp_name = _resolve_relative(imp_name, level, current_module)
                if imp_name is None:
                    continue
            normalized = self._normalize(imp_name)
            if normalized is not None and normalized in self._module_paths:
                results.append(normalized)
        return results

    def _normalize(self, import_name: str) -> Optional[str]:
        """将 import 名归一化为项目内模块名，非项目库返回 None。"""
        if not import_name:
            return None
        import_name = import_name.rstrip(".*")
        if not import_name:
            return None

        top = import_name.split(".")[0]
        if not hasattr(self, "_top_pkgs"):
            self._top_pkgs: Set[str] = {m.split(".")[0] for m in self._module_paths}
        if top not in self._top_pkgs:
            return None

        # 逐段匹配最长项目内前缀
        parts = import_name.split(".")
        for i in range(len(parts), 0, -1):
            candidate = ".".join(parts[:i])
            if candidate in self._module_paths:
                return candidate
        return None

    def _extract_imports(self, file_path: str) -> List[Tuple[str, int]]:
        """解析 import/from-import 语句，返回 [(模块名, 相对层级)]。"""
        results: List[Tuple[str, int]] = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                tree = ast.parse(f.read())
        except (OSError, SyntaxError):
            return results

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    results.append((alias.name, 0))
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                results.append((node.module, node.level))
        return results

    def _to_module(self, path_str: str) -> str:
        """将文件路径或模块名统一转换为模块名。"""
        ps = path_str.replace("\\", "/")
        root = self._project_root.replace("\\", "/")
        if ps.startswith(root):
            rel = ps[len(root):].lstrip("/")
            parts = list(Path(rel).parts)
            if parts[-1].endswith(".py"):
                parts[-1] = parts[-1].replace(".py", "")
            if parts and parts[-1] == "__init__":
                parts = parts[:-1]
            return ".".join(parts)
        return path_str.replace("/", ".").replace(".py", "").rstrip(".")

    def _build_networkx(self) -> None:
        try:
            import networkx as nx
            g = nx.DiGraph()
            for m in self._module_paths:
                g.add_node(m)
            for src, targets in self._adj_out.items():
                for tgt in targets:
                    g.add_edge(src, tgt)
            self._graph = g
            self._has_networkx = True
        except ImportError:
            self._graph = None
            self._has_networkx = False

```
