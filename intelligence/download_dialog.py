# -*- coding: utf-8 -*-
"""
下载链接窗口
从云端 version.json 获取最新下载地址并展示，与管理员后台发布的内容完全同步。
"""

import os
import webbrowser

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFrame, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor


class DownloadDialog(QDialog):
    """APP 下载链接窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._links = {}  # {(platform, channel): url}
        self._init_ui()
        self.setStyleSheet(self._base_style())

    def load_from_cloud(self, cloud_data: dict, current_version: str):
        """
        从云端数据填充窗口
        cloud_data: UpdateChecker.get_latest() 的返回结果
        """
        if not cloud_data:
            self._show_error()
            return

        latest = cloud_data.get("latest_version", "未知")
        notes = cloud_data.get("release_notes", "")
        downloads = cloud_data.get("downloads", {})

        # 版本信息
        self._ver_label.setText(f"云端最新版本：{latest}    |    当前版本：{current_version}")

        if notes.strip():
            self._changelog_text.setText(notes.strip())
        else:
            self._changelog_text.setText("暂无更新说明")

        # 填下载链接
        self._fill_links(downloads)

    def load_from_url(self, current_version: str):
        """直接从 Supabase 拉取并展示"""
        try:
            from core.supabase_client import UpdateChecker
            data = UpdateChecker.get_latest()
            self.load_from_cloud(data, current_version)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"获取下载信息失败：{str(e)[:200]}")

    # ── 内部方法 ──────────────────────────────────────────

    def _init_ui(self):
        self.setWindowTitle("APP 下载中心")
        self.setMinimumSize(520, 420)
        self.setMaximumSize(640, 560)

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(24, 20, 24, 24)

        # ── 标题 ──
        title = QLabel("📥 一人公司管理系统 — 下载中心")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("dlg_title")
        root.addWidget(title)

        # ── 版本信息 ──
        ver_box = QGroupBox("版本信息")
        vlay = QVBoxLayout(ver_box)
        vlay.setSpacing(6)

        self._ver_label = QLabel()
        self._ver_label.setObjectName("ver_info")
        vlay.addWidget(self._ver_label)

        self._changelog_text = QLabel()
        self._changelog_text.setWordWrap(True)
        self._changelog_text.setObjectName("changelog")
        vlay.addWidget(self._changelog_text)

        root.addWidget(ver_box)

        # ── 电脑版 ──
        self._win_box = self._build_platform_group("💻 电脑版 (Windows)")
        root.addWidget(self._win_box)

        # ── 手机版 ──
        self._and_box = self._build_platform_group("📱 手机版 (Android)")
        root.addWidget(self._and_box)

        root.addStretch()

    def _build_platform_group(self, title: str) -> QGroupBox:
        gb = QGroupBox(title)
        lay = QHBoxLayout(gb)
        lay.setSpacing(12)

        btn_baidu = QPushButton("百度网盘")
        btn_baidu.setObjectName(f"btn_baidu_{hash(title) % 100}")
        btn_baidu.setMinimumHeight(40)
        btn_baidu.setCursor(Qt.PointingHandCursor)
        btn_baidu.clicked.connect(lambda: self._open_link(title, "baidu"))
        btn_baidu.setToolTip("跳转到百度网盘下载页面")

        btn_gitee = QPushButton("Gitee 直链")
        btn_gitee.setObjectName(f"btn_gitee_{hash(title) % 100}")
        btn_gitee.setMinimumHeight(40)
        btn_gitee.setCursor(Qt.PointingHandCursor)
        btn_gitee.clicked.connect(lambda: self._open_link(title, "gitee"))
        btn_gitee.setToolTip("Gitee 高速下载（推荐）")

        lay.addWidget(btn_baidu)
        lay.addWidget(btn_gitee)

        # store refs
        if "Windows" in title:
            self._btn_win_baidu, self._btn_win_gitee = btn_baidu, btn_gitee
        else:
            self._btn_and_baidu, self._btn_and_gitee = btn_baidu, btn_gitee

        return gb

    def _fill_links(self, downloads: dict):
        """将云端下载链接填入按钮"""
        platforms = {
            "windows": {"box": self._win_box, "baidu": self._btn_win_baidu, "gitee": self._btn_win_gitee},
            "android": {"box": self._and_box, "baidu": self._btn_and_baidu, "gitee": self._btn_and_gitee},
        }

        for key, widgets in platforms.items():
            plat = downloads.get(key, {})
            bd = plat.get("baidu", "")
            gitee = plat.get("gitee", "")

            self._links[("baidu", key)] = bd
            self._links[("gitee", key)] = gitee

            if bd:
                widgets["baidu"].setEnabled(True)
                widgets["baidu"].setToolTip(bd[:80])
            else:
                widgets["baidu"].setEnabled(False)
                widgets["baidu"].setText("百度网盘 (暂无)")

            if gitee:
                widgets["gitee"].setEnabled(True)
                widgets["gitee"].setToolTip(gitee[:80])
            else:
                widgets["gitee"].setEnabled(False)
                widgets["gitee"].setText("Gitee (暂无)")

    def _open_link(self, group_title: str, channel: str):
        """打开下载链接"""
        plat = "windows" if "Windows" in group_title else "android"
        url = self._links.get((channel, plat), "")

        if not url:
            QMessageBox.information(self, "提示", "此下载地址暂未设置，请联系管理员。")
            return

        try:
            webbrowser.open(url)
        except Exception as e:
            QMessageBox.warning(self, "打开失败", f"无法打开链接：{str(e)[:150]}")

    def _show_error(self):
        self._ver_label.setText("❌ 无法连接云端，请稍后重试")
        self._changelog_text.setText("")
        self._btn_win_baidu.setEnabled(False)
        self._btn_win_gitee.setEnabled(False)
        self._btn_and_baidu.setEnabled(False)
        self._btn_and_gitee.setEnabled(False)

    def _base_style(self) -> str:
        return """
            QDialog {
                background-color: #f5f6fa;
            }
            QLabel#dlg_title {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 6px;
            }
            QLabel#ver_info {
                font-size: 13px;
                color: #34495e;
                padding: 2px 0px;
            }
            QLabel#changelog {
                font-size: 12px;
                color: #7f8c8d;
                background-color: #ecf0f1;
                border-radius: 6px;
                padding: 10px;
            }
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                color: #2c3e50;
                border: 1px solid #dcdde1;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """
