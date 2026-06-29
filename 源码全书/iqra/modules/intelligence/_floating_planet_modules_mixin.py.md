# `iqra/modules/intelligence/_floating_planet_modules_mixin.py`

> 路径：`iqra/modules/intelligence/_floating_planet_modules_mixin.py` | 行数：339


---


```python
# -*- coding: utf-8 -*-
"""
FloatingPlanetModulesMixin — 模块打开逻辑
_open_module / _open_ai_sub_module / _on_model_setup_done /
_on_login_success / _open_upgrade / _open_change_password
"""
import traceback
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QListWidget, QFileDialog, QMessageBox,
)


class FloatingPlanetModulesMixin:
    """模块打开逻辑 mixin"""

    # ── 第三层子模块 → 第二层大类回退映射 ──
    _SUB_TO_CATEGORY = {
        # AI 助手
        "iqra_chat": "ai_assistant",
        "super_intelligence": "ai_assistant",
        "enhanced_chat": "ai_assistant",
        "knowledge_base": "ai_assistant",
        "system_monitor": "ai_assistant",
        "quick_actions": "ai_assistant",
        "anomaly_detector": "ai_assistant",
        "recommendation_engine": "ai_assistant",
        "data_visualization": "ai_assistant",
        "smart_workflow": "ai_assistant",
        "business_ai": "ai_assistant",
        "voice_interface": "ai_assistant",

    }

    # ── AI 子模块集合（用于路由分流） ──
    _AI_SUB_MODULES = {
        "iqra_chat", "super_intelligence", "enhanced_chat", "knowledge_base",
        "system_monitor", "quick_actions", "anomaly_detector",
        "recommendation_engine", "data_visualization", "smart_workflow",
        "business_ai", "voice_interface",
    }

    # ── 模块打开 ──

    def _open_module(self, module_id: str):
        try:
            # ── AI 子模块：走专用窗口 ──
            if module_id in self._AI_SUB_MODULES:
                self._open_ai_sub_module(module_id)
                return

            # ── 非 AI 子模块 → 回退到对应大类窗口 ──
            if module_id in self._SUB_TO_CATEGORY:
                module_id = self._SUB_TO_CATEGORY[module_id]

            # ── 登录 ──
            if module_id == "login":
                from modules.auth.login_window import LoginWindow
                win = LoginWindow(iqra_floating=self)
            elif module_id == "model_settings":
                from modules.auth.model_setup_window import ModelSetupWindow
                win = ModelSetupWindow(
                    username=self._membership_info.get("username", "admin"),
                    role=self._role,
                    membership_info=self._membership_info if self._membership_info else None,
                )
                win.setup_complete.connect(self._on_model_setup_done)
            # ── AI助手大类 ──
            elif module_id == "ai_assistant":
                self._ensure_engine()
                from modules.intelligence.ai_assistant_window import AIAssistantWindow
                win = AIAssistantWindow(iqra_engine=self._engine)
            # ── 工具箱大类 ──
            elif module_id == "tools":
                from modules.intelligence.tools_window import ToolsWindow
                win = ToolsWindow()
            # ── 账号与安全大类 ──
            elif module_id == "account":
                from modules.intelligence.account_window import AccountWindow
                win = AccountWindow(role=self._role, iqra_engine=self._engine)
            else:
                return
            self._open_windows[module_id] = win
            win.destroyed.connect(lambda mid=module_id: self._open_windows.pop(mid, None))
            win.show()
        except Exception as e:
            print(f"[FloatingPlanet] Failed to open module {module_id}: {e}")
            traceback.print_exc()

    def _open_ai_sub_module(self, module_id: str):
        """直接创建并打开 AI 助手具体子功能窗口（不经过 AIAssistantWindow）"""
        try:
            from ._shell_dialogs import (
                SystemMonitorDialog, SmartWorkflowDialog, BusinessAIDialog,
            )
            from ._ai_widgets import (
                SuperIntelligenceWidget, AnomalyDetectorWidget,
                RecommendationEngineWidget, DataVisualizationWidget,
            )

            if module_id == "iqra_chat":
                self._ensure_engine()
                from modules.intelligence.ai_chat_window import AIChatWindow
                win = AIChatWindow(iqra_engine=self._engine)
                self._open_windows[module_id] = win
                win.destroyed.connect(lambda: self._open_windows.pop(module_id, None))
                win.show()
                return

            # ── 以下均为 QDialog 类型 ──
            dlg = None

            if module_id == "super_intelligence":
                from ._ai_shared import SUPER_INTELLIGENCE_AVAILABLE
                if not SUPER_INTELLIGENCE_AVAILABLE:
                    QMessageBox.information(None, "提示", "超级智能模块未安装，请检查依赖")
                    return
                dlg = QDialog()
                dlg.setWindowTitle("超级智能")
                dlg.setMinimumSize(750, 550)
                layout = QVBoxLayout(dlg)
                layout.addWidget(SuperIntelligenceWidget(dlg))

            elif module_id == "enhanced_chat":
                try:
                    from modules.intelligence.enhanced_chat import EnhancedChatWidget
                except ImportError as e:
                    QMessageBox.warning(None, "错误", f"增强对话模块加载失败: {e}")
                    return
                dlg = QDialog()
                dlg.setWindowTitle("增强对话")
                dlg.setMinimumSize(800, 600)
                layout = QVBoxLayout(dlg)
                layout.addWidget(EnhancedChatWidget(dlg))

            elif module_id == "knowledge_base":
                import os as _os4kb
                try:
                    from modules.intelligence.knowledge_base import KnowledgeBase
                    kb = KnowledgeBase()
                except ImportError as e:
                    QMessageBox.warning(None, "错误", f"知识库模块加载失败: {e}")
                    return
                dlg = QDialog()
                dlg.setWindowTitle("知识库")
                dlg.setMinimumSize(700, 500)
                dl = QVBoxLayout(dlg)

                search_layout = QHBoxLayout()
                search_input = QLineEdit()
                search_input.setPlaceholderText("输入查询关键词...")
                search_btn = QPushButton("搜索")
                search_layout.addWidget(search_input)
                search_layout.addWidget(search_btn)
                dl.addLayout(search_layout)

                result_area = QTextEdit()
                result_area.setReadOnly(True)
                result_area.setStyleSheet("font-family: monospace; font-size: 11px;")
                dl.addWidget(result_area)

                dl.addWidget(QLabel("已导入文档:"))
                doc_list = QListWidget()
                dl.addWidget(doc_list)

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
                    for d in kb.list_documents():
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
                        result_area.append("无匹配结果。")
                        return
                    result_area.append(f"答案: {res.get('answer', 'N/A')}\n{'-'*50}")
                    for s in sources:
                        result_area.append(
                            f"【{s.get('title', '?')}】(相似度: {s.get('score', 0):.2f})\n"
                            f"{s.get('chunk', '')}\n{'-'*50}"
                        )

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
                            outcome = kb.import_text(content, title=_os4kb.path.basename(fp))
                            result_area.append(f"导入文本: {outcome}")
                            refresh_docs()
                        except Exception as ex:
                            result_area.append(f"导入失败: {ex}")

                search_btn.clicked.connect(do_search)
                import_btn.clicked.connect(import_doc)
                import_text_btn.clicked.connect(import_txt)
                refresh_btn.clicked.connect(refresh_docs)
                refresh_docs()

            elif module_id == "system_monitor":
                dlg = SystemMonitorDialog()

            elif module_id == "quick_actions":
                try:
                    from modules.intelligence.quick_actions import QuickActionsWidget
                except ImportError as e:
                    QMessageBox.warning(None, "错误", f"快捷操作模块加载失败: {e}")
                    return
                dlg = QDialog()
                dlg.setWindowTitle("快捷操作")
                dlg.setMinimumSize(700, 550)
                layout = QVBoxLayout(dlg)
                layout.addWidget(QuickActionsWidget(dlg))

            elif module_id == "anomaly_detector":
                dlg = QDialog()
                dlg.setWindowTitle("异常检测")
                dlg.setMinimumSize(650, 500)
                layout = QVBoxLayout(dlg)
                layout.addWidget(AnomalyDetectorWidget(dlg))

            elif module_id == "recommendation_engine":
                dlg = QDialog()
                dlg.setWindowTitle("推荐引擎")
                dlg.setMinimumSize(650, 500)
                layout = QVBoxLayout(dlg)
                layout.addWidget(RecommendationEngineWidget(dlg))

            elif module_id == "data_visualization":
                dlg = QDialog()
                dlg.setWindowTitle("数据可视化")
                dlg.setMinimumSize(650, 500)
                layout = QVBoxLayout(dlg)
                layout.addWidget(DataVisualizationWidget(dlg))

            elif module_id == "smart_workflow":
                dlg = SmartWorkflowDialog()

            elif module_id == "business_ai":
                dlg = BusinessAIDialog()

            elif module_id == "voice_interface":
                try:
                    from modules.intelligence.voice_interface import VoiceWidget
                    dlg = VoiceWidget()
                except ImportError as e:
                    QMessageBox.warning(None, "错误", f"语音接口模块加载失败: {e}")
                    return
            else:
                return

            # 注册并显示 QDialog
            self._open_windows[module_id] = dlg
            dlg.destroyed.connect(lambda: self._open_windows.pop(module_id, None))
            dlg.show()

        except Exception as e:
            print(f"[FloatingPlanet] _open_ai_sub_module failed for {module_id}: {e}")
            traceback.print_exc()

    def _on_model_setup_done(self, result: dict):
        """模型设置完成后，更新悬浮球引擎并打开智能中心"""
        config = result.get("config", {})
        engine = result.get("engine", None)
        username = result.get("username", "")
        role = result.get("role", "member")
        membership_info = result.get("membership_info")

        self._engine = engine
        self._role = role
        self._config = config
        if membership_info:
            self._membership_info = membership_info

        try:
            from modules.intelligence.intelligence_window import IntelligenceWindow
            win = IntelligenceWindow(role=role, iqra_engine=engine)
            self._open_windows["intelligence"] = win
            win.destroyed.connect(lambda: self._open_windows.pop("intelligence", None))
            win.show()
        except Exception as e:
            print(f"[FloatingPlanet] Failed to open intelligence: {e}")

    def _on_login_success(self, username: str, role: str,
                          membership_info: dict, engine, config: dict):
        """登录成功后更新悬浮球状态（由 LoginWindow 回调）"""
        self._engine = engine
        self._role = role
        self._config = config
        if membership_info:
            self._membership_info = membership_info

    def _open_upgrade(self):
        """升级会员"""
        from modules.auth.upgrade_window import UpgradeWindow
        dlg = UpgradeWindow(
            username=self._membership_info.get("username", ""),
            parent=None,
            role=self._role,
            membership=self._membership_info.get("membership", "trial"),
            expire_at=self._membership_info.get("expire_at"),
        )
        dlg.exec_()

    def _open_change_password(self):
        """修改密码"""
        from modules.auth.change_password_dialog import ChangePasswordWindow
        dlg = ChangePasswordWindow(
            username=self._membership_info.get("username", "admin"),
            parent=None,
        )
        dlg.exec_()

```
