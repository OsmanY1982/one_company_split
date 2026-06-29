"""
一人公司 · 统一主题常量
三套色系供各窗口模块按需导入：
    CYBER_TEAL    - 青绿数据主题 (data_center, dashboard, business)
    CYBER_PURPLE  - 紫色智能主题 (intelligence, vault, scan, editor)
    CYBER_BLUE    - 蓝色设置主题 (auth, settings, model_config)
"""
from types import SimpleNamespace

# ═══════════════════════════════════════════════════════════════
# 青绿数据主题 — 用于数据面板 / 报表 / BI / 业务窗口
# ═══════════════════════════════════════════════════════════════
CYBER_TEAL = SimpleNamespace(
    DIALOG_QSS="""
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(4,12,16,245), stop:1 rgba(8,18,24,245));
        border: 2px solid rgba(0,180,150,50);
        border-radius: 14px;
    }
""",
    TABLE_STYLE="""
    QTableWidget {
        background: rgba(6,18,20,220); color: #aacccc;
        border: 1px solid rgba(0,160,140,30); border-radius: 8px;
        gridline-color: rgba(0,100,80,25); font-size: 12px;
        selection-background-color: rgba(0,180,150,60);
    }
    QTableWidget::item { padding: 5px 10px; }
    QHeaderView::section {
        background: rgba(10,22,24,230); color: #88aaaa; padding: 8px 10px;
        border: none; border-bottom: 1px solid rgba(0,180,160,40);
        font-weight: 700; font-size: 11px; letter-spacing: 1px;
    }
""",
    INPUT_STYLE="""
    QLineEdit, QComboBox, QTextEdit {
        background: rgba(6,18,20,230); color: #aacccc;
        border: 1px solid rgba(0,160,140,35); border-radius: 6px;
        padding: 6px 10px; font-size: 12px;
    }
    QLineEdit:focus { border: 1px solid rgba(0,200,160,180); }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: #0a1618; color: #aacccc;
        selection-background-color: rgba(0,180,150,80);
    }
""",
    BTN_PRIMARY="""
    QPushButton {
        background: rgba(0,160,140,40); color: #aaeecc;
        border: 1px solid rgba(0,180,150,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(0,200,160,70); }
""",
    BTN_DANGER="""
    QPushButton {
        background: rgba(200,60,40,40); color: #ffaaaa;
        border: 1px solid rgba(200,80,50,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(220,80,50,70); }
""",
)

# ═══════════════════════════════════════════════════════════════
# 紫色智能主题 — 用于 AI 对话 / 保险库 / 扫描 / 编辑器
# ═══════════════════════════════════════════════════════════════
CYBER_PURPLE = SimpleNamespace(
    DIALOG_QSS="""
    QDialog {
        background: rgba(10,5,20,240);
        border: 2px solid rgba(140,60,200,45);
        border-radius: 14px;
    }
""",
    TABLE_STYLE="""
    QTableWidget {
        background: rgba(12,6,22,220); color: #ccbbdd;
        border: 1px solid rgba(140,60,200,30); border-radius: 8px;
        gridline-color: rgba(60,20,100,25); font-size: 12px;
        selection-background-color: rgba(150,60,220,60);
    }
    QTableWidget::item { padding: 5px 10px; }
    QHeaderView::section {
        background: rgba(20,10,32,230); color: #aa99cc; padding: 8px 10px;
        border: none; border-bottom: 1px solid rgba(170,80,255,40);
        font-weight: 700; font-size: 11px; letter-spacing: 1px;
    }
""",
    INPUT_STYLE="""
    QLineEdit, QTextEdit, QComboBox {
        background: rgba(12,6,22,230); color: #ccbbdd;
        border: 1px solid rgba(170,80,255,35); border-radius: 6px;
        padding: 6px 10px; font-size: 12px;
    }
    QLineEdit:focus { border: 1px solid rgba(180,100,255,180); }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background: #150a20; color: #ccbbdd;
        selection-background-color: rgba(150,60,220,80);
    }
""",
    BTN_PRIMARY="""
    QPushButton {
        background: rgba(150,60,220,40); color: #ddaaff;
        border: 1px solid rgba(170,80,240,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(170,80,240,70); }
""",
    BTN_DANGER="""
    QPushButton {
        background: rgba(200,60,40,40); color: #ffaaaa;
        border: 1px solid rgba(200,80,50,60); border-radius: 16px;
        padding: 6px 18px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(220,80,50,70); }
""",
    BTN_SETTINGS="""
    QPushButton {
        background: rgba(100,140,200,35); color: #99bbee;
        border: 1px solid rgba(100,140,200,55); border-radius: 16px;
        padding: 6px 14px; font-size: 11px;
    }
    QPushButton:hover { background: rgba(120,160,220,60); }
""",
    BTN_ACTIVE="""
    QPushButton {
        background: rgba(180,100,240,70); color: #ffffff;
        border: 1px solid rgba(200,120,255,100); border-radius: 16px;
        padding: 6px 18px; font-size: 11px; font-weight: 600;
    }
""",
)

# ═══════════════════════════════════════════════════════════════
# 蓝色设置主题 — 用于模型配置 / 登录 / 注册 / 连接窗口
# ═══════════════════════════════════════════════════════════════
CYBER_BLUE = SimpleNamespace(
    DIALOG_QSS="""
    QDialog {
        background: rgba(8,14,28,245);
        border: 2px solid rgba(40,120,220,45);
        border-radius: 14px;
    }
""",
    TABLE_STYLE="""
    QTableWidget {
        background: rgba(8,16,28,220); color: #99bbdd;
        border: 1px solid rgba(40,100,200,30); border-radius: 8px;
        gridline-color: rgba(20,50,120,25); font-size: 12px;
        selection-background-color: rgba(40,100,200,60);
    }
    QTableWidget::item { padding: 5px 10px; }
    QHeaderView::section {
        background: rgba(12,20,36,230); color: #7788aa; padding: 8px 10px;
        border: none; border-bottom: 1px solid rgba(60,140,240,40);
        font-weight: 700; font-size: 11px; letter-spacing: 1px;
    }
""",
    INPUT_STYLE="""
    QLineEdit {
        background: rgba(8,16,32,220); color: #99ccff;
        border: 1px solid rgba(60,140,240,45); border-radius: 18px;
        padding: 10px 18px; font-size: 13px;
    }
    QLineEdit:focus {
        border: 1px solid rgba(0,200,255,160);
        background: rgba(10,20,40,240);
    }
    QLineEdit::placeholder { color: #334466; }
""",
    BTN_PRIMARY="""
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0055cc, stop:1 #0088ff);
        color: white; border: none; border-radius: 22px;
        padding: 10px 40px; font-size: 14px; font-weight: 700;
        letter-spacing: 4px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0077ee, stop:1 #00aaff);
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0044aa, stop:1 #0066cc);
    }
""",
    BTN_SECONDARY="""
    QPushButton {
        background: rgba(30,40,60,200); color: #8899aa;
        border: 1px solid rgba(70,90,120,50); border-radius: 22px;
        padding: 9px 32px; font-size: 13px;
        font-weight: 600; letter-spacing: 3px;
    }
    QPushButton:hover { background: rgba(40,55,80,220); color: #aaccee; }
""",
)
