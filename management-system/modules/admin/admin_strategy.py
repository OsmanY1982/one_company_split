# 修复core导入
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
# -*- coding: utf-8 -*-
"""
后台管理 - 策略管理
"""
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

class AdminStrategyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QListWidget, QListWidgetItem, QInputDialog, QMessageBox
        layout = QVBoxLayout(self)
        title = QLabel("策略管理")
        title.setStyleSheet("color: #00bcd4; font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # 策略列表
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("background:#23272e;color:#fff;font-size:15px;")
        layout.addWidget(self.list_widget)
        # 加载本地策略
        self.load_strategies()

        # 按钮区
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("添加策略")
        btn_add.setStyleSheet(self.btn_style())
        btn_add.clicked.connect(self.add_strategy)
        btn_layout.addWidget(btn_add)
        btn_edit = QPushButton("编辑策略")
        btn_edit.setStyleSheet(self.btn_style())
        btn_edit.clicked.connect(self.edit_strategy)
        btn_layout.addWidget(btn_edit)
        btn_del = QPushButton("删除策略")
        btn_del.setStyleSheet(self.btn_style())
        btn_del.clicked.connect(self.del_strategy)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()

    def btn_style(self):
        return """
            QPushButton {
                background-color: #2c313c;
                color: #fff;
                font-size: 15px;
                border: none;
                border-radius: 4px;
                padding: 8px 18px;
            }
            QPushButton:hover {
                background-color: #00bcd4;
                color: #23272e;
            }
        """

    def add_strategy(self):
        from modules.admin.strategy_dao import save_strategies
        name, ok = QInputDialog.getText(self, "添加策略", "请输入策略名称：")
        if ok and name:
            self.list_widget.addItem(QListWidgetItem(name))
            self.save_strategies()

    def edit_strategy(self):
        from modules.admin.strategy_dao import save_strategies
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择要编辑的策略！")
            return
        name, ok = QInputDialog.getText(self, "编辑策略", "修改策略名称：", text=item.text())
        if ok and name:
            item.setText(name)
            self.save_strategies()

    def del_strategy(self):
        from modules.admin.strategy_dao import save_strategies
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择要删除的策略！")
            return
        row = self.list_widget.row(item)
        self.list_widget.takeItem(row)
        self.save_strategies()

    def load_strategies(self):
        from modules.admin.strategy_dao import load_strategies
        self.list_widget.clear()
        for name in load_strategies():
            self.list_widget.addItem(QListWidgetItem(name))

    def save_strategies(self):
        from modules.admin.strategy_dao import save_strategies
        names = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        save_strategies(names)
