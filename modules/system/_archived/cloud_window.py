"""
云端同步 · ENGINEERING DECK — 本地数据备份与恢复
提供数据目录导出（zip）和导入恢复，日志记录到 system_logs.db
"""
import os
import sqlite3
import shutil
import traceback
import zipfile
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit,
    QGroupBox, QFrame, QFileDialog, QMessageBox,
)
from PyQt5.QtCore import Qt

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

# ═══════ QSS ═══════
QSS = """
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 rgba(14,16,20,245), stop:1 rgba(20,23,28,245));
        border: 2px solid rgba(100,160,220,50);
        border-radius: 14px;
    }
"""
INPUT_STYLE = """
    QLineEdit, QTextEdit {
        background: rgba(16,18,22,230); color: #aabbcc;
        border: 1px solid rgba(130,145,165,35); border-radius: 6px;
        padding: 6px 10px; font-size: 12px;
    }
    QLineEdit:focus { border: 1px solid rgba(160,175,195,180); }
"""
BTN_BLUE = """
    QPushButton {
        background: rgba(100,160,220,40); color: #aaddff;
        border: 1px solid rgba(120,180,240,60); border-radius: 16px;
        padding: 7px 22px; font-size: 12px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(120,180,240,70); }
"""
BTN_GREEN = """
    QPushButton {
        background: rgba(60,180,120,35); color: #aaffdd;
        border: 1px solid rgba(80,200,140,55); border-radius: 16px;
        padding: 7px 22px; font-size: 12px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(80,200,140,65); }
"""
BTN_AMBER = """
    QPushButton {
        background: rgba(200,140,40,35); color: #ffddaa;
        border: 1px solid rgba(220,160,60,55); border-radius: 16px;
        padding: 7px 22px; font-size: 12px; font-weight: 600;
    }
    QPushButton:hover { background: rgba(220,160,60,65); }
"""
GROUP_STYLE = """
    QGroupBox {
        color: #889999; font-weight: 700; font-size: 12px;
        border: 1px solid rgba(130,145,165,35); border-radius: 10px;
        margin-top: 12px; padding-top: 16px;
    }
    QGroupBox::title { left: 14px; padding: 0 6px; }
    QLabel { color: #889999; background: transparent; }
"""


class CloudWindow(QDialog):
    """数据备份与恢复 — 本地 zip 导出/导入"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("云端同步 · ENGINEERING DECK")
        self.setMinimumSize(600, 500)
        self.setStyleSheet(QSS)
        self._build_ui()
        self._refresh_storage_info()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(22, 18, 22, 18)

        title = QLabel("云端同步 · ENGINEERING DECK")
        title.setStyleSheet("color: #aabbcc; font-size: 16px; font-weight: 800; letter-spacing: 3px; background: transparent;")
        layout.addWidget(title, alignment=Qt.AlignCenter)

        # ── 存储状态卡片 ──
        status_card = QFrame()
        status_card.setStyleSheet(
            "background: rgba(16,18,22,230); border: 1px solid rgba(130,145,165,35);"
            "border-radius: 10px; padding: 14px;"
        )
        sl = QHBoxLayout(status_card); sl.setSpacing(18)
        self._size_label = QLabel("数据目录大小: 计算中...")
        self._size_label.setStyleSheet("color: #8899aa; font-size: 12px; font-weight: 600; background:transparent;")
        sl.addWidget(self._size_label)
        sl.addStretch()
        self._db_count_label = QLabel("")
        self._db_count_label.setStyleSheet("color: #667788; font-size: 11px; background:transparent;")
        sl.addWidget(self._db_count_label)
        layout.addWidget(status_card)

        # ── 导出备份 ──
        export_grp = QGroupBox("导出备份")
        export_grp.setStyleSheet(GROUP_STYLE)
        el = QVBoxLayout(export_grp); el.setSpacing(8)

        export_row = QHBoxLayout()
        self._backup_path = QLineEdit()
        self._backup_path.setReadOnly(True)
        self._backup_path.setPlaceholderText("选择备份文件保存位置...")
        self._backup_path.setStyleSheet(INPUT_STYLE)
        export_row.addWidget(self._backup_path, 1)

        browse_btn = QPushButton("浏览...")
        browse_btn.setStyleSheet(BTN_BLUE)
        browse_btn.clicked.connect(self._browse_export)
        export_row.addWidget(browse_btn)
        el.addLayout(export_row)

        export_act = QHBoxLayout()
        export_act.addStretch()
        export_btn = QPushButton("导出备份")
        export_btn.setStyleSheet(BTN_GREEN)
        export_btn.clicked.connect(self._do_export)
        export_act.addWidget(export_btn)
        el.addLayout(export_act)
        layout.addWidget(export_grp)

        # ── 导入恢复 ──
        import_grp = QGroupBox("导入恢复")
        import_grp.setStyleSheet(GROUP_STYLE)
        il = QVBoxLayout(import_grp); il.setSpacing(8)

        import_row = QHBoxLayout()
        self._restore_path = QLineEdit()
        self._restore_path.setReadOnly(True)
        self._restore_path.setPlaceholderText("选择备份文件 (.zip)...")
        self._restore_path.setStyleSheet(INPUT_STYLE)
        import_row.addWidget(self._restore_path, 1)

        browse2_btn = QPushButton("浏览...")
        browse2_btn.setStyleSheet(BTN_BLUE)
        browse2_btn.clicked.connect(self._browse_import)
        import_row.addWidget(browse2_btn)
        il.addLayout(import_row)

        import_act = QHBoxLayout()
        import_act.addStretch()
        import_btn = QPushButton("导入恢复")
        import_btn.setStyleSheet(BTN_AMBER)
        import_btn.clicked.connect(self._do_import)
        import_act.addWidget(import_btn)
        il.addLayout(import_act)
        layout.addWidget(import_grp)

        # ── 操作日志 ──
        log_label = QLabel("操作日志:")
        log_label.setStyleSheet("color: #667788; font-size: 11px; background:transparent;")
        layout.addWidget(log_label)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(INPUT_STYLE)
        layout.addWidget(self.log_view)

    # ═══════ 存储信息 ═══════
    def _refresh_storage_info(self):
        if not os.path.isdir(DATA_DIR):
            self._size_label.setText("数据目录不存在")
            return
        total_size = 0
        db_count = 0
        for root, _, files in os.walk(DATA_DIR):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total_size += os.path.getsize(fp)
                except OSError:
                    pass
                if f.endswith(".db"):
                    db_count += 1
        if total_size < 1024:
            size_str = f"{total_size} B"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.1f} KB"
        else:
            size_str = f"{total_size / (1024 * 1024):.1f} MB"
        self._size_label.setText(f"数据目录大小: {size_str}")
        self._db_count_label.setText(f"| {db_count} 个数据库" if db_count else "")

    # ═══════ 导出 ═══════
    def _browse_export(self):
        default_name = f"cosmic_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        path, _ = QFileDialog.getSaveFileName(self, "导出备份", default_name, "ZIP 压缩包 (*.zip)")
        if path:
            self._backup_path.setText(path)

    def _do_export(self):
        target = self._backup_path.text().strip()
        if not target:
            QMessageBox.warning(self, "提示", "请先选择备份文件保存位置")
            return
        if not os.path.isdir(DATA_DIR):
            QMessageBox.warning(self, "提示", "数据目录不存在，无法导出")
            return
        try:
            with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(DATA_DIR):
                    for f in files:
                        fp = os.path.join(root, f)
                        arcname = os.path.relpath(fp, os.path.dirname(DATA_DIR))
                        zf.write(fp, arcname)
            size = os.path.getsize(target)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            self._add_log(f"[{datetime.now().strftime('%H:%M:%S')}] 导出成功 → {os.path.basename(target)} ({size_str})")
            self._log_op("导出", "成功", f"备份文件: {target} ({size_str})")
            QMessageBox.information(self, "导出完成", f"备份已保存至:\n{target}\n大小: {size_str}")
        except Exception as e:
            traceback.print_exc()
            self._add_log(f"[{datetime.now().strftime('%H:%M:%S')}] 导出失败: {e}")
            self._log_op("导出", "失败", str(e))
            QMessageBox.critical(self, "导出失败", str(e))

    # ═══════ 导入 ═══════
    def _browse_import(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择备份文件", "", "ZIP 压缩包 (*.zip)")
        if path:
            self._restore_path.setText(path)

    def _do_import(self):
        source = self._restore_path.text().strip()
        if not source:
            QMessageBox.warning(self, "提示", "请先选择备份文件 (.zip)")
            return
        if not os.path.isfile(source):
            QMessageBox.warning(self, "提示", "备份文件不存在")
            return
        reply = QMessageBox.question(
            self, "确认导入",
            f"将用以下备份覆盖当前数据:\n{os.path.basename(source)}\n\n此操作不可撤销，是否继续？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            self._add_log(f"[{datetime.now().strftime('%H:%M:%S')}] 导入已取消")
            return
        try:
            if not zipfile.is_zipfile(source):
                QMessageBox.critical(self, "导入失败", "文件不是有效的 ZIP 压缩包")
                return
            tmp_dir = os.path.join(DATA_DIR, "_restore_tmp")
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
            os.makedirs(tmp_dir, exist_ok=True)
            with zipfile.ZipFile(source, 'r') as zf:
                zf.extractall(tmp_dir)
            extracted_data = os.path.join(tmp_dir, "data")
            if os.path.isdir(extracted_data):
                for item in os.listdir(extracted_data):
                    src = os.path.join(extracted_data, item)
                    dst = os.path.join(DATA_DIR, item)
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
            else:
                for item in os.listdir(tmp_dir):
                    if item == "data":
                        continue
                    src = os.path.join(tmp_dir, item)
                    dst = os.path.join(DATA_DIR, item)
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
            shutil.rmtree(tmp_dir)
            self._add_log(f"[{datetime.now().strftime('%H:%M:%S')}] 导入成功 ← {os.path.basename(source)}")
            self._log_op("导入", "成功", f"从 {source} 恢复数据")
            QMessageBox.information(self, "导入完成", f"数据已从备份恢复:\n{os.path.basename(source)}")
            self._refresh_storage_info()
        except Exception as e:
            traceback.print_exc()
            self._add_log(f"[{datetime.now().strftime('%H:%M:%S')}] 导入失败: {e}")
            self._log_op("导入", "失败", str(e))
            QMessageBox.critical(self, "导入失败", str(e))
            tmp_dir = os.path.join(DATA_DIR, "_restore_tmp")
            if os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)

    # ═══════ 日志 ═══════
    def _add_log(self, msg):
        self.log_view.append(msg)

    def _log_op(self, op_type, status, detail):
        try:
            db = os.path.join(DATA_DIR, "system_logs.db")
            conn = sqlite3.connect(db)
            conn.execute(
                "CREATE TABLE IF NOT EXISTS sync_logs("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "sync_type TEXT, status TEXT, detail TEXT,"
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                ")"
            )
            conn.execute(
                "INSERT INTO sync_logs(sync_type, status, detail) VALUES(?,?,?)",
                (op_type, status, detail)
            )
            conn.commit()
            conn.close()
        except Exception:
            traceback.print_exc()
