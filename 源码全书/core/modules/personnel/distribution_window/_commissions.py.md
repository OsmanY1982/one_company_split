# `core/modules/personnel/distribution_window/_commissions.py`

> 路径：`core/modules/personnel/distribution_window/_commissions.py` | 行数：152


---


```python
"""
_CommissionsMixin — 佣金记录 Tab 全部操作
"""
from PyQt5.QtWidgets import (
    QMessageBox, QTableWidgetItem, QLineEdit,
    QFormLayout, QDialog, QDoubleSpinBox, QComboBox,
)
from PyQt5.QtGui import QColor

from core.ui_components import PrimaryButton, SecondaryButton, DangerButton
from core.light_tool_theme import LIGHT_TOOL_STYLE

from core.modules.personnel.distribution_service import (
    search_commissions, add_commission, update_commission_status,
    export_commissions_csv,
)


class _CommissionsMixin:
    """佣金记录 Tab 全部操作"""

    # ── 搜索 ──
    def _search_commissions(self, _=None):
        user_text = self.comm_user_search.text().strip()
        uid = int(user_text) if user_text else None
        date_from = self.comm_date_from.text().strip() or None
        date_to = self.comm_date_to.text().strip() or None
        status = self.comm_filter.currentText()
        status_filter = None if (not status or status == "全部") else status
        rows = search_commissions(
            user_id=uid, date_from=date_from, date_to=date_to,
            status=status_filter
        )
        self.comm_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.comm_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.comm_table.setItem(i, 1, QTableWidgetItem(str(r["user_name"])))
            self.comm_table.setItem(i, 2, QTableWidgetItem(str(r.get("from_user_name") or "")))
            self.comm_table.setItem(i, 3, QTableWidgetItem(f"{r['amount']:.2f}"))
            self.comm_table.setItem(i, 4, QTableWidgetItem(str(r["type"])))
            status_item = QTableWidgetItem(str(r["status"]))
            if r["status"] == "approved":
                status_item.setForeground(QColor(136, 255, 187))
            elif r["status"] == "rejected":
                status_item.setForeground(QColor(255, 170, 170))
            elif r["status"] == "paid":
                status_item.setForeground(QColor(170, 200, 255))
            self.comm_table.setItem(i, 5, status_item)
            self.comm_table.setItem(i, 6, QTableWidgetItem(str(r.get("created_at") or "")))
        self._update_stats()

    def _clear_comm_search(self):
        self.comm_user_search.clear()
        self.comm_date_from.clear()
        self.comm_date_to.clear()
        self.comm_filter.setCurrentText("全部")
        self._search_commissions()

    # ── 发放佣金对话框 ──
    def _show_add_commission_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("发放佣金")
        dlg.setMinimumWidth(420)
        dlg.setStyleSheet(LIGHT_TOOL_STYLE)
        layout = QFormLayout(dlg)
        layout.setSpacing(12)
        user_input = QLineEdit()
        user_input.setPlaceholderText("受益用户ID")
        layout.addRow("用户ID:", user_input)
        from_input = QLineEdit()
        from_input.setPlaceholderText("来源用户ID（可选）")
        layout.addRow("来源用户:", from_input)
        amt = QDoubleSpinBox()
        amt.setRange(0.01, 999999)
        amt.setValue(10)
        amt.setDecimals(2)
        layout.addRow("金额:", amt)
        type_combo = QComboBox()
        type_combo.addItems(["direct", "indirect", "team", "referral"])
        layout.addRow("类型:", type_combo)
        desc = QLineEdit()
        desc.setText("后台发放")
        layout.addRow("备注:", desc)
        btn = PrimaryButton("确认发放")

        def do_add():
            uid = user_input.text().strip()
            if not uid:
                QMessageBox.warning(dlg, "提示", "用户ID不能为空")
                return
            try:
                uid_int = int(uid)
            except ValueError:
                QMessageBox.warning(dlg, "格式错误", "用户ID必须是整数")
                return
            from_uid = from_input.text().strip()
            from_uid_int = int(from_uid) if from_uid else None
            result = add_commission(
                user_id=uid_int,
                amount=amt.value(),
                from_user_id=from_uid_int,
                comm_type=type_combo.currentText(),
                description=desc.text()
            )
            if result["ok"]:
                warn = ""
                if result.get("wallet_error"):
                    warn = f"\n⚠️ 钱包同步失败: {result['wallet_error']}"
                QMessageBox.information(dlg, "成功",
                    f"佣金 {amt.value():.2f} 已发放给 {uid}{warn}")
                self._search_commissions()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "失败", f"发放失败: {result.get('error', '未知错误')}")

        btn.clicked.connect(do_add)
        layout.addRow(btn)
        dlg.exec_()

    # ── 佣金操作 ──
    def _update_comm_status(self, status):
        row = self.comm_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一条佣金记录")
            return
        comm_id = int(self.comm_table.item(row, 0).text())
        result = update_commission_status(comm_id, status)
        if result["ok"]:
            self._search_commissions()
            QMessageBox.information(self, "成功", f"佣金状态已更新为: {status}")
        else:
            QMessageBox.warning(self, "失败", result.get("error", "操作失败"))

    def _delete_commission(self):
        row = self.comm_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一条佣金记录")
            return
        comm_id = int(self.comm_table.item(row, 0).text())
        if QMessageBox.question(self, "确认", f"确定删除佣金记录 #{comm_id}？",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        from core.modules.personnel import distribution_service
        result = distribution_service.delete_commission(comm_id)
        if result["ok"]:
            self._search_commissions()

    def _export_commissions(self):
        result = export_commissions_csv()
        if result["ok"]:
            QMessageBox.information(self, "导出成功",
                f"已导出 {result['count']} 条记录到:\n{result['filepath']}")

```
