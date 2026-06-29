"""
定时任务调度服务
管理定时任务的创建、修改、删除和执行
"""

import json
import threading
import time
import uuid
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field


@dataclass
class ScheduledTask:
    """定时任务"""
    task_id: str
    name: str
    task_type: str  # 'once', 'interval', 'cron', 'daily'
    interval: Optional[int] = None  # 秒
    cron_expression: Optional[str] = None
    daily_time: Optional[str] = None  # 'HH:MM'
    enabled: bool = True
    next_run: Optional[float] = None
    last_run: Optional[float] = None
    last_result: Optional[str] = None
    run_count: int = 0
    max_runs: Optional[int] = None
    metadata: Dict = field(default_factory=dict)


class SchedulerService:
    """定时任务调度服务"""

    def __init__(self, config_dir: str = "data"):
        self.config_dir = config_dir
        self.tasks_file = f"{config_dir}/scheduled_tasks.json"
        self._tasks: Dict[str, ScheduledTask] = {}
        self._handlers: Dict[str, Callable] = {}
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._load_tasks()

    def _load_tasks(self):
        """加载任务配置"""
        import os
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("tasks", []):
                        task = ScheduledTask(**item)
                        self._tasks[task.task_id] = task
            except Exception:
                pass

    def _save_tasks(self):
        """保存任务配置"""
        import os
        os.makedirs(self.config_dir, exist_ok=True)
        tasks_data = []
        for task in self._tasks.values():
            tasks_data.append({
                "task_id": task.task_id,
                "name": task.name,
                "task_type": task.task_type,
                "interval": task.interval,
                "cron_expression": task.cron_expression,
                "daily_time": task.daily_time,
                "enabled": task.enabled,
                "max_runs": task.max_runs,
                "metadata": task.metadata,
            })
        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump({"tasks": tasks_data}, f, ensure_ascii=False, indent=2)

    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self._handlers[task_type] = handler

    def add_task(self,
                 name: str,
                 task_type: str,
                 interval: Optional[int] = None,
                 cron_expression: Optional[str] = None,
                 daily_time: Optional[str] = None,
                 max_runs: Optional[int] = None,
                 metadata: Optional[Dict] = None) -> Dict:
        """添加任务"""
        task_id = str(uuid.uuid4())[:8]

        task = ScheduledTask(
            task_id=task_id,
            name=name,
            task_type=task_type,
            interval=interval,
            cron_expression=cron_expression,
            daily_time=daily_time,
            max_runs=max_runs,
            metadata=metadata or {},
        )

        # 计算下次运行时间
        task.next_run = self._calculate_next_run(task)
        self._tasks[task_id] = task
        self._save_tasks()

        return {"success": True, "task_id": task_id, "next_run": task.next_run}

    def remove_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            self._save_tasks()
            return True
        return False

    def update_task(self, task_id: str, updates: Dict) -> bool:
        """更新任务"""
        task = self._tasks.get(task_id)
        if not task:
            return False

        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)

        task.next_run = self._calculate_next_run(task)
        self._save_tasks()
        return True

    def enable_task(self, task_id: str, enabled: bool = True):
        """启用/禁用任务"""
        if task_id in self._tasks:
            self._tasks[task_id].enabled = enabled
            if enabled:
                self._tasks[task_id].next_run = self._calculate_next_run(self._tasks[task_id])
            self._save_tasks()

    def get_all_tasks(self) -> List[Dict]:
        """获取所有任务"""
        return [
            {
                "task_id": t.task_id,
                "name": t.name,
                "task_type": t.task_type,
                "interval": t.interval,
                "enabled": t.enabled,
                "next_run": t.next_run,
                "last_run": t.last_run,
                "last_result": t.last_result,
                "run_count": t.run_count,
            }
            for t in self._tasks.values()
        ]

    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务详情"""
        task = self._tasks.get(task_id)
        if not task:
            return None

        return {
            "task_id": task.task_id,
            "name": task.name,
            "task_type": task.task_type,
            "interval": task.interval,
            "cron_expression": task.cron_expression,
            "daily_time": task.daily_time,
            "enabled": task.enabled,
            "next_run": task.next_run,
            "last_run": task.last_run,
            "last_result": task.last_result,
            "run_count": task.run_count,
            "max_runs": task.max_runs,
            "metadata": task.metadata,
        }

    def run_task_now(self, task_id: str) -> Dict:
        """立即运行任务"""
        task = self._tasks.get(task_id)
        if not task:
            return {"success": False, "message": "任务不存在"}

        return self._execute_task(task)

    def start(self):
        """启动调度器"""
        if self._running:
            return

        self._running = True
        self._scheduler_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._scheduler_thread.start()

    def stop(self):
        """停止调度器"""
        self._running = False

    def _run_loop(self):
        """调度循环"""
        while self._running:
            now = time.time()

            for task in list(self._tasks.values()):
                if not task.enabled:
                    continue

                if task.next_run and now >= task.next_run:
                    self._execute_task(task)
                    task.next_run = self._calculate_next_run(task)

                # 检查最大运行次数
                if task.max_runs and task.run_count >= task.max_runs:
                    task.enabled = False

            self._save_tasks()
            time.sleep(1)

    def _execute_task(self, task: ScheduledTask) -> Dict:
        """执行任务"""
        handler = self._handlers.get(task.task_type)
        if not handler:
            task.last_result = f"未找到处理器: {task.task_type}"
            return {"success": False, "message": task.last_result}

        try:
            result = handler(task.metadata)
            task.last_run = time.time()
            task.run_count += 1
            task.last_result = "成功"
            return {"success": True, "result": result}
        except Exception as e:
            task.last_result = str(e)
            return {"success": False, "message": str(e)}

    def _calculate_next_run(self, task: ScheduledTask) -> Optional[float]:
        """计算下次执行时间"""
        now = time.time()

        if task.task_type == "once":
            return None

        elif task.task_type == "interval":
            return now + (task.interval or 3600)

        elif task.task_type == "daily":
            if task.daily_time:
                hour, minute = map(int, task.daily_time.split(":"))
                target = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                if target <= datetime.now():
                    target += timedelta(days=1)
                return target.timestamp()

        return now + 3600  # 默认每小时

    def get_next_runs(self, count: int = 5) -> List[Dict]:
        """获取即将运行的任务"""
        upcoming = []
        for task in self._tasks.values():
            if task.enabled and task.next_run:
                upcoming.append({
                    "task_id": task.task_id,
                    "name": task.name,
                    "next_run": task.next_run,
                    "time_remaining": max(0, task.next_run - time.time()),
                })

        upcoming.sort(key=lambda x: x["next_run"])
        return upcoming[:count]

