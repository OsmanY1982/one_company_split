# -*- coding: utf-8 -*-
"""
钱包数据库初始化
"""
import os
import sys

# ── 路径：wallet_service/_db.py → 项目根目录（4层dirname）──
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    from database import get_conn
except ImportError:
    try:
        from database import get_conn
    except ImportError:
        from core.database import get_conn
try:
    from paths import DATA_DIR
except ImportError:
    try:
        from paths import DATA_DIR
    except ImportError:
        from core.paths import DATA_DIR

DB_PATH = os.path.join(DATA_DIR, "wallet.db")


def _connect():
    """返回统一连接管理器中的 wallet.db 连接"""
    return get_conn("wallet.db")


def init_db():
    """初始化钱包相关表结构"""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = get_conn("wallet.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallet (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          TEXT UNIQUE NOT NULL,
            balance          REAL DEFAULT 0,
            frozen_amount    REAL DEFAULT 0,
            total_income     REAL DEFAULT 0,
            total_withdraw   REAL DEFAULT 0,
            status           TEXT DEFAULT 'active',
            created_at       TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at       TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallet_transactions (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_id      INTEGER NOT NULL,
            type           TEXT NOT NULL,
            amount         REAL NOT NULL,
            balance_after  REAL NOT NULL,
            description    TEXT,
            created_at     TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (wallet_id) REFERENCES wallet(id)
        )
    ''')
    try:
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_wallet_txn_type "
            "ON wallet_transactions(wallet_id, type)"
        )
    except Exception:
        pass
    try:
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_wallet_txn_created "
            "ON wallet_transactions(created_at DESC)"
        )
    except Exception:
        pass
    conn.commit()


def init_address_book_db():
    conn = _connect()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS address_book (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_user TEXT NOT NULL,
            label TEXT NOT NULL,
            address TEXT NOT NULL,
            address_type TEXT DEFAULT 'user',
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    conn.commit()


def init_withdrawal_queue():
    """初始化提现审批队列表（幂等）"""
    conn = get_conn("wallet.db")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS withdrawal_queue (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      TEXT NOT NULL,
            wallet_id    INTEGER NOT NULL,
            amount       REAL NOT NULL,
            description  TEXT,
            status       TEXT DEFAULT 'pending',
            reviewed_by  TEXT,
            reviewed_at  TEXT,
            note         TEXT,
            created_at   TEXT DEFAULT (datetime('now'))
        )
    ''')
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_withdrawal_status ON withdrawal_queue(status)")
    except Exception:
        pass
    conn.commit()
