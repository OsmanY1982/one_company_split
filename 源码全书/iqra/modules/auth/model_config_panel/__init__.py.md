# `iqra/modules/auth/model_config_panel/__init__.py`

> 路径：`iqra/modules/auth/model_config_panel/__init__.py` | 行数：47


---


```python
"""
模型配置面板 — 可复用于登录后模型设置、智能中心AI对话、悬浮球对话框。
三种模式：预设云端模型 / 自定义端点 / 本地推理。
与 iqra 共享配置格式（iqra_config.json）。
"""
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

from ._constants import (
    PRESET_PROVIDERS, PROVIDER_MODELS, LOCAL_SERVICES,
    INPUT_STYLE, COMBO_STYLE, LABEL_STYLE, BTN_PRIMARY, BTN_SECONDARY,
    _load_iqra_config, _save_iqra_config, _filter_usable_models, _populate_model_combo,
)
from ._workers import _ManualModelFetcher, _OllamaModelFetcher
from ._dialog import ModelConfigDialog
from ._panel_ui import _PanelUIMixin
from ._panel_preset import _PanelPresetMixin
from ._panel_custom import _PanelCustomMixin
from ._panel_local import _PanelLocalMixin
from ._panel_config import _PanelConfigMixin


class ModelConfigPanel(
    QWidget,
    _PanelUIMixin,
    _PanelPresetMixin,
    _PanelCustomMixin,
    _PanelLocalMixin,
    _PanelConfigMixin,
):
    """
    可复用模型配置面板，用于:
      - 登录后模型设置（ModelSetupWindow 嵌入，standalone=True）
      - 智能中心 AI 对话窗口（AIChatWindow 弹窗，standalone=False）
      - 悬浮球对话框（FloatingPlanet 弹窗，standalone=False）

    standalone=True:  显示"点火"/"跳过配置"按钮，保存后发射 config_saved
    standalone=False: 显示"保存并切换"按钮，保存后发射 config_saved
    """

    config_saved = pyqtSignal(dict)

    def __init__(self, parent=None, standalone: bool = False):
        QWidget.__init__(self, parent)  # 显式调用 QWidget.__init__，不走 MRO super()
        self._standalone = standalone
        self._existing = _load_iqra_config()
        self._build_ui()

```
