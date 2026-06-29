# `iqra/iqra_chat.py`

> 路径：`iqra/iqra_chat.py` | 行数：232


---


```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Iqra AI 对话窗口 — 独立版
加载 data/iqra_config.json，启动 IqraCoreEngine 进入对话
"""
import os
import sys
import json
import threading

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QSplitter, QFrame,
    QScrollBar,
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QTextCursor, QColor
from core.dark_theme import apply_dark_theme

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CONFIG_PATH = os.path.join(DATA_DIR, "iqra_config.json")

# Iqra 对话窗口特有样式（叠加在 BASE_DARK_STYLE 之上）
IQRA_CHAT_EXTRA_STYLE = """
QLabel#title { font-size: 18px; font-weight: bold; color: #cba6f7; padding: 8px; }
QTextEdit#chat_display {
    background: #1e1e2e; color: #cdd6f4; border: 1px solid #313244;
    border-radius: 8px; padding: 12px; font-size: 14px; line-height: 1.6;
}
QLineEdit#input {
    background: #313244; color: #cdd6f4; border: 1px solid #45475a;
    border-radius: 8px; padding: 12px; font-size: 14px;
}
QLineEdit#input:focus { border-color: #5850ec; }
QPushButton#send_btn {
    background: #5850ec; color: white; border: none;
    border-radius: 8px; padding: 12px 28px; font-size: 14px; font-weight: bold;
}
QPushButton#send_btn:hover { background: #6c63ff; }
QPushButton#send_btn:disabled { background: #45475a; }
QFrame#status_bar {
    background: #11111b; border-top: 1px solid #313244;
}
QLabel#status { color: #6c7086; font-size: 12px; padding: 4px 12px; }
"""


class ChatSignals(QObject):
    response_ready = pyqtSignal(str)
    thinking = pyqtSignal(bool)
    error = pyqtSignal(str)


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Iqra — AI 对话")
        self.setMinimumSize(800, 600)
        self.resize(900, 680)
        apply_dark_theme(self)
        self.setStyleSheet(self.styleSheet() + IQRA_CHAT_EXTRA_STYLE)

        self._engine = None
        self._signals = ChatSignals()
        self._signals.response_ready.connect(self._on_response)
        self._signals.thinking.connect(self._on_thinking)
        self._signals.error.connect(self._on_error)

        self._build_ui()
        self._init_engine()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(12, 8, 12, 8)

        # 标题
        title = QLabel("Iqra AI 引擎 — 对话中")
        title.setObjectName("title")
        layout.addWidget(title)

        # 主内容区
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(1)

        # 对话显示区
        self._display = QTextEdit()
        self._display.setObjectName("chat_display")
        self._display.setReadOnly(True)
        splitter.addWidget(self._display)

        # 输入区
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 8, 0, 0)
        input_layout.setSpacing(8)

        self._input = QLineEdit()
        self._input.setObjectName("input")
        self._input.setPlaceholderText("输入消息，按 Enter 发送...")
        self._input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self._input, 1)

        self._send_btn = QPushButton("发送")
        self._send_btn.setObjectName("send_btn")
        self._send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self._send_btn)

        splitter.addWidget(input_container)
        splitter.setSizes([540, 70])
        layout.addWidget(splitter, 1)

        # 状态栏
        status_bar = QFrame()
        status_bar.setObjectName("status_bar")
        status_bar.setFixedHeight(28)
        sl = QHBoxLayout(status_bar)
        sl.setContentsMargins(12, 0, 12, 0)
        self._status = QLabel("就绪")
        self._status.setObjectName("status")
        sl.addWidget(self._status)
        layout.addWidget(status_bar)

    def _init_engine(self):
        """初始化 Iqra 核心引擎"""
        self._add_system_msg("正在初始化 Iqra 引擎...")
        try:
            from core.core_engine import IqraCoreEngine

            # 尝试加载配置
            config = None
            if os.path.exists(CONFIG_PATH):
                try:
                    with open(CONFIG_PATH, "r") as f:
                        cfg = json.load(f)
                    active_id = cfg.get("active_provider_id", "")
                    ptype = cfg.get("active_provider_type", "local")
                    providers = cfg.get("cloud_providers" if ptype == "cloud" else "local_providers", {})
                    provider = providers.get(active_id, {})
                    if provider:
                        from core.llm_backend import ProviderConfig
                        config = ProviderConfig(
                            name=provider.get("name", active_id),
                            provider_type="openai_compatible",
                            base_url=provider.get("base_url", "http://localhost:11434/v1"),
                            model=provider.get("model", "qwen2.5:7b"),
                            api_key=provider.get("api_key", ""),
                            temperature=0.7,
                            max_tokens=262144,
                        )
                        self._add_system_msg(f"已加载配置: {config.name} / {config.model}")
                except Exception as e:
                    self._add_system_msg(f"配置加载失败，使用默认配置: {e}")

            self._engine = IqraCoreEngine(provider_config=config)
            self._add_system_msg("Iqra 引擎就绪，可以开始对话")

        except Exception as e:
            self._add_system_msg(f"引擎初始化失败: {e}")
            self._status.setText("初始化失败")
            self._send_btn.setEnabled(False)
            self._input.setEnabled(False)

    def _add_system_msg(self, text):
        self._display.append(f'<span style="color:#6c7086;font-style:italic;">[系统] {text}</span>')

    def _add_user_msg(self, text):
        self._display.append(f'<p style="color:#f5c2e7;margin:8px 0 4px;"><b>你</b></p>'
                             f'<p style="color:#cdd6f4;margin:0 0 12px;">{text}</p>')

    def _add_assistant_msg(self, text):
        self._display.append(f'<p style="color:#cba6f7;margin:8px 0 4px;"><b>Iqra</b></p>'
                             f'<p style="color:#cdd6f4;margin:0 0 12px;white-space:pre-wrap;">{text}</p>')

    def _send_message(self):
        text = self._input.text().strip()
        if not text or self._engine is None:
            return

        self._input.clear()
        self._input.setEnabled(False)
        self._send_btn.setEnabled(False)

        self._add_user_msg(text)

        if text.lower() in ("退出", "exit", "quit", "再见"):
            self._add_assistant_msg("再见！欢迎随时回来。")
            self._input.setEnabled(True)
            self._send_btn.setEnabled(True)
            return

        self._status.setText("Iqra 思考中...")
        threading.Thread(target=self._run_chat, args=(text,), daemon=True).start()

    def _run_chat(self, user_input):
        try:
            self._signals.thinking.emit(True)
            response = self._engine.chat(user_input)
            self._signals.response_ready.emit(response)
        except Exception as e:
            self._signals.error.emit(str(e))

    def _on_response(self, text):
        self._add_assistant_msg(text)
        self._input.setEnabled(True)
        self._send_btn.setEnabled(True)
        self._input.setFocus()
        self._status.setText("就绪")

    def _on_thinking(self, is_thinking):
        if is_thinking:
            self._status.setText("Iqra 思考中...")

    def _on_error(self, msg):
        self._add_system_msg(f"错误: {msg}")
        self._input.setEnabled(True)
        self._send_btn.setEnabled(True)
        self._input.setFocus()
        self._status.setText(f"错误: {msg}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    app.exec_()

```
