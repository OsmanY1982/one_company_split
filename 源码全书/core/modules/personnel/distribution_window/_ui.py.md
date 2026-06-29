# `core/modules/personnel/distribution_window/_ui.py`

> 路径：`core/modules/personnel/distribution_window/_ui.py` | 行数：236


---


```python
"""
_UIMixin — 分销窗口 UI 构建 + 主题样式常量
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QLineEdit, QHeaderView, QComboBox, QFrame, QTabWidget, QMessageBox,
)

from core.ui_components import SectionTitle, PrimaryButton, SecondaryButton, DangerButton
from core.light_tool_theme import LIGHT_TOOL_STYLE

# ── 白底表格补充样式 ──
LIGHT_TABLE_STYLE = """
    QTableWidget {
        background: white;
        color: #2d3748;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        gridline-color: #e2e8f0;
        selection-background-color: #bee3f8;
    }
    QTableWidget::item {
        padding: 4px 8px;
    }
    QHeaderView::section {
        background: #edf2f7;
        color: #2d3748;
        border: 1px solid #e2e8f0;
        padding: 6px;
        font-weight: bold;
    }
"""


class _UIMixin:
    """UI 构建 Mixin — 终端 Mixin（MRO 链末端），QMainWindow 初始化由 DistributionWindow.__init__ 完成，故此处不调 super().__init__()"""

    def __init__(self, parent=None):
        self.setWindowTitle("分销管理 · CREW")
        self.setMinimumSize(1200, 750)
        self.setStyleSheet(LIGHT_TOOL_STYLE)
        self._init_ui()
        self._load_all()

    # ── UI 构建 ──
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # ── 标题栏 ──
        top_row = QHBoxLayout()
        title = SectionTitle("分销管理")
        title.setStyleSheet("font-size: 20px; font-weight: 800; letter-spacing: 8px;")
        top_row.addWidget(title)
        top_row.addStretch()

        # 统计标签
        self.stats_label = QLabel("加载中...")
        top_row.addWidget(self.stats_label)
        top_row.addSpacing(16)

        btn_back = SecondaryButton("返回")
        btn_back.clicked.connect(self._go_back)
        btn_back.setFixedWidth(80)
        top_row.addWidget(btn_back)
        main_layout.addLayout(top_row)

        # ── 分隔线 ──
        sep = QFrame()
        sep.setFixedHeight(1)
        main_layout.addWidget(sep)

        # ── Tab 切换 ──
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # ===== Tab 1: 分销链接 =====
        tab_links = QWidget()
        ll = QVBoxLayout(tab_links)
        ll.setContentsMargins(10, 10, 10, 10)
        ll.setSpacing(8)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel("搜索用户:"))
        self.link_search = QLineEdit()
        self.link_search.setPlaceholderText("输入用户ID或邀请码")
        self.link_search.textChanged.connect(self._search_links)
        r1.addWidget(self.link_search)
        r1.addStretch()
        btn_create_link = PrimaryButton("创建链接")
        btn_create_link.clicked.connect(self._show_create_link_dialog)
        r1.addWidget(btn_create_link)
        ll.addLayout(r1)

        self.link_table = QTableWidget()
        self.link_table.setColumnCount(7)
        self.link_table.setHorizontalHeaderLabels(
            ["ID", "用户ID", "推广码", "链接", "点击", "注册", "状态"])
        self.link_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.link_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.link_table.setStyleSheet(LIGHT_TABLE_STYLE)
        self.link_table.verticalHeader().setVisible(False)
        ll.addWidget(self.link_table)

        r2 = QHBoxLayout()
        btn_sim_click = PrimaryButton("模拟点击")
        btn_sim_click.clicked.connect(self._simulate_click)
        r2.addWidget(btn_sim_click)
        btn_sim_reg = PrimaryButton("模拟注册")
        btn_sim_reg.clicked.connect(self._simulate_register)
        r2.addWidget(btn_sim_reg)
        r2.addStretch()
        btn_toggle = SecondaryButton("停用/启用")
        btn_toggle.clicked.connect(self._toggle_link_status)
        r2.addWidget(btn_toggle)
        btn_del_link = DangerButton("删除链接")
        btn_del_link.clicked.connect(self._delete_selected_link)
        r2.addWidget(btn_del_link)
        btn_export_links = SecondaryButton("导出 CSV")
        btn_export_links.clicked.connect(self._export_links)
        r2.addWidget(btn_export_links)
        ll.addLayout(r2)
        self.tabs.addTab(tab_links, "分销链接")

        # ===== Tab 2: 佣金记录 =====
        tab_comm = QWidget()
        cl = QVBoxLayout(tab_comm)
        cl.setContentsMargins(10, 10, 10, 10)
        cl.setSpacing(8)

        sr = QHBoxLayout()
        sr.addWidget(QLabel("用户ID:"))
        self.comm_user_search = QLineEdit()
        self.comm_user_search.setPlaceholderText("按用户ID搜索")
        self.comm_user_search.setMaximumWidth(120)
        self.comm_user_search.returnPressed.connect(self._search_commissions)
        sr.addWidget(self.comm_user_search)
        sr.addWidget(QLabel("从:"))
        self.comm_date_from = QLineEdit()
        self.comm_date_from.setPlaceholderText("2024-01-01")
        self.comm_date_from.setMaximumWidth(100)
        sr.addWidget(self.comm_date_from)
        sr.addWidget(QLabel("到:"))
        self.comm_date_to = QLineEdit()
        self.comm_date_to.setPlaceholderText("2024-12-31")
        self.comm_date_to.setMaximumWidth(100)
        sr.addWidget(self.comm_date_to)
        sr.addWidget(QLabel("状态:"))
        self.comm_filter = QComboBox()
        self.comm_filter.addItems(["全部", "pending", "approved", "rejected", "paid"])
        self.comm_filter.setMaximumWidth(100)
        self.comm_filter.currentTextChanged.connect(self._search_commissions)
        sr.addWidget(self.comm_filter)
        btn_search_comm = SecondaryButton("搜索")
        btn_search_comm.clicked.connect(self._search_commissions)
        sr.addWidget(btn_search_comm)
        btn_clear_comm = DangerButton("清除")
        btn_clear_comm.clicked.connect(self._clear_comm_search)
        sr.addWidget(btn_clear_comm)
        sr.addStretch()
        btn_add_comm = PrimaryButton("发放佣金")
        btn_add_comm.clicked.connect(self._show_add_commission_dialog)
        sr.addWidget(btn_add_comm)
        btn_export_comm = SecondaryButton("导出 CSV")
        btn_export_comm.clicked.connect(self._export_commissions)
        sr.addWidget(btn_export_comm)
        cl.addLayout(sr)

        self.comm_table = QTableWidget()
        self.comm_table.setColumnCount(7)
        self.comm_table.setHorizontalHeaderLabels(
            ["ID", "用户ID", "来源用户", "金额", "类型", "状态", "时间"])
        self.comm_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.comm_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.comm_table.setStyleSheet(LIGHT_TABLE_STYLE)
        self.comm_table.verticalHeader().setVisible(False)
        cl.addWidget(self.comm_table)

        ar = QHBoxLayout()
        btn_approve = PrimaryButton("审批通过")
        btn_approve.clicked.connect(lambda: self._update_comm_status("approved"))
        ar.addWidget(btn_approve)
        btn_reject = DangerButton("拒绝")
        btn_reject.clicked.connect(lambda: self._update_comm_status("rejected"))
        ar.addWidget(btn_reject)
        btn_pending = SecondaryButton("改回待审")
        btn_pending.clicked.connect(lambda: self._update_comm_status("pending"))
        ar.addWidget(btn_pending)
        btn_paid = PrimaryButton("标记已付")
        btn_paid.clicked.connect(lambda: self._update_comm_status("paid"))
        ar.addWidget(btn_paid)
        ar.addStretch()
        btn_del_comm = DangerButton("删除记录")
        btn_del_comm.clicked.connect(self._delete_commission)
        ar.addWidget(btn_del_comm)
        cl.addLayout(ar)
        self.tabs.addTab(tab_comm, "佣金记录")

        # ===== Tab 3: 团队管理 =====
        tab_team = QWidget()
        tl = QVBoxLayout(tab_team)
        tl.setContentsMargins(10, 10, 10, 10)
        tl.setSpacing(8)

        tr = QHBoxLayout()
        tr.addWidget(QLabel("搜索用户:"))
        self.team_search = QLineEdit()
        self.team_search.setPlaceholderText("输入用户ID或上级ID")
        self.team_search.textChanged.connect(self._search_team)
        tr.addWidget(self.team_search)
        tr.addStretch()
        btn_add_team = PrimaryButton("添加成员")
        btn_add_team.clicked.connect(self._show_add_team_dialog)
        tr.addWidget(btn_add_team)
        btn_rem_team = DangerButton("移除成员")
        btn_rem_team.clicked.connect(self._remove_selected_member)
        tr.addWidget(btn_rem_team)
        btn_export_team = SecondaryButton("导出 CSV")
        btn_export_team.clicked.connect(self._export_team)
        tr.addWidget(btn_export_team)
        tl.addLayout(tr)

        self.team_table = QTableWidget()
        self.team_table.setColumnCount(5)
        self.team_table.setHorizontalHeaderLabels(
            ["ID", "用户ID", "上级ID", "层级", "加入时间"])
        self.team_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.team_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.team_table.setStyleSheet(LIGHT_TABLE_STYLE)
        self.team_table.verticalHeader().setVisible(False)
        tl.addWidget(self.team_table)
        self.tabs.addTab(tab_team, "团队管理")

```
