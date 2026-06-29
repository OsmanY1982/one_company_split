# -*- coding: utf-8 -*-
"""星球渲染通用基类 — 球面纹理 / 标签 / 悬停边框"""
import math, random
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QRadialGradient, QColor, QPen, QFont, QPainterPath,
)


def _lerp_color(a: QColor, b: QColor, t: float) -> QColor:
    return QColor(
        int(a.red() + (b.red() - a.red()) * t),
        int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t),
        int(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


def _noise_1d(seed: float, x: float, scale: float = 1.0) -> float:
    return math.sin(x * scale * 7.1 + seed * 13.7) * math.cos(x * scale * 3.3 - seed * 5.9)


def _band_interpolate(colors: list, t: float) -> QColor:
    if t <= colors[0][0]:
        return colors[0][1]
    if t >= colors[-1][0]:
        return colors[-1][1]
    for i in range(len(colors) - 1):
        if colors[i][0] <= t <= colors[i + 1][0]:
            lt = (t - colors[i][0]) / (colors[i + 1][0] - colors[i][0])
            return _lerp_color(colors[i][1], colors[i + 1][1], lt)
    return colors[-1][1]


def _paint_surface(p: QPainter, center: QPointF, r: float, style: dict, anim_t: float):
    """多层横纹 + 湍流扰动 + 3D 球体光照"""
    cx, cy = center.x(), center.y()
    band_colors = style.get("band_colors", [(0.0, QColor(128, 128, 128)), (1.0, QColor(128, 128, 128))])
    turbulence = style.get("turbulence", 0.1)
    feature_spots = style.get("feature_spots", 0)
    has_bands = style.get("bands", False)
    great_spot = style.get("great_spot")

    p.save()
    clip = QPainterPath()
    clip.addEllipse(center, r, r)
    p.setClipPath(clip)

    seed = 42 + hash(style.get("name", "")) % 1000
    num_strips = 60
    strip_h = (r * 2) / num_strips
    for i in range(num_strips):
        y_local = -r + i * strip_h + strip_h / 2
        y_abs = cy + y_local
        ny = y_local / r
        span = math.sqrt(max(0, r * r - y_local * y_local))
        if span < 0.5:
            continue
        twist = turbulence * span * _noise_1d(seed + i * 0.7, ny, 4.0 + float(has_bands))
        twist += (0.02 * span * math.sin(ny * 15 + anim_t * 2.0)) if has_bands else 0
        t = (ny + 1) / 2
        strip_color = _band_interpolate(band_colors, t)
        noise_val = _noise_1d(seed + i, ny + anim_t * 0.1, 3.5) * 25
        rv = max(0, min(255, strip_color.red() + int(noise_val)))
        gv = max(0, min(255, strip_color.green() + int(noise_val)))
        bv = max(0, min(255, strip_color.blue() + int(noise_val)))
        strip_color = QColor(rv, gv, bv)
        x_left = cx - span + twist
        x_width = span * 2
        p.setBrush(strip_color)
        p.setPen(Qt.NoPen)
        p.drawRect(QRectF(x_left, y_abs - strip_h / 2, x_width, strip_h + 1))

    # ── 斑点 ──
    random.seed(int(seed + 1000))
    for _ in range(feature_spots):
        fy = random.uniform(-r * 0.85, r * 0.85)
        fspan = math.sqrt(max(0, r * r - fy * fy))
        fx = random.uniform(-fspan * 0.7, fspan * 0.7)
        spot_r = random.uniform(0.03, 0.08) * r
        spot_color = QColor(
            random.randint(0, 80), random.randint(0, 80),
            random.randint(0, 80), random.randint(30, 100),
        )
        spot_grad = QRadialGradient(QPointF(cx + fx, cy + fy), spot_r)
        spot_grad.setColorAt(0, spot_color)
        spot_grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(spot_grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(cx + fx, cy + fy), spot_r, spot_r * 0.7)

    # ── 大红斑 ──
    if great_spot:
        gs = great_spot
        # 自转：让大红斑随 anim_t 横移
        spot_shift = math.sin(anim_t * 0.5) * 0.28
        gx = cx + (gs["x"] - 0.5 + spot_shift) * r * 2
        gy = cy + (gs["y"] - 0.5) * r * 2
        gw = gs["w"] * r * 2
        gh = gs["h"] * r * 2
        spot_grad = QRadialGradient(QPointF(gx, gy), gw * 0.7)
        gc = gs["color"]
        spot_grad.setColorAt(0, gc)
        spot_grad.setColorAt(0.5, QColor(gc.red(), gc.green() // 2, gc.blue() // 3, 120))
        spot_grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(spot_grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(gx, gy), gw, gh)

    random.seed()

    # ── 3D 光照 ──
    light_x = cx - r * 0.35
    light_y = cy - r * 0.35
    shadow = QRadialGradient(light_x, light_y, r * 1.8)
    shadow.setColorAt(0, QColor(255, 255, 255, 0))
    shadow.setColorAt(0.35, QColor(0, 0, 0, 0))
    shadow.setColorAt(0.55, QColor(0, 0, 0, 30))
    shadow.setColorAt(0.75, QColor(0, 0, 0, 100))
    shadow.setColorAt(0.90, QColor(0, 0, 0, 170))
    shadow.setColorAt(1.0, QColor(0, 0, 0, 220))
    p.setBrush(shadow)
    p.setPen(Qt.NoPen)
    p.drawEllipse(center, r, r)

    spec = QRadialGradient(light_x, light_y, r * 0.7)
    spec.setColorAt(0, QColor(255, 255, 255, 40))
    spec.setColorAt(0.3, QColor(255, 255, 255, 15))
    spec.setColorAt(0.6, QColor(255, 255, 255, 0))
    p.setBrush(spec)
    p.drawEllipse(center, r, r)

    p.restore()


def _paint_atmosphere(p: QPainter, c: QPointF, r: float, style: dict):
    atmos = style.get("atmosphere", QColor(100, 100, 255, 30))
    for i in range(3):
        scale = 1.08 + i * 0.06
        alpha = atmos.alpha() // (i + 2)
        ac = QColor(atmos.red(), atmos.green(), atmos.blue(), alpha)
        grad = QRadialGradient(c, r * scale)
        grad.setColorAt(0, QColor(0, 0, 0, 0))
        grad.setColorAt(0.7, ac)
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(c, r * scale, r * scale)


def _paint_clouds(p: QPainter, c: QPointF, r: float, anim_t: float):
    cx, cy = c.x(), c.y()
    random.seed(88)
    p.setPen(Qt.NoPen)
    rot = anim_t * 0.25
    for _ in range(14):
        base_angle = random.uniform(0, 2 * math.pi)
        angle = (base_angle + rot) % (2 * math.pi)
        dist = random.uniform(0.15, 0.78) * r
        cloud_cx = cx + math.cos(angle) * dist
        cloud_cy = cy + math.sin(angle) * dist
        cloud_r = random.uniform(0.06, 0.16) * r
        alpha_base = random.randint(25, 60)
        cloud_grad = QRadialGradient(cloud_cx, cloud_cy, cloud_r)
        cloud_grad.setColorAt(0, QColor(255, 255, 255, alpha_base))
        cloud_grad.setColorAt(0.5, QColor(255, 255, 255, alpha_base // 3))
        cloud_grad.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(cloud_grad)
        p.drawEllipse(QPointF(cloud_cx, cloud_cy), cloud_r, cloud_r * 0.6)


def _paint_craters(p: QPainter, c: QPointF, r: float, anim_t: float):
    cx, cy = c.x(), c.y()
    random.seed(123)
    p.setPen(Qt.NoPen)
    rot = anim_t * 0.18
    for _ in range(22):
        base_angle = random.uniform(0, 2 * math.pi)
        angle = (base_angle + rot) % (2 * math.pi)
        dist = random.uniform(0.05, 0.88) * r
        crater_cx = cx + math.cos(angle) * dist
        crater_cy = cy + math.sin(angle) * dist
        crater_r = random.uniform(0.02, 0.07) * r
        crater = QRadialGradient(crater_cx, crater_cy, crater_r)
        crater.setColorAt(0, QColor(30, 30, 30, 120))
        crater.setColorAt(0.6, QColor(60, 60, 60, 60))
        crater.setColorAt(1, QColor(100, 100, 100, 5))
        p.setBrush(crater)
        p.drawEllipse(QPointF(crater_cx, crater_cy), crater_r, crater_r * 0.65)


def _paint_ring(p: QPainter, c: QPointF, r: float, vertical: bool = False):
    cx, cy = c.x(), c.y()
    ring_inner = r * 1.2
    ring_outer = r * 2.0
    ring_layers = 30
    p.save()
    p.translate(cx, cy)
    for i in range(ring_layers):
        t = i / (ring_layers - 1)
        rad = ring_inner + (ring_outer - ring_inner) * t
        gap_t = (rad - ring_inner) / (ring_outer - ring_inner)
        if 0.30 < gap_t < 0.38:
            alpha = 10 + int(15 * abs(gap_t - 0.34))
        else:
            alpha = 60 + int(40 * (1.0 - abs(gap_t - 0.5) * 1.5))
            alpha = max(8, min(100, alpha))
        t_color = gap_t
        ring_color = _lerp_color(
            QColor(210, 180, 120, alpha),
            QColor(180, 160, 110, alpha), t_color
        )
        pen = QPen(ring_color)
        pen.setWidth(2)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        if vertical:
            p.drawEllipse(QPointF(0, 0), rad, rad * 0.08)
        else:
            p.drawEllipse(QPointF(0, 0), rad, rad * 0.045)
    p.restore()


def _paint_hover_glow(p: QPainter, c: QPointF, r: float):
    draw_radius = r * 1.15
    for i in range(2):
        gs = 1.25 + i * 0.3
        glow = QRadialGradient(c, draw_radius * gs)
        glow.setColorAt(0, QColor(180, 140, 255, 45 - i * 20))
        glow.setColorAt(0.5, QColor(120, 80, 220, 15 - i * 8))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(glow)
        p.setPen(Qt.NoPen)
        p.drawEllipse(c, draw_radius * gs, draw_radius * gs)


def _paint_hover_border(p: QPainter, c: QPointF, r: float):
    pen = QPen(QColor(255, 255, 255, 180))
    pen.setWidth(2)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(c, r, r)


def _paint_label(p: QPainter, c: QPointF, r: float, label: str, font_size: int):
    fm = p.fontMetrics()
    tw = fm.horizontalAdvance(label)
    tx = c.x() - tw / 2
    ty = c.y() + r + 14
    font = QFont("PingFang SC", font_size)
    p.setFont(font)
    pad = 4
    p.setBrush(QColor(5, 5, 20, 150))
    p.setPen(QPen(QColor(80, 60, 150, 60), 1))
    p.drawRoundedRect(tx - pad, ty - fm.height() + 2, tw + pad * 2,
                      fm.height() + 4, 4, 4)
    p.setPen(QColor(200, 180, 220))
    p.drawText(QPointF(tx, ty), label)
