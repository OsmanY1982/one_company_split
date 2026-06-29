# `iqra/iqra_chat.py`

> 路径：`iqra/iqra_chat.py` | 行数：353


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
import time

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
from iqra.core.workspace_watcher import WorkspaceWatcher

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
        self._episodic_memory = None    # 跨会话情节记忆
        self._semantic_memory = None    # 语义记忆层（知识图谱）
        self._project_knowledge = None  # 项目知识库索引
        self.workspace_watcher = None
        self._cached_changes_summary = None
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

        # 初始化情节记忆引擎
        try:
            from core.episodic_memory import EpisodicMemory
            data_dir = os.path.join(PROJECT_ROOT, "data")
            self._episodic_memory = EpisodicMemory(data_dir=data_dir, project="iqra")
            self._add_system_msg("情节记忆引擎已加载")
        except Exception as e:
            self._episodic_memory = None

        # 初始化语义记忆（知识图谱）
        try:
            from iqra.core.semantic_memory import SemanticMemory
            self._semantic_memory = SemanticMemory()
            s = self._semantic_memory.stats()
            self._add_system_msg(
                f"语义记忆已加载 (实体: {s['entity_count']}, 关系: {s['relation_count']}, 事实: {s['fact_count']})")
        except Exception:
            self._semantic_memory = None

        # 初始化项目知识库
        try:
            from iqra.core.project_knowledge import ProjectKnowledge
            self._project_knowledge = ProjectKnowledge()
            s = self._project_knowledge.build_index()
            self._add_system_msg(
                f"项目知识库已加载 (文件: {s['file_count']}, 分块: {s['chunk_count']})")
        except Exception:
            self._project_knowledge = None

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

        # 初始化工作区监视器
        try:
            self.workspace_watcher = WorkspaceWatcher()
            self.workspace_watcher.start()
            self._cached_changes_summary = self.workspace_watcher.get_changes_summary(since_seconds=86400)
            if any(self._cached_changes_summary.values()):
                self._add_system_msg("工作区监视器已启动")
        except Exception:
            self.workspace_watcher = None
            self._cached_changes_summary = None

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

        # 检测工作区变更查询
        change_kw = ["最近改了什么", "最近变了什么", "文件变更", "改了什么", "最近修改", "最近变更"]
        if any(kw in text for kw in change_kw) and self.workspace_watcher:
            try:
                changes = self.workspace_watcher.get_recent_changes(since_seconds=86400)
                if changes:
                    lines = []
                    for c in changes[:30]:
                        ts = time.strftime("%H:%M:%S", time.localtime(c["timestamp"]))
                        lines.append(f"• [{c['event_type']}] {c['file_path']} ({ts})")
                    self._add_assistant_msg("工作区最近 24h 文件变更：\n" + "\n".join(lines))
                else:
                    self._add_assistant_msg("最近 24 小时工作区无文件变更。")
            except Exception:
                self._add_assistant_msg("无法获取工作区变更信息。")
            self._input.setEnabled(True)
            self._send_btn.setEnabled(True)
            return

        # 注入上下文：项目知识 > 工作区变更 > 语义记忆 > 情节记忆
        augmented_text = text
        context_parts = []

        # 1. 项目知识库检索
        if self._project_knowledge:
            try:
                ctx = self._project_knowledge.get_relevant_context(text, top_k=3)
                if ctx:
                    context_parts.append(f"[项目知识]\n{ctx}")
            except Exception:
                pass

        # 1.5 工作区变更摘要
        if self.workspace_watcher:
            try:
                summary = self.workspace_watcher.get_changes_summary(since_seconds=86400)
                if any(summary.values()):
                    s = f"新增 {summary['created']} 文件、修改 {summary['modified']} 文件、删除 {summary['deleted']} 文件"
                    context_parts.append(f"[工作区变更(24h)]\n{s}")
            except Exception:
                pass

        # 2. 语义记忆检索
        if self._semantic_memory:
            try:
                ctx = self._semantic_memory.get_context(text, top_k=3)
                if ctx:
                    context_parts.append(f"[语义记忆]\n{ctx}")
            except Exception:
                pass

        # 3. 情节记忆检索（已有）
        if self._episodic_memory:
            try:
                ctx = self._episodic_memory.get_context(text)
                if ctx:
                    context_parts.append(f"[情节记忆]\n{ctx}")
            except Exception:
                pass

        if context_parts:
            augmented_text = "\n\n".join(context_parts) + "\n\n[当前对话]\n" + text

        self._status.setText("Iqra 思考中...")
        threading.Thread(target=self._run_chat, args=(augmented_text, text), daemon=True).start()

    def _run_chat(self, user_input, original_text=None):
        try:
            self._signals.thinking.emit(True)
            response = self._engine.chat(user_input)
            self._signals.response_ready.emit(response)

            # 记录会话到情节记忆
            if original_text and self._episodic_memory:
                try:
                    self._episodic_memory.record(
                        user_query=original_text,
                        summary=response[:500],
                    )
                except Exception:
                    pass
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
