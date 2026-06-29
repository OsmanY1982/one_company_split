# -*- coding: utf-8 -*-
"""激活码生成、验证、工具函数"""
import os
import json
import hashlib
import hmac

from core.paths import BASE_DIR, CONFIG_DIR as LICENSE_DIR

# ── 激活码规则 ──
CODE_TYPES = {
    "TRIAL": {"name": "体验会员",  "days": 7,   "price": 0,  "features": ["basic"]},
    "PRO":   {"name": "VIP会员",  "days": 365, "price": 49, "features": ["basic"]},
    "VIP":   {"name": "钻石会员",  "days": 0,   "price": 99, "features": ["basic", "quant", "cloud"]},
}

# ── 防篡改密钥 ──
_HMAC_KEY = b"replace_with_your_32byte_hex_key_here_64hex"
SECRET_KEY = "replace_with_your_secret_key_here"


def _sign_license(data: dict) -> str:
    expires = data.get('expires_at') or ''
    payload = f"{data.get('type','')}{data.get('account','')}{data.get('machine_code','')}{data.get('activated_at','')}{expires}"
    return hmac.new(_HMAC_KEY, payload.encode(), hashlib.sha256).hexdigest()


def _verify_license_signature(data: dict) -> bool:
    expected = _sign_license(data)
    actual   = data.get("_sig", "")
    return hmac.compare_digest(expected, actual)


def _get_license_file(account="default") -> str:
    if account and account != "default":
        return f"{LICENSE_DIR}/license_{account}.json"
    return f"{LICENSE_DIR}/license.json"


def _normalize(code: str) -> str:
    return code.upper().replace("-", "").replace(" ", "")


def _format_code(code: str) -> str:
    c = _normalize(code)
    if len(c) >= 14:
        prefix = c[:3] if c[:3] in ("VIP", "PRO") else c[:5]
        rest   = c[len(prefix):]
        parts  = [rest[i:i+4] for i in range(0, len(rest), 4)]
        return f"{prefix}-" + "-".join(parts)
    return code


def _get_type_from_code(code: str):
    c = _normalize(code)
    for prefix in ["VIP", "PRO", "TRIAL"]:
        if c.startswith(prefix):
            return prefix
    return None


def validate_code_format(code: str):
    return _get_type_from_code(code)


def generate_activation_code(machine_code: str, act_type="TRIAL") -> str:
    s = f"{machine_code}{SECRET_KEY}{act_type}"
    return hashlib.md5(s.encode()).hexdigest().upper()[:16]
