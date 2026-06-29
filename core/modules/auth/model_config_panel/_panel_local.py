"""
模型配置面板 — 本地推理模式面板 Mixin。
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox
from PyQt5.QtCore import Qt

from ._constants import LOCAL_SERVICES, COMBO_STYLE, LABEL_STYLE, INPUT_STYLE, BTN_SECONDARY, _populate_model_combo
from ._workers import _ManualModelFetcher, _OllamaModelFetcher


class _PanelLocalMixin:
    """Mixin: 本地推理服务面板。"""

    def _build_local_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        v = QVBoxLayout(panel)
        v.setSpacing(14)
        v.setContentsMargins(50, 10, 50, 10)

        lbl1 = QLabel("本地推理服务")
        lbl1.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl1)

        self._local_service = QComboBox()
        self._local_service.setStyleSheet(COMBO_STYLE)
        self._local_service.setMinimumHeight(42)
        for s in LOCAL_SERVICES:
            self._local_service.addItem(f"🖥  {s['name']} — {s['desc']}", s["id"])
        self._local_service.currentIndexChanged.connect(self._on_local_service_changed)
        v.addWidget(self._local_service)

        lbl2 = QLabel("Base URL")
        lbl2.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl2)

        self._local_url = QLineEdit()
        self._local_url.setStyleSheet(INPUT_STYLE)
        self._local_url.setPlaceholderText("自动填充")
        v.addWidget(self._local_url)

        lbl3 = QLabel("模型名称")
        lbl3.setStyleSheet(LABEL_STYLE)
        v.addWidget(lbl3)

        model_row = QHBoxLayout()
        model_row.setSpacing(8)

        self._local_model = QComboBox()
        self._local_model.setStyleSheet(COMBO_STYLE)
        self._local_model.setEditable(True)
        self._local_model.setMinimumHeight(42)
        model_row.addWidget(self._local_model, stretch=1)

        self._refresh_btn = QPushButton("刷新模型")
        self._refresh_btn.setStyleSheet(BTN_SECONDARY)
        self._refresh_btn.setFixedWidth(100)
        self._refresh_btn.setFixedHeight(42)
        self._refresh_btn.setCursor(Qt.PointingHandCursor)
        self._refresh_btn.clicked.connect(self._refresh_local_models)
        model_row.addWidget(self._refresh_btn)

        v.addLayout(model_row)
        v.addStretch()

        self._on_local_service_changed()

        local = self._existing.get("local_providers", {})
        if local:
            first_key = list(local.keys())[0] if local else None
            if first_key:
                idx = self._local_service.findData(first_key)
                if idx >= 0:
                    self._local_service.setCurrentIndex(idx)
                cfg = local[first_key]
                if cfg.get("base_url"):
                    self._local_url.setText(cfg["base_url"])
                if cfg.get("model"):
                    midx = self._local_model.findText(cfg["model"])
                    if midx >= 0:
                        self._local_model.setCurrentIndex(midx)
                    else:
                        self._local_model.setEditText(cfg["model"])

        return panel

    def _on_local_service_changed(self):
        sid = self._local_service.currentData()
        svc = next((s for s in LOCAL_SERVICES if s["id"] == sid), None)
        if not svc:
            return
        self._local_url.setText(svc["base_url"])

        self._local_model.clear()
        hardcoded = svc.get("models", [])
        if hardcoded:
            for m in hardcoded:
                self._local_model.addItem(m, m)

    def _refresh_local_models(self):
        """手动刷新：从本地服务端点重新拉取模型列表。"""
        url = self._local_url.text().strip()
        sid = self._local_service.currentData()
        saved_model = self._local_model.currentText().strip()
        self._refresh_btn.setEnabled(False)
        self._refresh_btn.setText("获取中...")

        combo = self._local_model
        loading_label = "⏳ 刷新模型列表中..."
        old_idx = combo.findText(loading_label)
        if old_idx >= 0:
            combo.removeItem(old_idx)
        combo.insertItem(0, loading_label, "")
        combo.setCurrentIndex(0)

        if sid == "ollama" or "11434" in url:
            self._model_fetcher = _OllamaModelFetcher(url, timeout=15)
        else:
            self._model_fetcher = _ManualModelFetcher(url, "", timeout=15)

        def on_finished(models, error):
            try:
                lidx = combo.findText(loading_label)
                if lidx >= 0:
                    combo.removeItem(lidx)
                if error:
                    print(f"[ModelConfigPanel] 获取本地模型列表失败: {error}")
                    if saved_model and combo.findText(saved_model) < 0:
                        combo.setEditText(saved_model)
                elif models:
                    _populate_model_combo(combo, models, saved_model)
                self._refresh_btn.setEnabled(True)
                self._refresh_btn.setText("刷新模型")
            except RuntimeError:
                pass
            finally:
                self._model_fetcher = None

        self._model_fetcher.finished.connect(on_finished)
        self._model_fetcher.start()
