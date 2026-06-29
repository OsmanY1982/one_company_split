# -*- coding: utf-8 -*-
"""
公共 UI 组件库
提供统一的标题、按钮、卡片等可复用组件
"""
from PyQt5.QtWidgets import QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class SectionTitle(QLabel):
    """统一章节标题：18px bold #2c3e50"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")


class Subtitle(QLabel):
    """统一副标题：13px #718096"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setStyleSheet("font-size: 13px; color: #718096;")


class PrimaryButton(QPushButton):
    """蓝色主按钮"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            "background: #3182ce; color: white; border: none; "
            "border-radius: 6px; padding: 8px 16px;"
        )


class SecondaryButton(QPushButton):
    """灰色次按钮"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            "background: #e2e8f0; color: #2d3748; border: none; "
            "border-radius: 6px; padding: 8px 16px;"
        )


class DangerButton(QPushButton):
    """红色危险按钮"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            "background: #e53e3e; color: white; border: none; "
            "border-radius: 6px; padding: 8px 16px;"
        )


class CardWidget(QFrame):
    """统一卡片容器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "background: white; border: 1px solid #e2e8f0; "
            "border-radius: 8px; padding: 16px;"
        )
        self.setFrameShape(QFrame.StyledPanel)
