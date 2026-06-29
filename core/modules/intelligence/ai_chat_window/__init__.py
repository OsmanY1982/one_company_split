"""AI助手 · NEURAL v5 — 统一 AgentBridge 对话窗口（模块化 Mixin 架构）"""

import sys as _sys, os as _os
_dir = _os.path.dirname(_os.path.abspath(__file__))
for _ in range(10):
    if _os.path.exists(_os.path.join(_dir, 'dark_theme.py')):
        _parent = _os.path.dirname(_dir)
        if _parent not in _sys.path:
            _sys.path.insert(0, _parent)
        break
    _dir = _os.path.dirname(_dir)

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
