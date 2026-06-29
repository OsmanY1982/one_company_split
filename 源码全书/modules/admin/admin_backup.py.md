# `modules/admin/admin_backup.py`

> 路径：`modules/admin/admin_backup.py` | 行数：404


---


```python
# -*- coding: utf-8 -*-
"""
后台管理 - 备份设置（自动备份、云端备份、本地备份）
"""
import sys
import os
import json
import ssl
import time
from urllib.request import urlopen, Request

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QComboBox, QInputDialog
)
from PyQt5.QtCore import Qt

# 动态获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.paths import BASE_DIR as CORE_BASE_DIR, DATA_DIR, CONFIG_DIR
from config.supabase_config import SUPABASE_URL, SUPABASE_SERVICE_KEY


class AdminBackupWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_backup_history()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # ═══ 自动备份设置 ═══
        sg = QGroupBox("自动备份设置")
        s_layout = QVBoxLayout(sg)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("启用自动备份:"))
        self.auto_backup_check = QComboBox()
        self.auto_backup_check.addItems(["关闭", "开启"])
        row1.addWidget(self.auto_backup_check)
        s_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("备份频率:"))
        self.backup_frequency = QComboBox()
        self.backup_frequency.addItems(["每日", "每周"])
        row2.addWidget(self.backup_frequency)
        s_layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("保留备份数量:"))
        self.keep_count = QComboBox()
        self.keep_count.addItems(["3", "5", "7", "10", "15"])
        self.keep_count.setCurrentText("7")
        row3.addWidget(self.keep_count)
        s_layout.addLayout(row3)

        btn_save = QPushButton("保存设置")
        btn_save.setStyleSheet("background-color: #28a745; color: white; padding: 8px 20px;")
        btn_save.clicked.connect(self._save_backup_settings)
        s_layout.addWidget(btn_save)
        layout.addWidget(sg)

        # ═══ 云端备份 ═══
        cloud_group = QGroupBox("云端备份")
        c_layout = QVBoxLayout(cloud_group)
        c_layout.addWidget(QLabel("将备份上传到云端,支持随时随地恢复"))

        cloud_btn_row = QHBoxLayout()
        self.btn_cloud_backup = QPushButton("备份到云端")
        self.btn_cloud_backup.setStyleSheet("background-color: #17a2b8; color: white; padding: 10px 24px; font-weight: bold;")
        self.btn_cloud_backup.clicked.connect(self._cloud_backup)
        cloud_btn_row.addWidget(self.btn_cloud_backup)

        self.btn_cloud_restore = QPushButton("从云端恢复")
        self.btn_cloud_restore.setStyleSheet("background-color: #6610f2; color: white; padding: 10px 24px;")
        self.btn_cloud_restore.clicked.connect(self._cloud_restore)
        cloud_btn_row.addWidget(self.btn_cloud_restore)
        cloud_btn_row.addStretch()
        c_layout.addLayout(cloud_btn_row)

        c_layout.addWidget(QLabel("云端备份列表:"))
        self.cloud_backup_table = QTableWidget()
        self.cloud_backup_table.setColumnCount(4)
        self.cloud_backup_table.setHorizontalHeaderLabels(["文件名", "大小", "时间", "操作"])
        self.cloud_backup_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        c_layout.addWidget(self.cloud_backup_table)

        btn_cloud_refresh = QPushButton("刷新云端列表")
        btn_cloud_refresh.setStyleSheet("background-color: #6c757d; color: white; padding: 6px 16px;")
        btn_cloud_refresh.clicked.connect(self._load_cloud_backups)
        c_layout.addWidget(btn_cloud_refresh)
        layout.addWidget(cloud_group)

        # ═══ 本地备份历史 ═══
        hg = QGroupBox("本地备份历史")
        h_layout = QVBoxLayout(hg)
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(5)
        self.backup_table.setHorizontalHeaderLabels(["文件名", "大小", "时间", "加密", "操作"])
        self.backup_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        h_layout.addWidget(self.backup_table)
        btn_row2 = QHBoxLayout()
        btn_create = QPushButton("创建本地加密备份")
        btn_create.setStyleSheet("background-color: #28a745; color: white; padding: 6px 20px; font-weight: bold;")
        btn_create.clicked.connect(self._create_backup)
        btn_row2.addWidget(btn_create)
        btn_refresh = QPushButton("刷新列表")
        btn_refresh.clicked.connect(self._load_backup_history)
        btn_row2.addWidget(btn_refresh)
        btn_row2.addStretch()
        h_layout.addLayout(btn_row2)
        layout.addWidget(hg)
        layout.addStretch()

    def _save_backup_settings(self):
        try:
            settings = {
                "auto_backup": self.auto_backup_check.currentText() == "开启",
                "frequency": self.backup_frequency.currentText(),
                "keep_count": int(self.keep_count.currentText())
            }
            config_path = os.path.join(CONFIG_DIR, "backup_settings.json")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

            QMessageBox.information(self, "成功", "备份设置已保存!")

            if settings["auto_backup"]:
                self._create_backup()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存设置失败:{e}")

    def _load_backup_history(self):
        from core.backup import list_backups
        backups = list_backups()
        self.backup_table.setRowCount(len(backups))
        for i, b in enumerate(backups):
            self.backup_table.setItem(i, 0, QTableWidgetItem(b["name"]))
            self.backup_table.setItem(i, 1, QTableWidgetItem(f"{b['size']:.1f} MB"))
            self.backup_table.setItem(i, 2, QTableWidgetItem(b["time"]))
            enc_item = QTableWidgetItem("🔐 加密" if b.get("encrypted") else "📁 明文")
            enc_item.setForeground(Qt.darkGreen if b.get("encrypted") else Qt.gray)
            self.backup_table.setItem(i, 3, enc_item)
            btn_restore = QPushButton("恢复")
            btn_restore.setStyleSheet("background-color: #007bff; color: white; padding: 2px 8px;")
            btn_restore.clicked.connect(lambda _, n=b["name"], p=b["path"]: self._restore_backup(n, p))
            self.backup_table.setCellWidget(i, 4, btn_restore)

    def _restore_backup(self, name, path):
        reply = QMessageBox.question(self, "确认恢复",
            f"确定要恢复备份 [{name}] 吗?\n当前文件将被覆盖!",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        from core.backup import restore_backup
        ok, msg = restore_backup(path)
        if ok:
            QMessageBox.information(self, "恢复成功", msg)
        else:
            QMessageBox.warning(self, "恢复失败", msg)

    def _create_backup(self):
        from core.backup import auto_backup
        ok, msg, _ = auto_backup("后台手动备份")
        if ok:
            QMessageBox.information(self, "备份成功", msg)
        else:
            QMessageBox.warning(self, "备份失败", msg)
        self._load_backup_history()

    def _cloud_backup(self):
        """将本地加密备份上传到云端"""
        from core.backup import list_backups, BACKUP_DIR

        backups = list_backups()
        if not backups:
            reply = QMessageBox.question(
                self, "无本地备份",
                "当前没有本地备份文件。\n\n是否立即创建一个加密备份并上传?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                from core.backup import auto_backup
                ok, msg, backup_path = auto_backup("云端备份前自动创建", encrypt=True)
                if not ok:
                    QMessageBox.warning(self, "备份失败", msg)
                    return
                backups = list_backups()
            else:
                return

        latest = backups[0]
        reply = QMessageBox.question(
            self, "确认上传",
            f"将上传最新的备份:\n{latest['name']}\n大小:{latest['size']:.1f} MB\n时间:{latest['time']}\n\n继续?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return

        try:
            backup_path = latest['path']
            local_display = latest['name']
            safe_name = f"admin_backup_{int(time.time() * 1000)}.opcbak"

            with open(backup_path, 'rb') as f:
                file_data = f.read()

            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            headers = {
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": "Bearer " + SUPABASE_SERVICE_KEY,
                "Content-Type": "application/octet-stream",
                "x-upsert": "true"
            }

            req = Request(
                f"{SUPABASE_URL}/storage/v1/object/admin_backups/{safe_name}",
                data=file_data,
                headers=headers,
                method="PUT"
            )

            with urlopen(req, context=ctx, timeout=60) as resp:
                resp.read()

            QMessageBox.information(
                self, "上传成功",
                f"✅ 备份已上传到云端!\n\n文件:{local_display}\n大小:{latest['size']:.1f} MB"
            )
            self._load_cloud_backups()

        except Exception as e:
            QMessageBox.critical(self, "上传失败", f"❌ 上传失败:{str(e)[:200]}")

    def _cloud_restore(self):
        """从云端恢复备份"""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            headers = {
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": "Bearer " + SUPABASE_SERVICE_KEY,
                "Content-Type": "application/json"
            }

            req = Request(
                f"{SUPABASE_URL}/storage/v1/object/list/admin_backups",
                data=json.dumps({"prefix": ""}).encode(),
                headers=headers,
                method="POST"
            )

            with urlopen(req, context=ctx, timeout=15) as resp:
                cloud_files = json.loads(resp.read().decode())

            if not cloud_files:
                QMessageBox.warning(self, "无云端备份", "云端暂无备份文件")
                return

            file_list = "\n".join([
                f"{i+1}. {f['name']} ({f['metadata'].get('size', 0)/1024/1024:.1f} MB)"
                for i, f in enumerate(cloud_files[:10])
            ])

            choice, ok = QInputDialog.getText(
                self, "选择备份",
                f"选择要恢复的备份(输入编号):\n\n{file_list}"
            )

            if not ok or not choice:
                return

            try:
                idx = int(choice) - 1
                if idx < 0 or idx >= len(cloud_files):
                    raise ValueError()
            except ValueError:
                QMessageBox.warning(self, "无效选择", "请输入有效的编号")
                return

            selected = cloud_files[idx]
            file_name = selected['name']

            req = Request(
                f"{SUPABASE_URL}/storage/v1/object/admin_backups/{file_name}",
                headers=headers,
                method="GET"
            )

            with urlopen(req, context=ctx, timeout=60) as resp:
                backup_data = resp.read()

            temp_path = os.path.join(CORE_BASE_DIR, "backup", f"cloud_{file_name}")
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            with open(temp_path, 'wb') as f:
                f.write(backup_data)

            from core.backup import restore_backup
            ok, msg = restore_backup(temp_path)

            if ok:
                QMessageBox.information(self, "恢复成功", f"✅ {msg}")
            else:
                QMessageBox.warning(self, "恢复失败", msg)

        except Exception as e:
            QMessageBox.critical(self, "恢复失败", f"❌ 从云端恢复失败:{str(e)[:200]}")

    def _load_cloud_backups(self):
        """加载云端备份列表"""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            headers = {
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": "Bearer " + SUPABASE_SERVICE_KEY,
                "Content-Type": "application/json"
            }

            req = Request(
                f"{SUPABASE_URL}/storage/v1/object/list/admin_backups",
                data=json.dumps({"prefix": ""}).encode(),
                headers=headers,
                method="POST"
            )

            with urlopen(req, context=ctx, timeout=15) as resp:
                cloud_files = json.loads(resp.read().decode())

            self.cloud_backup_table.setRowCount(len(cloud_files))
            for i, f in enumerate(cloud_files):
                self.cloud_backup_table.setItem(i, 0, QTableWidgetItem(f['name']))
                size_mb = f['metadata'].get('size', 0) / 1024 / 1024
                self.cloud_backup_table.setItem(i, 1, QTableWidgetItem(f"{size_mb:.1f} MB"))
                created_at = f.get('created_at', '')
                if created_at:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        created_at = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        pass
                self.cloud_backup_table.setItem(i, 2, QTableWidgetItem(created_at))

                btn_download = QPushButton("下载")
                btn_download.setStyleSheet("background-color: #007bff; color: white; padding: 2px 8px;")
                btn_download.clicked.connect(lambda _, name=f['name']: self._download_cloud_backup(name))
                self.cloud_backup_table.setCellWidget(i, 3, btn_download)

        except Exception as e:
            print(f"加载云端备份列表失败:{e}")
            self.cloud_backup_table.setRowCount(1)
            self.cloud_backup_table.setItem(0, 0, QTableWidgetItem("无法连接云端"))
            self.cloud_backup_table.setItem(0, 1, QTableWidgetItem(str(e)[:50]))

    def _download_cloud_backup(self, file_name):
        """下载单个云端备份"""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            headers = {
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": "Bearer " + SUPABASE_SERVICE_KEY
            }

            req = Request(
                f"{SUPABASE_URL}/storage/v1/object/admin_backups/{file_name}",
                headers=headers,
                method="GET"
            )

            with urlopen(req, context=ctx, timeout=60) as resp:
                backup_data = resp.read()

            from core.backup import BACKUP_DIR
            local_path = BACKUP_DIR / f"cloud_{file_name}"
            with open(local_path, 'wb') as f:
                f.write(backup_data)

            QMessageBox.information(
                self, "下载成功",
                f"✅ 备份已下载到本地:\n{local_path}"
            )
            self._load_backup_history()

        except Exception as e:
            QMessageBox.critical(self, "下载失败", f"❌ 下载失败:{str(e)[:200]}")

```
