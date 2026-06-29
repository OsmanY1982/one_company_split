"""
DashboardWindow UI 初始化与布局 — _UIMixin
包含 __init__、resizeEvent、_build_ui
"""
from PyQt5.QtWidgets import QLabel, QPushButton, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QMouseEvent

try:
    from cosmic import CosmicBackground
except ImportError:
    try:
        from cosmic import CosmicBackground
    except ImportError:
        from core.cosmic import CosmicBackground
from ._planets import ALL_PLANETS, MEMBER_PLANET_IDS, MEMBERSHIP_LABELS


class _UIMixin:
    """UI 初始化、布局与窗口事件 — 终端 Mixin（MRO 链末端），QMainWindow 初始化已由 DashboardWindow.__init__ 完成，故此处不调 super().__init__()"""

    def __init__(self, config=None, role: str = "admin",
                 membership_info: dict = None,
                 iqra_engine=None):
        # QMainWindow 初始化已由 DashboardWindow.__init__ 完成
        self._role = role
        self._membership_info = membership_info or {}

        # 根据角色确定可见星球
        if role == "member":
            self._planets = [p for p in ALL_PLANETS if p["id"] in MEMBER_PLANET_IDS]
            mode_title = "舰桥 · 船员模式"
            if membership_info:
                ms = membership_info
                level = ms.get("membership", "trial")
                expire = ms.get("expire_at", "")
                mode_title += f" | 会员等级: {MEMBERSHIP_LABELS.get(level, level)} | 到期: {expire[:10]}"
            self.setWindowTitle(f"一人公司 — {mode_title}")
        else:
            self._planets = list(ALL_PLANETS)
            self.setWindowTitle("一人公司 — 舰桥 · 指挥官模式")

        self.setMinimumSize(1200, 760)

        # iqra 引擎（优先级最高）
        self._iqra = iqra_engine

        # 星空背景
        self._cosmic = CosmicBackground()
        self.setCentralWidget(self._cosmic)

        # HUD 层 — 必须是窗口直接子控件，不是 _cosmic 子控件
        # 否则 _cosmic 的 WA_TransparentForMouseEvents 会在 macOS 26.x 拦截所有鼠标事件
        self._hud = QWidget(self)
        self._hud.setAttribute(Qt.WA_TranslucentBackground)
        self._hud.setGeometry(0, 0, 1200, 760)

        # 动画状态
        self._t = 0
        self._hovered_planet = None
        self._modules_open = {}

        self._build_ui()

        # 确保 HUD 在星空背景之上
        self._hud.raise_()

        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(45)

        # 让 HUD 接收鼠标事件以检测星球 hover/click
        self._hud.setMouseTracking(True)
        self._hud.mouseMoveEvent = self._on_hud_mouse_move
        self._hud.mousePressEvent = self._on_hud_click

    def resizeEvent(self, event):
        from PyQt5.QtWidgets import QMainWindow
        QMainWindow.resizeEvent(self, event)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        # 重新摆放顶部控件
        self._title_label.move(24, 18)
        self._title_label.adjustSize()
        if self._upgrade_btn:
            tw = self._title_label.width()
            self._upgrade_btn.move(32 + tw, 14)
            self._upgrade_btn.adjustSize()
            self._fuel_indicator.move(48 + tw + self._upgrade_btn.width(), 20)
        else:
            self._fuel_indicator.move(32 + self._title_label.width(), 20)
        self._fuel_indicator.adjustSize()

    def _build_ui(self):
        self._hud.paintEvent = self._paint_hud

        # 顶部标题（浮在 HUD 上）
        if self._role == "member":
            ms = self._membership_info
            level_label = MEMBERSHIP_LABELS.get(ms.get("membership", "trial"), "体验会员")
            expire_str = (ms.get("expire_at", ""))[:10] if ms.get("expire_at") else "N/A"
            title_text = f"舰桥 · 船员模式 | {level_label} | 到期: {expire_str}"
        else:
            title_text = "舰桥 · 指挥官模式"

        self._title_label = QLabel(title_text, self._hud)
        self._title_label.setStyleSheet(
            "color: #8899bb; font-size: 13px; font-weight: 700; "
            "letter-spacing: 4px; background: transparent;"
        )
        self._title_label.move(24, 18)
        self._title_label.adjustSize()

        # 引擎指示
        self._fuel_indicator = QLabel("", self._hud)
        self._fuel_indicator.setStyleSheet(
            "color: #00cc88; font-size: 9px; background: transparent;"
        )
        if self._iqra:
            self._fuel_indicator.setText("引擎: iqra")
        self._fuel_indicator.adjustSize()

        # 船员升级按钮
        if self._role == "member":
            self._upgrade_btn = QPushButton("升级会员", self._hud)
            self._upgrade_btn.setCursor(Qt.PointingHandCursor)
            self._upgrade_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255,180,45,35);
                    color: #ffdd88;
                    border: 1px solid rgba(255,200,60,55);
                    border-radius: 14px;
                    padding: 4px 14px;
                    font-size: 11px; font-weight: 600;
                }
                QPushButton:hover { background: rgba(255,190,50,60); }
            """)
            self._upgrade_btn.clicked.connect(self._open_upgrade)
            self._upgrade_btn.adjustSize()
        else:
            self._upgrade_btn = None
