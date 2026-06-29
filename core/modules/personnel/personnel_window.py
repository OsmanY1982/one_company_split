"""
人员管理 → 居住环 · CREW QUARTERS
宇宙主题窗口：小星球导航 — 员工 / 会员 / 钱包 / 分销
DAO 层保留，UI 改为星球环绕导航
"""
import csv, os, json, math, sqlite3
from core.database import get_conn as _pool_get_conn, close_conn as _pool_close_conn
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import (
    QPainter, QColor, QRadialGradient, QPen, QBrush,
    QLinearGradient, QFont, QPainterPath
)
from core.cosmic import CosmicBackground
from core.planet_painter import PLANET_STYLES, paint_planet, paint_orbit, paint_energy_line
from core.ui_components import SectionTitle, Subtitle
from core.light_tool_theme import LIGHT_TOOL_STYLE

# ═══════ 天体身份 ═══════
PLANET_COLOR = QColor(255, 102, 68)
PLANET_COLOR_NAME = "#ff6644"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ═══════ 星球配置 — 使用 planet_painter 纹理 ═══════
# 窗口 900×650，中心约 (450, 325)，轨道均匀排列
PLANETS = [
    {"id": "staff",   "name": "员工",   "style": "mars",    "orbit": 110, "size": 48, "angle": -90},
    {"id": "member",  "name": "会员",   "style": "venus",   "orbit": 175, "size": 50, "angle": 0},
    {"id": "wallet",  "name": "钱包",   "style": "jupiter", "orbit": 230, "size": 52, "angle": 90},
    {"id": "dist",    "name": "分销",   "style": "saturn",  "orbit": 280, "size": 48, "angle": 180},
]


# ═══════ DAO / Service Layer ═══════
def _get_db_path(name: str) -> str:
    return os.path.join(DATA_DIR, name)

def _get_conn(db_name: str):
    conn = _pool_get_conn(db_name)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn, db_name


# ─── 员工 (staff) ───
def staff_init_db():
    conn, _dbn = _get_conn("staff.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, phone TEXT, email TEXT,
        position TEXT, salary REAL DEFAULT 0,
        status TEXT DEFAULT '在职', note TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    conn.commit(); _pool_close_conn(_dbn)

def staff_get_all(search=""):
    conn, _dbn = _get_conn("staff.db")
    if search:
        rows = conn.execute("SELECT * FROM staff WHERE name LIKE ? OR phone LIKE ? ORDER BY id DESC",
                            (f"%{search}%", f"%{search}%")).fetchall()
    else:
        rows = conn.execute("SELECT * FROM staff ORDER BY id DESC").fetchall()
    _pool_close_conn(_dbn); return rows

def staff_add(name, phone, email, position, salary, status, note):
    conn, _dbn = _get_conn("staff.db")
    c = conn.execute("INSERT INTO staff(name,phone,email,position,salary,status,note) VALUES(?,?,?,?,?,?,?)",
                     (name, phone, email, position, salary, status, note))
    conn.commit(); _pool_close_conn(_dbn); return c.lastrowid

def staff_update(sid, name, phone, email, position, salary, status, note):
    conn, _dbn = _get_conn("staff.db")
    conn.execute("UPDATE staff SET name=?,phone=?,email=?,position=?,salary=?,status=?,note=? WHERE id=?",
                 (name, phone, email, position, salary, status, note, sid))
    conn.commit(); _pool_close_conn(_dbn)

def staff_delete(sid):
    conn, _dbn = _get_conn("staff.db")
    conn.execute("DELETE FROM staff WHERE id=?", (sid,))
    conn.commit(); _pool_close_conn(_dbn)

def staff_import_csv(filepath):
    count = 0
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            staff_add(row.get('name',''), row.get('phone',''), row.get('email',''),
                      row.get('position',''), float(row.get('salary',0) or 0),
                      row.get('status','在职'), row.get('note', row.get('notes','')))
            count += 1
    return count

def staff_export_csv(filepath):
    rows = staff_get_all()
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['ID','姓名','电话','邮箱','职位','薪资','状态','备注','创建时间'])
        for r in rows:
            w.writerow([r['id'],r['name'],r['phone'],r['email'],r['position'],
                        r['salary'],r['status'],r['note'],r['created_at']])


# ─── 会员 (member) ───
def member_init_db():
    conn, _dbn = _get_conn("member.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS member (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        level TEXT DEFAULT 'TRIAL',
        points INTEGER DEFAULT 0,
        rights TEXT DEFAULT '',
        vip_expire TEXT DEFAULT '',
        status TEXT DEFAULT '激活',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    conn.commit(); _pool_close_conn(_dbn)

def member_get_all(search="", level=""):
    conn, _dbn = _get_conn("member.db")
    sql = "SELECT * FROM member WHERE 1=1"
    params = []
    if search:
        sql += " AND (name LIKE ? OR phone LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if level:
        sql += " AND level=?"
        params.append(level)
    sql += " ORDER BY id DESC"
    rows = conn.execute(sql, params).fetchall()
    _pool_close_conn(_dbn); return rows

def member_add(name, phone, email, level, points, rights, vip_expire, status):
    conn, _dbn = _get_conn("member.db")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c = conn.execute("INSERT INTO member(name,phone,email,level,points,rights,vip_expire,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                     (name, phone, email, level, points, rights, vip_expire, status, now, now))
    conn.commit(); _pool_close_conn(_dbn); return c.lastrowid

def member_update(mid, name, phone, email, level, points, rights, vip_expire, status):
    conn, _dbn = _get_conn("member.db")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("UPDATE member SET name=?,phone=?,email=?,level=?,points=?,rights=?,vip_expire=?,status=?,updated_at=? WHERE id=?",
                 (name, phone, email, level, points, rights, vip_expire, status, now, mid))
    conn.commit(); _pool_close_conn(_dbn)

def member_delete(mid):
    conn, _dbn = _get_conn("member.db")
    conn.execute("DELETE FROM member WHERE id=?", (mid,))
    conn.commit(); _pool_close_conn(_dbn)

def member_stats():
    conn, _dbn = _get_conn("member.db")
    total = conn.execute("SELECT COUNT(*) FROM member").fetchone()[0]
    levels = {}
    for r in conn.execute("SELECT level, COUNT(*) as cnt FROM member GROUP BY level").fetchall():
        levels[r['level']] = r['cnt']
    _pool_close_conn(_dbn); return {"total": total, "levels": levels}


# ─── 钱包 (wallet) ───
def wallet_init_db():
    conn, _dbn = _get_conn("wallet.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS wallet (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL, user_name TEXT,
        balance REAL DEFAULT 0, frozen REAL DEFAULT 0,
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS wallet_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        wallet_id INTEGER, user_id TEXT, amount REAL,
        trans_type TEXT, note TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS wallet_withdraw (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        wallet_id INTEGER, user_id TEXT, amount REAL,
        method TEXT, account TEXT, status TEXT DEFAULT 'pending',
        note TEXT, reviewed_by TEXT, reviewed_at TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    try: conn.execute("ALTER TABLE wallet ADD COLUMN status TEXT DEFAULT 'active'")
    except sqlite3.OperationalError: pass
    try: conn.execute("ALTER TABLE wallet_withdraw ADD COLUMN reviewed_by TEXT DEFAULT ''")
    except sqlite3.OperationalError: pass
    try: conn.execute("ALTER TABLE wallet_withdraw ADD COLUMN reviewed_at TEXT DEFAULT ''")
    except sqlite3.OperationalError: pass
    conn.commit(); _pool_close_conn(_dbn)

def wallet_get_all():
    conn, _dbn = _get_conn("wallet.db")
    rows = conn.execute("SELECT * FROM wallet ORDER BY id DESC").fetchall()
    _pool_close_conn(_dbn); return rows

def wallet_get_trans():
    conn, _dbn = _get_conn("wallet.db")
    rows = conn.execute("SELECT * FROM wallet_transactions ORDER BY id DESC LIMIT 100").fetchall()
    _pool_close_conn(_dbn); return rows

def wallet_get_withdraw(status=""):
    conn, _dbn = _get_conn("wallet.db")
    if status:
        rows = conn.execute("SELECT * FROM wallet_withdraw WHERE status=? ORDER BY id DESC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM wallet_withdraw ORDER BY id DESC").fetchall()
    _pool_close_conn(_dbn); return rows

def wallet_stats():
    conn, _dbn = _get_conn("wallet.db")
    bal = conn.execute("SELECT COALESCE(SUM(balance),0) FROM wallet").fetchone()[0]
    froz = conn.execute("SELECT COALESCE(SUM(frozen),0) FROM wallet").fetchone()[0]
    income = conn.execute("SELECT COALESCE(SUM(amount),0) FROM wallet_transactions WHERE trans_type='收入'").fetchone()[0]
    expense = conn.execute("SELECT COALESCE(SUM(amount),0) FROM wallet_transactions WHERE trans_type='支出'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM wallet_withdraw WHERE status='pending'").fetchone()[0]
    _pool_close_conn(_dbn)
    return {"balance": bal, "frozen": froz, "income": income, "expense": expense, "pending": pending}

def wallet_create(user_id, user_name=""):
    conn, _dbn = _get_conn("wallet.db")
    existing = conn.execute("SELECT id FROM wallet WHERE user_id=?", (user_id,)).fetchone()
    if existing:
        _pool_close_conn(_dbn)
        return existing['id']
    c = conn.execute("INSERT INTO wallet(user_id,user_name,balance,frozen) VALUES(?,?,0,0)",
                     (user_id, user_name))
    conn.commit(); _pool_close_conn(_dbn)
    return c.lastrowid

def wallet_get_by_user(user_id):
    conn, _dbn = _get_conn("wallet.db")
    row = conn.execute("SELECT * FROM wallet WHERE user_id=?", (user_id,)).fetchone()
    _pool_close_conn(_dbn)
    return row

def wallet_recharge(user_id, amount, note=""):
    conn, _dbn = _get_conn("wallet.db")
    w = conn.execute("SELECT id,balance FROM wallet WHERE user_id=?", (user_id,)).fetchone()
    if not w:
        _pool_close_conn(_dbn)
        return {"ok": False, "error": "钱包不存在"}
    conn.execute("UPDATE wallet SET balance=balance+? WHERE user_id=?", (amount, user_id))
    conn.execute("INSERT INTO wallet_transactions(wallet_id,user_id,amount,trans_type,note) VALUES(?,?,?,?,?)",
                 (w['id'], user_id, amount, '收入', note or '充值'))
    conn.commit()
    new_bal = conn.execute("SELECT balance FROM wallet WHERE user_id=?", (user_id,)).fetchone()['balance']
    _pool_close_conn(_dbn)
    return {"ok": True, "balance": new_bal}

def wallet_withdraw_request(user_id, amount, method="", account="", note=""):
    conn, _dbn = _get_conn("wallet.db")
    w = conn.execute("SELECT id,balance,frozen FROM wallet WHERE user_id=?", (user_id,)).fetchone()
    if not w:
        _pool_close_conn(_dbn)
        return {"ok": False, "error": "钱包不存在"}
    available = w['balance'] - w['frozen']
    if amount > available:
        _pool_close_conn(_dbn)
        return {"ok": False, "error": f"余额不足，可用余额: {available:.2f}"}
    conn.execute("UPDATE wallet SET frozen=frozen+? WHERE user_id=?", (amount, user_id))
    conn.execute("INSERT INTO wallet_withdraw(wallet_id,user_id,amount,method,account,status,note) VALUES(?,?,?,?,?,?,?)",
                 (w['id'], user_id, amount, method, account, 'pending', note or ''))
    conn.commit(); _pool_close_conn(_dbn)
    return {"ok": True, "message": "提现申请已提交"}

def wallet_transfer(from_user, to_user, amount, note=""):
    conn, _dbn = _get_conn("wallet.db")
    fw = conn.execute("SELECT id,balance,frozen,status FROM wallet WHERE user_id=?", (from_user,)).fetchone()
    if not fw:
        _pool_close_conn(_dbn)
        return {"ok": False, "error": "转出钱包不存在"}
    if fw['status'] != 'active':
        _pool_close_conn(_dbn)
        return {"ok": False, "error": "转出钱包已被封禁"}
    available = fw['balance'] - fw['frozen']
    if amount > available:
        _pool_close_conn(_dbn)
        return {"ok": False, "error": f"余额不足，可用余额: {available:.2f}"}
    tw = conn.execute("SELECT id FROM wallet WHERE user_id=?", (to_user,)).fetchone()
    if not tw:
        _pool_close_conn(_dbn)
        return {"ok": False, "error": "目标钱包不存在"}
    conn.execute("UPDATE wallet SET balance=balance-? WHERE user_id=?", (amount, from_user))
    conn.execute("UPDATE wallet SET balance=balance+? WHERE user_id=?", (amount, to_user))
    conn.execute("INSERT INTO wallet_transactions(wallet_id,user_id,amount,trans_type,note) VALUES(?,?,?,?,?)",
                 (fw['id'], from_user, -amount, '支出', note or f'转账至{to_user}'))
    conn.execute("INSERT INTO wallet_transactions(wallet_id,user_id,amount,trans_type,note) VALUES(?,?,?,?,?)",
                 (tw['id'], to_user, amount, '收入', note or f'来自{from_user}转账'))
    conn.commit()
    from_bal = conn.execute("SELECT balance FROM wallet WHERE user_id=?", (from_user,)).fetchone()['balance']
    _pool_close_conn(_dbn)
    return {"ok": True, "from_balance": from_bal}

def wallet_commission(user_id, amount, note=""):
    conn, _dbn = _get_conn("wallet.db")
    w = conn.execute("SELECT id,balance FROM wallet WHERE user_id=?", (user_id,)).fetchone()
    if not w:
        _pool_close_conn(_dbn)
        return {"ok": False, "error": "钱包不存在"}
    conn.execute("UPDATE wallet SET balance=balance+? WHERE user_id=?", (amount, user_id))
    conn.execute("INSERT INTO wallet_transactions(wallet_id,user_id,amount,trans_type,note) VALUES(?,?,?,?,?)",
                 (w['id'], user_id, amount, '收入', note or '佣金'))
    conn.commit()
    new_bal = conn.execute("SELECT balance FROM wallet WHERE user_id=?", (user_id,)).fetchone()['balance']
    _pool_close_conn(_dbn)
    return {"ok": True, "balance": new_bal}

def wallet_approve_withdraw(withdraw_id, operator="", note=""):
    conn, _dbn = _get_conn("wallet.db")
    wd = conn.execute("SELECT * FROM wallet_withdraw WHERE id=?", (withdraw_id,)).fetchone()
    if not wd:
        _pool_close_conn(_dbn)
        return {"ok": False, "error": "记录不存在"}
    if wd['status'] != 'pending':
        _pool_close_conn(_dbn)
        return {"ok": False, "error": "记录已处理"}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    merged = (wd['note'] or '')
    if note:
        merged = f"{merged} | 审批通过({note})" if merged else f"审批通过({note})"
    conn.execute("UPDATE wallet_withdraw SET status='approved',note=?,reviewed_by=?,reviewed_at=? WHERE id=?",
                 (merged, operator, now, withdraw_id))
    conn.execute("UPDATE wallet SET balance=balance-?,frozen=frozen-? WHERE user_id=?",
                 (wd['amount'], wd['amount'], wd['user_id']))
    conn.execute("INSERT INTO wallet_transactions(wallet_id,user_id,amount,trans_type,note) VALUES(?,?,?,?,?)",
                 (wd['wallet_id'], wd['user_id'], -wd['amount'], '支出', f'提现审批通过 #{withdraw_id}'))
    conn.commit(); _pool_close_conn(_dbn)
    return {"ok": True, "amount": wd['amount']}

def wallet_reject_withdraw(withdraw_id, operator="", note=""):
    conn, _dbn = _get_conn("wallet.db")
    wd = conn.execute("SELECT * FROM wallet_withdraw WHERE id=?", (withdraw_id,)).fetchone()
    if not wd:
        _pool_close_conn(_dbn)
        return {"ok": False, "error": "记录不存在"}
    if wd['status'] != 'pending':
        _pool_close_conn(_dbn)
        return {"ok": False, "error": "记录已处理"}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    merged = (wd['note'] or '')
    if note:
        merged = f"{merged} | 驳回({note})" if merged else f"驳回({note})"
    conn.execute("UPDATE wallet_withdraw SET status='rejected',note=?,reviewed_by=?,reviewed_at=? WHERE id=?",
                 (merged, operator, now, withdraw_id))
    conn.execute("UPDATE wallet SET frozen=frozen-? WHERE user_id=?", (wd['amount'], wd['user_id']))
    conn.commit(); _pool_close_conn(_dbn)
    return {"ok": True, "amount": wd['amount']}

def wallet_cancel_withdraw(withdraw_id):
    conn, _dbn = _get_conn("wallet.db")
    wd = conn.execute("SELECT * FROM wallet_withdraw WHERE id=?", (withdraw_id,)).fetchone()
    if not wd:
        _pool_close_conn(_dbn)
        return {"ok": False, "error": "记录不存在"}
    if wd['status'] != 'pending':
        _pool_close_conn(_dbn)
        return {"ok": False, "error": "只能取消待审批记录"}
    conn.execute("UPDATE wallet_withdraw SET status='cancelled' WHERE id=?", (withdraw_id,))
    conn.execute("UPDATE wallet SET frozen=frozen-? WHERE user_id=?", (wd['amount'], wd['user_id']))
    conn.commit(); _pool_close_conn(_dbn)
    return {"ok": True, "amount": wd['amount']}

def wallet_update_status(user_id, status):
    conn, _dbn = _get_conn("wallet.db")
    conn.execute("UPDATE wallet SET status=? WHERE user_id=?", (status, user_id))
    conn.commit(); _pool_close_conn(_dbn)
    return {"ok": True}

def wallet_delete_wallet(wallet_id):
    conn, _dbn = _get_conn("wallet.db")
    conn.execute("DELETE FROM wallet_transactions WHERE wallet_id=?", (wallet_id,))
    conn.execute("DELETE FROM wallet_withdraw WHERE wallet_id=?", (wallet_id,))
    conn.execute("DELETE FROM wallet WHERE id=?", (wallet_id,))
    conn.commit(); _pool_close_conn(_dbn)
    return {"ok": True}

def wallet_get_transactions(wallet_id=None, trans_type="", start_date="", end_date="",
                            min_amount=None, max_amount=None, keyword="", limit=500):
    conn, _dbn = _get_conn("wallet.db")
    sql = "SELECT * FROM wallet_transactions WHERE 1=1"
    params = []
    if wallet_id:
        sql += " AND wallet_id=?"
        params.append(wallet_id)
    if trans_type:
        sql += " AND trans_type=?"
        params.append(trans_type)
    if start_date:
        sql += " AND created_at >= ?"
        params.append(start_date)
    if end_date:
        sql += " AND created_at <= ?"
        params.append(end_date + " 23:59:59")
    if min_amount is not None:
        sql += " AND ABS(amount) >= ?"
        params.append(min_amount)
    if max_amount is not None:
        sql += " AND ABS(amount) <= ?"
        params.append(max_amount)
    if keyword:
        sql += " AND note LIKE ?"
        params.append(f"%{keyword}%")
    sql += f" ORDER BY id DESC LIMIT {min(limit, 1000)}"
    rows = conn.execute(sql, params).fetchall()
    _pool_close_conn(_dbn)
    return rows

def wallet_get_balance_trend(days=7):
    conn, _dbn = _get_conn("wallet.db")
    from datetime import timedelta
    end = datetime.now()
    result = []
    for i in range(days - 1, -1, -1):
        day = end - timedelta(days=i)
        date_str = day.strftime("%Y-%m-%d")
        next_str = (day + timedelta(days=1)).strftime("%Y-%m-%d")
        bal = conn.execute(
            "SELECT COALESCE(SUM(balance),0) FROM wallet WHERE created_at <= ?",
            (next_str,)
        ).fetchone()[0]
        income = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM wallet_transactions WHERE trans_type='收入' AND created_at >= ? AND created_at < ?",
            (date_str, next_str)
        ).fetchone()[0]
        expense = conn.execute(
            "SELECT COALESCE(SUM(ABS(amount)),0) FROM wallet_transactions WHERE trans_type='支出' AND created_at >= ? AND created_at < ?",
            (date_str, next_str)
        ).fetchone()[0]
        result.append({"date": date_str, "balance": bal, "income": income, "expense": expense})
    _pool_close_conn(_dbn)
    return result


# ─── 分销 (distribution) ───
def dist_init_db():
    conn, _dbn = _get_conn("distribution.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS distribution_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, code TEXT UNIQUE, url TEXT,
        clicks INTEGER DEFAULT 0, registrations INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active', created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS commissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, source_user TEXT, amount REAL,
        comm_type TEXT, status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS team_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        leader_id TEXT, member_id TEXT, member_name TEXT,
        joined_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    conn.commit(); _pool_close_conn(_dbn)

def dist_get_links(search=""):
    conn, _dbn = _get_conn("distribution.db")
    if search:
        rows = conn.execute("SELECT * FROM distribution_links WHERE user_id LIKE ? ORDER BY id DESC",
                            (f"%{search}%",)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM distribution_links ORDER BY id DESC").fetchall()
    _pool_close_conn(_dbn); return rows

def dist_get_commissions(user="", date_from="", date_to="", status=""):
    conn, _dbn = _get_conn("distribution.db")
    sql = "SELECT * FROM commissions WHERE 1=1"
    params = []
    if user: sql += " AND user_id LIKE ?"; params.append(f"%{user}%")
    if date_from: sql += " AND created_at >= ?"; params.append(date_from)
    if date_to: sql += " AND created_at <= ?"; params.append(date_to + " 23:59:59")
    if status: sql += " AND status=?"; params.append(status)
    sql += " ORDER BY id DESC"
    rows = conn.execute(sql, params).fetchall()
    _pool_close_conn(_dbn); return rows

def dist_get_team(search=""):
    conn, _dbn = _get_conn("distribution.db")
    if search:
        rows = conn.execute("SELECT * FROM team_members WHERE leader_id LIKE ? OR member_id LIKE ? ORDER BY id DESC",
                            (f"%{search}%", f"%{search}%")).fetchall()
    else:
        rows = conn.execute("SELECT * FROM team_members ORDER BY id DESC").fetchall()
    _pool_close_conn(_dbn); return rows


# 初始化所有 DB
for init in [staff_init_db, member_init_db, wallet_init_db, dist_init_db]:
    try: init()
    except Exception as e:
        import traceback; traceback.print_exc()


# ═══════════════ 星球导航 HUD 层 ═══════════════
class PlanetHUD(QWidget):
    """绘制核心光球 + 4颗真实纹理环绕星球"""

    def __init__(self, parent=None, callback=None):
        super().__init__(parent)
        self._callback = callback
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._hover_planet = None
        self._animation_phase = 0.0

        # 开启动画
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(50)

    def _animate(self):
        self._animation_phase += 0.02
        self.update()

    def _planet_positions(self, cx, cy):
        """返回每颗星球的画面坐标"""
        positions = []
        for p in PLANETS:
            angle_rad = math.radians(p["angle"] + self._animation_phase * 8)
            px = cx + p["orbit"] * math.cos(angle_rad)
            py = cy + p["orbit"] * math.sin(angle_rad)
            positions.append((px, py, p))
        return positions

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        center = QPointF(cx, cy)

        # ── 轨道线（使用 planet_painter） ──
        for p in PLANETS:
            paint_orbit(painter, center, p["orbit"])

        # ── 星球（使用 planet_painter 纹理） ──
        positions = self._planet_positions(cx, cy)

        for px, py, pdata in positions:
            is_hover = (self._hover_planet == pdata["id"])
            style = PLANET_STYLES.get(pdata["style"], PLANET_STYLES["mars"])
            paint_planet(painter, QPointF(px, py), pdata["size"], style,
                         hovered=is_hover, label=pdata["name"], font_size=10)

        painter.end()

    def _planet_at(self, mx, my):
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        positions = self._planet_positions(cx, cy)

        for px, py, pdata in positions:
            hit_r = pdata["size"] + 14
            dist = math.hypot(mx - px, my - py)
            if dist <= hit_r:
                return pdata["id"]
        return None

    def mouseMoveEvent(self, event):
        pid = self._planet_at(event.x(), event.y())
        if pid != self._hover_planet:
            self._hover_planet = pid
            self.setCursor(Qt.PointingHandCursor if pid else Qt.ArrowCursor)
            self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        pid = self._planet_at(event.x(), event.y())
        if pid and self._callback:
            self._callback(pid)


# ═══════════════ 主窗口 ═══════════════
class PersonnelWindow(QMainWindow):
    """居住环 · CREW QUARTERS — 星球导航"""

    def __init__(self, parent=None, role="admin"):
        super().__init__(parent)
        self._role = role
        self.setWindowTitle("一人公司 — 居住环 · CREW QUARTERS")
        self.setMinimumSize(900, 650)
        self.setStyleSheet(LIGHT_TOOL_STYLE)
        self._build_ui()

    def _build_ui(self):
        # 星空背景
        bg = CosmicBackground()
        self.setCentralWidget(bg)

        # 主布局
        main = QVBoxLayout(bg)
        main.setSpacing(0)
        main.setContentsMargins(24, 16, 24, 16)

        # ── 天体 Header ──
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet("background: transparent;")
        hl = QVBoxLayout(header)
        hl.setSpacing(4)
        hl.setContentsMargins(0, 0, 0, 0)

        title = SectionTitle("居住环", parent=header)
        title.setStyleSheet("font-size: 24px; font-weight: 800; letter-spacing: 8px;")
        hl.addWidget(title, alignment=Qt.AlignCenter)

        subtitle = Subtitle("CREW QUARTERS · 点击星球进入对应模块", parent=header)
        subtitle.setStyleSheet("font-size: 11px; letter-spacing: 3px;")
        hl.addWidget(subtitle, alignment=Qt.AlignCenter)

        # 辉光线
        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent, stop:0.3 rgba(255,100,60,50),
                stop:0.5 rgba(255,140,80,120),
                stop:0.7 rgba(255,100,60,50), stop:1 transparent);
            border: none;
        """)
        hl.addWidget(line)
        main.addWidget(header)

        # ── 星球导航 HUD ──（父控件 self，避免 CosmicBackground WA_TransparentForMouseEvents 穿透）
        self._planet_hud = PlanetHUD(self, callback=self._on_planet_click)
        self._planet_hud.setGeometry(0, 0, self.width(), self.height())
        self._planet_hud.raise_()

        # 底部提示
        hint = QLabel("点击星球进入模块 · 员工 / 会员 / 钱包 / 分销")
        hint.setStyleSheet(
            "color: #554433; font-size: 10px; letter-spacing: 2px; "
            "background: transparent; padding: 6px 0;"
        )
        main.addWidget(hint, alignment=Qt.AlignCenter)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_planet_hud'):
            self._planet_hud.setGeometry(0, 0, self.width(), self.height())

    def _on_planet_click(self, planet_id):
        if planet_id == "staff":
            from core.modules.personnel.staff_window import StaffWindow
            StaffWindow(self).exec_()
        elif planet_id == "member":
            from core.modules.personnel.member_window import MemberWindow
            MemberWindow(self).exec_()
        elif planet_id == "wallet":
            from core.modules.personnel.wallet_window import WalletWindow
            self._wallet_win = WalletWindow(self)
            self._wallet_win.show()
        elif planet_id == "dist":
            from core.modules.personnel.distribution_window import DistributionWindow
            self._distribution_win = DistributionWindow(self)
            self._distribution_win.show()