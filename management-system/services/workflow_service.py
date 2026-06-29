"""
Workflow Service - 工作流引擎
支持审批流程、状态流转、条件分支
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable
from enum import Enum


class WorkflowStatus(Enum):
    """工作流状态"""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVING = "approving"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class NodeType(Enum):
    """节点类型"""
    START = "start"
    END = "end"
    TASK = "task"
    APPROVAL = "approval"
    CONDITION = "condition"
    PARALLEL = "parallel"
    NOTIFICATION = "notification"


class WorkflowService:
    """工作流服务"""
    
    def __init__(self, db_path: str = "data/workflows.db"):
        self.db_path = db_path
        self.init_db()
        self._handlers: Dict[str, Callable] = {}
    
    def init_db(self):
        """初始化工作流数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 流程定义表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                version INTEGER DEFAULT 1,
                definition TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 流程实例表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                definition_id INTEGER NOT NULL,
                business_key TEXT,
                status TEXT DEFAULT 'draft',
                current_node TEXT,
                variables TEXT,
                started_by TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (definition_id) REFERENCES workflow_definitions(id)
            )
        """)
        
        # 任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_id INTEGER NOT NULL,
                node_id TEXT NOT NULL,
                node_name TEXT,
                assignee TEXT,
                candidate_groups TEXT,
                status TEXT DEFAULT 'pending',
                action TEXT,
                comment TEXT,
                due_date TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (instance_id) REFERENCES workflow_instances(id)
            )
        """)
        
        # 历史记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_id INTEGER NOT NULL,
                task_id INTEGER,
                node_id TEXT,
                node_name TEXT,
                action TEXT,
                operator TEXT,
                comment TEXT,
                variables TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (instance_id) REFERENCES workflow_instances(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def register_handler(self, action: str, handler: Callable):
        """注册动作处理器"""
        self._handlers[action] = handler
    
    def create_definition(self, code: str, name: str, definition: Dict, description: str = "") -> int:
        """创建流程定义"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO workflow_definitions (code, name, description, definition)
            VALUES (?, ?, ?, ?)
        """, (code, name, description, json.dumps(definition)))
        
        definition_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return definition_id
    
    def get_definition(self, code: str) -> Optional[Dict]:
        """获取流程定义"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM workflow_definitions 
            WHERE code = ? AND is_active = 1
            ORDER BY version DESC
            LIMIT 1
        """, (code,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            definition = dict(row)
            definition['definition'] = json.loads(definition['definition'])
            return definition
        
        return None
    
    def start_instance(self, definition_code: str, business_key: str = None, 
                      variables: Dict = None, started_by: str = None) -> int:
        """启动流程实例"""
        definition = self.get_definition(definition_code)
        if not definition:
            raise ValueError(f"流程定义不存在: {definition_code}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建实例
        cursor.execute("""
            INSERT INTO workflow_instances 
            (definition_id, business_key, status, variables, started_by, started_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            definition['id'],
            business_key,
            WorkflowStatus.PENDING.value,
            json.dumps(variables or {}),
            started_by,
            datetime.now().isoformat()
        ))
        
        instance_id = cursor.lastrowid
        
        # 获取开始节点
        flow_def = definition['definition']
        start_node = self._get_start_node(flow_def)
        
        if start_node:
            # 创建第一个任务
            self._create_task(cursor, instance_id, start_node, variables)
            
            # 更新当前节点
            cursor.execute("""
                UPDATE workflow_instances 
                SET current_node = ?, status = ?
                WHERE id = ?
            """, (start_node['id'], WorkflowStatus.APPROVING.value, instance_id))
        
        conn.commit()
        conn.close()
        
        return instance_id
    
    def complete_task(self, task_id: int, action: str, operator: str, 
                     comment: str = None, variables: Dict = None) -> bool:
        """完成任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取任务
        cursor.execute("""
            SELECT * FROM workflow_tasks WHERE id = ?
        """, (task_id,))
        
        task = cursor.fetchone()
        if not task:
            conn.close()
            return False
        
        task = dict(task)
        instance_id = task['instance_id']
        
        # 更新任务
        cursor.execute("""
            UPDATE workflow_tasks 
            SET status = ?, action = ?, comment = ?, completed_at = ?
            WHERE id = ?
        """, ('completed', action, comment, datetime.now().isoformat(), task_id))
        
        # 记录历史
        cursor.execute("""
            INSERT INTO workflow_history 
            (instance_id, task_id, node_id, node_name, action, operator, comment, variables)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            instance_id, task_id, task['node_id'], task['node_name'],
            action, operator, comment, json.dumps(variables or {})
        ))
        
        # 获取流程定义
        cursor.execute("""
            SELECT wd.definition FROM workflow_instances wi
            JOIN workflow_definitions wd ON wi.definition_id = wd.id
            WHERE wi.id = ?
        """, (instance_id,))
        
        definition = json.loads(cursor.fetchone()[0])
        
        # 查找下一个节点
        current_node = self._get_node_by_id(definition, task['node_id'])
        next_node = self._get_next_node(definition, current_node, action, variables)
        
        if next_node:
            if next_node['type'] == NodeType.END.value:
                # 结束流程
                cursor.execute("""
                    UPDATE workflow_instances 
                    SET status = ?, current_node = ?, completed_at = ?
                    WHERE id = ?
                """, (WorkflowStatus.COMPLETED.value, next_node['id'], 
                      datetime.now().isoformat(), instance_id))
            else:
                # 创建下一个任务
                self._create_task(cursor, instance_id, next_node, variables)
                
                cursor.execute("""
                    UPDATE workflow_instances 
                    SET current_node = ?, status = ?
                    WHERE id = ?
                """, (next_node['id'], WorkflowStatus.APPROVING.value, instance_id))
        
        conn.commit()
        conn.close()
        
        # 执行处理器
        handler = self._handlers.get(action)
        if handler:
            handler(instance_id, task_id, variables)
        
        return True
    
    def get_tasks(self, user_id: str = None, status: str = 'pending') -> List[Dict]:
        """获取任务列表"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute("""
                SELECT t.*, i.business_key, wd.name as workflow_name
                FROM workflow_tasks t
                JOIN workflow_instances i ON t.instance_id = i.id
                JOIN workflow_definitions wd ON i.definition_id = wd.id
                WHERE t.status = ? AND (t.assignee = ? OR t.assignee IS NULL)
                ORDER BY t.created_at DESC
            """, (status, user_id))
        else:
            cursor.execute("""
                SELECT t.*, i.business_key, wd.name as workflow_name
                FROM workflow_tasks t
                JOIN workflow_instances i ON t.instance_id = i.id
                JOIN workflow_definitions wd ON i.definition_id = wd.id
                WHERE t.status = ?
                ORDER BY t.created_at DESC
            """, (status,))
        
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return tasks
    
    def get_instance_history(self, instance_id: int) -> List[Dict]:
        """获取流程历史"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM workflow_history 
            WHERE instance_id = ?
            ORDER BY created_at
        """, (instance_id,))
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return history
    
    def _get_start_node(self, definition: Dict) -> Optional[Dict]:
        """获取开始节点"""
        nodes = definition.get('nodes', [])
        for node in nodes:
            if node['type'] == NodeType.START.value:
                # 返回开始节点的下一个节点
                return self._get_node_by_id(definition, node.get('next'))
        return None
    
    def _get_node_by_id(self, definition: Dict, node_id: str) -> Optional[Dict]:
        """根据ID获取节点"""
        nodes = definition.get('nodes', [])
        for node in nodes:
            if node['id'] == node_id:
                return node
        return None
    
    def _get_next_node(self, definition: Dict, current_node: Dict, 
                      action: str, variables: Dict) -> Optional[Dict]:
        """获取下一个节点"""
        if current_node.get('type') == NodeType.CONDITION.value:
            # 条件节点
            conditions = current_node.get('conditions', [])
            for condition in conditions:
                if self._evaluate_condition(condition, variables):
                    return self._get_node_by_id(definition, condition.get('next'))
            # 默认分支
            return self._get_node_by_id(definition, current_node.get('default_next'))
        else:
            # 普通节点
            next_id = current_node.get('next')
            if action == 'reject':
                next_id = current_node.get('reject_next', next_id)
            return self._get_node_by_id(definition, next_id)
    
    def _evaluate_condition(self, condition: Dict, variables: Dict) -> bool:
        """评估条件"""
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')
        
        actual_value = variables.get(field)
        
        if operator == 'eq':
            return actual_value == value
        elif operator == 'ne':
            return actual_value != value
        elif operator == 'gt':
            return actual_value is not None and actual_value > value
        elif operator == 'gte':
            return actual_value is not None and actual_value >= value
        elif operator == 'lt':
            return actual_value is not None and actual_value < value
        elif operator == 'lte':
            return actual_value is not None and actual_value <= value
        elif operator == 'in':
            return actual_value in value if isinstance(value, list) else False
        
        return False
    
    def _create_task(self, cursor, instance_id: int, node: Dict, variables: Dict):
        """创建任务"""
        assignee = node.get('assignee')
        
        # 支持表达式
        if assignee and assignee.startswith('${') and assignee.endswith('}'):
            expr = assignee[2:-1]
            assignee = variables.get(expr)
        
        cursor.execute("""
            INSERT INTO workflow_tasks 
            (instance_id, node_id, node_name, assignee, candidate_groups, due_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            instance_id,
            node['id'],
            node.get('name', node['id']),
            assignee,
            json.dumps(node.get('candidate_groups', [])),
            node.get('due_date')
        ))


# 便捷函数
def create_approval_workflow(code: str, name: str, steps: List[Dict]) -> int:
    """创建审批流程"""
    service = WorkflowService()
    
    nodes = [
        {"id": "start", "type": "start", "next": steps[0]['id'] if steps else "end"}
    ]
    
    for i, step in enumerate(steps):
        node = {
            "id": step['id'],
            "type": "approval",
            "name": step.get('name', step['id']),
            "assignee": step.get('assignee'),
            "candidate_groups": step.get('candidate_groups', []),
        }
        
        if i < len(steps) - 1:
            node["next"] = steps[i + 1]['id']
        else:
            node["next"] = "end"
        
        node["reject_next"] = step.get('reject_next', 'end')
        nodes.append(node)
    
    nodes.append({"id": "end", "type": "end"})
    
    definition = {
        "nodes": nodes,
        "variables": {}
    }
    
    return service.create_definition(code, name, definition)


def start_approval_process(definition_code: str, business_key: str, 
                          data: Dict, starter: str) -> int:
    """启动审批流程"""
    service = WorkflowService()
    return service.start_instance(
        definition_code=definition_code,
        business_key=business_key,
        variables=data,
        started_by=starter
    )
