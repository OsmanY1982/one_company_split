# `iqra/modules/intelligence/_ai_widgets_workflow.py`

> 路径：`iqra/modules/intelligence/_ai_widgets_workflow.py` | 行数：79


---


```python
# -*- coding: utf-8 -*-
"""智能工作流 Widget — SmartWorkflowWidget

拆分自 _ai_widgets.py（原 784 行 → 本文件 ~70 行）
为纯后端模块 smart_workflow / workflow_engine 提供可视化界面
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGroupBox,
    QTextEdit,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class SmartWorkflowWidget(QWidget):
    """智能工作流可视化面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
        from modules.intelligence.smart_workflow import SmartWorkflowManager
        from modules.intelligence.workflow_engine import WorkflowEngine

        self._manager = SmartWorkflowManager()
        self._engine = WorkflowEngine()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("🔗 智能工作流引擎")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet("color: #1a202c;")
        layout.addWidget(title)

        desc = QLabel("自动化业务流程编排与执行引擎，支持预设工作流和自定义工作流")
        desc.setStyleSheet("color: #718096; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        presets_group = QGroupBox("预设工作流")
        presets_group.setStyleSheet("QGroupBox { font-weight: 600; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-top: 10px; }")
        presets_layout = QVBoxLayout(presets_group)
        presets_layout.setSpacing(8)

        try:
            workflows = self._manager.list_available_workflows()
            for wf in workflows:
                row = QHBoxLayout()
                wf_name = wf.get('name', wf.name) if isinstance(wf, dict) else wf.name
                wf_status = wf.get('status', '就绪') if isinstance(wf, dict) else getattr(wf, 'status', '就绪')
                name_lbl = QLabel(f"📋 {wf_name}")
                name_lbl.setStyleSheet("font-size: 13px; font-weight: 500;")
                row.addWidget(name_lbl)
                status_lbl = QLabel(wf_status)
                status_lbl.setStyleSheet(f"color: {'#38a169' if wf_status == '就绪' else '#718096'}; font-size: 12px;")
                row.addWidget(status_lbl)
                row.addStretch()
                run_btn = QPushButton("▶ 执行")
                run_btn.setMinimumHeight(32)
                run_btn.setCursor(Qt.PointingHandCursor)
                run_btn.setStyleSheet("QPushButton { background: #38a169; color: white; border: none; border-radius: 6px; padding: 6px 14px; font-size: 12px; } QPushButton:hover { background: #2f855a; }")
                row.addWidget(run_btn)
                presets_layout.addLayout(row)
        except Exception as e:
            presets_layout.addWidget(QLabel(f"加载工作流列表失败: {e}"))

        layout.addWidget(presets_group)

        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("工作流执行日志将显示在这里...")
        self._output.setStyleSheet("background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 13px;")
        layout.addWidget(self._output)

```
