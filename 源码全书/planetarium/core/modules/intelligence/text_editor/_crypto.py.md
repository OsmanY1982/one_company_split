# `planetarium/core/modules/intelligence/text_editor/_crypto.py`

> 路径：`planetarium/core/modules/intelligence/text_editor/_crypto.py` | 行数：37


---


```python
# -*- coding: utf-8 -*-
from core.paths import DATA_DIR
import os, hashlib, base64

NOTES_DIR  = os.path.join(DATA_DIR, "notes")
INDEX_FILE = os.path.join(DATA_DIR, "notes/index.json")
ENC_MAGIC  = b"OPC_ENC_V1:"   # 加密文件头标识


def _derive_key(password: str) -> bytes:
    salt = b"OPC_TextEditor_Salt_2026"
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)


def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encrypt_text(text: str, password: str) -> bytes:
    key  = _derive_key(password)
    enc  = _xor(text.encode('utf-8'), key)
    return ENC_MAGIC + base64.b64encode(enc)


def decrypt_text(data: bytes, password: str) -> str:
    if not data.startswith(ENC_MAGIC):
        raise ValueError("不是加密文件")
    enc  = base64.b64decode(data[len(ENC_MAGIC):])
    key  = _derive_key(password)
    return _xor(enc, key).decode('utf-8')


def is_encrypted(filepath: str) -> bool:
    try:
        with open(filepath, 'rb') as f:
            return f.read(len(ENC_MAGIC)) == ENC_MAGIC
    except Exception: return False

```
