# `core/modules/intelligence/iqra_floating_planet/_exit_mixin.py`

> 路径：`core/modules/intelligence/iqra_floating_planet/_exit_mixin.py` | 行数：35


---


```python
# -*- coding: utf-8 -*-
"""悬浮球退出 Mixin — _on_exit / closeEvent / _do_cleanup"""
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt


class FloatingPlanetExitMixin:
    """退出逻辑：确认对话框 + 清理 + closeEvent 拦截"""

    def _on_exit(self):
        reply = QMessageBox.question(
            self, "退出悬浮球",
            "确定要退出悬浮球吗？\n可从智能中心重新启动。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._do_cleanup()
            self.close()

    def _do_cleanup(self):
        if self._cleanup_done:
            return
        self._cleanup_done = True
        if self._daemon_cleanup:
            self._daemon_cleanup()

    def closeEvent(self, event):
        if hasattr(self, '_keep_on_top_timer') and self._keep_on_top_timer.isActive():
            self._keep_on_top_timer.stop()
        if not event.spontaneous():
            self._do_cleanup()
        else:
            event.ignore()
            return
        super().closeEvent(event)

```
