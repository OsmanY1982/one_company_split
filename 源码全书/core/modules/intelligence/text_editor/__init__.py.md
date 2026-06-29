# `core/modules/intelligence/text_editor/__init__.py`

> 路径：`core/modules/intelligence/text_editor/__init__.py` | 行数：12


---


```python
from ._crypto import (
    NOTES_DIR, INDEX_FILE, ENC_MAGIC, _derive_key, _xor,
    encrypt_text, decrypt_text, is_encrypted,
)
from ._note_tab import PasswordDialog, NoteTab
from ._core import TextEditorWidget

__all__ = [
    "NOTES_DIR", "INDEX_FILE", "ENC_MAGIC",
    "encrypt_text", "decrypt_text", "is_encrypted",
    "PasswordDialog", "NoteTab", "TextEditorWidget",
]

```
