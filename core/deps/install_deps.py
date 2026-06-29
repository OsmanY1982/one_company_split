#!/usr/bin/env python3
"""
一人公司 · 宇宙版 —— 按需依赖安装器

打包时默认不装任何依赖。首次运行或功能触发时按需自动安装。
所有 .whl 文件存放在 deps/ 目录，安装器优先从本地安装（离线），
本地缺失时回退到 pip 在线安装。

用法：
    python deps/install_deps.py              # 安装所有核心依赖
    python deps/install_deps.py --group ai   # 安装 AI 相关依赖
    python deps/install_deps.py --group voice  # 安装语音相关依赖
    python deps/install_deps.py --group image  # 安装图像相关依赖
    python deps/install_deps.py --list       # 列出所有已安装/未安装状态

集成方式（在 main.py 或入口处）：
    from deps.install_deps import ensure_core_deps
    ensure_core_deps()  # 自动检查并安装缺失的核心依赖
"""

from __future__ import annotations

import os
import sys
import subprocess
import importlib
from pathlib import Path


# ═══════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════

DEPS_DIR = Path(__file__).resolve().parent

DEPENDENCY_GROUPS = {
    "core": {
        "desc": "核心依赖（运行时必需）",
        "packages": [
            "numpy", "psutil", "httpx", "requests",
            "qrcode", "PyQt5",
            "urllib3", "certifi", "charset_normalizer", "idna",
        ],
    },
    "voice": {
        "desc": "语音识别与合成",
        "packages": [
            "sounddevice", "faster_whisper", "ctranslate2", "onnxruntime",
        ],
    },
    "ai": {
        "desc": "AI / 大模型",
        "packages": [
            "huggingface_hub", "tokenizers", "protobuf",
        ],
    },
    "image": {
        "desc": "图像与视觉处理",
        "packages": [
            "pillow", "pyzbar", "av",
        ],
    },
    "crypto": {
        "desc": "加密与安全",
        "packages": [
            "cryptography", "bcrypt", "cffi",
        ],
    },
    "net": {
        "desc": "网络与爬虫",
        "packages": [
            "beautifulsoup4", "urllib3", "anyio", "h11",
            "httpcore", "idna", "charset_normalizer", "certifi",
        ],
    },
    "cli": {
        "desc": "命令行与工具",
        "packages": [
            "rich", "typer", "click", "pygments", "pyyaml",
            "markdown_it_py", "mdurl", "shellingham",
        ],
    },
    "data": {
        "desc": "数据与文件处理",
        "packages": [
            "fsspec", "filelock", "tqdm", "packaging",
            "soupsieve", "flatbuffers", "hf_xet",
            "matplotlib", "jinja2", "openpyxl",
        ],
    },
    "notify": {
        "desc": "系统通知",
        "packages": [
            "plyer",
        ],
    },
}


# ═══════════════════════════════════════════
# 安装器核心逻辑
# ═══════════════════════════════════════════

def _find_local_wheel(package_name: str) -> str | None:
    """在 deps/ 中查找匹配的 .whl 文件"""
    if not DEPS_DIR.exists():
        return None
    prefix = package_name.replace("-", "_").replace(".", "_")
    for f in sorted(DEPS_DIR.glob("*.whl"), reverse=True):
        name = f.name.lower()
        # 匹配规则：文件名以包名开头
        if name.startswith(prefix.lower()):
            return str(f)
    # 尝试更宽松匹配
    for f in sorted(DEPS_DIR.glob("*.whl"), reverse=True):
        name = f.name.lower().split("-")[0].replace("_", "-")
        if name == package_name.lower().replace("_", "-"):
            return str(f)
    return None


def _check_installed(package_name: str) -> bool:
    """检查包是否已安装"""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False


def _pip_install(package_name: str, wheel_path: str | None = None) -> bool:
    """安装单个包，优先本地 wheel；本地失败自动降级到在线安装"""
    # 第一轮：尝试本地 wheel
    if wheel_path and os.path.exists(wheel_path):
        try:
            print(f"  📦 本地安装: {os.path.basename(wheel_path)}")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--no-deps", wheel_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return True
        except subprocess.CalledProcessError:
            print(f"  ⚠️  本地不兼容，降级在线安装: {package_name}")

    # 第二轮：在线安装
    try:
        print(f"  🌐 在线安装: {package_name}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package_name],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        print(f"  ❌ 安装失败: {package_name}")
        return False


def install_group(group_name: str, force: bool = False) -> dict:
    """安装指定依赖组，返回 {package: success_bool}"""
    if group_name not in DEPENDENCY_GROUPS:
        print(f"未知依赖组: {group_name}")
        print(f"可用组: {', '.join(DEPENDENCY_GROUPS)}")
        return {}

    info = DEPENDENCY_GROUPS[group_name]
    print(f"\n━━━ {info['desc']} ━━━")

    results = {}
    for pkg in info["packages"]:
        if not force and _check_installed(pkg):
            print(f"  ✅ {pkg} (已安装)")
            results[pkg] = True
            continue

        wheel = _find_local_wheel(pkg)
        ok = _pip_install(pkg, wheel)
        results[pkg] = ok

    return results


def install_all(force: bool = False):
    """安装所有依赖组"""
    for group_name in DEPENDENCY_GROUPS:
        install_group(group_name, force=force)


def list_status():
    """列出所有依赖的安装状态"""
    print("\n══════════════ 依赖状态 ══════════════")
    for group_name, info in DEPENDENCY_GROUPS.items():
        print(f"\n[{group_name}] {info['desc']}:")
        for pkg in info["packages"]:
            installed = _check_installed(pkg)
            wheel = _find_local_wheel(pkg)
            wheel_label = f" (本地: {os.path.basename(wheel)})" if wheel else " (需在线)"
            status = "✅ 已安装" if installed else "❌ 未安装"
            print(f"  {status}  {pkg}{wheel_label if not installed else ''}")


def ensure(*package_names: str) -> bool:
    """
    按需确保模块可用 —— 兼容旧版 core.deps.ensure() 调用。
    检查模块是否可导入，不可用则 pip install。
    示例: ensure("PIL", "serial", "numpy")
    """
    missing = []
    for mod in package_names:
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(mod)
    if not missing:
        return True

    ok = True
    for pkg in missing:
        wheel = _find_local_wheel(pkg)
        if not _pip_install(pkg, wheel):
            ok = False
    return ok


def ensure_core_deps() -> bool:
    """
    确保核心依赖已安装。
    在 main.py 入口处调用，输出静默，仅首次安装时有提示。
    返回 True 表示核心依赖就绪。
    """
    info = DEPENDENCY_GROUPS["core"]
    all_ok = True
    need_install = any(not _check_installed(p) for p in info["packages"])

    if not need_install:
        return True

    print("⚙️  首次运行，正在安装核心依赖...")
    for pkg in info["packages"]:
        if not _check_installed(pkg):
            wheel = _find_local_wheel(pkg)
            ok = _pip_install(pkg, wheel)
            if not ok:
                all_ok = False
    return all_ok


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="一人公司 · 宇宙版 依赖安装器")
    parser.add_argument("--group", "-g", type=str,
                        help=f"安装指定依赖组: {', '.join(DEPENDENCY_GROUPS)}")
    parser.add_argument("--all", "-a", action="store_true",
                        help="安装所有依赖")
    parser.add_argument("--list", "-l", action="store_true",
                        help="列出依赖状态")
    parser.add_argument("--force", "-f", action="store_true",
                        help="强制重装已安装的包")

    args = parser.parse_args()

    if args.list:
        list_status()
    elif args.all:
        install_all(force=args.force)
    elif args.group:
        install_group(args.group, force=args.force)
    else:
        # 默认：确保核心依赖 + 显示状态
        ensure_core_deps()
        print("\n全部核心依赖就绪。使用 --list 查看完整状态。")
