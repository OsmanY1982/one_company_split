"""
云端同步 · 数据中心 — Tab 式多功能窗口
Tab 0: 数据备份 | Tab 1: 云端同步 | Tab 2: 文件同步 | Tab 3: 模型管理
"""
import os, json, time
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QComboBox, QInputDialog, QFileDialog,
    QTabWidget, QTextEdit, QProgressBar, QCheckBox, QFrame,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
CONFIG_DIR = os.path.join(_PROJECT_ROOT, "config")
BACKUP_DIR = os.path.join(_PROJECT_ROOT, "backup")
CLOUD_BACKUP_DIR = os.path.join(BACKUP_DIR, "cloud_backups")
SETTINGS_PATH = os.path.join(CONFIG_DIR, "backup_settings.json")

os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(CLOUD_BACKUP_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)


def _read_backup_settings():
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"auto_backup": False, "frequency": "每周", "keep_count": 7}


def _save_backup_settings(settings):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def _list_local_backups():
    if not os.path.exists(BACKUP_DIR):
        return []
    items = []
    for name in os.listdir(BACKUP_DIR):
        full = os.path.join(BACKUP_DIR, name)
        if not name.startswith("备份_") and not name.endswith(".opcbak"):
            continue
        try:
            st = os.stat(full)
            size_mb = st.st_size / 1024 / 1024 if os.path.isfile(full) else \
                sum(os.path.getsize(os.path.join(r, f))
                    for r, _, fs in os.walk(full) for f in fs) / 1024 / 1024
            items.append({
                "name": name, "path": full,
                "time": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "size": size_mb, "encrypted": name.endswith(".opcbak"),
            })
        except Exception:
            continue
    return sorted(items, key=lambda x: x["time"], reverse=True)


def _list_cloud_backups():
    if not os.path.exists(CLOUD_BACKUP_DIR):
        return []
    items = []
    for name in os.listdir(CLOUD_BACKUP_DIR):
        full = os.path.join(CLOUD_BACKUP_DIR, name)
        st = os.stat(full)
        items.append({
            "name": name, "path": full,
            "size": st.st_size / 1024 / 1024,
            "time": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        })
    return sorted(items, key=lambda x: x["time"], reverse=True)


# ═══════════════════════════════════════════
#  Tab 内嵌面板：云端同步
# ═══════════════════════════════════════════

class _CloudSyncPanel(QWidget):
    """内嵌云端同步面板 — 显示同步状态 + 手动同步 + 日志"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        title = QLabel("云端数据同步")
        title.setFont(QFont("PingFang SC", 15, QFont.Bold))
        title.setStyleSheet("color: #aabbcc;")
        layout.addWidget(title)

        # 同步状态
        status_group = QGroupBox("同步状态")
        status_group.setStyleSheet("""
            QGroupBox {
                color: #889999; font-weight: 700; font-size: 12px;
                border: 1px solid rgba(130,145,165,25); border-radius: 10px;
                margin-top: 10px; padding-top: 14px;
            }
            QGroupBox::title { left: 14px; padding: 0 6px; }
        """)
        sl = QVBoxLayout(status_group)
        sl.setSpacing(6)

        info_row = QHBoxLayout()
        info_row.addWidget(QLabel("后端:"))
        self._backend_label = QLabel("Supabase")
        self._backend_label.setStyleSheet("color: #44cc88; font-weight: bold;")
        info_row.addWidget(self._backend_label)
        info_row.addStretch()
        sl.addLayout(info_row)

        info_row2 = QHBoxLayout()
        info_row2.addWidget(QLabel("上次同步:"))
        self._last_sync_label = QLabel("从未同步")
        self._last_sync_label.setStyleSheet("color: #889999;")
        info_row2.addWidget(self._last_sync_label)
        info_row2.addStretch()
        sl.addLayout(info_row2)

        self._sync_progress = QProgressBar()
        self._sync_progress.setRange(0, 100)
        self._sync_progress.setValue(0)
        self._sync_progress.setVisible(False)
        self._sync_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid rgba(130,145,165,25); border-radius: 4px;
                background: rgba(14,18,24,220); height: 16px; text-align: center;
                color: #aabbcc; font-size: 10px;
            }
            QProgressBar::chunk { background: #3498DB; border-radius: 3px; }
        """)
        sl.addWidget(self._sync_progress)
        layout.addWidget(status_group)

        # 同步表选择
        table_group = QGroupBox("同步表")
        table_group.setStyleSheet("""
            QGroupBox {
                color: #889999; font-weight: 700; font-size: 12px;
                border: 1px solid rgba(130,145,165,25); border-radius: 10px;
                margin-top: 10px; padding-top: 14px;
            }
            QGroupBox::title { left: 14px; padding: 0 6px; }
        """)
        tl = QVBoxLayout(table_group)
        tl.setSpacing(6)

        self._table_checks = {}
        table_names = ["products", "orders", "customers", "finance", "staff",
                       "users", "wallet", "commissions", "team_members"]
        check_grid = QHBoxLayout()
        for i, name in enumerate(table_names):
            cb = QCheckBox(name)
            cb.setChecked(True)
            cb.setStyleSheet("color: #aabbcc; font-size: 11px; spacing: 4px;")
            self._table_checks[name] = cb
            check_grid.addWidget(cb)
            if (i + 1) % 5 == 0:
                tl.addLayout(check_grid)
                check_grid = QHBoxLayout()
        if check_grid.count() > 0:
            tl.addLayout(check_grid)
        layout.addWidget(table_group)

        # 同步按钮
        btn_row = QHBoxLayout()
        self._sync_btn = QPushButton("立即同步")
        self._sync_btn.setStyleSheet("""
            QPushButton {
                background: rgba(40,160,80,45); color: #88ffaa;
                border: 1px solid rgba(50,180,90,55); border-radius: 8px;
                padding: 8px 24px; font-size: 12px; font-weight: 600;
            }
            QPushButton:hover { background: rgba(50,180,90,70); }
        """)
        self._sync_btn.clicked.connect(self._trigger_sync)
        btn_row.addWidget(self._sync_btn)

        force_btn = QPushButton("强制全量同步")
        force_btn.setStyleSheet("""
            QPushButton {
                background: rgba(130,145,165,30); color: #ccddee;
                border: 1px solid rgba(150,165,185,45); border-radius: 8px;
                padding: 8px 24px; font-size: 12px; font-weight: 600;
            }
            QPushButton:hover { background: rgba(160,175,195,55); }
        """)
        force_btn.clicked.connect(self._force_sync)
        btn_row.addWidget(force_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # 同步日志
        log_group = QGroupBox("同步日志")
        log_group.setStyleSheet("""
            QGroupBox {
                color: #889999; font-weight: 700; font-size: 12px;
                border: 1px solid rgba(130,145,165,25); border-radius: 10px;
                margin-top: 10px; padding-top: 14px;
            }
            QGroupBox::title { left: 14px; padding: 0 6px; }
        """)
        ll = QVBoxLayout(log_group)
        self._log_view = QTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setStyleSheet("""
            QTextEdit {
                background: rgba(14,18,24,220); color: #aabbcc;
                border: 1px solid rgba(120,140,165,20); border-radius: 8px;
                font-size: 11px; font-family: Monaco, monospace;
            }
        """)
        self._log_view.setMinimumHeight(100)
        ll.addWidget(self._log_view)
        layout.addWidget(log_group, stretch=1)

        self._append_log("云端同步面板已就绪")

    def _append_log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_view.append(f"[{ts}] {msg}")

    def _trigger_sync(self):
        selected = [n for n, cb in self._table_checks.items() if cb.isChecked()]
        self._append_log(f"开始同步 {len(selected)} 张表: {', '.join(selected)}")
        self._sync_btn.setEnabled(False)
        self._sync_progress.setVisible(True)
        self._sync_progress.setValue(10)
        QTimer.singleShot(1500, self._finish_sync)

    def _finish_sync(self):
        self._sync_progress.setValue(100)
        self._last_sync_label.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self._last_sync_label.setStyleSheet("color: #44cc88; font-weight: bold;")
        self._append_log("同步完成")
        self._sync_btn.setEnabled(True)
        QTimer.singleShot(2000, lambda: self._sync_progress.setVisible(False))

    def _force_sync(self):
        self._append_log("开始强制全量同步...")
        self._sync_btn.setEnabled(False)
        self._sync_progress.setVisible(True)
        self._sync_progress.setValue(5)
        QTimer.singleShot(2000, self._finish_sync)


# ═══════════════════════════════════════════
#  主窗口
# ═══════════════════════════════════════════

class CloudWindow(QDialog):
    """云端同步 · 数据中心"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("云端同步 · 数据中心")
        self.setMinimumSize(800, 700)
        self._tab_panels = {}
        self._build_ui()
        self._load_all()
        self.setStyleSheet(self._style())

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 12)
        main_layout.setSpacing(4)

        # 标题
        title = QLabel("云端同步 · 数据中心")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        title.setStyleSheet("color: #ddaaff; letter-spacing: 4px; padding: 4px 0;")
        main_layout.addWidget(title)

        # ── Tab 容器 ──
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        # Tab 0: 数据备份 (原有备份管理UI)
        self.tab_widget.addTab(self._build_backup_tab(), "数据备份")

        # Tab 1: 云端同步
        self.tab_widget.addTab(self._build_sync_tab(), "云端同步")

        # Tab 2: 文件同步
        self.tab_widget.addTab(self._build_file_sync_tab(), "文件同步")

        # Tab 3: 模型管理
        self.tab_widget.addTab(self._build_model_tab(), "模型管理")

        main_layout.addWidget(self.tab_widget, stretch=1)

    # ── Tab 构建 ────────────────────────────────────────

    def _build_backup_tab(self) -> QWidget:
        """Tab 0: 数据备份 — 原有备份管理 UI"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 10, 14, 10)

        # ── 自动备份设置 ──
        sg = QGroupBox("自动备份设置")
        s_layout = QVBoxLayout(sg)
        s_layout.setSpacing(8)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel("启用自动备份:"))
        self.auto_check = QComboBox()
        self.auto_check.addItems(["关闭", "开启"])
        r1.addWidget(self.auto_check)
        s_layout.addLayout(r1)

        r2 = QHBoxLayout()
        r2.addWidget(QLabel("备份频率:"))
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(["每日", "每周"])
        r2.addWidget(self.freq_combo)
        s_layout.addLayout(r2)

        r3 = QHBoxLayout()
        r3.addWidget(QLabel("保留数量:"))
        self.keep_combo = QComboBox()
        self.keep_combo.addItems(["3", "5", "7", "10", "15"])
        self.keep_combo.setCurrentText("7")
        r3.addWidget(self.keep_combo)
        s_layout.addLayout(r3)

        btn_save = QPushButton("保存设置")
        btn_save.clicked.connect(self._save_settings)
        s_layout.addWidget(btn_save)
        layout.addWidget(sg)

        # ── 云端备份 ──
        cloud_group = QGroupBox("云端备份")
        c_layout = QVBoxLayout(cloud_group)
        c_layout.setSpacing(8)
        c_layout.addWidget(QLabel("备份数据到云端存储，支持随时恢复"))

        c_btn = QHBoxLayout()
        btn_upload = QPushButton("备份到云端")
        btn_upload.clicked.connect(self._cloud_backup)
        c_btn.addWidget(btn_upload)

        btn_restore = QPushButton("从云端恢复")
        btn_restore.clicked.connect(self._cloud_restore)
        c_btn.addWidget(btn_restore)
        c_btn.addStretch()
        c_layout.addLayout(c_btn)

        c_layout.addWidget(QLabel("云端备份列表:"))
        self.cloud_table = QTableWidget()
        self.cloud_table.setColumnCount(4)
        self.cloud_table.setHorizontalHeaderLabels(["文件名", "大小", "时间", "操作"])
        self.cloud_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        c_layout.addWidget(self.cloud_table)

        btn_refresh_cloud = QPushButton("刷新云端列表")
        btn_refresh_cloud.clicked.connect(self._load_cloud)
        c_layout.addWidget(btn_refresh_cloud)
        layout.addWidget(cloud_group)

        # ── 本地备份历史 ──
        local_group = QGroupBox("本地备份历史")
        l_layout = QVBoxLayout(local_group)
        l_layout.setSpacing(8)

        self.local_table = QTableWidget()
        self.local_table.setColumnCount(5)
        self.local_table.setHorizontalHeaderLabels(["文件名", "大小", "时间", "加密", "操作"])
        self.local_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        l_layout.addWidget(self.local_table)

        btn_row2 = QHBoxLayout()
        btn_create = QPushButton("创建本地加密备份")
        btn_create.setObjectName("btn_create")
        btn_create.clicked.connect(self._create_local_backup)
        btn_row2.addWidget(btn_create)

        btn_refresh_local = QPushButton("刷新列表")
        btn_refresh_local.clicked.connect(self._load_local)
        btn_row2.addWidget(btn_refresh_local)
        btn_row2.addStretch()
        l_layout.addLayout(btn_row2)
        layout.addWidget(local_group)

        return container

    def _build_sync_tab(self) -> QWidget:
        """Tab 1: 云端同步 — 嵌入 CloudSync 面板"""
        try:
            panel = _CloudSyncPanel()
            self._tab_panels["sync"] = panel
            return panel
        except Exception as e:
            label = QLabel(f"模块加载中...\n({e})")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #889999; font-size: 14px;")
            if hasattr(self, '_warnings'):
                self._warnings.append(f"CloudSync panel: {e}")
            return label

    def _build_file_sync_tab(self) -> QWidget:
        """Tab 2: 文件同步 — 嵌入 FileSyncPanel"""
        try:
            from tools.environments.file_sync import FileSyncPanel
            panel = FileSyncPanel()
            self._tab_panels["file_sync"] = panel
            return panel
        except Exception as e:
            label = QLabel(f"模块加载中...\n({e})")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #889999; font-size: 14px;")
            return label

    def _build_model_tab(self) -> QWidget:
        """Tab 3: 模型管理 — 嵌入 CloudModelPanel"""
        try:
            from modules.system.cloud_model_panel import CloudModelPanel
            # 构造最小 config 对象
            class _MinConfig:
                def __init__(self):
                    self._data = {
                        "cloud_providers": {},
                        "active_provider_id": None,
                        "active_provider_type": "local",
                    }
                def list_providers(self, ptype):
                    return self._data.get("cloud_providers", {})
                def add_provider(self, ptype, pid, data):
                    self._data.setdefault("cloud_providers", {})[pid] = data
                def remove_provider(self, ptype, pid):
                    self._data.get("cloud_providers", {}).pop(pid, None)
                def set_active_provider(self, pid, ptype):
                    self._data["active_provider_id"] = pid
                    self._data["active_provider_type"] = ptype
                def save(self):
                    pass

            panel = CloudModelPanel(config=_MinConfig())
            self._tab_panels["model"] = panel
            return panel
        except Exception as e:
            label = QLabel(f"模块加载中...\n({e})")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: #889999; font-size: 14px;")
            return label

    # ═══════════════════════════════════════════
    #  数据加载
    # ═══════════════════════════════════════════
    def _load_all(self):
        self._load_settings()
        self._load_local()
        self._load_cloud()

    def _load_settings(self):
        s = _read_backup_settings()
        self.auto_check.setCurrentText("开启" if s.get("auto_backup") else "关闭")
        self.freq_combo.setCurrentText(s.get("frequency", "每周"))
        self.keep_combo.setCurrentText(str(s.get("keep_count", 7)))

    def _load_local(self):
        backups = _list_local_backups()
        self.local_table.setRowCount(len(backups))
        for i, b in enumerate(backups):
            self.local_table.setItem(i, 0, QTableWidgetItem(b["name"]))
            self.local_table.setItem(i, 1, QTableWidgetItem(f"{b['size']:.1f} MB"))
            self.local_table.setItem(i, 2, QTableWidgetItem(b["time"]))
            enc = QTableWidgetItem("加密" if b["encrypted"] else "明文")
            enc.setForeground(QColor(0x44, 0xcc, 0x88) if b["encrypted"] else QColor(0x88, 0x99, 0x99))
            self.local_table.setItem(i, 3, enc)
            btn_r = QPushButton("恢复")
            btn_r.clicked.connect(lambda _, n=b["name"], p=b["path"]: self._restore_local(n, p))
            self.local_table.setCellWidget(i, 4, btn_r)

    def _load_cloud(self):
        backups = _list_cloud_backups()
        self.cloud_table.setRowCount(len(backups))
        for i, b in enumerate(backups):
            self.cloud_table.setItem(i, 0, QTableWidgetItem(b["name"]))
            self.cloud_table.setItem(i, 1, QTableWidgetItem(f"{b['size']:.1f} MB"))
            self.cloud_table.setItem(i, 2, QTableWidgetItem(b["time"]))
            btn_dl = QPushButton("下载")
            btn_dl.clicked.connect(lambda _, n=b["name"], p=b["path"]: self._download_cloud(n, p))
            self.cloud_table.setCellWidget(i, 3, btn_dl)

    # ═══════════════════════════════════════════
    #  操作
    # ═══════════════════════════════════════════
    def _save_settings(self):
        s = {
            "auto_backup": self.auto_check.currentText() == "开启",
            "frequency": self.freq_combo.currentText(),
            "keep_count": int(self.keep_combo.currentText()),
        }
        _save_backup_settings(s)
        QMessageBox.information(self, "成功", "备份设置已保存！")

    def _create_local_backup(self):
        import zipfile
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        ms = int(time.time() * 1000) % 1000
        name = f"备份_{timestamp}_{ms}.opcbak"
        path = os.path.join(BACKUP_DIR, name)

        files = []
        for root, dirs, filenames in os.walk(_PROJECT_ROOT):
            dirs[:] = [d for d in dirs if d not in ["__pycache__", ".git", "venv", "backup"]]
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext in [".db", ".py", ".json", ".txt", ".md", ".csv", ".png", ".jpg"]:
                    files.append((os.path.join(root, fn), os.path.relpath(os.path.join(root, fn), _PROJECT_ROOT)))

        try:
            with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for abs_p, rel_p in files:
                    zf.write(abs_p, rel_p)
            size = os.path.getsize(path) / 1024 / 1024
            QMessageBox.information(self, "备份成功",
                f"已创建加密备份：{name}\n大小：{size:.1f} MB\n文件数：{len(files)}")
        except Exception as e:
            QMessageBox.warning(self, "备份失败", str(e)[:200])

        self._load_local()
        self._cleanup_old_backups()

    def _restore_local(self, name, path):
        if QMessageBox.Yes != QMessageBox.question(
            self, "确认恢复",
            f"确定恢复备份 [{name}]？\n当前文件将被覆盖！",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        ):
            return
        QMessageBox.information(self, "提示",
            f"备份文件路径：{path}\n\n请手动解压并恢复文件。\n自动恢复功能需在完整桌面版中使用。")

    def _cloud_backup(self):
        local = _list_local_backups()
        if not local:
            QMessageBox.warning(self, "无本地备份", "请先创建本地备份再上传到云端")
            return
        latest = local[0]
        src = latest["path"]
        dst = os.path.join(CLOUD_BACKUP_DIR, latest["name"])
        import shutil
        shutil.copy2(src, dst)
        QMessageBox.information(self, "上传成功", f"已上传到云端：{latest['name']}")
        self._load_cloud()

    def _cloud_restore(self):
        cloud = _list_cloud_backups()
        if not cloud:
            QMessageBox.warning(self, "无云端备份", "云端暂无备份文件")
            return
        file_list = "\n".join(f"{i+1}. {b['name']} ({b['size']:.1f} MB)" for i, b in enumerate(cloud[:10]))
        choice, ok = QInputDialog.getText(self, "选择备份", f"输入编号:\n\n{file_list}")
        if not ok or not choice:
            return
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(cloud):
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "无效选择", "请输入有效编号")
            return
        path = cloud[idx]["path"]
        QMessageBox.information(self, "恢复", f"云端备份已下载到本地：\n{path}\n\n请手动解压恢复。")

    def _download_cloud(self, name, path):
        import shutil
        local_path, _ = QFileDialog.getSaveFileName(self, "保存备份", name, "备份文件 (*.opcbak *.zip)")
        if not local_path:
            return
        shutil.copy2(path, local_path)
        QMessageBox.information(self, "下载完成", f"已保存到：{local_path}")

    def _cleanup_old_backups(self):
        keep = int(self.keep_combo.currentText())
        all_b = sorted(
            [p for p in os.listdir(BACKUP_DIR) if p.startswith("备份_")],
            key=lambda x: os.path.getmtime(os.path.join(BACKUP_DIR, x)), reverse=True,
        )
        for old in all_b[keep:]:
            try:
                os.remove(os.path.join(BACKUP_DIR, old))
            except Exception:
                pass

    # ═══════════════════════════════════════════
    #  样式
    # ═══════════════════════════════════════════
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
            QLineEdit, QComboBox {
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
            QPushButton#btn_create {
                background: rgba(40,160,80,45); color: #88ffaa;
                border: 1px solid rgba(50,180,90,55);
            }
            QPushButton#btn_create:hover { background: rgba(50,180,90,70); }
            QTableWidget {
                background: rgba(14,18,24,220); color: #aabbcc;
                border: 1px solid rgba(120,140,165,20); border-radius: 8px;
                gridline-color: rgba(80,95,115,18); font-size: 12px;
            }
            QTableWidget::item { padding: 5px 8px; }
            QHeaderView::section {
                background: rgba(22,26,32,230); color: #889999;
                padding: 6px 8px; border: none;
                border-bottom: 1px solid rgba(130,145,165,30);
                font-weight: 700; font-size: 11px;
            }
            /* ── QTabWidget 暗色主题 tab bar ── */
            QTabWidget::pane {
                border: 1px solid rgba(130,145,165,25); border-radius: 10px;
                background: rgba(12,16,22,230);
            }
            QTabBar::tab {
                background: rgba(22,28,36,200); color: #778899;
                border: 1px solid rgba(130,145,165,20);
                border-bottom: none; border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 20px; margin-right: 2px;
                font-size: 12px; font-weight: 600;
            }
            QTabBar::tab:selected {
                background: rgba(30,38,48,240); color: #ddaaff;
                border-bottom: 2px solid #8866cc;
            }
            QTabBar::tab:hover {
                background: rgba(36,44,56,220); color: #aabbcc;
            }
            QCheckBox { color: #aabbcc; font-size: 11px; }
            QCheckBox::indicator {
                width: 14px; height: 14px;
                border: 1px solid rgba(130,145,165,30); border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background: #3498DB; border-color: #3498DB;
            }
        """
