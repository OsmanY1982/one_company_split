# -*- coding: utf-8 -*-
"""
文本批量处理工具
支持：批量查找替换、批量重命名、编码转换、行处理
"""
import os
import re
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QLineEdit, QTextEdit, QFileDialog, QComboBox,
    QCheckBox, QSpinBox, QMessageBox, QGroupBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class BatchTextThread(QThread):
    """后台处理线程"""
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, files, operation, params):
        super().__init__()
        self.files = files
        self.operation = operation
        self.params = params
        self.running = True
    
    def run(self):
        total = len(self.files)
        for i, filepath in enumerate(self.files):
            if not self.running:
                break
            try:
                if self.operation == "replace":
                    self._do_replace(filepath)
                elif self.operation == "rename":
                    self._do_rename(filepath)
                elif self.operation == "encoding":
                    self._do_encoding(filepath)
                elif self.operation == "line":
                    self._do_line_process(filepath)
                self.log.emit(f"✅ {filepath}")
            except Exception as e:
                self.log.emit(f"❌ {filepath}: {e}")
            self.progress.emit(int((i + 1) * 100 / total))
        self.finished.emit()
    
    def _do_replace(self, filepath):
        find = self.params.get("find", "")
        replace = self.params.get("replace", "")
        use_regex = self.params.get("regex", False)
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if use_regex:
            content = re.sub(find, replace, content)
        else:
            content = content.replace(find, replace)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _do_rename(self, filepath):
        pattern = self.params.get("pattern", "")
        replace = self.params.get("replace", "")
        
        dirname = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        name, ext = os.path.splitext(filename)
        
        new_name = name.replace(pattern, replace)
        new_path = os.path.join(dirname, new_name + ext)
        
        if new_path != filepath:
            os.rename(filepath, new_path)
    
    def _do_encoding(self, filepath):
        from_encoding = self.params.get("from", "gbk")
        to_encoding = self.params.get("to", "utf-8")
        
        with open(filepath, 'r', encoding=from_encoding, errors='ignore') as f:
            content = f.read()
        
        with open(filepath, 'w', encoding=to_encoding) as f:
            f.write(content)
    
    def _do_line_process(self, filepath):
        operation = self.params.get("operation", "")
        line_num = self.params.get("line", 0)
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        if operation == "delete_empty":
            lines = [l for l in lines if l.strip()]
        elif operation == "trim":
            lines = [l.strip() + '\n' for l in lines]
        elif operation == "delete_line" and 0 <= line_num < len(lines):
            lines.pop(line_num)
        elif operation == "unique":
            seen = set()
            new_lines = []
            for l in lines:
                if l not in seen:
                    seen.add(l)
                    new_lines.append(l)
            lines = new_lines
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)


class BatchTextWidget(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📝 文本批量处理")
        self.setMinimumSize(700, 600)
        self.files = []
        self.thread = None
        self._build_ui()
    
    def _build_ui(self):
        self.setStyleSheet("""
            QMainWindow { background: #f0f2f5; }
            QGroupBox { font-weight: bold; border: 2px solid #e2e8f0; border-radius: 8px; margin-top: 10px; padding: 10px; }
            QPushButton { background: #3182ce; color: white; border: none; border-radius: 6px; padding: 8px 16px; }
            QPushButton:hover { background: #2b6cb0; }
            QPushButton#danger { background: #e53e3e; }
            QTextEdit { background: white; border: 1px solid #e2e8f0; border-radius: 6px; }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 文件选择
        file_group = QGroupBox("文件选择")
        file_layout = QHBoxLayout(file_group)
        self.file_label = QLabel("未选择文件")
        file_layout.addWidget(self.file_label)
        btn_select = QPushButton("选择文件/文件夹")
        btn_select.clicked.connect(self._select_files)
        file_layout.addWidget(btn_select)
        layout.addWidget(file_group)
        
        # 功能标签页
        tabs = QTabWidget()
        
        # 1. 查找替换
        tab1 = QWidget()
        t1_layout = QVBoxLayout(tab1)
        t1_layout.addWidget(QLabel("查找内容:"))
        self.find_input = QLineEdit()
        t1_layout.addWidget(self.find_input)
        t1_layout.addWidget(QLabel("替换为:"))
        self.replace_input = QLineEdit()
        t1_layout.addWidget(self.replace_input)
        self.regex_check = QCheckBox("使用正则表达式")
        t1_layout.addWidget(self.regex_check)
        btn_replace = QPushButton("执行替换")
        btn_replace.clicked.connect(lambda: self._run("replace"))
        t1_layout.addWidget(btn_replace)
        t1_layout.addStretch()
        tabs.addTab(tab1, "查找替换")
        
        # 2. 批量重命名
        tab2 = QWidget()
        t2_layout = QVBoxLayout(tab2)
        t2_layout.addWidget(QLabel("文件名中查找:"))
        self.rename_find = QLineEdit()
        t2_layout.addWidget(self.rename_find)
        t2_layout.addWidget(QLabel("替换为:"))
        self.rename_replace = QLineEdit()
        t2_layout.addWidget(self.rename_replace)
        btn_rename = QPushButton("执行重命名")
        btn_rename.clicked.connect(lambda: self._run("rename"))
        t2_layout.addWidget(btn_rename)
        t2_layout.addStretch()
        tabs.addTab(tab2, "批量重命名")
        
        # 3. 编码转换
        tab3 = QWidget()
        t3_layout = QVBoxLayout(tab3)
        t3_layout.addWidget(QLabel("源编码:"))
        self.from_encoding = QComboBox()
        self.from_encoding.addItems(["gbk", "utf-8", "gb2312", "big5", "latin1"])
        t3_layout.addWidget(self.from_encoding)
        t3_layout.addWidget(QLabel("目标编码:"))
        self.to_encoding = QComboBox()
        self.to_encoding.addItems(["utf-8", "gbk", "gb2312"])
        self.to_encoding.setCurrentIndex(0)
        t3_layout.addWidget(self.to_encoding)
        btn_encoding = QPushButton("转换编码")
        btn_encoding.clicked.connect(lambda: self._run("encoding"))
        t3_layout.addWidget(btn_encoding)
        t3_layout.addStretch()
        tabs.addTab(tab3, "编码转换")
        
        # 4. 行处理
        tab4 = QWidget()
        t4_layout = QVBoxLayout(tab4)
        self.line_op = QComboBox()
        self.line_op.addItems([
            "删除空行", "去重", "Trim空格", "删除指定行"
        ])
        t4_layout.addWidget(self.line_op)
        self.line_num = QSpinBox()
        self.line_num.setMinimum(1)
        t4_layout.addWidget(QLabel("行号（仅删除指定行时有效）:"))
        t4_layout.addWidget(self.line_num)
        btn_line = QPushButton("执行")
        btn_line.clicked.connect(lambda: self._run("line"))
        t4_layout.addWidget(btn_line)
        t4_layout.addStretch()
        tabs.addTab(tab4, "行处理")
        
        layout.addWidget(tabs)
        
        # 进度和日志
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(150)
        layout.addWidget(self.log_area)
        
        # 停止按钮
        btn_stop = QPushButton("停止")
        btn_stop.setObjectName("danger")
        btn_stop.clicked.connect(self._stop)
        layout.addWidget(btn_stop)
    
    def _select_files(self):
        path, _ = QFileDialog.getOpenFileNames(
            self, "选择文本文件", "", 
            "文本文件 (*.txt *.csv *.md *.py *.json *.xml *.html *.js *.css);;所有文件 (*)")
        if path:
            self.files = path
            self.file_label.setText(f"已选择 {len(path)} 个文件")
    
    def _run(self, operation):
        if not self.files:
            QMessageBox.warning(self, "提示", "请先选择文件")
            return
        
        params = {}
        if operation == "replace":
            params = {
                "find": self.find_input.text(),
                "replace": self.replace_input.text(),
                "regex": self.regex_check.isChecked()
            }
        elif operation == "rename":
            params = {
                "pattern": self.rename_find.text(),
                "replace": self.rename_replace.text()
            }
        elif operation == "encoding":
            params = {
                "from": self.from_encoding.currentText(),
                "to": self.to_encoding.currentText()
            }
        elif operation == "line":
            op_map = {"删除空行": "delete_empty", "去重": "unique", 
                     "Trim空格": "trim", "删除指定行": "delete_line"}
            params = {
                "operation": op_map.get(self.line_op.currentText(), ""),
                "line": self.line_num.value() - 1
            }
        
        self.log_area.clear()
        self.progress.setValue(0)
        
        self.thread = BatchTextThread(self.files, operation, params)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.log.connect(self._log)
        self.thread.finished.connect(lambda: QMessageBox.information(self, "完成", "处理完成！"))
        self.thread.start()
    
    def _log(self, msg):
        self.log_area.append(msg)
    
    def _stop(self):
        if self.thread and self.thread.isRunning():
            self.thread.running = False
            self.thread.wait(1000)
