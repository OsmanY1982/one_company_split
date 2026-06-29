# `core/modules/dashboard/dashboard_window/__init__.py`

> 路径：`core/modules/dashboard/dashboard_window/__init__.py` | 行数：39


---


```python
"""
舰桥主控面板 — DashboardWindow（模块化重组）
通过多重继承组合 UI、导航、账号工具、渲染能力。
"""

import sys as _sys, os as _os
_dir = _os.path.dirname(_os.path.abspath(__file__))
for _ in range(10):
    if _os.path.exists(_os.path.join(_dir, 'dark_theme.py')):
        _parent = _os.path.dirname(_dir)
        if _parent not in _sys.path:
            _sys.path.insert(0, _parent)
        break
    _dir = _os.path.dirname(_dir)

from PyQt5.QtWidgets import QMainWindow

from ._ui import _UIMixin
from ._module_navigator import _ModuleNavigatorMixin
from ._account_tools import _AccountToolsMixin
from ._renderer import _RendererMixin


class DashboardWindow(
    QMainWindow,
    _UIMixin,
    _ModuleNavigatorMixin,
    _AccountToolsMixin,
    _RendererMixin,
):
    """舰桥 — AI Agent 驾驶舱"""

    def __init__(self, config=None, role: str = "admin",
                 membership_info: dict = None,
                 iqra_engine=None):
        QMainWindow.__init__(self)
        _UIMixin.__init__(self, config=config, role=role,
                          membership_info=membership_info,
                          iqra_engine=iqra_engine)

```
