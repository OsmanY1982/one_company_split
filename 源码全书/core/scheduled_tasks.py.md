# `core/scheduled_tasks.py`

> 路径：`core/scheduled_tasks.py` | 行数：115


---


```python
# -*- coding: utf-8 -*-
"""
定时任务调度器
- 每 30 分钟处理同步队列
- 每天凌晨 2 点执行全量对账
"""
import threading
import time
from datetime import datetime, timedelta


class ScheduledTasks:
    """定时任务管理"""
    
    def __init__(self):
        self._running = False
        self._thread = None
        self._interval = 1800  # 30 分钟
    
    def start(self):
        """启动定时任务"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print("[ScheduledTasks] 定时任务已启动")
    
    def stop(self):
        """停止定时任务"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[ScheduledTasks] 定时任务已停止")
    
    def _run(self):
        """主循环"""
        while self._running:
            try:
                now = datetime.now()
                
                # 每 30 分钟处理同步队列
                self._process_sync_queue()
                
                # 每天凌晨 2 点执行对账
                if now.hour == 2 and now.minute < 30:
                    self._run_reconciliation()
                
                # 等待到下一个周期
                time.sleep(self._interval)
                
            except Exception as e:
                print(f"[ScheduledTasks] 错误: {e}")
                time.sleep(60)  # 出错后 1 分钟重试
    
    def _process_sync_queue(self):
        """处理同步队列"""
        try:
            from core.sync_manager import process_queue
            result = process_queue(batch_size=100)
            if result["success"] > 0 or result["failed"] > 0:
                print(f"[ScheduledTasks] 队列处理: 成功 {result['success']}, 失败 {result['failed']}")
        except Exception as e:
            print(f"[ScheduledTasks] 队列处理失败: {e}")
    
    def _run_reconciliation(self):
        """执行对账"""
        try:
            from core.reconciliation import Reconciliation
            print("[ScheduledTasks] 开始全量对账...")
            reports = Reconciliation.run_full_reconciliation()
            
            # 生成对账报告
            total_issues = sum(
                len(r.get("missing_in_cloud", [])) + 
                len(r.get("mismatched", []))
                for r in reports
            )
            
            if total_issues > 0:
                print(f"[ScheduledTasks] 发现 {total_issues} 条数据不一致")
                # TODO: 发送通知
            else:
                print("[ScheduledTasks] 数据一致性检查通过")
                
        except Exception as e:
            print(f"[ScheduledTasks] 对账失败: {e}")


# 全局实例
_scheduler = None

def start_scheduler():
    """启动调度器"""
    global _scheduler
    if _scheduler is None:
        _scheduler = ScheduledTasks()
        _scheduler.start()
    return _scheduler

def stop_scheduler():
    """停止调度器"""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
        _scheduler = None


if __name__ == "__main__":
    print("定时任务测试")
    scheduler = start_scheduler()
    try:
        time.sleep(5)
    finally:
        stop_scheduler()

```
