# -*- coding: utf-8 -*-
"""
自动任务执行器
扩展定时任务，支持事件触发和异常检测
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from core.database import get_conn, close_conn


class TaskType(Enum):
    """任务类型"""
    SCHEDULED = "scheduled"     # 定时任务
    EVENT = "event"             # 事件触发
    MONITOR = "monitor"         # 监控任务
    MANUAL = "manual"           # 手动执行


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AutoTask:
    """自动任务定义"""
    id: str
    name: str
    task_type: str
    priority: int = TaskPriority.NORMAL.value
    schedule: str = ""          # cron表达式或时间间隔
    condition: str = ""         # 触发条件
    action: str = ""            # 执行动作
    parameters: Dict = field(default_factory=dict)
    is_active: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    fail_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class AutoTaskExecutor:
    """自动任务执行器"""
    
    def __init__(self):
        self.tasks: Dict[str, AutoTask] = {}
        self._handlers: Dict[str, Callable] = {}
        self._running = False
        self._thread = None
        self._interval = 60  # 检查间隔（秒）
        
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认任务处理器"""
        self._handlers = {
            "sync_data": self._handle_sync_data,
            "check_stock": self._handle_check_stock,
            "generate_report": self._handle_generate_report,
            "check_member_expiry": self._handle_check_member_expiry,
            "reconciliation": self._handle_reconciliation,
            "backup_data": self._handle_backup_data,
            "anomaly_scan": self._handle_anomaly_scan,
            "daily_report": self._handle_daily_report,
            "weekly_report": self._handle_weekly_report,
            "low_stock_alert": self._handle_low_stock_alert,
            "sales_summary": self._handle_sales_summary,
        }
    
    def register_handler(self, action: str, handler: Callable):
        """注册自定义任务处理器"""
        self._handlers[action] = handler
    
    def add_task(self, name: str, task_type: str, action: str,
                schedule: str = "", condition: str = "",
                parameters: Dict = None, priority: int = 2) -> AutoTask:
        """添加任务"""
        import uuid
        task_id = str(uuid.uuid4())[:8]
        
        task = AutoTask(
            id=task_id,
            name=name,
            task_type=task_type,
            action=action,
            schedule=schedule,
            condition=condition,
            parameters=parameters or {},
            priority=priority
        )
        
        self.tasks[task_id] = task
        return task
    
    def start(self):
        """启动执行器"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print("[AutoTaskExecutor] 自动任务执行器已启动")
    
    def stop(self):
        """停止执行器"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[AutoTaskExecutor] 自动任务执行器已停止")
    
    def _run_loop(self):
        """主循环"""
        while self._running:
            try:
                now = datetime.now()
                
                for task in self.tasks.values():
                    if not task.is_active:
                        continue
                    
                    # 检查是否应该执行
                    if self._should_execute(task, now):
                        self._execute_task(task)
                
                time.sleep(self._interval)
                
            except Exception as e:
                print(f"[AutoTaskExecutor] 错误: {e}")
                time.sleep(10)
    
    def _should_execute(self, task: AutoTask, now: datetime) -> bool:
        """检查任务是否应该执行"""
        if task.task_type == TaskType.SCHEDULED.value:
            return self._check_schedule(task, now)
        elif task.task_type == TaskType.EVENT.value:
            return self._check_event(task)
        elif task.task_type == TaskType.MONITOR.value:
            return self._check_monitor(task)
        
        return False
    
    def _check_schedule(self, task: AutoTask, now: datetime) -> bool:
        """检查定时任务"""
        if not task.schedule:
            return False
        
        # 简单的间隔解析（例如："30m"表示30分钟，"1h"表示1小时）
        try:
            if task.last_run:
                last_run = datetime.fromisoformat(task.last_run)
                
                if task.schedule.endswith('m'):
                    minutes = int(task.schedule[:-1])
                    return (now - last_run).total_seconds() >= minutes * 60
                elif task.schedule.endswith('h'):
                    hours = int(task.schedule[:-1])
                    return (now - last_run).total_seconds() >= hours * 3600
                elif task.schedule.endswith('d'):
                    days = int(task.schedule[:-1])
                    return (now - last_run).days >= days
            else:
                # 首次执行
                return True
        except:
            pass
        
        return False
    
    def _check_event(self, task: AutoTask) -> bool:
        """检查事件触发条件"""
        # 这里可以集成事件系统
        # 例如：新订单创建、库存变化等
        return False
    
    def _check_monitor(self, task: AutoTask) -> bool:
        """检查监控条件"""
        # 这里可以集成监控系统
        # 例如：CPU使用率、内存使用率等
        return False
    
    def _execute_task(self, task: AutoTask):
        """执行任务"""
        print(f"[AutoTaskExecutor] 执行任务: {task.name}")
        
        handler = self._handlers.get(task.action)
        if not handler:
            print(f"[AutoTaskExecutor] 未知动作: {task.action}")
            return
        
        try:
            result = handler(task.parameters)
            task.last_run = datetime.now().isoformat()
            task.run_count += 1
            task.next_run = self._calculate_next_run(task)
            
            print(f"[AutoTaskExecutor] 任务完成: {task.name}")
            
        except Exception as e:
            task.fail_count += 1
            print(f"[AutoTaskExecutor] 任务失败: {task.name}, 错误: {e}")
    
    def _calculate_next_run(self, task: AutoTask) -> Optional[str]:
        """计算下次执行时间"""
        if not task.schedule:
            return None
        
        now = datetime.now()
        
        try:
            if task.schedule.endswith('m'):
                minutes = int(task.schedule[:-1])
                next_run = now + timedelta(minutes=minutes)
            elif task.schedule.endswith('h'):
                hours = int(task.schedule[:-1])
                next_run = now + timedelta(hours=hours)
            elif task.schedule.endswith('d'):
                days = int(task.schedule[:-1])
                next_run = now + timedelta(days=days)
            else:
                return None
            
            return next_run.isoformat()
        except:
            return None
    
    def _handle_sync_data(self, parameters: Dict) -> Dict:
        """处理数据同步"""
        try:
            from core.sync_manager import process_queue
            result = process_queue(batch_size=100)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_check_stock(self, parameters: Dict) -> Dict:
        """处理库存检查"""
        try:
            threshold = parameters.get("threshold", 10)
            # 这里可以集成库存查询逻辑
            return {"success": True, "low_stock_items": []}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_generate_report(self, parameters: Dict) -> Dict:
        """处理报告生成"""
        try:
            report_type = parameters.get("report_type", "daily")
            # 这里可以集成报告生成逻辑
            return {"success": True, "report_type": report_type}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_check_member_expiry(self, parameters: Dict) -> Dict:
        """处理会员到期检查"""
        try:
            from core.notification_service import check_member_expiry
            alerts = check_member_expiry()
            return {"success": True, "alerts": alerts}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_reconciliation(self, parameters: Dict) -> Dict:
        """处理对账"""
        try:
            from core.reconciliation import Reconciliation
            reports = Reconciliation.run_full_reconciliation()
            return {"success": True, "reports": reports}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_backup_data(self, parameters: Dict) -> Dict:
        """处理数据备份"""
        try:
            # 这里可以集成备份逻辑
            return {"success": True, "backup_path": ""}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_anomaly_scan(self, parameters: Dict) -> Dict:
        """处理异常扫描"""
        try:
            from .anomaly_detector import get_detector
            detector = get_detector()
            alerts = detector.run_full_scan()
            return {"success": True, "alerts_count": len(alerts), "alerts": [{"title": a.title, "severity": a.severity} for a in alerts]}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_daily_report(self, parameters: Dict) -> Dict:
        """处理日报生成"""
        try:
            from .report_generator import get_generator
            gen = get_generator()
            report = gen.generate_daily_report()
            return {"success": True, "report_id": report.id, "summary": report.summary}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_weekly_report(self, parameters: Dict) -> Dict:
        """处理周报生成"""
        try:
            from .report_generator import get_generator
            gen = get_generator()
            report = gen.generate_weekly_report()
            return {"success": True, "report_id": report.id, "summary": report.summary}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_low_stock_alert(self, parameters: Dict) -> Dict:
        """处理低库存预警"""
        try:
            import os
            db_path = os.path.join(BASE_DIR, "data", "orders.db")
            conn = get_conn('order.db')
            cursor = conn.cursor()
            threshold = parameters.get("threshold", 10)
            cursor.execute("SELECT name, stock, price FROM products WHERE stock <= ? ORDER BY stock ASC", (threshold,))
            items = [{"name": row[0], "stock": row[1], "price": row[2]} for row in cursor.fetchall()]
            close_conn('order.db')
            return {"success": True, "low_stock_count": len(items), "items": items}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _handle_sales_summary(self, parameters: Dict) -> Dict:
        """处理销售汇总"""
        try:
            import os
            from datetime import datetime, timedelta
            db_path = os.path.join(BASE_DIR, "data", "orders.db")
            conn = get_conn('order.db')
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM orders
                WHERE DATE(created_at) = ? AND status != 'cancelled'
            """, (today,))
            count, total = cursor.fetchone()
            
            close_conn('order.db')
            return {"success": True, "date": today, "orders": count or 0, "revenue": round(total or 0, 2)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_tasks(self) -> List[AutoTask]:
        """列出所有任务"""
        return list(self.tasks.values())
    
    def get_task(self, task_id: str) -> Optional[AutoTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        task = self.tasks.get(task_id)
        if task:
            task.is_active = True
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        task = self.tasks.get(task_id)
        if task:
            task.is_active = False
            return True
        return False


# 预定义任务模板 V2
TASK_TEMPLATES = [
    {
        "name": "每30分钟同步数据",
        "task_type": "scheduled",
        "action": "sync_data",
        "schedule": "30m",
        "priority": 3
    },
    {
        "name": "每日凌晨2点对账",
        "task_type": "scheduled",
        "action": "reconciliation",
        "schedule": "1d",
        "priority": 2
    },
    {
        "name": "每小时检查会员到期",
        "task_type": "scheduled",
        "action": "check_member_expiry",
        "schedule": "1h",
        "priority": 2
    },
    {
        "name": "每日生成经营日报",
        "task_type": "scheduled",
        "action": "daily_report",
        "schedule": "1d",
        "priority": 1
    },
    {
        "name": "每周一生成周报",
        "task_type": "scheduled",
        "action": "weekly_report",
        "schedule": "1d",
        "priority": 1
    },
    {
        "name": "库存预警检查",
        "task_type": "monitor",
        "action": "low_stock_alert",
        "schedule": "4h",
        "parameters": {"threshold": 10},
        "priority": 3
    },
    {
        "name": "业务异常扫描",
        "task_type": "monitor",
        "action": "anomaly_scan",
        "schedule": "2h",
        "priority": 2
    },
    {
        "name": "每日销售汇总",
        "task_type": "scheduled",
        "action": "sales_summary",
        "schedule": "1d",
        "priority": 1
    }
]


def create_default_tasks(executor: AutoTaskExecutor):
    """创建默认任务"""
    for template in TASK_TEMPLATES:
        executor.add_task(
            name=template["name"],
            task_type=template["task_type"],
            action=template["action"],
            schedule=template.get("schedule", ""),
            parameters=template.get("parameters"),
            priority=template.get("priority", 2)
        )


# 全局执行器实例
_executor = None

def get_executor() -> AutoTaskExecutor:
    """获取全局执行器实例"""
    global _executor
    if _executor is None:
        _executor = AutoTaskExecutor()
        create_default_tasks(_executor)
    return _executor
