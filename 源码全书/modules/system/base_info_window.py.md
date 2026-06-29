# `modules/system/base_info_window.py`

> 路径：`modules/system/base_info_window.py` | 行数：269


---


```python
"""
系统设置 · 基础信息配置 + 版本发布
对标桌面版 AdminSettingsWidget — 本地 JSON 替代 Supabase
"""
import os, json, shutil
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QMessageBox,
    QGroupBox, QComboBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
CONFIG_DIR = os.path.join(_PROJECT_ROOT, "config")
VERSION_FILE = os.path.join(CONFIG_DIR, "version.json")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "system_settings.json")
VERSION_TXT = os.path.join(_PROJECT_ROOT, "version.txt")

os.makedirs(CONFIG_DIR, exist_ok=True)


def _read_version_file():
    """读取当前版本号"""
    if os.path.exists(VERSION_TXT):
        with open(VERSION_TXT, "r", encoding="utf-8") as f:
            return f.readline().strip()
    return "1.0.0"


def _read_version_json():
    """读取云端版本配置（本地 JSON）"""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "latest_version": _read_version_file(),
        "release_notes": "",
        "released_at": "",
        "min_version": "1.0.0",
        "downloads": {
            "windows": {"name": "电脑版 (Windows)", "baidu": "", "gitee": ""},
            "android": {"name": "手机版 (Android)", "baidu": "", "gitee": ""},
        },
    }


def _read_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"system_name": "一人公司管理系统", "data_dir": DATA_DIR}


class BaseInfoWindow(QDialog):
    """系统设置 · ENGINEERING DECK"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("系统设置 · ENGINEERING DECK")
        self.setMinimumSize(600, 520)
        self._build_ui()
        self._load_current()
        self.setStyleSheet(self._style())

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 24)

        # 标题
        title = QLabel("系统设置")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        title.setStyleSheet("color: #ddaaff; letter-spacing: 4px;")
        layout.addWidget(title)

        # ── 基本设置 ──
        basic_group = QGroupBox("基本信息")
        bg = QGridLayout(basic_group)
        bg.setSpacing(10)

        bg.addWidget(QLabel("系统名称:"), 0, 0)
        self.sys_name = QLineEdit()
        bg.addWidget(self.sys_name, 0, 1)

        bg.addWidget(QLabel("当前版本:"), 1, 0)
        self.cur_ver = QLabel()
        self.cur_ver.setStyleSheet("color: #aabbcc; font-size: 13px; font-weight: bold;")
        bg.addWidget(self.cur_ver, 1, 1)

        bg.addWidget(QLabel("数据目录:"), 2, 0)
        data_lbl = QLabel(DATA_DIR)
        data_lbl.setStyleSheet("color: #889999; font-size: 11px;")
        bg.addWidget(data_lbl, 2, 1)

        launch_combo = QComboBox()
        launch_combo.addItems(["正常启动", "安全模式", "调试模式"])
        bg.addWidget(QLabel("启动模式:"), 3, 0)
        bg.addWidget(launch_combo, 3, 1)

        layout.addWidget(basic_group)

        # ── 版本发布 ──
        ver_group = QGroupBox("版本发布（更新云端版本信息）")
        vg = QGridLayout(ver_group)
        vg.setSpacing(10)

        vg.addWidget(QLabel("最新版本号:"), 0, 0)
        self.ver_version = QLineEdit()
        self.ver_version.setPlaceholderText("如: 2.1.0")
        vg.addWidget(self.ver_version, 0, 1)

        vg.addWidget(QLabel("更新说明:"), 1, 0)
        self.ver_notes = QTextEdit()
        self.ver_notes.setMaximumHeight(70)
        self.ver_notes.setPlaceholderText("每行一条更新内容")
        vg.addWidget(self.ver_notes, 1, 1)

        vg.addWidget(QLabel("电脑版 百度网盘:"), 2, 0)
        self.ver_win_baidu = QLineEdit()
        self.ver_win_baidu.setPlaceholderText("百度网盘链接")
        vg.addWidget(self.ver_win_baidu, 2, 1)

        vg.addWidget(QLabel("电脑版 Gitee:"), 3, 0)
        self.ver_win_gitee = QLineEdit()
        self.ver_win_gitee.setPlaceholderText("Gitee Release 链接")
        vg.addWidget(self.ver_win_gitee, 3, 1)

        vg.addWidget(QLabel("手机版 百度网盘:"), 4, 0)
        self.ver_android_baidu = QLineEdit()
        self.ver_android_baidu.setPlaceholderText("百度网盘链接")
        vg.addWidget(self.ver_android_baidu, 4, 1)

        vg.addWidget(QLabel("手机版 Gitee:"), 5, 0)
        self.ver_android_gitee = QLineEdit()
        self.ver_android_gitee.setPlaceholderText("Gitee Release 链接")
        vg.addWidget(self.ver_android_gitee, 5, 1)

        btn_row = QHBoxLayout()
        btn_load = QPushButton("读取当前版本")
        btn_load.clicked.connect(self._load_current)
        btn_row.addWidget(btn_load)

        btn_publish = QPushButton("发布新版本")
        btn_publish.setObjectName("btn_publish")
        btn_publish.clicked.connect(self._publish_version)
        btn_row.addWidget(btn_publish)
        btn_row.addStretch()
        vg.addLayout(btn_row, 6, 0, 1, 2)

        layout.addWidget(ver_group)

        # 保存按钮
        btn_save = QPushButton("保存设置")
        btn_save.setObjectName("btn_save")
        btn_save.clicked.connect(self._save_settings)
        layout.addWidget(btn_save)
        layout.addStretch()

    def _load_current(self):
        data = _read_version_json()
        self.cur_ver.setText(_read_version_file())
        self.ver_version.setText(data.get("latest_version", ""))
        self.ver_notes.setPlainText(data.get("release_notes", ""))
        downloads = data.get("downloads", {})
        win = downloads.get("windows", {})
        android = downloads.get("android", {})
        self.ver_win_baidu.setText(win.get("baidu", ""))
        self.ver_win_gitee.setText(win.get("gitee", ""))
        self.ver_android_baidu.setText(android.get("baidu", ""))
        self.ver_android_gitee.setText(android.get("gitee", ""))

        settings = _read_settings()
        self.sys_name.setText(settings.get("system_name", ""))

    def _publish_version(self):
        version = self.ver_version.text().strip()
        if not version:
            QMessageBox.warning(self, "发布失败", "版本号不能为空")
            return

        reply = QMessageBox.question(
            self, "确认发布",
            f"确定发布版本 v{version}？\n所有用户将收到更新提示。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        version_info = {
            "latest_version": version.lstrip("vV"),
            "release_notes": self.ver_notes.toPlainText().strip(),
            "released_at": datetime.now().strftime("%Y-%m-%d"),
            "min_version": "1.0.0",
            "downloads": {
                "windows": {
                    "name": "电脑版 (Windows)",
                    "baidu": self.ver_win_baidu.text().strip(),
                    "gitee": self.ver_win_gitee.text().strip(),
                },
                "android": {
                    "name": "手机版 (Android)",
                    "baidu": self.ver_android_baidu.text().strip(),
                    "gitee": self.ver_android_gitee.text().strip(),
                },
            },
        }

        # 备份旧版
        if os.path.exists(VERSION_FILE):
            bak = VERSION_FILE + ".bak"
            shutil.copy2(VERSION_FILE, bak)

        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump(version_info, f, ensure_ascii=False, indent=2)

        # 更新 version.txt
        with open(VERSION_TXT, "w", encoding="utf-8") as f:
            f.write(version.lstrip("vV"))

        QMessageBox.information(
            self, "发布成功",
            f"版本 v{version} 已发布！\n\n更新信息已写入 config/version.json\n用户点击'检查更新'即可收到提示。",
        )
        self._load_current()

    def _save_settings(self):
        settings = {"system_name": self.sys_name.text().strip(), "data_dir": DATA_DIR}
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, "成功", "设置已保存！")

    def _style(self):
        return """
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(10,12,18,245), stop:1 rgba(18,21,28,245));
                border: 2px solid rgba(130,145,165,35); border-radius: 14px;
            }
            QLabel { color: #99aabb; background: transparent; font-size: 12px; }
            QGroupBox {
                color: #889999; font-weight: 700; font-size: 12px;
                border: 1px solid rgba(130,145,165,25); border-radius: 10px;
                margin-top: 10px; padding-top: 14px;
            }
            QGroupBox::title { left: 14px; padding: 0 6px; }
            QLineEdit, QTextEdit, QComboBox {
                background: rgba(16,20,26,220); color: #aabbcc;
                border: 1px solid rgba(130,145,165,25); border-radius: 6px;
                padding: 6px 10px; font-size: 12px;
            }
            QPushButton {
                background: rgba(130,145,165,30); color: #ccddee;
                border: 1px solid rgba(150,165,185,45); border-radius: 8px;
                padding: 7px 20px; font-size: 11px; font-weight: 600;
            }
            QPushButton:hover { background: rgba(160,175,195,55); }
            QPushButton#btn_save, QPushButton#btn_publish {
                background: rgba(40,160,80,45); color: #88ffaa;
                border: 1px solid rgba(50,180,90,55);
            }
            QPushButton#btn_save:hover, QPushButton#btn_publish:hover {
                background: rgba(50,180,90,70);
            }
        """

```
