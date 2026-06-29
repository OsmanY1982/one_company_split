# `iqra/core/secure_storage.py`

> 路径：`iqra/core/secure_storage.py` | 行数：434


---


```python
"""
安全存储模块 - macOS Keychain + AES 加密 API Key

特性:
- 使用 macOS Keychain 安全存储 AES 主密钥
- 使用 AES (Fernet) 加密数据存储在本地文件
- 绑定当前用户账户，换用户无法解密（Keychain 天然按用户隔离）
- 可选绑定机器指纹，防止文件复制到其他设备
- 平台检测：仅支持 macOS，其他平台给出明确错误提示
"""

import json
import os
import hashlib
import platform
import subprocess
from pathlib import Path

# ── 平台检测 ──
_CURRENT_OS = platform.system()
_IS_MACOS = _CURRENT_OS == "Darwin"

if _IS_MACOS:
    try:
        from cryptography.fernet import Fernet, InvalidToken
        _FERNET_AVAILABLE = True
    except ImportError:
        _FERNET_AVAILABLE = False
else:
    _FERNET_AVAILABLE = False

# Keychain 常量
_KEYCHAIN_SERVICE = "com.iqra.secure-storage"
_KEYCHAIN_ACCOUNT = "aes-master-key"

# Fernet 单例缓存
_fernet = None


# ═══════════════════════════════════════════
# Keychain 操作
# ═══════════════════════════════════════════

def _keychain_add(service: str, account: str, password: str) -> None:
    """向 Keychain 添加或更新通用密码条目。"""
    subprocess.run(
        [
            "security", "add-generic-password",
            "-a", account,
            "-s", service,
            "-w", password,
            "-U",
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _keychain_get(service: str, account: str) -> str:
    """从 Keychain 读取通用密码条目。"""
    result = subprocess.run(
        [
            "security", "find-generic-password",
            "-a", account,
            "-s", service,
            "-w",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Keychain 访问失败: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def _keychain_delete(service: str, account: str) -> None:
    """从 Keychain 删除通用密码条目。"""
    subprocess.run(
        [
            "security", "delete-generic-password",
            "-a", account,
            "-s", service,
        ],
        capture_output=True,
        text=True,
    )


# ═══════════════════════════════════════════
# 机器指纹
# ═══════════════════════════════════════════

def _get_machine_fingerprint() -> str:
    """生成机器指纹（硬件 UUID + 主机名）。"""
    try:
        result = subprocess.run(
            ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
            capture_output=True, text=True, timeout=5,
        )
        uuid = ""
        for line in result.stdout.split("\n"):
            if "IOPlatformUUID" in line:
                # 形如: "IOPlatformUUID" = "XXXXXXXX-XXXX-..."
                parts = line.split('"')
                if len(parts) >= 4:
                    uuid = parts[3]
                break

        fingerprint = f"{uuid}-{platform.node()}"
        return hashlib.sha256(fingerprint.encode()).hexdigest()[:32]
    except Exception:
        # 降级方案：使用用户名 + 主机名
        return hashlib.sha256(
            f"{os.getlogin()}-{platform.node()}".encode()
        ).hexdigest()[:32]


# ═══════════════════════════════════════════
# AES 加密 / 解密（Fernet + Keychain 主密钥）
# ═══════════════════════════════════════════

def _get_or_create_fernet():
    """获取或创建 Fernet 实例 — 从 Keychain 读取 AES 主密钥。

    首次调用时，如果 Keychain 中不存在主密钥，则自动生成新密钥并存储。
    后续调用复用缓存的 Fernet 实例，避免重复访问 Keychain。
    """
    global _fernet
    if _fernet is not None:
        return _fernet

    if not _IS_MACOS:
        raise RuntimeError(
            f"Secure storage requires macOS. "
            f"Current OS: {_CURRENT_OS}. "
            f"This module uses macOS Keychain Services for encryption."
        )
    if not _FERNET_AVAILABLE:
        raise RuntimeError(
            "cryptography library is required for secure storage. "
            "Install it with: pip install cryptography"
        )

    try:
        key_str = _keychain_get(_KEYCHAIN_SERVICE, _KEYCHAIN_ACCOUNT)
        _fernet = Fernet(key_str.encode())
    except Exception:
        # 主密钥不存在或 Keychain 出错：生成新密钥
        key = Fernet.generate_key()
        _keychain_add(_KEYCHAIN_SERVICE, _KEYCHAIN_ACCOUNT, key.decode())
        _fernet = Fernet(key)

    return _fernet


def _encrypt_data(data: bytes) -> bytes:
    """使用 Fernet (AES-128-CBC + HMAC) 加密数据。"""
    f = _get_or_create_fernet()
    return f.encrypt(data)


def _decrypt_data(encrypted: bytes) -> bytes:
    """使用 Fernet (AES-128-CBC + HMAC) 解密数据。

    Raises:
        RuntimeError: 密钥不匹配（数据来自其他用户/机器）。
    """
    f = _get_or_create_fernet()
    try:
        return f.decrypt(encrypted)
    except InvalidToken:
        raise RuntimeError(
            "Decryption failed - data may be from a different user or machine. "
            "The Keychain encryption key does not match the stored data."
        )


# ═══════════════════════════════════════════
# SecureStorage 类
# ═══════════════════════════════════════════

class SecureStorage:
    """安全存储管理器"""

    def __init__(self, app_name: str = "iqra", bind_machine: bool = False):
        """
        Args:
            app_name: 应用名称，用于生成存储路径
            bind_machine: 是否绑定机器指纹（防止文件复制到其他设备）
        """
        self.app_name = app_name
        self.bind_machine = bind_machine
        self._storage_dir = Path.home() / f".{app_name}"
        self._storage_dir.mkdir(exist_ok=True)
        self._keys_file = self._storage_dir / "keys.enc"
        self._machine_file = self._storage_dir / ".machine"

    def _get_machine_id(self) -> str:
        """获取或创建机器标识"""
        if self._machine_file.exists():
            return self._machine_file.read_text().strip()

        machine_id = _get_machine_fingerprint()
        self._machine_file.write_text(machine_id)
        return machine_id

    def _check_machine_binding(self) -> bool:
        """检查机器绑定是否有效"""
        if not self.bind_machine:
            return True
        if not self._machine_file.exists():
            return True  # 首次使用

        stored = self._machine_file.read_text().strip()
        current = _get_machine_fingerprint()
        return stored == current

    def save_api_key(self, provider_id: str, api_key: str) -> bool:
        """
        安全保存 API Key

        Args:
            provider_id: 供应商 ID (如 "bailian", "deepseek")
            api_key: 要保存的 API Key

        Returns:
            是否保存成功
        """
        try:
            # 读取现有数据
            keys = self.load_all_keys()
            keys[provider_id] = api_key

            # 序列化
            data = json.dumps(keys, ensure_ascii=False).encode("utf-8")

            # 加密
            encrypted = _encrypt_data(data)

            # 写入文件
            self._keys_file.write_bytes(encrypted)

            # 如果启用机器绑定，写入机器标识
            if self.bind_machine:
                self._get_machine_id()

            return True
        except Exception as e:
            print(f"[SecureStorage] 保存失败: {e}")
            return False

    def load_api_key(self, provider_id: str) -> str:
        """
        加载指定供应商的 API Key

        Args:
            provider_id: 供应商 ID

        Returns:
            API Key 或空字符串
        """
        keys = self.load_all_keys()
        return keys.get(provider_id, "")

    def load_all_keys(self) -> dict:
        """
        加载所有保存的 API Key

        Returns:
            {provider_id: api_key} 字典
        """
        if not self._keys_file.exists():
            return {}

        # 检查机器绑定
        if not self._check_machine_binding():
            print("[SecureStorage] 检测到机器变更，加密数据无法解密")
            return {}

        try:
            encrypted = self._keys_file.read_bytes()
            decrypted = _decrypt_data(encrypted)
            return json.loads(decrypted.decode("utf-8"))
        except Exception as e:
            print(f"[SecureStorage] 解密失败: {e}")
            return {}

    def delete_api_key(self, provider_id: str) -> bool:
        """删除指定供应商的 API Key"""
        keys = self.load_all_keys()
        if provider_id in keys:
            del keys[provider_id]
            try:
                data = json.dumps(keys, ensure_ascii=False).encode("utf-8")
                encrypted = _encrypt_data(data)
                self._keys_file.write_bytes(encrypted)
                return True
            except Exception as e:
                print(f"[SecureStorage] 删除失败: {e}")
                return False
        return True

    def clear_all(self) -> bool:
        """清除所有存储的 API Key"""
        try:
            if self._keys_file.exists():
                self._keys_file.unlink()
            if self._machine_file.exists():
                self._machine_file.unlink()
            return True
        except Exception as e:
            print(f"[SecureStorage] 清除失败: {e}")
            return False

    def is_configured(self) -> bool:
        """检查是否已配置过 API Key"""
        return self._keys_file.exists() and len(self.load_all_keys()) > 0

    # ── 管理员密码管理 ──

    def get_admin_password(self) -> str:
        """
        获取管理员密码（从加密存储解密）

        Returns:
            管理员密码，如果未配置则返回空字符串
        """
        try:
            pwd_file = self._storage_dir / "admin_pwd.enc"
            if not pwd_file.exists():
                return ""
            encrypted = pwd_file.read_bytes()
            decrypted = _decrypt_data(encrypted)
            return decrypted.decode("utf-8")
        except Exception as e:
            print(f"[SecureStorage] 读取管理员密码失败: {e}")
            return ""

    def set_admin_password(self, password: str) -> bool:
        """
        安全保存管理员密码（加密存储）

        Args:
            password: 新密码

        Returns:
            是否保存成功
        """
        try:
            pwd_file = self._storage_dir / "admin_pwd.enc"
            data = password.encode("utf-8")
            encrypted = _encrypt_data(data)
            pwd_file.write_bytes(encrypted)
            return True
        except Exception as e:
            print(f"[SecureStorage] 保存管理员密码失败: {e}")
            return False

    def is_admin_configured(self) -> bool:
        """检查管理员密码是否已配置"""
        pwd_file = self._storage_dir / "admin_pwd.enc"
        return pwd_file.exists()


# ═══════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════

_storage = None


def get_storage(bind_machine: bool = False) -> SecureStorage:
    """获取全局存储实例"""
    global _storage
    if _storage is None:
        _storage = SecureStorage(bind_machine=bind_machine)
    return _storage


def save_key(provider_id: str, api_key: str, bind_machine: bool = False) -> bool:
    """便捷函数：保存 API Key"""
    return get_storage(bind_machine).save_api_key(provider_id, api_key)


def load_key(provider_id: str, bind_machine: bool = False) -> str:
    """便捷函数：加载 API Key"""
    return get_storage(bind_machine).load_api_key(provider_id)


def load_all(bind_machine: bool = False) -> dict:
    """便捷函数：加载所有 Key"""
    return get_storage(bind_machine).load_all_keys()


# ═══════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════

if __name__ == "__main__":
    if not _IS_MACOS:
        print(f"ERROR: SecureStorage requires macOS. Current OS: {_CURRENT_OS}")
        exit(1)
    if not _FERNET_AVAILABLE:
        print("ERROR: cryptography library required. Install: pip install cryptography")
        exit(1)

    storage = SecureStorage(bind_machine=False)

    print("=== Iqra Secure Storage Test (macOS Keychain) ===")

    # 保存测试
    test_key = "sk-test-123456789"
    if storage.save_api_key("openai", test_key):
        print("[OK] Save success")
    else:
        print("[FAIL] Save failed")

    # 读取测试
    loaded = storage.load_api_key("openai")
    if loaded == test_key:
        print(f"[OK] Load success: {loaded[:10]}...")
    else:
        print(f"[FAIL] Load failed: expected {test_key[:10]}..., got {loaded[:10]}...")

    # 列出所有
    all_keys = storage.load_all_keys()
    print(f"[INFO] All keys: {list(all_keys.keys())}")

    # 清理
    storage.clear_all()
    print("[OK] Test data cleaned")
```
