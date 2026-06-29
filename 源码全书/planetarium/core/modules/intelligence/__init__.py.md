# `planetarium/core/modules/intelligence/__init__.py`

> 路径：`planetarium/core/modules/intelligence/__init__.py` | 行数：5


---


```python
# 智能中心模块
try:
    from core.modules.intelligence.intelligence_window import IntelligenceWindow
except ImportError:
    IntelligenceWindow = None
```
