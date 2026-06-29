# `core/modules/auth/model_config_panel/_dialog.py`

> 路径：`core/modules/auth/model_config_panel/_dialog.py` | 行数：70


---


```python
"""
模型配置弹窗 — 嵌入 ModelConfigPanel，用于 AIChatWindow / FloatingPlanet 的「引擎设置」按钮。
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal


class ModelConfigDialog(QWidget):
    """模型设置弹窗，嵌入 ModelConfigPanel。"""

    accepted = pyqtSignal()

    def __init__(self, parent=None, bridge=None):
        super().__init__(parent)
        self._bridge = bridge
        self.setWindowFlags(
            Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint
        )
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("引 擎 设 置")
        self.setMinimumSize(620, 580)
        self.setStyleSheet("""
            ModelConfigDialog {
                background: rgba(5, 10, 24, 248);
                border: 1px solid rgba(0, 180, 255, 60);
                border-radius: 16px;
            }
        """)

        from . import ModelConfigPanel  # 延迟导入，避免循环依赖

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._panel = ModelConfigPanel(self, standalone=False)
        self._panel.config_saved.connect(self._on_config_saved)
        layout.addWidget(self._panel)

    def closeEvent(self, event):
        """弹窗关闭时清理正在运行的模型拉取线程"""
        if hasattr(self._panel, '_model_fetcher') and self._panel._model_fetcher:
            try:
                self._panel._model_fetcher.quit()
                self._panel._model_fetcher.wait(2000)
            except Exception:
                pass
        super().closeEvent(event)

    def _on_config_saved(self, config: dict):
        """保存后自动切换引擎模型"""
        provider_id = config.get("active_provider_id", "")
        provider_type = config.get("active_provider_type", "")
        model = ""

        if provider_type == "cloud":
            prov = config.get("cloud_providers", {}).get(provider_id, {})
            model = prov.get("model", "")
        elif provider_type == "local":
            prov = config.get("local_providers", {}).get(provider_id, {})
            model = prov.get("model", "")
            if not model and prov.get("models"):
                model = prov["models"][0]

        if self._bridge and provider_id and model:
            try:
                self._bridge.switch_model(provider_id, model)
            except Exception as e:
                print(f"[ModelConfigDialog] 切换模型失败: {e}")

        self.accepted.emit()
        self.close()

```
