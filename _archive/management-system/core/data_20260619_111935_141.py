"""
统一数据层 — 路径管理 + 数据库初始化 + 版本迁移
从桌面版 business_service.init_business_dbs() 完整迁移，确保两版表结构一致
"""
import os, sqlite3, logging
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "log")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 当前 schema 版本号（递增）
SCHEMA_VERSION = 1

# ── DB 路径（与桌面版完全一致） ──
ORDER_DB        = os.path.join(DATA_DIR, "order.db")
PRODUCT_DB      = os.path.join(DATA_DIR, "product.db")
CUSTOMER_DB     = os.path.join(DATA_DIR, "customer.db")
FINANCE_DB      = os.path.join(DATA_DIR, "finance.db")
MEMBER_DB       = os.path.join(DATA_DIR, "member.db")
USERS_DB        = os.path.join(DATA_DIR, "users.db")
STAFF_DB        = os.path.join(DATA_DIR, "staff.db")
WALLET_DB       = os.path.join(DATA_DIR, "wallet.db")
DISTRIBUTION_DB = os.path.join(DATA_DIR, "distribution.db")
ACTIVATION_ADMIN_DB = os.path.join(DATA_DIR, "activation_admin.db")

# 迁移日志
_migration_log = os.path.join(LOG_DIR, "migration.log")

def _log_migration(msg):
    try:
        with open(_migration_log, "a", encoding="utf-8") as f:
            from datetime import datetime
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def _ensure_schema_version(conn, db_path):
    """为数据库创建 _schema_version 表并检查/写入版本号"""
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS _schema_version (
        id INTEGER PRIMARY KEY CHECK (id=1),
        version INTEGER NOT NULL,
        updated_at TEXT DEFAULT (datetime('now','localtime'))
    )''')
    row = c.execute("SELECT version FROM _schema_version WHERE id=1").fetchone()
    if row is None:
        c.execute("INSERT INTO _schema_version (id, version) VALUES (1, ?)", (SCHEMA_VERSION,))
        _log_migration(f"{db_path}: 初始化 schema v{SCHEMA_VERSION}")
    else:
        old_ver = row[0]
        if old_ver < SCHEMA_VERSION:
            c.execute("UPDATE _schema_version SET version=?, updated_at=datetime('now','localtime') WHERE id=1",
                      (SCHEMA_VERSION,))
            _log_migration(f"{db_path}: 升级 schema v{old_ver} → v{SCHEMA_VERSION}")


def init_all_dbs():
    """初始化所有业务表（含 schema 版本管理），与桌面版 business_service.init_business_dbs() 一致"""
    os.makedirs(DATA_DIR, exist_ok=True)

    # ── 1. order.db ──
    conn = sqlite3.connect(ORDER_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_no TEXT UNIQUE NOT NULL,
        customer_name TEXT,
        customer_id TEXT,
        product_name TEXT,
        quantity INTEGER DEFAULT 1,
        unit_price REAL DEFAULT 0,
        total_amount REAL DEFAULT 0,
        status TEXT DEFAULT '已完成',
        note TEXT,
        payment_method TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        updated_at TEXT
    )''')
    # 兼容已存在的 orders 表：补充缺失列
    for col, col_def in [
        ("customer_id", "TEXT"),
        ("updated_at", "TEXT"),
    ]:
        try:
            c.execute(f"ALTER TABLE orders ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass
    _ensure_schema_version(conn, ORDER_DB)
    conn.commit()
    conn.close()

    # ── 2. finance.db ──
    conn = sqlite3.connect(FINANCE_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        category TEXT,
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        description TEXT,
        order_no TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )''')
    _ensure_schema_version(conn, FINANCE_DB)
    conn.commit()
    conn.close()

    # ── 3. member.db ──
    conn = sqlite3.connect(MEMBER_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS member (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        level TEXT DEFAULT 'TRIAL',
        points INTEGER DEFAULT 0,
        rights TEXT DEFAULT '',
        vip_expire TEXT DEFAULT '',
        status TEXT DEFAULT '激活',
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )''')
    _ensure_schema_version(conn, MEMBER_DB)
    conn.commit()
    conn.close()

    # ── 4. users.db ──
    conn = sqlite3.connect(USERS_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        user_id TEXT,
        role TEXT DEFAULT 'user',
        license_type TEXT,
        created_at TEXT,
        updated_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_memberships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        membership_type TEXT,
        activated_at TEXT,
        expires_at TEXT,
        activation_code TEXT
    )''')
    # 兼容已存在的 users 表：补充缺失列
    for col, col_def in [
        ("user_id", "TEXT"),
        ("role", "TEXT DEFAULT 'user'"),
        ("updated_at", "TEXT"),
    ]:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass
    _ensure_schema_version(conn, USERS_DB)
    conn.commit()

    # 确保 admin 存在
    c.execute('SELECT id FROM users WHERE username = ?', ('admin',))
    if not c.fetchone():
        c.execute('INSERT INTO users (username, password, license_type, role) VALUES (?, ?, ?, ?)',
                  ('admin', 'admin', 'VIP', 'admin'))
        c.execute('INSERT OR IGNORE INTO user_memberships (username, membership_type, activated_at) VALUES (?, ?, ?)',
                  ('admin', 'VIP', '2024-01-01 00:00:00'))
    conn.commit()
    conn.close()

    # ── 5. product.db ──
    conn = sqlite3.connect(PRODUCT_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specs TEXT,
        category TEXT,
        unit_price REAL DEFAULT 0,
        price REAL DEFAULT 0,
        cost REAL DEFAULT 0,
        stock INTEGER DEFAULT 0,
        unit TEXT,
        status TEXT DEFAULT '上架',
        note TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sync_version INTEGER DEFAULT 0,
        last_modified_by TEXT DEFAULT 'desktop',
        last_sync_at TIMESTAMP
    )''')
    # 兼容已存在的 products 表：补充缺失列（cloud_pull 映射所需）
    for col, col_def in [
        ("specs", "TEXT"),
        ("unit_price", "REAL DEFAULT 0"),
        ("price", "REAL DEFAULT 0"),
        ("cost", "REAL DEFAULT 0"),
        ("unit", "TEXT"),
        ("note", "TEXT"),
        ("description", "TEXT"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("sync_version", "INTEGER DEFAULT 0"),
        ("last_modified_by", "TEXT DEFAULT 'desktop'"),
        ("last_sync_at", "TIMESTAMP"),
    ]:
        try:
            c.execute(f"ALTER TABLE products ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass
    c.execute('CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)')
    _ensure_schema_version(conn, PRODUCT_DB)
    conn.commit()
    conn.close()

    # ── 6. staff.db ──
    conn = sqlite3.connect(STAFF_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, phone TEXT, email TEXT,
        position TEXT, salary REAL DEFAULT 0,
        status TEXT DEFAULT '在职', note TEXT,
        department TEXT DEFAULT '', hire_date TEXT DEFAULT '',
        created_at TEXT DEFAULT '', updated_at TEXT DEFAULT '',
        sync_version INTEGER DEFAULT 0,
        last_modified_by TEXT DEFAULT 'desktop',
        last_sync_at TIMESTAMP
    )''')
    _ensure_schema_version(conn, STAFF_DB)
    conn.commit()
    conn.close()

    # ── 7. customer.db ──
    conn = sqlite3.connect(CUSTOMER_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS customer (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        name         TEXT    NOT NULL,
        company      TEXT,
        phone        TEXT,
        email        TEXT,
        address      TEXT,
        level        TEXT    DEFAULT '普通',
        note         TEXT,
        created_at   TEXT    NOT NULL,
        sync_version INTEGER DEFAULT 0,
        last_modified_by TEXT DEFAULT 'desktop',
        last_sync_at TIMESTAMP
    )''')
    # 兼容已存在的 customer 表：补充缺失列
    for col, col_def in [
        ("sync_version", "INTEGER DEFAULT 0"),
        ("last_modified_by", "TEXT DEFAULT 'desktop'"),
        ("last_sync_at", "TIMESTAMP"),
    ]:
        try:
            c.execute(f"ALTER TABLE customer ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass
    _ensure_schema_version(conn, CUSTOMER_DB)
    conn.commit()
    conn.close()

    # ── 8. wallet.db ──
    conn = sqlite3.connect(WALLET_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS wallet (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id          TEXT UNIQUE NOT NULL,
        balance          REAL DEFAULT 0,
        frozen_amount    REAL DEFAULT 0,
        total_income     REAL DEFAULT 0,
        total_withdraw   REAL DEFAULT 0,
        status           TEXT DEFAULT 'active',
        created_at       TEXT DEFAULT (datetime('now', 'localtime')),
        updated_at       TEXT DEFAULT (datetime('now', 'localtime'))
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS wallet_transactions (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        wallet_id      INTEGER NOT NULL,
        type           TEXT NOT NULL,
        amount         REAL NOT NULL,
        balance_after  REAL NOT NULL,
        description    TEXT,
        created_at     TEXT DEFAULT (datetime('now', 'localtime')),
        related_id     TEXT,
        FOREIGN KEY (wallet_id) REFERENCES wallet(id)
    )''')
    # 兼容已存在的 wallet_transactions 表
    try:
        c.execute('ALTER TABLE wallet_transactions ADD COLUMN related_id TEXT')
    except sqlite3.OperationalError:
        pass
    try:
        c.execute('CREATE INDEX IF NOT EXISTS idx_wallet_txn_type ON wallet_transactions(wallet_id, type)')
    except Exception:
        pass
    try:
        c.execute('CREATE INDEX IF NOT EXISTS idx_wallet_txn_created ON wallet_transactions(created_at DESC)')
    except Exception:
        pass
    _ensure_schema_version(conn, WALLET_DB)
    conn.commit()
    conn.close()

    # ── 9. distribution.db ──
    conn = sqlite3.connect(DISTRIBUTION_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS distribution_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        url TEXT,
        click_count INTEGER DEFAULT 0,
        register_count INTEGER DEFAULT 0,
        total_commission REAL DEFAULT 0,
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        user_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS commissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL,
        from_user_name TEXT,
        amount REAL NOT NULL,
        type TEXT DEFAULT 'direct',
        status TEXT DEFAULT 'pending',
        order_id TEXT,
        description TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        user_id INTEGER,
        from_user_id INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS team_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL,
        parent_name TEXT NOT NULL,
        level INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        user_id INTEGER,
        parent_id INTEGER,
        username TEXT,
        total_contribution REAL DEFAULT 0
    )''')
    # 兼容已存在的 distribution 表：补充 cloud_pull 映射所需的缺失列
    for tbl, cols in [
        ("distribution_links", [("user_id", "INTEGER"), ("total_commission", "REAL DEFAULT 0")]),
        ("commissions", [("user_id", "INTEGER"), ("from_user_id", "INTEGER")]),
        ("team_members", [("user_id", "INTEGER"), ("parent_id", "INTEGER"), ("username", "TEXT"), ("total_contribution", "REAL DEFAULT 0")]),
    ]:
        for col, col_def in cols:
            try:
                c.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_def}")
            except sqlite3.OperationalError:
                pass
    _ensure_schema_version(conn, DISTRIBUTION_DB)
    conn.commit()
    conn.close()

    # ── 10. activation_admin.db ──
    conn = sqlite3.connect(ACTIVATION_ADMIN_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS admin_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        user_type TEXT DEFAULT 'PRO',
        status TEXT DEFAULT 'unused',
        bound_account TEXT,
        bound_machine TEXT,
        note TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        expires_at TEXT,
        used_at TEXT
    )''')
    _ensure_schema_version(conn, ACTIVATION_ADMIN_DB)
    conn.commit()
    conn.close()
