# -*- coding: utf-8 -*-
"""时间戳转换工具"""
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QGroupBox, QComboBox)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class TimestampTools(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("时间戳转换")
        self.resize(600, 400)
        self.setStyleSheet("""
            QWidget { background-color: #f5f5f5; }
            QGroupBox { font-weight: bold; font-size: 14px; border: 2px solid #38a169; 
                        border-radius: 8px; margin-top: 10px; padding: 10px;
                        background-color: white; }
            QPushButton { background-color: #38a169; color: white; border: none;
                          border-radius: 6px; padding: 8px 20px; font-size: 14px; }
            QPushButton:hover { background-color: #2f855a; }
            QLineEdit { border: 1px solid #ccc; border-radius: 4px; padding: 6px; font-size: 14px; }
            QTextEdit { border: 1px solid #ccc; border-radius: 4px; font-size: 13px; }
            QLabel { font-size: 14px; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 标题
        title = QLabel("⏰ 时间戳转换工具")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ── 当前时间信息 ──
        time_group = QGroupBox("🕐 当前时间")
        time_layout = QVBoxLayout(time_group)
        self.time_label = QLabel()
        self.time_label.setFont(QFont("Menlo", 14))
        self.time_label.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(self.time_label)
        
        now_btn = QPushButton("🔄 刷新当前时间")
        now_btn.clicked.connect(self._update_now)
        time_layout.addWidget(now_btn)
        layout.addWidget(time_group)

        # ── 时间戳 → 日期 ──
        ts_group = QGroupBox("📅 时间戳 → 日期")
        ts_layout = QVBoxLayout(ts_group)
        ts_input = QHBoxLayout()
        ts_input.addWidget(QLabel("时间戳(秒):"))
        self.ts_input = QLineEdit()
        self.ts_input.setPlaceholderText("输入时间戳，如 1711680000")
        ts_input.addWidget(self.ts_input)
        ts_layout.addLayout(ts_input)
        
        ts_result_layout = QVBoxLayout()
        self.ts_result = QLabel("转换结果将显示在这里")
        self.ts_result.setFont(QFont("Menlo", 13))
        ts_result_layout.addWidget(self.ts_result)
        
        ts_btn_row = QHBoxLayout()
        ts_to_date_btn = QPushButton("▶ 转换为日期")
        ts_to_date_btn.clicked.connect(self._ts_to_date)
        ts_now_btn = QPushButton("🕐 当前时间戳")
        ts_now_btn.clicked.connect(lambda: self.ts_input.setText(str(int(datetime.now().timestamp()))))
        ts_now_13_btn = QPushButton("🕐 当前时间戳(毫秒)")
        ts_now_13_btn.clicked.connect(lambda: self.ts_input.setText(str(int(datetime.now().timestamp() * 1000))))
        ts_btn_row.addWidget(ts_to_date_btn)
        ts_btn_row.addWidget(ts_now_btn)
        ts_btn_row.addWidget(ts_now_13_btn)
        ts_result_layout.addLayout(ts_btn_row)
        ts_layout.addLayout(ts_result_layout)
        layout.addWidget(ts_group)

        # ── 日期 → 时间戳 ──
        date_group = QGroupBox("📆 日期 → 时间戳")
        date_layout = QVBoxLayout(date_group)
        date_input = QHBoxLayout()
        date_input.addWidget(QLabel("日期格式:"))
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("输入日期，如 2024-03-29 12:00:00")
        date_input.addWidget(self.date_input)
        date_layout.addLayout(date_input)
        
        date_result_layout = QVBoxLayout()
        self.date_result = QLabel("转换结果将显示在这里")
        self.date_result.setFont(QFont("Menlo", 13))
        date_result_layout.addWidget(self.date_result)
        
        date_btn_row = QHBoxLayout()
        date_to_ts_btn = QPushButton("▶ 转换为时间戳")
        date_to_ts_btn.clicked.connect(self._date_to_ts)
        date_now_btn = QPushButton("🕐 现在时间")
        date_now_btn.clicked.connect(lambda: self.date_input.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        date_btn_row.addWidget(date_to_ts_btn)
        date_btn_row.addWidget(date_now_btn)
        date_result_layout.addLayout(date_btn_row)
        date_layout.addLayout(date_result_layout)
        layout.addWidget(date_group)

        self._update_now()

    def _update_now(self):
        now = datetime.now()
        ts = int(now.timestamp())
        self.time_label.setText(
            f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"时间戳(秒): {ts}  |  时间戳(毫秒): {ts * 1000}"
        )

    def _ts_to_date(self):
        try:
            ts_str = self.ts_input.text().strip()
            if len(ts_str) == 13:
                ts = int(ts_str) / 1000
            else:
                ts = int(ts_str)
            dt = datetime.fromtimestamp(ts)
            self.ts_result.setText(
                f"转换结果:\n"
                f"📅 日期: {dt.strftime('%Y-%m-%d')}\n"
                f"🕐 时间: {dt.strftime('%H:%M:%S')}\n"
                f"📋 完整: {dt.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except ValueError:
            self.ts_result.setText("❌ 请输入有效的时间戳（纯数字）")
        except Exception as e:
            self.ts_result.setText(f"❌ 转换失败: {e}")

    def _date_to_ts(self):
        try:
            date_str = self.date_input.text().strip()
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            ts = int(dt.timestamp())
            self.date_result.setText(
                f"转换结果:\n"
                f"⏱️ 时间戳(秒): {ts}\n"
                f"⏱️ 时间戳(毫秒): {ts * 1000}"
            )
        except ValueError:
            self.date_result.setText("❌ 日期格式错误，请使用: 2024-03-29 12:00:00")
        except Exception as e:
            self.date_result.setText(f"❌ 转换失败: {e}")
