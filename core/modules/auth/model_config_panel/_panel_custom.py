"""
模型配置面板 — 自定义端点模式面板 Mixin。
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox
from PyQt5.QtCore import Qt

from ._constants import COMBO_STYLE, LABEL_STYLE, INPUT_STYLE, _populate_model_combo
from ._workers import _ManualModelFetcher


class _PanelCustomMixin:
    """Mixin: 自定义 OpenAI 兼容端点面板。"""

    def _build_custom_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        v = QVBoxLayout(panel)
        v.setSpacing(14)
        v.setContentsMargins(50, 10, 50, 10)

        lines = [
            ("API Base URL", "custom_url", "https://api.example.com/v1", False),
            ("API Key", "custom_key", "sk-...", True),
        ]
        self._custom_inputs = {}
        for label_text, attr, placeholder, is_pass in lines:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(LABEL_STYLE)
            v.addWidget(lbl)

            le = QLineEdit()
            le.setStyleSheet(INPUT_STYLE)
            le.setPlaceholderText(placeholder)
            if is_pass:
                le.setEchoMode(QLineEdit.Password)
            v.addWidget(le)
            self._custom_inputs[attr] = le

        self._custom_inputs["custom_url"].editingFinished.connect(self._on_custom_url_changed)

        model_label = QLabel("模型名称 (Model Name)")
        model_label.setStyleSheet(LABEL_STYLE)
        v.addWidget(model_label)

        model_row = QHBoxLayout()
        model_row.setSpacing(8)

        self._custom_model_combo = QComboBox()
        self._custom_model_combo.setStyleSheet(COMBO_STYLE)
        self._custom_model_combo.setEditable(True)
        self._custom_model_combo.setMinimumHeight(42)
        self._custom_model_combo.setPlaceholderText("输入模型名或点击获取模型")
        model_row.addWidget(self._custom_model_combo, 1)

        fetch_btn = QPushButton("获取模型")
        fetch_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0, 160, 240, 25);
                color: #66bbff;
                border: 1px solid rgba(0, 160, 240, 50);
                border-radius: 18px;
                padding: 10px 18px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(0, 180, 255, 40);
                border-color: rgba(0, 200, 255, 140);
            }
            QPushButton:disabled {
                color: rgba(102, 187, 255, 40);
                border-color: rgba(0, 160, 240, 20);
            }
        """)
        fetch_btn.clicked.connect(self._on_fetch_custom_models)
        model_row.addWidget(fetch_btn)
        v.addLayout(model_row)

        self._custom_inputs["custom_model"] = self._custom_model_combo

        v.addStretch()

        existing_custom = self._existing.get("cloud_providers", {}).get("custom", {})
        if existing_custom:
            self._custom_inputs["custom_url"].setText(existing_custom.get("base_url", ""))
            self._custom_inputs["custom_key"].setText(existing_custom.get("api_key", ""))
            existing_model = existing_custom.get("model", "")
            if existing_model:
                idx = self._custom_model_combo.findText(existing_model)
                if idx >= 0:
                    self._custom_model_combo.setCurrentIndex(idx)
                else:
                    self._custom_model_combo.setEditText(existing_model)

        return panel

    def _on_custom_url_changed(self):
        """自定义端点 URL 变更后记录，不自动拉取模型列表（由用户手动点击"获取模型"触发）。"""
        pass

    def _on_fetch_custom_models(self):
        """手动点击"获取模型"按钮时拉取模型列表。"""
        url = self._custom_inputs["custom_url"].text().strip()
        key = self._custom_inputs["custom_key"].text().strip()

        if not url:
            QMessageBox.warning(self, "缺少URL", "请先填写 API Base URL")
            return

        btn = self.sender()
        if btn:
            btn.setEnabled(False)
            btn.setText("获取中...")

        saved_model = self._custom_inputs["custom_model"].currentText().strip()
        combo = self._custom_model_combo

        loading_label = "⏳ 刷新模型列表中..."
        old_idx = combo.findText(loading_label)
        if old_idx >= 0:
            combo.removeItem(old_idx)
        combo.insertItem(0, loading_label, "")
        combo.setCurrentIndex(0)

        self._model_fetcher = _ManualModelFetcher(url, key, timeout=15)

        def on_finished(models, error):
            try:
                lidx = combo.findText(loading_label)
                if lidx >= 0:
                    combo.removeItem(lidx)
                if error:
                    print(f"[ModelConfigPanel] 获取模型列表失败: {error}")
                    if saved_model and combo.findText(saved_model) < 0:
                        combo.setEditText(saved_model)
                elif models:
                    _populate_model_combo(combo, models, saved_model)
                if btn:
                    btn.setEnabled(True)
                    btn.setText("获取模型")
            except RuntimeError:
                pass
            finally:
                self._model_fetcher = None

        self._model_fetcher.finished.connect(on_finished)
        self._model_fetcher.start()
