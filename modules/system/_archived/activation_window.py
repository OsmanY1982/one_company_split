"""
激活码 · ENGINEERING DECK
QDialog：激活码生成 / 验证 / 使用记录，金色点缀金属灰主题
"""
import traceback
import os, sqlite3, random, string
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QHeaderView, QLineEdit, QComboBox, QGroupBox, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

QSS = """
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(14,16,20,245), stop:1 rgba(20,23,28,245));
        border: 2px solid rgba(130,145,165,50);
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
    QLineEdit, QComboBox {
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
BTN_GOLD = """
    QPushButton {
        background: rgba(200,170,60,40); color: #ffdd88;
        border: 1px solid rgba(220,190,80,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(220,190,80,70); }
"""
GROUP_STYLE = """
    QGroupBox {
        color: #889999; font-weight: 700; font-size: 12px;
        border: 1px solid rgba(130,145,165,35); border-radius: 10px;
        margin-top: 12px; padding-top: 16px;
    }
    QGroupBox::title { left: 14px; padding: 0 6px; }
    QLabel { color: #889999; background: transparent; }
"""


class ActivationWindow(QDialog):
    """激活码管理"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("激活码 · ENGINEERING DECK")
        self.setMinimumSize(800, 560)
        self.setStyleSheet(QSS)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(22, 18, 22, 18)

        title = QLabel("激活码管理 · ENGINEERING DECK")
        title.setStyleSheet("color: #aabbcc; font-size: 16px; font-weight: 800; letter-spacing: 3px; background: transparent;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # ── 生成区 ──
        gen = QGroupBox("生成激活码")
        gen.setStyleSheet(GROUP_STYLE)
        gl = QHBoxLayout(gen); gl.setSpacing(12)
        gl.addWidget(QLabel("类型:"))
        self.act_type = QComboBox()
        self.act_type.addItems(["试用", "月卡", "季卡", "年卡", "永久"])
        self.act_type.setStyleSheet(INPUT_STYLE)
        gl.addWidget(self.act_type)
        gl.addWidget(QLabel("天数:"))
        self.act_days = QComboBox()
        self.act_days.addItems(["7", "15", "30", "90", "365", "9999"])
        self.act_days.setStyleSheet(INPUT_STYLE)
        gl.addWidget(self.act_days)
        gl.addWidget(QLabel("数量:"))
        self.act_count = QComboBox()
        self.act_count.addItems(["1", "5", "10", "20", "50"])
        self.act_count.setStyleSheet(INPUT_STYLE)
        gl.addWidget(self.act_count)
        gen_btn = QPushButton("生成")
        gen_btn.setStyleSheet(BTN_GOLD)
        gen_btn.clicked.connect(self._gen)
        gl.addWidget(gen_btn); gl.addStretch()
        layout.addWidget(gen)

        # ── 统计卡片 ──
        sc = QHBoxLayout()
        self.total_lbl = QLabel("—")
        self.used_lbl = QLabel("—")
        self.avail_lbl = QLabel("—")
        for label, val in [("总数", self.total_lbl), ("已用", self.used_lbl), ("可用", self.avail_lbl)]:
            card = QFrame()
            card.setStyleSheet("background: rgba(18,20,24,230); border: 1px solid rgba(130,145,165,30); border-radius: 8px; padding: 8px 20px;")
            cl = QVBoxLayout(card); cl.setContentsMargins(0, 0, 0, 0)
            lb = QLabel(label)
            lb.setStyleSheet("color: #667788; font-size: 10px; background:transparent;")
            val.setStyleSheet("color: #ccddee; font-size: 18px; font-weight: 700; background:transparent;")
            cl.addWidget(lb); cl.addWidget(val)
            sc.addWidget(card)
        sc.addStretch()
        layout.addLayout(sc)

        # ── 搜索 ──
        sr = QHBoxLayout()
        sr.addWidget(QLabel("搜索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("激活码或用户")
        self.search_input.setMaximumWidth(220)
        self.search_input.setStyleSheet(INPUT_STYLE)
        self.search_input.textChanged.connect(self._load)
        sr.addWidget(self.search_input)
        sr.addStretch()
        layout.addLayout(sr)

        # ── 表格 ──
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "激活码", "类型", "天数", "状态", "使用者"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def _gen(self):
        code_type = self.act_type.currentText()
        days = int(self.act_days.currentText())
        count = int(self.act_count.currentText())
        db = os.path.join(DATA_DIR, "activation.db")
        conn = sqlite3.connect(db)
        codes = []
        for _ in range(count):
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
            conn.execute("INSERT INTO activation(code, code_type, duration_days) VALUES(?,?,?)",
                         (code, code_type, days))
            codes.append(code)
        conn.commit(); conn.close()
        self._log_op("激活码", "生成", f"生成 {count} 个 {code_type} 激活码({days}天)")
        QMessageBox.information(self, "生成成功", f"已生成 {count} 个激活码\n示例: {codes[0]}")
        self._load()

    def _load(self):
        search = self.search_input.text().strip()
        db = os.path.join(DATA_DIR, "activation.db")
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row
        if search:
            rows = conn.execute(
                "SELECT * FROM activation WHERE code LIKE ? OR used_by LIKE ? ORDER BY id DESC",
                (f"%{search}%", f"%{search}%")
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM activation ORDER BY id DESC LIMIT 100").fetchall()
        total = conn.execute("SELECT COUNT(*) as c FROM activation").fetchone()['c']
        used = conn.execute("SELECT COUNT(*) as c FROM activation WHERE is_used=1").fetchone()['c']
        conn.close()

        self.total_lbl.setText(str(total))
        self.used_lbl.setText(str(used))
        self.avail_lbl.setText(str(total - used))

        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(r['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(r['code']))
            self.table.setItem(i, 2, QTableWidgetItem(r['code_type']))
            self.table.setItem(i, 3, QTableWidgetItem(str(r['duration_days'])))
            status_text = "已使用" if r['is_used'] else "未使用"
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QColor("#ffaa44") if r['is_used'] else QColor("#44cc88"))
            self.table.setItem(i, 4, status_item)
            self.table.setItem(i, 5, QTableWidgetItem(r['used_by'] or "-"))

    def _log_op(self, module, action, detail):
        try:
            db = os.path.join(DATA_DIR, "system_logs.db")
            conn = sqlite3.connect(db)
            conn.execute("INSERT INTO op_logs(module, action, detail) VALUES(?,?,?)",
                         (module, action, detail))
            conn.commit(); conn.close()
        except Exception:
            traceback.print_exc()
