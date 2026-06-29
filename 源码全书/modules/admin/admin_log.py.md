# `modules/admin/admin_log.py`

> 路径：`modules/admin/admin_log.py` | 行数：182


---


```python
# -*- coding: utf-8 -*-
"""
后台管理 - 操作日志查看
从 core.operation_log 读取操作日志，支持按用户/模块筛选，支持导出
"""
import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QComboBox, QLineEdit, QFileDialog
)
from PyQt5.QtCore import Qt

from core.operation_log import get_logs


class AdminLogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.load_logs()

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(20, 20, 20, 20)

        # --- 筛选栏 ---
        filter_group = QGroupBox("筛选条件")
        f_layout = QHBoxLayout(filter_group)

        f_layout.addWidget(QLabel("模块:"))
        self.filter_module = QComboBox()
        self.filter_module.addItems(["全部", "企业管理", "用户管理", "系统管理", "数据管理", "备份管理"])
        f_layout.addWidget(self.filter_module)

        f_layout.addWidget(QLabel("操作人:"))
        self.filter_user = QLineEdit()
        self.filter_user.setPlaceholderText("输入操作人")
        self.filter_user.setMaximumWidth(150)
        f_layout.addWidget(self.filter_user)

        btn_search = QPushButton("查询")
        btn_search.setStyleSheet("background-color: #007bff; color: white; padding: 6px 16px;")
        btn_search.clicked.connect(self.load_logs)
        f_layout.addWidget(btn_search)

        btn_export = QPushButton("导出CSV")
        btn_export.setStyleSheet("background-color: #28a745; color: white; padding: 6px 16px;")
        btn_export.clicked.connect(self.export_logs)
        f_layout.addWidget(btn_export)
        f_layout.addStretch()
        main.addWidget(filter_group)

        # --- 表格 ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["时间", "操作人", "操作", "模块", "详情"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        main.addWidget(self.table)

        # --- 底部 ---
        bottom = QHBoxLayout()
        bottom.addStretch()
        self.lbl_count = QLabel("共 0 条记录")
        self.lbl_count.setStyleSheet("color: #a0aec0; font-size: 13px;")
        bottom.addWidget(self.lbl_count)

        btn_clear = QPushButton("清空日志")
        btn_clear.setStyleSheet("background-color: #dc3545; color: white; padding: 6px 16px;")
        btn_clear.clicked.connect(self.clear_logs)
        bottom.addWidget(btn_clear)
        main.addLayout(bottom)

    def load_logs(self):
        module = self.filter_module.currentText()
        user = self.filter_user.text().strip()

        logs = get_logs()
        if not logs:
            self.table.setRowCount(0)
            self.lbl_count.setText("共 0 条记录（core.operation_log 无数据）")
            return

        # 简单筛选
        filtered = []
        for log in logs:
            # log 可能是 dict 或 元组，统一处理
            if isinstance(log, dict):
                mod = log.get("module", "")
                usr = log.get("operator", "")
            else:
                # 假设元组顺序: (id, module, operator, action, ..., detail)
                try:
                    mod = log[3] if len(log) > 3 else ""
                    usr = log[2] if len(log) > 2 else ""
                except:
                    mod, usr = "", ""

            if module and module != "全部" and mod != module:
                continue
            if user and user not in usr:
                continue

            filtered.append(log)

        self.table.setRowCount(len(filtered))
        for i, log in enumerate(filtered):
            if isinstance(log, dict):
                values = [
                    str(log.get("created_at", ""))[:19],
                    log.get("operator", ""),
                    log.get("action", ""),
                    log.get("module", ""),
                    log.get("detail", "")
                ]
            else:
                try:
                    values = [
                        str(log[1])[:19] if log[1] else "",   # 时间
                        str(log[2]) if log[2] else "",        # 操作人
                        str(log[4]) if len(log) > 4 and log[4] else "",  # 操作
                        str(log[3]) if log[3] else "",        # 模块
                        str(log[5]) if len(log) > 5 and log[5] else "",  # 详情
                    ]
                except:
                    values = [str(v)[:50] for v in log]

            for j, v in enumerate(values):
                item = QTableWidgetItem(v)
                if j == 1:
                    item.setForeground(Qt.blue)
                self.table.setItem(i, j, item)

        self.lbl_count.setText(f"共 {len(filtered)} 条记录")

    def clear_logs(self):
        reply = QMessageBox.question(self, "确认", "确定要清空所有操作日志吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "提示", "日志清空需要 core.operation_log 模块支持，请手动删除日志文件或数据库记录。")

    def export_logs(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出日志", "",
                                               "CSV 文件 (*.csv)")
        if not path:
            return
        try:
            import csv
            logs = get_logs()
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["时间", "操作人", "操作", "模块", "详情"])
                for log in logs:
                    if isinstance(log, dict):
                        row = [
                            str(log.get("created_at", ""))[:19],
                            log.get("operator", ""),
                            log.get("action", ""),
                            log.get("module", ""),
                            log.get("detail", "")
                        ]
                    else:
                        try:
                            row = [
                                str(log[1])[:19],
                                str(log[2]),
                                str(log[4]) if len(log) > 4 else "",
                                str(log[3]) if log[3] else "",
                                str(log[5]) if len(log) > 5 else "",
                            ]
                        except:
                            row = [str(v) for v in log]
                    writer.writerow(row)
            QMessageBox.information(self, "成功", f"已导出 {len(logs)} 条日志")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e)[:200])

```
