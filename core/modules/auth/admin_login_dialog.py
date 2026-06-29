"""
管理员入口 — 独立登录对话框
深色金属风格，升级为高权限指挥舱视觉
支持记住密码（存储到 data/remembered_admin.json）
"""
# ── 版本功能地图（core · 同步自 iqra 主源） ──────────────────────────
# 窗口尺寸:   480×480 无边框（FramelessWindowHint）
# 拖拽支持:   mousePressEvent / mouseMoveEvent / mouseReleaseEvent
# 顶部栏:     COMMAND CENTER 盾牌 + X 关闭按钮（HBoxLayout）
# 副标题:     "仅限最高权限者登录 · 需密钥验证"
# 分隔线:     三色渐变 2px 高
# 复选框:     水平行（显示密码 | spacer | 记住密码）
# 按钮文本:   "进 入 指 挥 舱" + "返回登舱口"
# paintEvent: 顶部辉光(1.5px) + 底部辉光(1px) + 圆角边框(12px)
# 主题引用:   core.dark_tool_theme (DARK_TEXT / DARK_TEXT_MUTED)
# 类型标注:   有（from __future__ + typing + 全方法注解）
# 差异说明:   core 保留类型标注（历史兼容），其余与 iqra 主源一致
# ─────────────────────────────────────────────────────────────────────

from __future__ import annotations
from typing import Any

import os, json, base64
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QFrame, QCheckBox
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QFont, QPainterPath
)

from core.dark_tool_theme import DARK_TEXT, DARK_TEXT_MUTED
from core.modules.auth.auth_service import AuthService, ADMIN_USERNAME

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
REMEMBERED_ADMIN = os.path.join(DATA_DIR, "remembered_admin.json")

def _load_admin_remembered() -> dict[str, Any]:
    try:
        if os.path.exists(REMEMBERED_ADMIN):
            with open(REMEMBERED_ADMIN, "r") as f:
                data = json.load(f)
            if data.get("password"):
                data["password"] = base64.b64decode(data["password"]).decode()
            return data
    except Exception:
        pass  # gracefully degrade on I/O failure
    return {}

def _save_admin_remembered(username: str, password: str) -> None:
    try:
        data = {"username": username, "password": base64.b64encode(password.encode()).decode()}
        with open(REMEMBERED_ADMIN, "w") as f:
            json.dump(data, f)
    except Exception:
        pass  # gracefully degrade on I/O failure

def _clear_admin_remembered() -> None:
    try:
        if os.path.exists(REMEMBERED_ADMIN):
            os.remove(REMEMBERED_ADMIN)
    except Exception:
        pass  # gracefully degrade on I/O failure


# ── 配色（深空金属风，引用统一主题） ──
DARK_METAL_BG = QColor(10, 14, 26)
BORDER_COLOR = f"rgba(100, 140, 200, 60)"
ACCENT_STEEL = f"rgba(90, 110, 150, 220)"
INPUT_BG = f"rgba(6, 10, 20, 240)"
TEXT_PRIMARY = DARK_TEXT
TEXT_MUTED = DARK_TEXT_MUTED
GLOW_COLOR = QColor(0, 180, 255)
AMBER_ACCENT = QColor(220, 170, 40)


class AdminLoginDialog(QDialog):
    """管理员登录对话框 — 指挥舱级高权限入口"""

    def __init__(self, on_success: Any = None, parent: Any = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("管理员入口 · 指挥舱")
        self.setFixedSize(480, 480)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        self._on_success = on_success
        self._auth = AuthService()
        self._drag_pos = None

        self.setStyleSheet("background: #0a0e1a;")

        self._build_ui()

        # 自动填充记忆的密码
        remembered = _load_admin_remembered()
        if remembered:
            self._user_input.setText(remembered.get("username", "admin"))
            self._pwd_input.setText(remembered.get("password", ""))
            self._remember_check.setChecked(True)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(36, 16, 36, 24)
        layout.setAlignment(Qt.AlignCenter)

        # ── 顶部栏：标题 + X 关闭 ──
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        # 标题区
        header_col = QVBoxLayout()
        header_col.setSpacing(1)
        shield = QLabel("COMMAND CENTER")
        shield.setStyleSheet("color: #8899bb; font-size: 10px; letter-spacing: 6px; background: transparent;")
        header_col.addWidget(shield)

        title = QLabel("管理员指挥舱")
        title.setStyleSheet("color: #e0f0ff; font-size: 22px; font-weight: 800; letter-spacing: 4px; background: transparent;")
        header_col.addWidget(title)

        top_bar.addLayout(header_col)
        top_bar.addStretch()

        # X 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #667788; border: none;
                font-size: 16px; font-weight: 700;
            }
            QPushButton:hover {
                color: #ff6666; background: rgba(255,60,60,20);
                border-radius: 14px;
            }
        """)
        close_btn.clicked.connect(self.reject)
        top_bar.addWidget(close_btn)

        layout.addLayout(top_bar)
        layout.addSpacing(4)

        # ── 副标题 ──
        sub = QLabel("仅限最高权限者登录 · 需密钥验证")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; letter-spacing: 2px; background: transparent;")
        layout.addWidget(sub)

        layout.addSpacing(8)

        # ── 分隔线（强化辉光） ──
        divider = QFrame()
        divider.setFixedHeight(2)
        divider.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "stop:0 transparent, stop:0.3 rgba(0, 160, 255, 40), "
            "stop:0.5 rgba(0, 200, 255, 120), "
            "stop:0.7 rgba(0, 160, 255, 40), stop:1 transparent); border: none;"
        )
        layout.addWidget(divider)

        layout.addSpacing(10)

        # ── 账号 ──
        user_label = QLabel("指挥官代号")
        user_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; padding-left: 4px; background: transparent;")
        layout.addWidget(user_label)

        self._user_input = QLineEdit()
        self._user_input.setPlaceholderText("admin")
        self._user_input.setText("admin")
        self._user_input.setAlignment(Qt.AlignCenter)
        self._user_input.setFixedHeight(46)
        self._user_input.setStyleSheet(f"""
            QLineEdit {{
                background: {INPUT_BG};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 16px;
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(0, 200, 255, 180);
                background: rgba(8, 14, 24, 250);
            }}
        """)
        layout.addWidget(self._user_input)

        layout.addSpacing(6)

        # ── 密码 ──
        pwd_label = QLabel("通行密钥")
        pwd_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; padding-left: 4px; background: transparent;")
        layout.addWidget(pwd_label)

        self._pwd_input = QLineEdit()
        self._pwd_input.setPlaceholderText("••••••••")
        self._pwd_input.setEchoMode(QLineEdit.Password)
        self._pwd_input.setAlignment(Qt.AlignCenter)
        self._pwd_input.setFixedHeight(46)
        self._pwd_input.setStyleSheet(f"""
            QLineEdit {{
                background: {INPUT_BG};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_COLOR};
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 16px;
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(0, 200, 255, 180);
                background: rgba(8, 14, 24, 250);
            }}
        """)
        self._pwd_input.returnPressed.connect(self._do_login)
        layout.addWidget(self._pwd_input)

        layout.addSpacing(6)

        # ── 选项行 ──
        opt_row = QHBoxLayout()
        self._show_pwd_check = QCheckBox("显示密码")
        self._show_pwd_check.setStyleSheet(
            "color: #6688aa; font-size: 12px; background: transparent; spacing: 6px;"
        )
        self._show_pwd_check.toggled.connect(self._toggle_pwd_echo)
        opt_row.addWidget(self._show_pwd_check)
        opt_row.addStretch()
        self._remember_check = QCheckBox("记住密码")
        self._remember_check.setStyleSheet(
            "color: #5577aa; font-size: 12px; background: transparent; spacing: 6px;"
        )
        opt_row.addWidget(self._remember_check)
        layout.addLayout(opt_row)

        layout.addSpacing(10)

        # ── 登录按钮（强化金色渐变） ──
        self._login_btn = QPushButton("进 入 指 挥 舱")
        self._login_btn.setCursor(Qt.PointingHandCursor)
        self._login_btn.setFixedHeight(48)
        self._login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(80, 110, 160, 230), stop:0.5 rgba(100, 140, 200, 250), stop:1 rgba(60, 85, 130, 230));
                color: #e8f0ff;
                border: 1px solid rgba(0, 180, 255, 100);
                border-radius: 24px;
                font-size: 16px;
                font-weight: 700;
                letter-spacing: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(100, 140, 200, 250), stop:0.5 rgba(130, 180, 240, 255), stop:1 rgba(80, 110, 160, 250));
                border: 1px solid rgba(0, 210, 255, 160);
                color: #ffffff;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(40, 60, 100, 230), stop:1 rgba(30, 45, 75, 230));
            }
        """)
        self._login_btn.clicked.connect(self._do_login)
        layout.addWidget(self._login_btn)

        layout.addSpacing(6)

        # ── 取消 ──
        cancel_btn = QPushButton("返回登舱口")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_MUTED};
                border: none;
                font-size: 12px;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                color: #aabbcc;
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn, alignment=Qt.AlignCenter)

    def _toggle_pwd_echo(self, checked: bool) -> None:
        """切换密码显示/隐藏"""
        self._pwd_input.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        )

    def _do_login(self) -> None:
        import traceback
        try:
            username = self._user_input.text().strip()
            password = self._pwd_input.text().strip()

            if not password:
                QMessageBox.warning(self, "登录失败", "请输入通行密钥")
                return

            result = self._auth.login(username, password)
            if result["ok"] and result["user"]["role"] == "admin":
                if self._remember_check.isChecked():
                    _save_admin_remembered(username, password)
                else:
                    _clear_admin_remembered()
                self.accept()
                if self._on_success:
                    self._on_success()
            else:
                QMessageBox.warning(self, "认证失败", "指挥官代号或通行密钥错误，或权限不足")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "系统错误", f"登录过程异常：{e}")

    # ── 无边框窗口拖拽 ──
    def mousePressEvent(self, event: Any) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Any) -> None:
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: Any) -> None:
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def paintEvent(self, event: Any) -> None:
        """装饰辉光 + 金属边框"""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # 顶部辉光线（强化）
        g = QLinearGradient(0, 0, w, 0)
        g.setColorAt(0, QColor(0, 0, 0, 0))
        g.setColorAt(0.3, QColor(0, 120, 200, 20))
        g.setColorAt(0.5, QColor(0, 180, 255, 60))
        g.setColorAt(0.7, QColor(0, 120, 200, 20))
        g.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(QPen(QBrush(g), 1.5))
        painter.drawLine(30, 1, w - 30, 1)

        # 底部辉光线
        g2 = QLinearGradient(0, 0, w, 0)
        g2.setColorAt(0, QColor(0, 0, 0, 0))
        g2.setColorAt(0.5, QColor(0, 100, 200, 30))
        g2.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(QPen(QBrush(g2), 1))
        painter.drawLine(30, h - 1, w - 30, h - 1)

        # 边框（金属色弱可见）
        painter.setPen(QPen(QColor(60, 100, 160, 40), 1))
        painter.drawRoundedRect(0, 0, w - 1, h - 1, 12, 12)

        painter.end()
