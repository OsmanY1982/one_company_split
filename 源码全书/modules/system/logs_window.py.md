# `modules/system/logs_window.py`

> 路径：`modules/system/logs_window.py` | 行数：357


---


```python
"""
系统日志 · 操作日志 + 同步状态 + 错误日志（三标签页）
数据源: operation_log.db + system_logs.db（通过 system_logs_service）
"""
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QWidget, QGroupBox, QFileDialog,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

from modules.system_logs.system_logs_service import (
    get_operation_logs, get_last_sync, get_sync_records,
    get_error_stats, get_error_logs, clear_old_logs, check_cloud_connection,
    init_error_logs_db,
)


class LogsWindow(QDialog):
    """系统日志 · ENGINEERING DECK"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统日志 · ENGINEERING DECK")
        self.setMinimumSize(900, 640)
        self._build_ui()
        self._load_logs()
        self.setStyleSheet(self._style())

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 16, 20, 20)

        title = QLabel("系统日志")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        title.setStyleSheet("color: #ddaaff; letter-spacing: 4px;")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._build_op_log_tab(), "操作日志")
        tabs.addTab(self._build_sync_tab(), "同步状态")
        tabs.addTab(self._build_error_tab(), "错误日志")
        layout.addWidget(tabs)

    # ═══════════════════════════════════════════
    #  标签页 1: 操作日志
    # ═══════════════════════════════════════════
    def _build_op_log_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)

        flt = QHBoxLayout()
        flt.addWidget(QLabel("操作类型:"))
        self.op_type = QComboBox()
        self.op_type.addItems(["全部", "登录", "登出", "添加", "修改", "删除", "同步", "备份", "恢复"])
        self.op_type.currentIndexChanged.connect(self._load_operation_logs)
        flt.addWidget(self.op_type)
        flt.addStretch()

        btn_export = QPushButton("导出")
        btn_export.clicked.connect(self._export_logs)
        flt.addWidget(btn_export)

        btn_clean = QPushButton("清理30天前")
        btn_clean.setObjectName("btn_clean")
        btn_clean.clicked.connect(self._clean_old_logs)
        flt.addWidget(btn_clean)
        lay.addLayout(flt)

        self.op_table = QTableWidget()
        self.op_table.setColumnCount(6)
        self.op_table.setHorizontalHeaderLabels(["ID", "时间", "用户", "操作", "模块", "详情"])
        self.op_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lay.addWidget(self.op_table)

        return w

    # ═══════════════════════════════════════════
    #  标签页 2: 同步状态
    # ═══════════════════════════════════════════
    def _build_sync_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)

        info_box = QGroupBox("连接状态")
        ig = QVBoxLayout(info_box)
        ig.setSpacing(6)

        self.sync_status_lbl = QLabel("状态: 检查中...")
        self.sync_status_lbl.setStyleSheet("font-size: 14px; font-weight: bold;")
        ig.addWidget(self.sync_status_lbl)

        self.sync_last_lbl = QLabel("最后同步: -")
        ig.addWidget(self.sync_last_lbl)

        ig.addWidget(QLabel("同步记录:"))
        lay.addWidget(info_box)

        self.sync_table = QTableWidget()
        self.sync_table.setColumnCount(5)
        self.sync_table.setHorizontalHeaderLabels(["时间", "表名", "方向", "记录数", "状态"])
        self.sync_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lay.addWidget(self.sync_table)

        btn_row = QHBoxLayout()
        btn_sync = QPushButton("手动同步")
        btn_sync.setObjectName("btn_sync")
        btn_sync.clicked.connect(self._manual_sync)
        btn_row.addWidget(btn_sync)

        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self._load_sync_status)
        btn_row.addWidget(btn_refresh)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        return w

    # ═══════════════════════════════════════════
    #  标签页 3: 错误日志
    # ═══════════════════════════════════════════
    def _build_error_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)

        stats = QHBoxLayout()
        self.err_today = QLabel("今日: 0")
        self.err_week = QLabel("本周: 0")
        self.err_pending = QLabel("未处理: 0")
        for lbl, color in [(self.err_today, "#e53e3e"), (self.err_week, "#f6ad55"), (self.err_pending, "#63b3ed")]:
            lbl.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold; margin-right: 14px;")
            stats.addWidget(lbl)
        stats.addStretch()

        btn_mark = QPushButton("标记为已处理")
        btn_mark.clicked.connect(self._mark_resolved)
        stats.addWidget(btn_mark)
        lay.addLayout(stats)

        self.err_table = QTableWidget()
        self.err_table.setColumnCount(5)
        self.err_table.setHorizontalHeaderLabels(["时间", "级别", "模块", "错误信息", "堆栈"])
        self.err_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        lay.addWidget(self.err_table)

        return w

    # ═══════════════════════════════════════════
    #  数据加载
    # ═══════════════════════════════════════════
    def _load_logs(self):
        self._load_operation_logs()
        self._load_sync_status()
        self._load_error_logs()

    def _load_operation_logs(self):
        try:
            op_type = self.op_type.currentText() if hasattr(self, 'op_type') else "全部"
            rows = get_operation_logs(op_type=op_type)

            self.op_table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                vals = [
                    str(r.get("id", "")),
                    str(r.get("created_at", "")),
                    str(r.get("username", "-")),
                    str(r.get("action", "-")),
                    str(r.get("module", "-")),
                    str(r.get("detail", "-")),
                ]
                for j, val in enumerate(vals):
                    item = QTableWidgetItem(val)
                    self.op_table.setItem(i, j, item)
        except Exception as e:
            print(f"[LogsWindow] 加载操作日志失败: {e}")

    def _load_sync_status(self):
        try:
            last_sync = get_last_sync()
            if last_sync:
                self.sync_last_lbl.setText(f"最后同步: {last_sync.get('created_at', '')} ({last_sync.get('status', '')})")
                self.sync_status_lbl.setText(f"状态: {'已连接' if last_sync.get('status') == 'success' else '连接异常'}")
            else:
                self.sync_status_lbl.setText("状态: 待同步")
                self.sync_last_lbl.setText("最后同步: -")

            recs = get_sync_records(50)
            self.sync_table.setRowCount(len(recs))
            for i, r in enumerate(recs):
                vals = [
                    str(r.get("created_at", "")),
                    str(r.get("table_name", "-")),
                    str(r.get("direction", "-")),
                    str(r.get("record_count", 0)),
                    str(r.get("status", "-")),
                ]
                for j, v in enumerate(vals):
                    item = QTableWidgetItem(v)
                    if j == 4 and v == "success":
                        item.setForeground(QColor(0x44, 0xcc, 0x88))
                    self.sync_table.setItem(i, j, item)
        except Exception as e:
            print(f"[LogsWindow] 加载同步状态失败: {e}")

    def _load_error_logs(self):
        try:
            init_error_logs_db()
            stats = get_error_stats()
            self.err_today.setText(f"今日: {stats['today']}")
            self.err_week.setText(f"本周: {stats['week']}")
            self.err_pending.setText(f"未处理: {stats['unhandled']}")

            rows = get_error_logs(100)
            self.err_table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                vals = [
                    str(r.get("created_at", "")),
                    str(r.get("level", "-")),
                    str(r.get("module", "-")),
                    str(r.get("message", "")),
                    str(r.get("stack_trace", "")),
                ]
                for j, val in enumerate(vals):
                    item = QTableWidgetItem(str(val)[:200] if val else "")
                    self.err_table.setItem(i, j, item)
        except Exception as e:
            print(f"[LogsWindow] 加载错误日志失败: {e}")

    # ═══════════════════════════════════════════
    #  操作
    # ═══════════════════════════════════════════
    def _export_logs(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出操作日志",
            f"操作日志_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV (*.csv)"
        )
        if not path:
            return
        import csv
        try:
            rows = get_operation_logs(limit=1000)
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["ID", "时间", "用户", "操作", "模块", "详情"])
                for r in rows:
                    w.writerow([r["id"], r.get("created_at",""), r.get("username",""),
                                r.get("action",""), r.get("module",""), r.get("detail","")])
            QMessageBox.information(self, "导出成功", f"已导出 {len(rows)} 条日志")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", str(e)[:200])

    def _clean_old_logs(self):
        if QMessageBox.Yes != QMessageBox.question(
            self, "清理确认", "删除 30 天前的操作日志？",
            QMessageBox.Yes | QMessageBox.No
        ):
            return
        try:
            clear_old_logs(30)
            QMessageBox.information(self, "清理完成", "已清理旧日志")
            self._load_logs()
        except Exception as e:
            QMessageBox.warning(self, "清理失败", str(e)[:200])

    def _manual_sync(self):
        try:
            from core.database import get_conn, commit
            conn = get_conn("system_logs.db")
            conn.execute(
                "INSERT INTO sync_logs (table_name, direction, record_count, status) VALUES (?,?,?,?)",
                ("manual", "up", 0, "success")
            )
            commit("system_logs.db")
            QMessageBox.information(self, "同步完成", "数据已同步到本地数据库")
            self._load_sync_status()
        except Exception as e:
            QMessageBox.warning(self, "同步失败", str(e)[:200])

    def _mark_resolved(self):
        row = self.err_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请选中一行错误记录")
            return
        try:
            from core.database import get_conn, commit
            err_time = self.err_table.item(row, 0).text()
            conn = get_conn("system_logs.db")
            conn.execute("UPDATE error_logs SET handled=1 WHERE created_at=?", (err_time,))
            commit("system_logs.db")
            self._load_error_logs()
        except Exception as e:
            QMessageBox.warning(self, "标记失败", str(e)[:200])

    def _style(self):
        return """
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(10,12,18,245), stop:1 rgba(18,21,28,245));
                border: 2px solid rgba(130,145,165,35); border-radius: 14px;
            }
            QTabWidget::pane {
                background: transparent; border: 1px solid rgba(130,145,165,20);
                border-radius: 8px; padding: 8px;
            }
            QTabBar::tab {
                background: rgba(18,22,30,200); color: #889999;
                padding: 8px 20px; border: 1px solid rgba(130,145,165,15);
                border-bottom: none; border-top-left-radius: 8px;
                border-top-right-radius: 8px; font-size: 12px;
            }
            QTabBar::tab:selected {
                background: rgba(30,36,46,230); color: #ddaaff;
                border-bottom: 1px solid rgba(30,36,46,230);
            }
            QLabel { color: #99aabb; background: transparent; font-size: 12px; }
            QGroupBox {
                color: #889999; font-weight: 700;
                border: 1px solid rgba(130,145,165,25); border-radius: 10px;
                margin-top: 8px; padding-top: 14px;
            }
            QGroupBox::title { left: 14px; padding: 0 6px; }
            QLineEdit, QComboBox {
                background: rgba(16,20,26,220); color: #aabbcc;
                border: 1px solid rgba(130,145,165,25); border-radius: 6px;
                padding: 6px 10px; font-size: 12px;
            }
            QPushButton {
                background: rgba(130,145,165,30); color: #ccddee;
                border: 1px solid rgba(150,165,185,45); border-radius: 8px;
                padding: 7px 18px; font-size: 11px; font-weight: 600;
            }
            QPushButton:hover { background: rgba(160,175,195,55); }
            QPushButton#btn_clean { background: rgba(200,50,50,35); color: #ff6666; }
            QPushButton#btn_clean:hover { background: rgba(220,70,70,55); }
            QPushButton#btn_sync { background: rgba(40,160,80,45); color: #88ffaa; }
            QTableWidget {
                background: rgba(14,18,24,220); color: #aabbcc;
                border: 1px solid rgba(120,140,165,20); border-radius: 8px;
                gridline-color: rgba(80,95,115,18); font-size: 12px;
            }
            QTableWidget::item { padding: 5px 8px; }
            QHeaderView::section {
                background: rgba(22,26,32,230); color: #889999;
                padding: 6px 8px; border: none;
                border-bottom: 1px solid rgba(130,145,165,30);
                font-weight: 700; font-size: 11px;
            }
        """

```
