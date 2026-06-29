# `planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_code_tools.py`

> 路径：`planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_code_tools.py` | 行数：242


---


```python
"""代码工具 Mixin：search_code / run_tests / execute_python / analyze_code / search_codebase / apply_patch"""

import os
import sys
import subprocess


class _CodeToolsMixin:
    """代码工具注册"""

    # ── 6. search_code（ripgrep 代码搜索）──
    def _reg_search_code(self):
        def handler(query: str, directory: str = ".", file_pattern: str = "*", max_results: int = 50) -> dict:
            try:
                cmd = ["rg", "--line-number", "--max-count", str(max_results), query]
                if file_pattern != "*":
                    cmd.extend(["--glob", file_pattern])
                cmd.append(directory)
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                                       cwd=os.path.expanduser("~"))
                if result.returncode == 1:
                    return {"query": query, "count": 0, "matches": [], "note": "未找到匹配"}
                lines = result.stdout.strip().split("\n")[:max_results]
                return {"query": query, "count": len(lines), "matches": lines}
            except FileNotFoundError:
                # 回退到 grep
                try:
                    cmd = ["grep", "-rn", "--include=" + file_pattern if file_pattern != "*" else "-r", query, directory]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    lines = result.stdout.strip().split("\n")[:max_results]
                    return {"query": query, "count": len(lines), "matches": lines, "backend": "grep"}
                except Exception as e:
                    return {"error": f"ripgrep 和 grep 均不可用: {e}"}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="search_code",
            description="在代码库中搜索文本（ripgrep）。支持正则、文件类型过滤",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词或正则表达式"},
                    "directory": {"type": "string", "description": "搜索目录，默认当前目录", "default": "."},
                    "file_pattern": {"type": "string", "description": "文件类型过滤（如 *.py, *.js）", "default": "*"},
                    "max_results": {"type": "integer", "description": "最大结果数", "default": 50},
                },
                "required": ["query"],
            },
            category="code",
        )(handler)

    # ── 7. run_tests ──
    def _reg_run_tests(self):
        def handler(test_path: str = "", framework: str = "auto") -> dict:
            try:
                if not test_path:
                    return {"error": "请指定测试文件或目录路径"}
                if framework == "auto":
                    if "pytest" in test_path.lower() or os.path.exists("pytest.ini") or os.path.exists("pyproject.toml"):
                        framework = "pytest"
                    else:
                        framework = "unittest"

                if framework == "pytest":
                    result = subprocess.run(
                        [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"],
                        capture_output=True, text=True, timeout=120,
                        cwd=os.path.expanduser("~"),
                    )
                else:
                    result = subprocess.run(
                        [sys.executable, "-m", "unittest", test_path, "-v"],
                        capture_output=True, text=True, timeout=120,
                        cwd=os.path.expanduser("~"),
                    )
                return {
                    "framework": framework,
                    "returncode": result.returncode,
                    "passed": result.returncode == 0,
                    "stdout": result.stdout[-3000:],
                    "stderr": result.stderr[-1000:],
                }
            except subprocess.TimeoutExpired:
                return {"error": "测试超时（120秒）"}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="run_tests",
            description="运行测试套件（自动检测 pytest/unittest）",
            parameters={
                "type": "object",
                "properties": {
                    "test_path": {"type": "string", "description": "测试文件或目录路径"},
                    "framework": {"type": "string", "description": "pytest / unittest / auto", "default": "auto"},
                },
                "required": ["test_path"],
            },
            category="code",
        )(handler)

    # ── 13. execute_python ──
    def _reg_execute_python(self):
        """Python 沙箱执行（code_executor 模块）"""
        def handler(code: str, timeout: int = 30) -> dict:
            if not self._code_executor:
                return {"error": "Python 沙箱未启用（code_executor 模块缺失）"}
            try:
                result = self._code_executor.execute(code, timeout=timeout)
                return {
                    "success": result.success,
                    "output": result.output or "",
                    "error": result.error or "",
                    "duration_ms": result.duration_ms,
                }
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="execute_python",
            description="在安全沙箱中执行 Python 代码，返回标准输出和错误",
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的 Python 代码"},
                    "timeout": {"type": "integer", "description": "超时秒数，默认30", "default": 30},
                },
                "required": ["code"],
            },
            category="code",
        )(handler)

    # ── 14. analyze_code ──
    def _reg_analyze_code(self):
        """代码智能分析（code_intel 模块）"""
        def handler(file_path: str, action: str = "symbols") -> dict:
            if not os.path.exists(file_path):
                return {"error": f"文件不存在: {file_path}"}
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()
                # 复用 agent_bridge 模块级 _HAVE_CODE_INTEL
                from core.modules.intelligence.agent_bridge import _HAVE_CODE_INTEL
                if _HAVE_CODE_INTEL:
                    import ast
                    from iqra.core.code_intel import SymbolExtractor
                    extractor = SymbolExtractor(source.split("\n"))
                    extractor.visit(ast.parse(source))
                    symbols = extractor._symbols if hasattr(extractor, '_symbols') else []
                    return {"file": file_path, "symbols": [s.__dict__ if hasattr(s, '__dict__') else str(s) for s in symbols], "total": len(symbols)}
                else:
                    return {"error": "代码智能引擎未启用（code_intel 模块缺失）"}
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="analyze_code",
            description="分析代码文件的符号结构（函数/类/变量定义）",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "要分析的代码文件绝对路径"},
                    "action": {
                        "type": "string",
                        "description": "分析类型: symbols（符号提取）/ usages（引用搜索）/ imports（依赖分析）/ refactor（重构建议）",
                        "enum": ["symbols", "usages", "imports", "refactor"],
                        "default": "symbols",
                    },
                },
                "required": ["file_path"],
            },
            category="code",
        )(handler)

    # ── 15. search_codebase ──
    def _reg_search_codebase(self):
        """代码库语义/全文搜索（workspace_indexer 模块）"""
        def handler(query: str, top_k: int = 10) -> dict:
            from core.modules.intelligence.agent_bridge import _HAVE_INDEXER
            if _HAVE_INDEXER:
                try:
                    from iqra.core.workspace_indexer import WorkspaceIndexer
                    # 子模块位于 agent_bridge_tools/ 子目录，需 4 层 dirname 到达项目根
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                    indexer = WorkspaceIndexer(project_root)
                    results = indexer.search(query, top_k=top_k)
                    return {
                        "query": query,
                        "results": [{"path": r.path, "score": round(r.score, 3), "snippet": r.snippet} for r in results],
                        "count": len(results),
                    }
                except Exception as e:
                    return {"error": str(e)}
            return {"error": "代码库索引器未启用（workspace_indexer 模块缺失）"}
        self.registry.register(
            name="search_codebase",
            description="在项目代码库中全文搜索，支持中文和英文关键词",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "top_k": {"type": "integer", "description": "返回结果数，默认10", "default": 10},
                },
                "required": ["query"],
            },
            category="code",
        )(handler)

    # ── 16. apply_patch ──
    def _reg_apply_patch(self):
        """文件补丁引擎（patch_engine 模块）"""
        def handler(file_path: str, pattern: str, replacement: str, dry_run: bool = True) -> dict:
            if not self._patch_engine:
                return {"error": "补丁引擎未启用（patch_engine 模块缺失）"}
            try:
                if dry_run:
                    result = self._patch_engine.preview(file_path, pattern, replacement)
                else:
                    result = self._patch_engine.apply(file_path, pattern, replacement)
                return {
                    "file": file_path,
                    "dry_run": dry_run,
                    "matches": result.get("matches", 0),
                    "changes": result.get("changes", []),
                    "success": result.get("success", False),
                }
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="apply_patch",
            description="对文件执行查找替换补丁（默认预览不写入）",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "目标文件绝对路径"},
                    "pattern": {"type": "string", "description": "要查找的文本模式"},
                    "replacement": {"type": "string", "description": "替换后的文本"},
                    "dry_run": {"type": "boolean", "description": "是否仅预览不实际修改，默认true", "default": True},
                },
                "required": ["file_path", "pattern", "replacement"],
            },
            category="code",
        )(handler)

```
