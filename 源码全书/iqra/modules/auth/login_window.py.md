# `iqra/modules/auth/login_window.py`

> 路径：`iqra/modules/auth/login_window.py` | 行数：699


---


```python
"""
蓝星登录窗口 — 地球注册/登录
底部蓝色地球缓慢旋转 + 上方全息登录/注册表单
管理员入口 → 独立管理员登录对话框
会员路由：admin → 指挥官舰桥 / member → 船员舰桥
支持记住密码（存储到 data/remembered_login.json）

=== 版本功能地图 ===
版本: iqra（智能助手主源版 — canonical source）
AI 引擎: 有（_init_engine 完整实现）
登录后流程: 登录 → ModelSetupWindow → IntelligenceWindow + FloatingPlanet
目标窗口: IntelligenceWindow（modules.intelligence.intelligence_window）
悬浮球: modules.intelligence.iqra_floating_planet.FloatingPlanet（带 iqra_engine）
IPC 锁文件: /tmp/iqra_floating_planet.pid / /tmp/iqra_floating_cmd
分支维护说明: 本文件为所有子项目 login_window.py 的主源。其他子项目差异：
  - core 版与本文件完全一致（逐字同步）
  - management-system 版：无 AI 引擎，跳过 ModelSetupWindow，直接进入 IntelligenceWindow
  - planetarium 版：无 AI 引擎，跳过 ModelSetupWindow，进入 AstronomyHubWindow
最后统一: 2026-06-26
"""
import math, os, json, base64
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget,
    QLineEdit, QPushButton, QLabel, QMessageBox, QCheckBox, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QPainterPath, QFont
)

from core.cosmic import CosmicBackground, ACCENT_CYAN, ACCENT_GOLD, ACCENT_PURPLE
from core.operation_log import log_action
from core.dark_theme import apply_dark_theme
from core.dark_tool_theme import DARK_TEXT_MUTED, DARK_TEXT, DARK_SEPARATOR
from modules.auth.auth_service import AuthService, MEMBERSHIP_LABELS
from modules.auth.model_setup_window import ModelSetupWindow
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
REMEMBERED_LOGIN = os.path.join(DATA_DIR, "remembered_login.json")

def _load_remembered():
    """加载记住的登录凭据"""
    try:
        if os.path.exists(REMEMBERED_LOGIN):
            with open(REMEMBERED_LOGIN, "r") as f:
                data = json.load(f)
            if data.get("password"):
                data["password"] = base64.b64decode(data["password"]).decode()
            return data
    except Exception:
        pass  # gracefully degrade on I/O failure
    return {}

def _save_remembered(username, password):
    """保存记住的登录凭据"""
    try:
        data = {"username": username, "password": base64.b64encode(password.encode()).decode()}
        with open(REMEMBERED_LOGIN, "w") as f:
            json.dump(data, f)
    except Exception:
        pass  # gracefully degrade on I/O failure

def _clear_remembered():
    """清除记住的登录凭据"""
    try:
        if os.path.exists(REMEMBERED_LOGIN):
            os.remove(REMEMBERED_LOGIN)
    except Exception:
        pass  # gracefully degrade on I/O failure


class EarthGlobe:
    """蓝星绘制器 — 带大气光晕和大陆轮廓伪 3D"""

    EARTH_BLUE = QColor(16, 60, 140)
    OCEAN_DARK = QColor(8, 30, 80)

    def __init__(self, cx: int, cy: int, radius: int):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.angle = 0

    def draw(self, painter: QPainter):
        """绘制蓝星 + 大气光晕 + 大陆轮廓"""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy, r = self.cx, self.cy, self.radius

        # 大气光晕
        for layer in range(6, 0, -1):
            lr = r + layer * 16
            alpha = int(14 * (7 - layer))
            g = QRadialGradient(QPointF(cx, cy), lr)
            g.setColorAt(0.72, QColor(0, 0, 0, 0))
            g.setColorAt(0.8, QColor(80, 180, 255, alpha))
            g.setColorAt(0.92, QColor(40, 100, 200, alpha // 2))
            g.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(g))
            painter.drawEllipse(QPointF(cx, cy), lr, lr)

        # 球体基础
        body = QRadialGradient(QPointF(cx - r * 0.25, cy - r * 0.25), r * 1.6)
        body.setColorAt(0.3, QColor(60, 140, 230))
        body.setColorAt(0.55, QColor(25, 80, 180))
        body.setColorAt(0.8, QColor(10, 40, 120))
        body.setColorAt(1, QColor(4, 16, 60))
        painter.setPen(QPen(QColor(30, 70, 150, 80), 1))
        painter.setBrush(QBrush(body))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # 大陆轮廓
        painter.setPen(Qt.NoPen)
        for (sx, sy, sr, shade) in self._continent_spots(cx, cy, r):
            color = QColor(shade, 135 + shade // 3, 60, 110)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(sx, sy), sr, sr * 0.7)

        # 云层
        for (bx, by, bw, bh, alpha) in self._cloud_bands(cx, cy, r):
            painter.setBrush(QBrush(QColor(200, 230, 255, alpha)))
            painter.save()
            painter.translate(bx, by)
            painter.rotate(25)
            painter.drawRoundedRect(QRectF(-bw / 2, -bh / 2, bw, bh), bh / 2, bh / 2)
            painter.restore()

        # 高光反射
        highlight = QRadialGradient(QPointF(cx - r * 0.35, cy - r * 0.35), r * 0.45)
        highlight.setColorAt(0, QColor(255, 255, 255, 50))
        highlight.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(highlight))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        painter.restore()

    def _continent_spots(self, cx, cy, r):
        import random
        random.seed(42)
        spots = []
        rr = r * 0.78
        for _ in range(200):
            angle = random.random() * 2 * math.pi
            dist = random.random() * rr
            sx = cx + math.cos(angle) * dist
            sy = cy + math.sin(angle) * dist * 0.95
            sr = r * 0.03 + random.random() * r * 0.10
            shade = random.randint(20, 80)
            spots.append((sx, sy, sr, shade))
        random.seed()
        return spots

    def _cloud_bands(self, cx, cy, r):
        import random
        random.seed(99)
        bands = []
        for _ in range(18):
            angle = random.random() * math.pi * 2
            dist = r * random.uniform(0.3, 0.85)
            bx = cx + math.cos(angle) * dist
            by = cy + math.sin(angle) * dist * 0.9
            bw = r * random.uniform(0.3, 0.9)
            bh = r * random.uniform(0.04, 0.12)
            alpha = random.randint(8, 25)
            bands.append((bx, by, bw, bh, alpha))
        random.seed()
        return bands


class LoginWindow(QMainWindow):
    """蓝星登录 — 地球注册/登录 + 管理员入口"""

    def __init__(self, iqra_floating=None):
        super().__init__()
        self._iqra_floating = iqra_floating
        self.setWindowTitle("一人公司 — 蓝星")
        self.setMinimumSize(900, 680)
        apply_dark_theme(self)

        self._auth = AuthService()

        self._cosmic = CosmicBackground()
        self.setCentralWidget(self._cosmic)

        # 注意：_hud 必须是 LoginWindow 的直接子控件，不能是 _cosmic 的子控件
        # 否则 _cosmic 的 WA_TransparentForMouseEvents 会在 macOS 26.x 下屏蔽所有子控件的鼠标事件
        self._hud = QWidget(self)
        self._hud.setAttribute(Qt.WA_TranslucentBackground)
        self._hud.setGeometry(0, 0, 900, 680)

        self._earth = None
        self._orbit_sats = []
        for i in range(5):
            self._orbit_sats.append(i * 2 * math.pi / 5)

        self._t = 0
        self._mode = "login"

        self._build_ui()

        # 自动填充记住的密码
        remembered = _load_remembered()
        if remembered:
            self._login_user.setText(remembered.get("username", ""))
            self._login_pass.setText(remembered.get("password", ""))
            self._remember_check.setChecked(True)

        self._hud.raise_()  # 确保 HUD 在 _cosmic 上方

        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(35)

    def _build_ui(self):
        self._hud.paintEvent = self._paint_hud

        self._stack = QStackedWidget(self._hud)
        self._stack.setStyleSheet("background: transparent;")

        self._stack.addWidget(self._build_login_panel())
        self._stack.addWidget(self._build_register_panel())
        self._stack.setCurrentIndex(0)
        self._stack.setFixedWidth(340)

    def _input_style(self) -> str:
        return """
            QLineEdit {
                background: rgba(5, 15, 40, 200);
                color: #99ccff;
                border: 1px solid rgba(60, 140, 240, 50);
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 14px;
                min-width: 260px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(0, 200, 255, 180);
                background: rgba(8, 20, 50, 230);
            }
            QLineEdit::placeholder {
                color: #334466;
            }
        """

    def _build_login_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        v = QVBoxLayout(panel)
        v.setSpacing(14)
        v.setAlignment(Qt.AlignCenter)

        title = QLabel("一 人 公 司")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #ccddf0; font-size: 26px; font-weight: 900; "
                           "letter-spacing: 10px; background: transparent;")
        v.addWidget(title)

        sub = QLabel("TERRA · 蓝星基地")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #446688; font-size: 10px; letter-spacing: 5px; background: transparent;")
        v.addWidget(sub)
        v.addSpacing(10)

        self._login_user = QLineEdit()
        self._login_user.setPlaceholderText("呼叫代号")
        self._login_user.setStyleSheet(self._input_style())
        self._login_user.setAlignment(Qt.AlignCenter)
        v.addWidget(self._login_user)

        self._login_pass = QLineEdit()
        self._login_pass.setPlaceholderText("通行密钥")
        self._login_pass.setEchoMode(QLineEdit.Password)
        self._login_pass.setStyleSheet(self._input_style())
        self._login_pass.setAlignment(Qt.AlignCenter)
        self._login_pass.returnPressed.connect(self._do_login)
        v.addWidget(self._login_pass)

        v.addSpacing(4)
        self._remember_check = QCheckBox("记住密码")
        self._remember_check.setStyleSheet(
            f"color: {DARK_TEXT_MUTED}; font-size: 11px; background: transparent; spacing: 6px;"
        )
        v.addWidget(self._remember_check, alignment=Qt.AlignCenter)
        v.addSpacing(2)

        btn = QPushButton("发 射")
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0066cc, stop:1 #0099ff);
                color: white; border: none; border-radius: 22px;
                padding: 10px 50px; font-size: 15px; font-weight: 700;
                letter-spacing: 10px; min-width: 200px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0088ee, stop:1 #00bbff); }
            QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0055aa, stop:1 #0077cc); }
        """)
        btn.clicked.connect(self._do_login)
        v.addWidget(btn, alignment=Qt.AlignCenter)

        # ── 管理员入口 ──
        admin_btn = QPushButton(" 管理员入口")
        admin_btn.setCursor(Qt.PointingHandCursor)
        admin_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(180, 130, 40, 180), stop:0.5 rgba(200, 150, 50, 200), stop:1 rgba(180, 130, 40, 180));
                color: #fff8e0;
                border: 1px solid rgba(220, 170, 70, 100);
                border-radius: 22px;
                padding: 9px 44px;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 6px;
                min-width: 220px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(220, 160, 50, 220), stop:0.5 rgba(240, 180, 60, 240), stop:1 rgba(220, 160, 50, 220));
                color: #ffffff;
                border: 1px solid rgba(255, 200, 80, 160);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(140, 100, 30, 200), stop:1 rgba(140, 100, 30, 200));
            }
        """)
        admin_btn.clicked.connect(self._open_admin_login)
        v.addWidget(admin_btn, alignment=Qt.AlignCenter)

        switch = QLabel("没有许可？申请通行证 →")
        switch.setAlignment(Qt.AlignCenter)
        switch.setStyleSheet("color: #446688; font-size: 11px; background: transparent;")
        switch.setCursor(Qt.PointingHandCursor)
        switch.mousePressEvent = lambda e: self._switch_to_register()
        v.addWidget(switch)

        v.addStretch()
        return panel

    def _build_register_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        v = QVBoxLayout(panel)
        v.setSpacing(12)
        v.setAlignment(Qt.AlignCenter)

        # 步骤指示
        step_label = QLabel("CREW REGISTRATION")
        step_label.setAlignment(Qt.AlignCenter)
        step_label.setStyleSheet("color: #667799; font-size: 9px; letter-spacing: 6px; background: transparent;")
        v.addWidget(step_label)

        title = QLabel("新 船 员 登 记")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {DARK_TEXT}; font-size: 22px; font-weight: 800; "
                           "letter-spacing: 6px; background: transparent;")
        v.addWidget(title)

        sub = QLabel("加入一人公司 · 获得 7 天体验会员")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #5577aa; font-size: 11px; letter-spacing: 2px; background: transparent;")
        v.addWidget(sub)
        v.addSpacing(8)

        # 分隔
        divider = QFrame()
        divider.setFixedHeight(2)
        divider.setStyleSheet(DARK_SEPARATOR)
        v.addWidget(divider)
        v.addSpacing(4)

        self._reg_user = QLineEdit()
        self._reg_user.setPlaceholderText("设定呼叫代号")
        self._reg_user.setStyleSheet(self._input_style())
        self._reg_user.setAlignment(Qt.AlignCenter)
        v.addWidget(self._reg_user)

        self._reg_pass = QLineEdit()
        self._reg_pass.setPlaceholderText("设定通行密钥（6位以上）")
        self._reg_pass.setEchoMode(QLineEdit.Password)
        self._reg_pass.setStyleSheet(self._input_style())
        self._reg_pass.setAlignment(Qt.AlignCenter)
        v.addWidget(self._reg_pass)

        self._reg_pass2 = QLineEdit()
        self._reg_pass2.setPlaceholderText("确认通行密钥")
        self._reg_pass2.setEchoMode(QLineEdit.Password)
        self._reg_pass2.setStyleSheet(self._input_style())
        self._reg_pass2.setAlignment(Qt.AlignCenter)
        self._reg_pass2.returnPressed.connect(self._do_register)
        v.addWidget(self._reg_pass2)

        v.addSpacing(4)

        info = QLabel("注册即获得 7 天体验会员 · 可随时升级")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #446688; font-size: 10px; background: transparent;")
        v.addWidget(info)

        v.addSpacing(4)

        btn = QPushButton("申 请 加 入")
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4455aa, stop:1 #6677cc);
                color: white; border: none; border-radius: 22px;
                padding: 10px 50px; font-size: 15px; font-weight: 700;
                letter-spacing: 8px; min-width: 220px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5566cc, stop:1 #8899ee); }
            QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3344aa, stop:1 #4455bb); }
        """)
        btn.clicked.connect(self._do_register)
        v.addWidget(btn, alignment=Qt.AlignCenter)

        back = QLabel("← 返回登录")
        back.setAlignment(Qt.AlignCenter)
        back.setStyleSheet("color: #5577aa; font-size: 11px; background: transparent;")
        back.setCursor(Qt.PointingHandCursor)
        back.mousePressEvent = lambda e: self._switch_to_login()
        v.addWidget(back)

        v.addStretch()
        return panel

    def _switch_to_register(self):
        self._stack.setCurrentIndex(1)
        self._mode = "register"
        self._reg_user.setFocus()

    def _switch_to_login(self):
        self._stack.setCurrentIndex(0)
        self._mode = "login"
        self._login_user.setFocus()

    def _tick(self):
        self._t += 0.018
        if self._earth:
            self._earth.angle += 0.005
        self._hud.update()

    def _paint_hud(self, event):
        # 先让 Qt 完成正常的 widget 绘制（包括子控件的绘制准备）
        QWidget.paintEvent(self._hud, event)

        painter = QPainter(self._hud)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self._hud.width(), self._hud.height()

        if not self._earth:
            painter.end()
            return

        self._earth.draw(painter)

        for i, phase in enumerate(self._orbit_sats):
            a = self._t * 0.4 + phase
            orb_r = self._earth.radius + 40 + i * 16
            sx = self._earth.cx + math.cos(a) * orb_r
            sy = self._earth.cy + math.sin(a) * orb_r * 0.85
            for trail in range(4):
                ta = a - trail * 0.08
                tx = self._earth.cx + math.cos(ta) * orb_r
                ty = self._earth.cy + math.sin(ta) * orb_r * 0.85
                alpha = int(80 - trail * 18)
                painter.setBrush(QBrush(QColor(180, 210, 255, alpha)))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(tx, ty), 2 - trail * 0.3, 2 - trail * 0.3)

        painter.setPen(QPen(QColor(30, 70, 130, 25), 0.5))
        for i in range(3):
            orb_r = self._earth.radius + 45 + i * 20
            painter.drawEllipse(QPointF(self._earth.cx, self._earth.cy), orb_r, orb_r * 0.85)

        painter.setPen(QPen(QColor(80, 130, 200, 60), 1))
        painter.setFont(QFont("Menlo", 8))
        painter.drawText(QRectF(20, 10, w - 40, 18), Qt.AlignCenter, "BLUE PLANET · TERRA STATION")

        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        self._hud.setGeometry(0, 0, w, h)
        self._cosmic.setGeometry(0, 0, w, h)
        self._earth = EarthGlobe(w // 2, h - 160, min(w, h) // 3)
        self._stack.move(
            (w - 340) // 2,
            (h - 320) // 2 - 60
        )

    # ════════════════ 业务逻辑 ════════════════

    def _do_login(self):
        username = self._login_user.text().strip()
        password = self._login_pass.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "对接失败", "呼叫代号和通行密钥不能为空")
            return

        result = self._auth.login(username, password)
        if not result["ok"]:
            QMessageBox.warning(self, "对接失败", result["msg"])
            return

        # 记住/清除密码
        if self._remember_check.isChecked():
            _save_remembered(username, password)
        else:
            _clear_remembered()

        user = result["user"]
        role = user.get("role", "member")
        try:
            log_action(username, "登录", "login", "用户登录成功")
        except Exception:
            pass
        self._open_model_setup(username, role)

    def _do_register(self):
        username = self._reg_user.text().strip()
        password = self._reg_pass.text().strip()
        password2 = self._reg_pass2.text().strip()

        if password != password2:
            QMessageBox.warning(self, "注册失败", "两次通行密钥不一致")
            return

        ok, msg = self._auth.register(username, password)
        if not ok:
            QMessageBox.warning(self, "注册失败", msg)
            return

        QMessageBox.information(
            self, "注册成功",
            f"船员 {username} 已登记。\n获得 7 天体验会员。\n请返回对接。"
        )
        try:
            log_action(username, "注册", "login", "新用户注册")
        except Exception:
            pass
        self._switch_to_login()
        self._login_user.setText(username)
        self._login_pass.setFocus()

    def _open_admin_login(self):
        """打开管理员登录对话框"""
        import traceback
        print("[_open_admin_login] CLICKED — 进入管理员入口")
        try:
            from modules.auth.admin_login_dialog import AdminLoginDialog
            print("[_open_admin_login] import OK")

            def on_admin_success():
                self._open_model_setup("admin", "admin")

            dlg = AdminLoginDialog(on_success=on_admin_success, parent=self)
            print(f"[_open_admin_login] dialog created, flags={hex(int(dlg.windowFlags()))}")
            result = dlg.exec_()
            print(f"[_open_admin_login] exec_ returned {result}")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "系统错误", f"打开管理舱失败：{e}")

    def _init_engine(self, config: dict):
        """初始化 iqra 引擎（智能助手版：从配置加载，跳过模型设置窗口）"""
        provider_id = config.get("active_provider_id", "")
        provider_type = config.get("active_provider_type", "")
        if not provider_id or not provider_type:
            return None

        try:
            from core.llm_backend import BackendFactory, ProviderConfig

            if provider_type == "cloud":
                prov_cfg = config.get("cloud_providers", {}).get(provider_id, {})
            elif provider_type == "local":
                prov_cfg = config.get("local_providers", {}).get(provider_id, {})
            else:
                return None

            if not prov_cfg:
                return None

            pc = ProviderConfig(
                name=prov_cfg.get("name", provider_id),
                provider_type=prov_cfg.get("provider_type", "openai_compatible"),
                base_url=prov_cfg.get("base_url", ""),
                api_key=prov_cfg.get("api_key", ""),
                model=prov_cfg.get("model", ""),
            )
            backend = BackendFactory.create(pc)

            from modules.intelligence.agent_bridge import AgentBridge
            bridge = AgentBridge(backend)
            try:
                bridge.load_session()
            except Exception:
                pass
            return bridge
        except Exception as e:
            print(f"[Login] iqra engine init failed: {e}")
            return None

    def _open_model_setup(self, username: str, role: str):
        """登录成功后打开模型配置窗口"""
        membership_info = None
        if role == "member":
            membership_info = self._auth.get_membership_info(username)

        self._setup = ModelSetupWindow(
            username=username, role=role, membership_info=membership_info
        )
        self._setup.setup_complete.connect(self._on_setup_complete)
        self._setup.show()
        self.close()

    def _on_setup_complete(self, result: dict):
        """模型配置完成后打开智能中心"""
        from modules.intelligence.intelligence_window import IntelligenceWindow

        config = result.get("config", {})
        engine = result.get("engine", None)
        username = result.get("username", "")
        role = result.get("role", "member")
        membership_info = result.get("membership_info")

        self._center = IntelligenceWindow(
            role=role,
            iqra_engine=engine,
        )
        self._center.show()

        # 若已有悬浮球（从悬浮球菜单触发的登录），更新其引擎，不创建新的
        if self._iqra_floating is not None:
            self._iqra_floating._on_login_success(
                username=username, role=role,
                membership_info=membership_info,
                engine=engine, config=config)
            return

        # 否则创建新悬浮球
        from modules.intelligence.iqra_floating_planet import FloatingPlanet

        _lock_file = "/tmp/iqra_floating_planet.pid"
        _cmd_file = "/tmp/iqra_floating_cmd"

        try:
            self._floating = FloatingPlanet(
                iqra_engine=engine,
                role=role,
                membership_info=membership_info,
                config=config,
                project_context="iqra",
            )
            self._floating.show()
            self._floating.raise_()

            # 写入 PID 锁文件
            with open(_lock_file, "w") as f:
                f.write(str(os.getpid()))
            import atexit as _ae
            _ae.register(lambda: os.path.exists(_lock_file) and os.remove(_lock_file))

            # ── IPC 命令监听 ──
            def _check_ipc_cmd():
                if not os.path.exists(_cmd_file):
                    return
                try:
                    with open(_cmd_file, "r") as f:
                        cmd = f.read().strip()
                    os.remove(_cmd_file)
                    if cmd in ("show", "toggle"):
                        if not self._floating.isVisible():
                            self._floating.show()
                            self._floating.raise_()
                        elif cmd == "toggle":
                            self._floating.hide()
                    elif cmd == "hide":
                        self._floating.hide()
                except OSError:
                    pass

            from PyQt5.QtCore import QTimer
            self._ipc_timer = QTimer(self._floating)
            self._ipc_timer.timeout.connect(_check_ipc_cmd)
            self._ipc_timer.start(500)
        except Exception as e:
            print(f"[Login] FloatingPlanet launch failed: {e}")
            traceback.print_exc()
            QMessageBox.warning(
                self._center, "悬浮球启动失败",
                f"悬浮星球未能启动：{e}\n可通过智能中心重新打开。"
            )

    def _open_dashboard(self, username: str, role: str):
        """根据角色打开对应舰桥（旧接口，保留兼容）"""
        self._open_model_setup(username, role)

```
