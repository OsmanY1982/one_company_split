# -*- coding: utf-8 -*-
"""
账号许可证 — 激活码全功能管理窗口
迁移自桌面版 ActivationCodeWindow，完整保留业务逻辑
"""
import sys, os, secrets, hashlib, csv
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QGroupBox, QComboBox, QLineEdit, QMessageBox, QHeaderView,
    QFileDialog, QTextEdit, QFrame, QApplication, QInputDialog,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from core.modules.account.license_local import (
    init_activation_db, CODE_TYPES, _normalize, _format_code, DB_FILE, activate_license
)
from core.modules.account.activation_service import (
    init_admin_db, generate_codes, get_codes, get_code_by_raw,
    update_code_status, bind_account, unbind_account, mark_used,
    unbind_machine, delete_codes, get_unused_codes, get_all_codes_raw,
    reset_admin_password,
)

# 确保数据库初始化
init_activation_db()
init_admin_db()


_STYLE = """
QDialog {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 rgba(10,12,18,245), stop:1 rgba(18,21,28,245));
    border: 2px solid rgba(130,145,165,35);
    border-radius: 14px;
}
QLabel { color: #99aabb; background: transparent; font-size: 12px; }
QGroupBox {
    color: #889999; font-weight: 700; font-size: 12px;
    border: 1px solid rgba(130,145,165,25); border-radius: 10px;
    margin-top: 10px; padding-top: 14px;
}
QGroupBox::title { left: 14px; padding: 0 6px; }
QLineEdit, QComboBox {
    background: rgba(16,20,26,220); color: #aabbcc;
    border: 1px solid rgba(130,145,165,25); border-radius: 6px;
    padding: 6px 10px; font-size: 12px;
}
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background: #14181e; color: #aabbcc;
    selection-background-color: rgba(130,145,165,50);
}
QPushButton {
    background: rgba(130,145,165,30); color: #ccddee;
    border: 1px solid rgba(150,165,185,45); border-radius: 8px;
    padding: 7px 20px; font-size: 11px; font-weight: 600;
}
QPushButton:hover { background: rgba(160,175,195,55); }
QTableWidget {
    background: rgba(14,18,24,220); color: #aabbcc;
    border: 1px solid rgba(120,140,165,20); border-radius: 8px;
    gridline-color: rgba(80,95,115,18); font-size: 12px;
    selection-background-color: rgba(100,120,150,45);
}
QTableWidget::item { padding: 5px 10px; }
QHeaderView::section {
    background: rgba(22,26,32,230); color: #889999;
    padding: 8px 10px; border: none;
    border-bottom: 1px solid rgba(130,145,165,30);
    font-weight: 700; font-size: 11px; letter-spacing: 1px;
}
"""


class AccountActivationWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("许可证管理 · ACCOUNT NEXUS")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(_STYLE)
        self._cloud_connected = False
        self.init_ui()
        self.load_codes()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 顶部标题栏
        top_layout = QHBoxLayout()
        title = QLabel("激活码管理")
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        top_layout.addWidget(title)
        self.cloud_status = QLabel("🟡 未连接")
        self.cloud_status.setStyleSheet("color: #999; font-size: 13px;")
        self.cloud_status.mousePressEvent = lambda e: self._test_cloud()
        self.cloud_status.setCursor(Qt.PointingHandCursor)
        top_layout.addWidget(self.cloud_status)
        self.total_label = QLabel("总: 0")
        self.total_label.setStyleSheet("color: #666;")
        top_layout.addWidget(self.total_label)
        self.unused_label = QLabel("未使用: 0")
        self.unused_label.setStyleSheet("color: #28a745; font-weight: bold;")
        top_layout.addWidget(self.unused_label)
        self.used_label = QLabel("已激活: 0")
        self.used_label.setStyleSheet("color: #4299e1; font-weight: bold;")
        top_layout.addWidget(self.used_label)
        self.expired_label = QLabel("已过期: 0")
        self.expired_label.setStyleSheet("color: #e53e3e; font-weight: bold;")
        top_layout.addWidget(self.expired_label)

        # 统计面板
        stats_group = QGroupBox("激活码统计")
        stats_layout = QHBoxLayout(stats_group)
        for t, info in CODE_TYPES.items():
            card = QWidget()
            card.setStyleSheet("background-color: #111936; border-radius: 8px; padding: 12px; min-width: 140px; border: 1px solid #1a237e;")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            lbl_name = QLabel(info["name"])
            lbl_name.setStyleSheet("color: #718096; font-size: 13px;")
            card_layout.addWidget(lbl_name)
            lbl_count = QLabel("0")
            lbl_count.setStyleSheet("color: #2d3748; font-size: 24px; font-weight: bold;")
            card_layout.addWidget(lbl_count)
            lbl_days = QLabel(
                "永久" if info["days"] == 0 else f"{info['days']}天"
            )
            lbl_days.setStyleSheet("color: #a0aec0; font-size: 12px;")
            card_layout.addWidget(lbl_days)
            stats_layout.addWidget(card)

        # 生成区域
        gen_group = QGroupBox("生成激活码")
        gen_layout = QHBoxLayout(gen_group)

        gen_layout.addWidget(QLabel("类型:"))
        self.type_combo = QComboBox()
        for t, info in CODE_TYPES.items():
            label = f"{info['name']}（{'永久' if info['days'] == 0 else str(info['days']) + '天'}）"
            self.type_combo.addItem(label, t)
        gen_layout.addWidget(self.type_combo)

        gen_layout.addWidget(QLabel("数量:"))
        self.count_spin = QComboBox()
        self.count_spin.addItems(["1", "5", "10", "20", "50"])
        gen_layout.addWidget(self.count_spin)

        self.gen_note_input = QLineEdit()
        self.gen_note_input.setPlaceholderText("备注（可选，如：好友赠送）")
        gen_layout.addWidget(self.gen_note_input)

        btn_gen = QPushButton("生成激活码")
        btn_gen.setStyleSheet("background-color: #28a745; color: white; padding: 8px 24px; font-weight: bold;")
        btn_gen.clicked.connect(self.generate_codes)
        gen_layout.addWidget(btn_gen)

        btn_gen_10 = QPushButton("批量生成10个")
        btn_gen_10.setStyleSheet("background-color: #17a2b8; color: white; padding: 8px 16px;")
        btn_gen_10.clicked.connect(lambda: self._quick_gen(10))
        gen_layout.addWidget(btn_gen_10)

        btn_reset_admin = QPushButton("⚠ 重置管理员")
        btn_reset_admin.setStyleSheet("background-color: #e53e3e; color: white; padding: 8px 16px;")
        btn_reset_admin.clicked.connect(self._reset_admin)
        gen_layout.addWidget(btn_reset_admin)

        # ====================== 【绑定账号区域 - 修复版】 ======================
        bind_group = QGroupBox("绑定账号")
        bind_layout = QHBoxLayout(bind_group)
        
        bind_layout.addWidget(QLabel("输入要绑定的用户名:"))
        self.bind_account_input = QLineEdit()
        self.bind_account_input.setPlaceholderText("例如：123")
        self.bind_account_input.setFixedWidth(180)
        bind_layout.addWidget(self.bind_account_input)

        btn_bind = QPushButton("🔗 绑定选中激活码")
        btn_bind.setStyleSheet("background-color: #007bff; color: white; font-weight:bold; padding:8px 16px;")
        btn_bind.clicked.connect(self.bind_selected_code)
        bind_layout.addWidget(btn_bind)

        btn_unbind = QPushButton("❌ 清空绑定")
        btn_unbind.setStyleSheet("background-color: #6c757d; color: white; padding:8px 16px;")
        btn_unbind.clicked.connect(self.unbind_selected_code)
        bind_layout.addWidget(btn_unbind)
        bind_layout.addStretch()
        # ========================================================================

        # 搜索
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("激活码 / 账号")
        self.search_input.textChanged.connect(self.search_codes)
        search_layout.addWidget(self.search_input)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部", "未使用", "已激活", "已过期"])
        self.filter_combo.currentIndexChanged.connect(self.load_codes)
        search_layout.addWidget(self.filter_combo)
        self.cloud_label = QLabel("云同步")
        self.cloud_label.setStyleSheet("color: #718096; font-size: 13px;")
        self.cloud_sync_btn = QPushButton("☁️ 一键同步全部")
        self.cloud_sync_btn.setStyleSheet("background-color: #805ad5; color: white; padding: 6px 16px; font-weight: bold;")
        self.cloud_sync_btn.clicked.connect(self._sync_all_to_cloud)
        self.cloud_sync_btn.setToolTip("将所有本地激活码同步到 Supabase 云端")
        btn_cloud_stats = QPushButton("📡 云端管理")
        btn_cloud_stats.setStyleSheet("background-color: #3182ce; color: white; padding: 6px 16px;")
        btn_cloud_stats.clicked.connect(self._open_cloud_manager)
        search_layout.addWidget(self.cloud_label)
        search_layout.addWidget(self.cloud_sync_btn)
        search_layout.addWidget(btn_cloud_stats)
        search_layout.addStretch()

        btn_stats = QPushButton("📊 激活统计")
        btn_stats.setStyleSheet("background-color: #805ad5; color: white; font-weight: bold;")
        btn_stats.clicked.connect(self._open_stats)
        search_layout.addWidget(btn_stats)
        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.load_codes)
        search_layout.addWidget(btn_refresh)
        btn_activate = QPushButton("✅ 直接激活用户")
        btn_activate.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        btn_activate.clicked.connect(self._activate_user)
        search_layout.addWidget(btn_activate)
        btn_remote = QPushButton("🌐 远程激活")
        btn_remote.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold;")
        btn_remote.setToolTip("为其他设备的用户远程激活，需提供目标机器码")
        btn_remote.clicked.connect(self._remote_activate_user)
        search_layout.addWidget(btn_remote)
        btn_unbind = QPushButton("🔓 解绑设备")
        btn_unbind.setStyleSheet("background-color: #9c27b0; color: white; font-weight: bold;")
        btn_unbind.setToolTip("解绑激活码的设备绑定，允许用户重新激活")
        btn_unbind.clicked.connect(self._unbind_device)
        search_layout.addWidget(btn_unbind)
        btn_delete = QPushButton("删除选中")
        btn_delete.setStyleSheet("background-color: #dc3545; color: white;")
        btn_delete.clicked.connect(self.delete_code)
        search_layout.addWidget(btn_delete)
        btn_copy = QPushButton("📋 复制选中激活码")
        btn_copy.setStyleSheet("background-color: #6c757d; color: white;")
        btn_copy.clicked.connect(self._copy_code)
        search_layout.addWidget(btn_copy)
        btn_export = QPushButton("📤 导出全部未使用码")
        btn_export.setStyleSheet("background-color: #6c757d; color: white;")
        btn_export.clicked.connect(self._export_codes)
        search_layout.addWidget(btn_export)
        btn_back = QPushButton("返回主控")
        btn_back.setStyleSheet("background-color: #6c757d; color: white; padding: 8px 20px;")
        btn_back.clicked.connect(self._go_back)
        search_layout.addWidget(btn_back)

        # 表格
        table_group = QGroupBox("激活码列表")
        table_layout = QVBoxLayout(table_group)
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            ["ID", "激活码", "类型", "状态", "绑定账号", "绑定机器", "生成时间", "到期时间", "云同步"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)  # 支持多选
        table_layout.addWidget(self.table)

        layout.addLayout(top_layout)
        layout.addWidget(stats_group)
        layout.addWidget(gen_group)
        layout.addWidget(bind_group)  # 这里修复：用 addWidget 而不是 addLayout
        layout.addLayout(search_layout)
        layout.addWidget(table_group)

    def _open_stats(self):
        from core.modules.account.activation_stats import ActivationStatsWindow
        self._stats_win = ActivationStatsWindow(self)
        self._stats_win.show()

    def _go_back(self):
        self.close()

    def _make_code(self, prefix, length=12):
        raw = secrets.token_hex(length // 2)
        return f"{prefix}-{raw[:4].upper()}-{raw[4:8].upper()}-{raw[8:12].upper()}"

    def _quick_gen(self, count):
        self.count_spin.setCurrentText(str(count))
        self.generate_codes()

    # ====================== 【绑定账号功能】 ======================
    def bind_selected_code(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中一个激活码！")
            return
        
        account = self.bind_account_input.text().strip()
        if not account:
            QMessageBox.warning(self, "提示", "请输入要绑定的用户名！")
            return

        code = self.table.item(row, 1).text()
        result = bind_account(code, account)
        if result["ok"]:
            self.load_codes()
            QMessageBox.information(self, "成功", f"激活码已绑定到用户：{account}")

    def unbind_selected_code(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中一个激活码！")
            return

        code = self.table.item(row, 1).text()
        result = unbind_account(code)
        if result["ok"]:
            self.load_codes()
            QMessageBox.information(self, "成功", "已清空该激活码的账号绑定")
    # =============================================================

    def generate_codes(self):
        user_type = self.type_combo.currentData()
        count = int(self.count_spin.currentText())
        note = self.gen_note_input.text().strip()
        info = CODE_TYPES[user_type]

        results = generate_codes(count, user_type, note)

        self.gen_note_input.clear()
        self.load_codes()

        created = len(results)
        failed = count - created
        msg = f"已生成 {created} 个【{info['name']}】激活码"
        if failed:
            msg += f"\n失败 {failed} 个"
        QMessageBox.information(self, "成功", msg)

    def load_codes(self, keyword=""):
        if not keyword:
            keyword = self.search_input.text().strip()
        filter_status = self.filter_combo.currentText()
        status_filter = None if filter_status == "全部" else filter_status

        rows, stats = get_codes(keyword=keyword, status_filter=status_filter)

        total = sum(stats.values())
        self.total_label.setText(f"总: {total}")
        self.unused_label.setText(f"未使用: {stats.get('unused', 0)}")
        self.used_label.setText(f"已激活: {stats.get('used', 0)}")
        self.expired_label.setText(f"已过期: {stats.get('expired', 0)}")

        status_text = {"unused": "未使用", "used": "已激活", "expired": "已过期"}
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            vals = [r["id"], r["code"], r["user_type"], r["status"],
                    r.get("bound_account", ""), r.get("bound_machine", ""),
                    r.get("created_at", ""), r.get("expires_at", "")]
            for j, val in enumerate(vals):
                item = QTableWidgetItem()
                if j == 1:
                    item.setText(_format_code(str(val)))
                elif j == 2:
                    item.setText(CODE_TYPES.get(val, {}).get("name", str(val)))
                elif j == 3:
                    item.setText(status_text.get(val, str(val)))
                    item.setForeground(Qt.red if val == "expired" else Qt.green)
                elif j == 6 or j == 7:
                    item.setText(str(val) if val else "-")
                else:
                    item.setText(str(val) if val else "-")
                self.table.setItem(i, j, item)
            # 云同步状态列
            sync_item = QTableWidgetItem()
            status_val = r.get("status", "")
            if status_val == "used":
                sync_item.setText("☁️")
                sync_item.setForeground(Qt.darkBlue)
            else:
                sync_item.setText("📍")
                sync_item.setForeground(Qt.darkGray)
            sync_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 8, sync_item)

    def search_codes(self):
        self.load_codes(self.search_input.text().strip())

    def _activate_user(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中一行激活码")
            return

        code_raw = self.table.item(row, 1).text().strip()
        if not code_raw:
            QMessageBox.warning(self, "错误", "激活码为空，请选择有效记录")
            return

        username, ok = QInputDialog.getText(self, "激活用户", f"请输入要激活的用户名\n激活码: {code_raw}")
        if not ok or not username.strip():
            return
        username = username.strip()

        code_info = get_code_by_raw(code_raw)
        if not code_info:
            QMessageBox.warning(self, "错误", f"激活码 {code_raw} 不存在")
            return

        code_type = code_info["user_type"]
        code_type_name = CODE_TYPES.get(code_type, {}).get("name", code_type)

        from core.modules.account.license_local import activate_license

        ok_result, msg = activate_license(code_raw, username)
        if ok_result:
            mark_used(code_raw, username)
            QMessageBox.information(self, "激活成功",
                f"用户: {username}\n类型: {code_type_name}\n\n请让用户重新登录")
            self.load_codes()
        else:
            QMessageBox.warning(self, "激活失败", msg)

    def _copy_code(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中一行")
            return
        code = self.table.item(row, 1).text()
        clipboard = QApplication.clipboard()
        clipboard.setText(code)
        QMessageBox.information(self, "已复制", f"激活码 {code} 已复制到剪贴板")

    def _export_codes(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出未使用激活码", "激活码导出.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        rows = get_unused_codes()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["激活码", "类型", "生成时间"])
            for r in rows:
                writer.writerow([_format_code(r["code"]), CODE_TYPES.get(r["user_type"], {}).get("name", r["user_type"]), r.get("created_at", "")])
        QMessageBox.information(self, "导出成功", f"已导出 {len(rows)} 个未使用激活码到：\n{path}")

    def delete_code(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "提示", "请先选中要删除的激活码")
            return
        if QMessageBox.Yes != QMessageBox.question(
            self, "确认删除激活码记录",
            f"确定删除选中的 {len(rows)} 个激活码记录？\n\n"
            f"⚠️ 注意：\n"
            f"  • 仅删除你的激活码台账记录\n"
            f"  • 不会影响已激活用户的登录和会员权限\n"
            f"  • 删除后无法追溯该码的使用情况"
        ):
            return
        ids = [int(self.table.item(r.row(), 0).text()) for r in rows]
        result = delete_codes(ids)
        self.load_codes()
        QMessageBox.information(self, "成功", f"已删除 {result['deleted']} 个激活码")

    def _reset_admin(self):
        reply = QMessageBox.question(
            self, "⚠️ 危险操作",
            "确定要重置管理员密码吗？\n这将清除所有管理员账号数据！",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        new_pwd, ok = QInputDialog.getText(
            self, "重置管理员密码",
            "请输入新的管理员密码：",
            QLineEdit.Password
        )
        if not ok or not new_pwd:
            return
        confirm_pwd, ok = QInputDialog.getText(
            self, "确认密码",
            "请再次输入新密码：",
            QLineEdit.Password
        )
        if not ok or confirm_pwd != new_pwd:
            QMessageBox.warning(self, "错误", "两次输入的密码不一致！")
            return
        try:
            init_activation_db()
            hashed_pwd = hashlib.sha256(new_pwd.encode()).hexdigest()
            result = reset_admin_password(hashed_pwd)
            if result["ok"]:
                QMessageBox.information(self, "成功", "管理员密码已重置！\n新账号：admin")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重置失败：{str(e)}")
    def _test_cloud(self):
        try:
            from core.supabase_client import _request
            ok, data = _request("GET", "/rest/v1/activation_codes?select=code&limit=1", service_key=True)
            if ok and isinstance(data, list):
                self.cloud_status.setText(f"🟢 云端已连接 ({len(data)} 条)")
                self.cloud_status.setStyleSheet("color: #38a169; font-size: 13px;")
                QMessageBox.information(self, "云端状态", "Supabase 云端连接正常。")
            else:
                self.cloud_status.setText("🟡 云端异常")
                self.cloud_status.setStyleSheet("color: #d69e2e; font-size: 13px;")
                QMessageBox.warning(self, "云端状态", "云端返回异常，请检查 Supabase 配置。")
        except Exception as e:
            self.cloud_status.setText("🔴 云端不可达")
            self.cloud_status.setStyleSheet("color: #e53e3e; font-size: 13px;")
            QMessageBox.critical(self, "云端状态", f"无法连接云端：{str(e)[:200]}")

    def _sync_all_to_cloud(self):
        """同步所有激活码到云端"""
        try:
            from core.simple_sync import push_to_cloud
            ok = push_to_cloud("activation_codes")
            if ok:
                self.cloud_status.setText("🟢 已同步")
                self.cloud_status.setStyleSheet("color: #38a169; font-size: 13px;")
                QMessageBox.information(self, "同步成功", "激活码已同步到云端。")
            else:
                self.cloud_status.setText("🔴 同步失败")
                self.cloud_status.setStyleSheet("color: #e53e3e; font-size: 13px;")
                QMessageBox.warning(self, "同步失败", "激活码同步失败，请检查网络连接后重试。")
        except Exception as e:
            self.cloud_status.setText("🔴 同步异常")
            self.cloud_status.setStyleSheet("color: #e53e3e; font-size: 13px;")
            QMessageBox.critical(self, "同步异常", f"同步出错：{str(e)[:200]}")
    def _open_cloud_manager(self):
        QMessageBox.information(self, "提示", "宇宙版云端管理面板暂未开放。")

    def _remote_activate_user(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中一行激活码")
            return

        code_raw = self.table.item(row, 1).text()
        code_info = get_code_by_raw(code_raw)
        if not code_info:
            QMessageBox.warning(self, "错误", f"激活码 {code_raw} 不存在")
            return

        code_type = code_info["user_type"]
        status = code_info["status"]
        bound_account = code_info.get("bound_account", "")
        code_type_name = CODE_TYPES.get(code_type, {}).get("name", code_type)

        from core.modules.account.license_local import activate_license

        dlg = QDialog(self)
        dlg.setWindowTitle("🌐 远程激活")
        dlg.setFixedSize(440, 260)
        dlg.setStyleSheet("")
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)
        info = QLabel(f"激活码: {code_raw}\n类型: {code_type_name}\n状态: {status}")
        info.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(info)
        form = QFormLayout()
        username_input = QLineEdit()
        username_input.setPlaceholderText("目标用户的登录账号")
        if bound_account:
            username_input.setText(bound_account)
        form.addRow("用户名:", username_input)
        machine_input = QLineEdit()
        machine_input.setPlaceholderText("目标设备的32位机器码")
        form.addRow("机器码:", machine_input)
        layout.addLayout(form)
        hint = QLabel("💡 让用户在升级会员窗口复制机器码发给你")
        hint.setStyleSheet("color: #fbbf24; font-size: 11px;")
        layout.addWidget(hint)
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("取消")
        btn_cancel.setObjectName("cancel")
        btn_cancel.clicked.connect(dlg.reject)
        btn_row.addWidget(btn_cancel)
        btn_ok = QPushButton("🌐 远程激活")
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

        def do_remote():
            username = username_input.text().strip()
            machine_code = machine_input.text().strip()
            if not username:
                QMessageBox.warning(dlg, "提示", "请输入用户名！")
                return
            if not machine_code or len(machine_code) < 8:
                QMessageBox.warning(dlg, "提示", "请输入有效的机器码（至少8位）！")
                return
            ok_result, msg = activate_license(code_raw, username, machine_code=machine_code)
            if ok_result:
                mark_used(code_raw, username, machine_code)
                QMessageBox.information(dlg, "激活成功",
                    f"用户 {username} 已在设备 {machine_code[:8]}... 上激活成功！\n\n请通知用户重新登录。")
                dlg.accept()
                self.load_codes()
            else:
                QMessageBox.warning(dlg, "激活失败", msg)
        btn_ok.clicked.connect(do_remote)
        dlg.exec_()

    def _unbind_device(self):
        """解绑设备"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中一行激活码")
            return
        code_raw = self.table.item(row, 1).text()
        reply = QMessageBox.question(
            self, "确认解绑",
            f"确定要解绑激活码 {code_raw} 的设备绑定吗？\n\n解绑后，该用户可以在新设备上重新激活。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            result = unbind_machine(code_raw)
            if result["ok"]:
                QMessageBox.information(self, "解绑成功", f"激活码 {code_raw} 已解绑设备！")
                self.load_codes()
        except Exception as e:
            QMessageBox.critical(self, "解绑失败", f"解绑出错：{str(e)}")