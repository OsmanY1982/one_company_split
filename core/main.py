"""
一人公司 · 宇宙版
启动入口

用法:
    python main.py                # 正常模式：显示登录窗口
    python main.py --floating-only # 极简浮球模式：跳过登录，直接显示悬浮球
"""
from __future__ import annotations

import sys
import os
import json
import atexit
import tempfile
import traceback
import threading
import logging
from datetime import datetime
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.dirname(__file__))  # core/ 优先于 one_company_split/，确保本项目的 modules 不被顶层 modules 子集遮盖
sys.path.append(os.path.join(os.path.dirname(__file__), "services"))

# ── 按需安装核心依赖（首次运行自动触发）──
# ensure_core_deps() skipped on Windows (deps pre-installed)

# ── 全局异常捕获 ──
LOG_DIR = os.path.join(os.path.dirname(__file__), "log")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "crash.log"),
    level=logging.ERROR,
    format="%(asctime)s [%(threadName)s] %(message)s",
    encoding="utf-8"
)

def _global_excepthook(exc_type: type, exc_value: BaseException, exc_tb: Any) -> None:
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logging.error(f"未捕获异常:\n{tb_str}")
    from PyQt5.QtWidgets import QApplication, QMessageBox
    app = QApplication.instance()
    if app:
        QMessageBox.critical(None, "系统错误",
            f"发生未处理的异常:\n\n{exc_value}\n\n详细日志已写入 log/crash.log")
    sys.__excepthook__(exc_type, exc_value, exc_tb)

def _thread_excepthook(args: threading.ExceptHookArgs) -> None:
    tb_str = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
    logging.error(f"子线程未捕获异常:\n{tb_str}")

sys.excepthook = _global_excepthook
threading.excepthook = _thread_excepthook

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPainterPath
from PyQt5.QtCore import Qt, QCoreApplication
from modules.auth.login_window import LoginWindow

# ── 极简浮球模式 ──
LOCK_FILE = os.path.join(tempfile.gettempdir(), "iqra_floating_planet.pid").replace("\\", "/")
CMD_FILE = os.path.join(tempfile.gettempdir(), "iqra_floating_cmd").replace("\\", "/")
PROJECT_ROOT = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(PROJECT_ROOT, "iqra", "data", "iqra_config.json")


def _init_engine() -> tuple[Any, dict]:
    """初始化 iqra 引擎（供 floating-only 模式使用）。"""
    if not os.path.exists(CONFIG_PATH):
        return None, {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        return None, {}

    try:
        from iqra.core.llm_backend import BackendFactory, ProviderConfig
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)
        elif sys.path[0] != PROJECT_ROOT:
            sys.path.remove(PROJECT_ROOT)
            sys.path.insert(0, PROJECT_ROOT)

        active_provider_id = config.get("active_provider_id", "")
        provider_type = config.get("active_provider_type", "local")
        if provider_type == "local":
            provider_data = config.get("local_providers", {}).get(active_provider_id, {})
        else:
            provider_data = config.get("cloud_providers", {}).get(active_provider_id, {})
        if not provider_data:
            return None, config

        provider_config = ProviderConfig(
            name=provider_data.get("name", active_provider_id),
            provider_type=provider_data.get("provider_type", "openai_compatible"),
            base_url=provider_data.get("base_url", ""),
            model=provider_data.get("model", ""),
            api_key=provider_data.get("api_key", ""),
        )
        backend = BackendFactory.create(provider_config)
        from modules.intelligence.agent_bridge import AgentBridge
        engine = AgentBridge(backend)

        try:
            engine.load_session()
        except Exception:
            pass

        return engine, config
    except Exception:
        return None, config


def _run_floating_only(app: QApplication) -> None:
    """极简浮球模式：只显示悬浮球，无登录窗口/智能中心。"""
    engine, config = _init_engine()
    from modules.intelligence.iqra_floating_planet import FloatingPlanet

    planet = FloatingPlanet(
        iqra_engine=engine,
        role="admin",
        membership_info={},
        config=config,
    )
    planet.show()

    # 写入 PID 锁文件
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    atexit.register(lambda: os.path.exists(LOCK_FILE) and os.remove(LOCK_FILE))

    # ── IPC 命令监听 ──
    def _check_ipc_cmd() -> None:
        if not os.path.exists(CMD_FILE):
            return
        try:
            with open(CMD_FILE, "r") as f:
                cmd = f.read().strip()
            os.remove(CMD_FILE)
            if cmd in ("show", "toggle"):
                if not planet.isVisible():
                    planet.show()
                    planet.raise_()
                elif cmd == "toggle":
                    planet.hide()
            elif cmd == "hide":
                planet.hide()
        except OSError:
            pass

    from PyQt5.QtCore import QTimer
    _ipc_timer = QTimer(planet)
    _ipc_timer.timeout.connect(_check_ipc_cmd)
    _ipc_timer.start(500)


def main() -> None:
    """CLI 入口，供 pyproject.toml [project.scripts] 调用。"""
    floating_only = "--floating-only" in sys.argv

    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 任务栏图标
    _logo_path = os.path.join(PROJECT_ROOT, "logo.jpg")
    if os.path.isfile(_logo_path):
        _src = QPixmap(_logo_path)
        if not _src.isNull():
            _sz = 128
            _src = _src.scaled(_sz, _sz, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            _rounded = QPixmap(_sz, _sz)
            _rounded.fill(Qt.transparent)
            _p = QPainter(_rounded)
            _p.setRenderHint(QPainter.Antialiasing)
            _path = QPainterPath()
            _r = int(_sz * 0.2237)
            _path.addRoundedRect(0, 0, _sz, _sz, _r, _r)
            _p.setClipPath(_path)
            _p.drawPixmap(0, 0, _src)
            _p.end()
            app.setWindowIcon(QIcon(_rounded))

    if floating_only:
        _run_floating_only(app)
    else:
        win = LoginWindow()
        win.show()

        # ── 云端同步（daemon 子线程，不阻塞 UI）──
        def _start_cloud_sync() -> None:
            """后台异步启动：先拉取云端数据，再推送本地数据到云端"""
            try:
                from core.data import init_all_dbs
                init_all_dbs()
            except Exception as e:
                logging.error(f"数据库初始化失败: {e}")
                return
            try:
                from core.cloud_pull import pull_all_from_cloud
                pull_all_from_cloud()
            except Exception as e:
                logging.error(f"云端拉取失败: {e}")
        threading.Thread(target=_start_cloud_sync, daemon=True, name="cloud_sync_startup").start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()