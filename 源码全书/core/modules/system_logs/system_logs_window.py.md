# `core/modules/system_logs/system_logs_window.py`

> 路径：`core/modules/system_logs/system_logs_window.py` | 行数：463


---


```python
# -*- coding: utf-8 -*-
"""
系统日志管理模块（宇宙版）
功能：查看系统操作日志、同步状态、错误日志

从桌面版移植，适配宇宙版 core.paths / core.database 路径体系。
"""
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDateEdit, QGroupBox, QMessageBox, QTabWidget,
    QTextEdit, QSplitter
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

from core.module_manager import module_manager
from core.modules.system_logs.system_logs_service import (
    get_operation_logs, get_last_sync, get_sync_records,
    get_error_stats, get_error_logs, clear_old_logs, check_cloud_connection,
    init_error_logs_db
)


class SystemLogsWindow(QMainWindow):
    """系统日志管理窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统日志管理")
        self.setMinimumSize(1000, 700)
        self._build_ui()
        self._load_logs()

    def _build_ui(self):
        """构建界面"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("系统日志管理")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 4px;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                background: #f5f5f5;
            }
            QTabBar::tab:selected {
                background: white;
                font-weight: bold;
            }
        """)

        # 操作日志标签
        self._build_operation_log_tab()

        # 同步状态标签
        self._build_sync_status_tab()

        # 错误日志标签
        self._build_error_log_tab()

        layout.addWidget(self.tabs)

        # 底部按钮
        btn_layout = QHBoxLayout()

        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet(self._btn_style("#3182ce"))
        refresh_btn.clicked.connect(self._load_logs)
        btn_layout.addWidget(refresh_btn)

        clear_btn = QPushButton("清理旧日志")
        clear_btn.setStyleSheet(self._btn_style("#e53e3e"))
        clear_btn.clicked.connect(self._clear_old_logs)
        btn_layout.addWidget(clear_btn)

        export_btn = QPushButton("导出日志")
        export_btn.setStyleSheet(self._btn_style("#38a169"))
        export_btn.clicked.connect(self._export_logs)
        btn_layout.addWidget(export_btn)

        btn_layout.addStretch()

        back_btn = QPushButton("返回")
        back_btn.setStyleSheet(self._btn_style("#718096"))
        back_btn.clicked.connect(self._go_back)
        btn_layout.addWidget(back_btn)

        layout.addLayout(btn_layout)

    def _build_operation_log_tab(self):
        """构建操作日志标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 筛选栏
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("操作类型:"))
        self.op_type_combo = QComboBox()
        self.op_type_combo.addItems(["全部", "登录", "登出", "添加", "修改", "删除", "同步", "备份", "恢复"])
        self.op_type_combo.currentTextChanged.connect(self._filter_logs)
        filter_layout.addWidget(self.op_type_combo)

        filter_layout.addWidget(QLabel("日期范围:"))
        self.op_date_from = QDateEdit()
        self.op_date_from.setCalendarPopup(True)
        self.op_date_from.setDate(QDate.currentDate().addDays(-7))
        filter_layout.addWidget(self.op_date_from)

        filter_layout.addWidget(QLabel("至"))
        self.op_date_to = QDateEdit()
        self.op_date_to.setCalendarPopup(True)
        self.op_date_to.setDate(QDate.currentDate())
        filter_layout.addWidget(self.op_date_to)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # 日志表格
        self.op_table = QTableWidget()
        self.op_table.setColumnCount(6)
        self.op_table.setHorizontalHeaderLabels(["ID", "时间", "用户", "操作", "模块", "详情"])
        self.op_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.op_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.op_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                background: white;
            }
            QHeaderView::section {
                background: #f7fafc;
                padding: 8px;
                font-weight: bold;
                border: 1px solid #e2e8f0;
            }
        """)
        layout.addWidget(self.op_table)

        self.tabs.addTab(tab, "操作日志")

    def _build_sync_status_tab(self):
        """构建同步状态标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 同步状态概览
        status_group = QGroupBox("同步状态概览")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        status_layout = QHBoxLayout(status_group)

        self.sync_status_labels = {}
        sync_items = [
            ("云端连接", "cloud"),
            ("最后同步", "last_sync"),
            ("同步状态", "status"),
            ("待同步数", "pending"),
        ]

        for title, key in sync_items:
            item = QVBoxLayout()
            label = QLabel(title)
            label.setStyleSheet("color: #666; font-size: 12px;")
            item.addWidget(label)

            value = QLabel("--")
            value.setStyleSheet("font-size: 16px; font-weight: bold; color: #3182ce;")
            item.addWidget(value)

            status_layout.addLayout(item)
            self.sync_status_labels[key] = value

        status_layout.addStretch()
        layout.addWidget(status_group)

        # 同步记录表格
        self.sync_table = QTableWidget()
        self.sync_table.setColumnCount(5)
        self.sync_table.setHorizontalHeaderLabels(["时间", "表名", "方向", "记录数", "状态"])
        self.sync_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sync_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                background: white;
            }
        """)
        layout.addWidget(self.sync_table)

        # 手动同步按钮
        sync_btn_layout = QHBoxLayout()

        sync_up_btn = QPushButton("同步到云端")
        sync_up_btn.setStyleSheet(self._btn_style("#3182ce"))
        sync_up_btn.clicked.connect(self._sync_to_cloud)
        sync_btn_layout.addWidget(sync_up_btn)

        sync_down_btn = QPushButton("从云端同步")
        sync_down_btn.setStyleSheet(self._btn_style("#38a169"))
        sync_down_btn.clicked.connect(self._sync_from_cloud)
        sync_btn_layout.addWidget(sync_down_btn)

        sync_btn_layout.addStretch()
        layout.addLayout(sync_btn_layout)

        self.tabs.addTab(tab, "同步状态")

    def _build_error_log_tab(self):
        """构建错误日志标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 错误统计
        stats_layout = QHBoxLayout()

        self.error_stats = {}
        for title, key, color in [
            ("今日错误", "today", "#e53e3e"),
            ("本周错误", "week", "#dd6b20"),
            ("未处理", "unhandled", "#805ad5"),
        ]:
            group = QGroupBox(title)
            group.setStyleSheet(f"""
                QGroupBox {{
                    font-weight: bold;
                    color: {color};
                    border: 2px solid {color}22;
                    border-radius: 4px;
                }}
            """)
            g_layout = QVBoxLayout(group)

            label = QLabel("0")
            label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
            label.setAlignment(Qt.AlignCenter)
            g_layout.addWidget(label)

            stats_layout.addWidget(group)
            self.error_stats[key] = label

        layout.addLayout(stats_layout)

        # 错误日志表格
        self.error_table = QTableWidget()
        self.error_table.setColumnCount(5)
        self.error_table.setHorizontalHeaderLabels(["时间", "级别", "模块", "错误信息", "堆栈"])
        self.error_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.error_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                background: white;
            }
        """)
        layout.addWidget(self.error_table)

        self.tabs.addTab(tab, "错误日志")

    def _load_logs(self):
        """加载所有日志数据"""
        self._load_operation_logs()
        self._load_sync_status()
        self._load_error_logs()

    def _load_operation_logs(self):
        """加载操作日志"""
        try:
            op_type = self.op_type_combo.currentText()
            date_from = self.op_date_from.date().toString("yyyy-MM-dd")
            date_to = self.op_date_to.date().toString("yyyy-MM-dd")
            rows = get_operation_logs(op_type=op_type, date_from=date_from, date_to=date_to)

            self.op_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    item = QTableWidgetItem(str(val) if val else "")
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.op_table.setItem(i, j, item)

        except Exception as e:
            print(f"加载操作日志失败: {e}")

    def _load_sync_status(self):
        """加载同步状态"""
        try:
            # 最近同步时间
            last_sync = get_last_sync()
            if last_sync:
                self.sync_status_labels["last_sync"].setText(str(last_sync.get("created_at", ""))[:16])
                self.sync_status_labels["status"].setText(str(last_sync.get("status", "")))

            # 同步记录
            sync_rows = get_sync_records(50)
            self.sync_table.setRowCount(len(sync_rows))
            for i, r in enumerate(sync_rows):
                vals = [r.get("created_at", ""), r.get("table_name", ""),
                        r.get("direction", ""), r.get("record_count", ""), r.get("status", "")]
                for j, val in enumerate(vals):
                    item = QTableWidgetItem(str(val) if val else "")
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.sync_table.setItem(i, j, item)

            # 云端连接检查
            if check_cloud_connection():
                self.sync_status_labels["cloud"].setText("已连接")
                self.sync_status_labels["cloud"].setStyleSheet("font-size: 16px; font-weight: bold; color: #38a169;")
            else:
                self.sync_status_labels["cloud"].setText("未连接")
                self.sync_status_labels["cloud"].setStyleSheet("font-size: 16px; font-weight: bold; color: #e53e3e;")
        except Exception as e:
            print(f"加载同步状态失败: {e}")

    def _load_error_logs(self):
        """加载错误日志"""
        try:
            init_error_logs_db()
            stats = get_error_stats()
            self.error_stats["today"].setText(str(stats["today"]))
            self.error_stats["week"].setText(str(stats["week"]))
            self.error_stats["unhandled"].setText(str(stats["unhandled"]))

            rows = get_error_logs(50)
            self.error_table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                vals = [r.get("created_at", ""), r.get("level", ""), r.get("module", ""),
                        r.get("message", ""), r.get("stack_trace", "")]
                for j, val in enumerate(vals):
                    item = QTableWidgetItem(str(val)[:200] if val else "")
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.error_table.setItem(i, j, item)
        except Exception as e:
            print(f"加载错误日志失败: {e}")

    def _filter_logs(self):
        """筛选日志"""
        self._load_operation_logs()

    def _clear_old_logs(self):
        """清理旧日志"""
        reply = QMessageBox.question(
            self, "确认清理",
            "确定要清理30天前的日志吗？此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                result = clear_old_logs(30)
                QMessageBox.information(self, "完成", "旧日志已清理")
                self._load_logs()
            except Exception as e:
                QMessageBox.warning(self, "错误", f"清理失败: {e}")

    def _export_logs(self):
        """导出日志"""
        try:
            from PyQt5.QtWidgets import QFileDialog

            filename, _ = QFileDialog.getSaveFileName(
                self, "导出日志",
                f"system_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "文本文件 (*.txt);;CSV文件 (*.csv)"
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=== 系统日志导出 ===\n")
                    f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                    # 导出操作日志
                    f.write("--- 操作日志 ---\n")
                    for row in range(self.op_table.rowCount()):
                        values = []
                        for col in range(self.op_table.columnCount()):
                            item = self.op_table.item(row, col)
                            values.append(item.text() if item else "")
                        f.write(" | ".join(values) + "\n")

                QMessageBox.information(self, "完成", f"日志已导出到:\n{filename}")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"导出失败: {e}")

    def _sync_to_cloud(self):
        """同步到云端"""
        try:
            from core.cloud_sync import sync_all
            sync_all()
            QMessageBox.information(self, "完成", "数据已同步到云端")
            self._load_sync_status()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"同步失败: {e}")

    def _sync_from_cloud(self):
        """从云端同步"""
        try:
            from core.cloud_pull import pull_all
            pull_all()
            QMessageBox.information(self, "完成", "数据已从云端同步")
            self._load_sync_status()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"同步失败: {e}")

    def _go_back(self):
        """返回"""
        self.close()
        module_manager.switch_module("dashboard")

    def _btn_style(self, color):
        """按钮样式"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
        """

```
