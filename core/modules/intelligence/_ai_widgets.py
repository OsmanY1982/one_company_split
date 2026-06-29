# -*- coding: utf-8 -*-
"""
AI 助手模块 v3 — 兼容入口（原 _ai_widgets.py 784 行 → 拆分为 7 个文件）
- _ai_widgets_core.py       → SuperIntelligenceWidget（~210 行）
- _ai_widgets_anomaly.py    → AnomalyDetectorWidget（~115 行）
- _ai_widgets_recommendation.py → RecommendationEngineWidget（~85 行）
- _ai_widgets_visualization.py  → DataVisualizationWidget（~115 行）
- _ai_widgets_workflow.py   → SmartWorkflowWidget（~70 行）
- _ai_widgets_business.py   → BusinessAIWidget（~140 行）

本文件作为兼容 shim：保持所有现有 import 路径不变，统一 re-export。
"""

import sys
import os

# ── 路径管理 ──────────────────────────────────────────────────────────────────
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
# ─────────────────────────────────────────────────────────────────────────────

from ._ai_widgets_core import SuperIntelligenceWidget
from ._ai_widgets_anomaly import AnomalyDetectorWidget
from ._ai_widgets_recommendation import RecommendationEngineWidget
from ._ai_widgets_visualization import DataVisualizationWidget
from ._ai_widgets_workflow import SmartWorkflowWidget
from ._ai_widgets_business import BusinessAIWidget

# 模块入口常量
MODULE_ID = "ai_assistant"
MODULE_NAME = "🤖 AI 助手"
MODULE_ICON = "🤖"
MODULE_DESCRIPTION = "AI 智能助手 - 支持云端/本地多模型"


def create_module(parent=None):
    """创建模块实例（延迟导入避免循环依赖）"""
    from .ai_assistant_window import AIAssistantWindow
    window = AIAssistantWindow(parent)
    return window
