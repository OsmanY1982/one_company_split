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
from core.dark_tool_theme import DARK_TEXT, DARK_TEXT_MUTED, DARK_BTN_PRIMARY, DARK_PREVIEW_STYLE, ACCENT_BLUE, ACCENT_BLUE_DIM, ACCENT_GOLD


class SmartWorkflowWidget(QWidget):
    """智能工作流可视化面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
        from core.modules.intelligence.smart_workflow import SmartWorkflowManager
        from core.modules.intelligence.workflow_engine import WorkflowEngine

        self._manager = SmartWorkflowManager()
        self._engine = WorkflowEngine()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("🔗 智能工作流引擎")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet(f"color: {DARK_TEXT};")
        layout.addWidget(title)

        desc = QLabel("自动化业务流程编排与执行引擎，支持预设工作流和自定义工作流")
        desc.setStyleSheet(f"color: {DARK_TEXT_MUTED}; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        presets_group = QGroupBox("预设工作流")
        presets_group.setStyleSheet(f"QGroupBox {{ font-weight: 600; border: 1px solid {ACCENT_BLUE_DIM}; border-radius: 8px; padding: 12px; margin-top: 10px; color: {DARK_TEXT}; }}")
        presets_layout = QVBoxLayout(presets_group)
        presets_layout.setSpacing(8)

        try:
            workflows = self._manager.list_available_workflows()
            for wf in workflows:
                row = QHBoxLayout()
                wf_name = wf.get('name', wf.name) if isinstance(wf, dict) else wf.name
                wf_status = wf.get('status', '就绪') if isinstance(wf, dict) else getattr(wf, 'status', '就绪')
                name_lbl = QLabel(f"📋 {wf_name}")
                name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 500; color: {DARK_TEXT};")
                row.addWidget(name_lbl)
                status_lbl = QLabel(wf_status)
                status_lbl.setStyleSheet(f"color: {ACCENT_BLUE} if wf_status == '就绪' else '{ACCENT_GOLD}'; font-size: 12px;")
                row.addWidget(status_lbl)
                row.addStretch()
                run_btn = QPushButton("▶ 执行")
                run_btn.setMinimumHeight(32)
                run_btn.setCursor(Qt.PointingHandCursor)
                run_btn.setStyleSheet(DARK_BTN_PRIMARY)
                row.addWidget(run_btn)
                presets_layout.addLayout(row)
        except Exception as e:
            presets_layout.addWidget(QLabel(f"加载工作流列表失败: {e}"))

        layout.addWidget(presets_group)

        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("工作流执行日志将显示在这里...")
        self._output.setStyleSheet(DARK_PREVIEW_STYLE)
        layout.addWidget(self._output)
