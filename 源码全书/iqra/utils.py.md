# `iqra/utils.py`

> 路径：`iqra/utils.py` | 行数：26


---


```python
# -*- coding: utf-8 -*-
"""iqra utils — lightweight utilities."""
import os
import tempfile
import shutil
from pathlib import Path
from typing import Union


def atomic_replace(target: Union[str, Path], content: Union[str, bytes]) -> None:
    """Write content to a temp file and atomically replace target."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    
    mode = "wb" if isinstance(content, bytes) else "w"
    encoding = None if isinstance(content, bytes) else "utf-8"
    
    fd, tmp_path = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, mode, encoding=encoding) as f:
            f.write(content)
        os.replace(tmp_path, str(target))
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

```
