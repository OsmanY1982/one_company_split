# `iqra/tools/check_imports.py`

> 路径：`iqra/tools/check_imports.py` | 行数：359


---


```python
#!/usr/bin/env python3
"""
导入引用完整性检查器
扫描 modules/ 下所有 .py 文件，检测"引用但未导入"的符号。
每次代码修改后运行此脚本，防止 NameError 回归。

用法:
    python tools/check_imports.py          # 检查所有模块
    python tools/check_imports.py --strict # 同时检查 core/ 目录
"""

import ast
import os
import sys

# ── 配置 ──────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES_DIR = os.path.join(PROJECT_ROOT, "modules")
CORE_DIR = os.path.join(PROJECT_ROOT, "core")

# 忽略的变量名（内置、PyQt 隐式注入、跨模块传递等）
IGNORE_NAMES = {
    # Python 内置
    "True", "False", "None", "self", "super", "cls",
    "__name__", "__file__", "__doc__", "__init__", "Exception",
    "object", "type", "str", "int", "float", "bool", "list", "dict",
    "set", "tuple", "range", "len", "print", "open", "isinstance",
    "hasattr", "getattr", "setattr", "enumerate", "zip", "sorted",
    "reversed", "any", "all", "map", "filter", "next", "iter",
    "lambda", "yield", "return", "pass", "break", "continue",
    "raise", "import", "from", "KeyError", "ValueError", "TypeError",
    "RuntimeError", "OSError", "IOError", "EOFError", "IndexError",
    "AttributeError", "NameError", "NotImplementedError", "StopIteration",
    # 常见标准库
    "json", "os", "sys", "math", "random", "time", "datetime",
    "traceback", "base64", "hashlib", "struct", "io", "textwrap",
    "zipfile", "logging", "atexit", "tempfile", "threading", "signal",
    "platform", "collections", "functools", "itertools", "subprocess",
    "pathlib", "Path",
    # PyQt 隐式可用
    "Qt", "QApplication", "QWidget", "QMainWindow", "QDialog",
    "QVBoxLayout", "QHBoxLayout", "QGridLayout", "QStackedWidget",
    "QLabel", "QLineEdit", "QPushButton", "QComboBox", "QCheckBox",
    "QTextEdit", "QPlainTextEdit", "QFrame", "QScrollArea", "QTabWidget",
    "QTableWidget", "QTableWidgetItem", "QHeaderView", "QSplitter",
    "QGroupBox", "QListWidget", "QListWidgetItem", "QTreeWidget",
    "QTreeWidgetItem", "QMessageBox", "QFileDialog", "QInputDialog",
    "QColorDialog", "QFontDialog", "QProgressBar", "QSlider",
    "QSpinBox", "QDoubleSpinBox", "QToolBar", "QStatusBar", "QMenuBar",
    "QMenu", "QAction", "QShortcut", "QTimer", "QThread", "QObject",
    "QPainter", "QColor", "QPen", "QBrush", "QFont", "QIcon",
    "QPixmap", "QImage", "QLinearGradient", "QRadialGradient",
    "QPainterPath", "QRectF", "QPointF", "QSizeF", "QPoint", "QSize",
    "QRect", "QMargins", "Qt", "pyqtSignal", "pyqtSlot", "QMouseEvent",
    "QKeyEvent", "QWheelEvent", "QResizeEvent", "QCloseEvent",
    "QShowEvent", "QHideEvent", "QEvent", "QCursor",
    "QStyle", "QStyleFactory", "QStyleOption", "QStylePainter",
    "QCoreApplication", "QThreadPool", "QRunnable", "QMutex",
    "QMutexLocker", "QWaitCondition", "QSemaphore", "QSettings",
    "QStandardPaths", "QDir", "QProcess", "QUrl",
    "QNetworkAccessManager", "QNetworkRequest", "QNetworkReply",
    "QJsonDocument", "QJsonObject", "QJsonArray", "QJsonValue",
    "QByteArray", "QBuffer",
    "QWebEngineView", "QWebEnginePage", "QWebEngineSettings",
    "QWebEngineProfile",
    # Markdown / HTML
    "markdown", "html", "etree", "ElementTree",
}


def scan_directory(root_dir: str) -> list[tuple[str, list[str], list[str]]]:
    """
    扫描目录，返回 violations 列表。
    每个元素: (相对路径, [未导入的变量名], [引用行号])
    """
    violations = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d != '__pycache__']
        for fname in filenames:
            if not fname.endswith('.py'):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath) as f:
                    source = f.read()
            except Exception:
                continue
            try:
                tree = ast.parse(source)
            except SyntaxError:
                print(f"[WARN] 语法错误: {os.path.relpath(fpath, PROJECT_ROOT)}")
                continue

            # 收集本文件定义的名字和导入的名字
            defined = set()
            imported = set()

            for node in ast.walk(tree):
                # 函数/类定义
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    defined.add(node.name)
                    # 函数参数也视为定义
                    for arg in node.args.args:
                        defined.add(arg.arg)
                    if node.args.vararg:
                        defined.add(node.args.vararg.arg)
                    if node.args.kwarg:
                        defined.add(node.args.kwarg.arg)
                elif isinstance(node, ast.ClassDef):
                    defined.add(node.name)
                # 赋值定义
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            defined.add(target.id)
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    defined.add(node.target.id)
                elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
                    defined.add(node.target.id)
                # For 循环变量
                elif isinstance(node, ast.For):
                    if isinstance(node.target, ast.Name):
                        defined.add(node.target.id)
                # import 语句
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imported.add(alias.asname or alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        name = alias.asname or alias.name
                        if name != '*':
                            imported.add(name)

            # 收集所有在表达式中使用的变量名（排除定义位置）
            all_toplevel = set()
            for node in ast.iter_child_nodes(tree):
                # 跳过 import 和定义语句中的 Name
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                for child in ast.walk(node):
                    if isinstance(child, ast.Name):
                        all_toplevel.add(child.id)

            # undefined = 引用了但既不是内置也不是本文件定义的也不是导入的
            undefined = all_toplevel - defined - imported - IGNORE_NAMES

            if undefined:
                rel = os.path.relpath(fpath, PROJECT_ROOT)
                # 找出引用位置
                lines = source.split('\n')
                ref_lines = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and node.id in undefined:
                        if hasattr(node, 'lineno'):
                            ref_lines.append(f"{node.id}:L{node.lineno}")
                violations.append((rel, sorted(undefined), ref_lines[:5]))  # 最多5个引用

    return violations


def check_exports_used_without_import(theme_file: str, scan_dir: str) -> list[tuple]:
    """
    专项检查：dark_tool_theme 常量是否被正确导入。
    扫描 scan_dir 下所有文件，检测引用了 theme 导出但未导入 theme 模块的文件。
    """
    with open(theme_file) as f:
        tree = ast.parse(f.read())
    exports = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    exports.add(target.id)

    bad_files = []
    for dirpath, dirnames, filenames in os.walk(scan_dir):
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d != '__pycache__']
        for fname in filenames:
            if not fname.endswith('.py'):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath) as f:
                    source = f.read()
            except:
                continue
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue

            # 检查是否导入了 dark_tool_theme
            has_import = False
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == 'core.dark_tool_theme':
                    has_import = True
                    break
            if has_import:
                continue

            # 检查是否引用了导出常量
            used = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id in exports:
                    used.add(node.id)
            if used:
                rel = os.path.relpath(fpath, PROJECT_ROOT)
                bad_files.append((rel, sorted(used)))

    return bad_files


def auto_fix(theme_file: str, scan_dir: str) -> int:
    """
    自动修复：为引用了 dark_tool_theme 常量但未导入的文件添加 import。
    返回修复的文件数。
    """
    bad = check_exports_used_without_import(theme_file, scan_dir)
    if not bad:
        return 0

    count = 0
    for rel_path, used_vars in bad:
        fpath = os.path.join(PROJECT_ROOT, rel_path)
        with open(fpath) as f:
            lines = f.readlines()

        # 拼装 import 语句
        names_str = ", ".join(used_vars)
        new_line = f"from core.dark_tool_theme import {names_str}\n"

        # 找到最佳插入位置：最后一个非 __future__ 的 import 行之后
        # 需处理多行 import（括号跨行），跳过 import (...) 区域
        insert_at = 0
        last_import_line = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("from __future__"):
                continue
            if stripped.startswith(("import ", "from ")):
                last_import_line = i
                # 多行 import（括号跨行）：跳过到闭合括号
                if "(" in stripped and ")" not in stripped:
                    depth = 1
                    for j in range(i + 1, len(lines)):
                        for ch in lines[j]:
                            if ch == "(":
                                depth += 1
                            elif ch == ")":
                                depth -= 1
                        if depth == 0:
                            last_import_line = j
                            break
            elif last_import_line > 0 and stripped and not stripped.startswith("#"):
                break

        if last_import_line > 0:
            insert_at = last_import_line + 1
        else:
            # 没有找到合适的 import 行，插在 docstring 之后
            in_docstring = False
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    if not in_docstring and i > 0:
                        # 多行 docstring 结束
                        in_docstring = not in_docstring
                    elif not in_docstring and i == 0:
                        in_docstring = True
                    elif in_docstring:
                        in_docstring = False
                        insert_at = i + 1
                        break
                elif not in_docstring and stripped and not stripped.startswith("#"):
                    insert_at = i
                    break
            # 如果前面没找到，放在文件头
            if insert_at == 0:
                insert_at = 0

        # 执行插入
        lines.insert(insert_at, new_line)
        with open(fpath, "w") as f:
            f.writelines(lines)

        print(f"  ✅ {rel_path} → +{len(used_vars)} import(s)")
        count += 1

    return count


def main():
    fix_mode = '--fix' in sys.argv
    strict = '--strict' in sys.argv

    print("=" * 56)
    if fix_mode:
        print("  导入引用完整性检查 + 自动修复")
    else:
        print("  导入引用完整性检查")
    print("=" * 56)

    theme_path = os.path.join(PROJECT_ROOT, "core", "dark_tool_theme.py")

    # ── 检测 ──
    print(f"\n[1/2] dark_tool_theme 导入完整性 ...")
    bad = check_exports_used_without_import(theme_path, MODULES_DIR)

    if bad:
        print(f"\n  ⚠️  {len(bad)} 个文件缺少导入:")
        for fpath, names in sorted(bad):
            print(f"  📄 {fpath}")
            for n in names:
                print(f"     ❌ {n}")

        # ── 自动修复 ──
        if fix_mode:
            print(f"\n  🔧 自动修复中 ...")
            fixed = auto_fix(theme_path, MODULES_DIR)
            print(f"\n  ✅ 已修复 {fixed} 个文件")
            # 修复后重新验证
            bad = check_exports_used_without_import(theme_path, MODULES_DIR)
    else:
        print("  ✅ 全部正确导入")

    # 第 2 层：通用未定义变量检查（仅 --strict 时启用，噪声大）
    if strict:
        print(f"\n[2/2] 通用未定义变量扫描 {os.path.relpath(MODULES_DIR, PROJECT_ROOT)}/ ...")
        print("  (此模式噪声较大，请人工筛选)")
        v = scan_directory(MODULES_DIR)
        if v:
            print(f"\n  ⚠️  {len(v)} 个文件存在可疑引用:")
            for fpath, names, refs in sorted(v):
                print(f"\n  📄 {fpath}")
                for n in names:
                    print(f"     ❌ {n}")
                for r in refs[:3]:
                    print(f"        → {r}")
        else:
            print("  ✅ 无可疑引用")

    # 总结
    has_error = len(bad) > 0
    print(f"\n{'=' * 56}")
    if has_error:
        if not fix_mode:
            print("  ❌ 发现问题，使用 --fix 自动修复，或手动修复后重新运行")
        else:
            print("  ❌ 仍有未修复项，请人工处理")
        sys.exit(1)
    else:
        print("  ✅ 全部通过")
        sys.exit(0)


if __name__ == '__main__':
    main()

```
