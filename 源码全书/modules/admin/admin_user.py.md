# `modules/admin/admin_user.py`

> 路径：`modules/admin/admin_user.py` | 行数：420


---


```python
# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import sqlite3
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QLineEdit, QComboBox, QDialog, QFormLayout, QDialogButtonBox,
    QGroupBox, QInputDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from core.paths import DATA_DIR, CONFIG_DIR
DB_FILE = os.path.join(DATA_DIR, "users.db")
LICENSE_DIR = CONFIG_DIR


class AdminUserWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.load_users()

    def _build_ui(self):
        self.setStyleSheet("background-color: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # 顶部标题 + 统计
        top = QHBoxLayout()
        title = QLabel("👥 用户管理")
        title.setFont(QFont("PingFang SC", 16, QFont.Bold))
        title.setStyleSheet("color: #90cdf4;")
        top.addWidget(title)
        top.addStretch()
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #a0aec0; font-size: 12px;")
        top.addWidget(self.stats_label)
        layout.addLayout(top)

        # 搜索栏
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索用户名...")
        self.search_input.textChanged.connect(self.load_users)
        search_row.addWidget(self.search_input)

        self.filter_role = QComboBox()
        self.filter_role.addItems(["全部角色", "user", "admin"])
        self.filter_role.currentTextChanged.connect(self.load_users)
        search_row.addWidget(self.filter_role)

        self.filter_license = QComboBox()
        self.filter_license.addItems(["全部状态", "vip", "pro", "trial", "未激活"])
        self.filter_license.currentTextChanged.connect(self.load_users)
        search_row.addWidget(self.filter_license)

        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.load_users)
        search_row.addWidget(btn_refresh)
        layout.addLayout(search_row)

        # 用户列表
        list_group = QGroupBox("用户列表")
        list_layout = QVBoxLayout(list_group)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["用户名", "角色", "激活状态", "注册时间", "最后更新", "密码", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 220)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        list_layout.addWidget(self.table)

        # 操作按钮行
        btn_row = QHBoxLayout()
        btn_add = QPushButton("➕ 新增用户")
        btn_add.setObjectName("green")
        btn_add.clicked.connect(self.add_user)
        btn_row.addWidget(btn_add)

        btn_export = QPushButton("📤 导出列表")
        btn_export.clicked.connect(self.export_users)
        btn_row.addWidget(btn_export)

        btn_row.addStretch()

        self.count_label = QLabel("共 0 位用户")
        self.count_label.setStyleSheet("color: #a0aec0;")
        btn_row.addWidget(self.count_label)
        list_layout.addLayout(btn_row)

        layout.addWidget(list_group)

    def load_users(self):
        keyword = self.search_input.text().strip().lower()
        role_filter = self.filter_role.currentText()
        license_filter = self.filter_license.currentText()

        # === 第一步：从云端拉取并同步到本地 ===
        self._sync_cloud_to_local()

        # === 第二步：从本地读取（已含云端数据）===
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT u.username, u.role, u.license_type, u.created_at, u.updated_at, "
                "u.password, COALESCE(m.membership_type, ''), m.expires_at "
                "FROM users u "
                "LEFT JOIN user_memberships m ON u.username = m.username "
                "ORDER BY u.created_at DESC"
            )
            rows = cursor.fetchall()
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载用户失败：{e}")
            return

        # 过滤
        filtered = []
        for row in rows:
            username, role, license_type, created_at, updated_at, pwd_status, mem_type, expires = row
            lic = mem_type or license_type or "未激活"

            # 管理员账号不在这里管理（管理员登录用的是 config/admin.json，不是 users.db）
            if role == 'admin':
                continue

            if keyword and keyword not in (username or '').lower():
                continue
            if role_filter != "全部角色" and role != role_filter:
                continue
            if license_filter != "全部状态":
                if license_filter == "未激活" and lic not in ["未激活", None, ""]:
                    continue
                elif license_filter != "未激活" and lic != license_filter:
                    continue

            filtered.append((username, role, lic, created_at, updated_at, pwd_status, expires))

        self.table.setRowCount(len(filtered))

        # 统计
        total = len(rows)
        vip_count = sum(1 for r in rows if (r[6] or r[2] or '') == 'vip')
        pro_count = sum(1 for r in rows if (r[6] or r[2] or '') == 'pro')
        self.stats_label.setText(f"总计 {total} 人 | VIP {vip_count} | PRO {pro_count}")
        self.count_label.setText(f"显示 {len(filtered)} / {total} 位用户")

        # 激活状态颜色
        lic_colors = {
            'vip': '#d69e2e', 'pro': '#38a169',
            'trial': '#3182ce', '未激活': '#718096'
        }

        for i, (username, role, lic, created_at, updated_at, pwd_status, expires) in enumerate(filtered):
            self.table.setItem(i, 0, QTableWidgetItem(username or ''))

            role_item = QTableWidgetItem(role or 'user')
            if role == 'admin':
                role_item.setForeground(QColor('#d69e2e'))
            self.table.setItem(i, 1, role_item)

            lic_item = QTableWidgetItem(lic)
            lic_item.setForeground(QColor(lic_colors.get(lic, '#718096')))
            self.table.setItem(i, 2, lic_item)

            self.table.setItem(i, 3, QTableWidgetItem(str(created_at or '')[:16]))
            self.table.setItem(i, 4, QTableWidgetItem(str(updated_at or '')[:16]))
            self.table.setItem(i, 5, QTableWidgetItem(pwd_status))

            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)

            btn_reset_pwd = QPushButton("重置密码")
            btn_reset_pwd.setObjectName("warn")
            btn_reset_pwd.setFixedHeight(26)
            btn_reset_pwd.clicked.connect(lambda _, u=username: self.reset_password(u))
            btn_layout.addWidget(btn_reset_pwd)

            btn_del = QPushButton("删除")
            btn_del.setObjectName("danger")
            btn_del.setFixedHeight(26)
            btn_del.clicked.connect(lambda _, u=username: self.delete_user(u))
            btn_layout.addWidget(btn_del)

            self.table.setCellWidget(i, 6, btn_widget)

    def _sync_cloud_to_local(self):
        """从 Supabase public.users 拉取所有用户 → 写入本地 users.db（云端优先）"""
        try:
            from core.supabase_client import _request
            ok, cloud_users = _request("GET", "/rest/v1/users?select=*", service_key=True)
            if not ok or not isinstance(cloud_users, list):
                return  # 云端不可用，静默跳过，不影响本地展示

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for cu in cloud_users:
                uname = cu.get("username", "")
                if not uname:
                    continue
                cursor.execute("SELECT id FROM users WHERE username=?", (uname,))
                exists = cursor.fetchone()
                if exists:
                    # 已存在 → 更新（云端数据优先）
                    cursor.execute(
                        "UPDATE users SET user_id=?, password=?, role=?, license_type=?, "
                        "created_at=COALESCE(?, created_at), updated_at=? WHERE username=?",
                        (cu.get("user_id", ""), cu.get("password", ""),
                         cu.get("role", "user"), cu.get("license_type", ""),
                         cu.get("created_at", now), now, uname)
                    )
                else:
                    # 云端有、本地没有 → 插入本地
                    cursor.execute(
                        "INSERT INTO users (username, user_id, role, license_type, password, created_at, updated_at) "
                        "VALUES (?,?,?,?,?,?,?)",
                        (uname, cu.get("user_id", ""), cu.get("role", "user"),
                         cu.get("license_type", ""), cu.get("password", ""),
                         cu.get("created_at", now), now)
                    )
            conn.commit()
            conn.close()
        except Exception:
            pass  # 云端同步失败不影响本地展示

    def add_user(self):
        from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
        dlg = QDialog(self)
        dlg.setWindowTitle("新增用户")
        dlg.setMinimumWidth(350)
        dlg.setStyleSheet("QDialog { background: #1a1a2e; color: #e2e8f0; } "
                         "QLabel { color: #e2e8f0; } "
                         "QLineEdit { background: #2d3748; border: 1px solid #4a5568; "
                         "border-radius: 6px; padding: 6px; color: #e2e8f0; } "
                         "QPushButton { background: #2b6cb0; color: white; border: none; "
                         "border-radius: 6px; padding: 8px 16px; }")
        layout = QFormLayout(dlg)

        username_input = QLineEdit()
        layout.addRow("用户名：", username_input)

        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.Password)
        layout.addRow("密码：", password_input)

        role_combo = QComboBox()
        role_combo.addItems(["user", "admin"])
        role_combo.setStyleSheet("background: #2d3748; color: #e2e8f0; padding: 6px;")
        layout.addRow("角色：", role_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addRow(buttons)

        if dlg.exec_() == QDialog.Accepted:
            username = username_input.text().strip()
            password = password_input.text().strip()
            role = role_combo.currentText()

            if not username or not password:
                QMessageBox.warning(self, "错误", "用户名和密码不能为空")
                return

            try:
                # 宇宙版明文存储密码，无需哈希

                # 1. 云端注册（写 public.users 表，service_key 绕过 RLS）
                cloud_ok = True
                cloud_msg = ""
                try:
                    from core.supabase_client import _request
                    import uuid
                    payload = {
                        "username": username,
                        "user_id": str(uuid.uuid4()),
                        "password": password,
                        "role": role,
                    }
                    ok, result = _request("POST", "/rest/v1/users", payload, service_key=True)
                    if not ok:
                        cloud_ok = False
                        cloud_msg = str(result)
                except Exception as cloud_err:
                    cloud_ok = False
                    cloud_msg = str(cloud_err)

                # 2. 本地写入（明文存储，与宇宙版一致）
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    "INSERT INTO users (username, password, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (username, password, role, now, now)
                )
                conn.commit()
                conn.close()

                if cloud_ok:
                    QMessageBox.information(self, "成功", f"用户 {username} 已创建（本地+云端同步）")
                else:
                    QMessageBox.warning(self, "部分成功", f"用户 {username} 已本地创建，但云端同步失败：{cloud_msg}")
                self.load_users()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "错误", "用户名已存在")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建失败：{e}")

    def reset_password(self, username):
        from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
        new_pwd, ok = QInputDialog.getText(
            self, "重置密码", f"为 {username} 设置新密码（至少6位）：",
            QLineEdit.Password)
        if not ok or not new_pwd:
            return

        from modules.auth.auth_service import AuthService
        auth = AuthService()
        ok2, msg = auth.admin_reset_password(username, new_pwd)
        if ok2:
            QMessageBox.information(self, "成功", msg)
            self.load_users()
        else:
            QMessageBox.warning(self, "失败", msg)

    def delete_user(self, username):
        from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
        if username == 'admin':
            QMessageBox.warning(self, "禁止", "不能删除管理员账号")
            return

        if QMessageBox.Yes != QMessageBox.question(
            self, "确认删除",
            f"⚠️ 删除用户 {username}？\n\n此操作将：\n• 删除本地数据\n• 删除云端账号（用户无法再登录）\n• 清除所有激活设备\n\n删除后用户需重新注册并激活。",
            QMessageBox.Yes | QMessageBox.No
        ):
            return

        try:
            # === 1. 云端删除（关键：删除后用户无法登录）===
            from core.supabase_client import _request

            # 删除云端用户记录（导致登录验证失败）
            _request("DELETE", f"/rest/v1/users?username=eq.{username}", service_key=True)

            # 清除该用户所有设备绑定（踢掉所有活跃设备）
            _request("PATCH", f"/rest/v1/device_bindings?username=eq.{username}",
                    {"is_current": False}, service_key=True)

            # 删除云端会员记录
            _request("DELETE", f"/rest/v1/user_memberships?username=eq.{username}",
                    service_key=True)

            # 删除云端激活码使用记录
            _request("PATCH", f"/rest/v1/activation_codes?bound_account=eq.{username}",
                    {"status": "unused", "bound_account": None, "bound_machine": None, "used_at": None},
                    service_key=True)

            # === 2. 本地删除 ===
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username=?", (username,))
            cursor.execute("DELETE FROM user_memberships WHERE username=?", (username,))
            conn.commit()
            conn.close()

            # 删除本地许可证文件
            lic_file = os.path.join(LICENSE_DIR, f"license_{username}.json")
            if os.path.exists(lic_file):
                os.remove(lic_file)

            QMessageBox.information(self, "✅ 删除成功",
                f"用户 {username} 已完全删除\n云端和本地数据均已清除\n该用户无法再登录，需重新注册")
            self.load_users()

        except Exception as e:
            QMessageBox.critical(self, "❌ 删除失败", f"删除过程中出错：{e}\n\n本地数据已删除，但云端可能残留。请手动检查云端。")

    def export_users(self):
        from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
        from PyQt5.QtWidgets import QFileDialog
        import csv
        path, _ = QFileDialog.getSaveFileName(self, "导出用户列表", "", "CSV (*.csv)")
        if not path:
            return
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, role, license_type, created_at FROM users ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
            conn.close()

            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["用户名", "角色", "激活状态", "注册时间"])
                for row in rows:
                    writer.writerow(row)

            QMessageBox.information(self, "成功", f"已导出 {len(rows)} 条记录")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：{e}")

```
