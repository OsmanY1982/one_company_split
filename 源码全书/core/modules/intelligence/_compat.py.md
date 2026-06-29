# `core/modules/intelligence/_compat.py`

> 路径：`core/modules/intelligence/_compat.py` | 行数：35


---


```python
"""
星空版 → 宇宙版 兼容适配层

提供宇宙版 core/ 中不存在但迁移模块需要的函数/常量：
- get_conn(db_name) → 桥接到 core.database.get_conn
- DATA_DIR → 兼容星空版 core.paths.DATA_DIR
"""

import os
from core.database import get_conn as _core_get_conn, close_conn as _core_close_conn
from core.paths import DATA_DIR

# ──────────── 数据库连接（桥接到 core.database） ────────────

def get_conn(db_name: str = "finance.db"):
    """获取数据库连接（桥接到 core.database 连接池）"""
    return _core_get_conn(db_name)

def close_conn(db_name: str):
    """关闭当前线程的某个数据库连接"""
    _core_close_conn(db_name)

# 保留 get_cursor 兼容（core.database.transaction 是推荐的替代方案）
from contextlib import contextmanager

@contextmanager
def get_cursor(db_name: str = "finance.db"):
    """上下文管理器：自动 commit/rollback"""
    conn = get_conn(db_name)
    try:
        yield conn.cursor()
        conn.commit()
    except Exception:
        conn.rollback()
        raise

```
