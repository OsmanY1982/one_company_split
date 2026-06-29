# -*- coding: utf-8 -*-
"""悬浮球 AI 对话 Mixin — 引擎恢复 + 打开对话窗口"""
import sys, os, traceback
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt


class FloatingPlanetChatMixin:
    """AI 对话：引擎检测/恢复、对话窗口打开"""

    def _ensure_engine(self):
        """检测 iqra 引擎：若为 None 则尝试从配置恢复；仍失败则提示进入模型设置。"""
        if self._engine is not None:
            return

        # 确保从 iqra 子项目导入模型设置（唯一入口）
        _IQRA_PROJECT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "iqra")
        _IQRA_PARENT = os.path.dirname(_IQRA_PROJECT)
        if _IQRA_PARENT not in sys.path:
            sys.path.insert(0, _IQRA_PARENT)
        if _IQRA_PROJECT not in sys.path:
            sys.path.insert(0, _IQRA_PROJECT)

        # 强制刷新：pop 已缓存的旧版模块，确保 iqra 修改后能生效
        _stale_keys = [k for k in sys.modules if k.startswith("modules.auth.model_setup_window")
                       or k.startswith("modules.intelligence.agent_bridge")
                       or k.startswith("modules.intelligence.agent_bridge_workers")]
        for k in _stale_keys:
            del sys.modules[k]

        # 尝试从已有配置恢复引擎
        try:
            import importlib.machinery
            _iqra_ms_win = importlib.machinery.SourceFileLoader(
                "modules.auth.model_setup_window",
                os.path.join(_IQRA_PROJECT, "modules", "auth", "model_setup_window.py")
            ).load_module()
            sys.modules["modules.auth.model_setup_window"] = _iqra_ms_win
            _load_iqra_config = _iqra_ms_win._load_iqra_config
            init_iqra_engine_from_config = _iqra_ms_win.init_iqra_engine_from_config
            config = _load_iqra_config()
            if config and config.get("active_provider_id"):
                engine = init_iqra_engine_from_config(config)
                if engine is not None:
                    self._engine = engine
                    return
        except Exception as e:
            pass

        # 引擎恢复失败 → 询问用户是否进入模型设置
        reply = QMessageBox.question(
            self, "AI 引擎未连接",
            "AI 引擎尚未配置或当前不可用（如 Ollama 未启动）。\n\n"
            "是否现在进入模型设置进行配置？\n"
            "选择「否」将以离线分析模式打开 AI 对话。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            try:
                from core.modules.auth.model_setup_window import ModelSetupWindow
                dlg = ModelSetupWindow(
                    username=self._membership_info.get("username", ""),
                    role=self._role,
                    membership_info=self._membership_info,
                )
                dlg.setup_complete.connect(self._on_engine_setup_done)
                self._open_windows["model_settings"] = dlg
                dlg.destroyed.connect(lambda: self._open_windows.pop("model_settings", None))
                dlg.show()
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法打开模型设置：{e}")

    def _on_engine_setup_done(self, data: dict):
        """模型设置完成后更新引擎引用并重新打开 AI 对话"""
        engine = data.get("engine")
        if engine is not None:
            self._engine = engine
            self._open_chat()

    def _open_chat(self):
        self.wake()
        self._ensure_engine()
        try:
            from core.modules.intelligence.ai_chat_window import AIChatWindow
            from core.modules.intelligence.session_context import session_ctx
            session_ctx.set_agent_bridge(self._engine)
            if self._standalone_chat is not None:
                try:
                    self._standalone_chat.close()
                except RuntimeError:
                    pass
                self._standalone_chat = None
            self._standalone_chat = AIChatWindow(
                iqra_engine=self._engine,
                embedded=False,
                session_id=session_ctx.current_session_id,
            )
            self._standalone_chat.setAttribute(Qt.WA_DeleteOnClose)
            self._standalone_chat.show()
        except Exception as e:
            print(f"[FloatingPlanet] Failed to open chat: {e}")
            traceback.print_exc()
