"""
统一数据层 — 路径管理 + 数据库初始化 + 版本迁移
对齐桌面版 core/business_service.py init_business_dbs()
"""
import os, sqlite3, logging
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "log")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 当前 schema 版本号（递增）
SCHEMA_VERSION = 2

# DB 路径 — 覆盖全部 9 个业务数据库
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


def _migrate_distribution_db_v2():
    """v1→v2: 将 distribution.db 中 NOT NULL 约束改为 DEFAULT ''，兼容 cloud_pull"""
    if not os.path.exists(DISTRIBUTION_DB):
        return
    conn = sqlite3.connect(DISTRIBUTION_DB)
    c = conn.cursor()
    try:
        row = c.execute("SELECT version FROM _schema_version WHERE id=1").fetchone()
        if row and row[0] >= 2:
            _log_migration(f"{DISTRIBUTION_DB}: 已是 v{row[0]}，跳过迁移")
            conn.close()
            return
    except sqlite3.OperationalError:
        pass  # no _schema_version table yet
    
    _log_migration(f"{DISTRIBUTION_DB}: 开始 v1→v2 迁移（修复 NOT NULL 约束）")
    
    migrations = [
        ("distribution_links", "user_name", "TEXT NOT NULL", "TEXT DEFAULT ''"),
        ("commissions",      "user_name", "TEXT NOT NULL", "TEXT DEFAULT ''"),
        ("team_members",     "user_name", "TEXT NOT NULL", "TEXT DEFAULT ''"),
        ("team_members",     "parent_name", "TEXT NOT NULL", "TEXT DEFAULT ''"),
    ]
    
    for table, col, old_def, new_def in migrations:
        try:
            # 查实际建表语句
            ddl = c.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'").fetchone()
            if ddl and old_def in ddl[0]:
                # 获取除该列外的所有列定义
                info = c.execute(f"PRAGMA table_info({table})").fetchall()
                col_names = [r[1] for r in info]
                if col not in col_names:
                    continue
                # 重建表
                new_sql = ddl[0].replace(old_def, new_def)
                c.execute("BEGIN TRANSACTION")
                c.execute(f"ALTER TABLE {table} RENAME TO {table}_old")
                c.execute(new_sql)
                cols = ", ".join(col_names)
                try:
                    c.execute(f"INSERT INTO {table} ({cols}) SELECT {cols} FROM {table}_old")
                except sqlite3.Error as e:
                    _log_migration(f"{table}: 数据迁移失败 {e}，保留旧表")
                    c.execute("ROLLBACK")
                    continue
                c.execute(f"DROP TABLE {table}_old")
                c.execute("COMMIT")
                _log_migration(f"{table}.{col}: NOT NULL → DEFAULT '' 成功")
        except Exception as e:
            _log_migration(f"{table}.{col}: 迁移异常 {e}")
            try:
                c.execute("ROLLBACK")
            except Exception:
                pass
    
    # 检查并添加 related_id 到 wallet_transactions
    try:
        info = c.execute("PRAGMA table_info(wallet_transactions)").fetchall()
        col_names = [r[1] for r in info]
        if "related_id" not in col_names:
            c.execute("ALTER TABLE wallet_transactions ADD COLUMN related_id TEXT DEFAULT ''")
            _log_migration("wallet_transactions: 添加 related_id 列")
    except sqlite3.OperationalError:
        pass
    
    # 更新版本号
    c.execute("INSERT OR REPLACE INTO _schema_version (id, version) VALUES (1, 2)")
    conn.commit()
    conn.close()
    _log_migration(f"{DISTRIBUTION_DB}: v1→v2 迁移完成")


def _migrate_users_db_v2():
    """v1→v2: 为 users.db 添加 password 列"""
    if not os.path.exists(USERS_DB):
        return
    conn = sqlite3.connect(USERS_DB)
    c = conn.cursor()
    try:
        row = c.execute("SELECT version FROM _schema_version WHERE id=1").fetchone()
        if row and row[0] >= 2:
            conn.close()
            return
    except sqlite3.OperationalError:
        pass
    
    try:
        info = c.execute("PRAGMA table_info(users)").fetchall()
        col_names = [r[1] for r in info]
        if "password" not in col_names:
            c.execute("ALTER TABLE users ADD COLUMN password TEXT DEFAULT ''")
            _log_migration("users: 添加 password 列")
            conn.commit()
    except sqlite3.OperationalError as e:
        _log_migration(f"users: ALTER TABLE 失败 {e}")
    
    c.execute("INSERT OR REPLACE INTO _schema_version (id, version) VALUES (1, 2)")
    conn.commit()
    conn.close()


def init_all_dbs():
    """初始化所有业务表（9 个数据库，cloud_pull 依赖全量覆盖）
    
    建表逻辑完全对齐桌面版 core/business_service.py init_business_dbs()
    - 表名：products（非 product）、wallet_transactions、distribution_links、commissions、team_members
    - 字段完全对齐桌面版
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # ── v1→v2 迁移：修复 NOT NULL 约束 ──
    _migrate_users_db_v2()
    _migrate_distribution_db_v2()

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
        password TEXT DEFAULT '',
        user_id TEXT,
        role TEXT DEFAULT 'user',
        license_type TEXT,
        created_at TEXT,
        updated_at TEXT
    )''')
    for col, col_def in [
        ("password", "TEXT DEFAULT ''"),
        ("user_id", "TEXT"),
        ("role", "TEXT DEFAULT 'user'"),
    ]:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass
    c.execute('''CREATE TABLE IF NOT EXISTS user_memberships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        membership_type TEXT,
        activated_at TEXT,
        expires_at TEXT,
        activation_code TEXT
    )''')
    _ensure_schema_version(conn, USERS_DB)
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
    for col, col_def in [
        ("price", "REAL DEFAULT 0"),
        ("cost", "REAL DEFAULT 0"),
        ("description", "TEXT"),
        ("unit", "TEXT"),
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
    for col, col_def in [
        ("department", "TEXT DEFAULT ''"),
    ]:
        try:
            c.execute(f"ALTER TABLE staff ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass
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
    for col, col_def in [
        ("frozen_amount", "REAL DEFAULT 0"),
        ("total_income", "REAL DEFAULT 0"),
    ]:
        try:
            c.execute(f"ALTER TABLE wallet ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass
    c.execute('''CREATE TABLE IF NOT EXISTS wallet_transactions (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        wallet_id      INTEGER NOT NULL,
        type           TEXT NOT NULL,
        amount         REAL NOT NULL,
        balance_after  REAL NOT NULL,
        description    TEXT,
        related_id     TEXT DEFAULT '',
        created_at     TEXT DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (wallet_id) REFERENCES wallet(id)
    )''')
    try:
        c.execute('CREATE INDEX IF NOT EXISTS idx_wallet_txn_type ON wallet_transactions(wallet_id, type)')
    except Exception:
        pass
    try:
        c.execute('CREATE INDEX IF NOT EXISTS idx_wallet_txn_created ON wallet_transactions(created_at DESC)')
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE wallet_transactions ADD COLUMN related_id TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    _ensure_schema_version(conn, WALLET_DB)
    conn.commit()
    conn.close()

    # ── 9. distribution.db ──
    conn = sqlite3.connect(DISTRIBUTION_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS distribution_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT DEFAULT '',
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
        user_name TEXT DEFAULT '',
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
        user_name TEXT DEFAULT '',
        parent_name TEXT DEFAULT '',
        level INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        user_id INTEGER,
        parent_id INTEGER,
        username TEXT,
        total_contribution REAL DEFAULT 0
    )''')
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
        user_type TEXT DEFAULT 'trial',
        status TEXT DEFAULT 'unused',
        bound_account TEXT DEFAULT '',
        bound_machine TEXT DEFAULT '',
        note TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now', 'localtime')),
        used_at TEXT DEFAULT '',
        expires_at TEXT DEFAULT ''
    )''')
    _ensure_schema_version(conn, ACTIVATION_ADMIN_DB)
    conn.commit()
    conn.close()
