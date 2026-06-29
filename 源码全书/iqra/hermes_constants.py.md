# `iqra/hermes_constants.py`

> 路径：`iqra/hermes_constants.py` | 行数：12


---


```python
# -*- coding: utf-8 -*-
"""Hermes home directory constants — generated stub."""
import os
from pathlib import Path


def get_hermes_home() -> Path:
    """Return the Hermes home directory path."""
    return Path.home() / ".hermes"


HERMES_HOME = get_hermes_home()

```
