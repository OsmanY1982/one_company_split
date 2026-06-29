"""
数据报表 · OBSERVATORY
QDialog：时间维度选择 + 统计类型 + 数据表格 + QPainter图表 + 导出CSV
"""
import os, sqlite3, csv
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QHeaderView, QTextEdit,
    QComboBox, QFrame, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import pyqtgraph as pg

from core.theme import CYBER_TEAL

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")


class ChartWidget(pg.PlotWidget):
    """pyqtgraph 宇宙主题柱状图/折线图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []          # list of (label, value)
        self._chart_type = "bar" # "bar" or "line"
        self.setMinimumHeight(200)
        self.setStyleSheet("border: 1px solid rgba(0,160,140,35); border-radius: 10px;")
        self.setBackground((6, 16, 18, 230))

        # Grid
        self.showGrid(x=False, y=True, alpha=0.08)

        # Axis styling
        left_axis = self.getPlotItem().getAxis('left')
        bottom_axis = self.getPlotItem().getAxis('bottom')
        left_axis.setPen(pg.mkPen(color=(0, 120, 100, 40)))
        bottom_axis.setPen(pg.mkPen(color=(0, 120, 100, 40)))
        left_axis.setTextPen(pg.mkPen(color=(80, 140, 130, 150)))
        bottom_axis.setTextPen(pg.mkPen(color=(100, 160, 150, 180)))

        # Hide default buttons/menu
        self.getPlotItem().hideButtons()
        self.getPlotItem().setMenuEnabled(False)

    def set_data(self, data, chart_type="bar"):
        self._data = data
        self._chart_type = chart_type
        self.getPlotItem().clear()
        self._plot()

    def _plot(self):
        if not self._data:
            return

        labels = [item[0] for item in self._data]
        values = [item[1] for item in self._data]
        x_indices = list(range(len(values)))

        if self._chart_type == "bar":
            bar_width = 0.6
            brush = pg.mkBrush(0, 200, 160, 180)
            bar_item = pg.BarGraphItem(
                x=x_indices, height=values, width=bar_width, brush=brush
            )
            self.addItem(bar_item)

            # Value labels on top of bars
            for i, v in enumerate(values):
                text = pg.TextItem(
                    f"{v:.0f}", color=(170, 240, 220), anchor=(0.5, 1.0)
                )
                text.setFont(QFont("Menlo", 9))
                text.setPos(i, v)
                self.addItem(text)

            # Top glow dots
            glow = pg.ScatterPlotItem(
                x=x_indices, y=values,
                size=10, brush=pg.mkBrush(0, 255, 200, 60),
                pen=pg.mkPen(None)
            )
            self.addItem(glow)
        else:  # line
            pen = pg.mkPen(color=(0, 220, 180, 200), width=2.5)
            self.getPlotItem().plot(x_indices, values, pen=pen)

            # Data points
            scatter = pg.ScatterPlotItem(
                x=x_indices, y=values,
                size=9, brush=pg.mkBrush(0, 240, 200, 220),
                pen=pg.mkPen(None)
            )
            self.addItem(scatter)

        # X axis tick labels
        bottom_axis = self.getPlotItem().getAxis('bottom')
        ticks = [(i, label) for i, label in enumerate(labels)]
        bottom_axis.setTicks([ticks])
        bottom_axis.setTickFont(QFont("PingFang SC", 8))

        # Y axis font
        self.getPlotItem().getAxis('left').setTickFont(QFont("Menlo", 8))


class ReportWindow(QDialog):
    """数据报表 · OBSERVATORY"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据报表 · OBSERVATORY")
        self.setMinimumSize(1000, 680)
        self.setStyleSheet(CYBER_TEAL.DIALOG_QSS)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(22, 18, 22, 18)

        # ── 标题 ──
        title = QLabel("数据报表 · OBSERVATORY")
        title.setStyleSheet("color: #aaeecc; font-size: 18px; font-weight: 800; letter-spacing: 4px; background: transparent;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # ── KPI 卡片 ──
        cards = QHBoxLayout()
        self.kpi_labels = {}
        for name, color in [("财务收入","#44cc88"),("会员总数","#4488ff"),("客户数量","#ffaa44"),("订单总数","#cc88ff"),("团队人数","#ff6688")]:
            card = QFrame()
            card.setStyleSheet(f"background: rgba(8,20,22,230); border: 1px solid rgba(0,160,140,30); border-radius: 10px; padding: 12px; min-width: 120px;")
            cll = QVBoxLayout(card); cll.setContentsMargins(0, 0, 0, 0)
            lb = QLabel(name)
            lb.setStyleSheet("color: #558877; font-size: 11px; background:transparent;")
            vl = QLabel("—")
            vl.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: 700; background:transparent;")
            cll.addWidget(lb); cll.addWidget(vl)
            self.kpi_labels[name] = vl
            cards.addWidget(card)
        cards.addStretch()
        layout.addLayout(cards)

        # ── 控制栏 ──
        ctrl = QHBoxLayout()

        ctrl.addWidget(QLabel("时间维度:"))
        self.time_dim = QComboBox()
        self.time_dim.addItems(["累计","今日","本周","本月","本年"])
        self.time_dim.setStyleSheet(CYBER_TEAL.INPUT_STYLE)
        self.time_dim.currentTextChanged.connect(self._refresh)
        ctrl.addWidget(self.time_dim)

        ctrl.addSpacing(20)
        ctrl.addWidget(QLabel("统计类型:"))
        self.report_type = QComboBox()
        self.report_type.addItems(["收入概览","订单明细","会员统计","客户分析","产品销售"])
        self.report_type.setStyleSheet(CYBER_TEAL.INPUT_STYLE)
        self.report_type.currentTextChanged.connect(self._refresh)
        ctrl.addWidget(self.report_type)

        ctrl.addStretch()
        export = QPushButton("导出CSV")
        export.setStyleSheet(CYBER_TEAL.BTN_PRIMARY)
        export.clicked.connect(self._export)
        ctrl.addWidget(export)
        layout.addLayout(ctrl)

        # ── 图表 ──
        self.chart = ChartWidget(self)
        layout.addWidget(self.chart, 1)

        # ── 数据表格 ──
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet(CYBER_TEAL.TABLE_STYLE)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table, 2)

        # ── 摘要 ──
        self.summary = QTextEdit()
        self.summary.setReadOnly(True)
        self.summary.setMaximumHeight(70)
        self.summary.setStyleSheet(CYBER_TEAL.INPUT_STYLE)
        layout.addWidget(self.summary)

    def _setup_table(self, headers):
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def _refresh(self):
        rtype = self.report_type.currentText()
        # 更新团队人数KPI（所有报表类型通用）
        self._load_team_kpi()
        try:
            if rtype == "收入概览":
                self._load_finance()
            elif rtype == "订单明细":
                self._load_orders()
            elif rtype == "会员统计":
                self._load_members()
            elif rtype == "客户分析":
                self._load_customers()
            elif rtype == "产品销售":
                self._load_products()
        except Exception as e:
            self.summary.setText(f"加载异常: {e}")

    def _load_team_kpi(self):
        """加载团队人数 KPI"""
        db = os.path.join(DATA_DIR, "staff.db")
        if os.path.exists(db):
            try:
                conn = get_conn(os.path.basename(db))
                total = conn.execute("SELECT COUNT(*) FROM staff").fetchone()[0]
                close_conn(os.path.basename(db))
                self.kpi_labels["团队人数"].setText(str(total))
            except Exception:
                self.kpi_labels["团队人数"].setText("—")
        else:
            self.kpi_labels["团队人数"].setText("—")

    def _load_finance(self):
        db = os.path.join(DATA_DIR, "finance.db")
        if not os.path.exists(db):
            self._setup_table(["提示"]); self.summary.setText("暂无财务数据"); return
        conn = get_conn(os.path.basename(db));         rows = conn.execute("SELECT * FROM finance ORDER BY id DESC LIMIT 50").fetchall(); close_conn(os.path.basename(db))
        self._setup_table(["ID","类型","类别","金额","备注","日期"])
        self.table.setRowCount(len(rows))
        inc = exp = 0
        for i, r in enumerate(rows):
            for j, k in enumerate(['id', 'type', 'category', 'amount', 'note', 'created_at']):
                self.table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))
            amt = float(r['amount'] or 0)
            if r['type'] and '收入' in str(r['type']): inc += amt
            else: exp += amt
        self.kpi_labels["财务收入"].setText(f"¥{inc:.0f}")
        self.summary.setText(f"总收入: ¥{inc:.2f} | 总支出: ¥{exp:.2f} | 利润: ¥{inc - exp:.2f}")
        self.chart.set_data([("收入", inc), ("支出", exp), ("利润", inc - exp)], "bar")

    def _load_orders(self):
        db = os.path.join(DATA_DIR, "order.db")
        if not os.path.exists(db): self._setup_table(["提示"]); self.summary.setText("暂无订单"); return
        conn = get_conn(os.path.basename(db));         rows = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 50").fetchall()
        t = conn.execute("SELECT COUNT(*), COALESCE(SUM(total_amount),0) FROM orders").fetchone(); close_conn(os.path.basename(db))
        self._setup_table(["ID","订单号","客户","金额","时间","状态"])
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate(['id', 'order_no', 'customer_name', 'total_amount', 'created_at', 'status']):
                self.table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))
        self.kpi_labels["订单总数"].setText(str(t[0]))
        self.summary.setText(f"订单总数: {t[0]} | 总金额: ¥{t[1]:.2f}")
        self.chart.set_data([("订单数", t[0]), ("总金额(元)", int(t[1]))], "bar")

    def _load_members(self):
        db = os.path.join(DATA_DIR, "member.db")
        if not os.path.exists(db): self._setup_table(["提示"]); self.summary.setText("暂无会员"); return
        conn = get_conn(os.path.basename(db));         rows = conn.execute("SELECT * FROM member ORDER BY id DESC LIMIT 50").fetchall()
        stats = conn.execute("SELECT level, COUNT(*) as c FROM member GROUP BY level").fetchall(); close_conn(os.path.basename(db))
        self._setup_table(["ID","姓名","电话","等级","积分","VIP到期","状态"])
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate(['id', 'name', 'phone', 'level', 'points', 'vip_expire', 'status']):
                self.table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))
        total = sum(s['c'] for s in stats)
        self.kpi_labels["会员总数"].setText(str(total))
        levels = " | ".join([f"{s['level']}:{s['c']}" for s in stats])
        self.summary.setText(f"总计: {total} | {levels}")
        chart_data = [(s['level'], s['c']) for s in stats]
        self.chart.set_data(chart_data, "bar")

    def _load_customers(self):
        db = os.path.join(DATA_DIR, "customer.db")
        if not os.path.exists(db): self._setup_table(["提示"]); self.summary.setText("暂无客户"); return
        conn = get_conn(os.path.basename(db));         rows = conn.execute("SELECT * FROM customer ORDER BY id DESC LIMIT 50").fetchall()
        total = conn.execute("SELECT COUNT(*) FROM customer").fetchone()[0]; close_conn(os.path.basename(db))
        self._setup_table(["ID","姓名","电话","公司","等级","备注"])
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate(['id', 'name', 'phone', 'company', 'level', 'note']):
                self.table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))
        self.kpi_labels["客户数量"].setText(str(total))
        self.summary.setText(f"客户总数: {total}")
        self.chart.set_data([("客户总数", total)], "bar")

    def _load_products(self):
        db = os.path.join(DATA_DIR, "product.db")
        if not os.path.exists(db): self._setup_table(["提示"]); self.summary.setText("暂无产品"); return
        conn = get_conn(os.path.basename(db));         rows = conn.execute("SELECT * FROM product ORDER BY id DESC LIMIT 50").fetchall()
        total = conn.execute("SELECT COUNT(*) FROM product").fetchone()[0]; close_conn(os.path.basename(db))
        self._setup_table(["ID","名称","类别","价格","库存","状态"])
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, k in enumerate(['id', 'name', 'category', 'price', 'stock', 'status']):
                self.table.setItem(i, j, QTableWidgetItem(str(r[k]) if r[k] is not None else ""))
        self.summary.setText(f"产品总数: {total}")
        self.chart.set_data([("产品总数", total)], "bar")

    def _export(self):
        fp, _ = QFileDialog.getSaveFileName(self, "导出", f"report_{datetime.now().strftime('%Y%m%d')}.csv", "CSV (*.csv)")
        if not fp: return
        with open(fp, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            headers = [self.table.horizontalHeaderItem(c).text() for c in range(self.table.columnCount())]
            w.writerow(headers)
            for row in range(self.table.rowCount()):
                w.writerow([self.table.item(row, c).text() if self.table.item(row, c) else "" for c in range(self.table.columnCount())])
        self.summary.setText(f"已导出: {fp}")