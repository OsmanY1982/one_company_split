# -*- coding: utf-8 -*-
"""窗口置顶工具"""
import ctypes
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem,
                             QGroupBox, QMessageBox)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer

class WindowTopTools(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("窗口置顶工具")
        self.resize(500, 450)
        self.top_windows = {}  # {(hwnd): (title)}
        self.setStyleSheet("""
            QWidget { background-color: #f5f5f5; }
            QGroupBox { font-weight: bold; font-size: 14px; border: 2px solid #e53e3e; 
                        border-radius: 8px; margin-top: 10px; padding: 10px;
                        background-color: white; }
            QPushButton { background-color: #e53e3e; color: white; border: none;
                          border-radius: 6px; padding: 8px 20px; font-size: 14px; }
            QPushButton:hover { background-color: #c53030; }
            QPushButton#greenBtn { background-color: #38a169; }
            QPushButton#greenBtn:hover { background-color: #2f855a; }
            QListWidget { border: 1px solid #ccc; border-radius: 4px; font-size: 13px; }
            QLabel { font-size: 13px; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 标题
        title = QLabel("📌 窗口置顶工具")
        title.setFont(QFont("PingFang SC", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 说明
        info = QLabel("💡 选择要置顶的窗口，被置顶的窗口会始终显示在最前面")
        info.setStyleSheet("color: #718096; font-size: 13px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

        # 窗口列表
        list_group = QGroupBox("🪟 窗口列表")
        list_layout = QVBoxLayout(list_group)
        self.window_list = QListWidget()
        self.window_list.setMinimumHeight(250)
        list_layout.addWidget(self.window_list)
        layout.addWidget(list_group)

        # 操作按钮
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 刷新列表")
        refresh_btn.clicked.connect(self._refresh_windows)
        pin_btn = QPushButton("📌 置顶选中")
        pin_btn.setObjectName("greenBtn")
        pin_btn.clicked.connect(self._pin_window)
        unpin_btn = QPushButton("📍 取消置顶")
        unpin_btn.clicked.connect(self._unpin_window)
        
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(pin_btn)
        btn_layout.addWidget(unpin_btn)
        layout.addLayout(btn_layout)

        # 当前置顶状态
        self.status_label = QLabel("当前置顶: 无")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #718096; font-size: 13px;")
        layout.addWidget(self.status_label)

        self._refresh_windows()

    def _refresh_windows(self):
        self.window_list.clear()
        self.top_windows.clear()
        
        try:
            import win32gui
            import win32con
            
            def enum_handler(hwnd, ctx):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        self.top_windows[hwnd] = title
                        item = QListWidgetItem(title)
                        item.setData(Qt.UserRole, hwnd)
                        self.window_list.addItem(item)
            
            win32gui.EnumWindows(enum_handler, None)
            
            if self.window_list.count() == 0:
                self.window_list.addItem("未找到窗口（可能需要管理员权限）")
                
        except ImportError:
            self.window_list.addItem("需要安装 pywin32 库")
            self.window_list.addItem("pip install pywin32")

    def _pin_window(self):
        if not self.top_windows:
            QMessageBox.warning(self, "提示", "请先刷新窗口列表")
            return
        
        item = self.window_list.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择一个窗口")
            return
        
        hwnd = item.data(Qt.UserRole)
        if not hwnd:
            return
        
        try:
            import win32gui
            import win32con
            # HWND_TOPMOST = -1, HWND_NOTOPMOST = -2
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                                   win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            self.status_label.setText(f"✅ 已置顶: {self.top_windows.get(hwnd, '?')}")
            self.status_label.setStyleSheet("color: #38a169; font-size: 13px;")
        except Exception as e:
            QMessageBox.warning(self, "失败", f"置顶失败: {e}")

    def _unpin_window(self):
        if not self.top_windows:
            QMessageBox.warning(self, "提示", "请先刷新窗口列表")
            return
        
        item = self.window_list.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择一个窗口")
            return
        
        hwnd = item.data(Qt.UserRole)
        if not hwnd:
            return
        
        try:
            import win32gui
            import win32con
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                   win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            self.status_label.setText(f"📍 已取消置顶: {self.top_windows.get(hwnd, '?')}")
            self.status_label.setStyleSheet("color: #718096; font-size: 13px;")
        except Exception as e:
            QMessageBox.warning(self, "失败", f"取消置顶失败: {e}")
