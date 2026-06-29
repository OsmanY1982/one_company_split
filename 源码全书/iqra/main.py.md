# `iqra/main.py`

> 路径：`iqra/main.py` | 行数：232


---


```python
"""
一人公司 · 智能助手子项目
启动入口（子项目：登录→模型设置→智能中心）

用法:
    python main.py                # 正常模式：登录→模型配置→智能中心
    python main.py --floating-only # 极简浮球模式：跳过登录，直接显示悬浮球
"""
import sys
import os
import json
import signal
import atexit
import traceback
import threading
import logging
import platform
import tempfile

# 忽略终端关闭 SIGHUP，防止终端退出时悬浮球被杀死
if platform.system() != "Windows":
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
from datetime import datetime

# ── 路径 ── 使用项目本地 core/services/tools，不依赖共享目录
_PROJECT_ROOT = os.path.dirname(__file__)
_PARENT_ROOT = os.path.dirname(_PROJECT_ROOT)  # 一人公司父项目根目录
sys.path.insert(0, _PARENT_ROOT)  # 让 iqra 可访问父项目的 core.modules (business/personnel 等共用模块)
sys.path.insert(0, _PROJECT_ROOT)  # iqra/ 优先于 one_company_split/，确保本项目的 modules 不被顶层 modules 子集遮盖

# ── 按需安装核心依赖（首次运行自动触发）──
# ensure_core_deps() skipped on Windows (deps pre-installed)

# ── Obscura 浏览器后端 ──
_OBSCURA_SERVER = None

def _start_obscura():
    """启动 Obscura serve 作为 iqra 的浏览器后端。"""
    global _OBSCURA_SERVER
    try:
        from core.obscura_provider import ObscuraServer, is_obscura_available
        if not is_obscura_available():
            return
        _OBSCURA_SERVER = ObscuraServer(port=9222, stealth=True, workers=2, quiet=True)
        if _OBSCURA_SERVER.start():
            atexit.register(_OBSCURA_SERVER.stop)
    except Exception:
        pass

# ── 全局异常捕获 ──
LOG_DIR = os.path.join(os.path.dirname(__file__), "log")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "crash.log"),
    level=logging.ERROR,
    format="%(asctime)s [%(threadName)s] %(message)s",
    encoding="utf-8"
)

def _global_excepthook(exc_type, exc_value, exc_tb):
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logging.error(f"未捕获异常:\n{tb_str}")
    from PyQt5.QtWidgets import QApplication, QMessageBox
    app = QApplication.instance()
    if app:
        QMessageBox.critical(None, "系统错误",
            f"发生未处理的异常:\n\n{exc_value}\n\n详细日志已写入 log/crash.log")
    sys.__excepthook__(exc_type, exc_value, exc_tb)

def _thread_excepthook(args):
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
CONFIG_PATH = os.path.join(_PROJECT_ROOT, "data", "iqra_config.json")


def _init_engine():
    """初始化 iqra 引擎（供 floating-only 模式使用）。"""
    if not os.path.exists(CONFIG_PATH):
        return None, {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        return None, {}

    try:
        from core.llm_backend import BackendFactory, ProviderConfig
        if _PROJECT_ROOT not in sys.path:
            sys.path.insert(0, _PROJECT_ROOT)
        elif sys.path[0] != _PROJECT_ROOT:
            sys.path.remove(_PROJECT_ROOT)
            sys.path.insert(0, _PROJECT_ROOT)

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


def _run_floating_only(app: QApplication):
    """极简浮球模式：只显示悬浮球，无登录窗口/智能中心。"""
    engine, config = _init_engine()
    from modules.intelligence.iqra_floating_planet import FloatingPlanet

    planet = FloatingPlanet(
        iqra_engine=engine,
        role="admin",
        membership_info={},
        config=config,
        project_context="iqra",
    )
    planet.show()

    # 写入 PID 锁文件
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    atexit.register(lambda: os.path.exists(LOCK_FILE) and os.remove(LOCK_FILE))

    # ── IPC 命令监听 ──
    def _check_ipc_cmd():
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


if __name__ == "__main__":
    floating_only = "--floating-only" in sys.argv

    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 启动 Obscura 浏览器后端（后台异步，不阻塞启动）
    threading.Thread(target=_start_obscura, daemon=True, name="obscura-startup").start()

    # 任务栏图标
    _logo_path = os.path.join(_PROJECT_ROOT, "logo.jpg")
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
        def _start_cloud_sync():
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
```
