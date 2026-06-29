# `core/modules/startup/startup_selector_window.py`

> 路径：`core/modules/startup/startup_selector_window.py` | 行数：114


---


```python
# -*- coding: utf-8 -*-

import os
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt

try:
    from dark_theme import apply_dark_theme, BG_MAIN, BG_CARD, BG_INPUT, BTN_NORMAL, BTN_HOVER, BTN_PRESSED, TEXT_WHITE, TEXT_LIGHT, TEXT_MUTED, ACCENT, SUCCESS, WARNING, DANGER, BORDER, BORDER_LIGHT
except ImportError:
    from core.dark_theme import apply_dark_theme, BG_MAIN, BG_CARD, BG_INPUT, BTN_NORMAL, BTN_HOVER, BTN_PRESSED, TEXT_WHITE, TEXT_LIGHT, TEXT_MUTED, ACCENT, SUCCESS, WARNING, DANGER, BORDER, BORDER_LIGHT

try:
    from paths import BASE_DIR, DATA_DIR, CONFIG_DIR
except ImportError:
    from core.paths import BASE_DIR, DATA_DIR, CONFIG_DIR
class StartupSelectorWindow(QMainWindow):
    def __init__(self, on_select_mode, parent=None):
        super().__init__(parent)
        apply_dark_theme(self)
        self.setWindowTitle("一人公司管理系统")
        self.setFixedSize(400, 320)
        self.on_select_mode = on_select_mode
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # 标题
        title = QLabel("一人公司管理系统")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2E86AB;")
        layout.addWidget(title)

        # 版本信息
        version = QLabel("v2.0.0  2026")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("font-size: 12px; color: #999;")
        layout.addWidget(version)

        layout.addSpacing(10)

        # 上次启动模式
        last_mode = self._load_last_mode()
        if last_mode:
            last_label = QLabel(f"上次选择: {'本地运行' if last_mode == 'local' else '云端登录'}")
            last_label.setAlignment(Qt.AlignCenter)
            last_label.setStyleSheet("font-size: 12px; color: #666;")
            layout.addWidget(last_label)

        btn_local = QPushButton("本地运行")
        btn_local.setStyleSheet
        btn_local.clicked.connect(lambda: self.select_mode('local'))
        layout.addWidget(btn_local)

        btn_cloud = QPushButton("云端登录")
        btn_cloud.setStyleSheet
        btn_cloud.clicked.connect(lambda: self.select_mode('cloud'))
        layout.addWidget(btn_cloud)

        # 系统状态检查
        check_layout = QHBoxLayout()
        check_layout.addStretch()
        if self._check_dependencies():
            check_label = QLabel("✓ 依赖正常")
            check_label.setStyleSheet("color: #28a745; font-size: 11px;")
        else:
            check_label = QLabel("⚠ 缺少依赖")
            check_label.setStyleSheet("color: #dc3545; font-size: 11px;")
        check_layout.addWidget(check_label)
        check_layout.addStretch()
        layout.addLayout(check_layout)

    def _load_last_mode(self):
        try:
            config_path = os.path.join(CONFIG_DIR, "last_mode.txt")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return f.read().strip()
        except Exception: pass
        return None

    def _save_last_mode(self, mode):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(os.path.join(CONFIG_DIR, "last_mode.txt"), 'w') as f:
                f.write(mode)
        except Exception:
            pass

    def _check_dependencies(self):
        """检查系统依赖，包括数据库、配置文件等"""
        import os
        missing = []
        for d in [BASE_DIR, DATA_DIR, CONFIG_DIR]:
            if not os.path.exists(d):
                try:
                    os.makedirs(d, exist_ok=True)
                except Exception:
                    missing.append(d)
        if missing:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "依赖检查", f"以下目录无法创建：{missing}")
            return False
        return True
    def select_mode(self, mode):
        self._save_last_mode(mode)
        if self.on_select_mode:
            self.on_select_mode(mode)
        self.close()


```
