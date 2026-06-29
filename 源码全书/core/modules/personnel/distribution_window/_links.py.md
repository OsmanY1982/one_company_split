# `core/modules/personnel/distribution_window/_links.py`

> 路径：`core/modules/personnel/distribution_window/_links.py` | 行数：181


---


```python
"""
_LinksMixin — 分销链接 Tab 全部操作
"""
import os
import csv
from datetime import datetime

from PyQt5.QtWidgets import (
    QMessageBox, QTableWidgetItem, QLineEdit,
    QFormLayout, QDialog,
)
from PyQt5.QtGui import QColor

from core.ui_components import PrimaryButton, SecondaryButton, DangerButton
from core.light_tool_theme import LIGHT_TOOL_STYLE

from core.modules.personnel.distribution_service import (
    get_all_links, create_link, increment_click, increment_register,
    update_link_status, delete_link,
)
try:
    from paths import DATA_DIR
except ImportError:
    try:
        from paths import DATA_DIR
    except ImportError:
        from core.paths import DATA_DIR


class _LinksMixin:
    """分销链接 Tab 全部操作"""

    # ── 数据加载 ──
    def _load_links(self):
        rows = get_all_links()
        self.link_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.link_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.link_table.setItem(i, 1, QTableWidgetItem(str(r["user_name"])))
            self.link_table.setItem(i, 2, QTableWidgetItem(str(r["code"])))
            self.link_table.setItem(i, 3, QTableWidgetItem(str(r.get("url") or "")))
            self.link_table.setItem(i, 4, QTableWidgetItem(str(r["click_count"])))
            self.link_table.setItem(i, 5, QTableWidgetItem(str(r["register_count"])))
            status_item = QTableWidgetItem(str(r["status"]))
            if r["status"] == "active":
                status_item.setForeground(QColor(136, 255, 187))
            elif r["status"] == "inactive":
                status_item.setForeground(QColor(255, 170, 170))
            self.link_table.setItem(i, 6, status_item)
        self._update_stats()

    def _search_links(self):
        text = self.link_search.text().strip()
        if not text:
            self._load_links()
            return
        rows = [r for r in get_all_links()
                if text.lower() in str(r.get("user_name", "")).lower()
                or text.lower() in str(r.get("code", "")).lower()]
        self.link_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.link_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.link_table.setItem(i, 1, QTableWidgetItem(str(r["user_name"])))
            self.link_table.setItem(i, 2, QTableWidgetItem(str(r["code"])))
            self.link_table.setItem(i, 3, QTableWidgetItem(str(r.get("url") or "")))
            self.link_table.setItem(i, 4, QTableWidgetItem(str(r["click_count"])))
            self.link_table.setItem(i, 5, QTableWidgetItem(str(r["register_count"])))
            self.link_table.setItem(i, 6, QTableWidgetItem(str(r["status"])))

    # ── 创建链接对话框 ──
    def _show_create_link_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("创建分销链接")
        dlg.setMinimumWidth(420)
        dlg.setStyleSheet(LIGHT_TOOL_STYLE)
        layout = QFormLayout(dlg)
        layout.setSpacing(12)
        user_input = QLineEdit()
        user_input.setPlaceholderText("输入用户ID")
        layout.addRow("用户ID:", user_input)
        code_input = QLineEdit()
        code_input.setPlaceholderText("留空自动生成")
        layout.addRow("推广码:", code_input)
        url_input = QLineEdit()
        url_input.setPlaceholderText("https://example.com/ref/...")
        layout.addRow("链接URL:", url_input)
        btn = PrimaryButton("创建")

        def do_create():
            uid = user_input.text().strip()
            if not uid:
                QMessageBox.warning(dlg, "提示", "用户ID不能为空")
                return
            try:
                uid_int = int(uid)
            except ValueError:
                QMessageBox.warning(dlg, "格式错误", "用户ID必须是整数")
                return
            code = code_input.text().strip()
            url = url_input.text().strip()
            result = create_link(user_id=uid_int, code=code or None, url=url or None)
            if result["ok"]:
                QMessageBox.information(dlg, "成功",
                    f"链接已创建\n推广码: {result.get('code', code)}")
                self._load_links()
                dlg.accept()
            else:
                err = result.get("error", "未知错误")
                if "UNIQUE constraint" in err or "已存在" in err:
                    QMessageBox.warning(dlg, "错误", "推广码已存在")
                else:
                    QMessageBox.warning(dlg, "错误", f"创建失败: {err}")

        btn.clicked.connect(do_create)
        layout.addRow(btn)
        dlg.exec_()

    # ── 链接操作 ──
    def _toggle_link_status(self):
        row = self.link_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个链接")
            return
        link_id = int(self.link_table.item(row, 0).text())
        current_status = self.link_table.item(row, 6).text()
        new_status = "inactive" if current_status == "active" else "active"
        result = update_link_status(link_id, new_status)
        if result["ok"]:
            self._load_links()
            QMessageBox.information(self, "成功", f"链接状态已更新为: {new_status}")

    def _delete_selected_link(self):
        row = self.link_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个链接")
            return
        link_id = int(self.link_table.item(row, 0).text())
        if QMessageBox.question(self, "确认", f"确定删除链接 #{link_id}？",
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        result = delete_link(link_id)
        if result["ok"]:
            self._load_links()

    def _simulate_click(self):
        row = self.link_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个链接")
            return
        code = self.link_table.item(row, 2).text()
        result = increment_click(code)
        if result["ok"]:
            self._load_links()
            QMessageBox.information(self, "完成", "点击数 +1")
        else:
            QMessageBox.warning(self, "错误", result.get("error", "操作失败"))

    def _simulate_register(self):
        row = self.link_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个链接")
            return
        code = self.link_table.item(row, 2).text()
        result = increment_register(code)
        if result["ok"]:
            self._load_links()
            QMessageBox.information(self, "完成", "注册数 +1")
        else:
            QMessageBox.warning(self, "错误", result.get("error", "操作失败"))

    def _export_links(self):
        filepath = os.path.join(DATA_DIR,
            f"links_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        rows = get_all_links()
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(["ID", "用户ID", "推广码", "链接", "点击", "注册", "状态"])
            for r in rows:
                w.writerow([r["id"], r["user_name"], r["code"], r.get("url", ""),
                            r["click_count"], r["register_count"], r.get("status", "")])
        QMessageBox.information(self, "导出成功", f"已导出 {len(rows)} 条链接到:\n{filepath}")

```
