# `core/modules/astronomy/solar_system/window/_hud.py`

> 路径：`core/modules/astronomy/solar_system/window/_hud.py` | 行数：554


---


```python
# -*- coding: utf-8 -*-
"""
太阳系天文馆 · HUD 渲染叠加层
"""
import math
import subprocess
import threading
import hashlib

from PyQt5.QtWidgets import QWidget, QMenu, QAction, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QRadialGradient, QFont,
)

try:
    from planet_painter import PLANET_STYLES, paint_planet
except ImportError:
    try:
        from planet_painter import PLANET_STYLES, paint_planet
    except ImportError:
        from core.planet_painter import PLANET_STYLES, paint_planet
from core.modules.astronomy.solar_system.renderer import paint_nebula
from core.modules.astronomy.solar_system.data import (
    SOLAR_CATALOG, get_children, all_bodies,
    km_to_px, radius_to_px,
)
from core.modules.astronomy.star_catalog.detail import _to_spoken_form

from ._colors import ORBIT_ALPHA, ORBIT_COLORS, MOON_ORBIT_ALPHA, ZOOM_DEFAULT, ZOOM_MIN, ZOOM_MAX, RICH_FACTS


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
        self._phases = {}
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
        speed = getattr(self.parent(), '_speed', 1.0)
        self._t += 0.003 * speed
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
        # macOS 触控板 pinch 优先 pixelDelta，鼠标滚轮回退 angleDelta
        delta = event.pixelDelta().y()
        if delta == 0:
            delta = event.angleDelta().y()
        if delta == 0:
            return
        factor = 1.15 if delta > 0 else 1.0 / 1.15
        new_zoom = max(ZOOM_MIN, min(ZOOM_MAX, self._zoom * factor))
        if new_zoom == self._zoom:
            return  # 已达缩放极限
        # 以鼠标位置为中心缩放
        mx, my = event.pos().x(), event.pos().y()
        cx, cy = self._center.x(), self._center.y()
        bx, by = self._base_center.x(), self._base_center.y()
        self._pan_x = mx - (mx - cx) * (new_zoom / self._zoom) - bx
        self._pan_y = my - (my - cy) * (new_zoom / self._zoom) - by
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

    def contextMenuEvent(self, event):
        body = self._find_body_at(event.pos())
        if body is None:
            return
        menu = QMenu(self)
        text_action = QAction("文字介绍", self)
        text_action.triggered.connect(lambda: self._show_description(body))
        speak_action = QAction("语音介绍", self)
        speak_action.triggered.connect(lambda: self._speak_description(body))
        menu.addAction(text_action)
        menu.addAction(speak_action)

        # 地球专属：地图导航
        if body.get("id") == "earth":
            map_action = QAction("地图导航", self)
            map_action.triggered.connect(self._open_map)
            menu.addAction(map_action)

        menu.exec_(event.globalPos())

    def _find_body_at(self, pos):
        """返回鼠标位置命中的天体数据，未命中返回 None"""
        bodies = self._bodies_for_current_zoom()
        for body in bodies:
            sp = self._body_screen_pos(body)
            if sp is None:
                continue
            dx = pos.x() - sp.x()
            dy = pos.y() - sp.y()
            # 命中半径与悬停检测统一：小星体也保证≥6px可点
            r_km = body.get("radius_km", body.get("mean_radius_km", 1000))
            r_px = max(6, radius_to_px(r_km, self._zoom) * 1.5)
            if dx * dx + dy * dy <= r_px * r_px:
                return body
        return None

    def _body_radius_px(self, body):
        """估算天体在屏幕上的像素半径"""
        r_km = body.get("radius_km", body.get("mean_radius_km", 1000))
        r_px = radius_to_px(r_km, self._zoom)
        return max(r_px, 3) + 2

    def _build_description(self, body):
        """用知识库+已有数据拼自然语言介绍——讲解员风格，口语化朗读。"""
        name = body.get("name", body.get("id", "Unknown"))
        body_id = body.get("id", "")
        body_type = body.get("type", "unknown")
        parent_name = body.get("parent", "")
        parent_body = SOLAR_CATALOG.get(parent_name, {})
        parent_cn = parent_body.get("name", parent_name)
        radius = body.get("radius_km", 0)
        orbit_r = body.get("orbit_km", 0)
        period = body.get("period_d", 0)

        type_map = {"star": "恒星", "planet": "行星", "dwarf": "矮行星",
                     "moon": "卫星", "asteroid": "小行星", "comet": "彗星"}
        cn_type = type_map.get(body_type, "天体")

        # ── 知识库核心描述 ──
        fact = RICH_FACTS.get(body_id) or ""

        # ── 组装口语化介绍 ──
        lines = []
        if fact:
            lines.append(fact)
        else:
            if body_type == "moon" and parent_name:
                lines.append(f"{name}是{parent_cn}的一颗{cn_type}")
            else:
                lines.append(f"{name}是一颗{cn_type}")

        # 物理参数（融入叙事，不独立成句）
        size_note = ""
        if isinstance(radius, (int, float)) and radius > 0:
            r_earth = 6371
            ratio = radius / r_earth
            dia = radius * 2
            if ratio < 0.01:
                size_note = f"直径大约{int(dia)}公里，算是很小的天体了"
            elif ratio < 0.5:
                size_note = f"直径大约{int(dia)}公里，大约是地球的{ratio:.1%}"
            elif ratio < 1.5:
                size_note = f"直径大约{int(dia)}公里，个头跟地球差不多"
            elif ratio < 12:
                size_note = f"直径大约{int(dia):,}公里，是地球的{ratio:.0f}倍"
            else:
                size_note = f"直径大约{int(dia):,}公里，是地球的{ratio:.0f}倍，非常庞大"
            if not fact:
                lines.append(size_note + "。")

        # 轨道（融入一句）
        orbit_note = ""
        if isinstance(orbit_r, (int, float)) and orbit_r > 0 and body_type != "star":
            au = orbit_r / 149597870.7
            if au >= 0.01:
                orbit_note = f"距离{parent_cn}大约{orbit_r:,.0f}公里，相当于{au:.1f}个天文单位"
            else:
                orbit_note = f"在距离{parent_cn}约{orbit_r:,.0f}公里的轨道上运行"
            if not fact:
                lines.append(orbit_note + "。")

        # 公转周期（融入一句）
        period_note = ""
        if isinstance(period, (int, float)) and period > 0:
            days = period
            if days >= 365:
                years = days / 365.25
                period_note = f"绕行一圈需要{years:.1f}年，大约{days:.0f}个地球日"
            elif days >= 1:
                period_note = f"公转周期大约{days:.0f}天"
            else:
                hours = days * 24
                period_note = f"公转周期只有{hours:.1f}个小时，转得飞快"
            if not fact:
                lines.append(period_note + "。")

        # 卫星统计
        if body_type in ("planet", "dwarf"):
            children = get_children(body_id)
            if children:
                moon_count = sum(1 for c in children if c["type"] == "moon")
                if moon_count > 0:
                    lines.append(f"目前已确认拥有{moon_count}颗卫星。")

        return "".join(lines)

    def _show_description(self, body):
        text = self._build_description(body)
        QMessageBox.information(self, body.get("name", body.get("id")), text)

    def _speak_description(self, body):
        text = self._build_description(body)
        text = _to_spoken_form(text)  # 口语化：英文术语、符号转中文
        name = body.get("name", body.get("id", "天体"))
        threading.Thread(target=lambda: subprocess.run(
            ["say", "-v", "Ting-Ting", f"{name}。{text}"],
            capture_output=True,
        ), daemon=True).start()

    def _open_map(self):
        """在系统默认浏览器中打开在线地图"""
        import webbrowser
        webbrowser.open("https://www.amap.com/")

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
            angle = (self._t * (2 * math.pi / math.sqrt(max(body["period_d"], 0.1))) * 0.5
                     + self._get_phase(body["id"]))
            cx, cy = self._center.x(), self._center.y()
            return QPointF(cx + orbit_px * math.cos(angle),
                           cy + orbit_px * math.sin(angle))
        else:
            # 卫星 — 先找母行星屏幕位置，再算相对偏移
            ppos = self._body_screen_pos(parent)
            if ppos is None:
                return None
            moon_orbit_px = km_to_px(body["orbit_km"], self._zoom * 8.0)
            angle = (self._t * (2 * math.pi / math.sqrt(max(body["period_d"], 0.01))) * 0.5
                     + self._get_phase(body["id"]))
            return QPointF(ppos.x() + moon_orbit_px * math.cos(angle),
                           ppos.y() + moon_orbit_px * math.sin(angle))

    def _get_phase(self, body_id):
        """返回天体初始轨道相位（弧度），用 hash 保证确定性、启动即分散。"""
        if body_id not in self._phases:
            h = int(hashlib.md5(body_id.encode()).hexdigest(), 16)
            self._phases[body_id] = math.radians(h % 360)
        return self._phases[body_id]

    def _bodies_for_current_zoom(self):
        """按当前缩放级别筛选可见天体"""
        bodies = []
        for body in all_bodies():
            if body["id"] == "sun":
                bodies.append(body)
                continue
            if body["tier"] == 0:
                bodies.append(body)
            elif body["tier"] == 1 and self._zoom >= 0.25:
                bodies.append(body)
            elif body["tier"] == 2 and self._zoom >= 0.35:
                bodies.append(body)
            elif body["tier"] == 3 and self._zoom >= 0.5:
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
        if is_moon:
            alpha = 0  # 卫星轨道始终隐藏，避免数百条线干扰视效
        else:
            alpha = 0 if self._zoom < 1.2 else min(ORBIT_ALPHA, int((self._zoom - 1.2) * 5))
        pen = QPen(QColor(color.red(), color.green(), color.blue(), alpha))
        pen.setWidthF(2.0)
        pen.setCapStyle(Qt.RoundCap)
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

    def _paint_mini_body(self, p, pos, color_hex, r, label=""):
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

        # 标签
        if label:
            font = QFont("PingFang SC", 7)
            p.setFont(font)
            p.setPen(QColor(255, 255, 255, 200))
            label_rect = QRectF(cx - 30, cy + r + 4, 60, 14)
            p.drawText(label_rect, Qt.AlignCenter, label)

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
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        w, h = self.width(), self.height()
        w2 = self._center

        # ── 星云背景 ──
        paint_nebula(p, w, h)

        visible = self._bodies_for_current_zoom()
        speed = getattr(self.parent(), '_speed', 1.0) if self.parent() else 1.0

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
                moon_orbit_alpha = 0  # 卫星轨道始终隐藏
                moon_pen = QPen(QColor(
                    ORBIT_COLORS.get(parent_id, ORBIT_COLORS["default"]).red(),
                    ORBIT_COLORS.get(parent_id, ORBIT_COLORS["default"]).green(),
                    ORBIT_COLORS.get(parent_id, ORBIT_COLORS["default"]).blue(),
                    moon_orbit_alpha,
                ))
                moon_pen.setWidthF(1.5)
                moon_pen.setCapStyle(Qt.RoundCap)
                p.setPen(moon_pen)
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(ppos, moon_orbit_px, moon_orbit_px)

        # ── 卫星渲染（在行星下方）──
        for parent_id, moons in moons_by_parent.items():
            ppos = planet_pos.get(parent_id)
            if ppos is None:
                continue
            parent_body = SOLAR_CATALOG.get(parent_id)
            for mi, moon in enumerate(moons):
                moon_orbit_px = km_to_px(moon["orbit_km"], self._zoom * 8.0)
                if moon_orbit_px < 0.4:
                    continue
                m_angle = ((self._t * (2 * math.pi / math.sqrt(max(moon["period_d"], 0.01))) * 0.5
                           + self._get_phase(moon["id"])
                           + mi * math.radians(72)))
                mpos = QPointF(ppos.x() + moon_orbit_px * math.cos(m_angle),
                               ppos.y() + moon_orbit_px * math.sin(m_angle))
                if not self._visible_in_viewport(mpos):
                    continue
                mr = radius_to_px(moon["radius_km"], self._zoom)
                mr = max(mr, 2.5)
                # 卫星像素半径足够大时显示名称标签
                moon_label = moon.get("name", "") if mr >= 5 else ""
                moon_style = moon.get("style")
                if moon_style is not None:
                    if isinstance(moon_style, str):
                        moon_style = PLANET_STYLES.get(moon_style, PLANET_STYLES["neptune"])
                    paint_planet(p, mpos, mr, moon_style, hovered=False,
                                 label=moon_label, font_size=7,
                                 anim_t=self._t * 0.3 * speed)
                else:
                    color = moon.get("color", "#999999")
                    self._paint_mini_body(p, mpos, color, mr, label=moon_label)

        # ── 行星/矮行星渲染 ──
        for body in planet_bodies:
            pos = planet_pos[body["id"]]
            if pos is None or not self._visible_in_viewport(pos):
                continue
            style = body["style"]
            if isinstance(style, str):
                style = PLANET_STYLES.get(style, PLANET_STYLES["neptune"])
            r = radius_to_px(body["radius_km"], self._zoom)
            r = max(r, 2.5)
            paint_planet(p, pos, r, style, hovered=False, font_size=9,
                         label=body.get("name", ""),
                         anim_t=self._t * 0.4 * speed)

        # ── 太阳 ──
        sun = SOLAR_CATALOG["sun"]
        sun_r = radius_to_px(sun["radius_km"], self._zoom)
        sun_r = max(sun_r, 10)
        sun_style = PLANET_STYLES["sun"]
        paint_planet(p, w2, sun_r, sun_style, hovered=False,
                     label=sun.get("name", ""),
                     anim_t=self._t * 0.3 * speed)

        # ── 悬停标签 ──
        self._paint_hover_label(p)

        p.end()

```
