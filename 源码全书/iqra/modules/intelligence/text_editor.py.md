# `iqra/modules/intelligence/text_editor.py`

> 路径：`iqra/modules/intelligence/text_editor.py` | 行数：30


---


```python
# -*- coding: utf-8 -*-
"""文本编辑器 - 组装入口。mixin 类均在同目录下。"""
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QTimer

from ._text_crypto import NoteTab, PasswordDialog, encrypt_text, decrypt_text, is_encrypted
from ._text_editor_ui_mixin import TextEditorUiMixin
from ._text_editor_tree_mixin import TextEditorTreeMixin
from ._text_editor_files_mixin import TextEditorFilesMixin
from ._text_editor_format_mixin import TextEditorFormatMixin


class TextEditorWidget(
    TextEditorUiMixin,
    TextEditorTreeMixin,
    TextEditorFilesMixin,
    TextEditorFormatMixin,
    QMainWindow,
):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝 文本编辑器")
        self.setMinimumSize(1100, 720)
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.timeout.connect(self._auto_save_all)
        self._auto_save_timer.start(60 * 1000)
        self._build_ui()
        self._load_tree()
        if self._tabs.count() == 0:
            self._new_tab()

```
