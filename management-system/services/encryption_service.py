"""
加密服务
数据加密解密、安全哈希
"""

import os
import json
import base64
import hashlib
import hmac
from typing import Dict, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


class EncryptionService:
    """加密服务"""

    def __init__(self, key_file: str = "data/.encryption_key"):
        self.key_file = key_file
        self._cipher: Optional[Fernet] = None
        self._load_key()

    def _load_key(self):
        """加载密钥"""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, "rb") as f:
                    key = f.read()
                self._cipher = Fernet(key)
        except Exception:
            self._cipher = None

    def _generate_key(self, password: Optional[str] = None) -> bytes:
        """生成密钥"""
        if password:
            salt = b"one_company_salt"
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        else:
            key = Fernet.generate_key()

        # 保存密钥
        os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
        with open(self.key_file, "wb") as f:
            f.write(key)

        return key

    def init(self, password: Optional[str] = None):
        """初始化加密服务"""
        key = self._generate_key(password)
        self._cipher = Fernet(key)

    def encrypt(self, data: str) -> Optional[str]:
        """加密数据"""
        if not self._cipher:
            return None

        try:
            encrypted = self._cipher.encrypt(data.encode("utf-8"))
            return base64.urlsafe_b64encode(encrypted).decode("utf-8")
        except Exception:
            return None

    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """解密数据"""
        if not self._cipher:
            return None

        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode("utf-8"))
            decrypted = self._cipher.decrypt(decoded)
            return decrypted.decode("utf-8")
        except Exception:
            return None

    def encrypt_dict(self, data: Dict) -> Optional[str]:
        """加密字典"""
        return self.encrypt(json.dumps(data, ensure_ascii=False))

    def decrypt_dict(self, encrypted_data: str) -> Optional[Dict]:
        """解密为字典"""
        decrypted = self.decrypt(encrypted_data)
        if decrypted:
            return json.loads(decrypted)
        return None

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Dict:
        """密码哈希"""
        if salt is None:
            salt = os.urandom(16).hex()

        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,
            dklen=32,
        )

        return {
            "hash": key.hex(),
            "salt": salt,
            "algorithm": "pbkdf2_sha256",
        }

    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """验证密码"""
        computed = EncryptionService.hash_password(password, salt)
        return hmac.compare_digest(computed["hash"], stored_hash)

    @staticmethod
    def md5(data: str) -> str:
        """MD5哈希"""
        return hashlib.md5(data.encode()).hexdigest()

    @staticmethod
    def sha256(data: str) -> str:
        """SHA256哈希"""
        return hashlib.sha256(data.encode()).hexdigest()

    def is_ready(self) -> bool:
        """检查加密服务是否就绪"""
        return self._cipher is not None

