# `core/sync_decorator.py`

> 路径：`core/sync_decorator.py` | 行数：53


---


```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步装饰器 - 自动同步到云端
使用方法：在业务函数上添加 @auto_sync("表名")
"""

import functools
import logging
from core.simple_sync import auto_sync_after_change

logger = logging.getLogger(__name__)


def auto_sync(table_name):
    """装饰器：数据变更后自动同步到云端"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 执行业务逻辑
            result = func(*args, **kwargs)
            
            # 业务成功后才同步
            if result is not False and result is not None:
                try:
                    logger.info(f"[{table_name}] 数据变更，自动同步...")
                    auto_sync_after_change(table_name)
                except Exception as e:
                    logger.error(f"自动同步失败: {e}")
            
            return result
        return wrapper
    return decorator


def sync_on_login(func):
    """装饰器：登录后自动从云端同步"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 执行业务逻辑
        result = func(*args, **kwargs)
        
        # 登录成功后才同步
        if result is not False and result is not None:
            try:
                from core.simple_sync import auto_sync_on_login
                logger.info("登录成功，自动同步数据...")
                auto_sync_on_login()
            except Exception as e:
                logger.error(f"登录同步失败: {e}")
        
        return result
    return wrapper

```
