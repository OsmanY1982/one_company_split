# `core/modules/auth/activation_gate.py`

> 路径：`core/modules/auth/activation_gate.py` | 行数：308


---


```python
# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import Any

import sys
import os
# 动态获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QMessageBox, QTabWidget, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from core.modules.account.license_local import (
    validate_license, activate_license, get_machine_code, CODE_TYPES
)
from core.paths import CONFIG_DIR

LICENSE_FILE = os.path.join(CONFIG_DIR, "license.json")


class ActivationGateWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        apply_dark_theme(self)
        self.setWindowTitle("一人公司管理系统")
        self.setMinimumSize(560, 680)
        self._build_ui()
        self.show()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(12)

        # 标题栏
        header_layout = QHBoxLayout()
        logo_lbl = QLabel("🏢")
        logo_lbl.setStyleSheet("font-size: 28px;")
        header_layout.addWidget(logo_lbl)
        title_col = QVBoxLayout()
        title_col.addWidget(QLabel("一人公司管理系统"))
        self.msg_label = QLabel()
        self.msg_label.setStyleSheet("color: #e53e3e; font-size: 12px; font-weight: normal;")
        title_col.addWidget(self.msg_label)
        header_layout.addLayout(title_col)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Tab
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self._build_pay_tab()
        self._build_code_tab()
        self._build_trial_tab()

        # 机器码 + 一键复制
        mc_layout = QHBoxLayout()
        mc_layout.setAlignment(Qt.AlignCenter)
        self.machine_label = QLabel()
        self.machine_label.setStyleSheet("color: #a0aec0; font-size: 11px; font-family: Menlo;")
        mc_layout.addWidget(self.machine_label)
        btn_copy_mc = QPushButton("📋 复制机器码")
        btn_copy_mc.setObjectName("grayBtn")
        btn_copy_mc.setFixedHeight(26)
        btn_copy_mc.setFixedWidth(110)
        btn_copy_mc.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        btn_copy_mc.clicked.connect(self._copy_machine_code)
        mc_layout.addWidget(btn_copy_mc)
        main_layout.addLayout(mc_layout)

        # 底部
        footer = QLabel("商务合作 & 定制开发  |  微信：Osman-Y  |  QQ：59435234  |  59435234@qq.com")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #cbd5e0; font-size: 11px;")
        main_layout.addWidget(footer)

        self._update_status()

    def _build_pay_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # 套餐卡片
        plan_layout = QGridLayout()
        plans = [
            ("🆓", "体验会员", "免费 / 7天", "#38b2ac", "trial"),
            ("⭐", "VIP会员", "¥49 / 1年", "#3182ce", "pro"),
            ("👑", "钻石会员", "¥99 / 终身", "#d69e2e", "vip"),
        ]
        self._selected_plan = [None]

        for i, (icon, name, price, color, pid) in enumerate(plans):
            card = QWidget()
            card.setStyleSheet(f"background: #111936; border: 2px solid {color}; border-radius: 10px; padding: 12px;")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(8, 8, 8, 8)
            cl.setSpacing(4)
            icon_lbl = QLabel(f'<span style="font-size:22px">{icon}</span>')
            icon_lbl.setAlignment(Qt.AlignCenter)
            cl.addWidget(icon_lbl)
            nl = QLabel(name)
            nl.setFont(QFont("PingFang SC", 12, QFont.Bold))
            nl.setAlignment(Qt.AlignCenter)
            nl.setStyleSheet(f"color: {color};")
            cl.addWidget(nl)
            pl = QLabel(price)
            pl.setFont(QFont("PingFang SC", 11))
            pl.setAlignment(Qt.AlignCenter)
            pl.setStyleSheet("color: #718096;")
            cl.addWidget(pl)
            btn = QPushButton("选择此套餐")
            btn.setObjectName({"trial": "greenBtn", "vip": "goldBtn"}.get(pid, ""))
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda _, p=pid: self._select_plan(p))
            cl.addWidget(btn)
            plan_layout.addWidget(card, 0, i)

        self.plan_hint = QLabel("👆 请先选择一个套餐，再扫码支付")
        self.plan_hint.setStyleSheet("color: #718096; font-size: 12px; font-weight: normal;")
        plan_hint_layout = QHBoxLayout()
        plan_hint_layout.addWidget(self.plan_hint)
        plan_hint_layout.addStretch()
        layout.addLayout(plan_layout)
        layout.addLayout(plan_hint_layout)

        # 收款码区域
        qr_group = QGroupBox("扫码支付")
        qr_layout = QHBoxLayout(qr_group)
        qr_layout.setSpacing(16)
        for icon, title, note in [
            ("💬", "微信支付", "[收款码待配置]"),
            ("💙", "支付宝", "[收款码待配置]"),
        ]:
            w = QWidget()
            w.setStyleSheet("background: #111936; border-radius: 8px; padding: 10px; border: 1px solid #e2e8f0;")
            wl = QVBoxLayout(w)
            wl.setContentsMargins(4, 4, 4, 4)
            lbl = QLabel(title)
            lbl.setFont(QFont("PingFang SC", 12, QFont.Bold))
            lbl.setAlignment(Qt.AlignCenter)
            wl.addWidget(lbl)
            img_lbl = QLabel(f"{icon}\n{note}")
            img_lbl.setAlignment(Qt.AlignCenter)
            img_lbl.setStyleSheet("color: #cbd5e0; font-size: 12px; padding: 40px;")
            wl.addWidget(img_lbl)
            qr_layout.addWidget(w)
        layout.addWidget(qr_group)

        # 激活码输入
        code_layout = QHBoxLayout()
        self.pay_code_input = QLineEdit()
        self.pay_code_input.setPlaceholderText("支付成功后，输入激活码并点击激活")
        code_layout.addWidget(self.pay_code_input)
        btn_active = QPushButton("🔓 激活")
        btn_active.setObjectName("greenBtn")
        btn_active.clicked.connect(self._do_pay_activate)
        code_layout.addWidget(btn_active)
        layout.addLayout(code_layout)
        layout.addStretch()
        self.tabs.addTab(tab, "💳 扫码支付")

    def _build_code_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        hint = QLabel("请输入您购买获得的激活码，格式如：PRO-XXXX-XXXX-XXXX")
        hint.setStyleSheet("color: #718096; font-size: 12px; padding: 4px;")
        layout.addWidget(hint)
        self.direct_code_input = QLineEdit()
        self.direct_code_input.setPlaceholderText("请输入激活码")
        self.direct_code_input.setMinimumHeight(44)
        layout.addWidget(self.direct_code_input)
        btn_direct = QPushButton("🔓 立即激活")
        btn_direct.setObjectName("greenBtn")
        btn_direct.setFixedHeight(44)
        btn_direct.clicked.connect(self._do_direct_activate)
        layout.addWidget(btn_direct)
        layout.addStretch()
        self.tabs.addTab(tab, "🔑 激活码激活")

    def _build_trial_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        info = QWidget()
        info.setStyleSheet("background: #111936; border-radius: 10px; padding: 20px; border: 1px solid #e2e8f0;")
        il = QVBoxLayout(info)
        il.setSpacing(8)
        il.addWidget(QLabel("🆓 免费体验"))
        l1 = QLabel("免费试用 7 天，基础功能可用")
        l1.setStyleSheet("color: #718096;")
        il.addWidget(l1)
        l2 = QLabel("到期自动锁定，需购买激活码续期")
        l2.setStyleSheet("color: #e53e3e; font-size: 12px;")
        il.addWidget(l2)
        l3 = QLabel("适合先体验功能，再决定是否购买")
        l3.setStyleSheet("color: #a0aec0; font-size: 12px;")
        il.addWidget(l3)
        layout.addWidget(info)
        btn_trial = QPushButton("🆓 立即免费体验 7 天")
        btn_trial.setObjectName("greenBtn")
        btn_trial.setFixedHeight(50)
        btn_trial.setFont(QFont("PingFang SC", 14))
        btn_trial.clicked.connect(self._do_trial)
        layout.addWidget(btn_trial)
        layout.addStretch()
        self.tabs.addTab(tab, "🆓 免费体验")

    def _copy_machine_code(self) -> None:
        from PyQt5.QtWidgets import QApplication
        mc = get_machine_code()
        QApplication.clipboard().setText(mc)
        QMessageBox.information(self, "已复制", f"机器码已复制到剪贴板：\n{mc}\n\n发给管理员即可获取激活码")

    def _update_status(self) -> None:
        lic = validate_license()
        if lic["valid"]:
            self.msg_label.setText("✅ 已激活，正在进入...")
            self.machine_label.setText(f"机器码：{get_machine_code()}")
            QTimer.singleShot(200, self._go_next)
        else:
            if lic.get("expired") and lic.get("reason"):
                self.msg_label.setText(f"⏰ {lic['reason']}，请重新激活")
            elif lic.get("expired"):
                self.msg_label.setText("⏰ 使用期限已到期，请重新激活")
            else:
                self.msg_label.setText("🆓 请先激活系统，免费体验7天")
            self.machine_label.setText(f"机器码：{get_machine_code()}")

    def _select_plan(self, plan_id: str) -> None:
        info = CODE_TYPES.get(plan_id.upper(), {})
        name = info.get("name", plan_id)
        price = "免费" if plan_id == "trial" else ("¥49/年" if plan_id == "pro" else "¥99/终身")
        self.plan_hint.setText(f"✅ 已选：【{name}】{price}，扫码支付后输入激活码激活")
        self.plan_hint.setStyleSheet("color: #38a169; font-size: 12px; font-weight: bold;")
        self._selected_plan[0] = plan_id

    def _do_activate(self, code: str) -> Any:
        from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
        from core.dark_theme import apply_dark_theme, BG_MAIN, BG_CARD, BG_INPUT, BTN_NORMAL, BTN_HOVER, BTN_PRESSED, TEXT_WHITE, TEXT_LIGHT, TEXT_MUTED, ACCENT, SUCCESS, WARNING, DANGER, BORDER, BORDER_LIGHT
        if not code:
            QMessageBox.warning(self, "提示", "请输入激活码")
            return False
        ok, msg = activate_license(code, "default")
        if ok:
            QMessageBox.information(self, "🎉 激活成功", msg)
            self.msg_label.setText("✅ 已激活，正在进入...")
            QTimer.singleShot(500, self._go_next)
            return True
        else:
            # 细化错误提示
            if "已被账号" in msg:
                detail = f"{msg}\n\n💡 每个激活码只能绑定一个账号，请联系管理员获取新激活码"
            elif "设备不匹配" in msg or "其他设备" in msg:
                detail = f"{msg}\n\n💡 激活码已绑定其他设备，不能在本机使用\n本机机器码：{get_machine_code()}"
            elif "格式不正确" in msg or "无效" in msg:
                detail = f"{msg}\n\n💡 正确格式示例：PRO-ABCD-1234-EFGH\n请检查是否有多余空格或字符"
            elif "篡改" in msg:
                detail = f"{msg}\n\n💡 请删除 config/license_*.json 文件后重新激活"
            else:
                detail = msg
            QMessageBox.warning(self, "激活失败", detail)
            return False

    def _do_pay_activate(self) -> None:
        self._do_activate(self.pay_code_input.text().strip())

    def _do_direct_activate(self) -> None:
        self._do_activate(self.direct_code_input.text().strip())

    def _do_trial(self) -> None:
        import json
        from datetime import datetime, timedelta
        os.makedirs(os.path.dirname(LICENSE_FILE), exist_ok=True)
        with open(LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "type": "TRIAL",
                "code": "TRIAL-FREE-00000",
                "account": "guest",
                "machine_code": get_machine_code(),
                "activated_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
                "name": "体验会员",
                "features": ["basic"]
            }, f, indent=2)
        QMessageBox.information(self, "🎉 激活成功", "免费体验 7 天已开始！")
        self.msg_label.setText("✅ 已激活，正在进入...")
        QTimer.singleShot(500, self._go_next)

    def _go_next(self) -> None:
        self.hide()
        def _show() -> None:
            from core.modules.login.select_mode_window import SelectModeWindow
            sw = SelectModeWindow()
            sw.show()
            sw.activateWindow()
        QTimer.singleShot(50, _show)

```
