# `planetarium/core/dark_tool_theme.py`

> 路径：`planetarium/core/dark_tool_theme.py` | 行数：198


---


```python
# -*- coding: utf-8 -*-
"""
深空金属风 · 子功能窗口统一样式常量
供 intelligence 模块和 auth 模块的暗色子窗口引用，替代各自内联 QSS 副本

配色基准（与悬浮球菜单/管理员对话框一致）：
  背景:       rgba(10,14,26,245)   深空蓝黑
  面板:       rgba(14,18,32,235)   略亮的表面
  主文字:     #ccd0e0              冷白灰
  辅助文字:   #6a7a9a              暗蓝灰
  主强调色:   rgba(100,140,255,...) 冰蓝金属
  金色点缀:   rgba(212,168,67,...)  辉光金
  危险色:     rgba(220,60,50,...)   暗红
"""

# ── 配色常量 ──────────────────────────────────
DARK_BG         = "rgba(10,14,26,245)"      # 主背景
DARK_SURFACE     = "rgba(14,18,32,235)"     # 卡片/面板
DARK_INPUT_BG    = "rgba(12,16,28,230)"     # 输入框背景
DARK_TEXT        = "#ccd0e0"                # 主文字
DARK_TEXT_MUTED  = "#6a7a9a"               # 辅助文字
ACCENT_BLUE      = "rgba(100,140,255,200)"  # 冰蓝强调
ACCENT_BLUE_DIM  = "rgba(100,140,255,45)"   # 冰蓝暗淡（边框）
ACCENT_GOLD      = "rgba(212,168,67,230)"   # 金辉强调
DANGER_RED       = "rgba(220,60,50,200)"    # 危险红
DANGER_RED_DIM   = "rgba(220,60,50,50)"     # 危险红暗淡

# ── 通用组件样式 ──────────────────────────────

DARK_TABLE_STYLE = f"""
    QTableWidget {{
        background: {DARK_SURFACE};
        color: {DARK_TEXT};
        border: 1px solid {ACCENT_BLUE_DIM};
        border-radius: 8px;
        gridline-color: rgba(40,60,120,25);
        font-size: 12px;
        selection-background-color: rgba(100,140,255,60);
    }}
    QTableWidget::item {{ padding: 5px 10px; }}
    QHeaderView::section {{
        background: rgba(16,22,38,235);
        color: {DARK_TEXT_MUTED};
        padding: 8px 10px;
        border: none;
        border-bottom: 1px solid {ACCENT_BLUE_DIM};
        font-weight: 700;
        font-size: 11px;
        letter-spacing: 1px;
    }}
"""

DARK_INPUT_STYLE = f"""
    QLineEdit, QComboBox, QTextEdit {{
        background: {DARK_INPUT_BG};
        color: {DARK_TEXT};
        border: 1px solid {ACCENT_BLUE_DIM};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 12px;
    }}
    QLineEdit:focus, QTextEdit:focus {{
        border: 1px solid {ACCENT_BLUE};
    }}
    QComboBox::drop-down {{ border: none; }}
    QComboBox QAbstractItemView {{
        background: {DARK_SURFACE};
        color: {DARK_TEXT};
        selection-background-color: rgba(100,140,255,80);
    }}
"""

DARK_BTN_PRIMARY = f"""
    QPushButton {{
        background: rgba(100,140,255,35);
        color: {DARK_TEXT};
        border: 1px solid {ACCENT_BLUE_DIM};
        border-radius: 16px;
        padding: 6px 18px;
        font-size: 11px;
        font-weight: 600;
    }}
    QPushButton:hover {{ background: rgba(100,140,255,65); }}
    QPushButton:pressed {{ background: rgba(80,120,240,80); }}
"""

DARK_BTN_DANGER = f"""
    QPushButton {{
        background: {DANGER_RED_DIM};
        color: #ffaaaa;
        border: 1px solid rgba(220,80,50,55);
        border-radius: 16px;
        padding: 6px 18px;
        font-size: 11px;
    }}
    QPushButton:hover {{ background: rgba(220,80,50,70); }}
"""

DARK_BTN_ACTIVE = f"""
    QPushButton {{
        background: rgba(120,160,255,65);
        color: #ffffff;
        border: 1px solid {ACCENT_BLUE};
        border-radius: 16px;
        padding: 6px 18px;
        font-size: 11px;
        font-weight: 600;
    }}
"""

DARK_PREVIEW_STYLE = f"""
    QTextBrowser {{
        background: {DARK_SURFACE};
        color: {DARK_TEXT};
        border: 1px solid {ACCENT_BLUE_DIM};
        border-radius: 10px;
        padding: 12px;
        font-size: 13px;
    }}
"""

DARK_EDITOR_STYLE = f"""
    QTextEdit {{
        background: {DARK_SURFACE};
        color: {DARK_TEXT};
        border: 1px solid {ACCENT_BLUE_DIM};
        border-radius: 10px;
        padding: 12px;
        font-size: 13px;
    }}
"""

# ── 对话框全局样式 ──────────────────────────────

DARK_DIALOG_STYLE = f"""
    QDialog, QMainWindow {{
        background: {DARK_BG};
    }}
    QLabel {{
        color: {DARK_TEXT};
        background: transparent;
    }}
    QMenu {{
        background: {DARK_SURFACE};
        color: {DARK_TEXT};
        border: 1px solid {ACCENT_BLUE_DIM};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item:selected {{
        background: rgba(100,140,255,50);
    }}
    QProgressBar {{
        border: 1px solid {ACCENT_BLUE_DIM};
        border-radius: 4px;
        text-align: center;
        background: {DARK_SURFACE};
        color: {DARK_TEXT};
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(100,140,255,180), stop:1 rgba(160,180,255,200));
        border-radius: 3px;
    }}
    QScrollBar:vertical {{
        background: {DARK_BG};
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {ACCENT_BLUE_DIM};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
"""

# ── 分割线（辉光渐变） ──────────────────────────

DARK_SEPARATOR = """
    QFrame {
        max-height: 2px;
        border: none;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 transparent,
            stop:0.3 rgba(100,140,255,50),
            stop:0.5 rgba(160,180,255,100),
            stop:0.7 rgba(100,140,255,50),
            stop:1 transparent);
    }
"""


def apply_dark_tool_theme(widget):
    """给深色子窗口应用深空金属风基础样式"""
    widget.setStyleSheet(DARK_DIALOG_STYLE)

```
