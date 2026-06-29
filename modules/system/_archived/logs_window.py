"""
系统日志 · ENGINEERING DECK
QDialog：日志表格 + 级别/时间筛选 + 导出，紫色点缀金属灰主题
"""
import traceback
import os, sqlite3, csv
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QHeaderView, QComboBox, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

QSS = """
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(14,16,20,245), stop:1 rgba(20,23,28,245));
        border: 2px solid rgba(140,100,180,50);
        border-radius: 14px;
    }
"""
TABLE_STYLE = """
    QTableWidget {
        background: rgba(16,18,22,220); color: #aabbcc;
        border: 1px solid rgba(120,135,155,30); border-radius: 8px;
        gridline-color: rgba(80,90,110,25); font-size: 12px;
        selection-background-color: rgba(130,145,165,60);
    }
    QTableWidget::item { padding: 5px 10px; }
    QHeaderView::section {
        background: rgba(22,24,28,230); color: #889999; padding: 8px 10px;
        border: none; border-bottom: 1px solid rgba(130,145,165,40);
        font-weight: 700; font-size: 11px; letter-spacing: 1px;
    }
"""
INPUT_STYLE = """
    QComboBox {
        background: rgba(16,18,22,230); color: #aabbcc;
        border: 1px solid rgba(130,145,165,35); border-radius: 6px;
        padding: 6px 10px; font-size: 12px;
    }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: #141618; color: #aabbcc;
        selection-background-color: rgba(130,145,165,80);
    }
"""
BTN_PRIMARY = """
    QPushButton {
        background: rgba(130,145,165,40); color: #ccddee;
        border: 1px solid rgba(150,165,185,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(150,165,185,70); }
"""
BTN_DANGER = """
    QPushButton {
        background: rgba(180,60,40,40); color: #ffaaaa;
        border: 1px solid rgba(180,80,50,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(200,80,50,70); }
"""
BTN_PURPLE = """
    QPushButton {
        background: rgba(140,100,180,40); color: #ccaadd;
        border: 1px solid rgba(160,120,200,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(160,120,200,70); }
"""


class LogsWindow(QDialog):
    """系统日志查看"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统日志 · ENGINEERING DECK")
        self.setMinimumSize(800, 560)
        self.setStyleSheet(QSS)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(22, 18, 22, 18)

        title = QLabel("系统日志 · ENGINEERING DECK")
        title.setStyleSheet("color: #aabbcc; font-size: 16px; font-weight: 800; letter-spacing: 3px; background: transparent;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # ── 筛选栏 ──
        sr = QHBoxLayout()
        sr.addWidget(QLabel("日志类型:"))
        self.log_type = QComboBox()
        self.log_type.addItems(["操作日志", "同步状态", "错误日志"])
        self.log_type.setStyleSheet(INPUT_STYLE)
        self.log_type.currentTextChanged.connect(self._load)
        sr.addWidget(self.log_type)

        sr.addSpacing(16)
        sr.addWidget(QLabel("时间筛选:"))
        self.time_filter = QComboBox()
        self.time_filter.addItems(["全部", "今日", "最近7天", "最近30天"])
        self.time_filter.setStyleSheet(INPUT_STYLE)
        self.time_filter.currentTextChanged.connect(self._load)
        sr.addWidget(self.time_filter)

        sr.addStretch()

        export_btn = QPushButton("导出CSV")
        export_btn.setStyleSheet(BTN_PURPLE)
        export_btn.clicked.connect(self._export)
        sr.addWidget(export_btn)

        clear_btn = QPushButton("清除30天前")
        clear_btn.setStyleSheet(BTN_DANGER)
        clear_btn.clicked.connect(self._clear_old)
        sr.addWidget(clear_btn)
        layout.addLayout(sr)

        # ── 表格 ──
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def _get_time_where(self):
        tf = self.time_filter.currentText()
        if tf == "全部":
            return ""
        elif tf == "今日":
            cutoff = datetime.now().strftime("%Y-%m-%d")
        elif tf == "最近7天":
            cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        elif tf == "最近30天":
            cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        else:
            return ""
        return f" AND created_at >= '{cutoff}'"

    def _load(self):
        log_type = self.log_type.currentText()
        time_where = self._get_time_where()

        if log_type == "操作日志":
            table_name, headers, cols = "op_logs", ["ID", "模块", "操作", "详情", "时间"], ['id', 'module', 'action', 'detail', 'created_at']
        elif log_type == "同步状态":
            table_name, headers, cols = "sync_logs", ["ID", "同步类型", "状态", "详情", "时间"], ['id', 'sync_type', 'status', 'detail', 'created_at']
        else:
            table_name, headers, cols = "error_logs", ["ID", "模块", "错误", "详情", "时间"], ['id', 'module', 'error', 'detail', 'created_at']

        db = os.path.join(DATA_DIR, "system_logs.db")
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
        rows = conn.execute(f"SELECT * FROM {table_name} WHERE 1=1 {time_where} ORDER BY id DESC LIMIT 200").fetchall()
        conn.close()

        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate(cols):
                self.table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))

    def _clear_old(self):
        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        db = os.path.join(DATA_DIR, "system_logs.db")
        conn = sqlite3.connect(db)
        for tbl in ["op_logs", "sync_logs", "error_logs"]:
            conn.execute(f"DELETE FROM {tbl} WHERE created_at < ?", (cutoff,))
        conn.commit(); conn.close()
        self._log_op("系统日志", "清理", "清除30天前日志")
        self._load()
        QMessageBox.information(self, "提示", f"已清理 {cutoff} 之前的日志")

    def _export(self):
        fp, _ = QFileDialog.getSaveFileName(
            self, "导出日志", f"logs_{datetime.now().strftime('%Y%m%d')}.csv", "CSV (*.csv)"
        )
        if not fp: return
        with open(fp, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            headers = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
            w.writerow(headers)
            for row in range(self.table.rowCount()):
                w.writerow([
                    self.table.item(row, c).text() if self.table.item(row, c) else ""
                    for c in range(self.table.columnCount())
                ])
        QMessageBox.information(self, "导出成功", f"已导出到: {fp}")

    def _log_op(self, module, action, detail):
        try:
            db = os.path.join(DATA_DIR, "system_logs.db")
            conn = sqlite3.connect(db)
            conn.execute("INSERT INTO op_logs(module, action, detail) VALUES(?,?,?)",
                         (module, action, detail))
            conn.commit(); conn.close()
        except Exception:
            traceback.print_exc()
