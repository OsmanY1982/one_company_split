# -*- coding: utf-8 -*-
"""
Dialogs Mixin — 操作对话框（创建/充值/提现/转账/佣金）（浅色主题）
"""
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLabel, QLineEdit,
    QPushButton, QDoubleSpinBox, QMessageBox
)

from core.ui_components import PrimaryButton, SecondaryButton, DangerButton
from core.light_tool_theme import LIGHT_TOOL_STYLE
from core.modules.personnel.wallet_service import (
    get_or_create_wallet, recharge, get_wallet,
    submit_withdrawal_request, transfer, add_commission,
)


class _DialogsMixin:
    """操作对话框"""

    def _show_create_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("创建钱包")
        dlg.setMinimumWidth(350)
        dlg.setStyleSheet(LIGHT_TOOL_STYLE)
        layout = QFormLayout(dlg)
        user_input = QLineEdit()
        user_input.setPlaceholderText("输入用户ID")
        layout.addRow("用户ID:", user_input)
        btn = PrimaryButton("创建")

        def do_create():
            uid = user_input.text().strip()
            if not uid:
                QMessageBox.warning(dlg, "提示", "用户ID不能为空")
                return
            result = get_or_create_wallet(uid)
            if result.get("id"):
                QMessageBox.information(
                    dlg, "成功",
                    f"钱包已创建: {uid}（ID: {result['id']}）"
                )
                self.load_wallets()
                self.load_dashboard()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "错误", "创建失败")

        btn.clicked.connect(do_create)
        layout.addRow(btn)
        dlg.exec_()

    def _show_recharge_dialog(self):
        sel = self._get_selected_wallet()
        if not sel:
            return
        wallet_id, user_id = sel
        dlg = QDialog(self)
        dlg.setWindowTitle(f"💰 充值 - {user_id}")
        dlg.setMinimumWidth(350)
        dlg.setStyleSheet(LIGHT_TOOL_STYLE)
        layout = QFormLayout(dlg)
        amt = QDoubleSpinBox()
        amt.setRange(0.01, 999999)
        amt.setValue(100)
        amt.setDecimals(2)
        layout.addRow("金额:", amt)
        desc = QLineEdit()
        desc.setText("后台充值")
        layout.addRow("备注:", desc)
        btn = PrimaryButton("确认充值")

        def do():
            result = recharge(user_id, amt.value(), desc.text())
            if result["ok"]:
                QMessageBox.information(dlg, "成功",
                    f"充值 {amt.value():.2f} 成功\n新余额: {result['balance']:.2f}")
                self.load_wallets()
                self.load_transactions()
                self.load_dashboard()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "错误", result.get("error", "充值失败"))

        btn.clicked.connect(do)
        layout.addRow(btn)
        dlg.exec_()

    def _show_withdrawal_request_dialog(self):
        sel = self._get_selected_wallet()
        if not sel:
            return
        wallet_id, user_id = sel
        w = get_wallet(user_id)
        available = w.get("balance", 0) - w.get("frozen_amount", 0)

        dlg = QDialog(self)
        dlg.setWindowTitle(f"📥 提现申请 - {user_id}")
        dlg.setMinimumWidth(380)
        dlg.setStyleSheet(LIGHT_TOOL_STYLE)
        layout = QFormLayout(dlg)
        info = QLabel(f"当前可用余额: ¥{available:.2f}（冻结中金额不会影响可用余额）")
        info.setStyleSheet("color: #6b7280; padding: 4px;")
        layout.addRow(info)
        amt = QDoubleSpinBox()
        amt.setRange(0.01, available if available > 0 else 0.01)
        amt.setDecimals(2)
        layout.addRow("提现金额:", amt)
        desc = QLineEdit()
        desc.setPlaceholderText("可选备注（如银行账号）")
        layout.addRow("备注:", desc)
        note_lbl = QLabel(
            "💡 提交后将冻结金额，等待审批通过后正式扣款\n"
            "审批拒绝后金额自动解冻"
        )
        note_lbl.setStyleSheet("color: #6b7280; font-size: 12px; padding: 4px;")
        layout.addRow(note_lbl)
        btn = SecondaryButton("提交申请")

        def do():
            if amt.value() <= 0:
                QMessageBox.warning(dlg, "提示", "金额必须大于 0")
                return
            result = submit_withdrawal_request(user_id, amt.value(), desc.text())
            if result["ok"]:
                QMessageBox.information(dlg, "成功",
                                        result.get("message", "申请已提交"))
                self.load_wallets()
                self.load_withdrawal_queue()
                self.load_dashboard()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "错误",
                                    result.get("error", "提交失败"))

        btn.clicked.connect(do)
        layout.addRow(btn)
        dlg.exec_()

    def _show_transfer_dialog(self):
        sel = self._get_selected_wallet()
        if not sel:
            return
        _, from_user = sel
        w = get_wallet(from_user)
        available = w.get("balance", 0) - w.get("frozen_amount", 0)

        dlg = QDialog(self)
        dlg.setWindowTitle(f"🔄 转账 - {from_user}")
        dlg.setMinimumWidth(380)
        dlg.setStyleSheet(LIGHT_TOOL_STYLE)
        layout = QFormLayout(dlg)
        layout.addRow(QLabel(f"可用余额: ¥{available:.2f}"))
        to_input = QLineEdit()
        to_input.setPlaceholderText("目标用户ID")
        layout.addRow("转入用户:", to_input)
        amt = QDoubleSpinBox()
        amt.setRange(0.01, available)
        amt.setDecimals(2)
        layout.addRow("金额:", amt)
        desc = QLineEdit()
        desc.setPlaceholderText("可选备注")
        layout.addRow("备注:", desc)
        btn = PrimaryButton("确认转账")

        def do():
            to_user = to_input.text().strip()
            if not to_user:
                QMessageBox.warning(dlg, "提示", "目标用户ID不能为空")
                return
            result = transfer(from_user, to_user, amt.value(), desc.text())
            if result["ok"]:
                QMessageBox.information(dlg, "成功",
                    f"转账 {amt.value():.2f} 给 {to_user} 成功\n"
                    f"你的新余额: {result['from_balance']:.2f}")
                self.load_wallets()
                self.load_transactions()
                self.load_dashboard()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "错误", result.get("error", "转账失败"))

        btn.clicked.connect(do)
        layout.addRow(btn)
        dlg.exec_()

    def _show_commission_dialog(self):
        sel = self._get_selected_wallet()
        if not sel:
            return
        wallet_id, user_id = sel
        dlg = QDialog(self)
        dlg.setWindowTitle(f"🎁 发放佣金 - {user_id}")
        dlg.setMinimumWidth(350)
        dlg.setStyleSheet(LIGHT_TOOL_STYLE)
        layout = QFormLayout(dlg)
        amt = QDoubleSpinBox()
        amt.setRange(0.01, 999999)
        amt.setDecimals(2)
        layout.addRow("佣金金额:", amt)
        desc = QLineEdit()
        desc.setText("佣金收入")
        layout.addRow("描述:", desc)
        btn = PrimaryButton("确认发放")

        def do():
            result = add_commission(user_id, amt.value(), desc.text())
            if result["ok"]:
                QMessageBox.information(dlg, "成功",
                    f"佣金 {amt.value():.2f} 发放成功\n新余额: {result['balance']:.2f}")
                self.load_wallets()
                self.load_transactions()
                self.load_dashboard()
                dlg.accept()
            else:
                QMessageBox.warning(dlg, "错误", result.get("error", "发放失败"))

        btn.clicked.connect(do)
        layout.addRow(btn)
        dlg.exec_()
