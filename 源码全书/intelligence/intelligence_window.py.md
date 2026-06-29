# `intelligence/intelligence_window.py`

> 路径：`intelligence/intelligence_window.py` | 行数：300


---


```python
from core.database import get_conn, close_conn
# -*- coding: utf-8 -*-
"""
智能中心 · NEURAL NEXUS（真实星球导航模式）
宇宙主题窗口：5颗真实风格星球环绕中央能量核心，点击弹出子窗口
"""
import os, sys, math
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QFrame, QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter
import logging

from core.planet_painter import (
    PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line,
)
from core.ui_components import SectionTitle, Subtitle
from core.light_tool_theme import LIGHT_TOOL_STYLE

# ═══════ 7颗星球配置 — 均匀轨道间距，无颜色冲突 ═══════
# 窗口 1200×850，中心约 (600, 425)，轨道 180~440 间距均匀
PLANETS = [
    {"id": "business",          "name": "业务管理",     "style": "mars",    "orbit": 180, "size": 56},
    {"id": "data_center",       "name": "数据中心",     "style": "neptune", "orbit": 240, "size": 54},
    {"id": "account",           "name": "账号与安全",   "style": "venus",   "orbit": 300, "size": 50},
    {"id": "tools",             "name": "工具箱",       "style": "saturn",  "orbit": 350, "size": 56},
    {"id": "ai_assistant",      "name": "AI助手",       "style": "jupiter", "orbit": 400, "size": 58},
    {"id": "system_mgmt",       "name": "系统管理",     "style": "earth",   "orbit": 440, "size": 50},
    {"id": "astronomy",         "name": "天文馆",       "style": "uranus",  "orbit": 480, "size": 48},

]

# ═══════ 导航 HUD 层 ═══════
class NavigationHUD(QWidget):
    """真实星球导航叠加层"""

    planet_clicked = None

    def __init__(self, parent=None, planets=None):
        super().__init__(parent)
        self._planets = planets if planets is not None else PLANETS
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._center = QPointF(0, 0)
        self._hovered_planet = None
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
        n = len(self._planets)
        for i, p in enumerate(self._planets):
            offset_angle = i * (360.0 / n)
            rad = math.radians(self._angle + offset_angle)
            x = w2.x() + p["orbit"] * math.cos(rad)
            y = w2.y() + p["orbit"] * math.sin(rad)
            positions.append((p, QPointF(x, y)))
        return positions

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w2 = self._center

        # ── 轨道线 ──
        for planet in self._planets:
            paint_orbit(p, w2, planet["orbit"])

        # ── 能量连接线 ──
        for _, pos in self._planet_positions():
            paint_energy_line(p, w2, pos)

        # ── 行星 ──
        for planet_data, pos in self._planet_positions():
            style = PLANET_STYLES.get(planet_data["style"], PLANET_STYLES["neptune"])
            hovered = (self._hovered_planet == planet_data["id"])
            paint_planet(p, pos, planet_data["size"], style,
                         hovered=hovered, label=planet_data["name"], font_size=10)

        p.end()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        self._hovered_planet = None
        for planet_data, pt in self._planet_positions():
            r = planet_data["size"] + 8
            dx = pos.x() - pt.x()
            dy = pos.y() - pt.y()
            if dx * dx + dy * dy <= r * r:
                self._hovered_planet = planet_data["id"]
                self.setCursor(Qt.PointingHandCursor)
                self.update()
                return
        self.setCursor(Qt.ArrowCursor)
        if self._hovered_planet is not None:
            self._hovered_planet = None
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._hovered_planet:
            if self.planet_clicked:
                self.planet_clicked(self._hovered_planet)


# ═══════ 主窗口 ═══════
class IntelligenceWindow(QMainWindow):
    """智能中心 · NEURAL NEXUS — 真实星球导航"""

    def __init__(self, parent=None, role="admin", iqra_engine=None):
        super().__init__(parent)
        self._role = role
        self._iqra_engine = iqra_engine
        self._account_win = None
        self._business_win = None
        self._tools_win = None
        self.setWindowTitle("一人公司 — 智能中心 · NEURAL NEXUS")
        self.setMinimumSize(1200, 850)
        self.resize(1200, 850)
        self.setStyleSheet(LIGHT_TOOL_STYLE)
        # 非管理员过滤掉系统管理星球
        self._planets = [p for p in PLANETS if p["id"] != "system_mgmt" or role == "admin"]
        self._build_ui()

    def _build_ui(self):
        from core.cosmic import CosmicBackground
        bg = CosmicBackground()
        self.setCentralWidget(bg)

        self._hud = NavigationHUD(self, planets=self._planets)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._hud.planet_clicked = self._on_planet_clicked
        self._hud.raise_()

        header = QWidget(self)
        header.setAttribute(Qt.WA_TranslucentBackground)
        header.setFixedHeight(70)
        header.setGeometry(0, 10, self.width(), 70)

        hl = QVBoxLayout(header)
        hl.setSpacing(2)
        title = SectionTitle("智能中心", parent=header)
        title.setStyleSheet("font-size: 24px; font-weight: 800; letter-spacing: 8px;")
        title.setAlignment(Qt.AlignCenter)
        hl.addWidget(title)
        subtitle = Subtitle(f"NEURAL NEXUS · {len(self._planets)}颗真实星球", parent=header)
        subtitle.setStyleSheet("font-size: 11px; letter-spacing: 3px;")
        subtitle.setAlignment(Qt.AlignCenter)
        hl.addWidget(subtitle)

        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(170,80,255,50),
                stop:0.5 rgba(200,120,255,120),
                stop:0.7 rgba(170,80,255,50), stop:1 transparent);
            border: none;
        """)
        hl.addWidget(line)

    def showEvent(self, event):
        super().showEvent(event)
        from core.ad_launcher import check_and_prompt_ad
        check_and_prompt_ad(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_hud'):
            self._hud.setGeometry(0, 0, self.width(), self.height())

    def _on_planet_clicked(self, planet_id):
        try:
            if planet_id == "tools":
                from core.modules.intelligence.tools_window import ToolsWindow
                self._tools_win = ToolsWindow(self)
                self._tools_win.show()
            elif planet_id == "system_mgmt":
                from core.modules.system.system_hub_window import SystemHubWindow
                dlg = SystemHubWindow(self, role=self._role)
                dlg.show()
            elif planet_id == "account":
                from .account_window import AccountWindow
                self._account_win = AccountWindow(self, role=self._role, iqra_engine=self._iqra_engine)
                self._account_win.show()
            elif planet_id == "business":
                from core.modules.business.business_window import BusinessWindow
                self._business_win = BusinessWindow(self)
                self._business_win.show()
            elif planet_id == "data_center":
                from core.modules.data_center.data_window import DataWindow
                self._data_win = DataWindow(self)
                self._data_win.show()
            elif planet_id == "astronomy":
                from core.modules.astronomy.hub import AstronomyHubWindow
                self._astro_win = AstronomyHubWindow()
                self._astro_win.show()
            elif planet_id == "ai_assistant":
                self._iqra_engine = self._ensure_engine(self._iqra_engine)
                from .ai_assistant_window import AIAssistantWindow
                self._ai_win = AIAssistantWindow(self, iqra_engine=self._iqra_engine)
                self._ai_win.show()

        except Exception as e:
            logging.getLogger(__name__).exception(
                f"模块加载失败 planet_id={planet_id}: {e}"
            )
            QMessageBox.warning(
                self, "加载失败", "模块加载失败，请重新安装应用"
            )


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

    def _get_project_root(self):
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def _ensure_engine(self, current_engine):
        """检测 iqra 引擎：若为 None 则尝试从配置恢复；仍失败则提示进入模型设置。"""
        if current_engine is not None:
            return current_engine

        # 确保从 iqra 子项目导入模型设置（唯一入口）
        _IQRA_PROJECT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "iqra")
        if _IQRA_PROJECT not in sys.path:
            sys.path.insert(0, _IQRA_PROJECT)

        # 尝试从已有配置恢复引擎
        try:
            from core.modules.auth.model_setup_window import _load_iqra_config, init_iqra_engine_from_config
            config = _load_iqra_config()
            if config and config.get("active_provider_id"):
                engine = init_iqra_engine_from_config(config)
                if engine is not None:
                    return engine
        except Exception:
            pass

        # 引擎恢复失败 → 询问用户是否进入模型设置
        reply = QMessageBox.question(
            self, "AI 引擎未连接",
            "AI 引擎尚未配置或当前不可用（如 Ollama 未启动）。\n\n"
            "是否现在进入模型设置进行配置？\n"
            "选择「否」将以离线分析模式打开 AI 对话。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            try:
                from core.modules.auth.model_setup_window import ModelSetupWindow
                dlg = ModelSetupWindow(
                    username=self._role or "",
                    role=self._role or "admin",
                    membership_info=self._membership_info,
                )
                dlg.setup_complete.connect(lambda data: self._on_engine_setup_done(data))
                dlg.show()
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法打开模型设置：{e}")
        return None

    def _on_engine_setup_done(self, data: dict):
        """模型设置完成后更新引擎引用"""
        engine = data.get("engine")
        if engine is not None:
            self._iqra_engine = engine
            # 重新打开 AI 助手
            from .ai_assistant_window import AIAssistantWindow
            self._ai_win = AIAssistantWindow(self, iqra_engine=self._iqra_engine)
            self._ai_win.show()

```
