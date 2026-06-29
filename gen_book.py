#!/usr/bin/env python3
"""源码全书生成器 — 扫描源码目录，为每个 .py 文件生成独立文档到 源码全书/ 目录"""
import os
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "源码全书"

SKIP_DIRS = {"__pycache__", "deps", ".git", "build", "dist", "assets", ".venv", "env",
             "docs", "resources", "temp", "output", "项目全书", "源码全书", "被删文件存档"}
SKIP_EXT = {".pyc", ".pyo", ".whl", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".icns",
            ".qrc", ".db", ".sqlite", ".log", ".bak"}


def build_tree(path: Path, prefix: str = "") -> list[str]:
    lines = []
    entries = sorted(
        [e for e in path.iterdir()
         if e.name not in SKIP_DIRS and not e.name.startswith(".")],
        key=lambda e: (not e.is_dir(), e.name.lower()))
    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        if entry.is_dir():
            lines.append(f"{prefix}{connector}{entry.name}/")
            lines.extend(build_tree(entry, prefix + ("    " if i == len(entries) - 1 else "│   ")))
        elif entry.suffix == ".py":
            lines.append(f"{prefix}{connector}{entry.name}")
    return lines


def collect_files(path: Path) -> list[Path]:
    files = []
    for entry in sorted(path.iterdir()):
        if entry.name in SKIP_DIRS or entry.name.startswith("."):
            continue
        if entry.is_dir():
            files.extend(collect_files(entry))
        elif entry.suffix == ".py":
            files.append(entry)
    return files


def main():
    # 清空并重建输出目录
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    files = collect_files(ROOT)
    total_size = 0

    # 为每个 .py 生成独立 .md
    for f in files:
        rel = f.relative_to(ROOT)
        out_subdir = OUT_DIR / rel.parent
        out_subdir.mkdir(parents=True, exist_ok=True)

        out_file = out_subdir / (rel.name + ".md")
        try:
            raw = f.read_text(encoding="utf-8")
        except Exception:
            raw = "# 无法读取"

        lines_count = raw.count("\n") + (0 if raw.endswith("\n") else 1)
        md = [f"# `{rel}`\n"]
        md.append(f"> 路径：`{rel}` | 行数：{lines_count}\n\n")
        md.append("---\n\n")
        md.append(f"```python\n{raw}\n```\n")

        content = "\n".join(md)
        out_file.write_text(content, encoding="utf-8")
        total_size += len(content)

    # 生成 README.md 索引
    tree_lines = build_tree(ROOT)
    readme = ["# 一人公司 · 宇宙版 — 源码全书\n"]
    readme.append(f"> 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    readme.append(f"> 共 {len(files)} 个模块，每个 `.py` 文件独立为一个文档\n\n")
    readme.append("---\n\n")
    readme.append("## 目录结构\n\n```\n.\n")
    for line in tree_lines:
        readme.append(line + "\n")
    readme.append("```\n\n")
    readme.append("---\n\n")
    readme.append("## 模块列表\n\n")

    for f in files:
        rel = f.relative_to(ROOT)
        md_rel = Path(str(rel) + ".md")
        readme.append(f"- [`{rel}`](./{md_rel})\n")

    index_path = OUT_DIR / "README.md"
    index_path.write_text("".join(readme), encoding="utf-8")

    total_kb = (total_size + len("".join(readme))) / 1024
    print(f"源码全书已更新 — {OUT_DIR}/ ({len(files)} 个模块文件, {total_kb:.1f} KB)")


if __name__ == "__main__":
    main()
