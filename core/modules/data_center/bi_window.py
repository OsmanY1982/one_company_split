"""
数据大屏 · OBSERVATORY
QDialog：核心KPI卡片 + QPainter趋势折线图 + Top排行 + 数据表格
"""
import os, sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QHeaderView, QTextEdit, QFrame
)
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush,
    QLinearGradient, QRadialGradient, QFont, QPainterPath
)

from core.theme import CYBER_TEAL

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")


class TrendChart(QFrame):
    """QPainter 自绘趋势折线图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []  # list of (label, value)
        self.setMinimumHeight(220)
        self.setStyleSheet("background: rgba(8,18,20,220); border: 1px solid rgba(0,180,150,35); border-radius: 10px;")

    def set_data(self, data):
        self._data = data
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        margin_l, margin_r, margin_t, margin_b = 55, 25, 25, 45
        plot_w = w - margin_l - margin_r
        plot_h = h - margin_t - margin_b

        if plot_w <= 0 or plot_h <= 0 or len(self._data) < 2:
            painter.end(); return

        values = [v for _, v in self._data]
        vmin, vmax = min(values), max(values)
        if vmax == vmin: vmax = vmin + 1
        vrange = vmax - vmin

        # 网格
        painter.setPen(QPen(QColor(0, 120, 100, 25), 0.5))
        for i in range(6):
            y = margin_t + plot_h * i / 5
            painter.drawLine(margin_l, int(y), w - margin_r, int(y))

        # 渐变填充
        fill_path = QPainterPath()
        points = []
        for i, (_, val) in enumerate(self._data):
            x = margin_l + plot_w * i / (len(self._data) - 1)
            y = margin_t + plot_h * (1 - (val - vmin) / vrange) if vrange > 0 else margin_t
            points.append(QPointF(x, y))

        fill_path.moveTo(points[0].x(), margin_t + plot_h)
        for pt in points:
            fill_path.lineTo(pt)
        fill_path.lineTo(points[-1].x(), margin_t + plot_h)
        fill_path.closeSubpath()

        fill_g = QLinearGradient(0, margin_t, 0, margin_t + plot_h)
        fill_g.setColorAt(0, QColor(0, 200, 160, 60))
        fill_g.setColorAt(0.7, QColor(0, 120, 100, 15))
        fill_g.setColorAt(1, QColor(0, 40, 30, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(fill_g))
        painter.drawPath(fill_path)

        # 折线
        line_path = QPainterPath()
        line_path.moveTo(points[0])
        for pt in points[1:]:
            line_path.lineTo(pt)
        painter.setPen(QPen(QColor(0, 220, 180, 220), 2.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(line_path)

        # 数据点
        for i, pt in enumerate(points):
            glow = QRadialGradient(pt, 8)
            glow.setColorAt(0, QColor(0, 240, 200, 100))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(pt, 8, 8)

            painter.setBrush(QBrush(QColor(0, 240, 200, 230)))
            painter.drawEllipse(pt, 3.5, 3.5)

            # 标签
            if i % max(1, len(points) // 6) == 0 or i == len(points) - 1:
                painter.setPen(QColor(120, 200, 180))
                painter.setFont(QFont("Menlo", 8))
                painter.drawText(QRectF(pt.x() - 25, pt.y() - 22, 50, 16),
                                 Qt.AlignCenter, f"{self._data[i][1]:.0f}")

        # X 轴标签
        painter.setPen(QColor(100, 160, 150, 140))
        painter.setFont(QFont("PingFang SC", 8))
        step = max(1, len(self._data) // 8)
        for i in range(0, len(self._data), step):
            x = margin_l + plot_w * i / (len(self._data) - 1)
            painter.drawText(QRectF(x - 25, margin_t + plot_h + 4, 50, 30),
                             Qt.AlignHCenter | Qt.TextWordWrap, self._data[i][0])

        # Y 轴标签
        painter.setPen(QColor(80, 140, 130, 120))
        painter.setFont(QFont("Menlo", 8))
        for i in range(6):
            val = vmax - vrange * i / 5
            y = margin_t + plot_h * i / 5
            painter.drawText(QRectF(2, int(y) - 10, margin_l - 8, 20),
                             Qt.AlignRight | Qt.AlignVCenter, f"{val:.0f}")

        painter.end()


class BIWindow(QDialog):
    """数据大屏 · OBSERVATORY"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据大屏 · OBSERVATORY")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet(CYBER_TEAL.DIALOG_QSS)
        self._build_ui()
        self._load_all()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(22, 18, 22, 18)

        # ── 标题栏 ──
        title_row = QHBoxLayout()
        title = QLabel("数据大屏 · OBSERVATORY")
        title.setStyleSheet("color: #aaeecc; font-size: 18px; font-weight: 800; letter-spacing: 4px; background: transparent;")
        title_row.addWidget(title)
        title_row.addStretch()
        fs_btn = QPushButton("全屏 F11")
        fs_btn.setStyleSheet(CYBER_TEAL.BTN_PRIMARY)
        fs_btn.clicked.connect(lambda: self.showFullScreen() if not self.isFullScreen() else self.showNormal())
        title_row.addWidget(fs_btn)
        layout.addLayout(title_row)

        # ── KPI 卡片 ──
        cards = QHBoxLayout()
        self.bi_kpi = {}
        for name, color, unit in [("总营收","#00ffaa","本月"),("订单数","#44ccff","本月"),("客单价","#ffaa44","平均"),("新增客户","#cc88ff","本月")]:
            card = QFrame()
            card.setStyleSheet(f"background: rgba(6,16,18,240); border: 1px solid rgba(0,180,150,40); border-radius: 14px; padding: 18px; min-width: 150px;")
            cll = QVBoxLayout(card); cll.setContentsMargins(0, 0, 0, 0); cll.setSpacing(6)
            lb = QLabel(name)
            lb.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 700; background:transparent;")
            vl = QLabel("—")
            vl.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: 800; background:transparent;")
            ul = QLabel(unit)
            ul.setStyleSheet("color: #447766; font-size: 10px; background:transparent;")
            cll.addWidget(lb); cll.addWidget(vl); cll.addWidget(ul)
            self.bi_kpi[name] = vl
            cards.addWidget(card)
        cards.addStretch()
        layout.addLayout(cards)

        # ── 趋势图 ──
        trend_header = QHBoxLayout()
        trend_label = QLabel("数据趋势概览")
        trend_label.setStyleSheet("color: #88aaaa; font-size: 13px; font-weight: 700; background:transparent;")
        trend_header.addWidget(trend_label)
        trend_header.addStretch()
        layout.addLayout(trend_header)

        self.trend_chart = TrendChart(self)
        layout.addWidget(self.trend_chart, 2)

        # ── 趋势文字摘要 ──
        self.trend_text = QTextEdit()
        self.trend_text.setReadOnly(True)
        self.trend_text.setMaximumHeight(90)
        self.trend_text.setStyleSheet("background: rgba(4,12,14,220); color: #88ccaa; border: 1px solid rgba(0,150,120,30); border-radius: 8px; padding: 10px; font-size: 12px; font-family: 'Courier New', monospace;")
        layout.addWidget(self.trend_text)

        # ── 详细数据表格 ──
        detail_label = QLabel("详细数据 / Top 排行")
        detail_label.setStyleSheet("color: #88aaaa; font-size: 13px; font-weight: 700; background:transparent;")
        layout.addWidget(detail_label)

        self.table = QTableWidget()
        self.table.setStyleSheet(CYBER_TEAL.TABLE_STYLE)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table, 1)

    def _load_all(self):
        try:
            total_revenue = total_orders = total_customers = 0

            # 订单
            db = os.path.join(DATA_DIR, "order.db")
            order_data = []
            if os.path.exists(db):
                conn = get_conn(os.path.basename(db));                 r = conn.execute("SELECT COUNT(*) as c, COALESCE(SUM(total_amount),0) as s FROM orders").fetchone()
                total_orders = r['c']; total_revenue = r['s']
                # 按日期分组趋势
                trend_rows = conn.execute(
                    "SELECT DATE(created_at) as d, COUNT(*) as cnt, COALESCE(SUM(total_amount),0) as amt "
                    "FROM orders GROUP BY d ORDER BY d DESC LIMIT 30"
                ).fetchall()
                order_data = [(row['d'] or '', row['amt']) for row in reversed(trend_rows)]
                close_conn(os.path.basename(db))

            # 客户
            db = os.path.join(DATA_DIR, "customer.db")
            if os.path.exists(db):
                conn = get_conn(os.path.basename(db))
                total_customers = conn.execute("SELECT COUNT(*) FROM customer").fetchone()[0]
                close_conn(os.path.basename(db))

            avg_order = total_revenue / total_orders if total_orders > 0 else 0

            # 更新 KPI
            self.bi_kpi["总营收"].setText(f"¥{total_revenue:.0f}")
            self.bi_kpi["订单数"].setText(str(total_orders))
            self.bi_kpi["客单价"].setText(f"¥{avg_order:.0f}")
            self.bi_kpi["新增客户"].setText(str(total_customers))

            # 趋势图
            if order_data:
                self.trend_chart.set_data(order_data)

            # 趋势文字
            self.trend_text.setText("\n".join([
                f"  {'─' * 44}",
                f"  总营收: ¥{total_revenue:,.2f}",
                f"  订单总数: {total_orders} 单",
                f"  客户数: {total_customers}",
                f"  平均客单价: ¥{avg_order:,.2f}",
                f"  {'─' * 44}",
            ]))

            # 详细表格
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["日期","收入","订单","新增客户","客单价"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            if order_data:
                self.table.setRowCount(len(order_data))
                for i, (d, amt) in enumerate(order_data):
                    self.table.setItem(i, 0, QTableWidgetItem(d))
                    self.table.setItem(i, 1, QTableWidgetItem(f"¥{amt:,.2f}"))
                    self.table.setItem(i, 2, QTableWidgetItem(str(total_orders // max(1, len(order_data)))))
                    self.table.setItem(i, 3, QTableWidgetItem(str(total_customers // max(1, len(order_data)))))
                    self.table.setItem(i, 4, QTableWidgetItem(f"¥{avg_order:,.2f}"))
            else:
                self.table.setRowCount(1)
                self.table.setItem(0, 0, QTableWidgetItem("当前汇总"))
                self.table.setItem(0, 1, QTableWidgetItem(f"¥{total_revenue:,.2f}"))
                self.table.setItem(0, 2, QTableWidgetItem(str(total_orders)))
                self.table.setItem(0, 3, QTableWidgetItem(str(total_customers)))
                self.table.setItem(0, 4, QTableWidgetItem(f"¥{avg_order:,.2f}"))

        except Exception as e:
            self.trend_text.setText(f"数据加载异常: {e}")