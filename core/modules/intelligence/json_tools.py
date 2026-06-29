# -*- coding: utf-8 -*-
"""JSON格式化工具"""
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QGroupBox, QCheckBox)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class JsonTools(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JSON格式化")
        self.resize(900, 650)
        self.setStyleSheet("""
            QWidget { background-color: #f5f5f5; }
            QGroupBox { font-weight: bold; font-size: 14px; border: 2px solid #805ad5; 
                        border-radius: 8px; margin-top: 10px; padding: 10px;
                        background-color: white; }
            QPushButton { background-color: #805ad5; color: white; border: none;
                          border-radius: 6px; padding: 8px 20px; font-size: 14px; }
            QPushButton:hover { background-color: #6b46c1; }
            QTextEdit { border: 1px solid #ccc; border-radius: 4px; font-family: Menlo; font-size: 13px; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 标题
        title = QLabel("📄 JSON格式化工具")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 操作按钮
        btn_layout = QHBoxLayout()
        format_btn = QPushButton("✨ 格式化 JSON")
        format_btn.clicked.connect(self._format_json)
        minify_btn = QPushButton("⬇️压缩 JSON")
        minify_btn.clicked.connect(self._minify_json)
        copy_btn = QPushButton("📋 复制结果")
        copy_btn.clicked.connect(self._copy_result)
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.clicked.connect(self._clear)
        validate_btn = QPushButton("✅ 验证JSON")
        validate_btn.clicked.connect(self._validate)
        
        btn_layout.addWidget(format_btn)
        btn_layout.addWidget(minify_btn)
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(validate_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 选项
        opt_layout = QHBoxLayout()
        self.indent_cb = QCheckBox("缩进2空格")
        self.indent_cb.setChecked(True)
        opt_layout.addWidget(self.indent_cb)
        self.sort_cb = QCheckBox("按键排序")
        opt_layout.addWidget(self.sort_cb)
        self.escape_cb = QCheckBox("转义中文")
        opt_layout.addWidget(self.escape_cb)
        opt_layout.addStretch()
        layout.addLayout(opt_layout)

        # 输入区域
        input_group = QGroupBox("📥 输入 JSON")
        input_layout = QVBoxLayout(input_group)
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("在此输入或粘贴 JSON 内容...")
        input_layout.addWidget(self.input_text)
        layout.addWidget(input_group)

        # 输出区域
        output_group = QGroupBox("📤 输出结果")
        output_layout = QVBoxLayout(output_group)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("格式化后的 JSON 将显示在这里...")
        output_layout.addWidget(self.output_text)
        layout.addWidget(output_group)

        # 状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #718096; font-size: 13px;")
        layout.addWidget(self.status_label)

    def _set_status(self, msg, color="#718096"):
        self.status_label.setText(msg)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 13px;")

    def _format_json(self):
        try:
            text = self.input_text.toPlainText().strip()
            if not text:
                self._set_status("❌ 请输入JSON内容", "#e53e3e")
                return
            obj = json.loads(text)
            
            kwargs = {"indent": 2 if self.indent_cb.isChecked() else None, "ensure_ascii": not self.escape_cb.isChecked()}
            if self.sort_cb.isChecked():
                kwargs["sort_keys"] = True
            result = json.dumps(obj, **kwargs)
            
            self.output_text.setPlainText(result)
            self._set_status(f"✅ 格式化成功 ({(len(result))} 字符)", "#38a169")
        except json.JSONDecodeError as e:
            self._set_status(f"❌ JSON格式错误: {e}", "#e53e3e")
        except Exception as e:
            self._set_status(f"❌ 错误: {e}", "#e53e3e")

    def _minify_json(self):
        try:
            text = self.input_text.toPlainText().strip()
            if not text:
                self._set_status("❌ 请输入JSON内容", "#e53e3e")
                return
            obj = json.loads(text)
            result = json.dumps(obj, separators=(',', ':'), ensure_ascii=not self.escape_cb.isChecked())
            self.output_text.setPlainText(result)
            self._set_status(f"✅ 压缩成功 ({(len(result))} 字符)", "#38a169")
        except json.JSONDecodeError as e:
            self._set_status(f"❌ JSON格式错误: {e}", "#e53e3e")
        except Exception as e:
            self._set_status(f"❌ 错误: {e}", "#e53e3e")

    def _validate(self):
        try:
            text = self.input_text.toPlainText().strip()
            if not text:
                self._set_status("❌ 请输入JSON内容", "#e53e3e")
                return
            obj = json.loads(text)
            self._set_status(f"✅ JSON格式有效 ({(len(text))} 字符)", "#38a169")
        except json.JSONDecodeError as e:
            self._set_status(f"❌ JSON格式错误: 行{e.lineno}, 列{e.colno}", "#e53e3e")
        except Exception as e:
            self._set_status(f"❌ 错误: {e}", "#e53e3e")

    def _copy_result(self):
        text = self.output_text.toPlainText()
        if text:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(text)
            self._set_status("✅ 已复制到剪贴板", "#38a169")

    def _clear(self):
        self.input_text.clear()
        self.output_text.clear()
        self._set_status("已清空", "#718096")
