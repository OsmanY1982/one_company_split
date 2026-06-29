# -*- coding: utf-8 -*-
"""
行业选择界面
让用户选择/切换行业，查看行业专属功能
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGridLayout, QFrame,
    QMessageBox, QApplication, QScrollArea, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from core.modules.industry.industry_config import get_all_industries, get_industry_config, set_industry
from core.modules.industry.industry_adapter import set_industry_adapter, get_adapter


class IndustryCard(QFrame):
    """行业卡片"""
    
    selected = pyqtSignal(str)  # 发送行业类型
    
    def __init__(self, industry_info, parent=None):
        super().__init__(parent)
        self.info = industry_info
        self.setup_ui()
    
    def setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setMinimumSize(280, 200)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 16px;
            }
            QFrame:hover {
                border-color: #2196F3;
                background-color: #f5f9ff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # 图标和名称
        header = QHBoxLayout()
        icon_label = QLabel(self.info['icon'])
        icon_label.setFont(QFont("Apple Color Emoji", 32))
        header.addWidget(icon_label)
        
        name_label = QLabel("<h2>%s</h2>" % self.info['name'])
        name_label.setFont(QFont("PingFang SC", 14, QFont.Bold))
        header.addWidget(name_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # 获取配置
        config = get_industry_config(self.info['type'])
        
        # 关键指标
        kpi_text = "关键指标: " + ", ".join(config.kpi_metrics[:4])
        kpi_label = QLabel(kpi_text)
        kpi_label.setWordWrap(True)
        kpi_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(kpi_label)
        
        # 角色数量
        roles_text = "专属角色: %d个" % len(config.employee_roles)
        roles_label = QLabel(roles_text)
        roles_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(roles_label)
        
        # 选择按钮
        select_btn = QPushButton("选择此行业")
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        select_btn.clicked.connect(lambda: self.selected.emit(self.info['type']))
        layout.addWidget(select_btn)
        
        layout.addStretch()


class IndustryDetailPanel(QWidget):
    """行业详情面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        self.title_label = QLabel("<h2>请选择行业</h2>")
        layout.addWidget(self.title_label)
        
        # 术语表
        self.terms_group = self._create_group("行业术语")
        layout.addWidget(self.terms_group)
        
        # KPI指标
        self.kpi_group = self._create_group("关键指标")
        layout.addWidget(self.kpi_group)
        
        # 角色列表
        self.roles_group = self._create_group("专属角色")
        layout.addWidget(self.roles_group)
        
        # 预警规则
        self.alert_group = self._create_group("预警规则")
        layout.addWidget(self.alert_group)
        
        # 工作流
        self.workflow_group = self._create_group("工作流模板")
        layout.addWidget(self.workflow_group)
        
        layout.addStretch()
    
    def _create_group(self, title):
        """创建分组"""
        from PyQt5.QtWidgets import QGroupBox
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        return group
    
    def update_content(self, industry_type: str):
        """更新内容"""
        config = get_industry_config(industry_type)
        
        self.title_label.setText("<h2>%s %s</h2>" % (config.icon, config.name))
        
        # 更新术语
        terms_layout = QVBoxLayout()
        for key, value in list(config.terminology.items())[:6]:
            terms_layout.addWidget(QLabel("<b>%s</b>: %s" % (key, value)))
        self._set_layout(self.terms_group, terms_layout)
        
        # 更新KPI
        kpi_layout = QVBoxLayout()
        for kpi in config.kpi_metrics:
            kpi_layout.addWidget(QLabel("- %s" % kpi))
        self._set_layout(self.kpi_group, kpi_layout)
        
        # 更新角色
        roles_layout = QVBoxLayout()
        for role in config.employee_roles:
            role_text = "<b>%s</b><br/>%s<br/>技能: %s" % (
                role['name'], 
                role['description'],
                ", ".join(role['skills'])
            )
            roles_layout.addWidget(QLabel(role_text))
        self._set_layout(self.roles_group, roles_layout)
        
        # 更新预警
        alert_layout = QVBoxLayout()
        for key, rule in config.alert_rules.items():
            alert_text = "<b>%s</b>: %s" % (key, rule['message'])
            alert_layout.addWidget(QLabel(alert_text))
        self._set_layout(self.alert_group, alert_layout)
        
        # 更新工作流
        workflow_layout = QVBoxLayout()
        for wf in config.workflow_templates:
            wf_text = "<b>%s</b><br/>%s" % (wf['name'], " → ".join(wf['steps']))
            workflow_layout.addWidget(QLabel(wf_text))
        self._set_layout(self.workflow_group, workflow_layout)
    
    def _set_layout(self, group, layout):
        """设置布局"""
        # 清除旧布局
        old = group.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            import sip
            sip.delete(old)
        group.setLayout(layout)


class IndustryWindow(QMainWindow):
    """行业选择主窗口"""
    
    industry_changed = pyqtSignal(str)  # 行业切换信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_industry = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("行业选择")
        self.setMinimumSize(900, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 左侧：行业卡片
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        title = QLabel("<h1>选择您的行业</h1>")
        title.setStyleSheet("color: #333; margin-bottom: 10px;")
        left_layout.addWidget(title)
        
        desc = QLabel("选择行业后，系统将自动适配专属功能和术语")
        desc.setStyleSheet("color: #666; margin-bottom: 20px;")
        left_layout.addWidget(desc)
        
        # 行业卡片网格
        cards_widget = QWidget()
        cards_layout = QGridLayout(cards_widget)
        cards_layout.setSpacing(16)
        
        industries = get_all_industries()
        for i, ind in enumerate(industries):
            card = IndustryCard(ind)
            card.selected.connect(self.on_industry_selected)
            cards_layout.addWidget(card, i // 2, i % 2)
        
        left_layout.addWidget(cards_widget)
        left_layout.addStretch()
        
        # 右侧：详情面板
        self.detail_panel = IndustryDetailPanel()
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.detail_panel)
        splitter.setSizes([450, 450])
        
        layout.addWidget(splitter)
    
    def on_industry_selected(self, industry_type: str):
        """选择行业"""
        self.current_industry = industry_type
        
        # 更新详情
        self.detail_panel.update_content(industry_type)
        
        # 设置全局行业
        set_industry_adapter(industry_type)
        
        # 发送信号
        self.industry_changed.emit(industry_type)
        
        # 提示
        config = get_industry_config(industry_type)
        QMessageBox.information(
            self, 
            "行业切换成功", 
            "已切换到: %s %s\n系统已自动适配行业专属功能。" % (config.icon, config.name)
        )


def main():
    app = QApplication(sys.argv)
    window = IndustryWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
