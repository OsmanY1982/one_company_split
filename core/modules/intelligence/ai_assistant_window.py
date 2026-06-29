# -*- coding: utf-8 -*-
"""
AI 助手模块 v3 — 支持本地模型管理
- 标签1: 💬 AI 对话 (AgentBridge 完整对话窗口)
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

from ._ai_shared import SUPER_INTELLIGENCE_AVAILABLE
from ._navigation_hud import NavigationHUD
from ._shell_dialogs import (
    SystemMonitorDialog,
    SmartWorkflowDialog, BusinessAIDialog,
)
from ._ai_widgets import (
    SuperIntelligenceWidget, AnomalyDetectorWidget,
    RecommendationEngineWidget, DataVisualizationWidget,
)
from core.dark_tool_theme import apply_dark_tool_theme



# ═══════════════════════════════════════════
# AI 助手主窗口 — 星球导航模式
# ═══════════════════════════════════════════

class AIAssistantWindow(QMainWindow):
    """AI 助手 · CREW — 13颗星球导航模式"""

    def __init__(self, parent=None, iqra_engine=None):
        super().__init__(parent)
        self._iqra = iqra_engine
        self._role = "admin"
        self.setWindowTitle("AI 助手 · CREW")
        self.setMinimumSize(1200, 900)
        self.resize(1200, 900)
        self._build_ui()

    def _build_ui(self):
        from core.cosmic import CosmicBackground
        bg = CosmicBackground()
        self.setCentralWidget(bg)

        self._hud = NavigationHUD(self)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._hud.planet_clicked = self._on_planet_clicked
        self._hud.raise_()

        header = QWidget(self)
        header.setAttribute(Qt.WA_TranslucentBackground)
        header.setFixedHeight(70)
        header.setGeometry(0, 10, self.width(), 70)

        hl = QVBoxLayout(header)
        hl.setSpacing(2)
        title = QLabel("AI 助手")
        title.setStyleSheet(
            "color: #ddaaff; font-size: 24px; font-weight: 800;"
            "letter-spacing: 8px; background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)
        hl.addWidget(title)
        subtitle = QLabel("CREW · 13颗智能星球")
        subtitle.setStyleSheet(
            "color: #776699; font-size: 11px; letter-spacing: 3px;"
            "background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        hl.addWidget(subtitle)

        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(170,80,255,50),
                stop:0.5 rgba(200,120,255,120),
                stop:0.7 rgba(170,80,255,50), stop:1 transparent);
            border: none;
        """)
        hl.addWidget(line)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_hud'):
            self._hud.setGeometry(0, 0, self.width(), self.height())

    # ═══════ 行星点击路由 ═══════
    def _on_planet_clicked(self, planet_id):
        if planet_id == "iqra_chat":
            from core.modules.intelligence.ai_chat_window import AIChatWindow
            self._chat_win = AIChatWindow(iqra_engine=self._iqra)
            self._chat_win.show()
        elif planet_id == "super_intelligence":
            if SUPER_INTELLIGENCE_AVAILABLE:
                dlg = QDialog(self)
                dlg.setWindowTitle("超级智能")
                dlg.setMinimumSize(750, 550)
                layout = QVBoxLayout(dlg)
                layout.addWidget(SuperIntelligenceWidget(dlg))
                dlg.show()
            else:
                QMessageBox.information(self, "提示", "超级智能模块未安装，请检查依赖")
        elif planet_id == "enhanced_chat":
            try:
                from core.modules.intelligence.enhanced_chat import EnhancedChatWidget
                dlg = QDialog(self)
                dlg.setWindowTitle("增强对话")
                dlg.setMinimumSize(800, 600)
                layout = QVBoxLayout(dlg)
                layout.addWidget(EnhancedChatWidget(dlg))
                dlg.show()
            except ImportError as e:
                QMessageBox.warning(self, "错误", f"增强对话模块加载失败: {e}")
        elif planet_id == "knowledge_base":
            try:
                from core.modules.intelligence.knowledge_base import KnowledgeBase
                kb = KnowledgeBase()
                from PyQt5.QtWidgets import QListWidget, QFileDialog
                dlg = QDialog(self)
                dlg.setWindowTitle("知识库")
                apply_dark_tool_theme(dlg)
                dlg.setMinimumSize(700, 500)
                dl = QVBoxLayout(dlg)

                # 搜索区域
                search_layout = QHBoxLayout()
                search_input = QLineEdit()
                search_input.setPlaceholderText("输入查询关键词...")
                search_btn = QPushButton("搜索")
                search_layout.addWidget(search_input)
                search_layout.addWidget(search_btn)
                dl.addLayout(search_layout)

                # 结果显示
                result_area = QTextEdit()
                result_area.setReadOnly(True)
                result_area.setStyleSheet("font-family: monospace; font-size: 11px;")
                dl.addWidget(result_area)

                # 文档列表
                dl.addWidget(QLabel("已导入文档:"))
                doc_list = QListWidget()
                dl.addWidget(doc_list)

                # 操作按钮
                btn_layout = QHBoxLayout()
                import_btn = QPushButton("导入文档")
                import_text_btn = QPushButton("导入文本")
                refresh_btn = QPushButton("刷新列表")
                btn_layout.addWidget(import_btn)
                btn_layout.addWidget(import_text_btn)
                btn_layout.addWidget(refresh_btn)
                btn_layout.addStretch()
                dl.addLayout(btn_layout)

                def refresh_docs():
                    doc_list.clear()
                    docs = kb.list_documents()
                    for d in docs:
                        title = d.get("title", d.get("id", "?"))
                        doc_list.addItem(title)

                def do_search():
                    q = search_input.text().strip()
                    if not q:
                        return
                    res = kb.query(q, top_k=10)
                    result_area.clear()
                    if not res.get("success"):
                        result_area.append(f"查询失败: {res.get('error', '未知错误')}")
                        return
                    sources = res.get("sources", [])
                    if not sources:
                        result_area.append(f"无匹配结果。")
                        return
                    result_area.append(f"答案: {res.get('answer', 'N/A')}\n{'-'*50}")
                    for s in sources:
                        result_area.append(f"【{s.get('title', '?')}】(相似度: {s.get('score', 0):.2f})\n{s.get('chunk', '')}\n{'-'*50}")

                def import_doc():
                    fp, _ = QFileDialog.getOpenFileName(dlg, "选择文档", "", "文本文件 (*.txt *.md *.json *.csv)")
                    if fp:
                        outcome = kb.import_document(fp, title="")
                        result_area.append(f"导入: {outcome}")
                        refresh_docs()

                def import_txt():
                    fp, _ = QFileDialog.getOpenFileName(dlg, "选择文件", "", "所有文件 (*)")
                    if fp:
                        try:
                            with open(fp, 'r', encoding='utf-8') as f:
                                content = f.read()
                            outcome = kb.import_text(content, title=os.path.basename(fp))
                            result_area.append(f"导入文本: {outcome}")
                            refresh_docs()
                        except Exception as ex:
                            result_area.append(f"导入失败: {ex}")

                search_btn.clicked.connect(do_search)
                import_btn.clicked.connect(import_doc)
                import_text_btn.clicked.connect(import_txt)
                refresh_btn.clicked.connect(refresh_docs)
                refresh_docs()
                dlg.show()
            except ImportError as e:
                QMessageBox.warning(self, "错误", f"知识库模块加载失败: {e}")
        elif planet_id == "system_monitor":
            dlg = SystemMonitorDialog(self)
            dlg.show()
        elif planet_id == "quick_actions":
            try:
                from core.modules.intelligence.quick_actions import QuickActionsWidget
                dlg = QDialog(self)
                dlg.setWindowTitle("快捷操作")
                dlg.setMinimumSize(700, 550)
                layout = QVBoxLayout(dlg)
                layout.addWidget(QuickActionsWidget(dlg))
                dlg.show()
            except ImportError as e:
                QMessageBox.warning(self, "错误", f"快捷操作模块加载失败: {e}")
        elif planet_id == "anomaly_detector":
            dlg = QDialog(self)
            dlg.setWindowTitle("异常检测")
            dlg.setMinimumSize(650, 500)
            layout = QVBoxLayout(dlg)
            layout.addWidget(AnomalyDetectorWidget(dlg))
            dlg.show()
        elif planet_id == "recommendation_engine":
            dlg = QDialog(self)
            dlg.setWindowTitle("推荐引擎")
            dlg.setMinimumSize(650, 500)
            layout = QVBoxLayout(dlg)
            layout.addWidget(RecommendationEngineWidget(dlg))
            dlg.show()
        elif planet_id == "data_visualization":
            dlg = QDialog(self)
            dlg.setWindowTitle("数据可视化")
            dlg.setMinimumSize(650, 500)
            layout = QVBoxLayout(dlg)
            layout.addWidget(DataVisualizationWidget(dlg))
            dlg.show()
        elif planet_id == "smart_workflow":
            dlg = SmartWorkflowDialog(self)
            dlg.show()
        elif planet_id == "business_ai":
            dlg = BusinessAIDialog(self)
            dlg.show()
        elif planet_id == "voice_interface":
            try:
                from core.modules.intelligence.voice_interface import VoiceWidget
                dlg = VoiceWidget(self)
                dlg.show()
            except ImportError as e:
                QMessageBox.warning(self, "错误", f"语音接口模块加载失败: {e}")

    def closeEvent(self, event):
        try:
            app_state.current_module = "dashboard"
        except Exception as e:
            print(f"[ai_assistant_window] closeEvent 状态切换失败: {e}")
        super().closeEvent(event)



