# `intelligence/agent_bridge_tools/_code_tools.py`

> 路径：`intelligence/agent_bridge_tools/_code_tools.py` | 行数：588


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
        """Python 沙箱执行（code_executor 的 SecureSandbox）"""
        def handler(code: str, timeout: int = 30) -> dict:
            import time as _time
            import json as _json

            # ── 尝试导入沙箱组件 ──
            try:
                from iqra.core.code_executor import SecureSandbox, CodeValidator, ExecutionResult
            except ImportError:
                SecureSandbox = None
                CodeValidator = None

            if SecureSandbox is None or CodeValidator is None:
                # 沙箱不可用，回退到 subprocess 并附加安全警告
                try:
                    result = subprocess.run(
                        [sys.executable, "-c", code],
                        capture_output=True, text=True, timeout=timeout,
                    )
                    return {
                        "success": result.returncode == 0,
                        "output": result.stdout or "",
                        "error": result.stderr or "",
                        "duration_ms": int(timeout * 1000),
                        "warning": "SecureSandbox 不可用，已回退到裸 subprocess 执行（无安全限制）",
                    }
                except subprocess.TimeoutExpired:
                    return {"error": f"执行超时（{timeout}秒）"}
                except Exception as e:
                    return {"error": str(e)}

            # ── 沙箱可用：安全验证 + 子进程隔离执行 ──
            start = _time.time()

            # Step 1: AST 安全验证（print 放行——子进程 wrapper 已用 _safe_print 替换）
            is_safe, error = CodeValidator.validate(code)
            if not is_safe and error:
                # print 是 DANGEROUS_FUNCTIONS 成员，但 wrapper 用 _safe_print 安全替换
                if "禁止调用函数: print" not in error:
                    return {
                        "success": False,
                        "output": "",
                        "error": f"代码安全验证失败: {error}",
                        "duration_ms": int((_time.time() - start) * 1000),
                    }

            # Step 2: 构建沙箱受限环境，通过子进程执行（避免 multiprocessing 在 macOS spawn 模式下的 pickle 问题）
            sandbox = SecureSandbox(timeout=timeout)
            safe_globals_json = _json.dumps(
                {k: True for k in sandbox.allow_modules},
                ensure_ascii=False,
            )
            stderr_output = ""

            sandbox_wrapper = f'''
import json, sys, io, contextlib, traceback

_module_names = json.loads({safe_globals_json!r})

# 重建白名单模块导入
_allowed = set()
for m in _module_names:
    try:
        mod = __import__(m)
        globals()[m] = mod
        _allowed.add(m)
    except ImportError:
        pass

# 重建安全内置函数
def _safe_print(*args, **kwargs):
    buf = io.StringIO()
    print(*args, file=buf, **kwargs)
    result = buf.getvalue()
    buf.close()
    sys.stdout.write(result)
    return result

def _safe_import(name, *args, **kwargs):
    base = name.split(".")[0]
    if base not in _allowed:
        raise ImportError(f"禁止导入模块: {{name}}")
    return __import__(name, *args, **kwargs)

_safe_builtins = {{
    "True": True, "False": False, "None": None,
    "abs": abs, "all": all, "any": any, "ascii": ascii,
    "bin": bin, "bool": bool, "bytearray": bytearray, "bytes": bytes,
    "callable": callable, "chr": chr, "complex": complex,
    "dict": dict, "divmod": divmod, "enumerate": enumerate,
    "filter": filter, "float": float, "format": format,
    "frozenset": frozenset, "hasattr": hasattr, "hash": hash,
    "hex": hex, "id": id, "int": int, "isinstance": isinstance,
    "issubclass": issubclass, "iter": iter, "len": len,
    "list": list, "map": map, "max": max, "memoryview": memoryview,
    "min": min, "next": next, "object": object, "oct": oct,
    "ord": ord, "pow": pow, "print": _safe_print, "property": property,
    "range": range, "repr": repr, "reversed": reversed, "round": round,
    "set": set, "slice": slice, "sorted": sorted,
    "staticmethod": staticmethod, "str": str, "sum": sum,
    "super": super, "tuple": tuple, "type": type, "vars": vars,
    "zip": zip, "__import__": _safe_import,
}}

_code = {code!r}

try:
    output_buf = io.StringIO()
    with contextlib.redirect_stdout(output_buf):
        compiled = compile(_code, "<sandbox>", "exec")
        exec(compiled, {{"__builtins__": _safe_builtins}}, {{}})
    result = {{"success": True, "output": output_buf.getvalue()}}
except SyntaxError as e:
    result = {{"success": False, "output": output_buf.getvalue() if "output_buf" in dir() else "", "error": f"语法错误: {{e}}"}}
except Exception as e:
    result = {{"success": False, "output": output_buf.getvalue() if "output_buf" in dir() else "", "error": f"{{e}}\\n{{traceback.format_exc()}}"}}
finally:
    if "output_buf" in dir():
        output_buf.close()

print("__SANDBOX_RESULT__", json.dumps(result), sep="")
'''

            try:
                proc = subprocess.run(
                    [sys.executable, "-c", sandbox_wrapper],
                    capture_output=True, text=True, timeout=timeout + 5,
                )
                duration_ms = int((_time.time() - start) * 1000)

                # 解析沙箱结果
                stdout = proc.stdout or ""
                if "__SANDBOX_RESULT__" in stdout:
                    marker = "__SANDBOX_RESULT__"
                    idx = stdout.rfind(marker)
                    json_str = stdout[idx + len(marker):].strip()
                    try:
                        sandbox_result = _json.loads(json_str)
                        return {
                            "success": sandbox_result.get("success", False),
                            "output": sandbox_result.get("output", ""),
                            "error": sandbox_result.get("error", ""),
                            "duration_ms": duration_ms,
                        }
                    except _json.JSONDecodeError:
                        pass

                # 无法解析沙箱结果，返回原始输出
                return {
                    "success": proc.returncode == 0,
                    "output": stdout,
                    "error": proc.stderr or "",
                    "duration_ms": duration_ms,
                }

            except subprocess.TimeoutExpired:
                return {"error": f"执行超时（{timeout}秒）", "duration_ms": int(timeout * 1000)}
            except Exception as e:
                return {"error": str(e), "duration_ms": int((_time.time() - start) * 1000)}
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
                    from core.workspace_indexer import WorkspaceIndexer
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

    # ── 15b. search_project_book（项目全书全局搜索）──
    def _reg_search_project_book(self):
        """项目全书 Markdown 文档全文搜索"""
        def handler(query: str, top_k: int = 10) -> dict:
            try:
                from iqra.core.book_search import BookSearcher
                searcher = BookSearcher()
                searcher.build_index()
                results = searcher.search(query, top_k=top_k)
                return {
                    "query": query,
                    "results": [
                        {
                            "file_name": r.file_name,
                            "heading": r.heading,
                            "score": r.score,
                            "snippet": r.snippet,
                            "file_path": r.file_path,
                        }
                        for r in results
                    ],
                    "count": len(results),
                }
            except Exception as e:
                return {"error": str(e)}
        self.registry.register(
            name="search_project_book",
            description="在项目全书（38 个 Markdown 文档）中全文搜索。适合查找架构说明、模块文档、设计决策等技术文档内容",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词或短语"},
                    "top_k": {"type": "integer", "description": "返回结果数，默认10", "default": 10},
                },
                "required": ["query"],
            },
            category="code",
        )(handler)

    # ── 16. generate_diff（为 old_str → new_str 生成 unified diff）──
    def _reg_generate_diff(self):
        """生成 standard unified diff，不修改文件"""
        import difflib

        def handler(file_path: str, old_str: str, new_str: str) -> dict:
            try:
                if not os.path.exists(file_path):
                    return {"error": f"文件不存在: {file_path}"}
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if old_str not in content:
                    return {"error": "old_str 在目标文件中未找到，无法生成 diff"}
                # 将 old_str 替换为 new_str，构建"修改后"的文件内容
                # 仅替换首次出现（edit_file 默认行为）
                modified = content.replace(old_str, new_str, 1)
                diff_lines = list(difflib.unified_diff(
                    content.splitlines(keepends=True),
                    modified.splitlines(keepends=True),
                    fromfile=os.path.basename(file_path),
                    tofile=os.path.basename(file_path),
                ))
                diff_text = "".join(diff_lines)
                # 统计 hunks
                hunk_count = sum(1 for line in diff_lines if line.startswith("@@"))
                # 统计变更行数
                added = sum(1 for line in diff_lines if line.startswith("+") and not line.startswith("+++"))
                removed = sum(1 for line in diff_lines if line.startswith("-") and not line.startswith("---"))
                return {
                    "success": True,
                    "diff": diff_text,
                    "hunks": hunk_count,
                    "stats": {"added_lines": added, "removed_lines": removed, "total_changes": added + removed},
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="generate_diff",
            description="对比 old_str 与 new_str，生成 standard unified diff 预览（基于目标文件内容）。不修改任何文件",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "目标文件绝对路径"},
                    "old_str": {"type": "string", "description": "要替换的原始文本片段，必须在文件中精确匹配"},
                    "new_str": {"type": "string", "description": "替换后的新文本"},
                },
                "required": ["file_path", "old_str", "new_str"],
            },
            category="code",
        )(handler)

    # ── 17. apply_patch（unified diff 应用引擎，含 .bak 备份）──
    def _reg_apply_patch(self):
        """应用 unified diff patch 到文件，自动创建 .bak 备份"""
        import difflib
        import re
        import shutil

        def parse_unified_diff(patch_text: str) -> list:
            """解析 unified diff 文本，返回 hunk 列表。
            每个 hunk: {old_start, old_count, new_start, new_count, lines}
            lines 为列表: (' ', line) 上下文 / ('-', line) 删除 / ('+', line) 新增
            """
            hunks = []
            hunk_header_re = re.compile(
                r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$'
            )
            current_hunk = None
            for line in patch_text.splitlines():
                # 跳过文件头（--- / +++）
                if line.startswith("--- ") or line.startswith("+++ "):
                    continue
                if line.startswith("diff ") or line.startswith("index ") or line.startswith("==="):
                    continue
                m = hunk_header_re.match(line)
                if m:
                    if current_hunk:
                        hunks.append(current_hunk)
                    old_start = int(m.group(1))
                    old_count = int(m.group(2) or 1)
                    new_start = int(m.group(3))
                    new_count = int(m.group(4) or 1)
                    current_hunk = {
                        "old_start": old_start, "old_count": old_count,
                        "new_start": new_start, "new_count": new_count,
                        "lines": [],
                    }
                elif current_hunk is not None:
                    if line.startswith(" "):
                        current_hunk["lines"].append((" ", line[1:]))
                    elif line.startswith("-"):
                        current_hunk["lines"].append(("-", line[1:]))
                    elif line.startswith("+"):
                        current_hunk["lines"].append(("+", line[1:]))
                    elif line.strip() == "":
                        current_hunk["lines"].append((" ", ""))
                    # 忽略 \ No newline at end of file
            if current_hunk:
                hunks.append(current_hunk)
            return hunks

        def _apply_hunks(original_lines: list, hunks: list) -> list:
            """将 hunks 应用到原始行列表，返回新行列表。失败抛 ValueError。
            注意：original_lines 应为 splitlines() 结果（不含换行符），以与 diff 解析结果对齐。
            """
            for hunk in reversed(hunks):
                old_start_0 = hunk["old_start"] - 1
                old_count = hunk["old_count"]
                new_lines = [line for tag, line in hunk["lines"] if tag in (" ", "+")]
                # 验证上下文
                expected_old = [line for tag, line in hunk["lines"] if tag in (" ", "-")]
                actual_old = original_lines[old_start_0:old_start_0 + old_count]
                # 两边都 strip 尾部空白后再比较
                actual_clean = [l.rstrip("\n").rstrip("\r") for l in actual_old]
                if expected_old != actual_clean:
                    mismatch_lines = []
                    max_len = max(len(expected_old), len(actual_clean))
                    for i in range(max_len):
                        exp = expected_old[i] if i < len(expected_old) else "<缺失>"
                        act = actual_clean[i] if i < len(actual_clean) else "<缺失>"
                        if exp != act:
                            mismatch_lines.append(
                                f"  line {old_start_0 + i + 1}: 期望={exp!r}  实际={act!r}"
                            )
                    raise ValueError(
                        f"patch 上下文不匹配（hunk @@ -{hunk['old_start']},{hunk['old_count']} "
                        f"+{hunk['new_start']},{hunk['new_count']} @@）:\n" +
                        "\n".join(mismatch_lines[:5]) +
                        (f"\n  ...共 {len(mismatch_lines)} 处不匹配" if len(mismatch_lines) > 5 else "")
                    )
                original_lines[old_start_0:old_start_0 + old_count] = new_lines
            return original_lines

        def handler(file_path: str, patch: str) -> dict:
            try:
                if not os.path.exists(file_path):
                    return {"error": f"文件不存在: {file_path}"}
                if not patch or not patch.strip():
                    return {"error": "patch 文本为空"}

                # 解析 hunks
                hunks = parse_unified_diff(patch)
                if not hunks:
                    return {"error": "无法解析 patch：未找到有效的 hunk。请确认是 unified diff 格式"}

                # 读取原文件（不使用 keepends，与 diff 解析结果对齐）
                with open(file_path, "r", encoding="utf-8") as f:
                    original_content = f.read()
                original_lines = original_content.splitlines()
                trailing_newline = original_content.endswith("\n")

                # 创建 .bak 备份
                backup_path = file_path + ".bak"
                shutil.copy2(file_path, backup_path)

                try:
                    new_lines = _apply_hunks(original_lines, hunks)
                except ValueError as ve:
                    # 应用失败，删除备份
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    return {"error": f"patch 应用失败: {ve}"}

                new_content = "\n".join(new_lines)
                if trailing_newline:
                    new_content += "\n"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

                return {
                    "success": True,
                    "file_path": file_path,
                    "backup_path": backup_path,
                    "stats": {
                        "hunks_applied": len(hunks),
                        "original_bytes": len(original_content),
                        "new_bytes": len(new_content),
                        "bytes_diff": len(new_content) - len(original_content),
                    },
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="apply_patch",
            description="将 unified diff patch 应用到目标文件。自动创建 .bak 备份防数据丢失。仅接受标准 unified diff 格式",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "目标文件绝对路径"},
                    "patch": {"type": "string", "description": "标准 unified diff 格式的 patch 文本"},
                },
                "required": ["file_path", "patch"],
            },
            category="code",
        )(handler)

```
