# `iqra/modules/auth/model_config_panel/_panel_ui.py`

> 路径：`iqra/modules/auth/model_config_panel/_panel_ui.py` | 行数：123


---


```python
"""
模型配置面板 — UI 构建 Mixin（Tab 栏、内容栈、底部按钮）。
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QLabel, QPushButton
from PyQt5.QtCore import Qt

from ._constants import BTN_PRIMARY, BTN_SECONDARY, _load_iqra_config


class _PanelUIMixin:
    """Mixin: 构建主 UI 结构（Tab 栏、内容栈、底部按钮）。"""

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(0)
        main.setContentsMargins(0, 0, 0, 0)

        # 标题
        title = QLabel("启 动 引 擎")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "color: #aaccee; font-size: 20px; font-weight: 900; "
            "letter-spacing: 12px; background: transparent; padding: 22px 0 10px 0;"
        )
        main.addWidget(title)

        sub = QLabel("选择 AI 模型提供商以激活智能中心")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #446688; font-size: 11px; background: transparent; padding-bottom: 14px;")
        main.addWidget(sub)

        # ── 三个 Tab ──
        self._tab_bar = QWidget()
        tab_layout = QHBoxLayout(self._tab_bar)
        tab_layout.setSpacing(0)
        tab_layout.setContentsMargins(40, 0, 40, 0)

        self._tab_preset = QPushButton("预设模型")
        self._tab_custom = QPushButton("自定义端点")
        self._tab_local = QPushButton("本地推理")
        self._tabs = [self._tab_preset, self._tab_custom, self._tab_local]
        for t in self._tabs:
            t.setCheckable(True)
            t.setCursor(Qt.PointingHandCursor)
            t.setFixedHeight(36)
            t.clicked.connect(lambda checked, btn=t: self._switch_tab(btn))
        self._tab_preset.setChecked(True)
        self._update_tab_styles()

        tab_layout.addWidget(self._tab_preset)
        tab_layout.addWidget(self._tab_custom)
        tab_layout.addWidget(self._tab_local)
        main.addWidget(self._tab_bar)
        main.addSpacing(8)

        # ── 内容栈 ──
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent;")
        self._stack.addWidget(self._build_preset_panel())
        self._stack.addWidget(self._build_custom_panel())
        self._stack.addWidget(self._build_local_panel())
        main.addWidget(self._stack, 1)

        # ── 底部按钮 ──
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(40, 12, 40, 20)
        btn_row.setSpacing(16)

        if self._standalone:
            skip_btn = QPushButton("跳过配置 (离线模式)")
            skip_btn.setStyleSheet(BTN_SECONDARY)
            skip_btn.setCursor(Qt.PointingHandCursor)
            skip_btn.clicked.connect(self._skip)
            btn_row.addWidget(skip_btn)

        btn_row.addStretch()

        if self._standalone:
            self._action_btn = QPushButton("点 火")
        else:
            self._action_btn = QPushButton("保存并切换")
        self._action_btn.setStyleSheet(BTN_PRIMARY)
        self._action_btn.setCursor(Qt.PointingHandCursor)
        self._action_btn.clicked.connect(self._on_action)
        btn_row.addWidget(self._action_btn)

        main.addLayout(btn_row)

    # ─── Tab 切换逻辑 ───

    def _tab_style(self, active: bool) -> str:
        if active:
            return """
                QPushButton {
                    background: rgba(20, 60, 140, 180);
                    color: #ddeeff; border: 1px solid rgba(0, 180, 255, 140);
                    border-bottom: none; border-radius: 14px 14px 0 0;
                    font-size: 12px; font-weight: 700;
                    padding: 8px 20px;
                }
            """
        return """
            QPushButton {
                background: transparent; color: #557799;
                border: 1px solid transparent;
                border-bottom: 1px solid rgba(50, 100, 180, 30);
                border-radius: 14px 14px 0 0;
                font-size: 12px; font-weight: 500;
                padding: 8px 20px;
            }
            QPushButton:hover { color: #88aacc; background: rgba(15, 30, 60, 100); }
        """

    def _update_tab_styles(self):
        for t in self._tabs:
            t.setStyleSheet(self._tab_style(t.isChecked()))

    def _switch_tab(self, btn):
        for t in self._tabs:
            t.setChecked(t == btn)
        self._update_tab_styles()
        idx = self._tabs.index(btn)
        self._stack.setCurrentIndex(idx)

```
