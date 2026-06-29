# `iqra/modules/intelligence/_ai_widgets_core.py`

> 路径：`iqra/modules/intelligence/_ai_widgets_core.py` | 行数：220


---


```python
# -*- coding: utf-8 -*-
"""超级智能控制面板 Widget — SuperIntelligenceWidget

拆分自 _ai_widgets.py（原 784 行 → 本文件 ~210 行）
依赖：_ai_shared (ButtonAnimationHelper, SUPER_INTELLIGENCE_AVAILABLE)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QGridLayout,
    QGroupBox, QCheckBox, QTextEdit,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ._ai_shared import ButtonAnimationHelper, SUPER_INTELLIGENCE_AVAILABLE


class SuperIntelligenceWidget(QWidget):
    """超级智能控制面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent_window = parent
        self._intel = None
        self._build_ui()
        self._init_intelligence()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("🧠 Iqra 超级智能系统")
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #2c3e50;")
        layout.addWidget(title)

        # 状态卡片
        status_card = QGroupBox("系统状态")
        status_layout = QVBoxLayout(status_card)

        self._status_label = QLabel("⏳ 正在初始化...")
        self._status_label.setStyleSheet("font-size: 14px; padding: 10px;")
        status_layout.addWidget(self._status_label)

        # 功能开关
        switches_layout = QHBoxLayout()

        self._deep_reasoning_cb = QCheckBox("深度推理")
        self._deep_reasoning_cb.setChecked(True)
        self._deep_reasoning_cb.setToolTip("对复杂查询进行多步推理")
        switches_layout.addWidget(self._deep_reasoning_cb)

        self._self_reflection_cb = QCheckBox("自我反思")
        self._self_reflection_cb.setChecked(True)
        self._self_reflection_cb.setToolTip("分析执行结果并优化策略")
        switches_layout.addWidget(self._self_reflection_cb)

        self._active_learning_cb = QCheckBox("主动学习")
        self._active_learning_cb.setChecked(True)
        self._active_learning_cb.setToolTip("从交互中学习用户偏好")
        switches_layout.addWidget(self._active_learning_cb)

        switches_layout.addStretch()
        status_layout.addLayout(switches_layout)
        layout.addWidget(status_card)

        # 能力展示
        caps_card = QGroupBox("7项核心AI能力")
        caps_layout = QGridLayout(caps_card)
        caps_layout.setSpacing(10)

        capabilities = [
            ("🔍", "多引擎搜索", "聚合多个搜索引擎结果"),
            ("📁", "文件操作", "智能文件读写与管理"),
            ("💻", "代码执行", "安全执行Python代码"),
            ("🌐", "浏览器自动化", "网页浏览与数据提取"),
            ("⏰", "定时任务", "智能调度与提醒"),
            ("🧠", "记忆系统", "长期记忆与学习"),
            ("💬", "会话管理", "多会话上下文切换"),
        ]

        for idx, (icon, name, desc) in enumerate(capabilities):
            row, col = idx // 3, idx % 3
            cap_label = QLabel(f"{icon} <b>{name}</b><br/><span style='color: #666; font-size: 12px;'>{desc}</span>")
            cap_label.setStyleSheet("padding: 8px; background: #f8f9fa; border-radius: 6px;")
            caps_layout.addWidget(cap_label, row, col)

        layout.addWidget(caps_card)

        # 测试区域
        test_card = QGroupBox("功能测试")
        test_layout = QVBoxLayout(test_card)

        self._test_input = QLineEdit()
        self._test_input.setPlaceholderText("输入测试查询，例如：搜索最新的AI新闻")
        test_layout.addWidget(self._test_input)

        btn_layout = QHBoxLayout()
        test_btn = QPushButton("🚀 运行测试")
        test_btn.setStyleSheet("""
            QPushButton {
                background: #3498db; color: white; padding: 10px 20px;
                border-radius: 6px; font-weight: 600;
            }
            QPushButton:hover { background: #2980b9; }
            QPushButton:pressed { padding-top: 11px; padding-bottom: 9px; }
        """)
        test_btn.clicked.connect(self._run_test)
        ButtonAnimationHelper.apply_scale_animation(test_btn, 1.03)
        btn_layout.addWidget(test_btn)

        reset_btn = QPushButton("🔄 重置学习")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #95a5a6; color: white; padding: 10px 20px;
                border-radius: 6px; font-weight: 600;
            }
            QPushButton:hover { background: #7f8c8d; }
            QPushButton:pressed { padding-top: 11px; padding-bottom: 9px; }
        """)
        reset_btn.clicked.connect(self._reset_learning)
        ButtonAnimationHelper.apply_scale_animation(reset_btn, 1.03)
        btn_layout.addWidget(reset_btn)

        btn_layout.addStretch()
        test_layout.addLayout(btn_layout)

        self._test_output = QTextEdit()
        self._test_output.setReadOnly(True)
        self._test_output.setPlaceholderText("测试结果将显示在这里...")
        self._test_output.setStyleSheet("background: #f8f9fa; padding: 10px; border-radius: 6px;")
        test_layout.addWidget(self._test_output)

        layout.addWidget(test_card)
        layout.addStretch()

    def _init_intelligence(self):
        """初始化超级智能系统"""
        if not SUPER_INTELLIGENCE_AVAILABLE:
            self._status_label.setText("❌ 超级智能模块未安装\n请确保 super_intelligence.py 和 intelligence_integration.py 在当前目录")
            return

        try:
            from modules.intelligence.super_intelligence import SuperIntelligence
            self._intel = SuperIntelligence()
            self._status_label.setText(
                f"✅ 超级智能系统就绪\n"
                f"   反思次数: {len(self._intel.reflection.reflections)}\n"
                f"   学习模式: {len(self._intel.learning.patterns.get('query_patterns', {}))} 个"
            )
        except Exception as e:
            self._status_label.setText(f"⚠️ 初始化失败: {str(e)}")

    def _run_test(self):
        """运行功能测试"""
        query = self._test_input.text().strip()
        if not query:
            self._test_output.setText("请输入测试查询")
            return

        if not self._intel:
            self._test_output.setText("超级智能系统未初始化")
            return

        try:
            enable_reasoning = self._deep_reasoning_cb.isChecked()
            enable_reflection = self._self_reflection_cb.isChecked()
            enable_learning = self._active_learning_cb.isChecked()

            self._test_output.setText(f"🔄 正在分析: {query}\n{'='*50}\n")

            self._intel.toggle_feature('reasoning', enable_reasoning)
            self._intel.toggle_feature('reflection', enable_reflection)
            self._intel.toggle_feature('learning', enable_learning)

            result = self._intel.process(query)

            output = []
            reasoning = result.get('reasoning', {})
            intent_data = reasoning.get('intent', {}) if isinstance(reasoning, dict) else {}
            output.append(f"📊 意图识别: {intent_data.get('primary', 'unknown') if isinstance(intent_data, dict) else 'unknown'}")
            output.append(f"🎯 置信度: {reasoning.get('intent', {}).get('confidence', 0):.2f}" if isinstance(reasoning, dict) else "🎯 置信度: N/A")

            recs = result.get('recommendations', {})
            if isinstance(recs, dict):
                tools = ', '.join(recs.get('suggested_tools', []))
                output.append(f"🔧 推荐工具: {tools}")

            if isinstance(reasoning, dict) and 'chain' in reasoning:
                output.append(f"\n🧠 推理链:")
                for step in reasoning['chain']:
                    if isinstance(step, dict):
                        output.append(f"  → Step {step.get('name', '?')}: {step.get('type', '')}")

            if isinstance(reasoning, dict) and 'strategy' in reasoning:
                strategy = reasoning['strategy']
                if isinstance(strategy, dict):
                    output.append(f"\n📋 执行策略: {strategy.get('approach', '')}")
                    for step in strategy.get('steps', []):
                        output.append(f"  • {step}")

            insights = result.get('insights', [])
            if insights:
                output.append(f"\n💡 智能洞察:")
                for insight in insights:
                    output.append(f"  • {insight}")

            self._test_output.setText(self._test_output.toPlainText() + '\n'.join(output))

        except Exception as e:
            self._test_output.setText(f"❌ 错误: {str(e)}")

    def _reset_learning(self):
        """重置学习数据"""
        if self._intel and self._intel.learning:
            self._intel.learning.patterns.get('query_patterns', {}).clear()
            self._status_label.setText("✅ 学习数据已重置")

```
