# `intelligence/_shell_dialogs.py`

> 路径：`intelligence/_shell_dialogs.py` | 行数：109


---


```python
# -*- coding: utf-8 -*-
"""
AI 助手模块 v3 — 支持本地模型管理
- 标签1: 💬 AI 对话 (iqra ChatWindow)
- 标签2: ⚡ 快捷工具 (模板、本地模型、系统状态)
- 标签3~6: 增强功能（智能对话、快捷操作、系统监控、高级功能）

改进:
- 添加 Ollama 本地模型管理（检测、启动、下载、切换）
- 添加多尺寸模型（超小/中等/大模型）
- 增强本地模型使用体验
- 优化界面布局
- 优化导入路径管理，提升模块加载稳定性
"""

import sys
import os
import subprocess
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

# ── 路径管理 ──────────────────────────────────────────────────────────────────
# 确保项目根目录（one_company_desktop）在 sys.path 中，
# 使「from iqra.xxx import ...」和「from core.modules.intelligence.xxx import ...」
# 在所有调用场景下均可正常工作。
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
# ─────────────────────────────────────────────────────────────────────────────

from PyQt5.QtWidgets import (
    QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QGridLayout, QMessageBox,
    QGroupBox, QComboBox, QDialog, QFormLayout, QCheckBox,
    QProgressBar, QTextEdit, QPlainTextEdit, QApplication,
    QScrollArea, QFrame, QSizePolicy,
)
from PyQt5.QtCore import Qt, QObject, QTimer, QThread, pyqtSignal, QUrl, QPropertyAnimation, QEasingCurve, pyqtProperty, QRect, QParallelAnimationGroup
from PyQt5.QtGui import QFont, QPalette

from core.modules.intelligence._stubs import app_state

from ._ai_widgets import SmartWorkflowWidget, BusinessAIWidget
from core.dark_tool_theme import apply_dark_tool_theme


# ═══════════════════════════════════════════
# ═══════════════════════════════════════════

class SystemMonitorDialog(QDialog):
    """系统监控弹窗包装器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        apply_dark_tool_theme(self)
        self.setWindowTitle("系统监控")
        self.setMinimumSize(700, 500)
        layout = QVBoxLayout(self)
        try:
            from core.modules.intelligence.system_monitor import SystemMonitorWidget
            self._widget = SystemMonitorWidget(self)
            layout.addWidget(self._widget)
        except ImportError as e:
            layout.addWidget(QLabel(f"模块加载失败: {e}"))


class AIDashboardDialog(QDialog):
    """AI仪表板弹窗包装器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        apply_dark_tool_theme(self)
        self.setWindowTitle("AI 仪表板")
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)
        try:
            from core.modules.intelligence.ai_dashboard_window import AIDashboardWindow
            self._widget = AIDashboardWindow(self)
            layout.addWidget(self._widget)
        except ImportError as e:
            layout.addWidget(QLabel(f"模块加载失败: {e}"))


class SmartWorkflowDialog(QDialog):
    """智能工作流弹窗包装器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        apply_dark_tool_theme(self)
        self.setWindowTitle("智能工作流")
        self.setMinimumSize(700, 500)
        layout = QVBoxLayout(self)
        layout.addWidget(SmartWorkflowWidget(self))


class BusinessAIDialog(QDialog):
    """业务AI弹窗包装器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        apply_dark_tool_theme(self)
        self.setWindowTitle("业务 AI 助手")
        self.setMinimumSize(700, 500)
        layout = QVBoxLayout(self)
        layout.addWidget(BusinessAIWidget(self))


# ═══════════════════════════════════════════
# AI 助手主窗口 — 星球导航模式
# ═══════════════════════════════════════════


```
