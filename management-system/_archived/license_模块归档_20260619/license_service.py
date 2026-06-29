# -*- coding: utf-8 -*-
"""
许可证服务 - 统一入口

内部实现已拆分到：
  - license_crypto: 激活码生成、签名、工具函数
  - license_db:     数据库操作、日志

本文件 re-export 所有公开接口，确保现有代码零改动。
"""
import os
import json
import hashlib
import uuid
from core.database import get_conn
from datetime import datetime, timedelta

# ── 从子模块 re-export ──
from core.license_crypto import (
    CODE_TYPES,
    _HMAC_KEY,
    SECRET_KEY,
    _sign_license,
    _verify_license_signature,
    _get_license_file,
    _normalize,
    _format_code,
    _get_type_from_code,
    validate_code_format,
    generate_activation_code,
)
from core.license_db import (
    DB_FILE,
    ADMIN_DB,
    LOG_FILE,
    init_activation_db,
    init_admin_db,
    _init_log_db,
    _write_log,
)

# ── 路径常量（兼容旧代码）──
from core.paths import BASE_DIR, CONFIG_DIR, DATA_DIR
LICENSE_DIR = CONFIG_DIR
LICENSE_FILE = os.path.join(CONFIG_DIR, "license.json")
KEY_FILE    = os.path.join(CONFIG_DIR, "machine_key.json")

# ── 超级管理员名单 ──
ADMIN_USERS = ["admin"]


# ══════════════════════════════════════════════
#  机器码
# ══════════════════════════════════════════════
def _get_mac_address() -> str:
    """跨平台获取 MAC 地址"""
    try:
        mac = uuid.getnode()
        if (mac >> 40) % 2:  # 本地管理位 → 随机 MAC，不可靠
            raise ValueError("random MAC")
        return format(mac, "012x")
    except Exception:
        return ""


def _get_cpu_info() -> str:
    """跨平台获取 CPU 标识"""
    import platform
    return platform.processor() or ""


def _get_disk_serial() -> str:
    """跨平台获取磁盘序列号"""
    import subprocess, sys
    try:
        if sys.platform == "win32":
            r = subprocess.run(['wmic', 'diskdrive', 'get', 'SerialNumber'],
                               capture_output=True, text=True, timeout=5)
            return r.stdout.strip().split('\n')[-1].strip()
        elif sys.platform == "darwin":
            r = subprocess.run(['system_profiler', 'SPStorageDataType', '|', 'grep', 'Volume UUID'],
                               capture_output=True, text=True, timeout=5, shell=True)
            return r.stdout.strip().replace("Volume UUID:", "").strip()[:16]
        else:
            r = subprocess.run(['lsblk', '-d', '-o', 'SERIAL', '-n'],
                               capture_output=True, text=True, timeout=5)
            return r.stdout.strip().split('\n')[0].strip()
    except Exception:
        pass
    return ""


def get_machine_code() -> str:
    """生成稳定的 32 位机器码（跨平台，写入 KEY_FILE 缓存）"""
    if os.path.exists(KEY_FILE):
        try:
            with open(KEY_FILE, "r") as f:
                data = json.load(f)
            mc = data.get("machine_code", "")
            if mc and len(mc) == 32:
                return mc
        except Exception:
            pass

    import platform, sys
    parts = []

    mac = _get_mac_address()
    if mac:
        parts.append("MAC:" + mac)

    cpu = _get_cpu_info()
    if cpu:
        parts.append("CPU:" + cpu)

    disk = _get_disk_serial()
    if disk:
        parts.append("DISK:" + disk)

    parts.append("HOST:" + platform.node())
    parts.append("SYS:" + sys.platform)

    combined = "|".join(parts)
    machine_code = hashlib.sha256(combined.encode()).hexdigest().upper()[:32]

    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
    with open(KEY_FILE, "w") as f:
        json.dump({"machine_code": machine_code, "created_at": datetime.now().isoformat()}, f, indent=2)
    return machine_code


# ══════════════════════════════════════════════
#  核心业务：验证许可证
# ══════════════════════════════════════════════
def validate_license(account="default") -> dict:
    init_activation_db()
    current_machine = get_machine_code()
    is_admin_user   = account in ADMIN_USERS

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

    if "_sig" in lic and not _verify_license_signature(lic):
        _write_log(account, current_machine, "", "", "validate", "TAMPERED",
                   "license file signature mismatch")
        return _fail("许可证已被篡改，请重新激活")

    lic_type = lic.get("type", "").upper()
    bound_machine = lic.get("machine_code", "")
    if bound_machine and bound_machine != current_machine:
        _write_log(account, current_machine, "", lic_type, "validate", "MACHINE_MISMATCH",
                   f"bound={bound_machine} current={current_machine}")
        return _fail("设备不匹配，此授权不适用于本机")

    try:
        from core.supabase_client import check_user_cloud_status
        ok, exists = check_user_cloud_status(account)
        if ok and exists is False:
            _write_log(account, current_machine, "", lic_type, "validate", "CLOUD_DELETED",
                       "user has been deleted from cloud by admin")
            return _fail("账号已被管理员删除，请联系管理员重新激活")
    except Exception:
        pass

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
            exp       = datetime.fromisoformat(expires_at)
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
            exp       = datetime.fromisoformat(expires_at)
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


# ══════════════════════════════════════════════
#  核心业务：激活许可证
# ══════════════════════════════════════════════
def activate_license(code: str, account="default") -> tuple:
    if not code or not code.strip():
        return False, "激活码不能为空"

    code            = code.strip()
    current_machine = get_machine_code()
    norm            = _normalize(code)
    act_type        = None

    # 方式1：机器码激活码（16位纯字母数字）
    if len(norm) == 16 and "-" not in code:
        valid_codes = {t: generate_activation_code(current_machine, t) for t in CODE_TYPES}
        for t, vc in valid_codes.items():
            if norm == vc:
                act_type = t
                break
    else:
        act_type = _get_type_from_code(code)

    if not act_type or act_type not in CODE_TYPES:
        _write_log(account, current_machine, code, "", "activate", "INVALID_FORMAT")
        return False, "激活码无效或格式不正确"

    init_activation_db()
    conn = get_conn("activation.db")
    c    = conn.cursor()
    c.execute("SELECT status, bound_account, bound_machine FROM activation_codes WHERE code=?", (norm,))
    row = c.fetchone()

    if row:
        status, bound_account, bound_machine = row
        if status == "used" and bound_account:
            if bound_account != account:
                _write_log(account, current_machine, code, act_type, "activate", "ALREADY_USED",
                           f"bound_to={bound_account}")
                return False, f"激活码已被账号 {bound_account} 使用，无法重复激活"
        if bound_machine and bound_machine != current_machine:
            _write_log(account, current_machine, code, act_type, "activate", "MACHINE_MISMATCH",
                       f"bound={bound_machine} current={current_machine}")
            return False, "此激活码已绑定其他设备，无法在本机激活"

    type_info  = CODE_TYPES[act_type]
    days       = type_info["days"]
    expires_at = None if days == 0 else (datetime.now() + timedelta(days=days)).isoformat()
    now_str    = datetime.now().isoformat()

    lic_data = {
        "type": act_type, "account": account,
        "machine_code": current_machine, "activated_at": now_str, "expires_at": expires_at,
    }
    lic_data["_sig"] = _sign_license(lic_data)

    lic_file = _get_license_file(account)
    os.makedirs(os.path.dirname(lic_file), exist_ok=True)
    with open(lic_file, "w", encoding="utf-8") as f:
        json.dump(lic_data, f, indent=2, ensure_ascii=False)

    conn = get_conn("activation.db")
    c    = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO activation_codes (code, type, status, bound_account, bound_machine, created_at) VALUES (?, ?, 'used', ?, ?, ?)",
        (norm, act_type, account, current_machine, now_str)
    )
    conn.commit()

    if os.path.exists(ADMIN_DB):
        try:
            conn2 = get_conn("activation_admin.db")
            c2    = conn2.cursor()
            c2.execute(
                "UPDATE admin_codes SET status='used', bound_account=?, bound_machine=?, used_at=? WHERE code=? OR code=?",
                (account, current_machine, now_str, code, norm)
            )
            conn2.commit()
        except Exception as e:
            print(f"[activate] admin_db update failed: {e}")

    try:
        from core.supabase_client import CloudActivation, CloudUser, CloudLog
        CloudActivation.use_code(code, account, current_machine)
        CloudUser.sync_membership(account, act_type.lower(), current_machine, norm, expires_at)
        CloudLog.log(account, current_machine, norm, "activate", "SUCCESS", f"type={act_type}")
    except Exception as e:
        print(f"[activate] cloud sync failed (non-blocking): {e}")

    _write_log(account, current_machine, code, act_type, "activate", "SUCCESS", f"expires={expires_at}")

    try:
        from core.business_service import on_membership_activated, _get_code_price
        price = _get_code_price(act_type)
        on_membership_activated(
            username=account, code_type=act_type, activation_code=norm,
            machine_code=current_machine, expires_at=expires_at, price=price
        )
    except Exception as e:
        print(f"[activate] business_service failed (non-blocking): {e}")

    return True, f"激活成功！{type_info['name']}"


def sync_license_from_cloud(account: str) -> tuple:
    try:
        from core.supabase_client import _request as _cloud_request
        ok, result = _cloud_request("GET", f"/rest/v1/user_memberships?username=eq.{account}&select=*",
                                    service_key=True)
        if not ok or not isinstance(result, list) or len(result) == 0:
            return False, "云端无激活记录"

        membership = result[0]
        mem_type = (membership.get("membership_type") or "").upper()
        if mem_type not in CODE_TYPES:
            return False, f"未知会员类型：{mem_type}"

        current_machine = get_machine_code()
        cloud_machine = membership.get("machine_code", "")
        expires_at = membership.get("expires_at")
        activation_code = membership.get("activation_code", "")
        now_str = datetime.now().isoformat()

        lic_data = {
            "type": mem_type, "account": account,
            "machine_code": current_machine,
            "activated_at": membership.get("activated_at") or now_str,
            "expires_at": expires_at, "synced_from_cloud": True,
        }
        lic_data["_sig"] = _sign_license(lic_data)

        lic_file = _get_license_file(account)
        os.makedirs(os.path.dirname(lic_file), exist_ok=True)
        with open(lic_file, "w", encoding="utf-8") as f:
            json.dump(lic_data, f, indent=2, ensure_ascii=False)

        _write_log(account, current_machine, activation_code, mem_type,
                   "cloud_sync", "SUCCESS", f"从云端同步，原设备：{cloud_machine}")
        return True, f"已从云端同步激活状态：{CODE_TYPES[mem_type]['name']}"
    except Exception as e:
        return False, f"云端同步失败：{str(e)[:80]}"


def sync_license_from_db(account: str) -> bool:
    lic_file = _get_license_file(account)
    if os.path.exists(lic_file):
        return True

    users_db = os.path.join(DATA_DIR, "users.db")
    if not os.path.exists(users_db):
        return False

    try:
        conn = get_conn("users.db")
        c = conn.cursor()
        c.execute("SELECT membership_type, activated_at, expires_at, activation_code FROM user_memberships WHERE username=?", (account,))
        row = c.fetchone()
    except Exception as e:
        print(f"[sync_license] db error: {e}")
        return False

    if not row or not row[0]:
        return False

    mem_type, activated_at, expires_at, activation_code = row
    act_type = mem_type.upper()
    if act_type not in CODE_TYPES:
        return False

    current_machine = get_machine_code()
    now_str = activated_at or datetime.now().isoformat()

    lic_data = {
        "type": act_type, "account": account,
        "machine_code": current_machine, "activated_at": now_str, "expires_at": expires_at,
    }
    lic_data["_sig"] = _sign_license(lic_data)

    os.makedirs(os.path.dirname(lic_file), exist_ok=True)
    with open(lic_file, "w", encoding="utf-8") as f:
        json.dump(lic_data, f, indent=2, ensure_ascii=False)

    print(f"[sync_license] rebuilt license for {account}: {act_type}")
    return True


def transfer_license(code: str, account="default") -> tuple:
    if not code or not code.strip():
        return False, "激活码不能为空"

    code = code.strip()
    current_machine = get_machine_code()
    norm = _normalize(code)
    act_type = _get_type_from_code(code)

    if not act_type or act_type not in CODE_TYPES:
        return False, "激活码无效或格式不正确"

    init_activation_db()
    conn = get_conn("activation.db")
    c = conn.cursor()
    c.execute("SELECT status, bound_account, bound_machine FROM activation_codes WHERE code=?", (norm,))
    row = c.fetchone()

    if not row:
        return False, "激活码不存在，无法迁移"

    status, bound_account, bound_machine = row
    if status == "used" and bound_account and bound_account != account:
        _write_log(account, current_machine, code, act_type, "transfer", "NOT_OWNER", f"bound_to={bound_account}")
        return False, f"此激活码属于账号 {bound_account}，您无权迁移"

    if not bound_machine or status != "used":
        return activate_license(code, account)

    if bound_machine == current_machine:
        return True, "当前设备已激活，无需迁移"

    type_info = CODE_TYPES[act_type]
    days = type_info["days"]
    now_str = datetime.now().isoformat()

    conn = get_conn("activation.db")
    c = conn.cursor()
    c.execute("SELECT expires_at FROM activation_codes WHERE code=?", (norm,))
    expires_row = c.fetchone()
    expires_at = expires_row[0] if expires_row and expires_row[0] else (
        None if days == 0 else (datetime.now() + timedelta(days=days)).isoformat())

    lic_data = {
        "type": act_type, "account": account,
        "machine_code": current_machine, "activated_at": now_str,
        "expires_at": expires_at, "transferred_from": bound_machine, "transferred_at": now_str,
    }
    lic_data["_sig"] = _sign_license(lic_data)

    lic_file = _get_license_file(account)
    os.makedirs(os.path.dirname(lic_file), exist_ok=True)
    with open(lic_file, "w", encoding="utf-8") as f:
        json.dump(lic_data, f, indent=2, ensure_ascii=False)

    conn = get_conn("activation.db")
    c = conn.cursor()
    c.execute("UPDATE activation_codes SET bound_account=?, bound_machine=?, used_at=?, status='used' WHERE code=?",
              (account, current_machine, now_str, norm))
    conn.commit()

    if os.path.exists(ADMIN_DB):
        try:
            conn2 = get_conn("activation_admin.db")
            c2 = conn2.cursor()
            c2.execute("UPDATE admin_codes SET status='used', bound_account=?, bound_machine=?, used_at=? WHERE code=? OR code=?",
                       (account, current_machine, now_str, code, norm))
            conn2.commit()
        except Exception as e:
            print(f"[transfer] admin_db update failed: {e}")

    _write_log(account, current_machine, code, act_type, "transfer", "SUCCESS",
               f"从设备 {bound_machine} 迁移到 {current_machine}")
    return True, f"设备迁移成功！{type_info['name']}，已绑定新设备"


def activate_license_for_machine(code: str, account: str, target_machine: str) -> tuple:
    if not code or not code.strip():
        return False, "激活码不能为空"
    if not account or not account.strip():
        return False, "账号不能为空"
    if not target_machine or not target_machine.strip():
        return False, "目标机器码不能为空"

    code = code.strip()
    account = account.strip()
    target_machine = target_machine.strip().upper()
    norm = _normalize(code)
    act_type = _get_type_from_code(code)

    if not act_type or act_type not in CODE_TYPES:
        return False, "激活码无效或格式不正确"

    init_activation_db()
    conn = get_conn("activation.db")
    c = conn.cursor()
    c.execute("SELECT status, bound_account, bound_machine FROM activation_codes WHERE code=?", (norm,))
    row = c.fetchone()

    if row:
        status, bound_account, bound_machine = row
        if status == "used" and bound_account and bound_account != account:
            _write_log(account, target_machine, code, act_type, "remote_activate", "ALREADY_USED", f"bound_to={bound_account}")
            return False, f"激活码已被账号 {bound_account} 使用，无法重复激活"
        if status == "used" and bound_account == account and bound_machine and bound_machine != target_machine:
            _write_log(account, target_machine, code, act_type, "remote_activate", "DEVICE_TRANSFER",
                       f"从 {bound_machine} 迁移到 {target_machine}")
        if status == "used" and bound_account == account and bound_machine == target_machine:
            return True, "该账号已在此设备激活，无需重复操作"

    type_info = CODE_TYPES[act_type]
    days = type_info["days"]
    expires_at = None if days == 0 else (datetime.now() + timedelta(days=days)).isoformat()
    now_str = datetime.now().isoformat()

    lic_data = {
        "type": act_type, "account": account,
        "machine_code": target_machine, "activated_at": now_str,
        "expires_at": expires_at, "remote_activated": True,
    }
    lic_data["_sig"] = _sign_license(lic_data)

    lic_file = _get_license_file(account)
    os.makedirs(os.path.dirname(lic_file), exist_ok=True)
    with open(lic_file, "w", encoding="utf-8") as f:
        json.dump(lic_data, f, indent=2, ensure_ascii=False)

    conn = get_conn("activation.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO activation_codes (code, type, status, bound_account, bound_machine, created_at) VALUES (?, ?, 'used', ?, ?, ?)",
              (norm, act_type, account, target_machine, now_str))
    conn.commit()

    if os.path.exists(ADMIN_DB):
        try:
            conn2 = get_conn("activation_admin.db")
            c2 = conn2.cursor()
            c2.execute("UPDATE admin_codes SET status='used', bound_account=?, bound_machine=?, used_at=? WHERE code=? OR code=?",
                       (account, target_machine, now_str, code, norm))
            conn2.commit()
        except Exception as e:
            print(f"[remote_activate] admin_db update failed: {e}")

    _write_log(account, target_machine, code, act_type, "remote_activate", "SUCCESS",
               f"管理员远程激活，目标设备：{target_machine}")
    return True, f"远程激活成功！账号 {account} 已绑定设备 {target_machine[:8]}...，类型：{type_info['name']}"


def unbind_machine(code: str) -> tuple:
    if not code or not code.strip():
        return False, "激活码不能为空"

    code = code.strip()
    norm = _normalize(code)

    init_activation_db()
    conn = get_conn("activation.db")
    c = conn.cursor()
    c.execute("SELECT status, bound_account, bound_machine, type FROM activation_codes WHERE code=?", (norm,))
    row = c.fetchone()

    if not row:
        return False, "激活码不存在"

    status, bound_account, bound_machine, code_type = row
    if status != "used":
        return False, "该激活码尚未使用，无需解绑"
    if not bound_machine:
        return False, "该激活码未绑定设备，无需解绑"

    c.execute("UPDATE activation_codes SET bound_machine='', status='unused' WHERE code=?", (norm,))
    conn.commit()

    if os.path.exists(ADMIN_DB):
        try:
            conn2 = get_conn("activation_admin.db")
            c2 = conn2.cursor()
            c2.execute("UPDATE admin_codes SET status='unused', bound_account='', bound_machine='', used_at=NULL WHERE code=? OR code=?",
                       (code, norm))
            conn2.commit()
        except Exception as e:
            print(f"[unbind] admin_db update failed: {e}")

    if bound_account:
        lic_file = _get_license_file(bound_account)
        if os.path.exists(lic_file):
            os.remove(lic_file)

    _write_log(bound_account or "unknown", bound_machine, code, code_type or "",
               "unbind", "SUCCESS", f"解绑设备 {bound_machine}")
    return True, f"已解绑设备 {bound_machine[:8]}...，激活码已恢复为未使用状态，用户可重新激活"


def clear_license(account="default"):
    lic_file = _get_license_file(account)
    if os.path.exists(lic_file):
        os.remove(lic_file)
    return True
