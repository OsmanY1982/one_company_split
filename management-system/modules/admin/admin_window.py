# -*- coding: utf-8 -*-

import os

from core.paths import DATA_DIR, BASE_DIR

import sqlite3

from datetime import datetime

from PyQt5.QtWidgets import (

    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,

    QLabel, QPushButton, QTableWidget, QTableWidgetItem,

    QGroupBox, QComboBox, QLineEdit, QMessageBox, QHeaderView, QTextEdit,

    QInputDialog

)

from PyQt5.QtCore import Qt, QTimer

from PyQt5.QtGui import QFont



from core.dark_theme import apply_dark_theme, BG_MAIN, BG_CARD, BG_INPUT, BTN_NORMAL, BTN_HOVER, BTN_PRESSED, TEXT_WHITE, TEXT_LIGHT, TEXT_MUTED, ACCENT, SUCCESS, WARNING, DANGER, BORDER, BORDER_LIGHT
DB_FILE = os.path.join(DATA_DIR, "admin.db")



class AdminWindow(QMainWindow):

    def __init__(self, parent=None):

        try:

            super().__init__(parent)
            apply_dark_theme(self)

            self.setWindowTitle("后台管理")

            self.setMinimumSize(1000, 700)

            self.init_db()

            self.init_ui()

        except Exception as e:

            import traceback

            print("=== AdminWindow.__init__ 崩溃 ===")

            traceback.print_exc()

            raise



    def init_db(self):
        from modules.admin import admin_service
        admin_service.init_db()

    def init_ui(self):

        central = QWidget()

        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        layout.setContentsMargins(20, 20, 20, 20)



        # 标题栏

        top_layout = QHBoxLayout()

        title = QLabel("后台管理")

        title.setFont(QFont("PingFang SC", 18, QFont.Bold))

        title.setStyleSheet("color: #ddaaff; background: transparent;")

        top_layout.addWidget(title)

        top_layout.addStretch()

        self.tab_combo = QComboBox()

        self.tab_combo.addItems(["用户管理", "激活码管理", "业务数据", "系统设置", "操作日志", "数据管理", "备份设置"])

        self.tab_combo.setStyleSheet(
            "background-color: #1a1a4e; color: white; border: 1px solid #3a3a7e; "
            "border-radius: 4px; padding: 6px 12px;"
        )

        self.tab_combo.currentIndexChanged.connect(self.switch_tab)

        top_layout.addWidget(self.tab_combo)

        btn_back = QPushButton("返回主控")

        btn_back.setStyleSheet(
            "background-color: #3a3a5e; color: white; padding: 8px 20px; "
            "border-radius: 5px; border: none;"
        )

        btn_back.clicked.connect(self._go_back)

        top_layout.addWidget(btn_back)

        layout.addLayout(top_layout)



        # Tab容器

        from PyQt5.QtWidgets import QStackedWidget

        self.tab_widget = QStackedWidget()

        layout.addWidget(self.tab_widget)

        self.tab_layouts = {}



        # 用户管理

        self._init_user_tab()



        # 激活码管理

        self._init_activation_tab()



        # 业务数据

        self._init_data_mgmt_tab()



        # 系统设置

        self._init_settings_tab()



        # 操作日志

        self._init_log_tab()



        # 数据管理

        self._init_data_tab()



        # 备份设置

        self._init_backup_settings_tab()



    def _go_back(self):

        from core.module_manager import module_manager

        from PyQt5.QtCore import QTimer

        QTimer.singleShot(0, lambda: module_manager.switch_module("dashboard"))



    def switch_tab(self, idx):

        self.tab_widget.setCurrentIndex(idx)



    # ==================== 用户管理 ====================

    def _init_user_tab(self):

        from modules.admin.admin_user import AdminUserWidget

        self.user_widget = AdminUserWidget()

        self.tab_widget.addWidget(self.user_widget)



    def _init_activation_tab(self):

        from modules.admin.admin_activation import AdminActivationWidget

        self.activation_widget = AdminActivationWidget()

        self.tab_widget.addWidget(self.activation_widget)



    def _init_data_mgmt_tab(self):

        from modules.admin.admin_data_mgmt import AdminDataMgmtWidget

        self.data_mgmt_widget = AdminDataMgmtWidget()

        self.tab_widget.addWidget(self.data_mgmt_widget)



    # ==================== 委托 ====================

    def _load_users(self):

        if hasattr(self, 'user_widget'):

            self.user_widget.load_users()



    def _add_user(self):

        if hasattr(self, 'user_widget'):

            self.user_widget.add_user()



    def _load_users_list(self):

        self._load_users()



    def _load_activation_codes(self):

        if hasattr(self, 'activation_widget'):

            self.activation_widget.load_codes()



    def _generate_activation_codes(self):

        if hasattr(self, 'activation_widget'):

            self.activation_widget.generate_codes()



    # ==================== 系统设置 ====================

    def _init_settings_tab(self):
        from modules.admin.admin_settings import AdminSettingsWidget
        self.settings_widget = AdminSettingsWidget()
        self.tab_widget.addWidget(self.settings_widget)

    # ==================== 操作日志 ====================

    def _init_log_tab(self):

        from modules.admin.admin_log import AdminLogWidget

        self.log_widget = AdminLogWidget()

        self.tab_widget.addWidget(self.log_widget)



    def _load_logs(self):

        if hasattr(self, 'log_widget'):

            self.log_widget.load_logs()



    def _log_action(self, user, action, detail=""):

        try:

            from core.operation_log import log_action

            log_action(user, action, "admin", detail)

        except Exception: pass



    # ==================== 数据管理 ====================

    def _init_data_tab(self):
        from modules.admin.admin_data import AdminDataWidget
        self.data_widget = AdminDataWidget()
        self.tab_widget.addWidget(self.data_widget)

    # ==================== 备份设置 ====================

    def _init_backup_settings_tab(self):
        from modules.admin.admin_backup import AdminBackupWidget
        self.backup_widget = AdminBackupWidget()
        self.tab_widget.addWidget(self.backup_widget)

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication

    app = QApplication([])

    win = AdminWindow()

    win.show()

    app.exec_()
