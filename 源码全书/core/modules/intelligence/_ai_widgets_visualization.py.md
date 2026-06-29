# `core/modules/intelligence/_ai_widgets_visualization.py`

> 路径：`core/modules/intelligence/_ai_widgets_visualization.py` | 行数：495


---


```python
# -*- coding: utf-8 -*-
"""数据可视化 Widget — DataVisualizationWidget

拆分自 _ai_widgets.py（原 784 行 → 本文件 ~280 行）
为纯后端模块 data_visualization / analysis_tools / data_import_tools 提供可视化界面

v2: 接入 pyqtgraph 实际图表渲染，原 JSON 文本展示保留为辅助调试区
"""

import json
import math

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGridLayout,
    QGroupBox, QPlainTextEdit, QTextEdit, QSplitter,
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QColor, QPainter, QPicture, QPen, QBrush

import pyqtgraph as pg

from core.dark_tool_theme import (
    DARK_DIALOG_STYLE, DARK_TABLE_STYLE, DARK_INPUT_STYLE,
    DARK_BTN_PRIMARY, DARK_BTN_DANGER, DARK_BTN_ACTIVE,
    DARK_PREVIEW_STYLE, DARK_EDITOR_STYLE, DARK_SEPARATOR,
    DARK_TEXT, DARK_TEXT_MUTED, DARK_BG, DARK_SURFACE, DARK_INPUT_BG,
    ACCENT_BLUE, ACCENT_BLUE_DIM, ACCENT_GOLD, DANGER_RED, DANGER_RED_DIM,
    apply_dark_tool_theme,
)


# ═══════════════════════════════════════════════════════════════════════
# 自定义 pyqtgraph 图形项
# ═══════════════════════════════════════════════════════════════════════

class PieItem(pg.GraphicsObject):
    """饼图图形项 — 复用 chart_window 中的实现"""

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

        start_angle = 90 * 16          # 从顶部开始
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


# ═══════════════════════════════════════════════════════════════════════
# 颜色映射 — 将 generate_chart_data 的 rgba 字符串转为色名/hex
# ═══════════════════════════════════════════════════════════════════════

def _rgba_to_qcolor(rgba_str):
    """将 'rgba(r,g,b,a)' 转为 QColor"""
    import re
    m = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)', rgba_str)
    if m:
        return QColor(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return QColor(rgba_str)


# ═══════════════════════════════════════════════════════════════════════
# 主 Widget
# ═══════════════════════════════════════════════════════════════════════

class DataVisualizationWidget(QWidget):
    """数据可视化面板 — pyqtgraph 渲染版"""

    def __init__(self, parent=None):
        super().__init__(parent)
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
        from core.modules.intelligence.data_visualization import DataVisualization
        from core.modules.intelligence.analysis_tools import AnalysisTools
        from core.modules.intelligence.data_import_tools import import_csv_to_db, import_json_to_db

        self._viz = DataVisualization()
        self._data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
        self._analysis = AnalysisTools(self._data_dir)
        self._import_csv = import_csv_to_db
        self._import_json = import_json_to_db
        self._current_viz_type = None   # 当前渲染类型: 'plot' | 'viewbox'
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # ── 标题 ──
        title = QLabel("📈 数据可视化")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet(f"color: {DARK_TEXT};")
        layout.addWidget(title)

        desc = QLabel("支持柱状图、折线图、饼图、热力图等多种图表类型的数据可视化引擎")
        desc.setStyleSheet(f"color: {DARK_TEXT_MUTED}; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # ── 图表类型按钮 ──
        chart_group = QGroupBox("图表类型")
        chart_group.setStyleSheet(
            f"QGroupBox {{ font-weight: 600; border: 1px solid {ACCENT_BLUE_DIM}; "
            f"border-radius: 8px; padding: 12px; margin-top: 10px; color: {DARK_TEXT}; }}"
        )
        chart_layout = QGridLayout(chart_group)
        chart_layout.setSpacing(10)

        chart_types = [
            ("bar", "📊 柱状图"), ("line", "📈 折线图"),
            ("pie", "🥧 饼图"), ("scatter", "🔵 散点图"),
            ("heatmap", "🔥 热力图"), ("radar", "🎯 雷达图"),
        ]
        self._chart_btns = {}
        for i, (ctype, cname) in enumerate(chart_types):
            btn = QPushButton(cname)
            btn.setMinimumHeight(44)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("chart_type", ctype)
            btn.setStyleSheet(
                f"QPushButton {{ background: {DARK_INPUT_BG}; border: 2px solid {ACCENT_BLUE_DIM}; "
                f"border-radius: 8px; font-size: 13px; font-weight: 500; color: {DARK_TEXT}; }} "
                f"QPushButton:checked {{ border-color: {ACCENT_BLUE}; background: rgba(100,140,255,45); color: {ACCENT_BLUE}; }} "
                f"QPushButton:hover {{ background: rgba(100,140,255,25); }}"
            )
            self._chart_btns[ctype] = btn
            chart_layout.addWidget(btn, i // 3, i % 3)

        layout.addWidget(chart_group)

        # ── 数据源输入 ──
        data_group = QGroupBox("数据源")
        data_group.setStyleSheet(f"QGroupBox {{ font-weight: 600; border: 1px solid {ACCENT_BLUE_DIM}; border-radius: 8px; padding: 12px; margin-top: 10px; color: {DARK_TEXT}; }}")
        data_layout = QVBoxLayout(data_group)
        self._data_input = QPlainTextEdit()
        self._data_input.setPlaceholderText(
            '输入 JSON 数据，如: [{"label":"A","value":10},{"label":"B","value":20}]'
        )
        self._data_input.setMaximumHeight(100)
        self._data_input.setStyleSheet(
            f"background: {DARK_INPUT_BG}; border: 1px solid {ACCENT_BLUE_DIM}; "
            f"border-radius: 6px; padding: 8px; font-size: 12px; color: {DARK_TEXT};"
        )
        data_layout.addWidget(self._data_input)

        btn_layout = QHBoxLayout()
        gen_btn = QPushButton("▶ 生成图表")
        gen_btn.setMinimumHeight(40)
        gen_btn.setCursor(Qt.PointingHandCursor)
        gen_btn.setStyleSheet(DARK_BTN_PRIMARY)
        gen_btn.clicked.connect(self._generate_chart)
        btn_layout.addWidget(gen_btn)
        btn_layout.addStretch()
        data_layout.addLayout(btn_layout)

        layout.addWidget(data_group)

        # ── 图表渲染区 + JSON 调试区（垂直分割） ──
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet(f"QSplitter::handle {{ height: 4px; background: {ACCENT_BLUE_DIM}; }}")

        # pyqtgraph 渲染容器
        self._chart_container = pg.GraphicsLayoutWidget()
        self._chart_container.setMinimumHeight(280)
        self._chart_container.setBackground((14, 18, 32))
        splitter.addWidget(self._chart_container)

        # JSON 调试输出
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("图表 JSON 数据 / 调试信息将显示在这里...")
        self._output.setStyleSheet(DARK_PREVIEW_STYLE)
        self._output.setMinimumHeight(100)
        splitter.addWidget(self._output)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

    # ── 核心：生成图表 ─────────────────────────────────────────────────

    def _generate_chart(self):
        selected = None
        for ctype, btn in self._chart_btns.items():
            if btn.isChecked():
                selected = ctype
                break
        if not selected:
            self._output.setText("请先选择一种图表类型")
            return

        raw = self._data_input.toPlainText().strip()
        if raw:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                self._output.setText("JSON 格式错误，请检查数据格式")
                return
        else:
            data = [{"label": f"项目{i}", "value": i * 10 + 10} for i in range(1, 8)]

        # 清除旧图表
        self._chart_container.clear()
        self._current_viz_type = None

        # 根据类型路由渲染
        if selected in ("bar", "line", "pie"):
            self._render_from_service(data, selected)
        elif selected == "scatter":
            self._render_scatter(data)
        elif selected == "heatmap":
            self._render_heatmap(data)
        elif selected == "radar":
            self._render_radar(data)
        else:
            self._output.setText(f"不支持的图表类型: {selected}")

    # ── 通过 data_visualization.py 渲染（bar / line / pie）─────────────

    def _render_from_service(self, data, chart_type):
        try:
            result = self._viz.generate_chart_data(data, chart_type)
        except Exception as e:
            self._output.setText(f"生成图表数据失败: {e}")
            return

        if "error" in result:
            self._output.setText(f"数据错误: {result['error']}")
            return

        # 调试 JSON
        self._output.setText(json.dumps(result, ensure_ascii=False, indent=2))

        chart_data = result.get("data", {})
        labels = chart_data.get("labels", [])
        datasets = chart_data.get("datasets", [])

        if chart_type == "bar":
            self._draw_bar(labels, datasets)
        elif chart_type == "line":
            self._draw_line(labels, datasets)
        elif chart_type == "pie":
            self._draw_pie(labels, datasets)

    # ── 柱状图 ─────────────────────────────────────────────────────────

    def _draw_bar(self, labels, datasets):
        plot = self._chart_container.addPlot()
        plot.showGrid(x=True, y=True, alpha=0.3)
        self._current_viz_type = 'plot'

        n_labels = max(len(labels), 1)
        n_sets = max(len(datasets), 1)
        bar_width = 0.65 / n_sets

        for i, ds in enumerate(datasets):
            values = ds.get("data", [])
            color_str = ds.get("backgroundColor", "#3498db")
            label = ds.get("label", "")
            color = _rgba_to_qcolor(color_str)
            x_positions = [j - 0.325 + (i + 0.5) * bar_width for j in range(n_labels)]
            bar = pg.BarGraphItem(
                x=x_positions, height=values,
                width=bar_width, brush=color, name=label
            )
            plot.addItem(bar)

        if labels:
            ticks = [(i, label) for i, label in enumerate(labels)]
            plot.getAxis("bottom").setTicks([ticks])

    # ── 折线图 ─────────────────────────────────────────────────────────

    def _draw_line(self, labels, datasets):
        plot = self._chart_container.addPlot()
        plot.showGrid(x=True, y=True, alpha=0.3)
        self._current_viz_type = 'plot'

        x = list(range(len(labels)))

        for ds in datasets:
            values = ds.get("data", [])
            color_str = ds.get("borderColor", "#2ecc71")
            label = ds.get("label", "")
            fill = ds.get("fill", False)
            color = _rgba_to_qcolor(color_str)
            pen = pg.mkPen(color=color, width=2.5)
            if fill:
                fill_color = _rgba_to_qcolor(ds.get("backgroundColor", color_str))
                fill_color.setAlpha(40)
                plot.plot(x, values, pen=pen, name=label, fillLevel=0,
                          fillBrush=fill_color)
            else:
                plot.plot(x, values, pen=pen, name=label)

        if labels:
            ticks = [(i, label) for i, label in enumerate(labels)]
            plot.getAxis("bottom").setTicks([ticks])

    # ── 饼图（ViewBox + PieItem）───────────────────────────────────────

    def _draw_pie(self, labels, datasets):
        view = self._chart_container.addViewBox()
        view.setAspectLocked(True)
        self._current_viz_type = 'viewbox'

        slices = []
        if datasets:
            values = datasets[0].get("data", [])
            colors = datasets[0].get("backgroundColor", [])

            for i, (label, value) in enumerate(zip(labels, values)):
                color = colors[i] if i < len(colors) else "#888888"
                slices.append((label, value, color))

        pie = PieItem(slices)
        view.addItem(pie)

    # ── 散点图 ─────────────────────────────────────────────────────────

    def _render_scatter(self, data):
        plot = self._chart_container.addPlot()
        plot.showGrid(x=True, y=True, alpha=0.3)
        self._current_viz_type = 'plot'

        # 解析数据: [{"x":..., "y":..., "label":...}, ...]
        xs = [item.get("x", item.get("value", 0)) for item in data]
        ys = [item.get("y", item.get("value", 0)) for item in data]

        scatter = pg.ScatterPlotItem(
            x=xs, y=ys, size=12,
            pen=pg.mkPen(color=(255, 255, 255), width=1),
            brush=pg.mkBrush(52, 152, 219, 180),
            symbol='o',
        )
        plot.addItem(scatter)
        plot.setLabel("bottom", "X")
        plot.setLabel("left", "Y")

        # 调试输出
        debug_data = {
            "type": "scatter",
            "data": {"points": [{"x": x, "y": y} for x, y in zip(xs, ys)]}
        }
        self._output.setText(json.dumps(debug_data, ensure_ascii=False, indent=2))

    # ── 热力图 ─────────────────────────────────────────────────────────

    def _render_heatmap(self, data):
        plot = self._chart_container.addPlot()
        plot.showGrid(x=True, y=True, alpha=0.2)
        self._current_viz_type = 'plot'

        # 期望数据格式: [{"row":0, "values":[1,2,3]}, ...] 或 [{"label":"A","value":10},...] 自动构造网格
        n = len(data)
        if n == 0:
            self._output.setText("热力图需要数据，请输入包含 values 数组的 JSON 或键值对") 
            return

        # 判断是不是二维数据
        if "values" in data[0] and isinstance(data[0]["values"], list):
            grid = [item["values"] for item in data]
        else:
            # 一维数据 → 构造为单行热力图
            values = [item.get("value", item.get("y", 0)) for item in data]
            grid = [values]

        import numpy as np
        grid_np = np.array(grid, dtype=float)

        img = pg.ImageItem(grid_np)
        # 设置颜色映射
        from pyqtgraph import colormap
        img.setLookupTable(colormap.get('plasma').getLookupTable())
        plot.addItem(img)

        # 设置坐标范围
        rows, cols = grid_np.shape
        img.setRect(-0.5, -0.5, cols, rows)

        # 颜色条
        bar = pg.ColorBarItem(
            values=(grid_np.min(), grid_np.max()),
            colorMap=colormap.get('plasma'),
            width=15,
            interactive=False,
        )
        bar.setImageItem(img)
        bar.setParentItem(plot.getViewBox())
        bar.anchor(item=plot.getViewBox(), rect=(1.02, 0), pos=(0, 0))
        plot.getViewBox().setMouseEnabled(x=True, y=True)

        debug_data = {
            "type": "heatmap",
            "data": {"grid": grid_np.tolist(), "shape": list(grid_np.shape)}
        }
        self._output.setText(json.dumps(debug_data, ensure_ascii=False, indent=2))

    # ── 雷达图 ─────────────────────────────────────────────────────────

    def _render_radar(self, data):
        plot = self._chart_container.addPlot()
        plot.showGrid(x=True, y=True, alpha=0.2)
        plot.setAspectLocked(True)
        self._current_viz_type = 'plot'

        # 解析数据: [{"label":"A","value":10}, ...]
        labels = [item.get("label", str(i)) for i, item in enumerate(data)]
        values = [item.get("value", 0) for item in data]
        n = len(values)
        if n < 3:
            self._output.setText("雷达图至少需要 3 个数据点")
            return

        # 计算多边形顶点（极坐标 → 直角坐标）
        angles = [2 * math.pi * i / n for i in range(n)]
        points = []
        for angle, val in zip(angles, values):
            x = val * math.cos(angle)
            y = val * math.sin(angle)
            points.append((x, y))
        # 闭合
        points.append(points[0])
        xs, ys = zip(*points)

        # 绘制填充多边形
        fill = pg.FillBetweenItem(
            pg.PlotDataItem(xs, ys),
            pg.PlotDataItem([0], [0]),  # origin filled
            brush=pg.mkBrush(52, 152, 219, 80)
        )
        plot.addItem(fill)

        # 绘制边框
        plot.plot(xs, ys, pen=pg.mkPen(color=(52, 152, 219), width=2))

        # 绘制轴线
        for angle in angles:
            r = max(values) * 1.1 if max(values) > 0 else 10
            plot.plot(
                [0, r * math.cos(angle)],
                [0, r * math.sin(angle)],
                pen=pg.mkPen(color=(180, 180, 180), width=0.8, style=Qt.DashLine)
            )

        # 标签
        for angle, label, val in zip(angles, labels, values):
            r = val * 1.15 if val > 0 else 1
            text = pg.TextItem(label, color=(80, 80, 80), anchor=(0.5, 0.5))
            text.setPos(r * math.cos(angle), r * math.sin(angle))
            plot.addItem(text)

        # 去掉坐标轴数字
        plot.getAxis("bottom").setTicks([])
        plot.getAxis("left").setTicks([])

        debug_data = {
            "type": "radar",
            "data": [{"label": l, "value": v} for l, v in zip(labels, values)]
        }
        self._output.setText(json.dumps(debug_data, ensure_ascii=False, indent=2))

```
