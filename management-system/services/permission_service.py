"""
Permission Service - 权限系统服务
RBAC模型 + 数据级权限 + 动态权限分配
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Set
from enum import Enum

from core.operation_log import log_action


class PermissionType(Enum):
    """权限类型"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    APPROVE = "approve"
    TRANSFER = "transfer"
    ADMIN = "admin"


class ResourceType(Enum):
    """资源类型"""
    ORDER = "order"
    PRODUCT = "product"
    CUSTOMER = "customer"
    EMPLOYEE = "employee"
    FINANCE = "finance"
    INVENTORY = "inventory"
    REPORT = "report"
    SETTING = "setting"
    USER = "user"
    ROLE = "role"
    SYSTEM = "system"


class PermissionService:
    """权限服务"""
    
    def __init__(self, db_path: str = "data/permissions.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """初始化权限数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 权限定义表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                resource_type TEXT NOT NULL,
                permission_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 角色表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                is_system INTEGER DEFAULT 0,
                parent_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES roles(id)
            )
        """)
        
        # 角色权限关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS role_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                conditions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES roles(id),
                FOREIGN KEY (permission_id) REFERENCES permissions(id),
                UNIQUE(role_id, permission_id)
            )
        """)
        
        # 用户角色关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                assigned_by TEXT,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES roles(id),
                UNIQUE(user_id, role_id)
            )
        """)
        
        # 数据权限表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT,
                permission_type TEXT NOT NULL,
                conditions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 初始化默认权限
        self._init_default_permissions(cursor)
        
        # 初始化默认角色
        self._init_default_roles(cursor)
        
        conn.commit()
        conn.close()
    
    def _init_default_permissions(self, cursor):
        """初始化默认权限"""
        permissions = [
            # 订单权限
            ("order:create", "创建订单", "创建新订单", "order", "create"),
            ("order:read", "查看订单", "查看订单详情", "order", "read"),
            ("order:update", "编辑订单", "修改订单信息", "order", "update"),
            ("order:delete", "删除订单", "删除订单记录", "order", "delete"),
            ("order:export", "导出订单", "导出订单数据", "order", "export"),
            
            # 产品权限
            ("product:create", "创建产品", "添加新产品", "product", "create"),
            ("product:read", "查看产品", "查看产品信息", "product", "read"),
            ("product:update", "编辑产品", "修改产品信息", "product", "update"),
            ("product:delete", "删除产品", "删除产品记录", "product", "delete"),
            
            # 客户权限
            ("customer:create", "创建客户", "添加新客户", "customer", "create"),
            ("customer:read", "查看客户", "查看客户信息", "customer", "read"),
            ("customer:update", "编辑客户", "修改客户信息", "customer", "update"),
            ("customer:delete", "删除客户", "删除客户记录", "customer", "delete"),
            
            # 财务权限
            ("finance:read", "查看财务", "查看财务数据", "finance", "read"),
            ("finance:update", "编辑财务", "修改财务记录", "finance", "update"),
            ("finance:approve", "审批财务", "审批财务操作", "finance", "approve"),
            
            # 报表权限
            ("report:read", "查看报表", "查看统计报表", "report", "read"),
            ("report:export", "导出报表", "导出报表数据", "report", "export"),
            
            # 系统权限
            ("setting:read", "查看设置", "查看系统设置", "setting", "read"),
            ("setting:update", "编辑设置", "修改系统设置", "setting", "update"),
            ("user:manage", "用户管理", "管理系统用户", "user", "admin"),
            ("role:manage", "角色管理", "管理系统角色", "role", "admin"),
            ("system:admin", "系统管理", "系统管理员权限", "system", "admin"),
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO permissions (code, name, description, resource_type, permission_type)
            VALUES (?, ?, ?, ?, ?)
        """, permissions)
    
    def _init_default_roles(self, cursor):
        """初始化默认角色"""
        roles = [
            ("super_admin", "超级管理员", "系统超级管理员，拥有所有权限", 1),
            ("admin", "管理员", "系统管理员，管理日常运营", 1),
            ("manager", "经理", "部门经理，查看和审批权限", 1),
            ("operator", "操作员", "日常操作员，基础操作权限", 1),
            ("viewer", "查看员", "只读权限，查看数据", 1),
            ("finance", "财务", "财务专员，财务相关权限", 1),
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO roles (code, name, description, is_system)
            VALUES (?, ?, ?, ?)
        """, roles)
        
        # 为角色分配权限
        self._assign_role_permissions(cursor)
    
    def _assign_role_permissions(self, cursor):
        """分配角色权限"""
        # 获取角色ID
        cursor.execute("SELECT id, code FROM roles")
        roles = {row[1]: row[0] for row in cursor.fetchall()}
        
        # 获取权限ID
        cursor.execute("SELECT id, code FROM permissions")
        permissions = {row[1]: row[0] for row in cursor.fetchall()}
        
        # 超级管理员 - 所有权限
        if "super_admin" in roles:
            for perm_id in permissions.values():
                cursor.execute("""
                    INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                    VALUES (?, ?)
                """, (roles["super_admin"], perm_id))
        
        # 管理员 - 除系统管理外的所有权限
        if "admin" in roles:
            admin_perms = [k for k in permissions.keys() if not k.startswith(("system:", "role:"))]
            for perm_code in admin_perms:
                cursor.execute("""
                    INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                    VALUES (?, ?)
                """, (roles["admin"], permissions[perm_code]))
        
        # 经理 - 查看、编辑、审批权限
        if "manager" in roles:
            manager_perms = [
                "order:read", "order:update", "order:approve",
                "product:read", "product:update",
                "customer:read", "customer:update",
                "finance:read", "finance:approve",
                "report:read", "report:export",
            ]
            for perm_code in manager_perms:
                if perm_code in permissions:
                    cursor.execute("""
                        INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                        VALUES (?, ?)
                    """, (roles["manager"], permissions[perm_code]))
        
        # 操作员 - 基础操作权限
        if "operator" in roles:
            operator_perms = [
                "order:create", "order:read", "order:update",
                "product:read",
                "customer:create", "customer:read", "customer:update",
                "report:read",
            ]
            for perm_code in operator_perms:
                if perm_code in permissions:
                    cursor.execute("""
                        INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                        VALUES (?, ?)
                    """, (roles["operator"], permissions[perm_code]))
        
        # 查看员 - 只读权限
        if "viewer" in roles:
            viewer_perms = [
                "order:read", "product:read", "customer:read",
                "finance:read", "report:read",
            ]
            for perm_code in viewer_perms:
                if perm_code in permissions:
                    cursor.execute("""
                        INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                        VALUES (?, ?)
                    """, (roles["viewer"], permissions[perm_code]))
        
        # 财务 - 财务相关权限
        if "finance" in roles:
            finance_perms = [
                "finance:read", "finance:update", "finance:approve",
                "order:read", "report:read", "report:export",
            ]
            for perm_code in finance_perms:
                if perm_code in permissions:
                    cursor.execute("""
                        INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                        VALUES (?, ?)
                    """, (roles["finance"], permissions[perm_code]))
    
    def check_permission(
        self,
        user_id: str,
        resource_type: str,
        permission_type: str,
        resource_id: Optional[str] = None
    ) -> bool:
        """检查用户权限"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查用户是否有该权限
        cursor.execute("""
            SELECT COUNT(*) FROM user_roles ur
            JOIN role_permissions rp ON ur.role_id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE ur.user_id = ?
            AND p.resource_type = ?
            AND p.permission_type = ?
            AND (ur.expires_at IS NULL OR ur.expires_at > datetime('now'))
        """, (user_id, resource_type, permission_type))
        
        has_permission = cursor.fetchone()[0] > 0
        
        # 如果指定了资源ID，检查数据级权限
        if has_permission and resource_id:
            cursor.execute("""
                SELECT COUNT(*) FROM data_permissions
                WHERE user_id = ?
                AND resource_type = ?
                AND (resource_id = ? OR resource_id IS NULL)
                AND permission_type = ?
            """, (user_id, resource_type, resource_id, permission_type))
            
            has_data_permission = cursor.fetchone()[0] > 0
            conn.close()
            return has_data_permission
        
        conn.close()
        return has_permission
    
    def get_user_permissions(self, user_id: str) -> List[Dict]:
        """获取用户所有权限"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT p.* FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            JOIN user_roles ur ON rp.role_id = ur.role_id
            WHERE ur.user_id = ?
            AND (ur.expires_at IS NULL OR ur.expires_at > datetime('now'))
            ORDER BY p.resource_type, p.permission_type
        """, (user_id,))
        
        permissions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return permissions
    
    def get_user_roles(self, user_id: str) -> List[Dict]:
        """获取用户角色"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT r.*, ur.assigned_at, ur.expires_at
            FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = ?
            AND (ur.expires_at IS NULL OR ur.expires_at > datetime('now'))
        """, (user_id,))
        
        roles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return roles
    
    def assign_role(self, user_id: str, role_code: str, assigned_by: str, expires_at: Optional[datetime] = None) -> bool:
        """分配角色给用户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取角色ID
        cursor.execute("SELECT id FROM roles WHERE code = ?", (role_code,))
        role = cursor.fetchone()
        
        if not role:
            conn.close()
            return False
        
        role_id = role[0]
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_roles (user_id, role_id, assigned_by, expires_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, role_id, assigned_by, expires_at.isoformat() if expires_at else None))
        
        conn.commit()
        conn.close()
        
        try:
            log_action(assigned_by, "分配角色", "permission",
                       f"用户={user_id}, 角色={role_code}")
        except Exception:
            pass
        
        return True
    
    def revoke_role(self, user_id: str, role_code: str) -> bool:
        """撤销用户角色"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取角色ID
        cursor.execute("SELECT id FROM roles WHERE code = ?", (role_code,))
        role = cursor.fetchone()
        
        if not role:
            conn.close()
            return False
        
        role_id = role[0]
        
        cursor.execute("""
            DELETE FROM user_roles WHERE user_id = ? AND role_id = ?
        """, (user_id, role_id))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if deleted:
            try:
                log_action("system", "撤销角色", "permission",
                           f"用户={user_id}, 角色={role_code}")
            except Exception:
                pass
        
        return deleted
    
    def create_custom_role(self, code: str, name: str, description: str, permission_codes: List[str]) -> bool:
        """创建自定义角色"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 创建角色
            cursor.execute("""
                INSERT INTO roles (code, name, description, is_system)
                VALUES (?, ?, ?, 0)
            """, (code, name, description))
            
            role_id = cursor.lastrowid
            
            # 分配权限
            for perm_code in permission_codes:
                cursor.execute("SELECT id FROM permissions WHERE code = ?", (perm_code,))
                perm = cursor.fetchone()
                
                if perm:
                    cursor.execute("""
                        INSERT INTO role_permissions (role_id, permission_id)
                        VALUES (?, ?)
                    """, (role_id, perm[0]))
            
            conn.commit()
            conn.close()
            try:
                log_action("system", "创建自定义角色", "permission",
                           f"角色={name}({code}), 权限数={len(permission_codes)}")
            except Exception:
                pass
            return True
            
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def add_data_permission(
        self,
        user_id: str,
        resource_type: str,
        permission_type: str,
        resource_id: Optional[str] = None,
        conditions: Optional[Dict] = None
    ) -> bool:
        """添加数据级权限"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO data_permissions (user_id, resource_type, resource_id, permission_type, conditions)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, resource_type, resource_id, permission_type, json.dumps(conditions) if conditions else None))
        
        conn.commit()
        conn.close()
        
        return True
    
    def get_permission_matrix(self) -> Dict:
        """获取权限矩阵"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取所有角色
        cursor.execute("SELECT * FROM roles ORDER BY id")
        roles = [dict(row) for row in cursor.fetchall()]
        
        # 获取所有权限
        cursor.execute("SELECT * FROM permissions ORDER BY resource_type, permission_type")
        permissions = [dict(row) for row in cursor.fetchall()]
        
        # 获取角色权限映射
        cursor.execute("""
            SELECT rp.role_id, p.code
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
        """)
        
        role_perms = {}
        for row in cursor.fetchall():
            role_id, perm_code = row
            if role_id not in role_perms:
                role_perms[role_id] = set()
            role_perms[role_id].add(perm_code)
        
        conn.close()
        
        # 构建矩阵
        matrix = {}
        for role in roles:
            matrix[role['code']] = {
                perm['code']: perm['code'] in role_perms.get(role['id'], set())
                for perm in permissions
            }
        
        return {
            "roles": roles,
            "permissions": permissions,
            "matrix": matrix
        }


# 装饰器：权限校验
def require_permission(resource_type: str, permission_type: str):
    """权限校验装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 从参数或上下文中获取用户ID
            user_id = kwargs.get('user_id') or (args[0] if args else None)
            
            if not user_id:
                raise PermissionError("未提供用户ID")
            
            service = PermissionService()
            if not service.check_permission(user_id, resource_type, permission_type):
                raise PermissionError(f"用户 {user_id} 没有 {resource_type}:{permission_type} 权限")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# 便捷函数
def check_user_permission(user_id: str, resource: str, action: str) -> bool:
    """检查用户权限"""
    service = PermissionService()
    return service.check_permission(user_id, resource, action)


def get_user_role_names(user_id: str) -> List[str]:
    """获取用户角色名称列表"""
    service = PermissionService()
    roles = service.get_user_roles(user_id)
    return [role['name'] for role in roles]
