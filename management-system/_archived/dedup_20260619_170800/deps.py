"""
依赖按需安装 — 从项目内置 deps/ 目录自动解压 wheel 到 site-packages
用户首次使用某功能时触发，未用到的依赖不占空间
"""
import os
import sys
import traceback
import zipfile
import importlib
from pathlib import Path
from typing import Optional, Union


def _find_deps_dir() -> Optional[Path]:
    """定位 deps 目录（开发模式 vs 打包模式）"""
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后，deps 在 bundle 资源目录下
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        candidate = base / "deps"
        return candidate if candidate.is_dir() else None
    else:
        # 开发模式：项目根目录下的 deps/
        candidate = Path(__file__).resolve().parent.parent / "deps"
        return candidate if candidate.is_dir() else None


def _build_index(deps_dir: Path) -> dict[str, list[Path]]:
    """扫描 deps 目录，建立 模块名 → [wheel路径,...] 映射"""
    index: dict[str, list[Path]] = {}
    for whl in sorted(deps_dir.glob("*.whl")):
        # wheel 文件名格式: {name}-{version}-{py_tag}-{abi_tag}-{plat_tag}.whl
        name = whl.name.split("-")[0].lower().replace("_", "-")
        index.setdefault(name, []).append(whl)
    return index


# ── 公开 API ──

def install(module_names: Union[str, list]) -> bool:
    """
    安装缺失的模块（从 deps/ 解压 wheel 到 site-packages）。
    返回 True 表示全部安装成功，False 表示部分或全部失败。
    """
    deps_dir = _find_deps_dir()
    if deps_dir is None:
        # 没有 deps 目录（打包时未包含或开发环境未下载）
        return False

    if isinstance(module_names, str):
        module_names = [module_names]

    index = _build_index(deps_dir)
    site_pkg = _get_site_packages()

    if site_pkg is None:
        return False

    for mod in module_names:
        key = mod.lower().replace("_", "-")
        wheels = index.get(key)
        if not wheels:
            continue
        for whl in wheels:
            _extract_wheel(whl, site_pkg)
        _ensure_module_loaded(mod)

    # 验证
    for mod in module_names:
        try:
            importlib.import_module(mod)
        except ImportError:
            return False
    return True


def ensure(*module_names: str) -> bool:
    """检查模块是否可用，不可用则从 deps 安装。比 install 更安全，已安装的不重复处理。"""
    missing = []
    for mod in module_names:
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(mod)
    if not missing:
        return True
    return install(missing)


# ── 内部工具 ──

def _get_site_packages() -> Optional[Path]:
    """获取当前 Python 环境的 site-packages 路径"""
    try:
        import site
        dirs = site.getsitepackages()
        if dirs:
            return Path(dirs[0])
    except Exception:
        traceback.print_exc()
    # 兜底：从 sys.path 中找 site-packages
    for p in sys.path:
        if "site-packages" in p and os.path.isdir(p):
            return Path(p)
    return None


def _extract_wheel(wheel_path: Path, site_pkg: Path) -> None:
    """解压 wheel 到 site-packages（跳过已存在的文件）"""
    site_pkg.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(wheel_path, "r") as zf:
            for member in zf.namelist():
                target = site_pkg / member
                if target.exists():
                    continue
                if member.endswith("/"):
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src, open(target, "wb") as dst:
                        dst.write(src.read())
    except Exception:
        traceback.print_exc()


def _ensure_module_loaded(mod_name: str) -> None:
    """强制刷新 import cache，确保刚解压的模块能被发现"""
    importlib.invalidate_caches()
