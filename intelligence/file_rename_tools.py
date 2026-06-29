# -*- coding: utf-8 -*-
"""文件批量重命名工具"""
import os
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QGroupBox, QComboBox, QLineEdit, QFileDialog, QHeaderView, QCheckBox)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class FileRenameTools(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("文件批量重命名")
        self.resize(900, 550)
        self.files = []
        self.setStyleSheet("""
            QWidget { background-color: #f5f5f5; }
            QGroupBox { font-weight: bold; font-size: 13px; border: 2px solid #dd6b20; 
                        border-radius: 8px; margin-top: 10px; padding: 10px;
                        background-color: white; }
            QPushButton { background-color: #dd6b20; color: white; border: none;
                          border-radius: 6px; padding: 8px 16px; font-size: 13px; }
            QPushButton:hover { background-color: #c05621; }
            QPushButton#greenBtn { background-color: #38a169; }
            QPushButton#greenBtn:hover { background-color: #2f855a; }
            QLineEdit { border: 1px solid #ccc; border-radius: 4px; padding: 6px; }
            QTableWidget { border: 1px solid #ccc; border-radius: 4px; font-size: 13px; }
            QLabel { font-size: 13px; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 标题
        title = QLabel("📁 文件批量重命名工具")
        title.setFont(QFont("PingFang SC", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 选择文件夹
        folder_group = QGroupBox("📂 选择文件")
        folder_layout = QVBoxLayout(folder_group)
        
        folder_row = QHBoxLayout()
        self.folder_path = QLineEdit()
        self.folder_path.setPlaceholderText("选择要重命名的文件夹...")
        folder_row.addWidget(self.folder_path)
        
        browse_btn = QPushButton("📁 浏览")
        browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(browse_btn)
        
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self._refresh_files)
        folder_row.addWidget(refresh_btn)
        folder_row.addStretch()
        folder_layout.addLayout(folder_row)
        layout.addWidget(folder_group)

        # 重命名规则
        rule_group = QGroupBox("⚙️ 重命名规则")
        rule_layout = QVBoxLayout(rule_group)
        
        rule_type_row = QHBoxLayout()
        rule_type_row.addWidget(QLabel("规则类型:"))
        
        self.rule_combo = QComboBox()
        self.rule_combo.addItems(["替换文本", "添加前缀", "添加后缀", "添加序号", "删除字符", "正则替换"])
        self.rule_combo.currentIndexChanged.connect(self._update_rule_ui)
        rule_type_row.addWidget(self.rule_combo)
        rule_type_row.addStretch()
        rule_layout.addLayout(rule_type_row)
        
        # 规则1: 替换
        self.rule_replace = QWidget()
        replace_layout = QHBoxLayout(self.rule_replace)
        replace_layout.setContentsMargins(0, 5, 0, 5)
        replace_layout.addWidget(QLabel("查找:"))
        self.replace_from = QLineEdit()
        self.replace_from.setPlaceholderText("要替换的文本")
        replace_layout.addWidget(self.replace_from)
        replace_layout.addWidget(QLabel("替换为:"))
        self.replace_to = QLineEdit()
        self.replace_to.setPlaceholderText("替换成的文本")
        replace_layout.addWidget(self.replace_to)
        replace_layout.addStretch()
        rule_layout.addWidget(self.rule_replace)
        
        # 规则2: 前缀后缀
        self.rule_prefix = QWidget()
        prefix_layout = QHBoxLayout(self.rule_prefix)
        prefix_layout.setContentsMargins(0, 5, 0, 5)
        prefix_layout.addWidget(QLabel("前缀:"))
        self.prefix_input = QLineEdit()
        prefix_layout.addWidget(self.prefix_input)
        prefix_layout.addWidget(QLabel("后缀:"))
        self.suffix_input = QLineEdit()
        prefix_layout.addWidget(self.suffix_input)
        prefix_layout.addStretch()
        rule_layout.addWidget(self.rule_prefix)
        
        # 规则3: 序号
        self.rule_seq = QWidget()
        seq_layout = QHBoxLayout(self.rule_seq)
        seq_layout.setContentsMargins(0, 5, 0, 5)
        seq_layout.addWidget(QLabel("序号格式:"))
        self.seq_format = QLineEdit()
        self.seq_format.setPlaceholderText("如: 图片_{:03d}")
        self.seq_format.setText("_{:03d}")
        seq_layout.addWidget(self.seq_format)
        seq_layout.addWidget(QLabel("起始:"))
        self.seq_start = QLineEdit()
        self.seq_start.setText("1")
        self.seq_start.setFixedWidth(60)
        seq_layout.addWidget(self.seq_start)
        seq_layout.addStretch()
        rule_layout.addWidget(self.rule_seq)
        
        # 规则4: 删除字符
        self.rule_delete = QWidget()
        delete_layout = QHBoxLayout(self.rule_delete)
        delete_layout.setContentsMargins(0, 5, 0, 5)
        delete_delete_layout = QHBoxLayout()
        delete_layout.addWidget(QLabel("删除前 N 个字符:"))
        self.delete_count = QLineEdit()
        self.delete_count.setPlaceholderText("如: 3")
        self.delete_count.setFixedWidth(60)
        delete_layout.addWidget(self.delete_count)
        delete_layout.addWidget(QLabel("个"))
        delete_layout.addStretch()
        rule_layout.addWidget(self.rule_delete)
        
        rule_layout.addStretch()
        layout.addWidget(rule_group)

        # 操作按钮
        btn_row = QHBoxLayout()
        preview_btn = QPushButton("👁️ 预览效果")
        preview_btn.clicked.connect(self._preview)
        rename_btn = QPushButton("✅ 执行重命名")
        rename_btn.setObjectName("greenBtn")
        rename_btn.clicked.connect(self._do_rename)
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.clicked.connect(self._clear)
        
        btn_row.addWidget(preview_btn)
        btn_row.addWidget(rename_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # 预览表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["原文件名", "新文件名", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self._update_rule_ui()
        self._refresh_files()

    def _update_rule_ui(self):
        rule = self.rule_combo.currentText()
        self.rule_replace.setVisible(rule == "替换文本")
        self.rule_prefix.setVisible(rule in ["添加前缀", "添加后缀"])
        self.rule_seq.setVisible(rule == "添加序号")
        self.rule_delete.setVisible(rule == "删除字符")

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.folder_path.setText(folder)
            self._refresh_files()

    def _refresh_files(self):
        folder = self.folder_path.text().strip()
        if not folder or not os.path.isdir(folder):
            return
        self.files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        self.table.setRowCount(len(self.files))
        for i, f in enumerate(self.files):
            self.table.setItem(i, 0, QTableWidgetItem(f))
            self.table.setItem(i, 1, QTableWidgetItem(f))
            self.table.setItem(i, 2, QTableWidgetItem("待处理"))

    def _preview(self):
        if not self.files:
            self._refresh_files()
        rule = self.rule_combo.currentText()
        
        for i, f in enumerate(self.files):
            ext = os.path.splitext(f)[1]
            name = os.path.splitext(f)[0]
            new_name = name
            
            if rule == "替换文本":
                find = self.replace_from.text()
                if find:
                    new_name = name.replace(find, self.replace_to.text())
            elif rule == "添加前缀":
                prefix = self.prefix_input.text()
                new_name = prefix + name
            elif rule == "添加后缀":
                suffix = self.suffix_input.text()
                new_name = name + suffix
            elif rule == "添加序号":
                fmt = self.seq_format.text() or "_{:03d}"
                start = int(self.seq_start.text() or "1")
                new_name = fmt.format(i + start)
            elif rule == "删除字符":
                try:
                    count = int(self.delete_count.text() or "0")
                    new_name = name[count:]
                except ValueError:
                    pass
            elif rule == "正则替换":
                try:
                    new_name = re.sub(self.replace_from.text(), self.replace_to.text(), name)
                except Exception: pass
            
            new_file = new_name + ext
            self.table.setItem(i, 1, QTableWidgetItem(new_file))
            self.table.setItem(i, 2, QTableWidgetItem("✅ 预览"))

    def _do_rename(self):
        folder = self.folder_path.text().strip()
        if not folder:
            return
        
        self._preview()
        success = 0
        for i, f in enumerate(self.files):
            new_f = self.table.item(i, 1).text()
            if new_f != f:
                try:
                    os.rename(os.path.join(folder, f), os.path.join(folder, new_f))
                    self.table.setItem(i, 2, QTableWidgetItem("✅ 成功"))
                    success += 1
                except Exception as e:
                    self.table.setItem(i, 2, QTableWidgetItem(f"❌ {e}"))
        
        self._refresh_files()
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "完成", f"成功重命名 {success} 个文件")

    def _clear(self):
        self.table.setRowCount(0)
        self.files = []
        self.folder_path.clear()
