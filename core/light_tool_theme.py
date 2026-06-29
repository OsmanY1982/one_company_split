# -*- coding: utf-8 -*-
"""
白底工具窗口统一样式
从 tools/compress_tool.py, batch_text.py, img_converter.py,
json_tools.py, password_tools.py, timestamp_tools.py 提取共性
"""

# ── 配色常量 ──────────────────────────────────
LIGHT_BG       = "#f0f2f5"   # 主背景
GROUP_BORDER   = "#e2e8f0"   # QGroupBox 边框
BTN_PRIMARY    = "#3182ce"   # 主按钮
BTN_PRIMARY_H  = "#2b6cb0"   # 主按钮 hover
BTN_DANGER     = "#e53e3e"   # 危险按钮
BTN_DANGER_H   = "#c53030"   # 危险按钮 hover
INPUT_BORDER   = "#e2e8f0"   # 输入组件边框
TEXT_DARK      = "#2d3748"   # 主文字颜色

# ── 基础白底工具样式 ──────────────────────────
LIGHT_TOOL_STYLE = f"""
    QMainWindow {{
        background: {LIGHT_BG};
    }}
    QWidget {{
        background-color: {LIGHT_BG};
        color: {TEXT_DARK};
    }}
    QGroupBox {{
        font-weight: bold;
        border: 2px solid {GROUP_BORDER};
        border-radius: 8px;
        margin-top: 10px;
        padding: 10px;
        background-color: white;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 8px;
    }}
    QPushButton {{
        background: {BTN_PRIMARY};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
    }}
    QPushButton:hover {{
        background: {BTN_PRIMARY_H};
    }}
    QPushButton#danger {{
        background: {BTN_DANGER};
    }}
    QPushButton#danger:hover {{
        background: {BTN_DANGER_H};
    }}
    QLabel {{
        color: {TEXT_DARK};
    }}
    QTextEdit, QPlainTextEdit, QLineEdit {{
        border: 1px solid {INPUT_BORDER};
        border-radius: 4px;
        padding: 4px;
        background: white;
    }}
    QComboBox {{
        border: 1px solid {INPUT_BORDER};
        border-radius: 4px;
        padding: 4px 8px;
        background: white;
    }}
    QListWidget {{
        border: 1px solid {INPUT_BORDER};
        border-radius: 6px;
        padding: 6px;
        background: white;
    }}
    QProgressBar {{
        border: 1px solid {INPUT_BORDER};
        border-radius: 4px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background: {BTN_PRIMARY};
        border-radius: 3px;
    }}
"""


def apply_light_tool_theme(widget):
    """给白底工具窗口应用统一样式"""
    widget.setStyleSheet(LIGHT_TOOL_STYLE)
