# `core/modules/dashboard/dashboard_window/_module_navigator.py`

> 路径：`core/modules/dashboard/dashboard_window/_module_navigator.py` | 行数：80


---


```python
"""
模块导航 — _ModuleNavigatorMixin
包含 _open_module、_open_upgrade、_open_activation、_open_update_check
"""
import traceback


class _ModuleNavigatorMixin:
    """模块导航：打开各子模块窗口"""

    def _open_module(self, module_id: str):
        """打开子模块窗口"""
        from ._module_window import _ModuleWindow

        planet = next((p for p in self._planets if p["id"] == module_id), None)
        if not planet:
            return

        # 船员模式权限检查
        if self._role == "member":
            if module_id in ("personnel", "system"):
                return

        if module_id in self._modules_open:
            try:
                self._modules_open[module_id].close()
            except Exception:
                traceback.print_exc()

        if module_id == "business":
            from core.modules.business.business_window import BusinessWindow
            win = BusinessWindow(self)
        elif module_id == "personnel":
            from core.modules.personnel.personnel_window import PersonnelWindow
            win = PersonnelWindow(self)
        elif module_id == "intelligence":
            from core.modules.intelligence.intelligence_window import IntelligenceWindow
            win = IntelligenceWindow(self, role=self._role, iqra_engine=self._iqra)
        elif module_id == "data":
            from core.modules.data_center.data_window import DataWindow
            win = DataWindow(self)
        elif module_id == "system":
            from core.modules.system.system_hub_window import SystemHubWindow
            win = SystemHubWindow(self, role=self._role)
        elif module_id == "account":
            self._show_account_tools()
            return
        elif module_id == "admin":
            from core.modules.admin.admin_window import AdminWindow
            win = AdminWindow(self)
        else:
            win = _ModuleWindow(planet, self)

        self._modules_open[module_id] = win
        win.show()

    def _open_upgrade(self):
        """船员点击升级会员按钮"""
        from core.modules.auth.upgrade_window import UpgradeWindow
        ms = self._membership_info
        dlg = UpgradeWindow(
            username=self._membership_info.get("username", ""),
            parent=self,
            role=self._role,
            membership=ms.get("membership", "trial"),
            expire_at=ms.get("expire_at"),
        )
        dlg.exec_()

    def _open_activation(self):
        """激活许可证"""
        from core.modules.account.account_activation import AccountActivationWindow
        dlg = AccountActivationWindow(self)
        dlg.exec_()

    def _open_update_check(self):
        """检查更新"""
        from core.modules.account.account_update import AccountUpdateDialog
        dlg = AccountUpdateDialog(self)
        dlg.exec_()

```
