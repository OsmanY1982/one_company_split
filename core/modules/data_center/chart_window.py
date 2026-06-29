"""
Chart Window - 桌面端数据可视化窗口
PyQt5 + pyqtgraph 实现
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QLabel, QPushButton, QDateEdit,
    QTabWidget, QGridLayout, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, QDate, QTimer, QRectF
from PyQt5.QtGui import QColor, QPainter, QPicture, QPen, QBrush

import pyqtgraph as pg

from services.chart_service import ChartService


# ── 自定义饼图 GraphicsObject ──────────────────────────────────────────

class PieItem(pg.GraphicsObject):
    """饼图图形项 — 替代 QPieSeries"""

    def __init__(self, slices):
        """
        slices: list of (label, value, color_str)
        """
        super().__init__()
        self.slices = slices
        self._picture = None
        self._generate_picture()

    def _generate_picture(self):
        total = sum(v for _, v, _ in self.slices)
        if total == 0:
            self._picture = QPicture()
            return

        pic = QPicture()
        painter = QPainter(pic)
        painter.setRenderHint(QPainter.Antialiasing)

        start_angle = 90 * 16          # Qt 角度单位: 1/16 度, 90° = 从顶部开始
        r = 120
        cx, cy = 0, 0

        for label, value, color_str in self.slices:
            span = int(value / total * 360 * 16)
            painter.setBrush(QColor(color_str))
            painter.setPen(QPen(QColor("white"), 2))
            painter.drawPie(cx - r, cy - r, r * 2, r * 2, start_angle, span)
            start_angle += span

        painter.end()
        self._picture = pic

    def paint(self, painter: QPainter, option, widget=None):
        if self._picture:
            painter.drawPicture(0, 0, self._picture)

    def boundingRect(self):
        return QRectF(-135, -135, 270, 270)


# ── UI 组件 ────────────────────────────────────────────────────────────

class ChartWidget(QFrame):
    """图表组件 — pyqtgraph 版本"""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.graphics_widget: pg.GraphicsLayoutWidget | None = None
        self.plot_widget: pg.PlotItem | None = None
        self.init_ui()

    def init_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        layout = QVBoxLayout(self)

        if self.title:
            title_label = QLabel(self.title)
            title_label.setStyleSheet("""
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 10px;
            """)
            layout.addWidget(title_label)

        self.graphics_widget = pg.GraphicsLayoutWidget()
        self.graphics_widget.setMinimumHeight(300)
        layout.addWidget(self.graphics_widget)

    def clear(self):
        """清除图表内容"""
        self.graphics_widget.clear()
        self.plot_widget = None

    def get_plot(self) -> pg.PlotItem:
        """获取或创建 PlotItem（折线图/柱状图共用）"""
        self.graphics_widget.clear()
        self.plot_widget = self.graphics_widget.addPlot()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        return self.plot_widget

    def get_viewbox(self) -> pg.ViewBox:
        """获取 ViewBox（饼图专用，锁定等比）"""
        self.graphics_widget.clear()
        view = self.graphics_widget.addViewBox()
        view.setAspectLocked(True)
        return view


class DashboardWidget(QFrame):
    """仪表盘组件 — 无图表引擎，保留原实现"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        layout = QGridLayout(self)
        layout.setSpacing(15)

        self.cards = {}
        metrics = [
            ("今日订单", "0", "#4CAF50"),
            ("今日营收", "¥0.00", "#2196F3"),
            ("本周订单", "0", "#FF9800"),
            ("本周营收", "¥0.00", "#9C27B0"),
            ("本月订单", "0", "#F44336"),
            ("本月营收", "¥0.00", "#00BCD4"),
            ("总客户", "0", "#795548"),
            ("总产品", "0", "#607D8B"),
        ]

        for i, (title, value, color) in enumerate(metrics):
            row = i // 4
            col = i % 4
            card = self.create_card(title, value, color)
            layout.addWidget(card, row, col)
            self.cards[title] = card

    def create_card(self, title: str, value: str, color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                padding: 15px;
            }}
            QLabel {{
                color: white;
            }}
        """)
        card_layout = QVBoxLayout(card)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; opacity: 0.9;")
        card_layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        value_label.setObjectName("value")
        card_layout.addWidget(value_label)

        return card

    def update_data(self, data: dict):
        updates = {
            "今日订单": str(data.get("today", {}).get("orders", 0)),
            "今日营收": f"¥{data.get('today', {}).get('revenue', 0):.2f}",
            "本周订单": str(data.get("week", {}).get("orders", 0)),
            "本周营收": f"¥{data.get('week', {}).get('revenue', 0):.2f}",
            "本月订单": str(data.get("month", {}).get("orders", 0)),
            "本月营收": f"¥{data.get('month', {}).get('revenue', 0):.2f}",
            "总客户": str(data.get("total_customers", 0)),
            "总产品": str(data.get("total_products", 0)),
        }
        for title, value in updates.items():
            if title in self.cards:
                card = self.cards[title]
                value_label = card.findChild(QLabel, "value")
                if value_label:
                    value_label.setText(value)


# ── 主窗口 ─────────────────────────────────────────────────────────────

class ChartWindow(QMainWindow):
    """数据可视化窗口 — pyqtgraph 版本"""

    def __init__(self):
        super().__init__()
        self.service = ChartService()
        self.init_ui()
        self.load_data()

        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(60000)

    # ── 布局（与原版完全一致）─────────────────────────────────────────

    def init_ui(self):
        self.setWindowTitle("数据可视化")
        self.setGeometry(50, 50, 1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("时间范围:"))

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        toolbar.addWidget(self.start_date)

        toolbar.addWidget(QLabel("至"))

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        toolbar.addWidget(self.end_date)

        refresh_btn = QPushButton("刷新数据")
        refresh_btn.clicked.connect(self.load_data)
        toolbar.addWidget(refresh_btn)

        toolbar.addStretch()

        export_btn = QPushButton("导出报表")
        export_btn.clicked.connect(self.export_report)
        toolbar.addWidget(export_btn)

        layout.addLayout(toolbar)

        # 标签页
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.dashboard_tab = QWidget()
        self.init_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "仪表盘")

        self.sales_tab = QWidget()
        self.init_sales_tab()
        self.tabs.addTab(self.sales_tab, "销售趋势")

        self.product_tab = QWidget()
        self.init_product_tab()
        self.tabs.addTab(self.product_tab, "产品分析")

        self.customer_tab = QWidget()
        self.init_customer_tab()
        self.tabs.addTab(self.customer_tab, "客户分析")

    def init_dashboard_tab(self):
        layout = QVBoxLayout(self.dashboard_tab)
        self.dashboard = DashboardWidget()
        layout.addWidget(self.dashboard)

        charts_layout = QHBoxLayout()
        self.quick_chart1 = ChartWidget("本周销售趋势")
        charts_layout.addWidget(self.quick_chart1)
        self.quick_chart2 = ChartWidget("产品分类占比")
        charts_layout.addWidget(self.quick_chart2)
        layout.addLayout(charts_layout)

    def init_sales_tab(self):
        layout = QVBoxLayout(self.sales_tab)
        self.sales_chart = ChartWidget("销售趋势")
        layout.addWidget(self.sales_chart)
        self.monthly_chart = ChartWidget("月度对比")
        layout.addWidget(self.monthly_chart)

    def init_product_tab(self):
        layout = QVBoxLayout(self.product_tab)
        self.category_chart = ChartWidget("产品分类分布")
        layout.addWidget(self.category_chart)
        self.top_chart = ChartWidget("热销产品 TOP10")
        layout.addWidget(self.top_chart)

    def init_customer_tab(self):
        layout = QVBoxLayout(self.customer_tab)
        self.customer_chart = ChartWidget("客户价值分布")
        layout.addWidget(self.customer_chart)

    # ── 数据加载 ───────────────────────────────────────────────────────

    def load_data(self):
        try:
            dashboard_data = self.service.get_dashboard_data()
            self.dashboard.update_data(dashboard_data)

            sales_data = self.service.get_sales_trend(days=30)
            self.update_line_chart(self.sales_chart, sales_data)

            week_data = self.service.get_sales_trend(days=7)
            self.update_line_chart(self.quick_chart1, week_data)

            category_data = self.service.get_product_category_distribution()
            self.update_pie_chart(self.category_chart, category_data)
            self.update_pie_chart(self.quick_chart2, category_data)

            monthly_data = self.service.get_monthly_comparison(months=6)
            self.update_bar_chart(self.monthly_chart, monthly_data)

            top_data = self.service.get_top_products(limit=10)
            self.update_bar_chart(self.top_chart, top_data)

            customer_data = self.service.get_customer_analysis()
            self.update_pie_chart(self.customer_chart, customer_data)

        except Exception as e:
            print(f"加载数据失败: {e}")

    # ── 折线图 ─────────────────────────────────────────────────────────

    def update_line_chart(self, widget: ChartWidget, data: dict):
        plot = widget.get_plot()
        plot.setTitle(data.get("title", ""))

        labels = data.get("labels", [])
        datasets = data.get("datasets", [])
        x = list(range(len(labels)))

        for dataset in datasets:
            values = dataset.get("data", [])
            color = dataset.get("borderColor", "#000000")
            label = dataset.get("label", "")
            pen = pg.mkPen(color=color, width=2)
            plot.plot(x, values, pen=pen, name=label)

        if labels:
            axis = plot.getAxis("bottom")
            ticks = [(i, label) for i, label in enumerate(labels)]
            axis.setTicks([ticks])

    # ── 柱状图 ─────────────────────────────────────────────────────────

    def update_bar_chart(self, widget: ChartWidget, data: dict):
        plot = widget.get_plot()
        plot.setTitle(data.get("title", ""))

        labels = data.get("labels", [])
        datasets = data.get("datasets", [])
        n_labels = max(len(labels), 1)
        n_sets = max(len(datasets), 1)
        bar_width = 0.65 / n_sets

        for i, dataset in enumerate(datasets):
            values = dataset.get("data", [])
            color = dataset.get("backgroundColor", "#000000")
            label = dataset.get("label", "")
            x_positions = [j - 0.325 + (i + 0.5) * bar_width for j in range(n_labels)]
            bar = pg.BarGraphItem(
                x=x_positions, height=values,
                width=bar_width, brush=color, name=label
            )
            plot.addItem(bar)

        if labels:
            axis = plot.getAxis("bottom")
            ticks = [(i, label) for i, label in enumerate(labels)]
            axis.setTicks([ticks])

    # ── 饼图 ───────────────────────────────────────────────────────────

    def update_pie_chart(self, widget: ChartWidget, data: dict):
        view = widget.get_viewbox()

        labels = data.get("labels", [])
        datasets = data.get("datasets", [])

        slices = []
        if datasets:
            values = datasets[0].get("data", [])
            colors = datasets[0].get("backgroundColor", [])

            for i, (label, value) in enumerate(zip(labels, values)):
                color = colors[i] if i < len(colors) else "#888888"
                slices.append((label, value, color))

        pie = PieItem(slices)
        view.addItem(pie)

    # ── 导出 ───────────────────────────────────────────────────────────

    def export_report(self):
        # TODO: 实现报表导出功能
        pass


# ── 便捷函数 ───────────────────────────────────────────────────────────

def show_chart_window():
    """显示图表窗口"""
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication.instance() or QApplication(sys.argv)
    window = ChartWindow()
    window.show()
    return window
