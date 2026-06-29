"""
AI 对话窗口样式常量与路径配置
"""
import os

# ═══════ 样式常量 ═══════
INPUT_STYLE = """
    QLineEdit, QTextEdit {
        background: rgba(12,6,22,230); color: #ccbbdd;
        border: 1px solid rgba(170,80,255,35); border-radius: 6px;
        padding: 6px 10px; font-size: 12px;
    }
    QLineEdit:focus { border: 1px solid rgba(180,100,255,180); }
"""
BTN_PRIMARY = """
    QPushButton {
        background: rgba(150,60,220,40); color: #ddaaff;
        border: 1px solid rgba(170,80,240,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(170,80,240,70); }
"""
BTN_DANGER = """
    QPushButton {
        background: rgba(200,60,40,40); color: #ffaaaa;
        border: 1px solid rgba(200,80,50,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(220,80,50,70); }
"""
BTN_SETTINGS = """
    QPushButton {
        background: rgba(100,140,200,35); color: #99bbee;
        border: 1px solid rgba(100,140,200,55); border-radius: 16px;
        padding: 6px 14px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(120,160,220,60); }
"""

# ═══════ 路径常量 ═══════
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
)
