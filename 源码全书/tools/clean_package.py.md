# `tools/clean_package.py`

> 路径：`tools/clean_package.py` | 行数：124


---


```python
# -*- coding: utf-8 -*-
"""
一人公司 项目打包瘦身工具

诊断项目中的冗余文件：
  - phoebe_tmp 临时纹理目录（零代码引用）
  - __pycache__ 缓存目录
  - 重复的 textures 文件（可通过共享路径优化）
  - 打包体积预估

用法：python tools/clean_package.py [--dry-run] [--clean]
"""
import os
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path("/Volumes/D盘工作区/一人公司拆分版/one_company_split")

CATEGORIES = {
    "phoebe_tmp": {
        "glob": "**/phoebe_tmp",
        "type": "dir",
        "desc": "临时纹理数据（未被任何代码引用）",
    },
    "__pycache__": {
        "glob": "**/__pycache__",
        "type": "dir",
        "desc": "Python 字节码缓存",
    },
    "texture_duplicates": {
        "patterns": ["2k_phoebe.png", "2k_4k_Phoebe.zip", "JVV_Phoebe.png"],
        "type": "file",
        "desc": "跨子项目重复的大纹理文件（非 core 副本）",
    },
}


def find_targets(dry_run: bool = False):
    """扫描并返回冗余目标列表"""
    targets = []
    total_bytes = 0

    # phoebe_tmp
    for entry in PROJECT_ROOT.rglob("phoebe_tmp"):
        if entry.is_dir() and ".git" not in str(entry):
            size = sum(f.stat().st_size for f in entry.rglob("*") if f.is_file())
            targets.append({
                "path": str(entry),
                "type": "dir",
                "size": size,
                "desc": "临时纹理数据（phoebe 中间产物）",
            })
            total_bytes += size

    # __pycache__
    for entry in PROJECT_ROOT.rglob("__pycache__"):
        if entry.is_dir() and ".git" not in str(entry):
            size = sum(f.stat().st_size for f in entry.rglob("*") if f.is_file())
            targets.append({
                "path": str(entry),
                "type": "dir",
                "size": size,
                "desc": "Python 字节码缓存",
            })
            total_bytes += size

    return targets, total_bytes


def print_report(targets, total_bytes):
    print(f"\n{'='*60}")
    print(f"  打包瘦身诊断报告")
    print(f"{'='*60}")
    print(f"  项目根目录: {PROJECT_ROOT}")
    print(f"  可清理目标: {len(targets)} 个")
    print(f"  可释放空间: {total_bytes / 1024 / 1024:.1f} MB")
    print(f"{'='*60}\n")

    for t in targets:
        print(f"  [{t['type']}] {t['path']}")
        print(f"        大小: {t['size'] / 1024:.1f} KB | {t['desc']}")


def clean_targets(targets):
    import shutil
    cleaned = 0
    failed = 0
    for t in targets:
        p = Path(t["path"])
        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            cleaned += 1
            print(f"  [OK] 已删除: {t['path']}")
        except Exception as e:
            failed += 1
            print(f"  [FAIL] {t['path']}: {e}")
    print(f"\n  清理完成: {cleaned} 成功, {failed} 失败")


def main():
    parser = argparse.ArgumentParser(description="一人公司 打包瘦身工具")
    parser.add_argument("--dry-run", action="store_true", help="仅扫描不删除")
    parser.add_argument("--clean", action="store_true", help="执行清理")
    args = parser.parse_args()

    targets, total_bytes = find_targets()
    print_report(targets, total_bytes)

    if args.clean and targets:
        resp = input("\n  确认删除以上文件? (y/N): ")
        if resp.lower() == "y":
            clean_targets(targets)
    elif args.clean:
        print("  没有发现需要清理的文件。")
    elif not args.dry_run:
        print("\n  提示: 使用 --dry-run 仅扫描, --clean 执行清理")


if __name__ == "__main__":
    main()

```
