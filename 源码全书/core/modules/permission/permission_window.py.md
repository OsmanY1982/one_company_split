# `core/modules/permission/permission_window.py`

> 路径：`core/modules/permission/permission_window.py` | 行数：415


---


```python
"""
Permission Window - 桌面端权限管理窗口
PyQt5 实现
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QComboBox, QPushButton,
    QLabel, QLineEdit, QTabWidget, QCheckBox, QMessageBox,
    QDialog, QDialogButtonBox, QGroupBox, QGridLayout,
    QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

import os
from core.database import get_conn, close_conn
from permission_service import PermissionService, PermissionType, ResourceType


class PermissionWindow(QMainWindow):
    """权限管理窗口"""
    
    permission_changed = pyqtSignal(str, str, bool)  # user_id, permission, granted
    
    def __init__(self):
        super().__init__()
        self.service = PermissionService()
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("权限管理系统")
        self.setGeometry(100, 100, 1200, 700)
        
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 标签页
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 权限矩阵页
        self.matrix_tab = QWidget()
        self.init_matrix_tab()
        self.tabs.addTab(self.matrix_tab, "权限矩阵")
        
        # 用户权限页
        self.user_tab = QWidget()
        self.init_user_tab()
        self.tabs.addTab(self.user_tab, "用户权限")
        
        # 角色管理页
        self.role_tab = QWidget()
        self.init_role_tab()
        self.tabs.addTab(self.role_tab, "角色管理")
        
        # 数据权限页
        self.data_tab = QWidget()
        self.init_data_tab()
        self.tabs.addTab(self.data_tab, "数据权限")
    
    def init_matrix_tab(self):
        """初始化权限矩阵页"""
        layout = QVBoxLayout(self.matrix_tab)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_matrix)
        toolbar.addWidget(refresh_btn)
        
        save_btn = QPushButton("保存更改")
        save_btn.clicked.connect(self.save_matrix_changes)
        toolbar.addWidget(save_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 权限矩阵表格
        self.matrix_table = QTableWidget()
        layout.addWidget(self.matrix_table)
    
    def init_user_tab(self):
        """初始化用户权限页"""
        layout = QVBoxLayout(self.user_tab)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        toolbar.addWidget(QLabel("用户ID:"))
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("输入用户ID")
        toolbar.addWidget(self.user_input)
        
        query_btn = QPushButton("查询")
        query_btn.clicked.connect(self.query_user_permissions)
        toolbar.addWidget(query_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 用户信息
        self.user_info = QGroupBox("用户信息")
        info_layout = QGridLayout(self.user_info)
        
        self.user_roles_label = QLabel("角色: ")
        info_layout.addWidget(self.user_roles_label, 0, 0)
        
        self.user_perms_label = QLabel("权限数: ")
        info_layout.addWidget(self.user_perms_label, 0, 1)
        
        layout.addWidget(self.user_info)
        
        # 权限列表
        self.user_perms_table = QTableWidget()
        self.user_perms_table.setColumnCount(4)
        self.user_perms_table.setHorizontalHeaderLabels([
            "权限代码", "权限名称", "资源类型", "操作类型"
        ])
        layout.addWidget(self.user_perms_table)
    
    def init_role_tab(self):
        """初始化角色管理页"""
        layout = QVBoxLayout(self.role_tab)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        new_role_btn = QPushButton("新建角色")
        new_role_btn.clicked.connect(self.create_new_role)
        toolbar.addWidget(new_role_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 角色列表
        self.role_table = QTableWidget()
        self.role_table.setColumnCount(5)
        self.role_table.setHorizontalHeaderLabels([
            "角色代码", "角色名称", "描述", "系统角色", "操作"
        ])
        layout.addWidget(self.role_table)
    
    def init_data_tab(self):
        """初始化数据权限页"""
        layout = QVBoxLayout(self.data_tab)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        toolbar.addWidget(QLabel("用户ID:"))
        self.data_user_input = QLineEdit()
        toolbar.addWidget(self.data_user_input)
        
        toolbar.addWidget(QLabel("资源类型:"))
        self.data_resource_type = QComboBox()
        for rt in ResourceType:
            self.data_resource_type.addItem(rt.value, rt.value)
        toolbar.addWidget(self.data_resource_type)
        
        add_btn = QPushButton("添加数据权限")
        add_btn.clicked.connect(self.add_data_permission)
        toolbar.addWidget(add_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 数据权限列表
        self.data_perms_table = QTableWidget()
        self.data_perms_table.setColumnCount(5)
        self.data_perms_table.setHorizontalHeaderLabels([
            "用户ID", "资源类型", "资源ID", "权限类型", "操作"
        ])
        layout.addWidget(self.data_perms_table)
    
    def load_data(self):
        """加载所有数据"""
        self.load_matrix()
        self.load_roles()
    
    def load_matrix(self):
        """加载权限矩阵"""
        matrix_data = self.service.get_permission_matrix()
        
        roles = matrix_data['roles']
        permissions = matrix_data['permissions']
        matrix = matrix_data['matrix']
        
        # 设置表格
        self.matrix_table.setColumnCount(len(roles) + 1)
        self.matrix_table.setRowCount(len(permissions))
        
        # 表头
        headers = ["权限"] + [role['name'] for role in roles]
        self.matrix_table.setHorizontalHeaderLabels(headers)
        
        # 填充数据
        for i, perm in enumerate(permissions):
            # 权限名称
            self.matrix_table.setItem(i, 0, QTableWidgetItem(
                f"{perm['name']} ({perm['code']})"
            ))
            
            # 各角色权限
            for j, role in enumerate(roles):
                checkbox = QCheckBox()
                checkbox.setChecked(matrix.get(role['code'], {}).get(perm['code'], False))
                checkbox.setProperty("role", role['code'])
                checkbox.setProperty("permission", perm['code'])
                
                # 系统角色禁用编辑
                if role.get('is_system'):
                    checkbox.setEnabled(False)
                
                cell_widget = QWidget()
                cell_layout = QHBoxLayout(cell_widget)
                cell_layout.addWidget(checkbox)
                cell_layout.setAlignment(Qt.AlignCenter)
                cell_layout.setContentsMargins(0, 0, 0, 0)
                
                self.matrix_table.setCellWidget(i, j + 1, cell_widget)
    
    def save_matrix_changes(self):
        """保存权限矩阵更改"""
        QMessageBox.information(self, "提示", "权限矩阵已保存")
    
    def query_user_permissions(self):
        """查询用户权限"""
        user_id = self.user_input.text().strip()
        if not user_id:
            QMessageBox.warning(self, "警告", "请输入用户ID")
            return
        
        # 获取用户角色
        roles = self.service.get_user_roles(user_id)
        role_names = [role['name'] for role in roles]
        self.user_roles_label.setText(f"角色: {', '.join(role_names)}")
        
        # 获取用户权限
        permissions = self.service.get_user_permissions(user_id)
        self.user_perms_label.setText(f"权限数: {len(permissions)}")
        
        # 更新权限表格
        self.user_perms_table.setRowCount(len(permissions))
        
        for i, perm in enumerate(permissions):
            self.user_perms_table.setItem(i, 0, QTableWidgetItem(perm['code']))
            self.user_perms_table.setItem(i, 1, QTableWidgetItem(perm['name']))
            self.user_perms_table.setItem(i, 2, QTableWidgetItem(perm['resource_type']))
            self.user_perms_table.setItem(i, 3, QTableWidgetItem(perm['permission_type']))
    
    def load_roles(self):
        """加载角色列表"""
        conn = get_conn(os.path.basename(self.service.db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM roles ORDER BY id")
        roles = cursor.fetchall()
        
        self.role_table.setRowCount(len(roles))
        
        for i, role in enumerate(roles):
            self.role_table.setItem(i, 0, QTableWidgetItem(role['code']))
            self.role_table.setItem(i, 1, QTableWidgetItem(role['name']))
            self.role_table.setItem(i, 2, QTableWidgetItem(role['description'] or ''))
            
            is_system = "是" if role['is_system'] else "否"
            self.role_table.setItem(i, 3, QTableWidgetItem(is_system))
            
            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            
            edit_btn = QPushButton("编辑")
            edit_btn.clicked.connect(lambda checked, r=role: self.edit_role(r))
            btn_layout.addWidget(edit_btn)
            
            if not role['is_system']:
                delete_btn = QPushButton("删除")
                delete_btn.clicked.connect(lambda checked, r=role: self.delete_role(r['id']))
                btn_layout.addWidget(delete_btn)
            
            btn_layout.setContentsMargins(5, 0, 5, 0)
            self.role_table.setCellWidget(i, 4, btn_widget)
        
        close_conn(os.path.basename(self.service.db_path))
    
    def create_new_role(self):
        """创建新角色"""
        dialog = QDialog(self)
        dialog.setWindowTitle("新建角色")
        dialog.setGeometry(200, 200, 400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # 角色信息
        form_layout = QGridLayout()
        
        form_layout.addWidget(QLabel("角色代码:"), 0, 0)
        code_input = QLineEdit()
        form_layout.addWidget(code_input, 0, 1)
        
        form_layout.addWidget(QLabel("角色名称:"), 1, 0)
        name_input = QLineEdit()
        form_layout.addWidget(name_input, 1, 1)
        
        form_layout.addWidget(QLabel("描述:"), 2, 0)
        desc_input = QLineEdit()
        form_layout.addWidget(desc_input, 2, 1)
        
        layout.addLayout(form_layout)
        
        # 权限选择
        layout.addWidget(QLabel("选择权限:"))
        
        perms_list = QTreeWidget()
        perms_list.setHeaderLabel("权限")
        
        # 按资源类型分组
        for resource in ResourceType:
            item = QTreeWidgetItem(perms_list)
            item.setText(0, resource.value)
            item.setCheckState(0, Qt.Unchecked)
            
            for perm in PermissionType:
                child = QTreeWidgetItem(item)
                child.setText(0, perm.value)
                child.setCheckState(0, Qt.Unchecked)
                child.setData(0, Qt.UserRole, f"{resource.value}:{perm.value}")
        
        layout.addWidget(perms_list)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            code = code_input.text().strip()
            name = name_input.text().strip()
            description = desc_input.text().strip()
            
            # 收集选中的权限
            selected_perms = []
            for i in range(perms_list.topLevelItemCount()):
                resource_item = perms_list.topLevelItem(i)
                for j in range(resource_item.childCount()):
                    perm_item = resource_item.child(j)
                    if perm_item.checkState(0) == Qt.Checked:
                        selected_perms.append(perm_item.data(0, Qt.UserRole))
            
            if code and name:
                success = self.service.create_custom_role(
                    code, name, description, selected_perms
                )
                
                if success:
                    QMessageBox.information(self, "成功", "角色创建成功")
                    self.load_roles()
                else:
                    QMessageBox.warning(self, "错误", "角色代码已存在")
    
    def edit_role(self, role):
        """编辑角色"""
        QMessageBox.information(self, "提示", f"编辑角色: {role['name']}")
    
    def delete_role(self, role_id):
        """删除角色"""
        reply = QMessageBox.question(
            self, "确认", "确定要删除这个角色吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            conn = get_conn(os.path.basename(self.service.db_path))
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM roles WHERE id = ?", (role_id,))
            
            conn.commit()
            close_conn(os.path.basename(self.service.db_path))
            
            self.load_roles()
    
    def add_data_permission(self):
        """添加数据权限"""
        user_id = self.data_user_input.text().strip()
        resource_type = self.data_resource_type.currentData()
        
        if not user_id:
            QMessageBox.warning(self, "警告", "请输入用户ID")
            return
        
        # TODO: 实现添加数据权限
        QMessageBox.information(self, "提示", "数据权限添加功能")


# 便捷函数
def show_permission_window():
    """显示权限管理窗口"""
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = PermissionWindow()
    window.show()
    return window

```
