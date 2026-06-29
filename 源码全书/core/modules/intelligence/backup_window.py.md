# `core/modules/intelligence/backup_window.py`

> 路径：`core/modules/intelligence/backup_window.py` | 行数：257


---


```python
# -*- coding: utf-8 -*-
"""
数据备份独立窗口 — 从 account_window.py 提取
提供加密用户数据备份功能
"""
import os, json, hashlib, zipfile, io, struct
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QInputDialog, QLineEdit, QMessageBox, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class BackupWindow(QDialog):
    """数据备份独立窗口"""

    def __init__(self, parent=None, username: str = "admin", role: str = "admin"):
        super().__init__(parent)
        self._username = username
        self._role = role
        self.setWindowTitle("数据备份")
        self.setMinimumSize(460, 320)
        self.setMaximumSize(560, 400)
        self._build_ui()
        self._apply_style()

    # ═══ UI ═══

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(28, 24, 28, 24)

        # 标题
        title = QLabel("数据备份")
        title.setObjectName("dialog_title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 信息框
        info_frame = QFrame()
        info_frame.setObjectName("info_frame")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(8)
        info_layout.setContentsMargins(16, 12, 16, 12)

        self._user_label = QLabel(f"当前用户：{self._username}")
        self._user_label.setObjectName("info_label")
        info_layout.addWidget(self._user_label)

        self._desc_label = QLabel(
            "备份将加密打包以下数据：\n"
            "  成员 / 客户 / 订单 / 产品 / 财务 / 钱包 / 分销 / 保险箱 / 笔记"
        )
        self._desc_label.setObjectName("desc_label")
        self._desc_label.setWordWrap(True)
        info_layout.addWidget(self._desc_label)

        layout.addWidget(info_frame)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._backup_btn = QPushButton("创建备份")
        self._backup_btn.setObjectName("backup_btn")
        self._backup_btn.setCursor(Qt.PointingHandCursor)
        self._backup_btn.setMinimumHeight(40)
        self._backup_btn.clicked.connect(self._do_backup)
        btn_row.addWidget(self._backup_btn)

        close_btn = QPushButton("关闭")
        close_btn.setObjectName("close_btn")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a1020, stop:1 #060e1a);
                border: 1px solid rgba(0, 160, 240, 40);
                border-radius: 12px;
            }
            QLabel {
                color: #8899bb;
                font-size: 12px;
                background: transparent;
            }
            #dialog_title {
                color: #c0d0ee;
                font-size: 18px;
                font-weight: 700;
                letter-spacing: 4px;
            }
            #info_frame {
                background: rgba(8, 16, 30, 200);
                border: 1px solid rgba(0, 140, 220, 30);
                border-radius: 8px;
            }
            #info_label {
                color: #aa99cc;
                font-size: 13px;
                font-weight: 600;
            }
            #desc_label {
                color: #667799;
                font-size: 11px;
                line-height: 1.6;
            }
            #backup_btn {
                background: rgba(0, 160, 100, 40);
                color: #88eebb;
                border: 1px solid rgba(0, 200, 140, 60);
                border-radius: 20px;
                padding: 8px 28px;
                font-size: 13px;
                font-weight: 700;
            }
            #backup_btn:hover {
                background: rgba(0, 180, 120, 60);
            }
            #close_btn {
                background: rgba(40, 50, 70, 120);
                color: #8899bb;
                border: 1px solid rgba(60, 80, 120, 40);
                border-radius: 20px;
                padding: 8px 20px;
                font-size: 12px;
            }
            #close_btn:hover {
                background: rgba(60, 80, 120, 160);
            }
        """)

    # ═══ 备份逻辑 ═══

    def _do_backup(self):
        root = self._get_project_root()

        pwd = self._verify_backup_password()
        if not pwd:
            return

        default_dir = os.path.join(root, "backup")
        os.makedirs(default_dir, exist_ok=True)
        default_name = f"user_{self._username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.usrbak"
        path, _ = QFileDialog.getSaveFileName(
            self, "备份数据",
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

            QMessageBox.information(self, "备份成功", f"数据已加密备份至：\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "备份失败", f"备份出错：{e}")

    def _verify_backup_password(self):
        config = self._get_backup_config()
        stored_hash = config.get("password_hash", "")

        if not stored_hash:
            pwd, ok = QInputDialog.getText(
                self, "设置备份密码", "首次使用，请设置备份主密码（至少4位）：",
                QLineEdit.Password)
            if not ok or len(pwd) < 4:
                if ok:
                    QMessageBox.warning(self, "错误", "密码至少4位")
                return None
            confirm, ok = QInputDialog.getText(
                self, "确认", "请再次输入备份密码确认：",
                QLineEdit.Password)
            if not ok or pwd != confirm:
                if ok:
                    QMessageBox.warning(self, "错误", "两次密码不一致")
                return None
            self._save_backup_config({
                "password_hash": hashlib.sha256(pwd.encode()).hexdigest(),
                "created_at": datetime.now().isoformat()
            })
            return pwd
        else:
            for _ in range(3):
                pwd, ok = QInputDialog.getText(
                    self, "验证备份密码", "请输入备份主密码：",
                    QLineEdit.Password)
                if not ok:
                    return None
                if hashlib.sha256(pwd.encode()).hexdigest() == stored_hash:
                    return pwd
                QMessageBox.warning(self, "错误", "备份密码错误！")
            return None

    def _get_backup_config(self):
        root = self._get_project_root()
        config_dir = os.path.join(root, "config")
        config_file = os.path.join(config_dir, f"backup_{self._username}.json")
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
        config_file = os.path.join(config_dir, f"backup_{self._username}.json")
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def _get_project_root(self):
        # backup_window.py 在 management-system/modules/intelligence/ 下
        # 项目根目录在 management-system/
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

```
