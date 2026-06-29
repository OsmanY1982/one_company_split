# `planetarium/core/modules/intelligence/enhanced/enhanced_tools.py`

> 路径：`planetarium/core/modules/intelligence/enhanced/enhanced_tools.py` | 行数：23


---


```python
# -*- coding: utf-8 -*-
"""
增强 AI 工具集 — 组装入口

通过多重继承组合所有功能 Mixin，保持原有 import 路径兼容。
"""

from ._enhanced_base import EnhancedAIAssistantBase, _safe_path, _DATA_DIR, _PROJECT_ROOT
from ._enhanced_files_mixin import EnhancedFilesMixin
from ._enhanced_web_mixin import EnhancedWebMixin
from ._enhanced_system_mixin import EnhancedSystemMixin
from ._enhanced_storage_mixin import EnhancedStorageMixin


class EnhancedAIAssistant(
    EnhancedAIAssistantBase,
    EnhancedFilesMixin,
    EnhancedWebMixin,
    EnhancedSystemMixin,
    EnhancedStorageMixin,
):
    """增强 AI 工具助手 — 纯本地、零联网依赖"""
    pass

```
