# `core/modules/intelligence/_chat_dialog/_dialog.py`

> 路径：`core/modules/intelligence/_chat_dialog/_dialog.py` | 行数：687


---


```python
# -*- coding: utf-8 -*-
"""
AI 助手模块 v3 — 支持本地模型管理
- 标签1: 💬 AI 对话 (iqra ChatWindow)
- 标签2: ⚡ 快捷工具 (模板、本地模型、系统状态)
- 标签3~6: 增强功能（智能对话、快捷操作、系统监控、高级功能）

改进:
- 添加 Ollama 本地模型管理（检测、启动、下载、切换）
- 添加多尺寸模型（超小/中等/大模型）
- 增强本地模型使用体验
- 优化界面布局
- 优化导入路径管理，提升模块加载稳定性
"""

import sys
import os
import subprocess
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

# ── 路径管理 ──────────────────────────────────────────────────────────────────
# 确保项目根目录（one_company_desktop）在 sys.path 中，
# 使「from core.modules.intelligence.xxx import ...」
# 在所有调用场景下均可正常工作。
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
# ─────────────────────────────────────────────────────────────────────────────

from PyQt5.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QGridLayout, QMessageBox,
    QGroupBox, QComboBox, QDialog, QFormLayout, QCheckBox,
    QProgressBar, QTextEdit, QPlainTextEdit, QApplication,
    QScrollArea, QFrame, QSizePolicy,
)
from PyQt5.QtCore import Qt, QObject, QTimer, QThread, pyqtSignal, QUrl, QPropertyAnimation, QEasingCurve, pyqtProperty, QRect, QParallelAnimationGroup
from PyQt5.QtGui import QFont, QPalette

from core.modules.intelligence._stubs import app_state


# ═══════════════════════════════════════════
# Iqra 对话弹窗
# ═══════════════════════════════════════════

class IqraChatDialog(QDialog):
    """Iqra 核心对话引擎弹窗 — 含模型切换 UI，与 AgentBridge 同步"""

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

        # ── 对话历史管理 ──
        self._messages = []       # [{role, content}, ...] 当前会话消息
        self._session_id = None   # 由外部 AIChatWindow 设置

        if floating_mode:
            self.setWindowTitle("iqra · AI 对话")
            self.setWindowFlags(
                Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowStaysOnTopHint
            )
            self.setMinimumSize(420, 480)
        else:
            self.setWindowTitle("Iqra 对话 · 核心引擎")
            self.setMinimumSize(800, 600)
            self.resize(900, 700)
        self._build_ui()
        self._refresh_model_list()

        # 监听全局模型变更（AIChatWindow / FloatingPlanet 切换后自动同步）
        if self._iqra and hasattr(self._iqra, "model_changed"):
            mc = self._iqra.model_changed
            if mc:
                mc.connect(self._on_external_model_change)

        # 悬浮球模式：加载对话历史 + 连接 Agent tool 信号
        if floating_mode:
            self._load_history()
            self._connect_agent_signals()

    def _build_ui(self):
        from datetime import datetime

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # ── 模型切换行 ──
        model_row = QHBoxLayout()
        model_row.setSpacing(6)

        if self._iqra is not None:
            prov = self._iqra.get_provider_info() if hasattr(self._iqra, "get_provider_info") else {}
            status_text = f"引擎: {prov.get('name', 'Iqra')} / {prov.get('model', self._current_model)}"
            status_color = "#44cc88"
        else:
            status_text = "引擎未连接"
            status_color = "#ff6644"

        self._lbl_status = QLabel(status_text)
        self._lbl_status.setStyleSheet(
            f"color: {status_color}; font-size: 10px; background: transparent;"
        )
        model_row.addWidget(self._lbl_status)
        model_row.addStretch()

        model_lbl = QLabel("模型:")
        model_lbl.setStyleSheet("color: #8877aa; font-size: 10px; background: transparent;")
        model_row.addWidget(model_lbl)

        self._cb_model = QComboBox()
        self._cb_model.setMinimumWidth(180)
        self._cb_model.setStyleSheet("""
            QComboBox {
                background: rgba(20,12,40,200); color: #ddccff;
                border: 1px solid rgba(150,60,220,30); border-radius: 6px;
                padding: 2px 6px; font-size: 10px;
            }
            QComboBox:hover { border: 1px solid rgba(170,80,255,100); }
            QComboBox::drop-down { border: none; width: 18px; }
            QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #8877bb; margin-right: 4px; }
            QComboBox QAbstractItemView {
                background: rgba(15,8,30,240); color: #ccbbdd;
                border: 1px solid rgba(170,80,255,40); selection-background-color: rgba(150,60,220,50);
            }
        """)
        self._cb_model.currentIndexChanged.connect(self._on_model_changed)
        model_row.addWidget(self._cb_model)

        refresh_btn = QPushButton("⟳")
        refresh_btn.setToolTip("刷新模型列表")
        refresh_btn.setFixedSize(24, 22)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: rgba(100,140,200,30); color: #99bbee; border: none;
                border-radius: 11px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(120,160,220,50); }
        """)
        refresh_btn.clicked.connect(self._refresh_model_list)
        model_row.addWidget(refresh_btn)

        layout.addLayout(model_row)

        # 消息历史
        self._chat_log = QTextEdit()
        self._chat_log.setReadOnly(True)
        self._chat_log.setStyleSheet("""
            QTextEdit {
                background: rgba(8,4,16,230); color: #bb99dd;
                border: 1px solid rgba(170,80,255,35); border-radius: 10px;
                padding: 12px; font-size: 13px; line-height: 1.6;
            }
        """)
        layout.addWidget(self._chat_log, 1)


        # 输入行
        ir = QHBoxLayout()

        if self._floating_mode:
            self._chat_input = QTextEdit()
            self._chat_input.setPlaceholderText("输入问题，Ctrl+Enter 发送...")
            self._chat_input.setMaximumHeight(80)
            self._chat_input.setStyleSheet("""
                QTextEdit {
                    background: rgba(10, 10, 30, 230);
                    color: #e0e0ff;
                    border: 1px solid rgba(80, 140, 255, 40);
                    border-radius: 8px;
                    padding: 6px;
                    font-size: 12px;
                }
            """)
            self._chat_input.installEventFilter(self)
            ir.addWidget(self._chat_input, 1)

            # 语音按钮
            if self._voice:
                self._mic_btn = QPushButton("🎤")
                self._mic_btn.setToolTip("语音输入")
                self._mic_btn.setFixedSize(36, 36)
                self._mic_btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(255, 100, 80, 160);
                        color: white;
                        border: none;
                        border-radius: 18px;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background: rgba(255, 130, 100, 200);
                    }
                """)
                self._mic_btn.clicked.connect(self._toggle_voice_input)
                ir.addWidget(self._mic_btn)
        else:
            self._chat_input = QLineEdit()
            self._chat_input.setPlaceholderText("输入问题，如：分析本月销售趋势...")
            self._chat_input.setStyleSheet("""
                QLineEdit {
                    background: rgba(20,10,40,200); color: #ddaaff;
                    border: 1px solid rgba(170,80,255,40); border-radius: 18px;
                    padding: 10px 18px; font-size: 13px;
                }
                QLineEdit:focus { border: 1px solid rgba(170,80,255,120); }
            """)
            self._chat_input.returnPressed.connect(self._send)
            ir.addWidget(self._chat_input, 1)

        send_btn = QPushButton("发送")
        send_btn.setCursor(Qt.PointingHandCursor)
        if self._floating_mode:
            send_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(60, 120, 255, 180);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: rgba(80, 150, 255, 220);
                }
            """)
        else:
            send_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(100,60,200,180); color: #fff;
                    border: none; border-radius: 18px;
                    padding: 10px 22px; font-size: 13px; font-weight: 600;
                }
                QPushButton:hover { background: rgba(120,80,220,220); }
            """)
        send_btn.clicked.connect(self._send)
        ir.addWidget(send_btn)

        if not self._floating_mode:
            clear_btn = QPushButton("清屏")
            clear_btn.setCursor(Qt.PointingHandCursor)
            clear_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(180,50,50,120); color: #ffaaaa;
                    border: none; border-radius: 18px;
                    padding: 10px 16px; font-size: 13px;
                }
                QPushButton:hover { background: rgba(200,60,60,160); }
            """)
            clear_btn.clicked.connect(lambda: self._chat_log.clear())
            ir.addWidget(clear_btn)
        layout.addLayout(ir)

        if self._iqra:
            self._chat_log.append(
                '<p style="color:#44cc66;">[系统] Iqra 引擎已就绪，可以开始对话。</p>'
            )
        else:
            self._chat_log.append(
                '<p style="color:#ffaa44;">[系统] Iqra 引擎未连接，请先完成模型配置。</p>'
            )

    # ─── 模型管理（通过 AgentBridge 统一管理，与 AIChatWindow 同步）───

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes >= 1024 ** 3:
            return f"{size_bytes / (1024**3):.1f} GB"
        if size_bytes >= 1024 ** 2:
            return f"{size_bytes / (1024**2):.0f} MB"
        return f"{size_bytes / 1024:.0f} KB"

    def _refresh_model_list(self):
        self._cb_model.blockSignals(True)
        self._cb_model.clear()
        self._all_models = []

        if self._iqra and hasattr(self._iqra, "list_all_models"):
            try:
                all_models = self._iqra.list_all_models()
            except Exception:
                all_models = []
        else:
            # 兜底：直接调 AgentBridge 静态方法
            try:
                from core.modules.intelligence.agent_bridge import AgentBridge
                all_models = AgentBridge.list_all_models()
            except Exception:
                all_models = []

        cloud_models = [m for m in all_models if m.get("category") == "cloud"]
        local_models = [m for m in all_models if m.get("category") == "local"]

        if cloud_models:
            self._cb_model.addItem("── 云端模型 ──")
            self._all_models.append(None)
            for m in cloud_models:
                display = f"  {m['provider_name']} · {m['model']}"
                self._cb_model.addItem(display, m)
                self._all_models.append(m)

        if local_models:
            self._cb_model.addItem("── 本地模型 ──")
            self._all_models.append(None)
            for m in local_models:
                size_info = f" ({self._format_size(m['size'])})" if m.get("size") else ""
                self._cb_model.addItem(f"  {m['model']}{size_info}", m)
                self._all_models.append(m)

        if not cloud_models and not local_models:
            self._cb_model.addItem("（暂无已配置模型）")

        # 选中当前模型
        if self._current_model:
            for i in range(self._cb_model.count()):
                data = self._cb_model.itemData(i)
                if data and isinstance(data, dict) and data.get("model") == self._current_model:
                    self._cb_model.setCurrentIndex(i)
                    break

        self._cb_model.blockSignals(False)

    def _on_model_changed(self, idx: int):
        data = self._cb_model.itemData(idx)
        if not data or not isinstance(data, dict):
            return

        provider_id = data.get("provider_id", "")
        model = data.get("model", "")
        if not model or model == self._current_model:
            return

        self._current_model = model

        if self._iqra and hasattr(self._iqra, "switch_model"):
            try:
                self._iqra.switch_model(provider_id, model)
                prov_name = data.get("provider_name", provider_id)
                self._chat_log.append(
                    f'<p style="color:#44cc88;font-size:10px;">[系统] 已切换到: {prov_name} / {model}</p>'
                )
                prov = self._iqra.get_provider_info() if hasattr(self._iqra, "get_provider_info") else {}
                self._lbl_status.setText(
                    f"引擎: {prov.get('name', prov_name)} / {model}"
                )
            except Exception as e:
                self._chat_log.append(
                    f'<p style="color:#ffaa44;font-size:10px;">[系统] 切换失败: {e}</p>'
                )

    def _on_external_model_change(self, provider_name: str, model: str):
        """其他窗口切换模型后自动同步 UI — 触发即更新下拉框选中项（不再次调用 switch_model）"""
        self._current_model = model
        self._cb_model.blockSignals(True)
        for i in range(self._cb_model.count()):
            data = self._cb_model.itemData(i)
            if data and isinstance(data, dict) and data.get("model") == model:
                self._cb_model.setCurrentIndex(i)
                break
        self._cb_model.blockSignals(False)
        self._lbl_status.setText(f"引擎: {provider_name} / {model}")

    def _send(self):
        from datetime import datetime

        if self._floating_mode:
            text = self._chat_input.toPlainText().strip()
        else:
            text = self._chat_input.text().strip()
        if not text:
            return
        self._chat_input.clear()
        # 消息追踪 + 实时增量保存
        self._messages.append({"role": "user", "content": text})
        if self._session_id and hasattr(self._iqra, "append_message"):
            try:
                self._iqra.append_message("user", text, self._session_id)
            except Exception:
                pass
        now = datetime.now().strftime("%H:%M:%S")
        self._chat_log.append(
            f'<p style="color:#ffaa44;font-weight:700;">[{now}] 你:</p>'
            f'<p style="color:#ddccff;">{text}</p>'
        )
        self._chat_input.setEnabled(False)

        if not self._iqra:
            self._chat_log.append(
                f'<p style="color:#ff6666;font-weight:700;">[{now}] 系统:</p>'
                f'<p style="color:#ffaaaa;">Iqra 引擎未连接，请先完成模型配置后重试。</p>'
            )
            self._chat_input.setEnabled(True)
            self._chat_input.setFocus()
            return

        # 流式输出（打字机效果）
        if hasattr(self._iqra, 'chat_stream'):
            self._stream_accumulated = ""
            self._stream_header = f'<p style="color:#44ccff;font-weight:700;">[{now}] AI:</p>'
            self._stream_chunks_received = False

            # 先插入流式占位块，防止 on_chunk 第一帧误删用户消息
            self._chat_log.append(
                f'{self._stream_header}'
                f'<p style="color:#ccaaff;">'
                f'<span style="color:#88ff88;">_</span></p>'
            )

            try:
                self._iqra.chat_stream(
                    text,
                    self._on_stream_chunk,
                    self._on_stream_done,
                    self._on_stream_tool,
                )
                return
            except Exception:
                import traceback; traceback.print_exc()
                # 流式失败，回退同步

        # 同步模式（回退 / 非流式引擎）
        try:
            reply = self._iqra.chat(text)
        except Exception as e:
            reply = f"Iqra 异常: {e}"

        self._chat_log.append(
            f'<p style="color:#44ccff;font-weight:700;">[{now}] AI:</p>'
            f'<p style="color:#ccaaff;">{reply}</p>'
        )
        self._chat_input.setEnabled(True)
        self._chat_input.setFocus()
        # 实时保存 AI 回复
        self._messages.append({"role": "assistant", "content": reply})
        if self._session_id and hasattr(self._iqra, "append_message"):
            try:
                self._iqra.append_message("assistant", reply, self._session_id)
            except Exception:
                pass
        sb = self._chat_log.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ═══ 流式回调（实例方法 — 确保 QueuedConnection 派发到主线程） ═══

    def _on_stream_chunk(self, chunk: str):
        self._stream_accumulated += chunk
        self._stream_chunks_received = True
        # 移除最后一个块（占位块或上一次流式块）
        cursor = self._chat_log.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.BlockUnderCursor)
        cursor.removeSelectedText()
        display = self._stream_accumulated[-600:].replace('\n', '<br>')
        self._chat_log.append(
            f'{self._stream_header}'
            f'<p style="color:#ccaaff;">{display}'
            f'<span style="color:#88ff88;">_</span></p>'
        )
        sb = self._chat_log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_stream_done(self, full_text: str):
        # 移除最后一个块（流式占位或最后一块内容）
        cursor = self._chat_log.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.BlockUnderCursor)
        cursor.removeSelectedText()
        final = full_text.replace('\n', '<br>') if full_text else ''
        if not final and not self._stream_chunks_received:
            # 流式完全没返回内容：显示错误提示
            self._chat_log.append(
                f'{self._stream_header}'
                f'<p style="color:#ff8888;">[响应为空，请重试]</p>'
            )
        else:
            self._chat_log.append(
                f'{self._stream_header}'
                f'<p style="color:#ccaaff;">{final}</p>'
            )
        self._chat_input.setEnabled(True)
        self._chat_input.setFocus()
        # 悬浮球模式：短回复自动 TTS 播报
        if self._floating_mode and self._voice and full_text and len(full_text) < 300:
            try:
                self._voice.speak(full_text)
            except Exception:
                pass
        sb = self._chat_log.verticalScrollBar()
        sb.setValue(sb.maximum())
        # 实时保存 AI 回复
        self._messages.append({"role": "assistant", "content": full_text})
        if self._session_id and hasattr(self._iqra, "append_message"):
            try:
                self._iqra.append_message("assistant", full_text, self._session_id)
            except Exception:
                pass

    def _on_stream_tool(self, name: str, status: str):
        icon = "[OK]" if status == "OK" else "[FAIL]" if status == "Failed" else "[...]"
        cursor = self._chat_log.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.BlockUnderCursor)
        cursor.removeSelectedText()
        display = (self._stream_accumulated[-400:] or "").replace('\n', '<br>')
        self._chat_log.append(
            f'{self._stream_header}'
            f'<p style="color:#ccaaff;">{display}'
            f'<span style="color:#888888;"> {name} {icon}</span> '
            f'<span style="color:#88ff88;">_</span></p>'
        )

    # ═══ 悬浮球模式专属方法 ═══

    def eventFilter(self, obj, event):
        """Ctrl+Enter 发送（悬浮球模式）"""
        from PyQt5.QtCore import QEvent
        if self._floating_mode and obj is self._chat_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                self._send()
                return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        """关闭对话框时保存会话并恢复悬浮球语音连接"""
        if self._floating_mode:
            if hasattr(self._iqra, 'save_session'):
                try:
                    self._iqra.save_session()
                except Exception:
                    pass
            parent = self.parent()
            if hasattr(parent, '_enable_voice_handlers'):
                parent._enable_voice_handlers()
        # 非悬浮球模式：用 messages + session_id 保存
        elif self._messages and self._session_id:
            if hasattr(self._iqra, 'save_session'):
                try:
                    self._iqra.save_session(
                        self._messages, self._session_id
                    )
                except Exception:
                    pass
        super().closeEvent(event)

    # ── 语音输入 ──

    def _toggle_voice_input(self):
        """切换语音输入"""
        if not self._voice:
            return
        if self._voice.is_listening():
            self._voice.stop_listening()
            self._mic_btn.setText("🎤")
            parent = self.parent()
            if hasattr(parent, '_enable_voice_handlers'):
                parent._enable_voice_handlers()
        else:
            parent = self.parent()
            if hasattr(parent, '_disable_voice_handlers'):
                parent._disable_voice_handlers()
            self._voice.recognition_result.connect(self._on_voice_result)
            self._voice.start_listening(timeout=6.0)
            self._mic_btn.setText("⏹️")
            self._mic_btn.setStyleSheet(self._mic_btn.styleSheet().replace("rgba(255, 100, 80, 160)", "rgba(255, 80, 80, 220)"))

    def _on_voice_result(self, text: str):
        """语音识别结果"""
        if not self._voice:
            return
        try:
            self._voice.recognition_result.disconnect(self._on_voice_result)
        except TypeError:
            import traceback; traceback.print_exc()
        self._chat_input.setText(text)
        self._mic_btn.setText("🎤")
        parent = self.parent()
        if hasattr(parent, '_enable_voice_handlers'):
            parent._enable_voice_handlers()

    # ── 对话持久化 ──

    def get_messages(self) -> list:
        """返回当前对话的所有消息（供外部 AIChatWindow 保存用）"""
        return list(self._messages)

    def clear_chat(self):
        """清空当前对话显示和消息缓存"""
        self._messages = []
        self._chat_log.clear()

    def _load_history(self):
        """启动时从 MemoryStore 恢复对话历史并在 UI 中显示"""
        if not hasattr(self._iqra, 'get_history'):
            return
        try:
            msgs = self._iqra.get_history()
        except Exception:
            return
        if not msgs:
            return
        self._messages = list(msgs)  # 同步消息缓存
        for msg in msgs:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                self._chat_log.append(
                    f'<p style="color:#80b0ff;"><b>你:</b> {content}</p>'
                )
            elif role == "assistant" and content:
                content_escaped = content.replace('\n', '<br>')
                self._chat_log.append(
                    f'<p style="color:#c0ffc0;"><b>iqra:</b> {content_escaped}</p>'
                )
            elif role == "tool":
                c = msg.get("content", "")[:200]
                self._chat_log.append(
                    f'<p style="color:#666; font-size:11px; margin-left:20px;">  [工具结果] {c}</p>'
                )

    # ── Agent 工具信号 ──

    def _connect_agent_signals(self):
        """连接 AgentLoop 工具信号（实时展示工具调用进度）"""
        if hasattr(self._iqra, 'on_tool_start'):
            self._iqra.on_tool_start.connect(self._on_agent_tool_start)
        if hasattr(self._iqra, 'on_tool_result'):
            self._iqra.on_tool_result.connect(self._on_agent_tool_result)
        if hasattr(self._iqra, 'on_agent_event'):
            self._iqra.on_agent_event.connect(self._on_agent_stage)

    def _on_agent_tool_start(self, name: str, args: dict):
        """AgentLoop 工具调用开始"""
        now = datetime.now().strftime("%H:%M")
        args_short = str(args)[:100] if args else ""
        self._chat_log.append(
            f'<p style="color:#888; font-size:11px; margin-left:20px;">'
            f'  [ACT] 调用工具: <b>{name}</b> {args_short}</p>'
        )

    def _on_agent_tool_result(self, name: str, success: bool, summary: str):
        """AgentLoop 工具执行结果"""
        icon = "OK" if success else "FAIL"
        color = "#44aa44" if success else "#cc4444"
        self._chat_log.append(
            f'<p style="color:{color}; font-size:11px; margin-left:20px;">'
            f'  [{name}: {icon}] {summary}</p>'
        )

    def _on_agent_stage(self, event):
        """AgentLoop 阶段变更"""
        stage_name = event.type.name if hasattr(event.type, 'name') else str(event.type)
        label = self._STAGE_LABELS.get(stage_name, stage_name)
        color_map = {
            "THINK": "#6688cc", "PLAN": "#8866cc", "ACT": "#cc8866",
            "OBSERVE": "#66cc88", "REFLECT": "#cc66aa", "COMPLETE": "#44cc44",
        }
        color = color_map.get(stage_name, "#888")
        msg = event.message[:200] if hasattr(event, 'message') else ""
        self._chat_log.append(
            f'<p style="color:{color}; font-size:11px; margin-left:10px;">'
            f'  [{label}] {msg}</p>'
        )


# ═══════════════════════════════════════════
# 子模块弹窗包装器
# ═══════════════════════════════════════════

```
