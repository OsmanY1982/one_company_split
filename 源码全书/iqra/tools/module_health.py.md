# `iqra/tools/module_health.py`

> 路径：`iqra/tools/module_health.py` | 行数：289


---


```python
#!/usr/bin/env python3
"""
模块状态自检脚本 — 全项目模块导入链、存根一致性、关键类实例化一键自检

检测维度：
  1. 导入链：所有 .py 模块能否被 import（py_compile）
  2. 存根一致性：iqra 存根（3行 from core.xxx import *）指向的 core 源是否存在
  3. 关键类实例化：核心类能否被 import 且具有预期方法签名
  4. 工具注册：AgentBridge 工具总数和关键工具存在性

用法:
    python tools/module_health.py              # 快速检查（导入 + 存根）
    python tools/module_health.py --full       # 完整检查（含关键类实例化）
    python tools/module_health.py --project iqra  # 仅检查指定项目
"""

import ast
import os
import sys
import py_compile
import traceback
from pathlib import Path
from typing import List, Tuple, Dict, Set

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════════
# 检查 1：全模块导入链
# ═══════════════════════════════════════════════════════════════

def check_import_chain(project_dir: Path) -> Tuple[int, int, List[Tuple[str, str]]]:
    """
    遍历 project_dir 下所有 .py 文件，执行 py_compile 检查能否被解析。
    返回 (total, passed, failures)。
    """
    total, passed = 0, 0
    failures = []
    root = project_dir.parent  # 以项目父级为相对路径基准

    for fpath in project_dir.rglob("*.py"):
        if any(p in fpath.parts for p in (".venv", "__pycache__", ".git", "node_modules", "dist", "build")):
            continue
        total += 1
        try:
            py_compile.compile(str(fpath), doraise=True)
            passed += 1
        except (py_compile.PyCompileError, FileNotFoundError) as e:
            rel = str(fpath.relative_to(root))
            failures.append((rel, str(e)))

    return total, passed, failures


# ═══════════════════════════════════════════════════════════════
# 检查 2：存根一致性
# ═══════════════════════════════════════════════════════════════

def check_stub_consistency(project_dir: Path) -> Tuple[int, int, List[str]]:
    """
    扫描 project_dir 下所有 .py 文件，检测存根模式：
    `from core.xxx import *` 或 `from core.xxx.xxx import YYY`
    验证 import 的源模块是否存在。
    返回 (total_stubs, valid, broken)。
    """
    total, valid = 0, 0
    broken = []
    root = project_dir.parent  # 项目父级为相对路径基准

    for fpath in project_dir.rglob("*.py"):
        if any(p in fpath.parts for p in (".venv", "__pycache__", ".git", "node_modules")):
            continue
        try:
            source = fpath.read_text()
        except Exception:
            continue

        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("core."):
                total += 1
                # 将 core.xxx.yyy 转为文件路径
                module_parts = node.module.split(".")
                # 在 project_root 下查找
                pkg_dir = project_dir.parent  # 跳出 project_dir
                parts_path = "/".join(module_parts)
                target = Path(str(pkg_dir)) / (parts_path + ".py")
                if not target.exists():
                    # 尝试 __init__.py
                    target_init = Path(str(pkg_dir)) / parts_path / "__init__.py"
                    if not target_init.exists():
                        rel = str(fpath.relative_to(root))
                        broken.append(f"{rel} → from {node.module} import ... (源不存在)")

    return total, total - len(broken), broken


# ═══════════════════════════════════════════════════════════════
# 检查 3：关键类实例化
# ═══════════════════════════════════════════════════════════════

CRITICAL_CLASSES = {
    # (模块路径, 类名, 实例化参数, 需有的方法列表)
    "iqra": [
        ("iqra.core._bm25", "BM25", (), ["index", "search", "_score"]),
        ("iqra.core._tokenizer", "Tokenizer", (), []),  # 类方法，不检查实例
        ("iqra.core.semantic_search", "SemanticReranker", (), ["fit", "rerank"]),
        ("iqra.core._chunker", "CodeChunker", (), ["chunk"]),
        ("iqra.core.workspace_indexer", "WorkspaceIndexer", (), ["index", "search", "search_semantic"]),
        ("iqra.core.book_search", "BookSearcher", (), ["build_index", "search"]),
        ("iqra.core.memory", "Memory", (), ["add", "search", "get"]),
    ],
}

def check_critical_classes(project_name: str) -> Tuple[int, int, List[str]]:
    """实例化关键类并验证方法签名"""
    failed = []
    classes = CRITICAL_CLASSES.get(project_name, [])
    total = len(classes)

    sys.path.insert(0, str(PROJECT_ROOT.parent.parent if project_name == "iqra" else PROJECT_ROOT.parent))

    for module_path, class_name, args, methods in classes:
        try:
            mod = __import__(module_path, fromlist=[class_name])
            cls = getattr(mod, class_name)
            # 实例化
            instance = cls(*args) if args else cls()
            # 验证方法
            for method in methods:
                if not hasattr(instance, method):
                    failed.append(f"{class_name}: 缺少方法 {method}")
        except Exception as e:
            failed.append(f"{class_name}: {e}")

    return total, total - len(failed), failed


# ═══════════════════════════════════════════════════════════════
# 检查 4：工具注册
# ═══════════════════════════════════════════════════════════════

REQUIRED_TOOLS = [
    "search_codebase", "search_project_book", "read_file", "write_file",
    "list_directory", "edit_file", "run_shell", "run_python",
]


def check_tool_registry() -> Tuple[bool, List[str]]:
    """验证 AgentBridge 工具注册"""
    try:
        from core.modules.intelligence.agent_bridge import AgentBridge
        bridge = AgentBridge()
        registered = list(bridge._tools.keys()) if hasattr(bridge, "_tools") else []
        missing = [t for t in REQUIRED_TOOLS if t not in registered]
        return len(missing) == 0, missing
    except Exception as e:
        return False, [f"AgentBridge 导入失败: {e}"]


# ═══════════════════════════════════════════════════════════════
# 检查 5：模块概览
# ═══════════════════════════════════════════════════════════════

def module_overview(project_dir: Path) -> Dict[str, int]:
    """统计各子目录模块分布"""
    stats = {}
    for fpath in project_dir.rglob("*.py"):
        if any(p in fpath.parts for p in (".venv", "__pycache__", ".git", "node_modules")):
            continue
        rel = fpath.relative_to(project_dir)
        top = rel.parts[0] if rel.parts else "root"
        stats[top] = stats.get(top, 0) + 1
    return stats


# ═══════════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════════

PROJECTS = {
    "iqra": PROJECT_ROOT,
    "core": PROJECT_ROOT.parent / "core",
    "management-system": PROJECT_ROOT.parent / "management-system",
    "planetarium": PROJECT_ROOT.parent / "planetarium",
}

def main():
    full_mode = "--full" in sys.argv
    project_filter = None
    for i, arg in enumerate(sys.argv):
        if arg == "--project" and i + 1 < len(sys.argv):
            project_filter = sys.argv[i + 1]

    targets = {project_filter: PROJECTS[project_filter]} if project_filter else PROJECTS

    print("=" * 60)
    print("  模块状态自检报告")
    print(f"  时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  模式: {'完整' if full_mode else '快速'} | 项目: {project_filter or '全部'}")
    print("=" * 60)

    all_ok = True
    grand_total = 0
    grand_passed = 0

    for name, project_dir in targets.items():
        if not project_dir.exists():
            print(f"\n  [{name}] ❌ 目录不存在: {project_dir}")
            continue

        print(f"\n{'─' * 60}")
        print(f"  [{name}] 项目: {project_dir.relative_to(PROJECT_ROOT.parent)}")
        print(f"{'─' * 60}")

        # --- 模块概览 ---
        overview = module_overview(project_dir)
        total_modules = sum(overview.values())
        print(f"  模块数: {total_modules}")
        for subdir, count in sorted(overview.items()):
            print(f"    {subdir}/: {count}")

        # --- 1. 导入链 ---
        print(f"\n  [1] 导入链检查 ...")
        total, passed, failures = check_import_chain(project_dir)
        grand_total += total
        grand_passed += passed
        if failures:
            all_ok = False
            print(f"  ⚠️  {total - passed}/{total} 失败:")
            for fpath, err in failures[:10]:
                err_short = err[:100].split("\n")[0]
                print(f"    ❌ {fpath}: {err_short}")
            if len(failures) > 10:
                print(f"    ... 及另外 {len(failures) - 10} 个")
        else:
            print(f"  ✅ {passed}/{total} 全部通过")

        # --- 2. 存根一致性 ---
        print(f"\n  [2] 存根一致性 ...")
        total_stubs, valid_stubs, broken_stubs = check_stub_consistency(project_dir)
        if broken_stubs:
            all_ok = False
            for b in broken_stubs[:10]:
                print(f"    ⚠️  {b}")
        else:
            print(f"  ✅ {total_stubs} 个存根全部有效")

        # --- 3. 关键类实例化（full 模式） ---
        if full_mode and name in CRITICAL_CLASSES:
            print(f"\n  [3] 关键类实例化 ...")
            total_cls, passed_cls, failed_cls = check_critical_classes(name)
            if failed_cls:
                all_ok = False
                for f in failed_cls:
                    print(f"    ❌ {f}")
            else:
                print(f"  ✅ {passed_cls}/{total_cls} 全部通过")

    # --- 4. 工具注册（跨项目检查） ---
    if full_mode:
        print(f"\n{'─' * 60}")
        print(f"  [4] AgentBridge 工具注册")
        print(f"{'─' * 60}")
        ok, missing = check_tool_registry()
        if not ok:
            all_ok = False
            for m in missing:
                print(f"  ❌ {m}")
        else:
            print(f"  ✅ 关键工具全部注册")

    # --- 总结 ---
    print(f"\n{'=' * 60}")
    if all_ok:
        print(f"  ✅ 所有检查通过 ({grand_passed}/{grand_total} 模块)")
    else:
        print(f"  ❌ 发现问题 ({grand_total - grand_passed}/{grand_total} 失败)")
    print(f"{'=' * 60}")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()

```
