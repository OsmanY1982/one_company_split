# -*- coding: utf-8 -*-
"""
太阳系天文馆 · SOLAR SYSTEM PLANETARIUM
300+ IAU 已命名天体 | 滚轮缩放 | 拖拽平移 | 悬停标签 | 多层级渲染
"""
import math
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QMenu, QAction, QMessageBox
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QRadialGradient, QFont,
)
import subprocess
import threading

from core.cosmic import CosmicBackground
from core.planet_painter import PLANET_STYLES, paint_planet
from modules.astronomy.solar_system.renderer import paint_nebula
from modules.astronomy.solar_system.data import (
    SOLAR_CATALOG, total_count, get_children, all_bodies,
    km_to_px, radius_to_px, PLANET_PALETTE,
)
from modules.astronomy.star_catalog.detail import _to_spoken_form

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

# ═══════════════════════════════════════════════════════
# 天体介绍知识库（内嵌，不创建独立数据文件）
# ═══════════════════════════════════════════════════════
RICH_FACTS = {
    "sun": "太阳是太阳系的中心恒星，光谱型 G2V，占太阳系总质量的 99.86%。核心温度约 1500 万摄氏度，通过氢核聚变产生能量。光球层温度约 5500°C，表面有太阳黑子、耀斑和日冕物质抛射等活动现象。太阳风以每秒数百公里的速度向外扩散，形成日球层。太阳年龄约 46 亿年，预计还有约 50 亿年的主序星寿命。",

    "mercury": "水星是离太阳最近的行星，也是太阳系最小的行星。表面布满了撞击坑，外形酷似月球。昼夜温差极大，白天可达 430°C，夜晚降至 -180°C。几乎没有大气层，只有稀薄的外逸层。水星拥有一个异常巨大的铁核，占行星半径的约 85%。一天（自转周期）约 59 个地球日，一年约 88 个地球日。已由信使号探测器详细勘测。",

    "venus": "金星是太阳系最亮的行星，常被称为启明星或长庚星。大小与地球相近，但环境极为恶劣：浓厚二氧化碳大气层造成失控温室效应，表面温度高达 465°C。大气压力是地球的 92 倍。自转方向与多数行星相反，一天比一年还长（自转周期 243 天，公转周期 225 天）。表面有大量火山和平原。",

    "earth": "地球是太阳系唯一已知存在生命的天体。拥有液态水海洋、含氧大气层和活跃的板块构造。磁场保护表面免受太阳风伤害。月球是地球唯一的天然卫星，由一次远古撞击事件形成。自转周期 24 小时，公转周期 365.25 天，自转轴倾斜 23.4 度产生了四季。",

    "mars": "火星因其红色外观被称为红色星球，表面氧化铁赋予了它独特的颜色。拥有太阳系最高的山——奥林帕斯山（高约 21.9 公里），以及巨大的水手号峡谷。两极有冰盖，地下可能存在水冰。大气层稀薄，以二氧化碳为主。目前有多辆火星车在执行探测任务。自转周期约 24.6 小时，公转周期约 687 天。",

    "jupiter": "木星是太阳系最大的行星，质量是其他所有行星总和的 2.5 倍。以氢和氦为主的巨大气态行星，著名的大红斑是一个持续数百年的巨型风暴。拥有 95 颗已命名卫星，其中四颗伽利略卫星（木卫一、木卫二、木卫三、木卫四）由伽利略在 1610 年发现。木卫二被认为冰壳下有液态海洋，是寻找地外生命的重要目标。",

    "saturn": "土星因其壮观的光环系统而闻名，由数十亿冰粒和岩石碎片组成。是太阳系第二大的气态巨行星，密度低于水。拥有 146 颗已命名卫星，其中土卫六（Titan）是太阳系唯一拥有浓厚大气层的卫星，表面有液态甲烷湖泊。光环主要由土卫一至土卫七的引力塑造。公转周期约 29.5 年。",

    "uranus": "天王星是太阳系最冷的行星之一，大气最低温度可达 -224°C。自转轴倾斜约 98 度，几乎是躺着公转，造成极端的季节变化。属冰巨行星，大气以氢、氦和甲烷为主，甲烷赋予了它蓝绿色外观。拥有 28 颗已命名卫星和暗淡的光环。由威廉·赫歇尔于 1781 年发现。",

    "neptune": "海王星是太阳系最远的行星，以强烈的风暴和狂风著称，风速可达每小时 2100 公里。大气中的甲烷使其呈现深蓝色。拥有 16 颗已命名卫星，其中海卫一（Triton）是太阳系最冷的天体之一，表面温度约 -235°C，并且绕海王星逆行公转。由数学预测而后观测发现，仅被旅行者 2 号飞掠探测。",

    "pluto": "冥王星原为第九大行星，2006 年被重新归类为矮行星。表面有广阔的氮冰平原（斯普特尼克平原）和高达数公里的冰山脉。拥有五颗已知卫星，其中冥卫一（Charon）的大小接近冥王星的一半。由新视野号探测器于 2015 年首次飞掠探测，揭示了复杂的地质活动。",

    "ceres": "谷神星是位于火星和木星之间小行星带中最大的天体，也是太阳系内唯一位于主小行星带的矮行星。表面有亮斑，被认为是盐类沉积物。黎明号探测器于 2015 年进入轨道，发现其地下可能存在液态水。直径约 940 公里。",

    "eris": "阋神星是太阳系已知质量第二大的矮行星（仅次于冥王星），也是直接导致冥王星被降级的导火索。位于离散盘，轨道极为椭圆，公转周期约 558 年。拥有一颗卫星——阋卫一（Dysnomia）。表面覆盖甲烷冰，呈白色。",

    "haumea": "妊神星是一颗外形独特的矮行星，呈椭球形，像一颗橄榄球——因其极快的自转（约 4 小时）而被拉长。位于柯伊伯带，拥有两颗卫星和一道暗淡的光环。表面覆盖水冰。以夏威夷生育女神命名。",

    "makemake": "鸟神星是柯伊伯带中一颗较亮的矮行星，以复活节岛创造神命名。表面覆盖甲烷和乙烷冰，呈淡红色。大气层可能在近日点时短暂出现。没有已知卫星。直径约 1430 公里。",

    # ── 大型卫星 ──
    "moon": "月球是地球唯一的天然卫星，距地球约 38 万公里。表面分为明亮的高地和暗色的月海（玄武岩平原）。没有大气层和液态水，但有水冰存在于两极永久阴影区。自转与公转同步，始终以同一面朝向地球。人类于 1969 年首次登月。",

    "io": "木卫一是太阳系火山活动最活跃的天体，有超过 400 座活火山。因木星强大的潮汐力持续加热内部，表面不断被喷发的硫和二氧化硫重塑。大气层极为稀薄，主要由二氧化硫组成。",

    "europa": "木卫二表面覆盖着光滑的冰壳，下方被认为存在液态咸水海洋，水量可能超过地球全部海洋的总和。是太阳系最有希望发现地外生命的地点之一。冰壳上布满了错综复杂的暗色条纹。",

    "ganymede": "木卫三是太阳系最大的卫星，比水星还大。是唯一拥有自身磁场的卫星。表面有古老的暗色坑洞区域和较年轻的明亮沟槽区域。内部可能存在分层海洋。",

    "callisto": "木卫四是太阳系表面撞击坑最密集的天体之一，古老的表面数十亿年来几乎未被改变。可能存在地下海洋。远离木星的辐射带，被认为是未来人类探索木星系统的潜在基地。",

    "titan": "土卫六是太阳系唯一拥有浓厚大气层的卫星，大气以氮为主，表面压力约为地球的 1.5 倍。表面有液态甲烷和乙烷的湖泊与河流。惠更斯号探测器于 2005 年成功着陆，拍摄了表面的河流侵蚀地貌。",

    "enceladus": "土卫二是一颗冰卫星，南极区域有巨大的水冰羽流喷入太空，表明冰壳下存在液态海洋和热液活动。羽流中含有有机分子，使其成为搜寻生命的重要目标之一。",

    "triton": "海卫一是太阳系最冷的已知天体之一，表面温度约 -235°C。以逆行轨道绕海王星运行，表明它可能是一颗被捕获的柯伊伯带天体。表面有氮冰间歇泉、冰火山和哈密瓜地形纹路。",

    "charon": "冥卫一大小约为冥王星的一半，使冥王星-冥卫一系统几乎构成双矮行星。表面有巨大的峡谷系统（Argo Chasma）和暗红色的极区（Mordor Macula），后者可能是从冥王星逃逸的甲烷分子在极区沉积形成。",

    "mimas": "土卫一以其巨大的赫歇尔撞击坑闻名，该撞击坑直径约 130 公里，几乎占卫星直径的三分之一，使其外观酷似《星球大战》中的死星。主要由水冰组成，密度极低。",

    "iapetus": "土卫八以其极端的双色表面著称：一侧明亮如雪，另一侧暗如煤灰。这种颜色差异可能源于另一颗卫星（土卫九）的暗色物质落入其前导面。还有一道环绕赤道的独特山脊。",

    "dione": "土卫四表面有起伏的悬崖、撞击坑和冰裂隙。被认为可能在地下存在液态海洋。密度高于许多土星卫星，暗示其内部有岩石成分。表面明亮的线条是冰崖。",

    "rhea": "土卫二是土星第二大卫星，主要由水冰组成，密度较低。表面布满撞击坑，较古老。研究表明它可能拥有稀薄的氧气/二氧化碳外逸层——这是首次在卫星上发现含氧大气。",

    "tethys": "土卫三表面有一个巨大的撞击盆地奥德修斯，直径约 400 公里。还有一道巨大的峡谷伊萨卡峡谷，延伸近四分之三周长。主要由水冰组成。",

    "ariel": "天卫一表面有峡谷、断层和冰火山平原。是天王星卫星中表面最年轻的一颗，有证据表明曾经历过地质活动。由水冰和岩石组成。",

    "umbriel": "天卫二是天王星卫星中表面最暗的一颗，撞击坑密布。有一个明亮的光环状地貌（荧光环），被认为是一次撞击后暴露出的地下冰层。",

    "titania": "天卫三是天王星最大的卫星，表面有巨大的峡谷和断层系统。主要由水冰和岩石组成，可能有地下液体层。由赫歇尔于 1787 年发现。",

    "oberon": "天卫四是天王星第二大卫星，也是天王星最外侧的大卫星。表面密布撞击坑，有些撞击坑底部有暗色物质。可能有古老的冰火山活动遗迹。",

    "miranda": "天卫五拥有太阳系最奇特的地形之一：表面仿佛由不同地质板块拼贴而成，有巨大的 V 形峡谷、冠状结构和悬崖。这些特征可能源于多次撞击-重组过程。",

    "phobos": "火卫一是火星两颗卫星中较大的一颗，呈不规则状。正在以极慢的速度螺旋式靠近火星，预计约 5000 万年后将解体成火星环。表面有大撞击坑 Stickney。",

    "deimos": "火卫二是火星较小的卫星，更为远离火星，表面较平滑。尺寸极小，呈不规则状。可能是一颗被捕获的小行星。",
}

# 缩放范围
ZOOM_MIN, ZOOM_MAX = 0.15, 80.0
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
            import hashlib
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
        p.drawRoundedRect(tx - pad, ty - fm.height() + 2, tw + pad * 2,
                          fm.height() + 4, 4, 4)

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

        # 看广告延长时间按钮
        # 缩放相关
        self._speed = 1.0
        self._build_zoom_controls()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Equal:
            self._speed = min(self._speed * 1.5, 100.0)
            self._show_speed_hint()
            self._sync_speed_ui()
        elif event.key() == Qt.Key_Minus:
            self._speed = max(self._speed / 1.5, 0.05)
            self._show_speed_hint()
            self._sync_speed_ui()
        else:
            super().keyPressEvent(event)

    def _show_speed_hint(self):
        from PyQt5.QtWidgets import QLabel
        from PyQt5.QtCore import QTimer
        if hasattr(self, '_speed_label') and self._speed_label:
            self._speed_label.setText(f"⏱ {self._speed:.1f}x")
        else:
            self._speed_label = QLabel(f"⏱ {self._speed:.1f}x", self)
            self._speed_label.setStyleSheet(
                "background:rgba(0,0,0,180);color:#fff;font-size:14px;padding:4px 10px;border-radius:6px;"
            )
            self._speed_label.move(12, 12)
            self._speed_label.show()
        QTimer.singleShot(1500, self._hide_speed_hint)

    def _hide_speed_hint(self):
        if hasattr(self, '_speed_label') and self._speed_label:
            self._speed_label.hide()

    def _build_zoom_controls(self):
        """构建公转速度控件：−/+ 按钮和滑动条"""
        from PyQt5.QtWidgets import QSlider

        btn_style = (
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

        self._speed_down_btn = QPushButton("−", self)
        self._speed_down_btn.setStyleSheet(btn_style)
        self._speed_down_btn.setFixedSize(28, 28)
        self._speed_down_btn.clicked.connect(self._speed_down)

        self._speed_up_btn = QPushButton("+", self)
        self._speed_up_btn.setStyleSheet(btn_style)
        self._speed_up_btn.setFixedSize(28, 28)
        self._speed_up_btn.clicked.connect(self._speed_up)

        self._speed_slider = QSlider(Qt.Horizontal, self)
        self._speed_slider.setRange(5, 10000)
        self._speed_slider.setValue(int(self._speed * 100))
        self._speed_slider.setFixedWidth(100)
        self._speed_slider.valueChanged.connect(self._on_speed_slider)

        self._speed_label = QLabel(f"{self._speed:.1f}x", self)
        self._speed_label.setStyleSheet(
            "color: #7799cc; background: transparent; font-size: 10px;"
            " font-family: 'PingFang SC';"
        )
        self._speed_label.setAlignment(Qt.AlignCenter)
        self._speed_label.setFixedWidth(40)

        self._reposition_zoom_controls()

    def _speed_up(self):
        self._speed = min(self._speed * 1.5, 100.0)
        self._sync_speed_ui()

    def _speed_down(self):
        self._speed = max(self._speed / 1.5, 0.05)
        self._sync_speed_ui()

    def _on_speed_slider(self, val):
        self._speed = val / 100.0
        self._speed_label.setText(f"{self._speed:.1f}x")

    def _sync_speed_ui(self):
        val = int(self._speed * 100)
        self._speed_slider.blockSignals(True)
        self._speed_slider.setValue(val)
        self._speed_slider.blockSignals(False)
        self._speed_label.setText(f"{self._speed:.1f}x")

    def _reposition_zoom_controls(self):
        w = self.width()
        y = self.height() - 42
        self._speed_down_btn.move(w - 200, y)
        self._speed_slider.move(w - 168, y + 4)
        self._speed_up_btn.move(w - 62, y)
        self._speed_label.move(w - 30, y + 2)

    def _open_catalog(self):
        from modules.astronomy.star_catalog.catalog import StarCatalogWindow
        self._catalog_win = StarCatalogWindow(self)
        self._catalog_win.show()
        self.hide()

    def resizeEvent(self, event):
        # ── 窗口调整 ──
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
        if hasattr(self, '_speed_down_btn'):
            self._reposition_zoom_controls()
