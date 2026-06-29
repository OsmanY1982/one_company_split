# `iqra/modules/intelligence/_ai_widgets_visualization.py`

> 路径：`iqra/modules/intelligence/_ai_widgets_visualization.py` | 行数：126


---


```python
# -*- coding: utf-8 -*-
"""数据可视化 Widget — DataVisualizationWidget

拆分自 _ai_widgets.py（原 784 行 → 本文件 ~115 行）
为纯后端模块 data_visualization / analysis_tools / data_import_tools 提供可视化界面
"""

import json

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGridLayout,
    QGroupBox, QPlainTextEdit, QTextEdit,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class DataVisualizationWidget(QWidget):
    """数据可视化面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
        from modules.intelligence.data_visualization import DataVisualization
        from modules.intelligence.analysis_tools import AnalysisTools
        from modules.intelligence.data_import_tools import import_csv_to_db, import_json_to_db

        self._viz = DataVisualization()
        self._data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
        self._analysis = AnalysisTools(self._data_dir)
        self._import_csv = import_csv_to_db
        self._import_json = import_json_to_db
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("📈 数据可视化")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet("color: #1a202c;")
        layout.addWidget(title)

        desc = QLabel("支持柱状图、折线图、饼图、热力图等多种图表类型的数据可视化引擎")
        desc.setStyleSheet("color: #718096; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        chart_group = QGroupBox("图表类型")
        chart_group.setStyleSheet("QGroupBox { font-weight: 600; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-top: 10px; }")
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
            btn.setStyleSheet("QPushButton { background: #f7fafc; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 13px; font-weight: 500; } QPushButton:checked { border-color: #3498db; background: #ebf5fb; color: #2980b9; } QPushButton:hover { background: #edf2f7; }")
            self._chart_btns[ctype] = btn
            chart_layout.addWidget(btn, i // 3, i % 3)

        layout.addWidget(chart_group)

        data_group = QGroupBox("数据源")
        data_group.setStyleSheet(chart_group.styleSheet())
        data_layout = QVBoxLayout(data_group)
        self._data_input = QPlainTextEdit()
        self._data_input.setPlaceholderText('输入 JSON 数据，如: [{"label":"A","value":10},{"label":"B","value":20}]')
        self._data_input.setMaximumHeight(100)
        self._data_input.setStyleSheet("background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px; font-size: 12px;")
        data_layout.addWidget(self._data_input)

        btn_layout = QHBoxLayout()
        gen_btn = QPushButton("▶ 生成图表")
        gen_btn.setMinimumHeight(40)
        gen_btn.setCursor(Qt.PointingHandCursor)
        gen_btn.setStyleSheet("QPushButton { background: #9b59b6; color: white; border: none; border-radius: 8px; padding: 10px 24px; font-size: 14px; font-weight: 600; } QPushButton:hover { background: #8e44ad; }")
        gen_btn.clicked.connect(self._generate_chart)
        btn_layout.addWidget(gen_btn)
        btn_layout.addStretch()
        data_layout.addLayout(btn_layout)

        layout.addWidget(data_group)

        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("图表 JSON 数据将显示在这里...")
        self._output.setStyleSheet("background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 13px; font-family: monospace;")
        layout.addWidget(self._output)

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

        try:
            result = self._viz.generate_chart_data(data, selected)
            self._output.setText(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as e:
            self._output.setText(f"生成图表失败: {e}")

```
