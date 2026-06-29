# `core/paths.py`

> 路径：`core/paths.py` | 行数：29


---


```python
# -*- coding: utf-8 -*-
"""
统一路径管理模块（宇宙版·简化）
所有项目路径都从这里获取，避免硬编码
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
LOG_DIR = os.path.join(BASE_DIR, "log")

for d in [DATA_DIR, CONFIG_DIR, LOG_DIR]:
    os.makedirs(d, exist_ok=True)


def get_data_path(filename: str) -> str:
    """获取数据文件路径"""
    return os.path.join(DATA_DIR, filename)


def get_config_path(filename: str) -> str:
    """获取配置文件路径"""
    return os.path.join(CONFIG_DIR, filename)


def get_log_path(filename: str) -> str:
    """获取日志文件路径"""
    return os.path.join(LOG_DIR, filename)

```
