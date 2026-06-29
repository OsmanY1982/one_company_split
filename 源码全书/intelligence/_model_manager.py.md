# `intelligence/_model_manager.py`

> 路径：`intelligence/_model_manager.py` | 行数：9


---


```python
# -*- coding: utf-8 -*-
"""Shim: re-export OllamaManager / DownloadModelDialog / DownloadWorker
原 _model_manager.py（725行）已拆分为 _model_manager_ollama.py + _model_manager_download.py
所有外部 import 路径不变，保持兼容。
"""
from core.modules.intelligence._model_manager_ollama import OllamaManager
from core.modules.intelligence._model_manager_download import DownloadModelDialog, DownloadWorker

__all__ = ["OllamaManager", "DownloadModelDialog", "DownloadWorker"]

```
