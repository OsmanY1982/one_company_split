# `iqra/iqra_setup.py`

> 路径：`iqra/iqra_setup.py` | 行数：267


---


```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Iqra 模型配置窗口 — 独立版（无管理系统依赖）
保存配置到 data/iqra_config.json，供 IqraCoreEngine 读取
"""
import os, sys, json

# 将项目根目录加入 path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QStackedWidget,
    QFrame, QMessageBox, QCheckBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from core.dark_theme import apply_dark_theme

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CONFIG_PATH = os.path.join(DATA_DIR, "iqra_config.json")

# ── 预设供应商 ──
CLOUD_PROVIDERS = [
    {"id": "deepseek",     "name": "DeepSeek",       "base_url": "https://api.deepseek.com/v1",             "models": ["deepseek-chat", "deepseek-reasoner"]},
    {"id": "openai",       "name": "OpenAI",          "base_url": "https://api.openai.com/v1",               "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]},
    {"id": "claude",       "name": "Anthropic Claude","base_url": "https://api.anthropic.com/v1",            "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514"]},
    {"id": "tongyi",       "name": "通义千问",        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "models": ["qwen-plus", "qwen-max", "qwen-turbo"]},
    {"id": "zhipu",        "name": "智谱 GLM",        "base_url": "https://open.bigmodel.cn/api/paas/v4",   "models": ["glm-4-plus", "glm-4-flash"]},
    {"id": "moonshot",     "name": "Moonshot",        "base_url": "https://api.moonshot.cn/v1",              "models": ["moonshot-v1-8k", "moonshot-v1-32k"]},
    {"id": "siliconflow",  "name": "SiliconFlow",     "base_url": "https://api.siliconflow.cn/v1",           "models": ["deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-72B-Instruct"]},
    {"id": "openrouter",   "name": "OpenRouter",      "base_url": "https://openrouter.ai/api/v1",            "models": ["openai/gpt-4o", "anthropic/claude-sonnet-4-20250514"]},
]

LOCAL_PROVIDERS = [
    {"id": "ollama",    "name": "Ollama",     "base_url": "http://localhost:11434/v1", "models": ["qwen2.5:7b", "llama3.1:8b", "codellama:7b"]},
    {"id": "lmstudio",  "name": "LM Studio",  "base_url": "http://localhost:1234/v1",  "models": ["local-model"]},
    {"id": "vllm",      "name": "vLLM",       "base_url": "http://localhost:8000/v1",  "models": ["default"]},
    {"id": "llamacpp",  "name": "llama.cpp",  "base_url": "http://localhost:8080/v1",  "models": ["local"]},
]

# Iqra 模型配置窗口特有样式（叠加在 BASE_DARK_STYLE 之上）
IQRA_SETUP_EXTRA_STYLE = """
QLabel#title { font-size: 22px; font-weight: bold; color: #cba6f7; }
QLabel#subtitle { font-size: 13px; color: #6c7086; }
QPushButton {
    background: #5850ec; color: white; border: none;
    border-radius: 8px; padding: 10px 24px; font-size: 14px; font-weight: bold;
}
QPushButton:hover { background: #6c63ff; }
QPushButton#secondary {
    background: #313244; color: #cdd6f4;
}
QPushButton#secondary:hover { background: #45475a; }
QPushButton#danger { background: #e64553; }
QPushButton#danger:hover { background: #d20f39; }
QLineEdit {
    background: #313244; color: #cdd6f4; border: 1px solid #45475a;
    border-radius: 6px; padding: 10px; font-size: 14px;
}
QLineEdit:focus { border-color: #5850ec; }
QComboBox {
    background: #313244; color: #cdd6f4; border: 1px solid #45475a;
    border-radius: 6px; padding: 10px; font-size: 14px; min-width: 200px;
}
QComboBox:focus { border-color: #5850ec; }
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background: #313244; color: #cdd6f4; selection-background-color: #5850ec;
}
QFrame#card {
    background: #1e1e2e; border: 1px solid #313244;
    border-radius: 12px; padding: 20px;
}
"""


class ModelSetupWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Iqra — 模型配置")
        self.setFixedSize(520, 560)
        apply_dark_theme(self)
        self.setStyleSheet(self.styleSheet() + IQRA_SETUP_EXTRA_STYLE)

        self._provider_list = []  # [(id, type)]
        self._build_ui()
        self._on_provider_type_changed(0)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(16)
        layout.setContentsMargins(32, 28, 32, 28)

        # 标题
        title = QLabel("Iqra AI 引擎")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("配置模型以启动 AI 对话")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # ── 类型选择 ──
        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setSpacing(12)

        type_label = QLabel("提供商类型")
        type_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #cba6f7;")
        cl.addWidget(type_label)

        self._type_combo = QComboBox()
        self._type_combo.addItems(["云端 API", "本地服务"])
        self._type_combo.currentIndexChanged.connect(self._on_provider_type_changed)
        cl.addWidget(self._type_combo)

        # ── 提供商选择 ──
        prov_label = QLabel("模型供应商")
        prov_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #cba6f7;")
        cl.addWidget(prov_label)

        self._provider_combo = QComboBox()
        self._provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        cl.addWidget(self._provider_combo)

        # ── API Key ──
        api_label = QLabel("API Key")
        api_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #cba6f7;")
        cl.addWidget(api_label)

        self._api_key_input = QLineEdit()
        self._api_key_input.setPlaceholderText("输入 API Key（本地服务可留空）")
        self._api_key_input.setEchoMode(QLineEdit.Password)
        cl.addWidget(self._api_key_input)

        # ── 模型 ──
        model_label = QLabel("模型")
        model_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #cba6f7;")
        cl.addWidget(model_label)

        self._model_combo = QComboBox()
        self._model_combo.setEditable(True)
        cl.addWidget(self._model_combo)

        layout.addWidget(card)
        layout.addStretch()

        # ── 按钮 ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        clear_btn = QPushButton("跳过（使用默认）")
        clear_btn.setObjectName("secondary")
        clear_btn.clicked.connect(self._skip)
        btn_row.addWidget(clear_btn)

        save_btn = QPushButton("保存并启动")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _on_provider_type_changed(self, idx):
        provider_type = "cloud" if idx == 0 else "local"
        providers = CLOUD_PROVIDERS if idx == 0 else LOCAL_PROVIDERS
        self._provider_combo.blockSignals(True)
        self._provider_combo.clear()
        self._provider_list.clear()
        for p in providers:
            self._provider_combo.addItem(p["name"])
            self._provider_list.append((p["id"], provider_type))
        self._provider_combo.blockSignals(False)
        self._provider_combo.setCurrentIndex(0)
        self._on_provider_changed(0)

        # 云端显示 API Key，本地隐藏
        self._api_key_input.setVisible(idx == 0)

    def _on_provider_changed(self, idx):
        if idx < 0 or idx >= len(self._provider_list):
            return
        pid, ptype = self._provider_list[idx]
        providers = CLOUD_PROVIDERS if ptype == "cloud" else LOCAL_PROVIDERS
        provider = next((p for p in providers if p["id"] == pid), None)
        if not provider:
            return
        self._model_combo.blockSignals(True)
        self._model_combo.clear()
        self._model_combo.addItems(provider["models"])
        self._model_combo.setCurrentIndex(0)
        self._model_combo.blockSignals(False)

    def _get_current_provider(self):
        idx = self._provider_combo.currentIndex()
        if idx < 0:
            return None, None
        pid, ptype = self._provider_list[idx]
        providers = CLOUD_PROVIDERS if ptype == "cloud" else LOCAL_PROVIDERS
        return next((p for p in providers if p["id"] == pid), None), ptype

    def _save(self):
        provider, ptype = self._get_current_provider()
        if not provider:
            QMessageBox.warning(self, "错误", "请选择模型供应商")
            return

        api_key = self._api_key_input.text().strip()
        model = self._model_combo.currentText().strip()

        os.makedirs(DATA_DIR, exist_ok=True)

        config = {
            "active_provider_id": provider["id"],
            "active_provider_type": ptype,
            "cloud_providers": {},
            "local_providers": {},
            "disabled_skills": [],
            "general": {"theme": "light", "auto_save": True, "max_tool_rounds": 8, "font_size": 14},
        }

        key = "cloud_providers" if ptype == "cloud" else "local_providers"
        config[key][provider["id"]] = {
            "name": provider["name"],
            "base_url": provider["base_url"],
            "model": model,
            "api_key": api_key,
        }

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        QMessageBox.information(self, "配置成功", f"已保存配置\n供应商: {provider['name']}\n模型: {model}")
        self.close()

    def _skip(self):
        """跳过配置，使用默认 Ollama"""
        os.makedirs(DATA_DIR, exist_ok=True)
        config = {
            "active_provider_id": "ollama",
            "active_provider_type": "local",
            "cloud_providers": {},
            "local_providers": {
                "ollama": {"name": "Ollama", "base_url": "http://localhost:11434/v1", "model": "qwen2.5:7b", "api_key": ""}
            },
            "disabled_skills": [],
            "general": {"theme": "light", "auto_save": True, "max_tool_rounds": 8, "font_size": 14},
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModelSetupWindow()
    window.show()
    app.exec_()

```
