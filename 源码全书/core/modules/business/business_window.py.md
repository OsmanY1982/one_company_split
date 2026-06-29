# `core/modules/business/business_window.py`

> 路径：`core/modules/business/business_window.py` | 行数：446


---


```python
"""
业务管理模块 — 小星球导航模式
订单 / 产品 / 客户 / 财务 四大板块，以环绕星球的宇宙导航呈现
"""
import os
from core.database import get_conn as _pool_get_conn, close_conn as _pool_close_conn
import math
import random
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QHeaderView, QMessageBox, QDialog, QFormLayout, QLineEdit,
    QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QPropertyAnimation, pyqtProperty, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QFont, QPainterPath, QConicalGradient
)

from core.cosmic import CosmicBackground, ACCENT_CYAN, draw_ring, draw_glow_ellipse
from core.planet_painter import PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line
from core.ui_components import SectionTitle, Subtitle
from core.light_tool_theme import LIGHT_TOOL_STYLE
from core.data import init_all_dbs, ORDER_DB, PRODUCT_DB, CUSTOMER_DB, FINANCE_DB

ACCENT_BLUE = QColor(68, 136, 255)
ACCENT_GREEN = QColor(0, 204, 170)

# ── 宇宙样式常量 ──
DIALOG_BG = """
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #080e1a, stop:1 #101a2e);
        border: 1px solid rgba(68,136,255,40);
        border-radius: 12px;
    }
"""
TABLE_STYLE = """
    QTableWidget {
        background: rgba(8,14,26,220);
        color: #ccddef;
        border: 1px solid rgba(50,100,170,35);
        border-radius: 8px;
        gridline-color: rgba(40,80,140,30);
        selection-background-color: rgba(68,136,255,60);
    }
    QTableWidget::item {
        padding: 4px 8px;
    }
    QHeaderView::section {
        background: rgba(20,40,80,180);
        color: #88aadd;
        border: 1px solid rgba(50,100,170,30);
        padding: 6px;
        font-weight: bold;
    }
"""
BTN_PRIMARY = """
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(68,136,255,200), stop:1 rgba(100,160,255,200));
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 20px;
        font-weight: bold;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(80,150,255,230), stop:1 rgba(120,180,255,230));
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(40,100,220,220), stop:1 rgba(60,120,240,220));
    }
"""


# ═══════════════════════════════════════════════════════
#  DAO 函数 — 订单 / 产品 / 客户 / 财务
# ═══════════════════════════════════════════════════════

def _get_conn(db_path):
    db_name = os.path.basename(db_path)
    conn = _pool_get_conn(db_name)
    return conn, db_name


# ── 订单 DAO ──
def order_create(customer_name, product_name, quantity, unit_price, total_amount,
                 status="已完成", note="", payment_method=""):
    conn, db_name = _get_conn(ORDER_DB)
    c = conn.cursor()
    order_no = "OR" + datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(100, 999))
    c.execute("""INSERT INTO orders (order_no, customer_name, product_name, quantity,
        unit_price, total_amount, status, note, payment_method)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (order_no, customer_name, product_name, quantity, unit_price, total_amount,
         status, note, payment_method))
    conn.commit()
    row_id = c.lastrowid
    _pool_close_conn(db_name)
    return order_no, row_id


def order_update(oid, customer_name, product_name, quantity, unit_price, total_amount,
                 status, note):
    conn, db_name = _get_conn(ORDER_DB)
    c = conn.cursor()
    c.execute("""UPDATE orders SET customer_name=?, product_name=?, quantity=?,
        unit_price=?, total_amount=?, status=?, note=? WHERE id=?""",
        (customer_name, product_name, quantity, unit_price, total_amount, status, note, oid))
    conn.commit()
    _pool_close_conn(db_name)


def order_delete(oid):
    conn, db_name = _get_conn(ORDER_DB)
    c = conn.cursor()
    c.execute("DELETE FROM orders WHERE id=?", (oid,))
    conn.commit()
    _pool_close_conn(db_name)


def order_list(search=""):
    conn, db_name = _get_conn(ORDER_DB)
    c = conn.cursor()
    if search:
        c.execute("""SELECT * FROM orders WHERE customer_name LIKE ? OR product_name LIKE ?
            OR order_no LIKE ? ORDER BY created_at DESC""",
            (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        c.execute("SELECT * FROM orders ORDER BY created_at DESC")
    rows = c.fetchall()
    _pool_close_conn(db_name)
    return rows


# ── 产品 DAO ──
def product_create(name, category, price, cost, stock, description="", unit="个"):
    conn, db_name = _get_conn(PRODUCT_DB)
    c = conn.cursor()
    c.execute("""INSERT INTO product (name, category, price, cost, stock, unit, description)
        VALUES (?,?,?,?,?,?,?)""",
        (name, category, price, cost, stock, unit, description))
    conn.commit()
    _pool_close_conn(db_name)


def product_update(pid, name, category, price, cost, stock, description):
    conn, db_name = _get_conn(PRODUCT_DB)
    c = conn.cursor()
    c.execute("""UPDATE product SET name=?, category=?, price=?, cost=?, stock=?,
        description=? WHERE id=?""",
        (name, category, price, cost, stock, description, pid))
    conn.commit()
    _pool_close_conn(db_name)


def product_delete(pid):
    conn, db_name = _get_conn(PRODUCT_DB)
    c = conn.cursor()
    c.execute("DELETE FROM product WHERE id=?", (pid,))
    conn.commit()
    _pool_close_conn(db_name)


def product_list(search=""):
    conn, db_name = _get_conn(PRODUCT_DB)
    c = conn.cursor()
    if search:
        c.execute("""SELECT * FROM product WHERE name LIKE ? OR category LIKE ?
            ORDER BY id DESC""", (f"%{search}%", f"%{search}%"))
    else:
        c.execute("SELECT * FROM product ORDER BY id DESC")
    rows = c.fetchall()
    _pool_close_conn(db_name)
    return rows


# ── 客户 DAO ──
def customer_create(name, company="", phone="", email="", address="", level="普通", note=""):
    conn, db_name = _get_conn(CUSTOMER_DB)
    c = conn.cursor()
    c.execute("""INSERT INTO customer (name, company, phone, email, address, level, note)
        VALUES (?,?,?,?,?,?,?)""", (name, company, phone, email, address, level, note))
    conn.commit()
    _pool_close_conn(db_name)


def customer_update(cid, name, company, phone, email, address, level, note):
    conn, db_name = _get_conn(CUSTOMER_DB)
    c = conn.cursor()
    c.execute("""UPDATE customer SET name=?, company=?, phone=?, email=?, address=?,
        level=?, note=? WHERE id=?""",
        (name, company, phone, email, address, level, note, cid))
    conn.commit()
    _pool_close_conn(db_name)


def customer_delete(cid):
    conn, db_name = _get_conn(CUSTOMER_DB)
    c = conn.cursor()
    c.execute("DELETE FROM customer WHERE id=?", (cid,))
    conn.commit()
    _pool_close_conn(db_name)


def customer_list(search=""):
    conn, db_name = _get_conn(CUSTOMER_DB)
    c = conn.cursor()
    if search:
        c.execute("""SELECT * FROM customer WHERE name LIKE ? OR company LIKE ?
            OR phone LIKE ? ORDER BY id DESC""",
            (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        c.execute("SELECT * FROM customer ORDER BY id DESC")
    rows = c.fetchall()
    _pool_close_conn(db_name)
    return rows


# ── 财务 DAO ──
def finance_add(ftype, amount, date, description="", order_no="", category=""):
    conn, db_name = _get_conn(FINANCE_DB)
    c = conn.cursor()
    c.execute("""INSERT INTO finance (type, amount, date, description, order_no, category)
        VALUES (?,?,?,?,?,?)""", (ftype, amount, date, description, order_no, category))
    conn.commit()
    _pool_close_conn(db_name)


def finance_list(search="", start_date="", end_date=""):
    conn, db_name = _get_conn(FINANCE_DB)
    c = conn.cursor()
    sql = "SELECT * FROM finance WHERE 1=1"
    params = []
    if search:
        sql += " AND (description LIKE ? OR order_no LIKE ? OR category LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if start_date:
        sql += " AND date >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND date <= ?"
        params.append(end_date)
    sql += " ORDER BY date DESC"
    c.execute(sql, params)
    rows = c.fetchall()
    _pool_close_conn(db_name)
    return rows


# ═══════════════════════════════════════════════════════
#  小星球导航 HUD 层 — 使用 planet_painter 真实纹理
# ═══════════════════════════════════════════════════════

# 窗口 900×680，中心约 (450, 340)，轨道 105~350 均匀排列
PLANET_DATA = {
    "order":        {"label": "订单",    "style": "sun",     "orbit": 105, "size": 48, "speed": 1.2},
    "product":      {"label": "产品",    "style": "earth",   "orbit": 148, "size": 50, "speed": 1.05},
    "customer":     {"label": "客户",    "style": "mars",    "orbit": 191, "size": 52, "speed": 0.9},
    "finance":      {"label": "财务",    "style": "neptune", "orbit": 234, "size": 54, "speed": 0.78},
    "distribution": {"label": "分销",    "style": "venus",   "orbit": 277, "size": 50, "speed": 0.66},
    "staff":        {"label": "员工",    "style": "pluto",   "orbit": 310, "size": 48, "speed": 0.56},
    "member":       {"label": "会员",    "style": "uranus",  "orbit": 336, "size": 50, "speed": 0.48},
    "wallet":       {"label": "钱包",    "style": "jupiter", "orbit": 356, "size": 52, "speed": 0.40},
}

class PlanetNavHUD(QWidget):
    """HUD 层 — 轨道环 + 8颗真实纹理星球，带公转动画"""

    planetClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._planet_angles = {key: 0.0 for key in PLANET_DATA}
        self._hovered = None
        self._planet_positions = {}  # key -> (px, py)

        self.setMouseTracking(True)

        self._anim = QTimer(self)
        self._anim.timeout.connect(self._tick)
        self._anim.start(40)

    def _tick(self):
        for key, data in PLANET_DATA.items():
            self._planet_angles[key] += 0.008 * data["speed"]
        self.update()

    def _planet_angle(self, planet_key):
        """每个星球按其固定轨道起始角 + 独立公转角度"""
        base_orbit = PLANET_DATA[planet_key]["orbit"]
        return math.radians(base_orbit) + self._planet_angles[planet_key]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        center = QPointF(cx, cy)

        # ── 轨道线（使用 planet_painter 轨道） ──
        for key, data in PLANET_DATA.items():
            paint_orbit(painter, center, data["orbit"])

        # ── 能量连接线 ──
        for key, data in PLANET_DATA.items():
            angle = self._planet_angle(key)
            px = cx + math.cos(angle) * data["orbit"]
            py = cy + math.sin(angle) * data["orbit"]
            paint_energy_line(painter, center, QPointF(px, py))

        # ── 星球（使用 planet_painter） ──
        self._planet_positions.clear()
        for key, data in PLANET_DATA.items():
            angle = self._planet_angle(key)
            px = cx + math.cos(angle) * data["orbit"]
            py = cy + math.sin(angle) * data["orbit"]
            self._planet_positions[key] = (px, py)

            style = PLANET_STYLES.get(data["style"], PLANET_STYLES["neptune"])
            is_hovered = (self._hovered == key)
            paint_planet(painter, QPointF(px, py), data["size"], style,
                         hovered=is_hovered, label=data["label"], font_size=10)

        painter.end()

    def mouseMoveEvent(self, event):
        mx, my = event.x(), event.y()
        old_hover = self._hovered
        self._hovered = None
        for key, (px, py) in self._planet_positions.items():
            hit_r = PLANET_DATA[key]["size"] + 12
            dist = math.hypot(mx - px, my - py)
            if dist <= hit_r:
                self._hovered = key
                break
        if old_hover != self._hovered:
            self.update()
            if self._hovered:
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if self._hovered:
            self.planetClicked.emit(self._hovered)
            self._hovered = None
            self.update()


# ═══════════════════════════════════════════════════════
#  BusinessWindow
# ═══════════════════════════════════════════════════════

class BusinessWindow(QMainWindow):
    """业务管理 — 小星球导航模式"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("业务管理 · BUSINESS HUB")
        self.resize(900, 680)
        self.setMinimumSize(900, 680)

        init_all_dbs()

        self.setStyleSheet(LIGHT_TOOL_STYLE)
        # 深空背景直接作为 central widget
        bg = CosmicBackground()
        self.setCentralWidget(bg)

        # HUD 层 — QMainWindow 直接子控件
        self._hud = PlanetNavHUD(self)
        self._hud.setGeometry(0, 0, self.width(), self.height())
        self._hud.planetClicked.connect(self._on_planet_clicked)
        self._hud.raise_()

        # 顶部标题
        title_label = SectionTitle("业务管理中心", self)
        title_label.setStyleSheet("color: #b0c4de; font-size: 20px; font-weight: bold; background: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setGeometry(0, 18, self.width(), 36)

        subtitle = Subtitle("点击环绕星球进入对应模块", self)
        subtitle.setStyleSheet("color: #5a7d9a; font-size: 12px; background: transparent;")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setGeometry(0, 52, self.width(), 24)

        # 版本号
        version = QLabel("v2.0 · ORBIT MODE", self)
        version.setStyleSheet("color: rgba(74,109,140,120); font-size: 10px; background: transparent;")
        version.setAlignment(Qt.AlignRight)
        version.setGeometry(self.width() - 180, self.height() - 30, 170, 20)

        # 子窗口引用
        self._order_win = None
        self._product_win = None
        self._customer_win = None
        self._finance_win = None
        self._distribution_win = None

    def _on_planet_clicked(self, key):
        if key == "order":
            from core.modules.business.order_window import OrderWindow
            self._order_win = OrderWindow(self)
            self._order_win.show()
        elif key == "product":
            from core.modules.business.product_window import ProductWindow
            self._product_win = ProductWindow(self)
            self._product_win.show()
        elif key == "customer":
            from core.modules.business.customer_window import CustomerWindow
            self._customer_win = CustomerWindow(self)
            self._customer_win.show()
        elif key == "finance":
            from core.modules.business.finance_window import FinanceWindow
            self._finance_win = FinanceWindow(self)
            self._finance_win.show()
        elif key == "distribution":
            from core.modules.personnel.distribution_window import DistributionWindow
            self._distribution_win = DistributionWindow(self)
            self._distribution_win.show()
        elif key == "staff":
            from core.modules.personnel.staff_window import StaffWindow
            self._staff_win = StaffWindow(self)
            self._staff_win.show()
        elif key == "member":
            from core.modules.personnel.member_window import MemberWindow
            self._member_win = MemberWindow(self)
            self._member_win.show()
        elif key == "wallet":
            from core.modules.personnel.wallet_window import WalletWindow
            self._wallet_win = WalletWindow(self)
            self._wallet_win.show()


    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        if hasattr(self, '_hud'):
            self._hud.setGeometry(0, 0, w, h)
```
