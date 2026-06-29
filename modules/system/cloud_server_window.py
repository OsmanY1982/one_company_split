# -*- coding: utf-8 -*-
"""
云服务器 · 云端管理 — Supabase 激活码管理、连接测试、云端日志
独立于「云端同步」（数据备份/同步/模型管理），管理云端数据库
"""
import os, json
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QTextEdit, QMessageBox, QComboBox, QSplitter,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
from core.supabase_client import CloudActivation, CloudUser, CloudLog, test_connection
from core.dark_theme import apply_dark_theme, BG_MAIN, BG_CARD, BG_INPUT, BTN_NORMAL, BTN_HOVER, BTN_PRESSED, \
    TEXT_WHITE, TEXT_LIGHT, TEXT_MUTED, ACCENT, SUCCESS, WARNING, DANGER, BORDER, BORDER_LIGHT

LOCAL_DB = os.path.join(DATA_DIR, "activation_admin.db")

# ── 激活码类型（内联，免依赖 license_service）──
CODE_TYPES = {
    "TRIAL": {"name": "体验会员",  "days": 7,   "price": 0,  "features": ["basic"]},
    "PRO":   {"name": "VIP会员",  "days": 365, "price": 49, "features": ["basic"]},
    "VIP":   {"name": "钻石会员",  "days": 0,   "price": 99, "features": ["basic", "quant", "cloud"]},
}


def _normalize(code: str) -> str:
    return code.upper().replace("-", "").replace(" ", "")


def _format_code(code: str) -> str:
    c = _normalize(code)
    if len(c) >= 14:
        prefix = c[:3] if c[:3] in ("VIP", "PRO") else c[:5]
        rest = c[len(prefix):]
        parts = [rest[i:i+4] for i in range(0, len(rest), 4)]
        return f"{prefix}-" + "-".join(parts)
    return code


class CloudFetchThread(QThread):
    finished = pyqtSignal(list, str)  # (codes, error_msg)

    def run(self):
        try:
            codes = CloudActivation.get_all_codes()
            self.finished.emit(codes, "")
        except Exception as e:
            self.finished.emit([], str(e))


class CloudServerWindow(QMainWindow):
    """云服务器管理窗口 — 管理 Supabase 云端激活码、连接状态与日志"""

    def __init__(self, parent=None):
        super().__init__(parent)
        apply_dark_theme(self)
        self.setWindowTitle("云服务器 · 云端管理")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(f"background-color: {BG_MAIN};")
        self._last_codes = []
        self.init_ui()
        self._refresh_cloud()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 顶部状态栏
        status_bar = QHBoxLayout()
        self.conn_label = QLabel("🔄 正在连接云端...")
        self.conn_label.setFont(QFont("PingFang SC", 13))
        self.conn_label.setStyleSheet(f"color: {TEXT_LIGHT};")
        status_bar.addWidget(self.conn_label)
        status_bar.addStretch()

        btn_test = QPushButton("🔗 测试连接")
        btn_test.setStyleSheet(f"""
            QPushButton {{ padding: 6px 16px; background: {BTN_NORMAL}; color: {TEXT_WHITE}; border-radius: 6px; }}
            QPushButton:hover {{ background: {BTN_HOVER}; }}
        """)
        btn_test.clicked.connect(self._test_conn)

        btn_pull = QPushButton("📥 拉取云端")
        btn_pull.setStyleSheet(f"""
            QPushButton {{ background-color: #3182ce; color: white; padding: 6px 16px; font-weight: bold; border-radius: 6px; }}
            QPushButton:hover {{ background-color: #2b6cb0; }}
        """)
        btn_pull.clicked.connect(self._pull_cloud)

        status_bar.addWidget(btn_test)
        status_bar.addWidget(btn_pull)

        # 统计卡片
        stats_group = QGroupBox("📊 云端激活码统计")
        stats_group.setStyleSheet(f"""
            QGroupBox {{ color: {ACCENT}; font-weight: bold; border: 1px solid {BORDER}; border-radius: 8px; margin-top: 10px; padding-top: 16px; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; }}
        """)
        stats_layout = QGridLayout(stats_group)
        self.stat_labels = {}
        for i, (key, label) in enumerate([
            ("total",   "全部"),
            ("unused",  "未使用"),
            ("used",    "已使用"),
        ]):
            card = QWidget()
            card.setStyleSheet(f"background-color: {BG_CARD}; border-radius: 10px; padding: 16px;")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            lbl_title = QLabel(label)
            lbl_title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
            card_layout.addWidget(lbl_title)
            lbl_val = QLabel("0")
            lbl_val.setStyleSheet(f"color: {TEXT_WHITE}; font-size: 28px; font-weight: bold;")
            card_layout.addWidget(lbl_val)
            self.stat_labels[key] = lbl_val
            stats_layout.addWidget(card, 0, i)

        # 操作区
        action_group = QGroupBox("快速操作")
        action_group.setStyleSheet(f"""
            QGroupBox {{ color: {ACCENT}; font-weight: bold; border: 1px solid {BORDER}; border-radius: 8px; margin-top: 10px; padding-top: 16px; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; }}
        """)
        action_layout = QHBoxLayout(action_group)
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["全部激活码", "未使用", "已使用"])
        self.filter_combo.currentTextChanged.connect(self._filter_cloud)
        self.filter_combo.setStyleSheet(f"""
            QComboBox {{ background: {BG_INPUT}; color: {TEXT_WHITE}; border: 1px solid {BORDER}; border-radius: 6px; padding: 6px 12px; }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{ background: {BG_CARD}; color: {TEXT_WHITE}; }}
        """)
        action_layout.addWidget(QLabel("筛选:"))
        action_layout.addWidget(self.filter_combo)
        action_layout.addStretch()
        btn_revoke = QPushButton("🗑️ 删除选中")
        btn_revoke.setStyleSheet(f"""
            QPushButton {{ background-color: {DANGER}; color: white; padding: 6px 16px; border-radius: 6px; }}
            QPushButton:hover {{ background-color: #c53030; }}
        """)
        btn_revoke.clicked.connect(self._delete_selected)
        action_layout.addWidget(btn_revoke)

        # 云端表格
        table_group = QGroupBox("☁️ 云端激活码列表")
        table_group.setStyleSheet(f"""
            QGroupBox {{ color: {ACCENT}; font-weight: bold; border: 1px solid {BORDER}; border-radius: 8px; margin-top: 10px; padding-top: 16px; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; }}
        """)
        table_layout = QVBoxLayout(table_group)
        self.cloud_table = QTableWidget()
        self.cloud_table.setColumnCount(8)
        self.cloud_table.setHorizontalHeaderLabels([
            "ID", "激活码", "类型", "状态", "绑定账号", "绑定机器", "生成时间", "云端ID"
        ])
        self.cloud_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cloud_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cloud_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cloud_table.setStyleSheet(f"""
            QTableWidget {{ background: {BG_CARD}; color: {TEXT_WHITE}; border: 1px solid {BORDER}; gridline-color: {BORDER_LIGHT}; }}
            QTableWidget::item {{ padding: 6px; }}
            QHeaderView::section {{ background: {BG_INPUT}; color: {ACCENT}; border: 1px solid {BORDER_LIGHT}; padding: 6px; font-weight: bold; }}
        """)
        table_layout.addWidget(self.cloud_table)

        # 日志区
        log_group = QGroupBox("操作日志")
        log_group.setStyleSheet(f"""
            QGroupBox {{ color: {ACCENT}; font-weight: bold; border: 1px solid {BORDER}; border-radius: 8px; margin-top: 10px; padding-top: 16px; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 12px; }}
        """)
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(160)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(f"background-color: #1a202c; color: #68d391; font-family: Menlo; font-size: 12px;")
        log_layout.addWidget(self.log_text)

        layout.addLayout(status_bar)
        layout.addWidget(stats_group)
        layout.addWidget(action_group)
        layout.addWidget(table_group)
        layout.addWidget(log_group)

    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {msg}")

    def _test_conn(self):
        ok, msg = test_connection()
        if ok:
            self.conn_label.setText("✅ 云端已连接")
            self.conn_label.setStyleSheet(f"color: {SUCCESS}; font-weight: bold;")
            QMessageBox.information(self, "连接测试", msg)
        else:
            self.conn_label.setText("❌ 连接失败")
            self.conn_label.setStyleSheet(f"color: {DANGER};")
            QMessageBox.warning(self, "连接失败", f"错误信息：{msg}")

    def _refresh_cloud(self, codes=None):
        if codes is None:
            self._pull_cloud()
            return

        self._last_codes = codes
        filter_text = self.filter_combo.currentText()
        if filter_text == "未使用":
            codes = [c for c in codes if c.get("status") == "unused"]
        elif filter_text == "已使用":
            codes = [c for c in codes if c.get("status") == "used"]

        # 统计
        total = len(self._last_codes)
        unused = sum(1 for c in self._last_codes if c.get("status") == "unused")
        used = sum(1 for c in self._last_codes if c.get("status") == "used")
        self.stat_labels["total"].setText(str(total))
        self.stat_labels["unused"].setText(str(unused))
        self.stat_labels["used"].setText(str(used))

        # 填充表格
        self.cloud_table.setRowCount(len(codes))
        for i, code in enumerate(codes):
            vals = [
                str(code.get("id", "")),
                _format_code(code.get("code", "")),
                CODE_TYPES.get(code.get("user_type", ""), {}).get("name", code.get("user_type", "")),
                "未使用" if code.get("status") == "unused" else "已使用" if code.get("status") == "used" else code.get("status", ""),
                code.get("bound_account", "-"),
                code.get("bound_machine", "-")[:16] + "..." if code.get("bound_machine") and len(str(code.get("bound_machine"))) > 16 else code.get("bound_machine", "-"),
                code.get("created_at", "-"),
                str(code.get("id", "")),
            ]
            for j, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if j == 3:
                    item.setForeground(Qt.green if v == "未使用" else Qt.blue)
                self.cloud_table.setItem(i, j, item)

    def _pull_cloud(self):
        self.conn_label.setText("🔄 正在拉取云端数据...")
        self.conn_label.setStyleSheet(f"color: {WARNING};")
        self._log("开始拉取云端激活码...")
        self.thread = CloudFetchThread()
        self.thread.finished.connect(self._on_pull_done)
        self.thread.start()

    def _on_pull_done(self, codes, err):
        if err:
            self.conn_label.setText("❌ 拉取失败")
            self.conn_label.setStyleSheet(f"color: {DANGER};")
            self._log(f"拉取失败：{err}")
            QMessageBox.warning(self, "拉取失败", err)
        else:
            self.conn_label.setText(f"✅ 云端已连接 ({len(codes)} 条)")
            self.conn_label.setStyleSheet(f"color: {SUCCESS}; font-weight: bold;")
            self._log(f"拉取成功：{len(codes)} 条")
            self._refresh_cloud(codes)

    def _filter_cloud(self):
        self._refresh_cloud(self._last_codes)

    def _delete_selected(self):
        rows = self.cloud_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "提示", "请先选中要删除的激活码")
            return
        if QMessageBox.No == QMessageBox.question(
            self, "确认删除",
            f"确定从云端删除选中的 {len(rows)} 个激活码？\n此操作不可撤销。",
        ):
            return
        deleted = 0
        for row in rows:
            code = self.cloud_table.item(row.row(), 1).text().replace("-", "")
            ok, _ = CloudActivation.delete_code(code)
            if ok:
                deleted += 1
            self._log(f"删除 {'成功' if ok else '失败'}：{code}")
        QMessageBox.information(self, "完成", f"成功删除 {deleted}/{len(rows)} 个")
        self._pull_cloud()
