# `modules/admin/strategy_dao.py`

> 路径：`modules/admin/strategy_dao.py` | 行数：32


---


```python
"""
简单的策略 DAO
"""
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                         "one_company", "strategy.json")
os.makedirs(os.path.dirname(DATA_DIR), exist_ok=True)


def load_strategies():
    if not os.path.exists(DATA_DIR):
        return []
    try:
        with open(DATA_DIR, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载策略失败: {e}")
        return []


def save_strategies(items):
    try:
        with open(DATA_DIR, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存策略失败: {e}")

```
