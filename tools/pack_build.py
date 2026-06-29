# -*- coding: utf-8 -*-
"""
PyInstaller 打包配置 — 一人公司

生成独立的 macOS .app 包，体积优化：排除不必要的库、压缩资源。

用法：
    pyinstaller pack_core.spec        # 打包 core
    pyinstaller pack_planetarium.spec  # 打包 planetarium
"""
import os
from pathlib import Path

PROJECT_ROOT = Path("/Volumes/D盘工作区/一人公司拆分版/one_company_split")
APP_NAME = "OneCompany"
BUNDLE_ID = "com.onecompany.app"

# ── 排除列表（减少包体积） ──
EXCLUDES = [
    "tkinter", "unittest", "test", "pydoc",
    "distutils", "setuptools", "pip",
    "PyQt5.QtWebEngine", "PyQt5.QtWebEngineWidgets",
    "matplotlib.tests", "numpy.tests", "scipy.tests",
    "pandas.tests",
]

# ── 核心数据文件 ──
DATAS = [
    ("data/*.db", "data"),
    ("data/*.json", "data"),
    ("assets/*", "assets"),
]

# ── 隐式导入 ──
HIDDEN_IMPORTS = [
    "core.database",
    "core.config",
    "core.operation_log",
    "modules.auth.auth_service",
    "modules.auth.auth_service_sync",
    "modules.auth.auth_service_membership",
    "modules.system.system_logs_service",
]

# ── PyInstaller spec 模板 ──
SPEC_TEMPLATE = '''# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — {project}"""

a = Analysis(
    ['{entry}'],
    pathex=['{project_root}'],
    binaries=[],
    datas={datas},
    hiddenimports={hidden_imports},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={excludes},
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='{app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''

# ── 子项目打包入口配置 ──
PROJECTS = {
    "core": {"entry": "core/main.py", "app_name": "OneCompany"},
    "iqra": {"entry": "iqra/main.py", "app_name": "IqraAI"},
}


def generate_specs():
    """为所有子项目生成 .spec 文件"""
    for proj, cfg in PROJECTS.items():
        spec_path = PROJECT_ROOT / f"pack_{proj}.spec"
        entry = PROJECT_ROOT / cfg["entry"]
        if not entry.exists():
            print(f"  [SKIP] {cfg['entry']} 不存在")
            continue

        datas = [(str(PROJECT_ROOT / d[0]), d[1]) for d in DATAS if (PROJECT_ROOT / d[0].replace("*", "")).parent.exists()]

        content = SPEC_TEMPLATE.format(
            project=proj,
            entry=str(entry),
            project_root=str(PROJECT_ROOT),
            datas=repr(datas),
            hidden_imports=repr(HIDDEN_IMPORTS),
            excludes=repr(EXCLUDES),
            app_name=cfg["app_name"],
        )
        spec_path.write_text(content, encoding="utf-8")
        print(f"  [OK] {spec_path}")


if __name__ == "__main__":
    print("生成 PyInstaller spec 文件...")
    generate_specs()
    print(f"\n打包命令:")
    for proj, cfg in PROJECTS.items():
        print(f"  pyinstaller pack_{proj}.spec")
