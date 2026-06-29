# -*- coding: utf-8 -*-
"""
数据可视化模块 - 图表生成、报表展示
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class DataVisualization:
    """数据可视化工具"""
    
    @staticmethod
    def generate_chart_data(data: List[Dict], chart_type: str = "bar") -> Dict[str, Any]:
        """生成图表数据"""
        try:
            if chart_type == "bar":
                return {
                    "type": "bar",
                    "data": {
                        "labels": [item.get("label", str(i)) for i, item in enumerate(data)],
                        "datasets": [{
                            "label": "数据",
                            "data": [item.get("value", 0) for item in data],
                            "backgroundColor": "rgba(52, 152, 219, 0.5)",
                            "borderColor": "rgba(52, 152, 219, 1)",
                            "borderWidth": 1,
                        }]
                    }
                }
            elif chart_type == "line":
                return {
                    "type": "line",
                    "data": {
                        "labels": [item.get("label", str(i)) for i, item in enumerate(data)],
                        "datasets": [{
                            "label": "趋势",
                            "data": [item.get("value", 0) for item in data],
                            "borderColor": "rgba(46, 204, 113, 1)",
                            "backgroundColor": "rgba(46, 204, 113, 0.1)",
                            "fill": True,
                        }]
                    }
                }
            elif chart_type == "pie":
                colors = [
                    "rgba(52, 152, 219, 0.7)",
                    "rgba(46, 204, 113, 0.7)",
                    "rgba(231, 76, 60, 0.7)",
                    "rgba(241, 196, 15, 0.7)",
                    "rgba(155, 89, 182, 0.7)",
                ]
                return {
                    "type": "pie",
                    "data": {
                        "labels": [item.get("label", str(i)) for i, item in enumerate(data)],
                        "datasets": [{
                            "data": [item.get("value", 0) for item in data],
                            "backgroundColor": colors[:len(data)],
                        }]
                    }
                }
            else:
                return {"error": f"不支持的图表类型: {chart_type}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def generate_table(data: List[Dict], columns: List[str] = None) -> Dict[str, Any]:
        """生成表格数据"""
        try:
            if not data:
                return {"headers": [], "rows": []}
            
            if columns is None:
                columns = list(data[0].keys())
            
            rows = []
            for item in data:
                row = [str(item.get(col, "")) for col in columns]
                rows.append(row)
            
            return {
                "headers": columns,
                "rows": rows,
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def generate_report(title: str, sections: List[Dict]) -> str:
        """生成HTML报表"""
        try:
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .section {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #3498db;
            color: white;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .metric {{
            display: inline-block;
            margin: 10px;
            padding: 15px;
            background: #3498db;
            color: white;
            border-radius: 4px;
            min-width: 120px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
        }}
        .metric-label {{
            font-size: 12px;
            opacity: 0.9;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p>生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
"""
            
            for section in sections:
                section_type = section.get("type", "text")
                section_title = section.get("title", "")
                
                html += f'<div class="section">\n'
                html += f'<h2>{section_title}</h2>\n'
                
                if section_type == "text":
                    html += f'<p>{section.get("content", "")}</p>\n'
                    
                elif section_type == "metrics":
                    metrics = section.get("metrics", [])
                    html += '<div>\n'
                    for metric in metrics:
                        html += f'''
                        <div class="metric">
                            <div class="metric-value">{metric.get("value", "")}</div>
                            <div class="metric-label">{metric.get("label", "")}</div>
                        </div>
'''
                    html += '</div>\n'
                    
                elif section_type == "table":
                    table_data = section.get("data", [])
                    if table_data:
                        headers = list(table_data[0].keys())
                        html += '<table>\n<thead>\n<tr>\n'
                        for header in headers:
                            html += f'<th>{header}</th>\n'
                        html += '</tr>\n</thead>\n<tbody>\n'
                        
                        for row in table_data:
                            html += '<tr>\n'
                            for header in headers:
                                html += f'<td>{row.get(header, "")}</td>\n'
                            html += '</tr>\n'
                        html += '</tbody>\n</table>\n'
                        
                elif section_type == "chart":
                    chart_data = section.get("data", [])
                    chart_type = section.get("chart_type", "bar")
                    # 这里可以集成Chart.js等图表库
                    html += f'<p>图表类型: {chart_type}</p>\n'
                    html += '<pre>' + json.dumps(chart_data, ensure_ascii=False, indent=2) + '</pre>\n'
                
                html += '</div>\n'
            
            html += f'''
        <div class="footer">
            <p>由 Iqra AI助手生成</p>
        </div>
    </div>
</body>
</html>
'''
            
            return html
            
        except Exception as e:
            return f"<html><body><h1>错误</h1><p>{str(e)}</p></body></html>"
    
    @staticmethod
    def save_report(html: str, output_path: str) -> bool:
        """保存报表到文件"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            return True
        except Exception as e:
            print(f"保存报表失败: {e}")
            return False
    
    @staticmethod
    def generate_summary(data: Dict[str, Any]) -> str:
        """生成数据摘要"""
        try:
            summary = []
            
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    summary.append(f"{key}: {value}")
                elif isinstance(value, list):
                    summary.append(f"{key}: {len(value)} 项")
                elif isinstance(value, dict):
                    summary.append(f"{key}: {len(value)} 个字段")
            
            return "\n".join(summary) if summary else "无数据"
            
        except Exception as e:
            return f"生成摘要失败: {e}"


from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt


class VisualizationWidget(QWidget):
    """数据可视化控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 标题
        title = QLabel("📊 数据可视化")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # 数据输入区域
        input_group = QGroupBox("数据输入 (JSON格式)")
        input_layout = QVBoxLayout(input_group)
        
        self._data_input = QTextEdit()
        self._data_input.setPlaceholderText('''[
  {"label": "A", "value": 10},
  {"label": "B", "value": 20},
  {"label": "C", "value": 30}
]''')
        self._data_input.setMaximumHeight(150)
        input_layout.addWidget(self._data_input)
        
        # 图表类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("图表类型:"))
        self._chart_type = QComboBox()
        self._chart_type.addItems(["柱状图 (bar)", "折线图 (line)", "饼图 (pie)", "表格 (table)"])
        type_layout.addWidget(self._chart_type)
        
        self._generate_btn = QPushButton("生成图表")
        self._generate_btn.setStyleSheet("""
            QPushButton {
                background: #3498db; color: white; padding: 8px 20px;
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background: #2980b9; }
        """)
        self._generate_btn.clicked.connect(self._generate)
        type_layout.addWidget(self._generate_btn)
        
        input_layout.addLayout(type_layout)
        layout.addWidget(input_group)
        
        # 结果显示区域
        result_group = QGroupBox("结果")
        result_layout = QVBoxLayout(result_group)
        
        self._result_table = QTableWidget()
        self._result_table.setColumnCount(0)
        self._result_table.setRowCount(0)
        self._result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        result_layout.addWidget(self._result_table)
        
        # HTML预览
        self._web_view = QWebEngineView()
        self._web_view.setMinimumHeight(300)
        result_layout.addWidget(self._web_view)
        
        layout.addWidget(result_group)
        
        # 报表生成
        report_group = QGroupBox("报表生成")
        report_layout = QVBoxLayout(report_group)
        
        self._report_title = QTextEdit()
        self._report_title.setPlaceholderText("报表标题")
        self._report_title.setMaximumHeight(50)
        report_layout.addWidget(self._report_title)
        
        self._report_btn = QPushButton("生成HTML报表")
        self._report_btn.clicked.connect(self._generate_report)
        report_layout.addWidget(self._report_btn)
        
        layout.addWidget(report_group)
        layout.addStretch()
        
    def _generate(self):
        """生成图表"""
        try:
            data_text = self._data_input.toPlainText().strip()
            if not data_text:
                QMessageBox.warning(self, "提示", "请输入数据")
                return
            
            data = json.loads(data_text)
            chart_type = self._chart_type.currentText().split(" ")[0]
            
            if "表格" in self._chart_type.currentText():
                # 生成表格
                table_data = DataVisualization.generate_table(data)
                if "error" in table_data:
                    QMessageBox.critical(self, "错误", table_data["error"])
                    return
                
                self._result_table.setColumnCount(len(table_data["headers"]))
                self._result_table.setRowCount(len(table_data["rows"]))
                self._result_table.setHorizontalHeaderLabels(table_data["headers"])
                
                for i, row in enumerate(table_data["rows"]):
                    for j, cell in enumerate(row):
                        self._result_table.setItem(i, j, QTableWidgetItem(cell))
            else:
                # 生成图表数据
                chart_data = DataVisualization.generate_chart_data(data, chart_type)
                if "error" in chart_data:
                    QMessageBox.critical(self, "错误", chart_data["error"])
                    return
                
                # 显示JSON数据
                html = f"""
                <html>
                <body>
                    <h3>图表数据 ({chart_type})</h3>
                    <pre>{json.dumps(chart_data, ensure_ascii=False, indent=2)}</pre>
                </body>
                </html>
                """
                self._web_view.setHtml(html)
                
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "错误", f"JSON格式错误: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))
    
    def _generate_report(self):
        """生成报表"""
        try:
            title = self._report_title.toPlainText().strip() or "数据报表"
            
            sections = [
                {
                    "type": "text",
                    "title": "概述",
                    "content": "这是自动生成的数据报表",
                },
                {
                    "type": "metrics",
                    "title": "关键指标",
                    "metrics": [
                        {"label": "总数据量", "value": "100"},
                        {"label": "增长率", "value": "15%"},
                        {"label": "完成率", "value": "98%"},
                    ],
                },
            ]
            
            html = DataVisualization.generate_report(title, sections)
            self._web_view.setHtml(html)
            
            # 保存到文件
            output_path = os.path.join(os.path.expanduser("~"), "report.html")
            if DataVisualization.save_report(html, output_path):
                QMessageBox.information(self, "完成", f"报表已保存到: {output_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    widget = VisualizationWidget()
    widget.setWindowTitle("数据可视化")
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec_())
