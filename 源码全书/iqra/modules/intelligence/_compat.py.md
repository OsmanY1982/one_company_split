# `iqra/modules/intelligence/_compat.py`

> 路径：`iqra/modules/intelligence/_compat.py` | 行数：55


---


```python
"""
星空版 → 宇宙版 兼容适配层

提供宇宙版 core/ 中不存在但迁移模块需要的函数/常量：
- get_conn(db_name) → 兼容星空版 core.database.get_conn
- DATA_DIR → 兼容星空版 core.paths.DATA_DIR
"""

import os
import sqlite3
import threading
from contextlib import contextmanager

# ──────────── 路径常量 ────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ──────────── 数据库连接（兼容星空版 core.database.get_conn） ────────────
_connections: dict[str, sqlite3.Connection] = {}
_lock = threading.Lock()


def get_conn(db_name: str = "finance.db") -> sqlite3.Connection:
    """获取数据库连接（线程本地，自动复用），兼容星空版接口"""
    tid = threading.get_ident()
    key = f"{tid}:{db_name}"

    with _lock:
        if key in _connections:
            try:
                _connections[key].execute("SELECT 1")
            except sqlite3.ProgrammingError:
                del _connections[key]

    if key not in _connections:
        db_path = os.path.join(DATA_DIR, db_name)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _connections[key] = conn

    return _connections[key]


@contextmanager
def get_cursor(db_name: str = "finance.db"):
    """上下文管理器：自动 commit/close"""
    conn = get_conn(db_name)
    try:
        yield conn.cursor()
        conn.commit()
    except Exception:
        conn.rollback()
        raise

```
