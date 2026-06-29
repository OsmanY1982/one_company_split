# `core/modules/intelligence/_ai_widgets_recommendation.py`

> 路径：`core/modules/intelligence/_ai_widgets_recommendation.py` | 行数：95


---


```python
# -*- coding: utf-8 -*-
"""推荐引擎 Widget — RecommendationEngineWidget

拆分自 _ai_widgets.py（原 784 行 → 本文件 ~85 行）
为纯后端模块 recommendation_engine 提供可视化界面
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGroupBox,
    QCheckBox, QTextEdit,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from core.dark_tool_theme import DARK_TEXT, DARK_TEXT_MUTED, DARK_BTN_PRIMARY, DARK_PREVIEW_STYLE, ACCENT_BLUE_DIM


class RecommendationEngineWidget(QWidget):
    """推荐引擎可视化面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        from core.modules.intelligence.recommendation_engine import RecommendationEngine
        self._engine = RecommendationEngine()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("💡 智能推荐引擎")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setStyleSheet(f"color: {DARK_TEXT};")
        layout.addWidget(title)

        desc = QLabel("基于购买历史、关联规则、热销排行、用户画像和季节趋势的多维推荐系统")
        desc.setStyleSheet(f"color: {DARK_TEXT_MUTED}; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        strategies_group = QGroupBox("推荐策略")
        strategies_group.setStyleSheet(f"QGroupBox {{ font-weight: 600; border: 1px solid {ACCENT_BLUE_DIM}; border-radius: 8px; padding: 12px; margin-top: 10px; color: {DARK_TEXT}; }}")
        strat_layout = QVBoxLayout(strategies_group)
        strat_layout.setSpacing(8)

        strategies = {
            "purchase_history": ("📋 购买历史推荐", "基于用户历史购买行为"),
            "association_rules": ("🔗 关联规则推荐", "买了A的人还买了B"),
            "hot_sales": ("🔥 热销排行推荐", "当前最受欢迎商品"),
            "personalized": ("👤 个性化推荐", "基于用户画像精准推荐"),
            "seasonal": ("🌸 季节性推荐", "时令/节日/趋势商品"),
        }
        for key, (name, desc_text) in strategies.items():
            row = QHBoxLayout()
            cb = QCheckBox(name)
            cb.setChecked(True)
            cb.setStyleSheet(f"font-size: 13px; font-weight: 500; color: {DARK_TEXT};")
            row.addWidget(cb)
            dl = QLabel(desc_text)
            dl.setStyleSheet(f"color: {DARK_TEXT_MUTED}; font-size: 12px;")
            row.addWidget(dl)
            row.addStretch()
            strat_layout.addLayout(row)

        layout.addWidget(strategies_group)

        btn_layout = QHBoxLayout()
        run_btn = QPushButton("▶ 生成推荐")
        run_btn.setMinimumHeight(40)
        run_btn.setCursor(Qt.PointingHandCursor)
        run_btn.setStyleSheet(DARK_BTN_PRIMARY)
        run_btn.clicked.connect(self._run_recommendation)
        btn_layout.addWidget(run_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setPlaceholderText("推荐结果将显示在这里...")
        self._output.setStyleSheet(DARK_PREVIEW_STYLE)
        layout.addWidget(self._output)

    def _run_recommendation(self):
        self._output.setText("💡 正在生成推荐...\n")
        try:
            if hasattr(self._engine, 'get_recommendations'):
                recs = self._engine.get_recommendations()
                self._output.append(f"✅ 生成 {len(recs) if recs else 0} 条推荐")
                for r in (recs or []):
                    self._output.append(f"  • {r}")
            else:
                self._output.append("✅ 推荐引擎已就绪，可通过 API 调用获取推荐结果")
        except Exception as e:
            self._output.append(f"❌ 推荐出错: {e}")

```
