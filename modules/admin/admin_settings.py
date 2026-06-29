# -*- coding: utf-8 -*-
"""
后台管理 - 系统设置（版本发布）
"""
import sys
import os
import json
import ssl
from datetime import datetime
from urllib.request import urlopen, Request

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QMessageBox,
    QGroupBox
)
from PyQt5.QtCore import QTimer

# 动态获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from config.supabase_config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from core.operation_log import log_action


class AdminSettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        # 自动加载当前云端版本
        QTimer.singleShot(500, self._load_cloud_version)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── 基本设置 ──
        group = QGroupBox("基本设置")
        g_layout = QGridLayout(group)

        g_layout.addWidget(QLabel("系统名称:"), 0, 0)
        name_input = QLineEdit()
        name_input.setText("一人公司管理系统")
        g_layout.addWidget(name_input, 0, 1)

        g_layout.addWidget(QLabel("版本:"), 1, 0)
        version_label = QLabel("v2.0.0")
        g_layout.addWidget(version_label, 1, 1)

        g_layout.addWidget(QLabel("数据目录:"), 2, 0)
        data_label = QLabel(os.path.join(BASE_DIR, "data"))
        g_layout.addWidget(data_label, 2, 1)

        layout.addWidget(group)

        # ── 版本发布设置 ──
        ver_group = QGroupBox("版本发布(更新云端版本信息)")
        v_layout = QGridLayout(ver_group)

        v_layout.addWidget(QLabel("最新版本号:"), 0, 0)
        self.ver_version = QLineEdit()
        self.ver_version.setPlaceholderText("如: 2.1.0")
        v_layout.addWidget(self.ver_version, 0, 1)

        v_layout.addWidget(QLabel("更新说明:"), 1, 0)
        self.ver_notes = QTextEdit()
        self.ver_notes.setMaximumHeight(60)
        self.ver_notes.setPlaceholderText("每行一条更新内容")
        v_layout.addWidget(self.ver_notes, 1, 1)

        # Windows 下载链接
        v_layout.addWidget(QLabel("电脑版 百度网盘:"), 2, 0)
        self.ver_win_baidu = QLineEdit()
        self.ver_win_baidu.setPlaceholderText("百度网盘链接")
        v_layout.addWidget(self.ver_win_baidu, 2, 1)

        v_layout.addWidget(QLabel("电脑版 Gitee:"), 3, 0)
        self.ver_win_gitee = QLineEdit()
        self.ver_win_gitee.setPlaceholderText("Gitee Release 链接")
        v_layout.addWidget(self.ver_win_gitee, 3, 1)

        # Android 下载链接
        v_layout.addWidget(QLabel("手机版 百度网盘:"), 4, 0)
        self.ver_android_baidu = QLineEdit()
        self.ver_android_baidu.setPlaceholderText("百度网盘链接")
        v_layout.addWidget(self.ver_android_baidu, 4, 1)

        v_layout.addWidget(QLabel("手机版 Gitee:"), 5, 0)
        self.ver_android_gitee = QLineEdit()
        self.ver_android_gitee.setPlaceholderText("Gitee Release 链接")
        v_layout.addWidget(self.ver_android_gitee, 5, 1)

        btn_row = QHBoxLayout()
        btn_load = QPushButton("读取当前版本")
        btn_load.setStyleSheet("background-color: #6c757d; color: white; padding: 6px 16px;")
        btn_load.clicked.connect(self._load_cloud_version)
        btn_row.addWidget(btn_load)

        btn_publish = QPushButton("发布新版本")
        btn_publish.setStyleSheet("background-color: #28a745; color: white; padding: 6px 16px; font-weight: bold;")
        btn_publish.clicked.connect(self._publish_version)
        btn_row.addWidget(btn_publish)
        btn_row.addStretch()
        v_layout.addLayout(btn_row, 6, 0, 1, 2)

        layout.addWidget(ver_group)

        btn_save = QPushButton("保存设置")
        btn_save.setStyleSheet("background-color: #28a745; color: white; padding: 8px 20px;")
        btn_save.clicked.connect(lambda: QMessageBox.information(self, "成功", "设置已保存!"))
        layout.addWidget(btn_save)
        layout.addStretch()

    def _load_cloud_version(self):
        try:
            from core.supabase_client import UpdateChecker
            info = UpdateChecker.get_latest()
            if info:
                self.ver_version.setText(info.get("latest_version", ""))
                self.ver_notes.setPlainText(info.get("release_notes", ""))
                downloads = info.get("downloads", {})
                win = downloads.get("windows", {})
                android = downloads.get("android", {})
                self.ver_win_baidu.setText(win.get("baidu", ""))
                self.ver_win_gitee.setText(win.get("gitee", ""))
                self.ver_android_baidu.setText(android.get("baidu", ""))
                self.ver_android_gitee.setText(android.get("gitee", ""))
            else:
                QMessageBox.warning(self, "读取失败", "无法连接云端")
        except Exception as e:
            QMessageBox.warning(self, "读取失败", str(e)[:100])

    def _publish_version(self):
        version = self.ver_version.text().strip()
        if not version:
            QMessageBox.warning(self, "发布失败", "版本号不能为空")
            return

        from PyQt5.QtWidgets import QMessageBox as MB
        if MB.Yes != MB.question(
            self, "确认发布",
            f"确定发布版本 v{version} 到云端?\n所有用户将收到更新提示。",
            MB.Yes | MB.No, MB.No
        ):
            return

        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            version_info = {
                "latest_version": version.lstrip("vV"),
                "release_notes": self.ver_notes.toPlainText().strip(),
                "released_at": datetime.now().strftime("%Y-%m-%d"),
                "min_version": "1.0.0",
                "downloads": {
                    "windows": {
                        "name": "电脑版 (Windows)",
                        "baidu": self.ver_win_baidu.text().strip(),
                        "gitee": self.ver_win_gitee.text().strip()
                    },
                    "android": {
                        "name": "手机版 (Android)",
                        "baidu": self.ver_android_baidu.text().strip(),
                        "gitee": self.ver_android_gitee.text().strip()
                    }
                }
            }

            headers = {
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": "Bearer " + SUPABASE_SERVICE_KEY,
                "Content-Type": "application/json"
            }
            req = Request(
                SUPABASE_URL + "/storage/v1/object/updates/version.json",
                data=json.dumps(version_info, ensure_ascii=False, indent=2).encode("utf-8"),
                headers=headers,
                method="PUT"
            )
            with urlopen(req, context=ctx, timeout=15) as resp:
                resp.read()

            QMessageBox.information(self, "发布成功", f"版本 v{version} 已发布到云端!\n用户点击'检查更新'即可收到提示。")
            try:
                log_action("system", "版本发布", "setting", f"发布版本 v{version}")
            except Exception:
                pass
        except Exception as e:
            QMessageBox.critical(self, "发布失败", f"发布失败:{str(e)[:100]}")
