# `core/modules/dashboard/dashboard_window/_account_tools.py`

> 路径：`core/modules/dashboard/dashboard_window/_account_tools.py` | 行数：204


---


```python
"""
账号与安全工具 — _AccountToolsMixin
包含 _show_account_tools、_get_project_root、_get_backup_config、
_save_backup_config、_verify_backup_password、_user_backup
"""
import os
import json
import hashlib
import zipfile
import io
import struct
import traceback
from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QInputDialog, QLineEdit, QFileDialog
)
from PyQt5.QtCore import Qt


class _AccountToolsMixin:
    """账号与安全：激活、升级、备份"""

    def _show_account_tools(self):
        """弹出账号与安全工具面板"""
        dlg = QDialog(self)
        dlg.setWindowTitle("账号与安全")
        dlg.setMinimumWidth(420)
        dlg.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #080e1a, stop:1 #0c1424);
            }
        """)

        layout = QVBoxLayout(dlg)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("账号与安全")
        title.setStyleSheet("color: #ddeeff; font-size: 18px; font-weight: 700; letter-spacing: 3px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        _btn_style = """
            QPushButton {{
                background: {bg};
                color: #e0e0f0;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background: {hover}; }}
            QPushButton:pressed {{ background: {pressed}; }}
        """

        # 1. 激活许可证
        btn1 = QPushButton("激活许可证")
        btn1.setStyleSheet(_btn_style.format(bg="#d69e2e", hover="#c59a2e", pressed="#b8860b"))
        btn1.clicked.connect(lambda: (dlg.close(), self._open_activation()))
        layout.addWidget(btn1)

        # 2. 升级会员
        btn2 = QPushButton("升级会员")
        btn2.setStyleSheet(_btn_style.format(bg="#7c3aed", hover="#6d28d9", pressed="#5b21b6"))
        btn2.clicked.connect(lambda: (dlg.close(), self._open_upgrade()))
        layout.addWidget(btn2)

        # 3. 检查更新
        btn3 = QPushButton("检查更新")
        btn3.setStyleSheet(_btn_style.format(bg="#2563eb", hover="#1d4ed8", pressed="#1e40af"))
        btn3.clicked.connect(lambda: (dlg.close(), self._open_update_check()))
        layout.addWidget(btn3)

        # 4. 数据备份
        btn4 = QPushButton("数据备份")
        btn4.setStyleSheet(_btn_style.format(bg="#059669", hover="#047857", pressed="#065f46"))
        btn4.clicked.connect(lambda: self._user_backup(dlg))
        layout.addWidget(btn4)

        dlg.exec_()

    def _get_project_root(self):
        """获取宇宙版项目根目录"""
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def _get_backup_config(self):
        root = self._get_project_root()
        config_dir = os.path.join(root, "config")
        username = self._membership_info.get("username", "admin")
        config_file = os.path.join(config_dir, f"backup_{username}.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_backup_config(self, config: dict):
        root = self._get_project_root()
        config_dir = os.path.join(root, "config")
        username = self._membership_info.get("username", "admin")
        config_file = os.path.join(config_dir, f"backup_{username}.json")
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def _verify_backup_password(self, parent=None):
        """验证或首次设置备份密码，返回密码字符串或 None"""
        config = self._get_backup_config()
        stored_hash = config.get("password_hash", "")

        if not stored_hash:
            pwd, ok = QInputDialog.getText(
                parent or self, "设置备份密码", "首次使用，请设置备份主密码（至少4位）：",
                QLineEdit.Password)
            if not ok or len(pwd) < 4:
                if ok:
                    QMessageBox.warning(parent or self, "错误", "密码至少4位")
                return None
            confirm, ok = QInputDialog.getText(
                parent or self, "确认", "请再次输入备份密码确认：",
                QLineEdit.Password)
            if not ok or pwd != confirm:
                if ok:
                    QMessageBox.warning(parent or self, "错误", "两次密码不一致")
                return None
            self._save_backup_config({
                "password_hash": hashlib.sha256(pwd.encode()).hexdigest(),
                "created_at": datetime.now().isoformat()
            })
            return pwd
        else:
            for _ in range(3):
                pwd, ok = QInputDialog.getText(
                    parent or self, "验证备份密码", "请输入备份主密码：",
                    QLineEdit.Password)
                if not ok:
                    return None
                if hashlib.sha256(pwd.encode()).hexdigest() == stored_hash:
                    return pwd
                QMessageBox.warning(parent or self, "错误", "备份密码错误！")
            return None

    def _user_backup(self, parent=None):
        """加密备份用户数据"""
        root = self._get_project_root()
        username = self._membership_info.get("username", "admin")

        pwd = self._verify_backup_password(parent)
        if not pwd:
            return

        default_dir = os.path.join(root, "backup")
        os.makedirs(default_dir, exist_ok=True)
        default_name = f"user_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.usrbak"
        path, _ = QFileDialog.getSaveFileName(
            parent or self, "备份数据",
            os.path.join(default_dir, default_name),
            "加密备份 (*.usrbak)"
        )
        if not path:
            return

        try:
            user_data_files = [
                "data/member.db", "data/customer.db",
                "data/order.db", "data/product.db",
                "data/finance.db", "data/wallet.db",
                "data/distribution.db", "data/vault.enc",
                "data/notes/",
            ]

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in user_data_files:
                    full_path = os.path.join(root, f)
                    if os.path.isfile(full_path):
                        zf.write(full_path, f)
                    elif os.path.isdir(full_path):
                        for dr, _, files in os.walk(full_path):
                            for file in files:
                                fp = os.path.join(dr, file)
                                arcname = os.path.relpath(fp, root)
                                zf.write(fp, arcname)
            zip_data = buf.getvalue()

            MAGIC = b"USRBAK_V1\x00"
            salt = os.urandom(16)
            key = hashlib.pbkdf2_hmac("sha256", pwd.encode(), salt, 100000)
            enc = bytes([b ^ key[i % len(key)] for i, b in enumerate(zip_data)])
            data_len = struct.pack(">I", len(enc))

            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(MAGIC + salt + data_len + enc)

            QMessageBox.information(parent or self, "备份成功", f"数据已加密备份至：\n{path}")
        except Exception as e:
            QMessageBox.critical(parent or self, "备份失败", f"备份出错：{e}")

```
