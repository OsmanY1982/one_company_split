# `core/modules/intelligence/quick_tools_panel/_api_config.py`

> 路径：`core/modules/intelligence/quick_tools_panel/_api_config.py` | 行数：300


---


```python
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QMessageBox,
    QGroupBox, QComboBox, QCheckBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from core.modules.intelligence._ai_shared import ButtonAnimationHelper


class APIKeyConfigDialog(QDialog):
    config_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("\U0001f511 \u914d\u7f6e\u4e91\u7aef\u6a21\u578b")
        self.setMinimumSize(520, 480)
        self.resize(560, 520)
        self._saved_keys = {}
        self._load_saved_keys()
        self._build_ui()

    def _load_saved_keys(self):
        try:
            from core.modules.intelligence._stubs import OpcSecureStorage as SecureStorage
            storage = SecureStorage()
            keys = storage.load_all_keys()
            alias_map = {
                "\u963f\u91cc\u4e91\u767e\u70bc": "bailian",
                "\u767e\u70bc": "bailian",
                "\u901a\u4e49\u5343\u95ee": "qwen",
                "\u5343\u95ee": "qwen",
            }
            for k, v in keys.items():
                if ":" in k:
                    _, key_id = k.split(":", 1)
                else:
                    key_id = k
                if key_id in alias_map:
                    key_id = alias_map[key_id]
                self._saved_keys[key_id] = v
        except Exception:
            self._saved_keys = {}

    def _on_provider_changed(self, index):
        provider = self.provider_combo.currentData()
        if provider and provider in self._saved_keys:
            self.key_input.setText(self._saved_keys[provider])
        else:
            self.key_input.clear()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(18)

        title = QLabel("\u26a1 \u5feb\u901f\u914d\u7f6e AI \u6a21\u578b")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet("color: #1a202c;")
        layout.addWidget(title)

        desc = QLabel("\u9009\u62e9\u6a21\u578b\u4f9b\u5e94\u5546\u5e76\u8f93\u5165 API Key\uff0c\u5373\u53ef\u5f00\u59cb\u4f7f\u7528 AI \u52a9\u624b")
        desc.setStyleSheet("color: #718096; font-size: 14px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(8)

        plat_group = QGroupBox("\u9009\u62e9\u6a21\u578b\u4f9b\u5e94\u5546")
        plat_group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                color: #2d3748;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                margin-top: 14px;
                padding: 18px 16px 14px 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #2b6cb0;
            }
        """)
        plat_layout = QVBoxLayout(plat_group)
        plat_layout.setContentsMargins(8, 8, 8, 8)

        self.provider_combo = QComboBox()
        self.provider_combo.setMinimumHeight(40)
        self.provider_combo.setCursor(Qt.PointingHandCursor)
        providers = [
            ("DeepSeek (\u63a8\u8350)", "deepseek"),
            ("OpenAI", "openai"),
            ("\u901a\u4e49\u5343\u95ee (\u963f\u91cc\u4e91)", "qwen"),
            ("\u667a\u8c31 GLM", "glm"),
            ("Moonshot (\u6708\u4e4b\u6697\u9762)", "moonshot"),
            ("SiliconFlow", "siliconflow"),
            ("\u963f\u91cc\u4e91\u767e\u70bc", "bailian"),
        ]
        for name, pid in providers:
            self.provider_combo.addItem(name, pid)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        self.provider_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background: white;
            }
            QComboBox:focus { border-color: #2b6cb0; }
            QComboBox::drop-down { border: none; }
        """)
        plat_layout.addWidget(self.provider_combo)
        layout.addWidget(plat_group)

        key_group = QGroupBox("API Key")
        key_group.setStyleSheet(plat_group.styleSheet())
        key_layout = QVBoxLayout(key_group)
        key_layout.setContentsMargins(8, 8, 8, 8)
        key_layout.setSpacing(12)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("\u5728\u6b64\u7c98\u8d34 API Key...")
        self.key_input.setEchoMode(QLineEdit.Password)
        self.key_input.setMinimumHeight(40)
        self.key_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus { border-color: #2b6cb0; }
        """)
        key_layout.addWidget(self.key_input)

        show_key = QCheckBox("\u663e\u793a Key")
        show_key.setStyleSheet("color: #718096; font-size: 13px;")
        show_key.toggled.connect(lambda checked: self.key_input.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        ))
        key_layout.addWidget(show_key)

        layout.addWidget(key_group)

        links_layout = QHBoxLayout()
        links_layout.setSpacing(10)
        links = [
            ("DeepSeek", "https://platform.deepseek.com/"),
            ("OpenAI", "https://platform.openai.com/"),
            ("\u901a\u4e49\u5343\u95ee", "https://dashscope.aliyun.com/"),
            ("SiliconFlow", "https://cloud.siliconflow.cn/"),
        ]
        for name, url in links:
            btn = QPushButton(name)
            btn.setMinimumHeight(32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #2b6cb0;
                    border: 1px solid #2b6cb0;
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #2b6cb0;
                    color: white;
                }
            """)
            btn.clicked.connect(lambda checked, u=url: self._open_url(u))
            links_layout.addWidget(btn)
        links_layout.addStretch()
        layout.addLayout(links_layout)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("\u53d6\u6d88")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #718096;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 14px;
            }
            QPushButton:hover { background: #f7fafc; }
            QPushButton:pressed { padding-top: 9px; padding-bottom: 7px; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("\U0001f4be \u4fdd\u5b58\u5e76\u8fde\u63a5")
        save_btn.setMinimumHeight(40)
        save_btn.setMinimumWidth(140)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b6cb0;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #2c5282; }
            QPushButton:pressed { background-color: #2a4365; padding-top: 9px; padding-bottom: 7px; }
        """)
        save_btn.clicked.connect(self._save_config)
        ButtonAnimationHelper.apply_scale_animation(save_btn, 1.03)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _open_url(self, url):
        import webbrowser
        webbrowser.open(url)

    def _save_config(self):
        provider = self.provider_combo.currentData()
        key = self.key_input.text().strip()

        if not key:
            QMessageBox.warning(self, "\u63d0\u793a", "\u8bf7\u8f93\u5165 API Key")
            return

        try:
            from core.modules.intelligence._stubs import OpcConfigManager as ConfigManager
            from core.modules.intelligence._compat import DATA_DIR as data_dir
            config = ConfigManager(data_dir)

            provider_configs = {
                "deepseek": {
                    "name": "DeepSeek",
                    "provider_type": "openai_compatible",
                    "base_url": "https://api.deepseek.com/v1",
                    "model": "deepseek-chat",
                },
                "openai": {
                    "name": "OpenAI",
                    "provider_type": "openai_compatible",
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-3.5-turbo",
                },
                "qwen": {
                    "name": "\u901a\u4e49\u5343\u95ee",
                    "provider_type": "openai_compatible",
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "model": "qwen-turbo",
                },
                "glm": {
                    "name": "\u667a\u8c31 GLM",
                    "provider_type": "openai_compatible",
                    "base_url": "https://open.bigmodel.cn/api/paas/v4",
                    "model": "glm-4-flash",
                },
                "moonshot": {
                    "name": "Moonshot",
                    "provider_type": "openai_compatible",
                    "base_url": "https://api.moonshot.cn/v1",
                    "model": "moonshot-v1-8k",
                },
                "siliconflow": {
                    "name": "SiliconFlow",
                    "provider_type": "openai_compatible",
                    "base_url": "https://api.siliconflow.cn/v1",
                    "model": "deepseek-ai/DeepSeek-V3",
                },
                "bailian": {
                    "name": "\u963f\u91cc\u4e91\u767e\u70bc",
                    "provider_type": "openai_compatible",
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "model": "qwen-plus",
                },
            }

            cfg = provider_configs.get(provider, provider_configs["deepseek"])
            cfg["api_key"] = key

            config.add_provider("cloud", provider, cfg)
            config.set_active_provider(provider, "cloud")

            QMessageBox.information(self, "\u6210\u529f", "\u914d\u7f6e\u5df2\u4fdd\u5b58\uff01AI \u52a9\u624b\u5df2\u5c31\u7eea\u3002")
            self.config_saved.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "\u9519\u8bef", f"\u4fdd\u5b58\u914d\u7f6e\u5931\u8d25: {e}")

```
