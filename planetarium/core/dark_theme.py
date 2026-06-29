# -*- coding: utf-8 -*-
"""
深色主题统一模块
配色基准：modules/dashboard/bi_dashboard.py
"""

# ── 配色常量 ──────────────────────────────────
BG_MAIN      = "#0a0e27"   # 主窗口背景
BG_CARD      = "#111936"   # 卡片/Frame背景
BG_INPUT     = "#1a1f3a"   # 输入框背景
BG_HOVER     = "#1e2545"   # hover背景

BTN_NORMAL   = "#1a237e"   # 按钮常态
BTN_HOVER    = "#283593"   # 按钮hover
BTN_PRESSED  = "#0d1642"   # 按钮按下
BTN_DISABLED = "#2a2a3a"   # 按钮禁用

TEXT_WHITE   = "#ffffff"   # 主文字
TEXT_LIGHT   = "#e0e0e0"   # 次要文字
TEXT_MUTED   = "#8899aa"   # 弱化文字

ACCENT       = "#00d4ff"   # 强调/标题色
SUCCESS      = "#52c41a"   # 成功绿色
WARNING      = "#faad14"   # 警告金色
DANGER       = "#f5222d"   # 危险红色
PURPLE       = "#722ed1"   # 紫色

BORDER       = "#1a237e"   # 边框色
BORDER_LIGHT = "#2a3378"   # 浅边框

SCROLL_BG    = "#0d1230"   # 滚动条背景
SCROLL_HANDLE = "#2a3378"  # 滚动条滑块

# ── 基础深色主题（窗口级 setStyleSheet） ──────
BASE_DARK_STYLE = f"""
    QMainWindow {{
        background-color: {BG_MAIN};
    }}
    QWidget {{
        background-color: {BG_MAIN};
        color: {TEXT_WHITE};
    }}
    QLabel {{
        color: {TEXT_WHITE};
        background: transparent;
    }}
    QPushButton {{
        background-color: {BTN_NORMAL};
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 5px;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {BTN_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {BTN_PRESSED};
    }}
    QPushButton:disabled {{
        background-color: {BTN_DISABLED};
        color: #666666;
    }}
    QFrame {{
        border: 1px solid {BORDER};
        border-radius: 8px;
        background-color: {BG_CARD};
    }}
    QGroupBox {{
        border: 1px solid {BORDER};
        border-radius: 8px;
        margin-top: 10px;
        padding-top: 16px;
        background-color: {BG_CARD};
        color: {TEXT_WHITE};
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 8px;
        color: {ACCENT};
    }}
    QLineEdit {{
        background-color: {BG_INPUT};
        color: {TEXT_WHITE};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 6px 10px;
        selection-background-color: {BTN_HOVER};
    }}
    QLineEdit:focus {{
        border: 1px solid {ACCENT};
    }}
    QTextEdit {{
        background-color: {BG_INPUT};
        color: {TEXT_WHITE};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 6px;
        selection-background-color: {BTN_HOVER};
    }}
    QPlainTextEdit {{
        background-color: {BG_INPUT};
        color: {TEXT_WHITE};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 6px;
        selection-background-color: {BTN_HOVER};
    }}
    QComboBox {{
        background-color: {BG_INPUT};
        color: {TEXT_WHITE};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 6px 10px;
    }}
    QComboBox:hover {{
        border: 1px solid {ACCENT};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {BG_CARD};
        color: {TEXT_WHITE};
        selection-background-color: {BTN_HOVER};
        border: 1px solid {BORDER};
    }}
    QSpinBox, QDoubleSpinBox {{
        background-color: {BG_INPUT};
        color: {TEXT_WHITE};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 4px 8px;
    }}
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 1px solid {ACCENT};
    }}
    QTableWidget {{
        background-color: {BG_CARD};
        color: {TEXT_WHITE};
        border: 1px solid {BORDER};
        border-radius: 6px;
        gridline-color: {BORDER_LIGHT};
        selection-background-color: {BTN_HOVER};
        alternate-background-color: {BG_INPUT};
    }}
    QTableWidget QHeaderView::section {{
        background-color: {BTN_NORMAL};
        color: white;
        border: 1px solid {BORDER_LIGHT};
        padding: 6px 10px;
        font-weight: bold;
    }}
    QTableWidget QHeaderView::section:hover {{
        background-color: {BTN_HOVER};
    }}
    QTableWidget::item {{
        padding: 4px 8px;
        border-bottom: 1px solid {BORDER_LIGHT};
    }}
    QTableWidget::item:selected {{
        background-color: {BTN_HOVER};
    }}
    QListWidget {{
        background-color: {BG_CARD};
        color: {TEXT_WHITE};
        border: 1px solid {BORDER};
        border-radius: 6px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 6px 12px;
        border-bottom: 1px solid {BORDER_LIGHT};
    }}
    QListWidget::item:selected {{
        background-color: {BTN_HOVER};
    }}
    QListWidget::item:hover {{
        background-color: {BG_HOVER};
    }}
    QScrollBar:vertical {{
        background-color: {SCROLL_BG};
        width: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {SCROLL_HANDLE};
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {BTN_NORMAL};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background-color: {SCROLL_BG};
        height: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {SCROLL_HANDLE};
        border-radius: 5px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {BTN_NORMAL};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    QTabWidget::pane {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 6px;
    }}
    QTabBar::tab {{
        background-color: {BG_MAIN};
        color: {TEXT_MUTED};
        border: 1px solid {BORDER};
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    QTabBar::tab:selected {{
        background-color: {BG_CARD};
        color: {ACCENT};
        border-bottom: 2px solid {ACCENT};
    }}
    QTabBar::tab:hover {{
        background-color: {BG_HOVER};
        color: {TEXT_WHITE};
    }}
    QTextBrowser {{
        background-color: {BG_CARD};
        color: {TEXT_WHITE};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 8px;
    }}
    QMenu {{
        background-color: {BG_CARD};
        color: {TEXT_WHITE};
        border: 1px solid {BORDER};
    }}
    QMenu::item {{
        padding: 6px 20px;
    }}
    QMenu::item:selected {{
        background-color: {BTN_HOVER};
    }}
    QToolTip {{
        background-color: {BG_CARD};
        color: {TEXT_WHITE};
        border: 1px solid {ACCENT};
        padding: 4px 8px;
    }}
    QCheckBox {{
        color: {TEXT_WHITE};
        spacing: 6px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {BORDER};
        border-radius: 3px;
        background-color: {BG_INPUT};
    }}
    QCheckBox::indicator:checked {{
        background-color: {BTN_NORMAL};
        border: 1px solid {ACCENT};
    }}
    QRadioButton {{
        color: {TEXT_WHITE};
        spacing: 6px;
    }}
    QRadioButton::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {BORDER};
        border-radius: 8px;
        background-color: {BG_INPUT};
    }}
    QRadioButton::indicator:checked {{
        background-color: {BTN_NORMAL};
        border: 1px solid {ACCENT};
    }}
    QProgressBar {{
        background-color: {BG_INPUT};
        border: 1px solid {BORDER};
        border-radius: 4px;
        text-align: center;
        color: {TEXT_WHITE};
    }}
    QProgressBar::chunk {{
        background-color: {ACCENT};
        border-radius: 3px;
    }}
    QDateEdit {{
        background-color: {BG_INPUT};
        color: {TEXT_WHITE};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 4px 8px;
    }}
    QDateEdit:focus {{
        border: 1px solid {ACCENT};
    }}
    QCalendarWidget {{
        background-color: {BG_CARD};
        color: {TEXT_WHITE};
    }}
    QCalendarWidget QToolButton {{
        color: {TEXT_WHITE};
        background-color: {BTN_NORMAL};
        border-radius: 4px;
    }}
    QSplitter::handle {{
        background-color: {BORDER};
        width: 2px;
    }}
"""


def apply_dark_theme(widget):
    """对 widget 应用基础深色主题"""
    widget.setStyleSheet(BASE_DARK_STYLE)


# ── 便捷暗色卡片样式 ──────────────────────────
def dark_card_style(extra=""):
    """暗色卡片样式模板"""
    return f"""
        QFrame {{
            background-color: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 8px;
            {extra}
        }}
    """


def dark_input_style(extra=""):
    """暗色输入框样式模板"""
    return f"""
        QLineEdit {{
            background-color: {BG_INPUT};
            color: {TEXT_WHITE};
            border: 1px solid {BORDER};
            border-radius: 4px;
            padding: 6px 10px;
            {extra}
        }}
    """


def dark_button_style(bg=BTN_NORMAL, hover=BTN_HOVER, pressed=BTN_PRESSED):
    """暗色按钮样式模板"""
    return f"""
        QPushButton {{
            background-color: {bg};
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: {hover};
        }}
        QPushButton:pressed {{
            background-color: {pressed};
        }}
    """
