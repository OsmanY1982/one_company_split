# -*- coding: utf-8 -*-
"""
许可证本地模块（替代原 core/license_service.py）
提供激活码验证、机器码生成等核心功能，供 account/auth 模块使用。
"""
import os, json, hashlib, uuid
import platform as _platform
from datetime import datetime, timedelta
from core.database import get_conn
from core.paths import DATA_DIR, CONFIG_DIR

# ── 常量 ──
DB_FILE = os.path.join(DATA_DIR, "activation.db")
LICENSE_FILE = os.path.join(CONFIG_DIR, "license.json")

CODE_TYPES = {
    "TRIAL": {"name": "体验会员",  "days": 7,   "price": 0,  "features": ["basic"]},
    "PRO":   {"name": "VIP会员",  "days": 365, "price": 49, "features": ["basic"]},
    "VIP":   {"name": "钻石会员",  "days": 0,   "price": 99, "features": ["basic", "quant", "cloud"]},
}

ADMIN_USERS = ["admin"]

# ── 机器码 ──
def get_machine_code() -> str:
    raw = f"{_platform.node()}-{uuid.getnode()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

# ── 工具函数 ──
def _normalize(code: str) -> str:
    return code.upper().replace("-", "").replace(" ", "")

def _format_code(code: str) -> str:
    c = _normalize(code)
    if len(c) >= 14:
        prefix = c[:3] if c[:3] in ("VIP", "PRO") else c[:5]
        rest = c[len(prefix):]
        parts = [rest[i:i+4] for i in range(0, len(rest), 4)]
        return f"{prefix}-" + "-".join(parts)
    return code

def _get_license_file(account="default") -> str:
    if account and account != "default":
        return os.path.join(CONFIG_DIR, f"license_{account}.json")
    return os.path.join(CONFIG_DIR, "license.json")

# ── 数据库初始化 ──
def init_activation_db():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = get_conn("activation.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS activation_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL,
            status TEXT DEFAULT 'unused',
            bound_account TEXT,
            bound_machine TEXT,
            created_at TEXT,
            used_at TEXT,
            expires_at TEXT,
            _sig TEXT
        )
    """)
    conn.commit()

# ── 验证许可证 ──
def validate_license(account="default") -> dict:
    init_activation_db()
    current_machine = get_machine_code()
    is_admin_user = account in ADMIN_USERS

    def _fail(reason="未激活", expired=False):
        return {
            "valid": False, "expired": expired,
            "type": None, "name": reason,
            "remaining_days": 0, "expires_at": None,
            "features": [], "machine_code": current_machine,
            "is_admin": is_admin_user
        }

    lic_file = _get_license_file(account)
    if not os.path.exists(lic_file):
        return _fail("未激活")

    try:
        with open(lic_file, "r", encoding="utf-8") as f:
            lic = json.load(f)
    except Exception:
        return _fail("许可证文件损坏")

    lic_type = lic.get("type", "").upper()
    bound_machine = lic.get("machine_code", "")
    if bound_machine and bound_machine != current_machine:
        return _fail("设备不匹配，此授权不适用于本机")

    if lic_type == "VIP":
        return {
            "valid": True, "expired": False,
            "type": "vip", "name": "钻石会员",
            "remaining_days": -1, "expires_at": None,
            "features": CODE_TYPES["VIP"]["features"],
            "machine_code": current_machine, "is_admin": is_admin_user
        }

    if lic_type == "PRO":
        expires_at = lic.get("expires_at")
        if not expires_at:
            return {
                "valid": True, "expired": False,
                "type": "pro", "name": "VIP会员（永久）",
                "remaining_days": -1, "expires_at": None,
                "features": CODE_TYPES["PRO"]["features"],
                "machine_code": current_machine, "is_admin": is_admin_user
            }
        try:
            exp = datetime.fromisoformat(expires_at)
            remaining = (exp - datetime.now()).days
            if remaining > 0:
                return {
                    "valid": True, "expired": False,
                    "type": "pro", "name": "VIP会员",
                    "remaining_days": remaining, "expires_at": expires_at,
                    "features": CODE_TYPES["PRO"]["features"],
                    "machine_code": current_machine, "is_admin": is_admin_user
                }
            else:
                return _fail("VIP会员(已过期)", expired=True)
        except Exception:
            return _fail("许可证数据异常")

    if lic_type == "TRIAL":
        expires_at = lic.get("expires_at")
        try:
            exp = datetime.fromisoformat(expires_at)
            remaining = (exp - datetime.now()).days
            return {
                "valid": remaining > 0,
                "expired": remaining <= 0,
                "type": "trial", "name": "体验会员",
                "remaining_days": remaining, "expires_at": expires_at,
                "features": CODE_TYPES["TRIAL"]["features"],
                "machine_code": current_machine, "is_admin": is_admin_user
            }
        except Exception:
            return _fail("体验码已过期", expired=True)

    return _fail("未知许可证类型")

# ── 激活许可证 ──
def activate_license(code: str, account="default", machine_code="") -> tuple:
    if not code or not code.strip():
        return False, "激活码不能为空"

    code = code.strip()
    current_machine = machine_code or get_machine_code()
    norm = _normalize(code)

    # 解析类型
    act_type = None
    for prefix in ["VIP", "PRO", "TRIAL"]:
        if norm.startswith(prefix):
            act_type = prefix
            break

    if not act_type or act_type not in CODE_TYPES:
        return False, "激活码无效或格式不正确"

    init_activation_db()
    conn = get_conn("activation.db")
    c = conn.cursor()
    c.execute("SELECT status, bound_account, bound_machine FROM activation_codes WHERE code=?", (norm,))
    row = c.fetchone()

    if row:
        status, bound_account, bound_machine = row
        if status == "used" and bound_account:
            if bound_account != account:
                return False, f"激活码已被账号 {bound_account} 使用，无法重复激活"
        if bound_machine and bound_machine != current_machine:
            return False, "此激活码已绑定其他设备，无法在本机激活"

    type_info = CODE_TYPES[act_type]
    days = type_info["days"]
    now = datetime.now()
    expires_at = None if days == 0 else (now + timedelta(days=days)).isoformat()

    lic_file = _get_license_file(account)
    os.makedirs(os.path.dirname(lic_file), exist_ok=True)
    with open(lic_file, "w", encoding="utf-8") as f:
        json.dump({
            "type": act_type,
            "code": code,
            "account": account,
            "machine_code": current_machine,
            "activated_at": now.isoformat(),
            "expires_at": expires_at,
            "name": type_info["name"],
            "features": type_info["features"]
        }, f, indent=2, ensure_ascii=False)

    # 更新数据库
    c.execute(
        "INSERT OR REPLACE INTO activation_codes (code, type, status, bound_account, bound_machine, created_at, used_at, expires_at) "
        "VALUES (?, ?, 'used', ?, ?, ?, ?, ?)",
        (norm, act_type, account, current_machine, now.isoformat(), now.isoformat(), expires_at)
    )
    conn.commit()

    return True, f"激活成功！类型：{type_info['name']}"

# ── 转移许可证 ──
def transfer_license(code: str, account="default") -> tuple:
    current_machine = get_machine_code()
    norm = _normalize(code)

    init_activation_db()
    conn = get_conn("activation.db")
    c = conn.cursor()
    c.execute("SELECT status, bound_account FROM activation_codes WHERE code=?", (norm,))
    row = c.fetchone()
    if not row:
        return False, "激活码不存在"

    return activate_license(code, account)
