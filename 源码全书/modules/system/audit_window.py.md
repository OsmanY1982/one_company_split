# `modules/system/audit_window.py`

> 路径：`modules/system/audit_window.py` | 行数：336


---


```python
"""
Audit Window - 桌面端审计日志窗口
PyQt5 实现
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QComboBox, QDateEdit,
    QPushButton, QLabel, QLineEdit, QTabWidget,
    QMessageBox, QFileDialog, QHeaderView
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QColor

import os
from core.paths import DATA_DIR
from services.audit_service import AuditService, AuditAction, AuditLevel


class AuditWindow(QMainWindow):
    """审计日志窗口"""
    
    def __init__(self):
        super().__init__()
        audit_db = os.path.join(DATA_DIR, "audit.db")
        self.service = AuditService(db_path=audit_db)
        self.init_ui()
        self.load_logs()
        
        # 定时刷新
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_logs)
        self.timer.start(30000)  # 30秒刷新
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("操作日志审计")
        self.setGeometry(100, 100, 1200, 700)
        
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        # 用户筛选
        toolbar.addWidget(QLabel("用户:"))
        self.user_filter = QLineEdit()
        self.user_filter.setPlaceholderText("用户ID")
        self.user_filter.setMaximumWidth(150)
        toolbar.addWidget(self.user_filter)
        
        # 操作类型筛选
        toolbar.addWidget(QLabel("操作:"))
        self.action_filter = QComboBox()
        self.action_filter.addItem("全部", None)
        for action in AuditAction:
            self.action_filter.addItem(action.value, action.value)
        toolbar.addWidget(self.action_filter)
        
        # 级别筛选
        toolbar.addWidget(QLabel("级别:"))
        self.level_filter = QComboBox()
        self.level_filter.addItem("全部", None)
        for level in AuditLevel:
            self.level_filter.addItem(level.value, level.value)
        toolbar.addWidget(self.level_filter)
        
        # 日期范围
        toolbar.addWidget(QLabel("从:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setCalendarPopup(True)
        toolbar.addWidget(self.start_date)
        
        toolbar.addWidget(QLabel("至:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        toolbar.addWidget(self.end_date)
        
        # 查询按钮
        query_btn = QPushButton("查询")
        query_btn.clicked.connect(self.load_logs)
        toolbar.addWidget(query_btn)
        
        toolbar.addStretch()
        
        # 导出按钮
        export_btn = QPushButton("导出")
        export_btn.clicked.connect(self.export_logs)
        toolbar.addWidget(export_btn)
        
        layout.addLayout(toolbar)
        
        # 标签页
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 日志列表页
        self.logs_tab = QWidget()
        self.init_logs_tab()
        self.tabs.addTab(self.logs_tab, "审计日志")
        
        # 统计页
        self.stats_tab = QWidget()
        self.init_stats_tab()
        self.tabs.addTab(self.stats_tab, "统计分析")
    
    def init_logs_tab(self):
        """初始化日志列表页"""
        layout = QVBoxLayout(self.logs_tab)
        
        # 日志表格
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(10)
        self.logs_table.setHorizontalHeaderLabels([
            "时间", "用户", "操作", "级别", "资源类型", "资源ID", 
            "状态", "IP地址", "耗时(ms)", "变更内容"
        ])
        
        # 设置列宽
        header = self.logs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.Stretch)
        
        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.logs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.logs_table)
    
    def init_stats_tab(self):
        """初始化统计页"""
        layout = QVBoxLayout(self.stats_tab)
        
        # 统计概览
        stats_layout = QHBoxLayout()
        
        self.total_label = QLabel("总操作: 0")
        stats_layout.addWidget(self.total_label)
        
        self.warning_label = QLabel("警告: 0")
        self.warning_label.setStyleSheet("color: orange;")
        stats_layout.addWidget(self.warning_label)
        
        self.error_label = QLabel("错误: 0")
        self.error_label.setStyleSheet("color: red;")
        stats_layout.addWidget(self.error_label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # 操作类型统计表格
        self.action_stats_table = QTableWidget()
        self.action_stats_table.setColumnCount(2)
        self.action_stats_table.setHorizontalHeaderLabels(["操作类型", "次数"])
        layout.addWidget(QLabel("操作类型分布:"))
        layout.addWidget(self.action_stats_table)
        
        # 用户活跃度表格
        self.user_stats_table = QTableWidget()
        self.user_stats_table.setColumnCount(2)
        self.user_stats_table.setHorizontalHeaderLabels(["用户", "操作次数"])
        layout.addWidget(QLabel("用户活跃度:"))
        layout.addWidget(self.user_stats_table)
    
    def load_logs(self):
        """加载审计日志"""
        # 获取筛选条件
        user_id = self.user_filter.text() or None
        
        action = None
        action_data = self.action_filter.currentData()
        if action_data:
            action = AuditAction(action_data)
        
        level = None
        level_data = self.level_filter.currentData()
        if level_data:
            level = AuditLevel(level_data)
        
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        
        # 查询日志
        logs = self.service.get_logs(
            user_id=user_id,
            action=action,
            level=level,
            start_date=start_date,
            end_date=end_date,
            limit=100
        )
        
        # 更新表格
        self.logs_table.setRowCount(len(logs))
        
        for i, log in enumerate(logs):
            # 时间
            self.logs_table.setItem(i, 0, QTableWidgetItem(
                log.get('timestamp', '')
            ))
            
            # 用户
            self.logs_table.setItem(i, 1, QTableWidgetItem(
                log.get('user_name') or log.get('user_id', '')
            ))
            
            # 操作
            self.logs_table.setItem(i, 2, QTableWidgetItem(
                log.get('action', '')
            ))
            
            # 级别（带颜色）
            level_item = QTableWidgetItem(log.get('level', 'INFO'))
            level_color = self.get_level_color(log.get('level', 'INFO'))
            if level_color:
                level_item.setBackground(level_color)
            self.logs_table.setItem(i, 3, level_item)
            
            # 资源类型
            self.logs_table.setItem(i, 4, QTableWidgetItem(
                log.get('resource_type', '')
            ))
            
            # 资源ID
            self.logs_table.setItem(i, 5, QTableWidgetItem(
                log.get('resource_id', '') or '-'
            ))
            
            # 状态
            status_item = QTableWidgetItem(log.get('status', ''))
            if log.get('status') == 'FAILED':
                status_item.setBackground(QColor(255, 200, 200))
            self.logs_table.setItem(i, 6, status_item)
            
            # IP地址
            self.logs_table.setItem(i, 7, QTableWidgetItem(
                log.get('ip_address', '') or '-'
            ))
            
            # 耗时
            duration = log.get('duration_ms')
            self.logs_table.setItem(i, 8, QTableWidgetItem(
                str(duration) if duration else '-'
            ))
            
            # 变更内容
            changes = log.get('changes')
            changes_text = '-'
            if changes:
                changes_list = []
                for field, change in changes.items():
                    changes_list.append(f"{field}: {change.get('old')} → {change.get('new')}")
                changes_text = '; '.join(changes_list)
            
            self.logs_table.setItem(i, 9, QTableWidgetItem(changes_text))
        
        # 加载统计
        self.load_statistics()
    
    def load_statistics(self):
        """加载统计信息"""
        stats = self.service.get_statistics(days=7)
        
        # 更新概览
        self.total_label.setText(f"总操作: {stats.get('total_operations', 0)}")
        
        anomalies = stats.get('anomalies', {})
        self.warning_label.setText(f"警告: {anomalies.get('WARNING', 0)}")
        self.error_label.setText(f"错误: {anomalies.get('ERROR', 0)}")
        
        # 操作类型统计
        action_stats = stats.get('action_breakdown', {})
        self.action_stats_table.setRowCount(len(action_stats))
        
        for i, (action, count) in enumerate(action_stats.items()):
            self.action_stats_table.setItem(i, 0, QTableWidgetItem(action))
            self.action_stats_table.setItem(i, 1, QTableWidgetItem(str(count)))
        
        # 用户活跃度
        user_stats = stats.get('top_users', [])
        self.user_stats_table.setRowCount(len(user_stats))
        
        for i, user in enumerate(user_stats):
            self.user_stats_table.setItem(i, 0, QTableWidgetItem(user.get('user_id', '')))
            self.user_stats_table.setItem(i, 1, QTableWidgetItem(str(user.get('count', 0))))
    
    def get_level_color(self, level: str) -> QColor:
        """获取级别颜色"""
        colors = {
            'INFO': QColor(200, 230, 255),
            'WARNING': QColor(255, 230, 200),
            'ERROR': QColor(255, 200, 200),
            'CRITICAL': QColor(255, 150, 150),
        }
        return colors.get(level)
    
    def export_logs(self):
        """导出日志"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出审计日志",
            f"audit_logs_{QDate.currentDate().toString('yyyyMMdd')}.json",
            "JSON Files (*.json);;CSV Files (*.csv)"
        )
        
        if file_path:
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            
            format = "json" if file_path.endswith('.json') else "csv"
            content = self.service.export_logs(start_date, end_date, format)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            QMessageBox.information(self, "成功", f"日志已导出到: {file_path}")


# 便捷函数
def show_audit_window():
    """显示审计窗口"""
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = AuditWindow()
    window.show()
    return window

```
