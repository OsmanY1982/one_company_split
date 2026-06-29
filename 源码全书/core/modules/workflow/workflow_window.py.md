# `core/modules/workflow/workflow_window.py`

> 路径：`core/modules/workflow/workflow_window.py` | 行数：422


---


```python
"""
Workflow Window - 桌面端工作流管理窗口
PyQt5 实现
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QComboBox, QPushButton,
    QLabel, QLineEdit, QTabWidget, QDialog, QDialogButtonBox,
    QTextEdit, QFormLayout, QMessageBox, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal

import os
from core.database import get_conn, close_conn
from workflow_service import WorkflowService, WorkflowStatus, NodeType


class WorkflowWindow(QMainWindow):
    """工作流管理窗口"""
    
    def __init__(self):
        super().__init__()
        self.service = WorkflowService()
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("工作流引擎")
        self.setGeometry(100, 100, 1200, 700)
        
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 标签页
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 待办任务页
        self.todo_tab = QWidget()
        self.init_todo_tab()
        self.tabs.addTab(self.todo_tab, "待办任务")
        
        # 流程实例页
        self.instance_tab = QWidget()
        self.init_instance_tab()
        self.tabs.addTab(self.instance_tab, "流程实例")
        
        # 流程定义页
        self.definition_tab = QWidget()
        self.init_definition_tab()
        self.tabs.addTab(self.definition_tab, "流程定义")
        
        # 历史记录页
        self.history_tab = QWidget()
        self.init_history_tab()
        self.tabs.addTab(self.history_tab, "历史记录")
    
    def init_todo_tab(self):
        """初始化待办任务页"""
        layout = QVBoxLayout(self.todo_tab)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        toolbar.addWidget(QLabel("用户:"))
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("输入用户ID")
        toolbar.addWidget(self.user_input)
        
        query_btn = QPushButton("查询")
        query_btn.clicked.connect(self.load_todo_tasks)
        toolbar.addWidget(query_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 任务列表
        self.todo_table = QTableWidget()
        self.todo_table.setColumnCount(7)
        self.todo_table.setHorizontalHeaderLabels([
            "任务ID", "流程", "业务Key", "节点", "创建时间", "状态", "操作"
        ])
        layout.addWidget(self.todo_table)
    
    def init_instance_tab(self):
        """初始化流程实例页"""
        layout = QVBoxLayout(self.instance_tab)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        new_btn = QPushButton("新建流程")
        new_btn.clicked.connect(self.create_new_instance)
        toolbar.addWidget(new_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 实例列表
        self.instance_table = QTableWidget()
        self.instance_table.setColumnCount(6)
        self.instance_table.setHorizontalHeaderLabels([
            "实例ID", "流程", "业务Key", "状态", "当前节点", "创建时间"
        ])
        layout.addWidget(self.instance_table)
    
    def init_definition_tab(self):
        """初始化流程定义页"""
        layout = QVBoxLayout(self.definition_tab)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        new_btn = QPushButton("新建流程定义")
        new_btn.clicked.connect(self.create_new_definition)
        toolbar.addWidget(new_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 定义列表
        self.definition_table = QTableWidget()
        self.definition_table.setColumnCount(5)
        self.definition_table.setHorizontalHeaderLabels([
            "ID", "代码", "名称", "版本", "状态"
        ])
        layout.addWidget(self.definition_table)
    
    def init_history_tab(self):
        """初始化历史记录页"""
        layout = QVBoxLayout(self.history_tab)
        
        # 查询条件
        toolbar = QHBoxLayout()
        
        toolbar.addWidget(QLabel("实例ID:"))
        self.history_instance_input = QLineEdit()
        toolbar.addWidget(self.history_instance_input)
        
        query_btn = QPushButton("查询")
        query_btn.clicked.connect(self.load_history)
        toolbar.addWidget(query_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 历史记录树
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["时间", "节点", "操作", "操作人", "备注"])
        layout.addWidget(self.history_tree)
    
    def load_data(self):
        """加载所有数据"""
        self.load_todo_tasks()
        self.load_instances()
        self.load_definitions()
    
    def load_todo_tasks(self):
        """加载待办任务"""
        user_id = self.user_input.text().strip() or None
        tasks = self.service.get_tasks(user_id=user_id)
        
        self.todo_table.setRowCount(len(tasks))
        
        for i, task in enumerate(tasks):
            self.todo_table.setItem(i, 0, QTableWidgetItem(str(task['id'])))
            self.todo_table.setItem(i, 1, QTableWidgetItem(task.get('workflow_name', '')))
            self.todo_table.setItem(i, 2, QTableWidgetItem(task.get('business_key', '') or '-'))
            self.todo_table.setItem(i, 3, QTableWidgetItem(task.get('node_name', '')))
            self.todo_table.setItem(i, 4, QTableWidgetItem(task.get('created_at', '')))
            self.todo_table.setItem(i, 5, QTableWidgetItem(task.get('status', '')))
            
            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            
            approve_btn = QPushButton("通过")
            approve_btn.clicked.connect(lambda checked, t=task: self.approve_task(t))
            btn_layout.addWidget(approve_btn)
            
            reject_btn = QPushButton("拒绝")
            reject_btn.clicked.connect(lambda checked, t=task: self.reject_task(t))
            btn_layout.addWidget(reject_btn)
            
            btn_layout.setContentsMargins(5, 0, 5, 0)
            self.todo_table.setCellWidget(i, 6, btn_widget)
    
    def load_instances(self):
        """加载流程实例"""
        conn = get_conn(os.path.basename(self.service.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT i.*, wd.name as workflow_name
            FROM workflow_instances i
            JOIN workflow_definitions wd ON i.definition_id = wd.id
            ORDER BY i.created_at DESC
        """)
        
        instances = cursor.fetchall()
        self.instance_table.setRowCount(len(instances))
        
        for i, instance in enumerate(instances):
            self.instance_table.setItem(i, 0, QTableWidgetItem(str(instance['id'])))
            self.instance_table.setItem(i, 1, QTableWidgetItem(instance['workflow_name']))
            self.instance_table.setItem(i, 2, QTableWidgetItem(instance['business_key'] or '-'))
            self.instance_table.setItem(i, 3, QTableWidgetItem(instance['status']))
            self.instance_table.setItem(i, 4, QTableWidgetItem(instance['current_node'] or '-'))
            self.instance_table.setItem(i, 5, QTableWidgetItem(instance['created_at']))
        
        close_conn(os.path.basename(self.service.db_path))
    
    def load_definitions(self):
        """加载流程定义"""
        conn = get_conn(os.path.basename(self.service.db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM workflow_definitions WHERE is_active = 1")
        definitions = cursor.fetchall()
        
        self.definition_table.setRowCount(len(definitions))
        
        for i, defn in enumerate(definitions):
            self.definition_table.setItem(i, 0, QTableWidgetItem(str(defn['id'])))
            self.definition_table.setItem(i, 1, QTableWidgetItem(defn['code']))
            self.definition_table.setItem(i, 2, QTableWidgetItem(defn['name']))
            self.definition_table.setItem(i, 3, QTableWidgetItem(str(defn['version'])))
            self.definition_table.setItem(i, 4, QTableWidgetItem('启用' if defn['is_active'] else '停用'))
        
        close_conn(os.path.basename(self.service.db_path))
    
    def load_history(self):
        """加载历史记录"""
        instance_id = self.history_instance_input.text().strip()
        if not instance_id:
            QMessageBox.warning(self, "警告", "请输入实例ID")
            return
        
        history = self.service.get_instance_history(int(instance_id))
        
        self.history_tree.clear()
        
        for record in history:
            item = QTreeWidgetItem([
                record.get('created_at', ''),
                record.get('node_name', ''),
                record.get('action', ''),
                record.get('operator', ''),
                record.get('comment', '')
            ])
            self.history_tree.addTopLevelItem(item)
    
    def approve_task(self, task):
        """通过任务"""
        self._complete_task_dialog(task, "approve", "通过")
    
    def reject_task(self, task):
        """拒绝任务"""
        self._complete_task_dialog(task, "reject", "拒绝")
    
    def _complete_task_dialog(self, task, action, action_name):
        """完成任务对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{action_name}任务")
        dialog.setGeometry(200, 200, 400, 200)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel(f"任务: {task.get('node_name', '')}"))
        layout.addWidget(QLabel(f"流程: {task.get('workflow_name', '')}"))
        
        layout.addWidget(QLabel("备注:"))
        comment_input = QTextEdit()
        comment_input.setMaximumHeight(80)
        layout.addWidget(comment_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            user_id = self.user_input.text().strip() or "system"
            self.service.complete_task(
                task_id=task['id'],
                action=action,
                operator=user_id,
                comment=comment_input.toPlainText()
            )
            self.load_todo_tasks()
            self.load_instances()
    
    def create_new_instance(self):
        """创建新流程实例"""
        dialog = QDialog(self)
        dialog.setWindowTitle("新建流程实例")
        dialog.setGeometry(200, 200, 400, 300)
        
        layout = QFormLayout(dialog)
        
        # 流程定义选择
        def_combo = QComboBox()
        conn = get_conn(os.path.basename(self.service.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT code, name FROM workflow_definitions WHERE is_active = 1")
        for code, name in cursor.fetchall():
            def_combo.addItem(f"{name} ({code})", code)
        close_conn(os.path.basename(self.service.db_path))
        layout.addRow("流程定义:", def_combo)
        
        # 业务Key
        business_input = QLineEdit()
        layout.addRow("业务Key:", business_input)
        
        # 变量
        vars_input = QTextEdit()
        vars_input.setPlaceholderText('{"key": "value"}')
        vars_input.setMaximumHeight(80)
        layout.addRow("变量:", vars_input)
        
        # 启动人
        starter_input = QLineEdit()
        starter_input.setText(self.user_input.text())
        layout.addRow("启动人:", starter_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                variables = {}
                if vars_input.toPlainText():
                    import json
                    variables = json.loads(vars_input.toPlainText())
                
                instance_id = self.service.start_instance(
                    definition_code=def_combo.currentData(),
                    business_key=business_input.text() or None,
                    variables=variables,
                    started_by=starter_input.text() or None
                )
                
                QMessageBox.information(self, "成功", f"流程实例已启动: {instance_id}")
                self.load_instances()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))
    
    def create_new_definition(self):
        """创建新流程定义"""
        dialog = QDialog(self)
        dialog.setWindowTitle("新建流程定义")
        dialog.setGeometry(200, 200, 500, 400)
        
        layout = QFormLayout(dialog)
        
        code_input = QLineEdit()
        layout.addRow("流程代码:", code_input)
        
        name_input = QLineEdit()
        layout.addRow("流程名称:", name_input)
        
        desc_input = QLineEdit()
        layout.addRow("描述:", desc_input)
        
        # 流程定义JSON
        def_input = QTextEdit()
        def_input.setPlaceholderText("""{
  "nodes": [
    {"id": "start", "type": "start", "next": "task1"},
    {"id": "task1", "type": "approval", "name": "审批", "assignee": "manager", "next": "end"},
    {"id": "end", "type": "end"}
  ]
}""")
        layout.addRow("流程定义:", def_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                import json
                definition = json.loads(def_input.toPlainText())
                
                self.service.create_definition(
                    code=code_input.text(),
                    name=name_input.text(),
                    description=desc_input.text(),
                    definition=definition
                )
                
                QMessageBox.information(self, "成功", "流程定义已创建")
                self.load_definitions()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))


# 便捷函数
def show_workflow_window():
    """显示工作流窗口"""
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = WorkflowWindow()
    window.show()
    return window

```
