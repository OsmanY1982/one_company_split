# `planetarium/core/modules/intelligence/_chat_dialog/_dialog.py`

> 路径：`planetarium/core/modules/intelligence/_chat_dialog/_dialog.py` | 行数：356


---


```python
# -*- coding: utf-8 -*-
"""
AI 助手模块 v3 — 支持本地模型管理
IqraChatDialog 核心对话类。
"""

import sys
import os
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QMessageBox,
    QGroupBox, QComboBox,
    QTextEdit, QScrollArea,
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from core.modules.intelligence._stubs import app_state


class IqraChatDialog(QDialog):
    _STAGE_LABELS = {
        "THINK": "分析中...",
        "PLAN": "规划步骤...",
        "ACT": "执行操作...",
        "OBSERVE": "观察结果...",
        "REFLECT": "反思调整...",
        "COMPLETE": "任务完成",
    }

    def __init__(self, parent=None, iqra_engine=None, floating_mode=False, voice=None):
        super().__init__(parent)
        self._iqra = iqra_engine
        self._all_models = []
        self._current_model = ""
        if self._iqra and hasattr(self._iqra, "get_model"):
            self._current_model = self._iqra.get_model()

        self._floating_mode = floating_mode
        self._voice = voice

        self._messages = []
        self._session_id = None

        if floating_mode:
            self.setWindowTitle("iqra · AI 对话")
            self.setWindowFlags(
                Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowStaysOnTopHint
            )
            self.resize(420, 620)
        else:
            self.setWindowTitle("AI 对话")
            self.setMinimumSize(480, 580)

        self._build_ui()

        if not floating_mode:
            QTimer.singleShot(300, self._refresh_model_list)

    # ═══════ UI ═══════
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        # 模型选择行
        model_row = QHBoxLayout()
        model_row.setSpacing(8)
        status_lbl = QLabel("模型:")
        status_lbl.setStyleSheet("color:#718096;font-size:12px;")
        model_row.addWidget(status_lbl)

        self._cb_model = QComboBox()
        self._cb_model.setMinimumHeight(30)
        self._cb_model.setStyleSheet("""
            QComboBox { border:1px solid #e2e8f0; border-radius:6px; padding:4px 8px; font-size:12px; background:white; }
            QComboBox:focus { border-color:#2b6cb0; }
            QComboBox::drop-down { border:none; }
        """)
        self._cb_model.currentIndexChanged.connect(self._on_model_changed)
        model_row.addWidget(self._cb_model, stretch=1)

        refresh_btn = QPushButton("⟳")
        refresh_btn.setFixedSize(28, 28)
        refresh_btn.setToolTip("刷新模型列表")
        refresh_btn.setStyleSheet("""
            QPushButton { background:#f7fafc; color:#4a5568; border:1px solid #e2e8f0; border-radius:6px; font-size:14px; }
            QPushButton:hover { background:#edf2f7; }
        """)
        refresh_btn.clicked.connect(self._refresh_model_list)
        model_row.addWidget(refresh_btn)
        layout.addLayout(model_row)

        # 对话历史
        self._chat_log = QTextEdit()
        self._chat_log.setReadOnly(True)
        self._chat_log.setStyleSheet("""
            QTextEdit { border:1px solid #e2e8f0; border-radius:8px; padding:8px; font-size:13px; background:#f7fafc; }
        """)
        layout.addWidget(self._chat_log, stretch=1)

        # 输入行
        input_row = QHBoxLayout()
        input_row.setSpacing(6)

        if self._floating_mode:
            self._input = QTextEdit()
            self._input.setPlaceholderText("输入问题... (Ctrl+Enter 发送)")
            self._input.setMaximumHeight(100)
            self._input.setMinimumHeight(36)
            self._input.setStyleSheet("""
                QTextEdit { border:1px solid #e2e8f0; border-radius:8px; padding:6px; font-size:13px; background:white; }
                QTextEdit:focus { border-color:#2b6cb0; }
            """)
            self._input.installEventFilter(self)
        else:
            self._input = QLineEdit()
            self._input.setPlaceholderText("输入问题... (Enter 发送)")
            self._input.setMinimumHeight(36)
            self._input.setStyleSheet("""
                QLineEdit { border:1px solid #e2e8f0; border-radius:8px; padding:6px 10px; font-size:13px; background:white; }
                QLineEdit:focus { border-color:#2b6cb0; }
            """)
            self._input.returnPressed.connect(self._send)

        input_row.addWidget(self._input, stretch=1)

        send_btn = QPushButton("发送")
        send_btn.setMinimumHeight(36)
        send_btn.setMinimumWidth(64)
        send_btn.setStyleSheet("""
            QPushButton { background:#2b6cb0; color:white; border:none; border-radius:8px; font-size:13px; font-weight:600; }
            QPushButton:hover { background:#2c5282; }
            QPushButton:pressed { padding-top:2px; }
            QPushButton:disabled { background:#cbd5e0; }
        """)
        send_btn.clicked.connect(self._send)
        self._send_btn = send_btn
        input_row.addWidget(send_btn)

        if self._voice:
            voice_btn = QPushButton("🎤")
            voice_btn.setFixedSize(36, 36)
            voice_btn.setToolTip("语音输入")
            voice_btn.setStyleSheet("""
                QPushButton { background:#f7fafc; border:1px solid #e2e8f0; border-radius:8px; font-size:16px; }
                QPushButton:hover { background:#edf2f7; }
            """)
            voice_btn.clicked.connect(self._toggle_voice_input)
            input_row.addWidget(voice_btn)

        layout.addLayout(input_row)

    # ═══════ 模型刷新 ═══════
    def _refresh_model_list(self):
        self._cb_model.blockSignals(True)
        self._cb_model.clear()
        self._all_models = []

        if self._iqra and hasattr(self._iqra, "list_models"):
            try:
                cloud_models = self._iqra.list_models(source="cloud")
                local_models = self._iqra.list_models(source="local")
            except Exception:
                cloud_models = []
                local_models = []

            for m in cloud_models:
                name = m.get("name", m) if isinstance(m, dict) else m
                self._cb_model.addItem(f"☁️ {name}")
                self._all_models.append(("cloud", name))
                if name == self._current_model:
                    self._cb_model.setCurrentIndex(self._cb_model.count() - 1)
            if cloud_models and local_models:
                self._cb_model.insertSeparator(self._cb_model.count())
            for m in local_models:
                name = m.get("name", m) if isinstance(m, dict) else m
                self._cb_model.addItem(f"💻 {name}")
                self._all_models.append(("local", name))
                if name == self._current_model:
                    self._cb_model.setCurrentIndex(self._cb_model.count() - 1)

        if self._cb_model.count() == 0:
            self._cb_model.addItem("（无可用模型）")

        self._cb_model.blockSignals(False)

    def _on_model_changed(self, idx):
        if idx < 0 or idx >= len(self._all_models):
            return
        source, name = self._all_models[idx]
        if self._iqra and hasattr(self._iqra, "switch_model"):
            self._iqra.switch_model(name, source=source)
            self._current_model = name

    def _on_external_model_change(self, model_name: str):
        self._current_model = model_name
        self._cb_model.blockSignals(True)
        for i, (_, name) in enumerate(self._all_models):
            if name == model_name:
                self._cb_model.setCurrentIndex(i)
                break
        self._cb_model.blockSignals(False)

    # ═══════ 发送 ═══════
    def _send(self):
        if isinstance(self._input, QTextEdit):
            text = self._input.toPlainText().strip()
            self._input.clear()
        else:
            text = self._input.text().strip()
            self._input.clear()

        if not text:
            return
        if not self._current_model:
            QMessageBox.warning(self, "提示", "请先选择一个模型")
            return

        self._messages.append({"role": "user", "content": text})
        self._append_to_log(f"**你:** {text}\n\n")
        self._send_btn.setEnabled(False)

        if self._iqra and hasattr(self._iqra, "chat"):
            try:
                if hasattr(self._iqra, "chat_stream"):
                    self._iqra.chat_stream(
                        text,
                        on_chunk=self._on_stream_chunk,
                        on_done=self._on_stream_done,
                        on_tool=self._on_stream_tool,
                    )
                else:
                    result = self._iqra.chat(text)
                    self._messages.append({"role": "assistant", "content": str(result)})
                    self._append_to_log(f"**iqra:** {result}\n\n")
                    self._send_btn.setEnabled(True)
            except Exception as e:
                self._append_to_log(f"*错误: {e}*\n\n")
                self._send_btn.setEnabled(True)

    # ═══════ 流式回调 ═══════
    def _on_stream_chunk(self, text: str):
        cursor = self._chat_log.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)
        self._chat_log.setTextCursor(cursor)

    def _on_stream_done(self, full_text: str):
        self._messages.append({"role": "assistant", "content": full_text})
        self._append_to_log("\n\n")
        self._send_btn.setEnabled(True)

    def _on_stream_tool(self, tool_info: dict):
        name = tool_info.get("name", "tool")
        self._append_to_log(f"\n> 🔧 调用工具: `{name}`\n")

    # ═══════ 事件 ═══════
    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if obj == self._input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                self._send()
                return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        if self._session_id:
            try:
                session_dir = self._get_session_dir()
                filepath = os.path.join(session_dir, f"{self._session_id}.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self._messages, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
        super().closeEvent(event)

    # ═══════ 会话 ═══════
    def _get_session_dir(self):
        base = os.path.join(os.path.expanduser("~"), ".opc", "iqra_sessions")
        os.makedirs(base, exist_ok=True)
        return base

    def _load_history(self, session_id: str):
        self._session_id = session_id
        filepath = os.path.join(self._get_session_dir(), f"{session_id}.json")
        if os.path.exists(filepath):
            try:
                self._messages = json.load(open(filepath, encoding='utf-8'))
                self._chat_log.clear()
                for msg in self._messages:
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    if role == "user":
                        self._append_to_log(f"**你:** {content}\n\n")
                    elif role == "assistant":
                        self._append_to_log(f"**iqra:** {content}\n\n")
            except Exception:
                self._messages = []

    def get_messages(self):
        return list(self._messages)

    def clear_chat(self):
        self._messages.clear()
        self._chat_log.clear()

    # ═══════ Agent 信号 ═══════
    def _connect_agent_signals(self, agent):
        pass

    def _on_agent_tool_start(self, tool_name: str, args: dict):
        self._append_to_log(f"\n> 🔧 开始执行: `{tool_name}`\n")

    def _on_agent_tool_result(self, tool_name: str, result):
        preview = str(result)[:200]
        self._append_to_log(f"> ✅ `{tool_name}` 完成: {preview}\n")

    def _on_agent_stage(self, stage: str):
        label = self._STAGE_LABELS.get(stage, stage)
        self._append_to_log(f"> *{label}*\n")

    # ═══════ 语音 ═══════
    def _toggle_voice_input(self):
        if not self._voice:
            return
        try:
            text = self._voice.listen()
            if isinstance(self._input, QTextEdit):
                self._input.setText(text)
            else:
                self._input.setText(text)
        except Exception as e:
            QMessageBox.warning(self, "语音错误", str(e))

    def _on_voice_result(self, text: str):
        if isinstance(self._input, QTextEdit):
            self._input.setPlainText(text)
        else:
            self._input.setText(text)

    # ═══════ 内部 ═══════
    def _append_to_log(self, text: str):
        self._chat_log.moveCursor(self._chat_log.textCursor().End)
        self._chat_log.insertHtml(text.replace("\n", "<br>").replace("**你:**", "<b>你:</b>").replace("**iqra:**", "<b>iqra:</b>"))
        scrollbar = self._chat_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

```
