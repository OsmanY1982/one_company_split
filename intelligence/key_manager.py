# -*- coding: utf-8 -*-
"""
用户 API Key 管理
每个用户可独立设置自己的云端 API Key
存储位置: data/user_keys/{username}.json
"""

import os
import json
import base64
import hashlib

# ── 存储路径 ──────────────────────────────────────────
_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "user_keys")

# 密钥派生（不可逆，用于混淆 Key 存储）
_SECRET_SALT = "one-company-2026"


def _derive_key(username: str) -> bytes:
    """从用户名派生加密密钥"""
    return hashlib.sha256(f"{username}:{_SECRET_SALT}".encode()).digest()


def _xor_encrypt(plaintext: str, key: bytes) -> str:
    """XOR 混淆（不是真正加密，防止明文存储）"""
    data = plaintext.encode("utf-8")
    key_cycle = (key * ((len(data) // len(key)) + 1))[:len(data)]
    encrypted = bytes(a ^ b for a, b in zip(data, key_cycle))
    return base64.b64encode(encrypted).decode("ascii")


def _xor_decrypt(ciphertext: str, key: bytes) -> str:
    """XOR 解密"""
    try:
        data = base64.b64decode(ciphertext.encode("ascii"))
        key_cycle = (key * ((len(data) // len(key)) + 1))[:len(data)]
        decrypted = bytes(a ^ b for a, b in zip(data, key_cycle))
        return decrypted.decode("utf-8")
    except Exception:
        return ""


def _get_user_file(username: str) -> str:
    """获取用户 Key 文件路径"""
    os.makedirs(_BASE_DIR, exist_ok=True)
    safe_name = "".join(c for c in username if c.isalnum() or c in "_-.")
    return os.path.join(_BASE_DIR, f"{safe_name}.json")


def _load_keys(username: str) -> dict:
    """加载用户的所有 Key"""
    path = _get_user_file(username)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_keys(username: str, keys: dict):
    """保存用户的所有 Key"""
    path = _get_user_file(username)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(keys, f, ensure_ascii=False, indent=2)


def get_api_key(username: str, provider: str) -> str:
    """获取用户在某个平台上的 API Key（解密后）"""
    keys = _load_keys(username)
    ciphertext = keys.get(provider, "")
    if not ciphertext:
        return ""
    return _xor_decrypt(ciphertext, _derive_key(username))


def set_api_key(username: str, provider: str, api_key: str):
    """设置用户在某个平台上的 API Key（加密后存储）"""
    keys = _load_keys(username)
    key = _derive_key(username)
    keys[provider] = _xor_encrypt(api_key.strip(), key)
    _save_keys(username, keys)


def delete_api_key(username: str, provider: str):
    """删除用户在某个平台上的 API Key"""
    keys = _load_keys(username)
    keys.pop(provider, None)
    _save_keys(username, keys)


def has_api_key(username: str, provider: str) -> bool:
    """检查用户是否设置了某个平台的 API Key"""
    keys = _load_keys(username)
    return provider in keys and bool(keys[provider])


def get_shared_api_key(provider: str) -> dict:
    """从 Hermes auth.json 读取共享 API Key（管理员在 Hermes 里配置的）
    返回 {"token": "sk-...", "base_url": "https://..."} 或空 dict
    """
    import os as _os
    auth_path = _os.path.join(_os.path.expanduser("~"), ".hermes", "auth.json")
    try:
        with open(auth_path, "r", encoding="utf-8") as f:
            auth = json.load(f)
        pool = auth.get("credential_pool", {})
        provider_map = {
            # ⚠️ bailian 已移除
            "openai": "custom:openai",
            "deepseek": "custom:deepseek",
        }
        key = provider_map.get(provider, f"custom:{provider}")
        creds = pool.get(key, [])
        if creds:
            return {
                "token": creds[0].get("access_token", ""),
                "base_url": creds[0].get("base_url", ""),
            }
    except Exception as e:
        print(f"[key_manager] 加载凭证失败: {e}")
    return {}


def get_current_username() -> str:
    """从 app_state 获取当前登录用户名"""
    try:
        from core.app_state import app_state
        return app_state.username or "unknown"
    except Exception:
        return "unknown"