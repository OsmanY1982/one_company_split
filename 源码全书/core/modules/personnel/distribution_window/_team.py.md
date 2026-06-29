# `core/modules/personnel/distribution_window/_team.py`

> 路径：`core/modules/personnel/distribution_window/_team.py` | 行数：108


---


```python
"""
_TeamMixin — 团队管理 Tab 全部操作
"""
from PyQt5.QtWidgets import (
    QMessageBox, QTableWidgetItem, QLineEdit,
    QFormLayout, QDialog,
)

from core.ui_components import PrimaryButton, SecondaryButton, DangerButton
from core.light_tool_theme import LIGHT_TOOL_STYLE

from core.modules.personnel.distribution_service import (
    get_all_team_members, add_team_member, remove_team_member,
    export_team_csv,
)


class _TeamMixin:
    """团队管理 Tab 全部操作"""

    # ── 数据加载 ──
    def _load_team(self):
        rows = get_all_team_members()
        self.team_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.team_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.team_table.setItem(i, 1, QTableWidgetItem(str(r["user_name"])))
            self.team_table.setItem(i, 2, QTableWidgetItem(str(r["parent_name"])))
            self.team_table.setItem(i, 3, QTableWidgetItem(str(r["level"])))
            self.team_table.setItem(i, 4, QTableWidgetItem(str(r.get("created_at") or "")))
        self._update_stats()

    def _search_team(self):
        text = self.team_search.text().strip()
        if not text:
            self._load_team()
            return
        rows = [r for r in get_all_team_members()
                if text.lower() in str(r.get("user_name", "")).lower()
                or text.lower() in str(r.get("parent_name", "")).lower()]
        self.team_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.team_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.team_table.setItem(i, 1, QTableWidgetItem(str(r["user_name"])))
            self.team_table.setItem(i, 2, QTableWidgetItem(str(r["parent_name"])))
            self.team_table.setItem(i, 3, QTableWidgetItem(str(r["level"])))
            self.team_table.setItem(i, 4, QTableWidgetItem(str(r.get("created_at") or "")))

    # ── 添加成员对话框 ──
    def _show_add_team_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("添加团队成员")
        dlg.setMinimumWidth(380)
        dlg.setStyleSheet(LIGHT_TOOL_STYLE)
        layout = QFormLayout(dlg)
        layout.setSpacing(12)
        user_input = QLineEdit()
        user_input.setPlaceholderText("成员用户ID")
        layout.addRow("成员ID:", user_input)
        parent_input = QLineEdit()
        parent_input.setPlaceholderText("上级用户ID")
        layout.addRow("上级ID:", parent_input)
        btn = PrimaryButton("添加")

        def do_add():
            uid = user_input.text().strip()
            pid = parent_input.text().strip()
            if not uid or not pid:
                QMessageBox.warning(dlg, "提示", "成员ID和上级ID都不能为空")
                return
            try:
                uid_int = int(uid)
                pid_int = int(pid)
            except ValueError:
                QMessageBox.warning(dlg, "格式错误", "ID必须是整数")
                return
            result = add_team_member(user_id=uid_int, parent_id=pid_int)
            if result["ok"]:
                QMessageBox.information(dlg, "成功",
                    f"成员 {uid} 已添加到 {pid} 团队")
                self._load_team()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "失败", f"添加失败: {result.get('error', '未知错误')}")

        btn.clicked.connect(do_add)
        layout.addRow(btn)
        dlg.exec_()

    # ── 团队操作 ──
    def _remove_selected_member(self):
        row = self.team_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个成员")
            return
        member_id = int(self.team_table.item(row, 0).text())
        if QMessageBox.question(self, "确认", f"确定移除成员 #{member_id}？",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        result = remove_team_member(member_id)
        if result["ok"]:
            self._load_team()

    def _export_team(self):
        result = export_team_csv()
        if result["ok"]:
            QMessageBox.information(self, "导出成功",
                f"已导出 {result['count']} 条记录到:\n{result['filepath']}")

```
