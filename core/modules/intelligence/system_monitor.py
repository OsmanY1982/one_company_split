# -*- coding: utf-8 -*-
"""
系统监控面板 - 实时显示系统状态和AI能力使用情况
"""

import os
import sys
import time
import psutil
from datetime import datetime
from typing import Dict, Any

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QTextEdit
)
from PyQt5.QtCore import QTimer, Qt


class SystemMonitorWidget(QWidget):
    """系统监控组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_timer()
        
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 标题
        title = QLabel("🔍 系统监控面板")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # 系统资源
        resource_group = QGroupBox("系统资源")
        resource_layout = QGridLayout(resource_group)
        
        # CPU
        resource_layout.addWidget(QLabel("CPU使用率:"), 0, 0)
        self._cpu_bar = QProgressBar()
        self._cpu_bar.setRange(0, 100)
        resource_layout.addWidget(self._cpu_bar, 0, 1)
        self._cpu_label = QLabel("0%")
        resource_layout.addWidget(self._cpu_label, 0, 2)
        
        # 内存
        resource_layout.addWidget(QLabel("内存使用率:"), 1, 0)
        self._mem_bar = QProgressBar()
        self._mem_bar.setRange(0, 100)
        resource_layout.addWidget(self._mem_bar, 1, 1)
        self._mem_label = QLabel("0%")
        resource_layout.addWidget(self._mem_label, 1, 2)
        
        # 磁盘
        resource_layout.addWidget(QLabel("磁盘使用率:"), 2, 0)
        self._disk_bar = QProgressBar()
        self._disk_bar.setRange(0, 100)
        resource_layout.addWidget(self._disk_bar, 2, 1)
        self._disk_label = QLabel("0%")
        resource_layout.addWidget(self._disk_label, 2, 2)
        
        layout.addWidget(resource_group)
        
        # AI能力使用统计
        stats_group = QGroupBox("AI能力使用统计")
        stats_layout = QVBoxLayout(stats_group)
        
        self._stats_table = QTableWidget()
        self._stats_table.setColumnCount(4)
        self._stats_table.setHorizontalHeaderLabels(["能力", "调用次数", "成功率", "平均响应时间"])
        self._stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        stats_layout.addWidget(self._stats_table)
        
        layout.addWidget(stats_group)
        
        # 日志输出
        log_group = QGroupBox("系统日志")
        log_layout = QVBoxLayout(log_group)
        
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMaximumHeight(150)
        log_layout.addWidget(self._log_text)
        
        # 清除日志按钮
        clear_btn = QPushButton("清除日志")
        clear_btn.clicked.connect(self._clear_logs)
        log_layout.addWidget(clear_btn)
        
        layout.addWidget(log_group)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 立即刷新")
        refresh_btn.clicked.connect(self._update_stats)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
        
    def _setup_timer(self):
        """设置定时器"""
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_stats)
        self._timer.start(5000)  # 每5秒更新一次
        
    def _update_stats(self):
        """更新统计信息"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self._cpu_bar.setValue(int(cpu_percent))
            self._cpu_label.setText(f"{cpu_percent:.1f}%")
            
            # 内存
            mem = psutil.virtual_memory()
            self._mem_bar.setValue(int(mem.percent))
            self._mem_label.setText(f"{mem.percent:.1f}%")
            
            # 磁盘
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self._disk_bar.setValue(int(disk_percent))
            self._disk_label.setText(f"{disk_percent:.1f}%")
            
            # 更新AI统计（示例数据）
            self._update_ai_stats()
            
        except Exception as e:
            self._log(f"更新统计失败: {e}")
            
    def _update_ai_stats(self):
        """更新AI能力统计"""
        # 示例数据，实际应从数据库或文件读取
        stats = [
            ("多引擎搜索", 45, "95%", "1.2s"),
            ("文件操作", 120, "98%", "0.3s"),
            ("代码执行", 30, "90%", "2.1s"),
            ("浏览器自动化", 15, "85%", "5.4s"),
            ("定时任务", 8, "100%", "0.1s"),
            ("记忆系统", 200, "99%", "0.1s"),
            ("会话管理", 50, "100%", "0.2s"),
        ]
        
        self._stats_table.setRowCount(len(stats))
        for i, (name, count, success, time) in enumerate(stats):
            self._stats_table.setItem(i, 0, QTableWidgetItem(name))
            self._stats_table.setItem(i, 1, QTableWidgetItem(str(count)))
            self._stats_table.setItem(i, 2, QTableWidgetItem(success))
            self._stats_table.setItem(i, 3, QTableWidgetItem(time))
            
    def _clear_logs(self):
        """清除日志"""
        self._log_text.clear()
        
    def _log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._log_text.append(f"[{timestamp}] {message}")


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    widget = SystemMonitorWidget()
    widget.setWindowTitle("系统监控面板")
    widget.resize(600, 500)
    widget.show()
    sys.exit(app.exec_())
