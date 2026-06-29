# -*- coding: utf-8 -*-
"""悬浮球右键菜单 Mixin — QMenu 原生实现（从备份恢复）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QCursor
from core.shapes import SHAPE_MODES


class FloatingPlanetMenuMixin:
    """右键菜单：QMenu 原生方案"""

    def contextMenuEvent(self, event):
        """macOS 触摸板双指点按：延迟弹出打破事件循环死锁"""
        # 清除拖拽状态，避免 mousePressEvent 残留干扰
        if hasattr(self, '_dragging'):
            self._dragging = False
        global_pos = QCursor.pos()
        QTimer.singleShot(10, lambda gp=global_pos: self._show_context_menu(gp))
        event.accept()

    def _smart_raise(self):
        """智能置顶：仅当无子窗口可见时才 raise()"""
        from PyQt5.QtWidgets import QApplication
        try:
            for widget in QApplication.topLevelWidgets():
                if widget is self:
                    continue
                if widget.isVisible() and widget.windowFlags() & Qt.Window:
                    return
        except Exception:
            pass
        self.raise_()

    def _show_context_menu(self, global_pos: QPoint):
        """QMenu 右键菜单 — 深空金属风（v2 强化版）"""
        menu = QMenu(self)

        # ── 菜单基础样式 ──
        MENU_STYLE = """
            QMenu {
                background: rgba(8, 12, 24, 248);
                color: #ddeeff;
                border: 1px solid rgba(80, 120, 180, 70);
                border-radius: 10px;
                padding: 6px 4px;
            }
            QMenu::item {
                padding: 7px 32px 7px 14px;
                border-radius: 5px;
                margin: 1px 4px;
            }
            QMenu::item:selected {
                background: rgba(60, 100, 160, 70);
                color: #e8f0ff;
            }
            QMenu::separator {
                height: 1px;
                background: rgba(60, 100, 160, 30);
                margin: 4px 8px;
            }
            QMenu::indicator {
                width: 12px;
                height: 12px;
                margin-left: 4px;
            }
        """
        menu.setStyleSheet(MENU_STYLE)

        shape_icons = {
            k: v.get("name", k) for k, v in SHAPE_MODES.items()
        }

        is_admin = (self._role == "admin")

        # ═══════════ 悬浮球 ═══════════
        floating_menu = menu.addMenu("悬浮球")
        floating_menu.setStyleSheet(MENU_STYLE)

        planet_menu = floating_menu.addMenu("星球形态")
        planet_menu.setStyleSheet(MENU_STYLE)
        for key in self._planet_keys:
            label = shape_icons.get(key, key)
            action = planet_menu.addAction(label)
            action.triggered.connect(
                lambda checked, cat="planet", k=key: self._switch_to_shape(cat, k)
            )

        alien_menu = floating_menu.addMenu("外星人形态")
        alien_menu.setStyleSheet(MENU_STYLE)
        for key in self._alien_keys:
            label = shape_icons.get(key, key)
            action = alien_menu.addAction(label)
            action.triggered.connect(
                lambda checked, cat="alien", k=key: self._switch_to_shape(cat, k)
            )

        starship_menu = floating_menu.addMenu("太空星舰")
        starship_menu.setStyleSheet(MENU_STYLE)
        for key in self._starship_keys:
            label = shape_icons.get(key, key)
            action = starship_menu.addAction(label)
            action.triggered.connect(
                lambda checked, cat="starship", k=key: self._switch_to_shape(cat, k)
            )

        # ═══════════ AI 对话 ═══════════
        chat_action = menu.addAction("AI 对话")
        chat_action.triggered.connect(self._open_chat)

        menu.addSeparator()

        # ═══════════ 打开模块 ═══════════
        modules_menu = menu.addMenu("打开模块")
        modules_menu.setStyleSheet(MENU_STYLE)

        # ── 第一层：登录/注册 ──
        login_action = modules_menu.addAction("登录/注册")
        login_action.triggered.connect(
            lambda checked: self._open_module("login")
        )

        # ── 第一层：模型设置 ──
        model_action = modules_menu.addAction("模型设置")
        model_action.triggered.connect(
            lambda checked: self._open_module("model_settings")
        )

        modules_menu.addSeparator()

        # ── 第一层：智能中心 ──
        intelligence_menu = modules_menu.addMenu("智能中心")
        intelligence_menu.setStyleSheet(MENU_STYLE)

        # ── 第二层：五大类（各自含第三层子模块） ──
        # 权限：仅系统管理锁定管理员，其余注册用户可见
        categories = [
            ("ai_assistant", "AI 助手", [
                ("iqra_chat",              "AI 对话"),
                ("super_intelligence",     "超级智能"),
                ("enhanced_chat",          "增强对话"),
                ("knowledge_base",         "知识库"),
                ("system_monitor",         "系统监控"),
                ("quick_actions",          "快捷操作"),
                ("anomaly_detector",       "异常检测"),
                ("recommendation_engine",  "推荐引擎"),
                ("data_visualization",     "数据可视化"),
                ("smart_workflow",         "智能工作流"),
                ("business_ai",            "商业 AI"),
                ("voice_interface",        "语音接口"),
            ]),
            ("tools", "工具箱", [
                ("calculator",  "计算器"),
                ("editor",      "文本编辑器"),
                ("vault",       "文件保险库"),
                ("scanner",     "系统扫描器"),
            ]),
            ("data", "数据中心", [
                ("dashboard",  "数据仪表盘"),
                ("report",     "报表中心"),
                ("bi",         "商业智能"),
                ("chart",      "数据图表"),
            ]),
            ("account", "账号与安全", [
                ("backup",     "数据备份"),
                ("update",     "软件更新"),
                ("password",   "修改密码"),
                ("upgrade",    "升级会员"),
            ]),
        ]

        for cat_id, cat_name, sub_modules in categories:
            cat_menu = intelligence_menu.addMenu(cat_name)
            cat_menu.setStyleSheet(MENU_STYLE)
            for sub_id, sub_name in sub_modules:
                action = cat_menu.addAction(sub_name)
                action.triggered.connect(
                    lambda checked, mid=sub_id: self._open_module(mid)
                )

        # ── 系统管理（仅管理员） ──
        if is_admin:
            sys_menu = intelligence_menu.addMenu("系统管理")
            sys_menu.setStyleSheet(MENU_STYLE)
            for sub_id, sub_name in [
                ("system_settings", "系统设置"),
                ("activation",      "软件激活"),
                ("cloud_sync",      "云端同步"),
                ("cloud_server",    "云服务器"),
                ("system_logs",     "系统日志"),
                ("admin",           "管理面板"),
            ]:
                action = sys_menu.addAction(sub_name)
                action.triggered.connect(
                    lambda checked, mid=sub_id: self._open_module(mid)
                )

        # ── 业务管理（注册用户可见） ──
        modules_menu.addSeparator()
        biz_menu = modules_menu.addMenu("业务管理")
        biz_menu.setStyleSheet(MENU_STYLE)
        for sub_id, sub_name in [
            ("order",        "订单管理"),
            ("product",      "产品管理"),
            ("customer",     "客户管理"),
            ("finance",      "财务管理"),
            ("distribution", "分配管理"),
            ("staff",        "员工管理"),
            ("member",       "会员管理"),
            ("wallet",       "钱包管理"),
        ]:
            action = biz_menu.addAction(sub_name)
            action.triggered.connect(
                lambda checked, mid=sub_id: self._open_module(mid)
            )

        # ═══════════ 缩放倍数 ═══════════
        scale_menu = menu.addMenu("缩放倍数")
        scale_menu.setStyleSheet(MENU_STYLE)
        scale_options = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
        for val in scale_options:
            label = f"{val:.2f}x" if val != int(val) else f"{val:.1f}x"
            if abs(self._scale_multiplier - val) < 0.01:
                label = f"✓ {label}"
            action = scale_menu.addAction(label)
            action.triggered.connect(
                lambda checked, v=val: self._set_scale_multiplier(v)
            )

        menu.addSeparator()

        # ═══════════ 底部操作 ═══════════
        move_action = menu.addAction("自动漫游 (开)" if self._auto_move else "自动漫游 (关)")
        move_action.triggered.connect(self._toggle_auto_move)

        exit_action = menu.addAction("退出悬浮球")
        exit_action.triggered.connect(self._on_exit)

        menu.exec_(global_pos)
