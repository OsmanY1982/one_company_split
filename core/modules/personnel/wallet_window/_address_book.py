# -*- coding: utf-8 -*-
"""
Address Book Mixin — 地址簿管理（浅色主题）
"""
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QDialog, QFormLayout, QMessageBox,
    QAbstractItemView
)

from core.ui_components import PrimaryButton, SecondaryButton, DangerButton
from core.light_tool_theme import LIGHT_TOOL_STYLE
from core.modules.personnel.wallet_service import (
    get_addresses, add_address, update_address, delete_address,
)


class _AddressBookMixin:
    """地址簿管理"""

    def _load_address_book(self):
        owner = self.addr_owner_input.text().strip() or None
        rows = get_addresses(owner) if owner else get_addresses()
        self.addr_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.addr_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.addr_table.setItem(i, 1, QTableWidgetItem(str(r.get("label", ""))))
            self.addr_table.setItem(i, 2, QTableWidgetItem(str(r.get("address", ""))))
            self.addr_table.setItem(i, 3, QTableWidgetItem(str(r.get("address_type", ""))))
            self.addr_table.setItem(i, 4, QTableWidgetItem(str(r.get("note", ""))))

    def _show_add_address_dialog(self):
        sel = self._get_selected_wallet()
        default_owner = sel[1] if sel else ""
        dlg = QDialog(self)
        dlg.setWindowTitle("添加地址")
        dlg.setMinimumWidth(400)
        dlg.setStyleSheet(LIGHT_TOOL_STYLE)
        layout = QFormLayout(dlg)
        owner_e = QLineEdit(default_owner)
        owner_e.setPlaceholderText("所属用户ID")
        layout.addRow("所属用户:", owner_e)
        label_e = QLineEdit()
        label_e.setPlaceholderText("如：我的银行卡")
        layout.addRow("标签:", label_e)
        addr_e = QLineEdit()
        addr_e.setPlaceholderText("账户地址/ID")
        layout.addRow("地址:", addr_e)
        type_e = QComboBox()
        type_e.addItems(["user", "bank", "alipay", "wechat", "other"])
        layout.addRow("类型:", type_e)
        note_e = QLineEdit()
        layout.addRow("备注:", note_e)
        btn = PrimaryButton("保存")

        def do_save():
            owner = owner_e.text().strip()
            label = label_e.text().strip()
            addr = addr_e.text().strip()
            if not owner or not label or not addr:
                QMessageBox.warning(dlg, "提示", "所属用户、标签、地址都不能为空")
                return
            result = add_address(owner, label, addr,
                                 type_e.currentText(), note_e.text().strip())
            if result["ok"]:
                QMessageBox.information(dlg, "成功", "地址已添加")
                self._load_address_book()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "失败",
                    "添加失败: " + result.get("error", "未知错误"))

        btn.clicked.connect(do_save)
        layout.addRow(btn)
        dlg.exec_()

    def _delete_address(self):
        row = self.addr_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择要删除的地址")
            return
        addr_id = int(self.addr_table.item(row, 0).text())
        confirm = QMessageBox.question(
            self, "确认删除", "确定要删除这条地址吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            result = delete_address(addr_id)
            if result["ok"]:
                self._load_address_book()
                QMessageBox.information(self, "成功", "地址已删除")
            else:
                QMessageBox.warning(self, "失败",
                    "删除失败: " + result.get("error", "未知错误"))

    def _edit_address(self):
        row = self.addr_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择要编辑的地址")
            return
        addr_id = int(self.addr_table.item(row, 0).text())
        old_label = self.addr_table.item(row, 1).text()
        old_addr = self.addr_table.item(row, 2).text()
        old_type = self.addr_table.item(row, 3).text()
        old_note = self.addr_table.item(row, 4).text()
        dlg = QDialog(self)
        dlg.setWindowTitle("编辑地址")
        dlg.setMinimumWidth(400)
        dlg.setStyleSheet(LIGHT_TOOL_STYLE)
        layout = QFormLayout(dlg)
        label_e = QLineEdit(old_label)
        layout.addRow("标签:", label_e)
        addr_e = QLineEdit(old_addr)
        layout.addRow("地址:", addr_e)
        type_e = QComboBox()
        type_e.addItems(["user", "bank", "alipay", "wechat", "other"])
        type_e.setCurrentText(old_type)
        layout.addRow("类型:", type_e)
        note_e = QLineEdit(old_note)
        layout.addRow("备注:", note_e)
        btn = PrimaryButton("保存修改")

        def do_save():
            label = label_e.text().strip()
            addr = addr_e.text().strip()
            if not label or not addr:
                QMessageBox.warning(dlg, "提示", "标签和地址都不能为空")
                return
            result = update_address(addr_id, label=label, address=addr,
                                    note=note_e.text().strip())
            if result["ok"]:
                QMessageBox.information(dlg, "成功", "地址已更新")
                self._load_address_book()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "失败",
                    "更新失败: " + result.get("error", "未知错误"))

        btn.clicked.connect(do_save)
        layout.addRow(btn)
        dlg.exec_()
