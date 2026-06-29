# `intelligence/iqra_floating_planet/_modules_mixin.py`

> 路径：`intelligence/iqra_floating_planet/_modules_mixin.py` | 行数：489


---


```python
# -*- coding: utf-8 -*-
"""悬浮球模块打开 Mixin — _open_module / _open_ai_sub_module"""
import sys, os, traceback
from PyQt5.QtWidgets import QMessageBox


class FloatingPlanetModulesMixin:
    """模块打开路由：三层架构 → 子项目 → 主分类 → 子模块"""

    # ── 第三层子模块 → 第二层大类回退映射 ──
    _SUB_TO_CATEGORY = {
        # AI 助手子模块 → AIAssistantWindow
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
        # 业务管理子模块 → 回退到 BusinessWindow（有精确路由则不触发回退）
        "distribution": "business",
        "staff": "business",
        "member": "business",
        "wallet": "business",
        # 工具箱 → calculator 回退到 ToolsWindow；其余有独立窗口
        "calculator": "tools",
        # 系统管理子模块 → SystemHubWindow
        "system_settings": "system",
        "activation": "system",
        "cloud_sync": "system",
        "cloud_server": "system",
        "system_logs": "system",
        "admin": "system",
        # 数据中心子模块 → DataWindow
        "dashboard": "data",
        "report": "data",
        "bi": "data",
        "chart": "data",
        "data_dashboard": "data",
        "charts": "data",
        # 账号与安全 → 回退到 AccountWindow
        "backup": "account",
        "update": "account",
        "profile": "account",
        "membership": "account",
        "security": "account",
        # 系统管理子模块 → SystemHubWindow
        "system_hub": "system",
        "audit_log": "system",
        "cloud_module": "system",
        # 天文馆子模块 → AstronomyHubWindow
        "star_catalog": "astronomy",
        # 大类别名
        "data_center": "data",
        "system_mgmt": "system",
    }

    def _open_module(self, module_id: str):
        try:
            # ── 第三层子模块：优先精确路由 ──
            if module_id == "upgrade":
                self._open_upgrade()
                return
            elif module_id == "password":
                self._open_change_password()
                return
            elif module_id == "editor":
                from core.modules.intelligence.editor_window import EditorWindow
                win = EditorWindow()
            elif module_id == "vault":
                from core.modules.intelligence.vault_window import VaultWindow
                win = VaultWindow()
            elif module_id == "scanner":
                from core.modules.intelligence.scan_window import ScanWindow
                win = ScanWindow()
            elif module_id == "astronomy_hub":
                from core.modules.astronomy.hub import AstronomyHubWindow
                win = AstronomyHubWindow()
            elif module_id == "solar_system":
                from core.modules.astronomy.solar_system.window import SolarSystemWindow
                win = SolarSystemWindow()
            elif module_id == "solar_explorer":
                from core.modules.astronomy.star_catalog.catalog import StarCatalogWindow
                win = StarCatalogWindow()
            elif module_id == "order":
                from core.modules.business.order_window import OrderWindow
                win = OrderWindow()
            elif module_id == "product":
                from core.modules.business.product_window import ProductWindow
                win = ProductWindow()
            elif module_id == "customer":
                from core.modules.business.customer_window import CustomerWindow
                win = CustomerWindow()
            elif module_id == "finance":
                from core.modules.business.finance_window import FinanceWindow
                win = FinanceWindow()
            elif module_id == "distribution":
                from core.modules.personnel.distribution_window import DistributionWindow
                win = DistributionWindow()
            elif module_id == "staff":
                from core.modules.personnel.staff_window import StaffWindow
                win = StaffWindow()
            elif module_id == "member":
                from core.modules.personnel.member_window import MemberWindow
                win = MemberWindow()
            elif module_id == "wallet":
                from core.modules.personnel.wallet_window import WalletWindow
                win = WalletWindow()

            # ── 数据中心子模块 → 直接打开具体功能窗口 ──
            elif module_id == "report":
                from core.modules.data_center.report_window import ReportWindow
                win = ReportWindow()
            elif module_id == "bi":
                from core.modules.data_center.bi_window import BIWindow
                win = BIWindow()
            elif module_id == "chart":
                from core.modules.data_center.chart_window import ChartWindow
                win = ChartWindow()

            # ── 账号与安全子模块 → 独立对话框 ──
            elif module_id == "backup":
                self._open_backup()
                return
            elif module_id == "update":
                self._open_check_update()
                return

            # ── 系统管理子模块 → 直接打开具体功能窗口 ──
            elif module_id == "system_settings":
                from core.modules.system.base_info_window import BaseInfoWindow
                dlg = BaseInfoWindow()
                dlg.exec_()
                return
            elif module_id == "activation":
                from core.modules.account.account_activation import AccountActivationWindow
                dlg = AccountActivationWindow()
                dlg.exec_()
                return
            elif module_id == "cloud_sync":
                from core.modules.system.cloud_window import CloudWindow
                dlg = CloudWindow()
                dlg.exec_()
                return
            elif module_id == "system_logs":
                from core.modules.system.logs_window import LogsWindow
                dlg = LogsWindow()
                dlg.exec_()
                return
            elif module_id == "cloud_server":
                from core.modules.system.cloud_server_window import CloudServerWindow
                win = CloudServerWindow()
            elif module_id == "admin":
                from core.modules.admin.admin_window import AdminWindow
                win = AdminWindow()

            # ── 工具箱子模块 → 计算器独立对话框 ──
            elif module_id == "calculator":
                from core.modules.intelligence.tools_window import CalcDialog
                dlg = CalcDialog()
                dlg.exec_()
                return

            # ── 天文馆子模块 → 星谱探索 ──
            elif module_id == "star_catalog":
                from core.modules.astronomy.star_catalog.catalog import StarCatalogWindow
                win = StarCatalogWindow()

            # ── AI 助手子模块 → 直接打开具体功能窗口 ──
            elif module_id in ("iqra_chat", "super_intelligence", "enhanced_chat",
                               "knowledge_base", "system_monitor", "quick_actions",
                               "anomaly_detector", "recommendation_engine",
                               "data_visualization", "smart_workflow", "business_ai",
                               "voice_interface"):
                self._open_ai_sub_module(module_id)
                return

            # ── 回退：其他子模块 → 大类窗口 ──
            elif module_id in self._SUB_TO_CATEGORY:
                return self._open_module(self._SUB_TO_CATEGORY[module_id])

            # ── 第二层大类 / 第一层独立项 ──
            elif module_id == "business":
                from core.modules.business.business_window import BusinessWindow
                win = BusinessWindow()
            elif module_id == "personnel":
                from core.modules.personnel.personnel_window import PersonnelWindow
                win = PersonnelWindow()
            elif module_id == "intelligence":
                from core.modules.intelligence.intelligence_window import IntelligenceWindow
                win = IntelligenceWindow(role=self._role, iqra_engine=self._engine)
            elif module_id == "data":
                from core.modules.data_center.data_window import DataWindow
                win = DataWindow()
            elif module_id == "system":
                from core.modules.system.system_hub_window import SystemHubWindow
                win = SystemHubWindow(role=self._role)
            elif module_id == "account":
                from core.modules.intelligence.account_window import AccountWindow
                win = AccountWindow(role=self._role, iqra_engine=self._engine)
            elif module_id == "ai_assistant":
                self._ensure_engine()
                from core.modules.intelligence.ai_assistant_window import AIAssistantWindow
                win = AIAssistantWindow(iqra_engine=self._engine)
            elif module_id == "astronomy":
                from core.modules.astronomy.hub import AstronomyHubWindow
                win = AstronomyHubWindow()
            elif module_id == "tools":
                from core.modules.intelligence.tools_window import ToolsWindow
                win = ToolsWindow()
            elif module_id == "login":
                from core.modules.auth.login_window import LoginWindow
                win = LoginWindow()
            elif module_id == "model_settings":
                from core.modules.auth.model_setup_window import ModelSetupWindow
                dlg = ModelSetupWindow(
                    username=self._membership_info.get("username", ""),
                    role=self._role,
                    membership_info=self._membership_info,
                )
                self._open_windows["model_settings"] = dlg
                dlg.destroyed.connect(lambda: self._open_windows.pop("model_settings", None))
                dlg.show()
                return
            else:
                return
            self._open_windows[module_id] = win
            win.destroyed.connect(lambda mid=module_id: self._open_windows.pop(mid, None))
            win.show()
        except Exception as e:
            if module_id == "chart":
                raise
            error_msg = f"[FloatingPlanet] Failed to open module '{module_id}': {e}"
            print(error_msg)
            traceback.print_exc()
            try:
                from PyQt5.QtWidgets import QApplication, QMessageBox
                if QApplication.instance():
                    QMessageBox.warning(
                        None,
                        "模块打开失败",
                        f"无法打开模块「{module_id}」\n{type(e).__name__}: {e}"
                    )
            except Exception:
                pass

    def _open_ai_sub_module(self, module_id: str):
        """直接创建并打开 AI 助手具体子功能窗口（不经过 AIAssistantWindow）"""
        try:
            from PyQt5.QtWidgets import (
                QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                QLineEdit, QTextEdit, QListWidget, QFileDialog,
            )
            from ._shell_dialogs import (
                SystemMonitorDialog, SmartWorkflowDialog, BusinessAIDialog,
            )
            from ._ai_widgets import (
                SuperIntelligenceWidget, AnomalyDetectorWidget,
                RecommendationEngineWidget, DataVisualizationWidget,
            )

            if module_id == "iqra_chat":
                self._ensure_engine()
                from core.modules.intelligence.ai_chat_window import AIChatWindow
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
                    from core.modules.intelligence.enhanced_chat import EnhancedChatWidget
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
                    from core.modules.intelligence.knowledge_base import KnowledgeBase
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
                    from core.modules.intelligence.quick_actions import QuickActionsWidget
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
                    from core.modules.intelligence.voice_interface import VoiceWidget
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

    def _open_upgrade(self):
        """升级会员"""
        from core.modules.auth.upgrade_window import UpgradeWindow
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
        from core.modules.auth.change_password_dialog import ChangePasswordWindow
        dlg = ChangePasswordWindow(
            username=self._membership_info.get("username", "admin"),
            parent=None,
        )
        dlg.exec_()

    def _open_backup(self):
        """数据备份"""
        from core.modules.intelligence.backup_window import BackupWindow
        dlg = BackupWindow(
            username=self._membership_info.get("username", "admin"),
            role=self._role,
            parent=None,
        )
        dlg.exec_()

    def _open_check_update(self):
        """检查更新"""
        from core.modules.account.account_update import AccountUpdateDialog
        dlg = AccountUpdateDialog(parent=None)
        dlg.exec_()

```
