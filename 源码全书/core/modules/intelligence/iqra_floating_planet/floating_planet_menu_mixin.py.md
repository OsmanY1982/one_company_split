# `core/modules/intelligence/iqra_floating_planet/floating_planet_menu_mixin.py`

> 路径：`core/modules/intelligence/iqra_floating_planet/floating_planet_menu_mixin.py` | 行数：220


---


```python
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
        """QMenu 右键菜单 — 从 6月18日全局备份恢复"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: rgba(20, 20, 40, 240);
                color: #e0e0ff;
                border: 1px solid rgba(100, 160, 255, 80);
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 6px 28px 6px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: rgba(80, 140, 255, 60);
            }
        """)

        shape_icons = {
            k: v.get("name", k) for k, v in SHAPE_MODES.items()
        }

        # ═══════════ 悬浮球子菜单 ═══════════
        floating_menu = menu.addMenu("悬浮球")
        floating_menu.setStyleSheet(menu.styleSheet())

        planet_menu = floating_menu.addMenu("星球形态")
        planet_menu.setStyleSheet(floating_menu.styleSheet())
        for key in self._planet_keys:
            label = shape_icons.get(key, key)
            action = planet_menu.addAction(label)
            action.triggered.connect(
                lambda checked, cat="planet", k=key: self._switch_to_shape(cat, k)
            )

        alien_menu = floating_menu.addMenu("外星人形态")
        alien_menu.setStyleSheet(floating_menu.styleSheet())
        for key in self._alien_keys:
            label = shape_icons.get(key, key)
            action = alien_menu.addAction(label)
            action.triggered.connect(
                lambda checked, cat="alien", k=key: self._switch_to_shape(cat, k)
            )

        starship_menu = floating_menu.addMenu("太空星舰")
        starship_menu.setStyleSheet(floating_menu.styleSheet())
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
        modules_menu.setStyleSheet(menu.styleSheet())

        # ── 第一层：登录/注册 ──
        login_action = modules_menu.addAction("登录/注册")
        login_action.triggered.connect(
            lambda checked: self._open_module("login")
        )

        # ── 第一层：模型设置 ──
        if self._role == "admin":
            model_action = modules_menu.addAction("模型设置")
            model_action.triggered.connect(
                lambda checked: self._open_module("model_settings")
            )

        modules_menu.addSeparator()

        # ═══════════ 模块入口 ═══════════
        sub_projects = [
            # iqra：Iqra（1主分类：AI助手，12子模块）
            ("iqra", "Iqra", [
                ("ai_assistant", "AI助手", [
                    ("iqra_chat",     "AI对话"),
                    ("super_intelligence","超级智能"),
                    ("enhanced_chat",    "增强对话"),
                    ("knowledge_base",   "知识库"),
                    ("system_monitor",   "系统监控"),
                    ("quick_actions",    "快捷操作"),
                    ("anomaly_detector", "异常检测"),
                    ("recommendation_engine", "推荐引擎"),
                    ("data_visualization", "数据可视化"),
                    ("smart_workflow",   "智能工作流"),
                    ("business_ai",      "商业AI"),
                    ("voice_interface",  "语音接口"),
                ], True),
            ]),
            # management-system：管理系统（5主分类）
            ("management", "管理系统", [
                ("business", "业务管理", [
                    ("order",        "订单"),
                    ("product",      "产品"),
                    ("customer",     "客户"),
                    ("finance",      "财务"),
                    ("distribution", "分销"),
                    ("staff",        "员工"),
                    ("member",       "成员"),
                    ("wallet",       "钱包"),
                ], True),
                ("data", "数据中心", [
                    ("dashboard", "数据看板"),
                    ("report",    "报表中心"),
                    ("bi",        "商业智能"),
                    ("chart",     "可视化图表"),
                ], True),
                ("tools", "工具箱", [
                    ("editor",     "编辑器"),
                    ("vault",      "保险箱"),
                    ("calculator", "计算器"),
                    ("scanner",    "扫码工具"),
                ], True),
                ("system", "系统管理", [
                    ("system_settings", "系统设置"),
                    ("activation",      "激活码"),
                    ("cloud_sync",      "云端同步"),
                    ("cloud_server",    "云服务器"),
                    ("system_logs",     "系统日志"),
                    ("admin",           "后台管理"),
                ], True),
                ("account", "账号与安全", [
                    ("password", "修改密码"),
                    ("upgrade",  "升级会员"),
                    ("backup",   "数据备份"),
                    ("update",   "检查更新"),
                ], True),
            ]),
            # planetarium：天文馆（1主分类）
            ("planetarium", "天文馆", [
                ("astronomy", "天文馆", [
                    ("solar_system",   "太阳系天文馆"),
                    ("solar_explorer", "星谱探索"),
                ], True),
            ]),
        ]

        for sp_id, sp_name, categories in sub_projects:
            sp_menu = modules_menu.addMenu(sp_name)
            sp_menu.setStyleSheet(modules_menu.styleSheet())
            for cat_id, cat_name, sub_modules, visible in categories:
                if not visible:
                    continue
                cat_menu = sp_menu.addMenu(cat_name)
                cat_menu.setStyleSheet(sp_menu.styleSheet())
                for sub_id, sub_name in sub_modules:
                    action = cat_menu.addAction(sub_name)
                    action.triggered.connect(
                        lambda checked, mid=sub_id: self._open_module(mid)
                    )

        # ═══════════ 缩放倍数子菜单 ═══════════
        scale_menu = menu.addMenu("缩放倍数")
        scale_menu.setStyleSheet(menu.styleSheet())
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

        # ═══════════ 第一层独立项 ═══════════
        move_action = menu.addAction("自动漫游 (开)" if self._auto_move else "自动漫游 (关)")
        move_action.triggered.connect(self._toggle_auto_move)

        exit_action = menu.addAction("退出悬浮球")
        exit_action.triggered.connect(self._on_exit)

        menu.exec_(global_pos)

```
