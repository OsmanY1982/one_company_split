# `core/workflow_engine.py`

> 路径：`core/workflow_engine.py` | 行数：403


---


```python
# -*- coding: utf-8 -*-
"""
工作流引擎
支持自定义工作流定义、节点执行、条件分支
"""

import json
import os
import threading
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from core.database import get_conn


class NodeType(Enum):
    START = "start"
    END = "end"
    TASK = "task"
    APPROVAL = "approval"
    CONDITION = "condition"
    PARALLEL = "parallel"
    DELAY = "delay"
    NOTIFICATION = "notification"


class WorkflowStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class NodeStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class WorkflowNode:
    """工作流节点"""
    node_id: str
    name: str
    node_type: NodeType = NodeType.TASK
    config: Dict[str, Any] = field(default_factory=dict)
    next_nodes: List[str] = field(default_factory=list)  # 条件节点可有两个
    condition: Optional[str] = None  # Python 表达式
    
    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "node_type": self.node_type.value,
            "config": self.config,
            "next_nodes": self.next_nodes,
            "condition": self.condition,
        }


@dataclass
class WorkflowInstance:
    """工作流实例（运行中的工作流）"""
    instance_id: str
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.ACTIVE
    current_node_id: str = ""
    context: Dict[str, Any] = field(default_factory=dict)  # 全局上下文
    node_results: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    
    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()
        if not self.current_node_id:
            self.current_node_id = "start"


class WorkflowDefinition:
    """工作流定义"""
    
    def __init__(self, workflow_id: str, name: str, description: str = ""):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.nodes: Dict[str, WorkflowNode] = {}
        self._add_builtin_nodes()
    
    def _add_builtin_nodes(self):
        """添加开始和结束节点"""
        self.add_node(WorkflowNode(node_id="start", name="开始", node_type=NodeType.START))
        self.add_node(WorkflowNode(node_id="end", name="结束", node_type=NodeType.END))
    
    def add_node(self, node: WorkflowNode):
        """添加节点"""
        self.nodes[node.node_id] = node
    
    def connect(self, from_node_id: str, to_node_id: str):
        """连接两个节点"""
        if from_node_id in self.nodes and to_node_id in self.nodes:
            node = self.nodes[from_node_id]
            if to_node_id not in node.next_nodes:
                node.next_nodes.append(to_node_id)
    
    def to_dict(self) -> Dict:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "nodes": [n.to_dict() for n in self.nodes.values()],
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "WorkflowDefinition":
        wf = cls(
            workflow_id=data["workflow_id"],
            name=data["name"],
            description=data.get("description", ""),
        )
        for node_data in data.get("nodes", []):
            node = WorkflowNode(
                node_id=node_data["node_id"],
                name=node_data["name"],
                node_type=NodeType(node_data.get("node_type", "task")),
                config=node_data.get("config", {}),
                next_nodes=node_data.get("next_nodes", []),
                condition=node_data.get("condition"),
            )
            wf.add_node(node)
        return wf


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.definitions: Dict[str, WorkflowDefinition] = {}
        self.instances: Dict[str, WorkflowInstance] = {}
        self.handlers: Dict[str, Callable] = {}  # 节点处理器
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认处理器"""
        self.handlers[NodeType.START.value] = self._handle_start
        self.handlers[NodeType.END.value] = self._handle_end
        self.handlers[NodeType.TASK.value] = self._handle_task
        self.handlers[NodeType.APPROVAL.value] = self._handle_approval
        self.handlers[NodeType.CONDITION.value] = self._handle_condition
        self.handlers[NodeType.PARALLEL.value] = self._handle_parallel
        self.handlers[NodeType.DELAY.value] = self._handle_delay
        self.handlers[NodeType.NOTIFICATION.value] = self._handle_notification
    
    def register_definition(self, definition: WorkflowDefinition):
        """注册工作流定义"""
        self.definitions[definition.workflow_id] = definition
    
    def start_workflow(self, workflow_id: str, context: Dict = None) -> Optional[str]:
        """启动工作流"""
        if workflow_id not in self.definitions:
            print(f"工作流不存在: {workflow_id}")
            return None
        
        import uuid
        instance_id = f"wf_{workflow_id}_{uuid.uuid4().hex[:8]}"
        instance = WorkflowInstance(
            instance_id=instance_id,
            workflow_id=workflow_id,
            context=context or {},
        )
        self.instances[instance_id] = instance
        
        # 开始执行
        self._execute_node(instance_id, "start")
        return instance_id
    
    def _execute_node(self, instance_id: str, node_id: str):
        """执行节点"""
        instance = self.instances.get(instance_id)
        if not instance:
            return
        
        definition = self.definitions.get(instance.workflow_id)
        if not definition:
            return
        
        node = definition.nodes.get(node_id)
        if not node:
            return
        
        # 记录执行历史
        instance.current_node_id = node_id
        instance.history.append({
            "node_id": node_id,
            "node_name": node.name,
            "node_type": node.node_type.value,
            "timestamp": datetime.now().isoformat(),
        })
        
        # 执行节点处理器
        handler = self.handlers.get(node.node_type.value)
        if handler:
            next_nodes = handler(instance, node, definition)
        else:
            next_nodes = node.next_nodes
        
        # 进入下一节点
        if next_nodes:
            for next_id in next_nodes:
                if next_id and next_id in definition.nodes:
                    self._execute_node(instance_id, next_id)
    
    def _handle_start(self, instance, node, definition):
        """处理开始节点"""
        print(f"[Workflow] 开始: {definition.name}")
        return node.next_nodes
    
    def _handle_end(self, instance, node, definition):
        """处理结束节点"""
        instance.status = WorkflowStatus.COMPLETED
        instance.completed_at = datetime.now().isoformat()
        print(f"[Workflow] 完成: {definition.name}")
        return []
    
    def _handle_task(self, instance, node, definition):
        """处理任务节点"""
        task_name = node.config.get("task_name", node.name)
        print(f"[Workflow] 执行任务: {task_name}")
        
        table = node.config.get("table")
        if table:
            try:
                conn = get_conn(f"{table}.db")
                action = node.config.get("action", "query")
                if action == "query":
                    sql = node.config.get("sql", f"SELECT * FROM {table} LIMIT 10")
                    cursor = conn.execute(sql)
                    rows = cursor.fetchall()
                    instance.node_results[node.node_id] = {
                        "table": table, "rows": rows, "count": len(rows)
                    }
                elif action == "insert":
                    cols = node.config.get("columns", [])
                    vals = node.config.get("values", [])
                    if cols and vals:
                        placeholders = ", ".join("?" * len(vals))
                        conn.execute(
                            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})",
                            vals
                        )
                        conn.commit()
            except Exception as e:
                print(f"[Workflow] 任务执行失败: {e}")
                instance.node_results[node.node_id] = {"error": str(e)}
        
        return node.next_nodes
    
    def _handle_approval(self, instance, node, definition):
        """处理审批节点"""
        approver = node.config.get("approver", "管理员")
        print(f"[Workflow] 待审批: {node.name} (审批人: {approver})")
        
        auto_approve = node.config.get("auto_approve", False)
        if auto_approve:
            print(f"[Workflow] 自动审批通过")
            return node.next_nodes
        else:
            # 等待人工审批
            instance.node_results[node.node_id] = {"status": "pending_approval"}
            return []
    
    def _handle_condition(self, instance, node, definition):
        """处理条件节点"""
        condition_expr = node.condition or node.config.get("condition", "")
        if not condition_expr:
            return node.next_nodes[:1] if node.next_nodes else []
        
        try:
            ctx = instance.context.copy()
            ctx.update(instance.node_results)
            result = eval(condition_expr, {"__builtins__": {}}, ctx)
        except Exception as e:
            print(f"[Workflow] 条件判断失败: {e}")
            return node.next_nodes[:1] if node.next_nodes else []
        
        if result and len(node.next_nodes) > 0:
            return [node.next_nodes[0]]
        elif not result and len(node.next_nodes) > 1:
            return [node.next_nodes[1]]
        return []
    
    def _handle_parallel(self, instance, node, definition):
        """处理并行节点"""
        print(f"[Workflow] 并行执行: {node.name}")
        threads = []
        for next_id in node.next_nodes:
            if next_id in definition.nodes:
                t = threading.Thread(target=self._execute_node, args=(instance.instance_id, next_id))
                t.start()
                threads.append(t)
        for t in threads:
            t.join()
        return []
    
    def _handle_delay(self, instance, node, definition):
        """处理延迟节点"""
        delay_seconds = node.config.get("seconds", 5)
        print(f"[Workflow] 等待 {delay_seconds} 秒...")
        import time
        time.sleep(delay_seconds)
        return node.next_nodes
    
    def _handle_notification(self, instance, node, definition):
        """处理通知节点"""
        message = node.config.get("message", "工作流通知")
        method = node.config.get("method", "log")
        print(f"[Workflow] 通知 ({method}): {message}")
        return node.next_nodes
    
    def get_instance(self, instance_id: str) -> Optional[Dict]:
        """获取工作流实例状态"""
        instance = self.instances.get(instance_id)
        if not instance:
            return None
        
        return {
            "instance_id": instance.instance_id,
            "workflow_id": instance.workflow_id,
            "status": instance.status.value,
            "current_node": instance.current_node_id,
            "context": instance.context,
            "history": instance.history,
            "started_at": instance.started_at,
            "completed_at": instance.completed_at,
        }


# 预设工作流模板
def get_presets() -> List[WorkflowDefinition]:
    """获取预设工作流模板"""
    presets = []
    
    # 1. 订单处理流程
    order_wf = WorkflowDefinition("order_processing", "订单处理", "从下单到完成的标准流程")
    confirm = WorkflowNode(node_id="confirm_order", name="确认订单", node_type=NodeType.TASK)
    check_stock = WorkflowNode(node_id="check_stock", name="检查库存", node_type=NodeType.CONDITION,
                              condition="context.get('stock', 0) > context.get('quantity', 0)")
    notify_low = WorkflowNode(node_id="notify_low_stock", name="库存不足通知", node_type=NodeType.NOTIFICATION,
                             config={"message": "库存不足，无法完成订单", "method": "alert"})
    ship = WorkflowNode(node_id="ship_order", name="发货", node_type=NodeType.TASK)
    
    order_wf.nodes = {n.node_id: n for n in [order_wf.nodes["start"], order_wf.nodes["end"],
                                              confirm, check_stock, notify_low, ship]}
    order_wf.connect("start", "confirm_order")
    order_wf.connect("confirm_order", "check_stock")
    order_wf.connect("check_stock", "ship_order")
    order_wf.connect("check_stock", "notify_low_stock")
    order_wf.connect("ship_order", "end")
    order_wf.connect("notify_low_stock", "end")
    presets.append(order_wf)
    
    # 2. 审批流程
    approval_wf = WorkflowDefinition("approval_flow", "审批流程", "标准多级审批")
    submit = WorkflowNode(node_id="submit", name="提交申请", node_type=NodeType.TASK)
    mgr_approve = WorkflowNode(node_id="mgr_approve", name="经理审批", node_type=NodeType.APPROVAL,
                              config={"approver": "部门经理"})
    ceo_approve = WorkflowNode(node_id="ceo_approve", name="总经理审批", node_type=NodeType.APPROVAL,
                              config={"approver": "总经理"})
    
    approval_wf.nodes = {n.node_id: n for n in [approval_wf.nodes["start"], approval_wf.nodes["end"],
                                                submit, mgr_approve, ceo_approve]}
    approval_wf.connect("start", "submit")
    approval_wf.connect("submit", "mgr_approve")
    approval_wf.connect("mgr_approve", "ceo_approve")
    approval_wf.connect("ceo_approve", "end")
    presets.append(approval_wf)
    
    return presets


if __name__ == "__main__":
    engine = WorkflowEngine()
    
    # 注册预设工作流
    for preset in get_presets():
        engine.register_definition(preset)
    
    print("预设工作流:")
    for wf_id, wf_def in engine.definitions.items():
        print(f"  {wf_def.name} ({wf_id}): {len(wf_def.nodes)} 个节点")
    
    # 测试订单处理
    print("\n=== 测试订单处理 ===")
    instance_id = engine.start_workflow("order_processing", {"stock": 10, "quantity": 5})
    if instance_id:
        result = engine.get_instance(instance_id)
        print(f"状态: {result['status']}")
        print(f"历史: {len(result['history'])} 个步骤")

```
