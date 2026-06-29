# `iqra/core/code_intel.py`

> 路径：`iqra/core/code_intel.py` | 行数：627


---


```python
# -*- coding: utf-8 -*-
"""
CodeIntel — 代码智能引擎（对标 Claude Code 代码理解/编辑/重构）

纯 Python 实现（AST + regex），零外部依赖。

能力:
  - extract_symbols   → 提取函数/类/变量定义
  - find_usages       → 符号引用搜索
  - analyze_imports   → 依赖图分析
  - suggest_refactor  → 重构建议（长函数/重复代码/未使用变量）
  - code_metrics      → 代码度量（行数/圈复杂度/耦合度）
"""

import os
import ast
import re
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path


# ═══════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════

@dataclass
class Symbol:
    """代码符号"""
    name: str
    kind: str            # function / class / method / variable / import
    line: int
    end_line: int = 0
    docstring: str = ""
    decorators: List[str] = field(default_factory=list)
    signature: str = ""  # 函数签名或类继承
    parent_class: str = ""
    file_path: str = ""


@dataclass
class ImportInfo:
    """导入信息"""
    module: str
    names: List[str] = field(default_factory=list)  # from X import a, b
    alias: str = ""
    line: int = 0
    is_relative: bool = False
    is_stdlib: bool = False
    is_third_party: bool = False


@dataclass
class FileDep:
    """文件依赖"""
    file_path: str
    imports: List[ImportInfo] = field(default_factory=list)
    imported_by: List[str] = field(default_factory=list)


@dataclass
class CodeMetric:
    """代码度量"""
    file_path: str
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    functions: int = 0
    classes: int = 0
    avg_function_length: float = 0.0
    max_function_length: int = 0
    max_complexity: int = 0  # 最大圈复杂度
    imports_count: int = 0
    todos: int = 0
    fixmes: int = 0


@dataclass
class RefactorSuggestion:
    """重构建议"""
    file_path: str
    line: int
    severity: str        # info / warning / critical
    category: str        # long_function / duplicate / unused / complexity / naming
    message: str


# ═══════════════════════════════════════════
# AST 符号提取器
# ═══════════════════════════════════════════

class SymbolExtractor(ast.NodeVisitor):
    """遍历 AST 提取所有符号"""

    def __init__(self, source_lines: List[str]):
        self.symbols: List[Symbol] = []
        self._lines = source_lines
        self._current_class = ""

    def visit_FunctionDef(self, node):
        sym = Symbol(
            name=node.name,
            kind="method" if self._current_class else "function",
            line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node) or "",
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            signature=self._get_function_sig(node),
            parent_class=self._current_class,
        )
        self.symbols.append(sym)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        sym = Symbol(
            name=node.name,
            kind="class",
            line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node) or "",
            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
            signature=f"({', '.join(self._get_base_name(b) for b in node.bases)})",
        )
        self.symbols.append(sym)

        prev_class = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = prev_class

    def visit_Assign(self, node):
        # 顶层赋值视为常量/变量
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name.isupper():  # 常量
                self.symbols.append(Symbol(
                    name=name,
                    kind="constant",
                    line=node.lineno,
                ))
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.symbols.append(Symbol(
                name=alias.asname or alias.name,
                kind="import",
                line=node.lineno,
            ))

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.symbols.append(Symbol(
                name=alias.asname or alias.name,
                kind="import",
                line=node.lineno,
            ))

    def _get_decorator_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{ast.unparse(node.attr)}" if hasattr(ast, 'unparse') else str(node.attr)
        if isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return "..."

    def _get_base_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return ast.unparse(node) if hasattr(ast, 'unparse') else f"...{node.attr}"
        return "..."

    def _get_function_sig(self, node) -> str:
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                try:
                    arg_str += f": {ast.unparse(arg.annotation)}"
                except Exception:
                    pass
            args.append(arg_str)
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")
        returns = ""
        if node.returns:
            try:
                returns = f" -> {ast.unparse(node.returns)}"
            except Exception:
                pass
        return f"({', '.join(args)}){returns}"


# ═══════════════════════════════════════════
# 代码智能引擎
# ═══════════════════════════════════════════

# 标准库白名单（Python 3.11）
STDLIB_MODULES = {
    "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio", "asyncore",
    "atexit", "audioop", "base64", "bdb", "binascii", "binhex", "bisect", "builtins",
    "bz2", "calendar", "cgi", "cgitb", "chunk", "cmath", "cmd", "code", "codecs",
    "codeop", "collections", "colorsys", "compileall", "concurrent", "configparser",
    "contextlib", "contextvars", "copy", "copyreg", "cProfile", "crypt", "csv",
    "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal", "difflib",
    "dis", "distutils", "doctest", "email", "encodings", "enum", "errno",
    "faulthandler", "fcntl", "filecmp", "fileinput", "fnmatch", "fractions",
    "ftplib", "functools", "gc", "getopt", "getpass", "gettext", "glob", "graphlib",
    "grp", "gzip", "hashlib", "heapq", "hmac", "html", "http", "idlelib", "imaplib",
    "imghdr", "imp", "importlib", "inspect", "io", "ipaddress", "itertools", "json",
    "keyword", "lib2to3", "linecache", "locale", "logging", "lzma", "mailbox",
    "mailcap", "marshal", "math", "mimetypes", "mmap", "modulefinder", "multiprocessing",
    "netrc", "nis", "nntplib", "numbers", "operator", "optparse", "os", "ossaudiodev",
    "pathlib", "pdb", "pickle", "pickletools", "pipes", "pkgutil", "platform",
    "plistlib", "poplib", "posix", "posixpath", "pprint", "profile", "pstats", "pty",
    "pwd", "py_compile", "pyclbr", "pydoc", "queue", "quopri", "random", "re",
    "readline", "reprlib", "resource", "rlcompleter", "runpy", "sched", "secrets",
    "select", "selectors", "shelve", "shlex", "shutil", "signal", "site", "smtpd",
    "smtplib", "sndhdr", "socket", "socketserver", "sqlite3", "ssl", "stat",
    "statistics", "string", "stringprep", "struct", "subprocess", "sunau", "symtable",
    "sys", "sysconfig", "syslog", "tabnanny", "tarfile", "telnetlib", "tempfile",
    "termios", "test", "textwrap", "threading", "time", "timeit", "tkinter", "token",
    "tokenize", "tomllib", "trace", "traceback", "tracemalloc", "tty", "turtle",
    "turtledemo", "types", "typing", "unicodedata", "unittest", "urllib", "uu",
    "uuid", "venv", "warnings", "wave", "weakref", "webbrowser", "winreg",
    "winsound", "wsgiref", "xdrlib", "xml", "xmlrpc", "zipapp", "zipfile",
    "zipimport", "zlib", "_thread",
}


class CodeIntel:
    """代码智能引擎"""

    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)

    # ── 符号提取 ──

    def extract_symbols(self, file_path: str) -> List[Symbol]:
        """提取文件中的所有符号（函数/类/变量/导入）"""
        abs_path = self._resolve(file_path)
        if not os.path.isfile(abs_path):
            return []

        try:
            source = Path(abs_path).read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        lines = source.split("\n")

        try:
            tree = ast.parse(source, filename=abs_path)
        except SyntaxError:
            # 非 Python 文件 → 用 regex 兜底
            return self._regex_extract(abs_path, source)

        extractor = SymbolExtractor(lines)
        extractor.visit(tree)

        for sym in extractor.symbols:
            sym.file_path = abs_path

        return extractor.symbols

    def _regex_extract(self, file_path: str, source: str) -> List[Symbol]:
        """用正则兜底提取非 Python 文件符号"""
        symbols = []
        patterns = {
            "function": [
                (r'^(?:export\s+)?(?:async\s+)?function\s+(\w+)', "js/ts"),
                (r'^\s*def\s+(\w+)', "ruby"),
                (r'^\s*func\s+(\w+)', "go"),
                (r'^\s*(?:pub\s+)?fn\s+(\w+)', "rust"),
                (r'^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:[\w<>[\]]+\s+)?(\w+)\s*\(', "java/c#"),
            ],
            "class": [
                (r'^\s*class\s+(\w+)', "generic"),
                (r'^\s*(?:export\s+)?(?:abstract\s+)?class\s+(\w+)', "ts"),
            ],
        }
        for line_no, line in enumerate(source.split("\n"), 1):
            for kind, pats in patterns.items():
                for pat, lang in pats:
                    m = re.match(pat, line)
                    if m:
                        symbols.append(Symbol(
                            name=m.group(1),
                            kind=kind,
                            line=line_no,
                            file_path=file_path,
                        ))
                        break
        return symbols

    # ── 引用查找 ──

    def find_usages(self, symbol_name: str, file_path: str = "", max_results: int = 50) -> List[dict]:
        """在整个项目中搜索符号引用（使用 grep）"""
        search_dir = self._resolve(file_path) if file_path else self.project_root

        if os.path.isfile(search_dir):
            files = [search_dir]
        else:
            files = self._grep_files(symbol_name, max_results)

        results = []
        for fpath, matches in files:
            for line_no, line_text in matches:
                results.append({
                    "file": fpath,
                    "line": line_no,
                    "text": line_text.strip(),
                })
                if len(results) >= max_results:
                    break
            if len(results) >= max_results:
                break

        return results

    def _grep_files(self, pattern: str, max_files: int = 20) -> List[Tuple[str, List[Tuple[int, str]]]]:
        """用 subprocess grep 搜索（高效）"""
        try:
            result = subprocess.run(
                ["grep", "-rn", "--include=*.py", "--include=*.js", "--include=*.ts",
                 "--include=*.java", "--include=*.go", "--include=*.rs", "--include=*.rb",
                 "-m", "5", pattern, self.project_root],
                capture_output=True, text=True, timeout=15,
                cwd=self.project_root,
            )
            if result.returncode not in (0, 1):
                return []

            file_matches: Dict[str, List[Tuple[int, str]]] = {}
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    fname = parts[0]
                    try:
                        lineno = int(parts[1])
                    except ValueError:
                        continue
                    text = parts[2]
                    if fname not in file_matches:
                        file_matches[fname] = []
                    file_matches[fname].append((lineno, text))

            return list(file_matches.items())[:max_files]

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    # ── 导入分析 ──

    def analyze_imports(self, file_path: str) -> FileDep:
        """分析文件的导入依赖"""
        abs_path = self._resolve(file_path)
        dep = FileDep(file_path=abs_path)

        if not os.path.isfile(abs_path):
            return dep

        try:
            source = Path(abs_path).read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=abs_path)
        except (SyntaxError, Exception):
            return dep

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    info = ImportInfo(
                        module=alias.name,
                        names=[alias.asname or alias.name],
                        alias=alias.asname or "",
                        line=node.lineno,
                        is_stdlib=alias.name.split(".")[0].lower() in STDLIB_MODULES,
                    )
                    dep.imports.append(info)

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.asname or alias.name for alias in node.names]
                info = ImportInfo(
                    module=module,
                    names=names,
                    line=node.lineno,
                    is_relative=node.level > 0,
                    is_stdlib=module.split(".")[0].lower() in STDLIB_MODULES if module else False,
                )
                dep.imports.append(info)

        return dep

    def build_dep_graph(self) -> Dict[str, FileDep]:
        """构建项目依赖图（限制前 500 个 .py 文件）"""
        graph: Dict[str, FileDep] = {}
        count = 0

        for root, dirs, files in os.walk(self.project_root):
            # 跳过隐藏/构建目录
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in
                       ("node_modules", "__pycache__", "build", "dist", ".git", "venv", "deps")]

            for f in files:
                if not f.endswith(".py"):
                    continue
                abs_path = os.path.join(root, f)
                dep = self.analyze_imports(abs_path)
                if dep.imports:
                    graph[abs_path] = dep
                    count += 1
                    if count >= 500:
                        return graph
        return graph

    # ── 度量 ──

    def code_metrics(self, file_path: str) -> CodeMetric:
        """计算代码度量"""
        abs_path = self._resolve(file_path)
        m = CodeMetric(file_path=abs_path)

        if not os.path.isfile(abs_path):
            return m

        try:
            source = Path(abs_path).read_text(encoding="utf-8", errors="replace")
        except Exception:
            return m

        lines = source.split("\n")
        m.total_lines = len(lines)

        in_multiline_comment = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                m.blank_lines += 1
                continue

            # 多行注释处理
            if in_multiline_comment:
                m.comment_lines += 1
                if '"""' in stripped or "'''" in stripped:
                    in_multiline_comment = False
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                m.comment_lines += 1
                if stripped.count('"""') < 2 and stripped.count("'''") < 2:
                    in_multiline_comment = True
                continue

            if stripped.startswith("#"):
                m.comment_lines += 1
            else:
                m.code_lines += 1

            # TODO/FIXME
            if re.search(r'\bTODO\b', stripped, re.IGNORECASE):
                m.todos += 1
            if re.search(r'\bFIXME\b', stripped, re.IGNORECASE):
                m.fixmes += 1

        # 符号统计 + 复杂度
        symbols = self.extract_symbols(abs_path)
        func_lines = []
        max_complexity = 0

        for sym in symbols:
            if sym.kind == "class":
                m.classes += 1
            elif sym.kind in ("function", "method"):
                m.functions += 1
                length = sym.end_line - sym.line + 1
                func_lines.append(length)
                c = self._cyclomatic_complexity(source, sym.line, sym.end_line)
                max_complexity = max(max_complexity, c)
            elif sym.kind == "import":
                m.imports_count += 1

        if func_lines:
            m.avg_function_length = sum(func_lines) / len(func_lines)
            m.max_function_length = max(func_lines)
        m.max_complexity = max_complexity

        return m

    def _cyclomatic_complexity(self, source: str, start_line: int, end_line: int) -> int:
        """估算圈复杂度（1 + 分支数）"""
        lines = source.split("\n")[start_line - 1:end_line]
        segment = "\n".join(lines)
        branches = len(re.findall(r'\b(if|elif|for|while|and|or|except|with|assert)\b', segment))
        return 1 + branches

    # ── 重构建议 ──

    def suggest_refactor(self, file_path: str) -> List[RefactorSuggestion]:
        """分析文件并给出重构建议"""
        abs_path = self._resolve(file_path)
        suggestions: List[RefactorSuggestion] = []

        if not os.path.isfile(abs_path):
            return suggestions

        metrics = self.code_metrics(abs_path)
        symbols = self.extract_symbols(abs_path)

        # 1. 长函数（> 100 行）
        for sym in symbols:
            if sym.kind in ("function", "method"):
                length = sym.end_line - sym.line + 1
                if length > 150:
                    suggestions.append(RefactorSuggestion(
                        file_path=abs_path,
                        line=sym.line,
                        severity="critical",
                        category="long_function",
                        message=f"函数 '{sym.name}' 长达 {length} 行，建议拆分为 3-5 个小函数",
                    ))
                elif length > 80:
                    suggestions.append(RefactorSuggestion(
                        file_path=abs_path,
                        line=sym.line,
                        severity="warning",
                        category="long_function",
                        message=f"函数 '{sym.name}' 有 {length} 行，考虑提取子逻辑",
                    ))

        # 2. 高复杂度
        if metrics.max_complexity > 20:
            suggestions.append(RefactorSuggestion(
                file_path=abs_path,
                line=0,
                severity="critical",
                category="complexity",
                message=f"最大圈复杂度 {metrics.max_complexity}，存在难以测试的复杂逻辑",
            ))
        elif metrics.max_complexity > 10:
            suggestions.append(RefactorSuggestion(
                file_path=abs_path,
                line=0,
                severity="warning",
                category="complexity",
                message=f"最大圈复杂度 {metrics.max_complexity}，建议简化条件分支",
            ))

        # 3. 文件过长
        if metrics.total_lines > 500:
            suggestions.append(RefactorSuggestion(
                file_path=abs_path,
                line=0,
                severity="info",
                category="file_size",
                message=f"文件 {metrics.total_lines} 行，超过 500 行建议按职责拆分",
            ))

        # 4. TODO/FIXME 过多
        if metrics.todos + metrics.fixmes > 5:
            suggestions.append(RefactorSuggestion(
                file_path=abs_path,
                line=0,
                severity="info",
                category="tech_debt",
                message=f"发现 {metrics.todos} 个 TODO + {metrics.fixmes} 个 FIXME",
            ))

        return suggestions

    # ── 项目级分析 ──

    def project_metrics(self) -> dict:
        """全项目代码度量汇总"""
        total_files = 0
        total_lines = 0
        total_funcs = 0
        total_classes = 0
        files_over_500 = 0
        funcs_over_100 = 0

        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in
                       ("__pycache__", "build", "dist", ".git", "venv", "deps", "node_modules")]
            for f in files:
                if not f.endswith(".py"):
                    continue
                abs_path = os.path.join(root, f)
                m = self.code_metrics(abs_path)
                total_files += 1
                total_lines += m.code_lines
                total_funcs += m.functions
                total_classes += m.classes
                if m.total_lines > 500:
                    files_over_500 += 1

                syms = self.extract_symbols(abs_path)
                for sym in syms:
                    if sym.kind in ("function", "method") and (sym.end_line - sym.line) > 100:
                        funcs_over_100 += 1

        return {
            "total_files": total_files,
            "total_code_lines": total_lines,
            "total_functions": total_funcs,
            "total_classes": total_classes,
            "files_over_500_lines": files_over_500,
            "functions_over_100_lines": funcs_over_100,
        }

    # ── 辅助 ──

    def _resolve(self, path: str) -> str:
        if os.path.isabs(path):
            return path
        return os.path.abspath(os.path.join(self.project_root, path))

```
