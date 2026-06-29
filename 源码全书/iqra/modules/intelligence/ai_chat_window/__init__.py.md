# `iqra/modules/intelligence/ai_chat_window/__init__.py`

> 路径：`iqra/modules/intelligence/ai_chat_window/__init__.py` | 行数：26


---


```python
"""AI助手 · NEURAL v5 — 统一 AgentBridge 对话窗口（模块化 Mixin 架构）"""
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget

from ._ui import _UIMixin
from ._chat_stream import _ChatStreamMixin
from ._voice import _VoiceMixin
from ._model_selector import _ModelSelectorMixin
from ._file_upload import _FileUploadMixin
from ._session import _SessionMixin
from ._misc import _MiscMixin


class AIChatWindow(
    _UIMixin,
    _ChatStreamMixin,
    _VoiceMixin,
    _ModelSelectorMixin,
    _FileUploadMixin,
    _SessionMixin,
    _MiscMixin,
    QWidget,
):
    """AI助手 · NEURAL v5 — 统一 AgentBridge，顶部嵌入紧凑模型选择器"""

    chat_close_requested = pyqtSignal()

```
