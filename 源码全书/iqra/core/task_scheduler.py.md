# `iqra/core/task_scheduler.py`

> 路径：`iqra/core/task_scheduler.py` | 行数：268


---


```python
"""
任务调度器 — 定时任务与自动化

提供:
- 定时任务创建/管理
- 周期性执行
- 任务触发条件
- 执行日志
"""

import os
import json
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass


@dataclass
class ScheduledTask:
    """定时任务"""
    task_id: str
    name: str
    schedule: str  # cron 表达式或 '30m', '2h', 'daily' 等
    handler: str  # 处理函数名
    params: Dict[str, Any]
    enabled: bool = True
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    last_result: Optional[Dict] = None


class TaskScheduler:
    """任务调度器"""
    
    _DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "scheduler.db")

    def __init__(self, db_path: str = None):
        self.db_path = db_path or self._DEFAULT_DB
        self.tasks: Dict[str, ScheduledTask] = {}
        self._handlers: Dict[str, Callable] = {}
        self._init_db()
        self._load_tasks()
    
    def _init_db(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                name TEXT,
                schedule TEXT,
                handler TEXT,
                params TEXT,
                enabled INTEGER DEFAULT 1,
                last_run TEXT,
                next_run TEXT,
                run_count INTEGER DEFAULT 0,
                last_result TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def _load_tasks(self):
        """从数据库加载任务"""
        if not os.path.exists(self.db_path):
            return
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM tasks").fetchall()
        
        for row in rows:
            task = ScheduledTask(
                task_id=row["task_id"],
                name=row["name"],
                schedule=row["schedule"],
                handler=row["handler"],
                params=json.loads(row["params"] or "{}"),
                enabled=bool(row["enabled"]),
                last_run=row["last_run"],
                next_run=row["next_run"],
                run_count=row["run_count"],
                last_result=json.loads(row["last_result"] or "null")
            )
            self.tasks[task.task_id] = task
        
        conn.close()
    
    def _save_task(self, task: ScheduledTask):
        """保存任务到数据库"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO tasks 
            (task_id, name, schedule, handler, params, enabled, last_run, next_run, run_count, last_result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.task_id, task.name, task.schedule, task.handler,
            json.dumps(task.params), int(task.enabled),
            task.last_run, task.next_run, task.run_count,
            json.dumps(task.last_result) if task.last_result else None
        ))
        conn.commit()
        conn.close()
    
    def add_task(self, name: str, schedule: str, handler_name: str, 
                 params: Dict = None, task_id: str = None) -> ScheduledTask:
        """添加定时任务"""
        import uuid
        task_id = task_id or f"task_{uuid.uuid4().hex[:8]}"
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            schedule=schedule,
            handler=handler_name,
            params=params or {},
            enabled=True
        )
        
        self.tasks[task_id] = task
        self._save_task(task)
        return task
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            conn.commit()
            conn.close()
            return True
        return False
    
    def pause_task(self, task_id: str):
        """暂停任务"""
        task = self.tasks.get(task_id)
        if task:
            task.enabled = False
            self._save_task(task)
    
    def resume_task(self, task_id: str):
        """恢复任务"""
        task = self.tasks.get(task_id)
        if task:
            task.enabled = True
            self._save_task(task)
    
    def register_handler(self, name: str, func: Callable):
        """注册处理函数"""
        self._handlers[name] = func
    
    def get_due_tasks(self) -> List[ScheduledTask]:
        """获取需要执行的任务"""
        due = []
        now = datetime.now()
        
        for task in self.tasks.values():
            if not task.enabled:
                continue
            
            next_run = self._parse_next_run(task.schedule, task.last_run)
            if next_run and next_run <= now:
                due.append(task)
        
        return due
    
    def execute_task(self, task: ScheduledTask) -> Dict:
        """执行任务"""
        handler = self._handlers.get(task.handler)
        if not handler:
            return {"error": f"未找到处理函数: {task.handler}"}
        
        try:
            result = handler(**task.params)
            
            # 更新任务状态
            task.last_run = datetime.now().isoformat()
            task.next_run = self._parse_next_run(task.schedule, task.last_run).isoformat() if task.schedule else None
            task.run_count += 1
            task.last_result = {"success": True, "result": str(result)[:1000]}
            
            self._save_task(task)
            return {"success": True, "result": result}
            
        except Exception as e:
            task.last_result = {"success": False, "error": str(e)}
            self._save_task(task)
            return {"success": False, "error": str(e)}
    
    def _parse_next_run(self, schedule: str, last_run: Optional[str] = None) -> Optional[datetime]:
        """解析下次执行时间"""
        now = datetime.now()
        
        if schedule.startswith("every ") or "h" in schedule or "m" in schedule:
            # 解析 '30m', '2h', 'every 4h' 等
            import re
            match = re.search(r'(\d+)\s*([mhd])', schedule)
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                
                if unit == 'm':
                    delta = timedelta(minutes=value)
                elif unit == 'h':
                    delta = timedelta(hours=value)
                elif unit == 'd':
                    delta = timedelta(days=value)
                else:
                    return None
                
                if last_run:
                    return datetime.fromisoformat(last_run) + delta
                else:
                    return now + delta
        
        elif schedule == "daily":
            return now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        elif schedule == "weekly":
            return now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=7)
        
        return None
    
    def list_tasks(self) -> List[Dict]:
        """列出所有任务"""
        return [
            {
                "task_id": t.task_id,
                "name": t.name,
                "schedule": t.schedule,
                "handler": t.handler,
                "enabled": t.enabled,
                "last_run": t.last_run,
                "next_run": t.next_run,
                "run_count": t.run_count,
                "last_result": t.last_result
            }
            for t in self.tasks.values()
        ]
    
    def get_stats(self) -> Dict:
        """获取调度器统计"""
        return {
            "total_tasks": len(self.tasks),
            "enabled_tasks": sum(1 for t in self.tasks.values() if t.enabled),
            "disabled_tasks": sum(1 for t in self.tasks.values() if not t.enabled),
            "total_runs": sum(t.run_count for t in self.tasks.values())
        }


# ═══════════════════════════════════════════
# 全局实例
# ═══════════════════════════════════════════

_scheduler = None

def get_scheduler(db_path: str = None) -> TaskScheduler:
    """获取调度器单例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler(db_path)
    return _scheduler

```
