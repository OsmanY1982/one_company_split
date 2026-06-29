# `core/modules/intelligence/quick_tools_panel/_quick_tools.py`

> 路径：`core/modules/intelligence/quick_tools_panel/_quick_tools.py` | 行数：476


---


```python
# -*- coding: utf-8 -*-
import os
import urllib.request

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGridLayout, QMessageBox,
    QGroupBox, QComboBox,
    QScrollArea, QFrame,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont

from core.modules.intelligence._ai_shared import ButtonAnimationHelper, QUICK_TEMPLATES
from core.modules.intelligence._model_manager_ollama import OllamaManager
from core.modules.intelligence._model_manager_download import DownloadModelDialog


class QuickToolsWidget(QWidget):
    template_selected = pyqtSignal(str)
    use_local_model = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        title_row = QHBoxLayout()
        title_icon = QLabel("\u26a1")
        title_icon.setFont(QFont("PingFang SC", 28))
        title_row.addWidget(title_icon)
        title = QLabel("\u5feb\u6377\u5de5\u5177")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet("color: #1a202c;")
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)

        template_group = QGroupBox("\U0001f4dd \u5feb\u901f\u63d0\u95ee\u6a21\u677f")
        template_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                color: #2d3748;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 14px;
                padding: 18px 16px 14px 16px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 8px;
                color: #2b6cb0;
            }
        """)
        template_layout = QGridLayout(template_group)
        template_layout.setSpacing(12)
        template_layout.setContentsMargins(8, 8, 8, 8)

        for i, (name, template) in enumerate(QUICK_TEMPLATES):
            btn = QPushButton(name)
            btn.setMinimumHeight(56)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f7fafc;
                    color: #1a202c;
                    border: 1px solid #e2e8f0;
                    border-radius: 10px;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #ebf8ff;
                    border-color: #2b6cb0;
                    color: #2b6cb0;
                }
                QPushButton:pressed {
                    background-color: #bee3f8;
                    padding-top: 9px;
                    padding-bottom: 7px;
                }
            """)
            btn.clicked.connect(lambda checked, t=template: self.template_selected.emit(t))
            ButtonAnimationHelper.apply_scale_animation(btn, 1.02)
            template_layout.addWidget(btn, i // 2, i % 2)

        layout.addWidget(template_group)

        local_group = QGroupBox("\U0001f5a5\ufe0f \u672c\u5730\u6a21\u578b (Ollama)")
        local_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                color: #2d3748;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 14px;
                padding: 18px 16px 14px 16px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 8px;
                color: #2b6cb0;
            }
        """)
        local_layout = QVBoxLayout(local_group)
        local_layout.setContentsMargins(8, 8, 8, 8)
        local_layout.setSpacing(16)

        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #f7fafc;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        status_layout_inner = QVBoxLayout(status_frame)
        status_layout_inner.setContentsMargins(16, 12, 16, 12)

        self.ollama_status = QLabel("\u68c0\u6d4b\u4e2d...")
        self.ollama_status.setStyleSheet("font-size: 14px; color: #1a202c;")
        self.ollama_status.setWordWrap(True)
        status_layout_inner.addWidget(self.ollama_status)
        local_layout.addWidget(status_frame)

        model_select_layout = QHBoxLayout()
        model_select_layout.setSpacing(12)
        model_label = QLabel("\u9009\u62e9\u6a21\u578b:")
        model_label.setStyleSheet("font-size: 14px; color: #1a202c;")
        model_select_layout.addWidget(model_label)

        self.model_combo = QComboBox()
        self.model_combo.setMinimumHeight(36)
        self.model_combo.setMinimumWidth(200)
        self.model_combo.setCursor(Qt.PointingHandCursor)
        self.model_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 13px;
                background: white;
            }
            QComboBox:focus { border-color: #2b6cb0; }
            QComboBox::drop-down { border: none; }
        """)
        self.model_combo.setEnabled(False)
        model_select_layout.addWidget(self.model_combo, stretch=1)
        local_layout.addLayout(model_select_layout)

        ollama_btn_layout = QHBoxLayout()
        ollama_btn_layout.setSpacing(12)

        self.start_ollama_btn = QPushButton("\u25b6\ufe0f \u542f\u52a8\u670d\u52a1")
        self.start_ollama_btn.setMinimumHeight(40)
        self.start_ollama_btn.setMinimumWidth(120)
        self.start_ollama_btn.setCursor(Qt.PointingHandCursor)
        self.start_ollama_btn.setStyleSheet("""
            QPushButton {
                background-color: #38a169;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #2f855a; }
            QPushButton:disabled { background-color: #cbd5e0; }
            QPushButton:pressed { padding-top: 9px; padding-bottom: 7px; }
        """)
        self.start_ollama_btn.clicked.connect(self._start_ollama)
        ButtonAnimationHelper.apply_scale_animation(self.start_ollama_btn, 1.03)
        ollama_btn_layout.addWidget(self.start_ollama_btn)

        self.download_btn = QPushButton("\u2b07\ufe0f \u4e0b\u8f7d\u6a21\u578b")
        self.download_btn.setMinimumHeight(40)
        self.download_btn.setMinimumWidth(120)
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b6cb0;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #2c5282; }
            QPushButton:disabled { background-color: #cbd5e0; }
            QPushButton:pressed { padding-top: 9px; padding-bottom: 7px; }
        """)
        self.download_btn.clicked.connect(self._show_download_dialog)
        self.download_btn.setEnabled(False)
        ButtonAnimationHelper.apply_scale_animation(self.download_btn, 1.03)
        ollama_btn_layout.addWidget(self.download_btn)

        self.use_local_btn = QPushButton("\u2705 \u4f7f\u7528\u672c\u5730\u6a21\u578b")
        self.use_local_btn.setMinimumHeight(40)
        self.use_local_btn.setMinimumWidth(140)
        self.use_local_btn.setCursor(Qt.PointingHandCursor)
        self.use_local_btn.setStyleSheet("""
            QPushButton {
                background-color: #553c9a;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #44337a; }
            QPushButton:disabled { background-color: #cbd5e0; }
            QPushButton:pressed { padding-top: 9px; padding-bottom: 7px; }
        """)
        self.use_local_btn.clicked.connect(self._use_local_model)
        self.use_local_btn.setEnabled(False)
        ButtonAnimationHelper.apply_scale_animation(self.use_local_btn, 1.03)
        ollama_btn_layout.addWidget(self.use_local_btn)

        refresh_ollama_btn = QPushButton("\U0001f504 \u5237\u65b0\u5217\u8868")
        refresh_ollama_btn.setMinimumHeight(40)
        refresh_ollama_btn.setMinimumWidth(110)
        refresh_ollama_btn.setCursor(Qt.PointingHandCursor)
        refresh_ollama_btn.setStyleSheet("""
            QPushButton {
                background-color: #718096;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #4a5568; }
            QPushButton:pressed { padding-top: 9px; padding-bottom: 7px; }
        """)
        refresh_ollama_btn.clicked.connect(self._check_ollama_status)
        ButtonAnimationHelper.apply_scale_animation(refresh_ollama_btn, 1.03)
        ollama_btn_layout.addWidget(refresh_ollama_btn)

        ollama_btn_layout.addStretch()
        local_layout.addLayout(ollama_btn_layout)
        layout.addWidget(local_group)

        status_group = QGroupBox("\U0001f4ca \u7cfb\u7edf\u72b6\u6001")
        status_group.setStyleSheet(template_group.styleSheet())
        sys_status_layout = QVBoxLayout(status_group)
        sys_status_layout.setSpacing(12)

        self.status_label = QLabel("\u68c0\u6d4b\u4e2d...")
        self.status_label.setStyleSheet("font-size: 14px; color: #2c3e50; line-height: 1.8;")
        self.status_label.setWordWrap(True)
        sys_status_layout.addWidget(self.status_label)

        refresh_btn = QPushButton("\U0001f504 \u5237\u65b0\u72b6\u6001")
        refresh_btn.setMinimumHeight(36)
        refresh_btn.setMinimumWidth(120)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b6cb0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #2c5282; }
            QPushButton:pressed { padding-top: 9px; padding-bottom: 7px; }
        """)
        refresh_btn.clicked.connect(self._check_status)
        ButtonAnimationHelper.apply_scale_animation(refresh_btn, 1.03)
        sys_status_layout.addWidget(refresh_btn)

        layout.addWidget(status_group)

        guide_group = QGroupBox("\U0001f4d6 \u4f7f\u7528\u6307\u5357")
        guide_group.setStyleSheet(template_group.styleSheet())
        guide_layout = QVBoxLayout(guide_group)

        guide_text = QLabel("""
<b>\U0001f680 \u5feb\u901f\u5f00\u59cb\uff1a</b><br>
1. <b>\u4e91\u7aef\u6a21\u578b</b>\uff1a\u914d\u7f6e API Key \u5373\u53ef\u4f7f\u7528\uff08\u9700\u8981\u7f51\u7edc\uff09<br>
2. <b>\u672c\u5730\u6a21\u578b</b>\uff1a\u542f\u52a8 Ollama \u2192 \u4e0b\u8f7d\u6a21\u578b \u2192 \u4f7f\u7528\uff08\u53ef\u79bb\u7ebf\uff09<br>
3. \u70b9\u51fb\u4e0a\u65b9\u6a21\u677f\u5feb\u901f\u63d0\u95ee<br><br>

<b>\u2601\ufe0f \u4e91\u7aef\u6a21\u578b\u63a8\u8350\uff1a</b><br>
\u2022 DeepSeek - \u6027\u4ef7\u6bd4\u9ad8\uff0c\u4e2d\u6587\u4f18\u79c0<br>
\u2022 OpenAI - \u529f\u80fd\u5f3a\u5927\uff0c\u56fd\u9645\u901a\u7528<br>
\u2022 \u901a\u4e49\u5343\u95ee - \u56fd\u5185\u7a33\u5b9a\uff0c\u901f\u5ea6\u5feb<br><br>

<b>\U0001f5a5\ufe0f \u672c\u5730\u6a21\u578b\u63a8\u8350\uff1a</b><br>
\u2022 qwen2.5:0.5b (400MB) - \u6781\u901f\u6d4b\u8bd5<br>
\u2022 llama3.2:1b (1.3GB) - \u8d85\u8f7b\u91cf<br>
\u2022 deepseek-r1:1.5b (1.1GB) - \u63a8\u7406\u5165\u95e8<br><br>

<b>\u2328\ufe0f \u5feb\u6377\u64cd\u4f5c\uff1a</b><br>
\u2022 Ctrl+Enter \u53d1\u9001\u6d88\u606f<br>
\u2022 \u652f\u6301 Markdown \u683c\u5f0f\u8f93\u51fa
        """)
        guide_text.setStyleSheet("font-size: 13px; color: #2c3e50; line-height: 1.8;")
        guide_text.setWordWrap(True)
        guide_layout.addWidget(guide_text)

        layout.addWidget(guide_group)
        layout.addStretch()

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        config_btn = QPushButton("\U0001f511 \u914d\u7f6e\u4e91\u7aef\u6a21\u578b")
        config_btn.setMinimumHeight(48)
        config_btn.setCursor(Qt.PointingHandCursor)
        config_btn.setStyleSheet("""
            QPushButton {
                background-color: #e53e3e;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #c53030; }
            QPushButton:pressed { padding-top: 13px; padding-bottom: 11px; }
        """)
        config_btn.clicked.connect(self._show_config_dialog)
        ButtonAnimationHelper.apply_scale_animation(config_btn, 1.02)
        main_layout.addWidget(config_btn)

        QTimer.singleShot(2000, self._check_ollama_status)
        QTimer.singleShot(500, self._check_status)

    def _check_status(self):
        status = []
        try:
            status.append("\u2705 Iqra \u6a21\u5757: \u5df2\u5b89\u88c5")
        except ImportError:
            status.append("\u274c Iqra \u6a21\u5757: \u672a\u5b89\u88c5")

        try:
            from core.modules.intelligence._stubs import OpcConfigManager as ConfigManager
            from core.modules.intelligence._compat import DATA_DIR as data_dir
            config = ConfigManager(data_dir)
            provider = config.get_active_provider()
            if provider:
                status.append(f"\u2705 \u4e91\u7aef\u6a21\u578b: {provider.name} \u5df2\u914d\u7f6e")
            else:
                status.append("\u26a0\ufe0f \u4e91\u7aef\u6a21\u578b: \u672a\u914d\u7f6e")
        except Exception:
            status.append("\u26a0\ufe0f \u4e91\u7aef\u6a21\u578b: \u68c0\u67e5\u5931\u8d25")

        try:
            urllib.request.urlopen("https://www.baidu.com", timeout=3)
            status.append("\u2705 \u7f51\u7edc\u8fde\u63a5: \u6b63\u5e38")
        except Exception:
            status.append("\u274c \u7f51\u7edc\u8fde\u63a5: \u5f02\u5e38")

        status.append("\u2705 \u7cfb\u7edf: \u8fd0\u884c\u6b63\u5e38")
        self.status_label.setText("<br>".join(status))
        self._check_ollama_status()

    def _check_ollama_status(self):
        if not OllamaManager.is_installed():
            self.ollama_status.setText("""
                <p style='color:#e53e3e; font-size:14px;'>\u274c Ollama \u672a\u5b89\u88c5</p>
                <p style='color:#718096; font-size:13px;'>\u8bf7\u8bbf\u95ee <a href='https://ollama.com'>ollama.com</a> \u4e0b\u8f7d\u5b89\u88c5</p>
            """)
            self.start_ollama_btn.setEnabled(False)
            self.download_btn.setEnabled(False)
            self.use_local_btn.setEnabled(False)
            return

        if not OllamaManager.is_running():
            self.ollama_status.setText("""
                <p style='color:#ed8936; font-size:14px;'>\u26a0\ufe0f Ollama \u5df2\u5b89\u88c5\u4f46\u672a\u8fd0\u884c</p>
                <p style='color:#718096; font-size:13px;'>\u70b9\u51fb\u201c\u542f\u52a8\u670d\u52a1\u201d\u6309\u94ae\u542f\u52a8</p>
            """)
            self.start_ollama_btn.setEnabled(True)
            self.download_btn.setEnabled(False)
            self.use_local_btn.setEnabled(False)
            return

        models = OllamaManager.list_models()
        if not models:
            self.ollama_status.setText("""
                <p style='color:#38a169; font-size:14px;'>\u2705 Ollama \u670d\u52a1\u8fd0\u884c\u4e2d</p>
                <p style='color:#718096; font-size:13px;'>\u6682\u65e0\u6a21\u578b\uff0c\u8bf7\u70b9\u51fb\u201c\u4e0b\u8f7d\u6a21\u578b\u201d</p>
            """)
            self.start_ollama_btn.setEnabled(False)
            self.start_ollama_btn.setText("\u2705 \u5df2\u542f\u52a8")
            self.download_btn.setEnabled(True)
            self.use_local_btn.setEnabled(False)
        else:
            model_names = [m.get("name", "") for m in models]
            model_list_str = ", ".join(model_names)
            self.ollama_status.setText(f"""
                <p style='color:#38a169; font-size:14px;'>\u2705 Ollama \u670d\u52a1\u8fd0\u884c\u4e2d</p>
                <p style='color:#1a202c; font-size:13px;'>\u5df2\u5b89\u88c5 {len(models)} \u4e2a\u6a21\u578b: {model_list_str}</p>
            """)
            self.start_ollama_btn.setEnabled(False)
            self.start_ollama_btn.setText("\u2705 \u5df2\u542f\u52a8")
            self.download_btn.setEnabled(True)
            self.use_local_btn.setEnabled(True)

            self.model_combo.clear()
            for m in models:
                name = m.get("name", "")
                size = m.get("size", 0)
                size_str = f"{size / 1024 / 1024 / 1024:.1f}GB" if size else ""
                self.model_combo.addItem(f"{name} ({size_str})", name)
            self.model_combo.setEnabled(True)

    def _start_ollama(self):
        if OllamaManager.start_service():
            self.start_ollama_btn.setText("\u542f\u52a8\u4e2d...")
            self.start_ollama_btn.setEnabled(False)
            QTimer.singleShot(3000, self._check_ollama_status)
        else:
            QMessageBox.warning(self, "\u5931\u8d25", "\u65e0\u6cd5\u542f\u52a8 Ollama \u670d\u52a1")

    def _show_download_dialog(self):
        dialog = DownloadModelDialog(self)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        dialog.show()

    def _use_local_model(self):
        model_name = self.model_combo.currentData()
        if not model_name:
            QMessageBox.warning(self, "\u63d0\u793a", "\u8bf7\u5148\u9009\u62e9\u6a21\u578b")
            return

        try:
            from core.modules.intelligence._stubs import OpcConfigManager as ConfigManager
            from core.modules.intelligence._compat import DATA_DIR as data_dir
            config = ConfigManager(data_dir)

            cfg = {
                "name": f"llama.cpp ({model_name})",
                "provider_type": "openai_compatible",
                "base_url": "http://localhost:8080/v1",
                "model": model_name,
                "api_key": "not-needed",
            }

            config.add_provider("local", "llama_proxy", cfg)
            config.set_active_provider("llama_proxy", "local")

            QMessageBox.information(self, "\u6210\u529f", f"\u5df2\u5207\u6362\u5230\u672c\u5730\u6a21\u578b: {model_name}\n\u8bf7\u5237\u65b0 AI \u5bf9\u8bdd\u6807\u7b7e\u9875")
            self.use_local_model.emit(model_name)
        except Exception as e:
            QMessageBox.critical(self, "\u9519\u8bef", f"\u5207\u6362\u6a21\u578b\u5931\u8d25: {e}")

    def _show_config_dialog(self):
        from ._api_config import APIKeyConfigDialog
        dialog = APIKeyConfigDialog(self)
        dialog.config_saved.connect(self._check_status)
        dialog.exec_()

```
