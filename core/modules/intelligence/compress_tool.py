# -*- coding: utf-8 -*-
"""
压缩解压工具
支持：ZIP、TAR、GZ、BZ2 格式
"""
import os
import zipfile
import tarfile
import shutil
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QLineEdit, QTextEdit, QFileDialog, QComboBox,
    QProgressBar, QMessageBox, QGroupBox, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class CompressThread(QThread):
    """压缩后台线程"""
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, sources, dest, fmt):
        super().__init__()
        self.sources = sources
        self.dest = dest
        self.fmt = fmt
        self.running = True
    
    def run(self):
        try:
            if self.fmt == "zip":
                self._compress_zip()
            elif self.fmt in ["tar", "tar.gz", "tar.bz2"]:
                self._compress_tar()
        except Exception as e:
            self.log.emit(f"❌ 错误: {e}")
        self.finished.emit()
    
    def _compress_zip(self):
        with zipfile.ZipFile(self.dest, 'w', zipfile.ZIP_DEFLATED) as zf:
            total = sum(len(files) for _, _, files in os.walk(self.sources[0])) if os.path.isdir(self.sources[0]) else len(self.sources)
            processed = 0
            
            for source in self.sources:
                if os.path.isdir(source):
                    for root, dirs, files in os.walk(source):
                        if not self.running:
                            return
                        for file in files:
                            filepath = os.path.join(root, file)
                            arcname = os.path.relpath(filepath, os.path.dirname(source))
                            zf.write(filepath, arcname)
                            processed += 1
                            self.progress.emit(int(processed * 100 / max(total, 1)))
                            self.log.emit(f"添加: {arcname}")
                else:
                    zf.write(source, os.path.basename(source))
                    processed += 1
                    self.progress.emit(int(processed * 100 / max(total, 1)))
                    self.log.emit(f"添加: {os.path.basename(source)}")
    
    def _compress_tar(self):
        mode = {'tar': 'w', 'tar.gz': 'w:gz', 'tar.bz2': 'w:bz2'}[self.fmt]
        with tarfile.open(self.dest, mode) as tf:
            for source in self.sources:
                tf.add(source, arcname=os.path.basename(source))
                self.log.emit(f"添加: {os.path.basename(source)}")
        self.progress.emit(100)


class ExtractThread(QThread):
    """解压后台线程"""
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, archive, dest):
        super().__init__()
        self.archive = archive
        self.dest = dest
        self.running = True
    
    def run(self):
        try:
            ext = os.path.splitext(self.archive)[1].lower()
            
            if ext == '.zip':
                self._extract_zip()
            elif ext in ['.tar', '.gz', '.bz2', '.tgz']:
                self._extract_tar()
            else:
                self.log.emit("❌ 不支持的格式")
        except Exception as e:
            self.log.emit(f"❌ 错误: {e}")
        self.finished.emit()
    
    def _extract_zip(self):
        with zipfile.ZipFile(self.archive, 'r') as zf:
            namelist = zf.namelist()
            for i, name in enumerate(namelist):
                if not self.running:
                    return
                zf.extract(name, self.dest)
                self.progress.emit(int((i + 1) * 100 / len(namelist)))
                self.log.emit(f"解压: {name}")
    
    def _extract_tar(self):
        with tarfile.open(self.archive, 'r:*') as tf:
            members = tf.getmembers()
            for i, member in enumerate(members):
                if not self.running:
                    return
                tf.extract(member, self.dest)
                self.progress.emit(int((i + 1) * 100 / len(members)))
                self.log.emit(f"解压: {member.name}")


class CompressWidget(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🗜️ 压缩解压工具")
        self.setMinimumSize(600, 500)
        self.sources = []
        self.thread = None
        self._build_ui()
    
    def _build_ui(self):
        self.setStyleSheet("""
            QMainWindow { background: #f0f2f5; }
            QGroupBox { font-weight: bold; border: 2px solid #e2e8f0; border-radius: 8px; margin-top: 10px; padding: 10px; }
            QPushButton { background: #3182ce; color: white; border: none; border-radius: 6px; padding: 8px 16px; }
            QPushButton:hover { background: #2b6cb0; }
            QPushButton#danger { background: #e53e3e; }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        
        tabs = QTabWidget()
        
        # 压缩标签
        compress_tab = QWidget()
        c_layout = QVBoxLayout(compress_tab)
        
        c_group = QGroupBox("选择文件/文件夹")
        c_g_layout = QHBoxLayout(c_group)
        self.c_label = QLabel("未选择")
        c_g_layout.addWidget(self.c_label)
        btn_c_select = QPushButton("选择...")
        btn_c_select.clicked.connect(self._select_compress_sources)
        c_g_layout.addWidget(btn_c_select)
        c_layout.addWidget(c_group)
        
        fmt_group = QGroupBox("压缩格式")
        fmt_layout = QHBoxLayout(fmt_group)
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems(["ZIP", "TAR", "TAR.GZ", "TAR.BZ2"])
        fmt_layout.addWidget(self.fmt_combo)
        c_layout.addWidget(fmt_group)
        
        dest_group = QGroupBox("输出路径")
        dest_layout = QHBoxLayout(dest_group)
        self.dest_input = QLineEdit()
        dest_layout.addWidget(self.dest_input)
        btn_dest = QPushButton("浏览...")
        btn_dest.clicked.connect(self._select_dest)
        dest_layout.addWidget(btn_dest)
        c_layout.addWidget(dest_group)
        
        btn_compress = QPushButton("开始压缩")
        btn_compress.clicked.connect(self._start_compress)
        c_layout.addWidget(btn_compress)
        c_layout.addStretch()
        tabs.addTab(compress_tab, "压缩")
        
        # 解压标签
        extract_tab = QWidget()
        e_layout = QVBoxLayout(extract_tab)
        
        a_group = QGroupBox("选择压缩包")
        a_g_layout = QHBoxLayout(a_group)
        self.a_label = QLabel("未选择")
        a_g_layout.addWidget(self.a_label)
        btn_a_select = QPushButton("选择...")
        btn_a_select.clicked.connect(self._select_archive)
        a_g_layout.addWidget(btn_a_select)
        e_layout.addWidget(a_group)
        
        e_dest_group = QGroupBox("解压到")
        e_dest_layout = QHBoxLayout(e_dest_group)
        self.e_dest_input = QLineEdit()
        e_dest_layout.addWidget(self.e_dest_input)
        btn_e_dest = QPushButton("浏览...")
        btn_e_dest.clicked.connect(self._select_extract_dest)
        e_dest_layout.addWidget(btn_e_dest)
        e_layout.addWidget(e_dest_group)
        
        btn_extract = QPushButton("开始解压")
        btn_extract.clicked.connect(self._start_extract)
        e_layout.addWidget(btn_extract)
        e_layout.addStretch()
        tabs.addTab(extract_tab, "解压")
        
        layout.addWidget(tabs)
        
        # 进度和日志
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(150)
        layout.addWidget(self.log_area)
        
        btn_stop = QPushButton("停止")
        btn_stop.setObjectName("danger")
        btn_stop.clicked.connect(self._stop)
        layout.addWidget(btn_stop)
    
    def _select_compress_sources(self):
        # 支持多选文件或选择文件夹
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        
        # 添加选择文件夹按钮
        tree = dialog.findChild(QTreeWidget)
        if tree:
            btn = QPushButton("选择当前文件夹")
            dialog.layout().addWidget(btn)
        
        if dialog.exec_():
            self.sources = dialog.selectedFiles()
            self.c_label.setText(f"已选择 {len(self.sources)} 项")
    
    def _select_dest(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存压缩包", "", "ZIP (*.zip);;TAR (*.tar);;TAR.GZ (*.tar.gz);;TAR.BZ2 (*.tar.bz2)")
        if path:
            self.dest_input.setText(path)
    
    def _select_archive(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择压缩包", "", "压缩文件 (*.zip *.tar *.tar.gz *.tgz *.tar.bz2)")
        if path:
            self.archive = path
            self.a_label.setText(os.path.basename(path))
            # 自动设置解压目录
            self.e_dest_input.setText(os.path.dirname(path))
    
    def _select_extract_dest(self):
        path = QFileDialog.getExistingDirectory(self, "选择解压目录")
        if path:
            self.e_dest_input.setText(path)
    
    def _start_compress(self):
        if not self.sources or not self.dest_input.text():
            QMessageBox.warning(self, "提示", "请选择文件并设置输出路径")
            return
        
        fmt_map = {"ZIP": "zip", "TAR": "tar", "TAR.GZ": "tar.gz", "TAR.BZ2": "tar.bz2"}
        fmt = fmt_map.get(self.fmt_combo.currentText(), "zip")
        
        self.log_area.clear()
        self.progress.setValue(0)
        
        self.thread = CompressThread(self.sources, self.dest_input.text(), fmt)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.log.connect(self._log)
        self.thread.finished.connect(lambda: QMessageBox.information(self, "完成", "压缩完成！"))
        self.thread.start()
    
    def _start_extract(self):
        if not hasattr(self, 'archive') or not self.e_dest_input.text():
            QMessageBox.warning(self, "提示", "请选择压缩包并设置解压目录")
            return
        
        self.log_area.clear()
        self.progress.setValue(0)
        
        self.thread = ExtractThread(self.archive, self.e_dest_input.text())
        self.thread.progress.connect(self.progress.setValue)
        self.thread.log.connect(self._log)
        self.thread.finished.connect(lambda: QMessageBox.information(self, "完成", "解压完成！"))
        self.thread.start()
    
    def _log(self, msg):
        self.log_area.append(msg)
    
    def _stop(self):
        if self.thread and self.thread.isRunning():
            self.thread.running = False
            self.thread.wait(1000)
