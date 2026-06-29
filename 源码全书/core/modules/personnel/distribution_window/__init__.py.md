# `core/modules/personnel/distribution_window/__init__.py`

> 路径：`core/modules/personnel/distribution_window/__init__.py` | 行数：49


---


```python
"""
DistributionWindow — 分销管理主窗口
通过 Mixin 多重继承组合 _UIMixin / _DashboardMixin / _LinksMixin / _CommissionsMixin / _TeamMixin
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

from ._stat_card import GoldStatCard
from ._ui import _UIMixin
from ._dashboard import _DashboardMixin
from ._links import _LinksMixin
from ._commissions import _CommissionsMixin
from ._team import _TeamMixin


class DistributionWindow(
    QMainWindow,
    _UIMixin,
    _DashboardMixin,
    _LinksMixin,
    _CommissionsMixin,
    _TeamMixin,
):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        _UIMixin.__init__(self, parent)

    # ═══════ 导航 ═══════
    def _go_back(self):
        self.close()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = DistributionWindow()
    w.show()
    sys.exit(app.exec_())

```
