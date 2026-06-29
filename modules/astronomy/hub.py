# -*- coding: utf-8 -*-
"""
天文馆 · 子星球导航
环绕太阳核心的2颗子星球：太阳系天文馆 + 星谱探索
"""
import math, random
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame,
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor

from core.planet_painter import (
    PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line,
)
from modules.astronomy.solar_system.data import SOLAR_CATALOG

# ═══════ 2颗子星球配置 ═══════
# 窗口 1000×750，中心约 (500, 375)，最大允许轨道 ≈ ...（自适应）
PLANETS = [
    {"id": "solar_system",   "name": "太阳系天文馆", "style": "uranus", "orbit": 180, "size": 52},
    {"id": "solar_explorer", "name": "星谱探索",     "style": "earth", "orbit": 240, "size": 52},
]

# ═══════════════════════════════════════════
# NavigationHUD
# ═══════════════════════════════════════════

class NavigationHUD(QWidget):
    """真实星球导航叠加层 — 中心太阳 + 轨道行星 + 星空粒子背景"""

    planet_clicked = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._center = QPointF(0, 0)
        self._hovered_planet = None
        self._angle = 0.0

        # ── 入场动画 ──
        self._intro_progress = 0.0
        self._intro_done = False
        self._intro_duration_steps = 24  # 50ms × 24 = 1.2s

        # ── 星空粒子 (~80颗) ──
        self._stars = self._generate_stars(80)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    def _generate_stars(self, count):
        """生成星空粒子：(rx, ry, size, base_alpha, phase)"""
        stars = []
        for _ in range(count):
            rx = random.random()
            ry = random.random()
            size = random.uniform(0.5, 2.5)
            alpha = random.randint(20, 120)
            phase = random.uniform(0, 2 * math.pi)
            stars.append((rx, ry, size, alpha, phase))
        return stars

    def _tick(self):
        self._angle = (self._angle + 0.3) % 360.0

        if not self._intro_done:
            self._intro_progress += 1.0 / self._intro_duration_steps
            if self._intro_progress >= 1.0:
                self._intro_progress = 1.0
                self._intro_done = True

        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._center = QPointF(self.width() / 2, self.height() / 2)

    def _planet_positions(self):
        w2 = self._center
        # easeOutCubic 缓动
        t = self._intro_progress
        ease = 1.0 - (1.0 - t) ** 3

        positions = []
        for i, p in enumerate(PLANETS):
            offset_angle = i * (360.0 / len(PLANETS))
            rad = math.radians(self._angle + offset_angle)
            orbit = p["orbit"] * ease
            x = w2.x() + orbit * math.cos(rad)
            y = w2.y() + orbit * math.sin(rad)
            positions.append((p, QPointF(x, y)))
        return positions

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w2 = self._center
        w, h = self.width(), self.height()

        # ── 层0：星空粒子背景 ──
        for rx, ry, size, base_alpha, phase in self._stars:
            sx = rx * w
            sy = ry * h
            alpha = base_alpha * (0.5 + 0.5 * math.sin(self._angle * 0.02 + phase))
            alpha = max(5, int(alpha))
            p.setBrush(QColor(255, 255, 255, alpha))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(sx, sy), size, size)

        # ── 层1：轨道虚线圆 ──
        for planet in PLANETS:
            paint_orbit(p, w2, planet["orbit"])

        # ── 层2：能量连接线 ──
        for planet_data, pos in self._planet_positions():
            paint_energy_line(p, w2, pos)

        # ── 层3：绕转行星 ──
        for planet_data, pos in self._planet_positions():
            style = PLANET_STYLES.get(planet_data.get("style"), PLANET_STYLES["neptune"])
            is_hovered = (self._hovered_planet == planet_data["id"])
            paint_planet(p, pos, planet_data["size"], style,
                         hovered=is_hovered, label=planet_data["name"], font_size=10,
                         anim_t=self._angle)

        p.end()

    # ── 鼠标交互 ──

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


# ═══════════════════════════════════════════
# AstronomyHubWindow
# ═══════════════════════════════════════════

class AstronomyHubWindow(QWidget):
    """天文馆 · 子星球导航主窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("一人公司 — 天文馆 · ASTRONOMY HUB")
        self.resize(1000, 750)
        self.setMinimumSize(600, 450)
        self.setWindowFlags(Qt.Window)
        self._build_ui()

    def _count_celestial(self):
        """从 SOLAR_CATALOG 动态统计天体数量
        Sun 在 catalog 中 type 为 "planet"（被 PLANETS 列表覆盖），
        通过 id=="sun" 和 orbit_km==0 识别为恒星。
        """
        stars = sum(1 for b in SOLAR_CATALOG.values() if b["id"] == "sun")
        planets = sum(1 for b in SOLAR_CATALOG.values()
                      if b.get("type") == "planet" and b["id"] != "sun")
        moons = sum(1 for b in SOLAR_CATALOG.values() if b.get("type") == "moon")
        total = len(SOLAR_CATALOG)
        return stars, planets, moons, total

    def _build_ui(self):
        from core.cosmic import CosmicBackground
        self._bg = CosmicBackground(self)
        self._bg.setGeometry(self.rect())

        self._hud = NavigationHUD(self)
        self._hud.setGeometry(self.rect())
        self._hud.planet_clicked = self._on_planet_clicked
        self._hud.raise_()

        # ── Header 区域 ──
        self._header = QWidget(self)
        self._header.setAttribute(Qt.WA_TranslucentBackground)
        self._header.setFixedHeight(90)
        self._header.setGeometry(0, 10, self.width(), 90)

        hl = QVBoxLayout(self._header)
        hl.setSpacing(2)
        hl.setContentsMargins(0, 0, 0, 0)

        title = QLabel("天文馆")
        title.setStyleSheet(
            "color: #ddaaff; font-size: 24px; font-weight: 800; "
            "letter-spacing: 8px; background: transparent;"
        )
        title.setAlignment(Qt.AlignCenter)
        hl.addWidget(title)

        subtitle = QLabel("ASTRONOMY HUB · 探索太阳系与恒星世界")
        subtitle.setStyleSheet(
            "color: #776699; font-size: 11px; letter-spacing: 3px; "
            "background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignCenter)
        hl.addWidget(subtitle)

        # 分隔线
        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(255,180,40,50),
                stop:0.5 rgba(255,200,60,120),
                stop:0.7 rgba(255,180,40,50), stop:1 transparent);
            border: none;
        """)
        hl.addWidget(line)

        # ── 信息统计条 ──
        s, p, m, t = self._count_celestial()
        stats_text = f"☀ {s} 颗恒星  ·  🪐 {p} 颗行星  ·  🌑 {m} 颗卫星  ·  🔭 {t} 个天体"
        stats = QLabel(stats_text)
        stats.setStyleSheet(
            "color: rgba(200,180,220,160); font-size: 12px; font-weight: 500; "
            "letter-spacing: 2px; background: transparent;"
        )
        stats.setAlignment(Qt.AlignCenter)
        hl.addWidget(stats)

        hl.addStretch()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_bg'):
            self._bg.setGeometry(self.rect())
        if hasattr(self, '_hud'):
            self._hud.setGeometry(self.rect())
        if hasattr(self, '_header'):
            self._header.setGeometry(0, 10, self.width(), 90)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def _on_planet_clicked(self, planet_id):
        try:
            if planet_id == "solar_system":
                from modules.astronomy.solar_system.window import SolarSystemWindow
                win = SolarSystemWindow(self)
                win.show()
            elif planet_id == "solar_explorer":
                from modules.astronomy.star_catalog.catalog import StarCatalogWindow
                win = StarCatalogWindow(self)
                win.show()
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "模块未就绪",
                                f"「{planet_id}」模块加载失败：{e}")
