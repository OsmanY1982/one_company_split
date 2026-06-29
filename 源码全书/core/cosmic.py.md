# `core/cosmic.py`

> 路径：`core/cosmic.py` | 行数：434


---


```python
"""
宇宙引擎 — 深空渲染核心
提供：动态星空背景（含真实星座+银河带）、星云、粒子效果、辉光绘制
"""
import math
import random
import time
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QPainterPath, QFont
)

# ═══════════════════════════════════════════════════════
#  色彩体系
# ═══════════════════════════════════════════════════════
SPACE_VOID   = QColor(3, 5, 16)        # 深空底色
NEBULA_BLUE  = QColor(20, 30, 90, 30)  # 蓝紫星云
NEBULA_PURPLE = QColor(60, 10, 50, 25) # 紫色星云
NEBULA_TEAL  = QColor(10, 50, 60, 20)  # 青蓝星云
STAR_COLD    = QColor(180, 200, 255)    # 冷白星
STAR_WARM    = QColor(255, 220, 180)    # 暖黄星
STAR_BLUE    = QColor(150, 180, 255)    # 蓝星
HOLO_BORDER  = QColor(80, 140, 255, 60) # 全息边框
HOLO_FILL    = QColor(8, 15, 35, 200)   # 全息面板底色
ACCENT_CYAN  = QColor(0, 200, 255)
ACCENT_PURPLE = QColor(140, 80, 255)
ACCENT_GOLD  = QColor(255, 180, 50)

# ═══════════════════════════════════════════════════════
#  真实星座数据（归一化坐标 0~1，屏幕自适应）
# ═══════════════════════════════════════════════════════
CONSTELLATIONS = {
    "大熊座": {
        "stars": [
            (0.78, 0.18), (0.80, 0.22), (0.79, 0.28), (0.77, 0.33),
            (0.75, 0.36), (0.70, 0.38), (0.73, 0.33),
        ],
        "lines": [(0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(3,6)],
        "label_pos": (0.74, 0.22),
        "brightness": 1.2,
    },
    "猎户座": {
        "stars": [
            (0.38, 0.42), (0.40, 0.40), (0.42, 0.42),  # 腰带三连星
            (0.39, 0.36), (0.41, 0.48),                   # 参宿四 + 参宿七
            (0.36, 0.41), (0.44, 0.41),                   # 肩星
        ],
        "lines": [(0,1),(1,2),(3,0),(4,2),(5,0),(6,2)],
        "label_pos": (0.40, 0.34),
        "brightness": 1.5,
    },
    "仙后座": {
        "stars": [
            (0.15, 0.15), (0.18, 0.20), (0.20, 0.16),
            (0.22, 0.20), (0.25, 0.15),
        ],
        "lines": [(0,1),(1,2),(2,3),(3,4)],
        "label_pos": (0.20, 0.12),
        "brightness": 1.0,
    },
    "天鹅座": {
        "stars": [
            (0.55, 0.30), (0.57, 0.35), (0.59, 0.40),
            (0.62, 0.43), (0.66, 0.47),
            (0.58, 0.35), (0.56, 0.40),
        ],
        "lines": [(0,1),(1,2),(2,3),(3,4),(1,5),(2,6)],
        "label_pos": (0.55, 0.27),
        "brightness": 1.1,
    },
    "天蝎座": {
        "stars": [
            (0.88, 0.50), (0.85, 0.56), (0.83, 0.62),
            (0.82, 0.68), (0.80, 0.74), (0.84, 0.70),
            (0.87, 0.64),
        ],
        "lines": [(0,1),(1,2),(2,3),(3,4),(1,5),(2,6)],
        "label_pos": (0.86, 0.48),
        "brightness": 1.3,
    },
    "天琴座": {
        "stars": [
            (0.32, 0.22), (0.34, 0.24), (0.31, 0.26),
            (0.33, 0.28), (0.36, 0.25),
        ],
        "lines": [(0,1),(0,2),(0,3),(1,4)],
        "label_pos": (0.30, 0.19),
        "brightness": 0.9,
    },
    "大犬座": {
        "stars": [
            (0.52, 0.58), (0.54, 0.54), (0.50, 0.55),
            (0.48, 0.60), (0.56, 0.56),
        ],
        "lines": [(0,1),(0,2),(0,3),(1,4)],
        "label_pos": (0.50, 0.56),
        "brightness": 1.0,
    },
    "狮子座": {
        "stars": [
            (0.65, 0.55), (0.68, 0.53), (0.72, 0.55),
            (0.70, 0.62), (0.66, 0.65),
        ],
        "lines": [(0,1),(1,2),(0,3),(3,4)],
        "label_pos": (0.68, 0.50),
        "brightness": 1.0,
    },
}


class CosmicBackground(QWidget):
    """动态深空背景 — 星座 + 银河带 + 星场 + 流星 + 缓慢漂移"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._stars = []
        self._nebulas = []
        self._shooting_stars = []
        self._milky_way_stars = []
        self._t = 0
        self._generate()

        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(50)

    def _generate(self):
        random.seed(42)

        # ── 星云 ──
        nebula_specs = [
            (0.25, 0.30, 280, NEBULA_BLUE),
            (0.70, 0.25, 320, NEBULA_PURPLE),
            (0.50, 0.65, 250, NEBULA_TEAL),
            (0.15, 0.75, 220, NEBULA_BLUE),
            (0.80, 0.70, 200, NEBULA_PURPLE),
        ]
        self._nebulas = [(cx, cy, r, c) for cx, cy, r, c in nebula_specs]

        # ── 小星 ~450 颗 ──
        self._stars = []
        for _ in range(450):
            self._stars.append({
                'x': random.random(),
                'y': random.random(),
                'r': random.uniform(0.3, 1.4),
                'a': random.randint(30, 180),
                'twinkle_speed': random.uniform(0.015, 0.07),
                'twinkle_phase': random.uniform(0, math.pi * 2),
                'drift_x': random.uniform(-0.0001, 0.0001),
                'drift_y': random.uniform(-0.0001, 0.0001),
            })

        # ── 银河带星星 ~200 颗（沿对角线密集）──
        self._milky_way_stars = []
        for _ in range(200):
            # 银河带：从左上 (0.1, 0.1) 到右下 (0.9, 0.85)，宽度 ~0.25
            t = random.random()
            base_x = 0.1 + t * 0.8
            base_y = 0.05 + t * 0.82
            spread = random.gauss(0, 0.08)
            nx = base_x + spread * 0.7
            ny = base_y + spread * 1.4
            self._milky_way_stars.append({
                'x': max(0, min(1, nx)),
                'y': max(0, min(1, ny)),
                'r': random.uniform(0.2, 0.8),
                'a': random.randint(20, 100),
                'twinkle_speed': random.uniform(0.01, 0.04),
                'twinkle_phase': random.uniform(0, math.pi * 2),
            })

        # ── 亮星 ~30 颗（含星座主星）──
        self._bright_stars = []
        bright_colors = ["#aaccff", "#ffddaa", "#ccddff", "#ffffff", "#aaddff", "#ffccaa"]

        # 先加星座主星（保证星座可见）
        used_positions = set()
        for const_name, const_data in CONSTELLATIONS.items():
            for sx, sy in const_data["stars"]:
                # 量化坐标防止重复
                key = (round(sx, 3), round(sy, 3))
                if key in used_positions:
                    continue
                used_positions.add(key)
                brightness = const_data.get("brightness", 1.0)
                self._bright_stars.append({
                    'x': sx, 'y': sy,
                    'r': 1.8 * brightness,
                    'color': QColor(random.choice(bright_colors)),
                    'glow_r': 8 * brightness,
                    'constellation_member': True,
                })

        # 再补随机亮星到 35 颗
        while len(self._bright_stars) < 35:
            bx = random.random()
            by = random.random()
            # 避免太靠近已有亮星
            too_close = False
            for s in self._bright_stars:
                if abs(s['x'] - bx) < 0.04 and abs(s['y'] - by) < 0.04:
                    too_close = True
                    break
            if too_close:
                continue
            self._bright_stars.append({
                'x': bx, 'y': by,
                'r': random.uniform(1.2, 2.5),
                'color': QColor(random.choice(bright_colors)),
                'glow_r': random.uniform(5, 10),
                'constellation_member': False,
            })

        # ── 流星 ──
        self._shooting_stars = []

    def _tick(self):
        self._t += 0.04
        w, h = self.width(), self.height()

        # 小星缓慢漂移
        for s in self._stars:
            s['x'] = (s['x'] + s['drift_x']) % 1.0
            s['y'] = (s['y'] + s['drift_y']) % 1.0

        # 银河带星漂移
        for s in self._milky_way_stars:
            s['x'] = (s['x'] + s.get('drift_x', 0.00005)) % 1.0
            s['y'] = (s['y'] + s.get('drift_y', 0.00005)) % 1.0

        # 流星
        if random.random() < 0.03 and len(self._shooting_stars) < 2:
            sx = random.uniform(0, w)
            sy = random.uniform(0, h * 0.4)
            angle = random.uniform(-0.6, -0.2)
            speed = random.uniform(3, 7)
            life = random.uniform(0.6, 1.2)
            self._shooting_stars.append({
                'x': sx, 'y': sy,
                'angle': angle, 'speed': speed,
                'life': life, 'age': 0,
                'len': random.uniform(30, 80),
            })

        survivors = []
        for s in self._shooting_stars:
            s['age'] += 0.05
            s['x'] += math.cos(s['angle']) * s['speed']
            s['y'] += math.sin(s['angle']) * s['speed']
            if s['age'] < s['life'] and 0 <= s['x'] <= w and 0 <= s['y'] <= h:
                survivors.append(s)
        self._shooting_stars = survivors

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        if w == 0 or h == 0:
            painter.end()
            return

        # ═══════ 深空底色 ═══════
        painter.fillRect(0, 0, w, h, SPACE_VOID)

        # ═══════ 银河带辉光 ═══════
        self._paint_milky_way_glow(painter, w, h)

        # ═══════ 星云 ═══════
        painter.setPen(Qt.NoPen)
        for cx, cy, cr, color in self._nebulas:
            px, py = cx * w, cy * h
            # 微小的相位偏移让星云"呼吸"
            phase_shift = math.sin(self._t * 0.3 + cx * 3) * 0.02
            g = QRadialGradient(QPointF(px, py), cr * (1 + phase_shift))
            g.setColorAt(0, color)
            g.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(g))
            painter.drawEllipse(QPointF(px, py), cr, cr)

        # ═══════ 银河带密星 ═══════
        for s in self._milky_way_stars:
            px, py = s['x'] * w, s['y'] * h
            flicker = 0.5 + 0.5 * math.sin(self._t * s['twinkle_speed'] + s['twinkle_phase'])
            a = int(s['a'] * (0.6 + 0.4 * flicker))
            color = QColor(180, 200, 240, a)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(px, py), s['r'], s['r'])

        # ═══════ 小星 ═══════
        for s in self._stars:
            px, py = s['x'] * w, s['y'] * h
            flicker = 0.5 + 0.5 * math.sin(self._t * s['twinkle_speed'] + s['twinkle_phase'])
            a = int(s['a'] * (0.6 + 0.4 * flicker))
            color = QColor(200, 210, 255, a)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(px, py), s['r'], s['r'])

        # ═══════ 星座连线 ═══════
        self._paint_constellation_lines(painter, w, h)

        # ═══════ 亮星 + 辉光 ═══════
        for s in self._bright_stars:
            px, py = s['x'] * w, s['y'] * h
            c = s['color']
            # 辉光
            glow = QRadialGradient(QPointF(px, py), s['glow_r'])
            glow.setColorAt(0, QColor(c.red(), c.green(), c.blue(), 50))
            glow.setColorAt(0.4, QColor(c.red(), c.green(), c.blue(), 15))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(QPointF(px, py), s['glow_r'], s['glow_r'])
            # 核心
            painter.setBrush(QBrush(c))
            painter.drawEllipse(QPointF(px, py), s['r'], s['r'])

        # ═══════ 星座名称标签 ═══════
        self._paint_constellation_labels(painter, w, h)

        # ═══════ 流星 ═══════
        for s in self._shooting_stars:
            progress = s['age'] / s['life']
            alpha = int(255 * (1 - progress))
            ex = s['x'] - math.cos(s['angle']) * s['len']
            ey = s['y'] - math.sin(s['angle']) * s['len']
            grad = QLinearGradient(QPointF(s['x'], s['y']), QPointF(ex, ey))
            grad.setColorAt(0, QColor(255, 255, 255, alpha))
            grad.setColorAt(1, QColor(255, 255, 255, 0))
            pen = QPen(QBrush(grad), 1.5)
            painter.setPen(pen)
            painter.drawLine(QPointF(int(s['x']), int(s['y'])),
                           QPointF(int(ex), int(ey)))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, alpha)))
            painter.drawEllipse(QPointF(s['x'], s['y']), 2, 2)

        painter.end()

    # ── 银河带柔光 ──
    def _paint_milky_way_glow(self, painter, w, h):
        """绘制银河带的柔光底衬"""
        # 沿着对角方向画几个大的径向渐变
        waypoints = [
            (0.1, 0.05), (0.25, 0.18), (0.40, 0.32),
            (0.55, 0.48), (0.70, 0.62), (0.85, 0.78),
        ]
        for wx, wy in waypoints:
            px, py = wx * w, wy * h
            g = QRadialGradient(QPointF(px, py), w * 0.28)
            g.setColorAt(0, QColor(40, 60, 120, 6))
            g.setColorAt(0.5, QColor(20, 30, 80, 3))
            g.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(g))
            painter.drawEllipse(QPointF(px, py), w * 0.28, w * 0.28)

    # ── 星座连线 ──
    def _paint_constellation_lines(self, painter, w, h):
        """绘制星座连线（极淡）"""
        for const_name, const_data in CONSTELLATIONS.items():
            stars = const_data["stars"]
            lines = const_data.get("lines", [])
            # 淡入淡出效果
            base_alpha = int(18 + 6 * math.sin(self._t * 0.15 + hash(const_name) % 100 * 0.1))
            base_alpha = max(10, min(30, base_alpha))

            pen = QPen(QColor(100, 140, 200, base_alpha), 0.6)
            painter.setPen(pen)

            for i, j in lines:
                if i < len(stars) and j < len(stars):
                    x1, y1 = stars[i][0] * w, stars[i][1] * h
                    x2, y2 = stars[j][0] * w, stars[j][1] * h
                    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    # ── 星座名称 ──
    def _paint_constellation_labels(self, painter, w, h):
        """绘制星座名称（极淡的注记）"""
        font = QFont("PingFang SC", 8)
        painter.setFont(font)

        for const_name, const_data in CONSTELLATIONS.items():
            lx, ly = const_data.get("label_pos", (0.5, 0.5))
            px, py = lx * w, ly * h
            # 呼吸效果
            alpha = int(30 + 10 * math.sin(self._t * 0.12 + hash(const_name) % 50 * 0.07))

            painter.setPen(QColor(120, 160, 210, alpha))
            painter.drawText(
                QRectF(px - 40, py - 10, 80, 20),
                Qt.AlignCenter, const_name
            )


# ═══════════════════════════════════════════════════════
#  工具函数（保持向后兼容）
# ═══════════════════════════════════════════════════════

def draw_ring(painter, cx, cy, radius, width, color, progress=1.0):
    """绘制辉光环 — 用于对接环、轨道环等"""
    segments = 120
    for i in range(segments):
        angle = (i / segments) * math.pi * 2
        if angle / (math.pi * 2) > progress:
            break
        a = i / segments * math.pi * 2
        next_a = (i + 1) / segments * math.pi * 2
        x1 = cx + math.cos(a) * radius
        y1 = cy + math.sin(a) * radius
        x2 = cx + math.cos(next_a) * radius
        y2 = cy + math.sin(next_a) * radius
        g = QLinearGradient(QPointF(x1, y1), QPointF(x2, y2))
        g.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 200))
        g.setColorAt(0.5, QColor(color.red(), color.green(), color.blue(), 80))
        g.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 200))
        painter.setPen(QPen(QBrush(g), width))
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))


def draw_glow_ellipse(painter, cx, cy, rx, ry, color, intensity=0.4):
    """绘制辉光椭圆 — 用于按钮、卡片发光"""
    for i in range(3, 0, -1):
        alpha = int(255 * intensity * (1 - i * 0.3))
        g = QRadialGradient(QPointF(cx, cy), max(rx, ry) * (1 + i * 0.5))
        g.setColorAt(0, QColor(color.red(), color.green(), color.blue(), alpha))
        g.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(g))
        painter.drawEllipse(QPointF(cx, cy), rx * (1 + i * 0.5), ry * (1 + i * 0.5))

```
