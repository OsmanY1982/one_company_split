# `iqra/modules/intelligence/solar_system_window.py`

> 路径：`iqra/modules/intelligence/solar_system_window.py` | 行数：530


---


```python
# -*- coding: utf-8 -*-
"""
太阳系天文馆 · SOLAR SYSTEM PLANETARIUM
300+ IAU 已命名天体 | 滚轮缩放 | 拖拽平移 | 悬停标签 | 多层级渲染
"""
import math
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QSlider
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QRadialGradient, QFont,
)

from core.cosmic import CosmicBackground
from core.planet_painter import PLANET_STYLES, paint_planet
from modules.intelligence.solar_system_data import (
    SOLAR_CATALOG, total_count, get_children, all_bodies,
    km_to_px, radius_to_px, PLANET_PALETTE,
)

# ═══════════════════════════════════════════════════════
# 色彩常量
# ═══════════════════════════════════════════════════════
ORBIT_ALPHA = 25          # 轨道线透明度 (≈0.10)
ORBIT_COLORS = {
    "mercury": QColor(180, 180, 180, ORBIT_ALPHA),
    "venus":   QColor(255, 220, 100, ORBIT_ALPHA),
    "earth":   QColor(80,  160, 255, ORBIT_ALPHA),
    "mars":    QColor(220, 100, 60,  ORBIT_ALPHA),
    "jupiter": QColor(220, 180, 100, ORBIT_ALPHA),
    "saturn":  QColor(230, 210, 160, ORBIT_ALPHA),
    "uranus":  QColor(100, 220, 200, ORBIT_ALPHA),
    "neptune": QColor(60,  140, 240, ORBIT_ALPHA),
    "pluto":   QColor(180, 160, 140, ORBIT_ALPHA),
    "default": QColor(140, 100, 200, ORBIT_ALPHA),
}
MOON_ORBIT_ALPHA = 18     # 卫星轨道透明度

# 缩放范围
ZOOM_MIN, ZOOM_MAX = 0.25, 25.0
ZOOM_DEFAULT = 1.0

# ═══════════════════════════════════════════════════════
# 渲染 HUD 层
# ═══════════════════════════════════════════════════════

class SolarSystemHUD(QWidget):
    """太阳系渲染叠加层 — 缩放/平移/悬停"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self._base_center = QPointF(450, 350)
        self._center = QPointF(450, 350)
        self._zoom = ZOOM_DEFAULT
        self._pan_x, self._pan_y = 0.0, 0.0
        self._t = 0.0
        self._dragging = False
        self._drag_start = QPointF(0, 0)
        self._drag_pan_start = (0.0, 0.0)
        self._hovered_id = None
        self._hovered_pos = QPointF(0, 0)
        self._hovered_name = ""

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    def _tick(self):
        self._t += 0.016
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._base_center = QPointF(self.width() / 2, self.height() / 2)
        self._update_center()

    def _update_center(self):
        self._center = QPointF(
            self._base_center.x() + self._pan_x,
            self._base_center.y() + self._pan_y,
        )

    # ── 缩放/平移 ──

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        factor = 1.12 if delta > 0 else 1.0 / 1.12
        new_zoom = max(ZOOM_MIN, min(ZOOM_MAX, self._zoom * factor))
        # 以鼠标位置为中心缩放
        mx, my = event.pos().x(), event.pos().y()
        cx, cy = self._center.x(), self._center.y()
        self._pan_x = mx - (mx - cx) * (new_zoom / self._zoom)
        self._pan_y = my - (my - cy) * (new_zoom / self._zoom)
        self._zoom = new_zoom
        self._update_center()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_start = event.pos()
            self._drag_pan_start = (self._pan_x, self._pan_y)
            self.setCursor(Qt.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self.setCursor(Qt.ArrowCursor)

    def mouseMoveEvent(self, event):
        if self._dragging:
            dx = event.pos().x() - self._drag_start.x()
            dy = event.pos().y() - self._drag_start.y()
            self._pan_x = self._drag_pan_start[0] + dx
            self._pan_y = self._drag_pan_start[1] + dy
            self._update_center()
            return

        # 悬停检测
        self._hovered_id = None
        pos = event.pos()
        best_dist = 9999
        best_body = None

        for body in self._bodies_for_current_zoom():
            spos = self._body_screen_pos(body)
            if spos is None:
                continue
            dx = pos.x() - spos.x()
            dy = pos.y() - spos.y()
            r = max(6, radius_to_px(body["radius_km"], self._zoom) * 1.5)
            dist = dx * dx + dy * dy
            if dist < r * r and dist < best_dist:
                best_dist = dist
                best_body = body

        if best_body:
            self._hovered_id = best_body["id"]
            self._hovered_name = best_body["name"]
            self._hovered_pos = self._body_screen_pos(best_body)
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    # ── 坐标计算 ──

    def _body_screen_pos(self, body):
        """天体在屏幕上的位置"""
        if body["id"] == "sun":
            return self._center

        parent = SOLAR_CATALOG.get(body["parent"])
        if parent is None:
            return None

        if body["type"] in ("planet", "dwarf"):
            orbit_px = km_to_px(body["orbit_km"], self._zoom)
            angle = self._t * (2 * math.pi / max(body["period_d"], 0.1)) * 365.25
            cx, cy = self._center.x(), self._center.y()
            return QPointF(cx + orbit_px * math.cos(angle),
                           cy + orbit_px * math.sin(angle))
        else:
            # 卫星 — 先找母行星屏幕位置，再算相对偏移
            ppos = self._body_screen_pos(parent)
            if ppos is None:
                return None
            moon_orbit_px = km_to_px(body["orbit_km"], self._zoom * 8.0)
            angle = self._t * (2 * math.pi / max(body["period_d"], 0.01)) * 365.25
            return QPointF(ppos.x() + moon_orbit_px * math.cos(angle),
                           ppos.y() + moon_orbit_px * math.sin(angle))

    def _bodies_for_current_zoom(self):
        """按当前缩放级别筛选可见天体"""
        bodies = []
        for body in all_bodies():
            if body["id"] == "sun":
                bodies.append(body)
                continue
            if body["tier"] == 0:
                bodies.append(body)
            elif body["tier"] == 1 and self._zoom >= 0.6:
                bodies.append(body)
            elif body["tier"] == 2 and self._zoom >= 1.8:
                bodies.append(body)
            elif body["tier"] == 3 and self._zoom >= 4.5:
                bodies.append(body)
        return bodies

    # ── 绘制 ──

    def _paint_orbit(self, p, orbit_px, body_id, is_moon=False):
        """绘制轨道圆环"""
        if orbit_px < 1.5 and not is_moon:
            return
        if is_moon and orbit_px < 0.8:
            return
        # 颜色按母行星区分
        parent = SOLAR_CATALOG.get(body_id, {})
        palette_key = parent.get("parent", "default") if is_moon else body_id
        color = ORBIT_COLORS.get(palette_key, ORBIT_COLORS["default"])
        alpha = MOON_ORBIT_ALPHA if is_moon else ORBIT_ALPHA
        pen = QPen(QColor(color.red(), color.green(), color.blue(), alpha))
        pen.setWidth(1)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        center = self._center if not is_moon else QPointF(0, 0)
        p.drawEllipse(self._center, orbit_px, orbit_px)

    def _paint_sun_corona(self, p):
        """太阳日冕 — 多层径向渐变"""
        cx, cy = self._center.x(), self._center.y()
        sun_r = max(8, radius_to_px(696340, self._zoom))
        corona_r = sun_r * 3.5
        for i in range(3):
            scale = 2.0 + i * 0.8
            r = sun_r * scale
            corona = QRadialGradient(QPointF(cx, cy), r)
            corona.setColorAt(0, QColor(255, 200, 50, 25 - i * 7))
            corona.setColorAt(0.3, QColor(255, 160, 30, 12 - i * 4))
            corona.setColorAt(0.6, QColor(255, 100, 20, 3))
            corona.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(corona)
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(cx, cy), r, r)

    def _paint_mini_body(self, p, pos, color_hex, r):
        """小卫星 — QRadialGradient 球体"""
        if r < 0.4:
            return
        r = max(r, 0.8)
        cx, cy = pos.x(), pos.y()
        grad = QRadialGradient(cx - r * 0.3, cy - r * 0.35, r)
        grad.setColorAt(0, QColor(color_hex).lighter(140))
        grad.setColorAt(0.5, QColor(color_hex))
        grad.setColorAt(1, QColor(color_hex).darker(180))
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(pos, r, r)

        spec = QRadialGradient(cx - r * 0.35, cy - r * 0.4, r * 0.5)
        spec.setColorAt(0, QColor(255, 255, 255, 45))
        spec.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(spec)
        p.drawEllipse(pos, r, r)

    def _paint_hover_label(self, p):
        """悬停标签"""
        if not self._hovered_id:
            return
        pos = self._hovered_pos
        name = self._hovered_name
        font = QFont("PingFang SC", 11, QFont.Bold)
        p.setFont(font)
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(name)
        tx = pos.x() - tw / 2
        ty = pos.y() - 18

        # 背景暗底
        p.setBrush(QColor(5, 5, 20, 180))
        p.setPen(QPen(QColor(140, 100, 200, 100), 1))
        pad = 5
        p.drawRoundedRect(QRectF(tx - pad, ty - fm.height() + 2, tw + pad * 2,
                          fm.height() + 4), 4, 4)

        # 文字
        p.setPen(QColor(220, 200, 255))
        p.drawText(QPointF(tx, ty), name)

    def _visible_in_viewport(self, pos, margin=50):
        """检查点是否在视口内"""
        if pos is None:
            return False
        return (-margin < pos.x() < self.width() + margin and
                -margin < pos.y() < self.height() + margin)

    # ── 主绘制 ──

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w2 = self._center

        visible = self._bodies_for_current_zoom()

        # ── 太阳日冕 ──
        self._paint_sun_corona(p)

        # ── 天体分组 ──
        planet_bodies = [b for b in visible if b["type"] in ("planet", "dwarf")]
        moon_bodies = [b for b in visible if b["type"] == "moon"]
        # 按 parent 分组卫星
        moons_by_parent = {}
        for m in moon_bodies:
            moons_by_parent.setdefault(m["parent"], []).append(m)

        # ── 行星/矮行星轨道 ──
        for body in planet_bodies:
            orbit_px = km_to_px(body["orbit_km"], self._zoom)
            self._paint_orbit(p, orbit_px, body["id"])

        # ── 行星位置预先计算 ──
        planet_pos = {}
        for body in planet_bodies:
            planet_pos[body["id"]] = self._body_screen_pos(body)

        # ── 卫星轨道（绕母行星）──
        for parent_id, moons in moons_by_parent.items():
            ppos = planet_pos.get(parent_id)
            if ppos is None:
                continue
            for moon in moons:
                moon_orbit_px = km_to_px(moon["orbit_km"], self._zoom * 8.0)
                if moon_orbit_px < 0.8:
                    continue
                moon_pen = QPen(QColor(
                    ORBIT_COLORS.get(parent_id, ORBIT_COLORS["default"]).red(),
                    ORBIT_COLORS.get(parent_id, ORBIT_COLORS["default"]).green(),
                    ORBIT_COLORS.get(parent_id, ORBIT_COLORS["default"]).blue(),
                    MOON_ORBIT_ALPHA,
                ))
                moon_pen.setWidth(1)
                p.setPen(moon_pen)
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(ppos, moon_orbit_px, moon_orbit_px)

        # ── 卫星渲染（在行星下方）──
        for parent_id, moons in moons_by_parent.items():
            ppos = planet_pos.get(parent_id)
            if ppos is None or not self._visible_in_viewport(ppos):
                continue
            parent_body = SOLAR_CATALOG.get(parent_id)
            parent_angle = (self._t * (2 * math.pi / max(parent_body["period_d"], 0.1))
                            * 365.25) if parent_body else 0
            for mi, moon in enumerate(moons):
                moon_orbit_px = km_to_px(moon["orbit_km"], self._zoom * 8.0)
                if moon_orbit_px < 0.4:
                    continue
                m_angle = (self._t * (2 * math.pi / max(moon["period_d"], 0.01)) * 365.25
                           + mi * math.radians(72))
                mpos = QPointF(ppos.x() + moon_orbit_px * math.cos(m_angle),
                               ppos.y() + moon_orbit_px * math.sin(m_angle))
                if not self._visible_in_viewport(mpos):
                    continue
                mr = radius_to_px(moon["radius_km"], self._zoom)
                color = moon.get("color", "#999999")
                self._paint_mini_body(p, mpos, color, mr)

        # ── 行星/矮行星渲染 ──
        for body in planet_bodies:
            pos = planet_pos[body["id"]]
            if pos is None or not self._visible_in_viewport(pos):
                continue
            style = PLANET_STYLES.get(body["style"], PLANET_STYLES["neptune"])
            r = radius_to_px(body["radius_km"], self._zoom)
            r = max(r, 2.5)
            paint_planet(p, pos, r, style, hovered=False, label=body["name"], font_size=9,
                         anim_t=self._t)

        # ── 太阳 ──
        sun = SOLAR_CATALOG["sun"]
        sun_r = radius_to_px(sun["radius_km"], self._zoom)
        sun_r = max(sun_r, 10)
        sun_style = PLANET_STYLES["sun"]
        paint_planet(p, w2, sun_r, sun_style, hovered=False, label="太阳", font_size=10,
                     anim_t=self._t)

        # ── 悬停标签 ──
        self._paint_hover_label(p)

        p.end()


# ═══════════════════════════════════════════════════════
# 主窗口 — SolarSystemWindow
# ═══════════════════════════════════════════════════════

class SolarSystemWindow(QWidget):
    """太阳系天文馆 — 可缩放交互窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("太阳系天文馆")
        self.setMinimumSize(700, 500)
        self.resize(1000, 750)

        # 底层宇宙背景
        self._bg = CosmicBackground(self)
        self._bg.setGeometry(0, 0, self.width(), self.height())

        # 太阳系 HUD
        self._hud = SolarSystemHUD(self)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._hud.raise_()

        # 底部状态标签
        count = total_count()
        self._status = QLabel(f"太阳系 · 已命名天体 {count}", self)
        self._status.setStyleSheet(
            "color: #7766aa; background: transparent; font-size: 11px;"
            " font-family: 'PingFang SC';"
        )
        self._status.setAlignment(Qt.AlignCenter)
        self._status.setGeometry(0, self.height() - 24, self.width(), 20)

        # 提示标签
        self._hint = QLabel("滚轮缩放 · 拖拽平移 · 悬停查看", self)
        self._hint.setStyleSheet(
            "color: #554477; background: transparent; font-size: 10px;"
            " font-family: 'PingFang SC';"
        )
        self._hint.setAlignment(Qt.AlignRight)
        self._hint.setGeometry(self.width() - 260, self.height() - 24, 250, 20)

        # 星谱跳转按钮
        self._catalog_btn = QPushButton("📖 打开星谱", self)
        self._catalog_btn.setStyleSheet(
            "QPushButton {"
            " color: #7799cc; background: rgba(20, 35, 65, 0.85);"
            " border: 1px solid rgba(60, 130, 200, 0.3); border-radius: 6px;"
            " padding: 3px 12px; font-size: 11px; font-family: 'PingFang SC';"
            " }"
            " QPushButton:hover {"
            " background: rgba(40, 70, 130, 0.9); color: #00ccff;"
            " border-color: rgba(0, 200, 255, 0.5);"
            " }"
        )
        self._catalog_btn.clicked.connect(self._open_catalog)
        self._catalog_btn.setGeometry(8, self.height() - 26, 110, 24)

        # 缩放控制按钮（样式与 _catalog_btn 一致）
        _btn_style = (
            "QPushButton {"
            " color: #7799cc; background: rgba(20, 35, 65, 0.85);"
            " border: 1px solid rgba(60, 130, 200, 0.3); border-radius: 6px;"
            " padding: 2px 6px; font-size: 13px; font-family: 'PingFang SC';"
            " }"
            " QPushButton:hover {"
            " background: rgba(40, 70, 130, 0.9); color: #00ccff;"
            " border-color: rgba(0, 200, 255, 0.5);"
            " }"
        )

        self._zoom_out_btn = QPushButton("−", self)
        self._zoom_out_btn.setStyleSheet(_btn_style)
        self._zoom_out_btn.clicked.connect(self._on_zoom_out)
        self._zoom_out_btn.setGeometry(130, self.height() - 26, 28, 24)

        self._zoom_slider = QSlider(Qt.Horizontal, self)
        self._zoom_slider.setRange(int(ZOOM_MIN * 100), int(ZOOM_MAX * 100))
        self._zoom_slider.setValue(int(ZOOM_DEFAULT * 100))
        self._zoom_slider.setStyleSheet(
            "QSlider::groove:horizontal {"
            " background: rgba(30, 50, 80, 0.5); border: 1px solid rgba(60, 130, 200, 0.2);"
            " border-radius: 3px; height: 6px;"
            " }"
            " QSlider::handle:horizontal {"
            " background: #5588cc; border: 1px solid #7799dd;"
            " border-radius: 5px; width: 12px; margin: -4px 0;"
            " }"
            " QSlider::handle:horizontal:hover { background: #00ccff; }"
            " QSlider::sub-page:horizontal {"
            " background: rgba(60, 120, 200, 0.4); border-radius: 3px;"
            " }"
        )
        self._zoom_slider.valueChanged.connect(self._on_zoom_changed)
        self._zoom_slider.setGeometry(162, self.height() - 26, 130, 24)

        self._zoom_in_btn = QPushButton("+", self)
        self._zoom_in_btn.setStyleSheet(_btn_style)
        self._zoom_in_btn.clicked.connect(self._on_zoom_in)
        self._zoom_in_btn.setGeometry(296, self.height() - 26, 28, 24)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def _open_catalog(self):
        from solar_explorer.star_catalog_window import StarCatalogWindow
        self._catalog_win = StarCatalogWindow(self)
        self._catalog_win.show()
        self.hide()

    # ── 缩放控制 ─────────────────────────────────────

    def _on_zoom_changed(self, value):
        """滑块值变化 → 以窗口中心为基准缩放"""
        new_zoom = value / 100.0
        old_zoom = self._hud._zoom
        if abs(new_zoom - old_zoom) < 1e-6:
            return
        cx, cy = self.width() / 2.0, self.height() / 2.0
        scale = new_zoom / old_zoom
        self._hud._pan_x = cx + scale * (self._hud._pan_x - cx)
        self._hud._pan_y = cy + scale * (self._hud._pan_y - cy)
        self._hud._zoom = new_zoom

    def _on_zoom_in(self):
        """放大 1.12 倍"""
        new_zoom = min(self._hud._zoom * 1.12, ZOOM_MAX)
        self._zoom_slider.setValue(int(new_zoom * 100))

    def _on_zoom_out(self):
        """缩小 1.12 倍"""
        new_zoom = max(self._hud._zoom / 1.12, ZOOM_MIN)
        self._zoom_slider.setValue(int(new_zoom * 100))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        if hasattr(self, '_bg'):
            self._bg.setGeometry(0, 0, w, h)
        if hasattr(self, '_hud'):
            self._hud.setGeometry(0, 0, w, h)
        if hasattr(self, '_status'):
            self._status.setGeometry(0, h - 24, w, 20)
        if hasattr(self, '_hint'):
            self._hint.setGeometry(w - 260, h - 24, 250, 20)
        if hasattr(self, '_catalog_btn'):
            self._catalog_btn.setGeometry(8, h - 26, 110, 24)
        if hasattr(self, '_zoom_out_btn'):
            self._zoom_out_btn.setGeometry(130, h - 26, 28, 24)
        if hasattr(self, '_zoom_slider'):
            self._zoom_slider.setGeometry(162, h - 26, 130, 24)
        if hasattr(self, '_zoom_in_btn'):
            self._zoom_in_btn.setGeometry(296, h - 26, 28, 24)

```
