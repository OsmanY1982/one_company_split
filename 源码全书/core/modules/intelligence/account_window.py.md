# `core/modules/intelligence/account_window.py`

> 路径：`core/modules/intelligence/account_window.py` | 行数：363


---


```python
from core.database import get_conn, close_conn
"""
账号与安全 — 真实星球导航模式
修改密码 / 升级会员 / 数据备份 / 检查更新
以环绕星球的宇宙导航呈现，与 intelligence_window 同渲染架构
"""
import os, math, hashlib, zipfile, io, struct
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QMessageBox,
    QInputDialog, QLineEdit, QFileDialog, QDialog,
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter

from core.cosmic import CosmicBackground
from core.planet_painter import (
    PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line,
)

# ═══════ 4颗星球配置 ═══════
PLANETS = [
    {"id": "password", "name": "修改密码", "style": "mars",    "orbit": 150, "size": 44},
    {"id": "upgrade",  "name": "升级会员", "style": "jupiter", "orbit": 220, "size": 46},
    {"id": "backup",   "name": "数据备份", "style": "earth",   "orbit": 290, "size": 44},
    {"id": "update",   "name": "检查更新", "style": "uranus",  "orbit": 350, "size": 46},
]

# ═══════ 导航 HUD ═══════
class AccountNavHUD(QWidget):
    """账号安全模块的真实星球导航覆盖层"""

    planet_clicked = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._center = QPointF(0, 0)
        self._hovered_key = None
        self._angle = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    def _tick(self):
        self._angle = (self._angle + 0.25) % 360.0
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._center = QPointF(self.width() / 2, self.height() / 2)

    def _planet_positions(self):
        w2 = self._center
        positions = []
        n = len(PLANETS)
        for i, p in enumerate(PLANETS):
            offset_angle = i * (360.0 / n)
            rad = math.radians(self._angle + offset_angle)
            x = w2.x() + p["orbit"] * math.cos(rad)
            y = w2.y() + p["orbit"] * math.sin(rad)
            positions.append((p, QPointF(x, y)))
        return positions

    # ═══ 绘制 ═══
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w2 = self._center

        # ── 轨道线 ──
        for planet in PLANETS:
            paint_orbit(p, w2, planet["orbit"])

        # ── 能量连接线 ──
        for _, pos in self._planet_positions():
            paint_energy_line(p, w2, pos)

        # ── 行星 ──
        for planet_data, pos in self._planet_positions():
            style = PLANET_STYLES.get(planet_data["style"], PLANET_STYLES["neptune"])
            hovered = (self._hovered_key == planet_data["id"])
            paint_planet(p, pos, planet_data["size"], style,
                         hovered=hovered, label=planet_data["name"], font_size=10)

        p.end()

    # ═══ 交互 ═══
    def mouseMoveEvent(self, event):
        pos = event.pos()
        self._hovered_key = None
        for planet_data, pt in self._planet_positions():
            r = planet_data["size"] + 8
            dx = pos.x() - pt.x()
            dy = pos.y() - pt.y()
            if dx * dx + dy * dy <= r * r:
                self._hovered_key = planet_data["id"]
                self.setCursor(Qt.PointingHandCursor)
                self.update()
                return
        self.setCursor(Qt.ArrowCursor)
        if self._hovered_key is not None:
            self._hovered_key = None
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._hovered_key:
            if self.planet_clicked:
                self.planet_clicked(self._hovered_key)

# ═══════ 主窗口 ═══════
class AccountWindow(QMainWindow):
    """账号与安全 — 小星球导航"""

    def __init__(self, parent=None, role="admin", iqra_engine=None):
        super().__init__(parent)
        self._role = role
        self._iqra_engine = iqra_engine
        self.setWindowTitle("一人公司 — 账号与安全")
        self.setMinimumSize(700, 600)
        self.resize(700, 600)
        self._build_ui()

    def _build_ui(self):
        # 深空背景直接作为 central widget（不套中间层 QWidget）
        bg = CosmicBackground()
        self.setCentralWidget(bg)

        # HUD 层 — QMainWindow 直接子控件，悬浮在背景之上
        self._hud = AccountNavHUD(self)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._hud.planet_clicked = self._on_planet_clicked
        self._hud.raise_()

        # 标题
        title = QLabel("账号与安全", self)
        title.setStyleSheet(
            "color: #ddaaff; font-size: 22px; font-weight: 800;"
            " letter-spacing: 6px; background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)
        title.setGeometry(0, 18, self.width(), 36)
        self._title = title

        subtitle = QLabel("点击环绕星球进入各功能", self)
        subtitle.setStyleSheet(
            "color: #776699; font-size: 11px; letter-spacing: 2px;"
            " background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setGeometry(0, 52, self.width(), 18)
        self._subtitle = subtitle

        version = QLabel("v1.0 · ACCOUNT NEXUS", self)
        version.setStyleSheet(
            "color: rgba(150,130,180,60); font-size: 10px; background: transparent;"
        )
        version.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        version.setGeometry(self.width() - 200, self.height() - 28, 190, 20)
        self._version = version

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        if hasattr(self, '_hud'):
            self._hud.setGeometry(0, 0, w, h)
        if hasattr(self, '_title'):
            self._title.setGeometry(0, 18, w, 36)
        if hasattr(self, '_subtitle'):
            self._subtitle.setGeometry(0, 52, w, 18)
        if hasattr(self, '_version'):
            self._version.setGeometry(w - 200, h - 28, 190, 20)

    # ═══ 星球路由 ═══
    def _on_planet_clicked(self, key):
        if key == "password":
            from core.modules.auth.change_password_dialog import ChangePasswordWindow
            dlg = ChangePasswordWindow(username=self._membership_info.get("username", "admin"), parent=self)
            dlg.exec_()
        elif key == "upgrade":
            self._open_upgrade()
        elif key == "backup":
            self._user_backup()
        elif key == "update":
            from core.modules.account.account_update import AccountUpdateDialog
            dlg = AccountUpdateDialog(self)
            dlg.exec_()

    # ═══ 升级会员 ═══
    def _open_upgrade(self):
        from core.modules.auth.upgrade_window import UpgradeWindow
        ms = self._membership_info
        dlg = UpgradeWindow(
            username=ms.get("username", ""),
            parent=self,
            role=self._role,
            membership=ms.get("membership", "trial"),
            expire_at=ms.get("expire_at"),
        )
        dlg.exec_()
        try:

            root = self._get_project_root()
            db_path = os.path.join(root, "data", "member.db")
            if os.path.exists(db_path):
                conn = get_conn('member.db')
                row = conn.execute(
                    "SELECT username, role, membership, expire_at FROM members WHERE username=?",
                    (ms.get("username", "admin"),)).fetchone()
                if row:
                    self._role = row[1] or "member"
                    self._membership_info_cache = {
                        "username": row[0], "role": row[1],
                        "membership": row[2] or "trial", "expire_at": row[3] or ""
                    }
                close_conn('member.db')
        except Exception:
            pass

    # ═══ 数据备份 ═══
    def _user_backup(self):
        root = self._get_project_root()
        username = self._membership_info.get("username", "admin")

        pwd = self._verify_backup_password()
        if not pwd:
            return

        default_dir = os.path.join(root, "backup")
        os.makedirs(default_dir, exist_ok=True)
        default_name = f"user_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.usrbak"
        path, _ = QFileDialog.getSaveFileName(
            self, "备份数据",
            os.path.join(default_dir, default_name),
            "加密备份 (*.usrbak)"
        )
        if not path:
            return

        try:
            user_data_files = [
                "data/member.db", "data/customer.db",
                "data/order.db", "data/product.db",
                "data/finance.db", "data/wallet.db",
                "data/distribution.db", "data/vault.enc",
                "data/notes/",
            ]

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in user_data_files:
                    full_path = os.path.join(root, f)
                    if os.path.isfile(full_path):
                        zf.write(full_path, f)
                    elif os.path.isdir(full_path):
                        for dr, _, files in os.walk(full_path):
                            for file in files:
                                fp = os.path.join(dr, file)
                                arcname = os.path.relpath(fp, root)
                                zf.write(fp, arcname)
            zip_data = buf.getvalue()

            MAGIC = b"USRBAK_V1\x00"
            salt = os.urandom(16)
            key = hashlib.pbkdf2_hmac("sha256", pwd.encode(), salt, 100000)
            enc = bytes([b ^ key[i % len(key)] for i, b in enumerate(zip_data)])
            data_len = struct.pack(">I", len(enc))

            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(MAGIC + salt + data_len + enc)

            QMessageBox.information(self, "备份成功", f"数据已加密备份至：\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "备份失败", f"备份出错：{e}")

    def _verify_backup_password(self):
        config = self._get_backup_config()
        stored_hash = config.get("password_hash", "")

        if not stored_hash:
            pwd, ok = QInputDialog.getText(
                self, "设置备份密码", "首次使用，请设置备份主密码（至少4位）：",
                QLineEdit.Password)
            if not ok or len(pwd) < 4:
                if ok:
                    QMessageBox.warning(self, "错误", "密码至少4位")
                return None
            confirm, ok = QInputDialog.getText(
                self, "确认", "请再次输入备份密码确认：",
                QLineEdit.Password)
            if not ok or pwd != confirm:
                if ok:
                    QMessageBox.warning(self, "错误", "两次密码不一致")
                return None
            self._save_backup_config({
                "password_hash": hashlib.sha256(pwd.encode()).hexdigest(),
                "created_at": datetime.now().isoformat()
            })
            return pwd
        else:
            for _ in range(3):
                pwd, ok = QInputDialog.getText(
                    self, "验证备份密码", "请输入备份主密码：",
                    QLineEdit.Password)
                if not ok:
                    return None
                if hashlib.sha256(pwd.encode()).hexdigest() == stored_hash:
                    return pwd
                QMessageBox.warning(self, "错误", "备份密码错误！")
            return None

    def _get_backup_config(self):
        import json
        root = self._get_project_root()
        config_dir = os.path.join(root, "config")
        username = self._membership_info.get("username", "admin")
        config_file = os.path.join(config_dir, f"backup_{username}.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_backup_config(self, config: dict):
        import json
        root = self._get_project_root()
        config_dir = os.path.join(root, "config")
        username = self._membership_info.get("username", "admin")
        config_file = os.path.join(config_dir, f"backup_{username}.json")
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    # ═══ 工具方法 ═══
    def _get_project_root(self):
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    @property
    def _membership_info(self):
        if hasattr(self, '_membership_info_cache'):
            return self._membership_info_cache
        info = {"username": self._role or "admin", "role": self._role or "admin",
                "membership": "trial", "expire_at": ""}
        try:

            root = self._get_project_root()
            db_path = os.path.join(root, "data", "member.db")
            if os.path.exists(db_path):
                conn = get_conn('member.db')
                row = conn.execute(
                    "SELECT username, role, membership, expire_at FROM members WHERE username=?",
                    (self._role or "admin",)).fetchone()
                if row:
                    info = {"username": row[0] or "admin", "role": row[1] or "member",
                            "membership": row[2] or "trial", "expire_at": row[3] or ""}
                close_conn('member.db')
        except Exception:
            pass
        return info

```
