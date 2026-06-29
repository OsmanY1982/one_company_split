# `core/modules/auth/model_config_panel/_panel_preset.py`

> 路径：`core/modules/auth/model_config_panel/_panel_preset.py` | 行数：85


---


```python
"""
模型配置面板 — 预设模式面板 Mixin。
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit
from PyQt5.QtCore import Qt

from ._constants import PRESET_PROVIDERS, PROVIDER_MODELS, COMBO_STYLE, LABEL_STYLE, INPUT_STYLE


class _PanelPresetMixin:
    """Mixin: 预设供应商模式面板。"""

    def _build_preset_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        v = QVBoxLayout(panel)
        v.setSpacing(14)
        v.setContentsMargins(50, 10, 50, 10)

        lbl1 = QLabel("模型提供商")
        lbl1.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl1)

        self._preset_provider = QComboBox()
        self._preset_provider.setStyleSheet(COMBO_STYLE)
        self._preset_provider.setMinimumHeight(42)
        for p in PRESET_PROVIDERS:
            icon = "🏠" if p["local"] else "☁️"
            self._preset_provider.addItem(f"{icon}  {p['name']} — {p['desc']}", p["id"])
        self._preset_provider.currentIndexChanged.connect(self._on_preset_provider_changed)
        v.addWidget(self._preset_provider)

        lbl2 = QLabel("模型")
        lbl2.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl2)

        self._preset_model = QComboBox()
        self._preset_model.setStyleSheet(COMBO_STYLE)
        self._preset_model.setEditable(True)
        self._preset_model.setMinimumHeight(42)
        v.addWidget(self._preset_model)

        lbl3 = QLabel("API Key")
        lbl3.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl3)

        self._preset_key = QLineEdit()
        self._preset_key.setStyleSheet(INPUT_STYLE)
        self._preset_key.setEchoMode(QLineEdit.Password)
        self._preset_key.setPlaceholderText("输入 API Key（安全存储，不外传）")
        v.addWidget(self._preset_key)

        v.addStretch()
        self._on_preset_provider_changed()
        return panel

    def _on_preset_provider_changed(self):
        idx = self._preset_provider.currentIndex()
        if idx < 0:
            return
        pid = self._preset_provider.currentData()
        provider = next((p for p in PRESET_PROVIDERS if p["id"] == pid), None)
        if not provider:
            return

        # 用硬编码字典填充模型列表（即时显示，无需网络）
        self._preset_model.clear()
        hardcoded = PROVIDER_MODELS.get(provider["name"], [])
        if hardcoded:
            for m in hardcoded:
                self._preset_model.addItem(m, m)

        # 恢复已保存的 key 和 model
        cloud = self._existing.get("cloud_providers", {})
        if pid in cloud:
            existing_key = cloud[pid].get("api_key", "")
            existing_model = cloud[pid].get("model", "")
            if existing_model:
                idx_m = self._preset_model.findText(existing_model)
                if idx_m >= 0:
                    self._preset_model.setCurrentIndex(idx_m)
                else:
                    self._preset_model.setEditText(existing_model)
            if existing_key:
                self._preset_key.setText(existing_key)

```
