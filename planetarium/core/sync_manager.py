#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步管理器
管理待同步队列、重试机制、批量处理
"""

import sqlite3
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SYNC_DB = os.path.join(DATA_DIR, "sync_queue.db")


class SyncOperation(Enum):
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


class SyncStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SyncTask:
    """同步任务"""
    id: Optional[int] = None
    table_name: str = ""
    record_id: str = ""
    operation: str = SyncOperation.UPDATE.value
    data: Dict = field(default_factory=dict)
    status: str = SyncStatus.PENDING.value
    retry_count: int = 0
    max_retries: int = 5
    created_at: str = ""
    updated_at: str = ""
    error_message: str = ""


class SyncQueueManager:
    """同步队列管理器"""
    
    def __init__(self):
        self._ensure_db()
    
    def _ensure_db(self):
        """确保数据库和表存在"""
        os.makedirs(DATA_DIR, exist_ok=True)
        conn = sqlite3.connect(SYNC_DB)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                record_id TEXT NOT NULL,
                operation TEXT NOT NULL DEFAULT 'update',
                data TEXT,
                status TEXT DEFAULT 'pending',
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 5,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                error_message TEXT DEFAULT ''
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sync_status ON sync_queue (status, table_name)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sync_created ON sync_queue (created_at)
        """)
        conn.commit()
        conn.close()
    
    def enqueue(self, table_name: str, record_id: str, operation: str = "update",
                data: Dict = None) -> int:
        """将任务加入队列"""
        conn = sqlite3.connect(SYNC_DB)
        cursor = conn.execute("""
            INSERT INTO sync_queue (table_name, record_id, operation, data)
            VALUES (?, ?, ?, ?)
        """, (
            table_name,
            str(record_id),
            operation,
            json.dumps(data, ensure_ascii=False) if data else "{}"
        ))
        conn.commit()
        task_id = cursor.lastrowid
        conn.close()
        return task_id
    
    def enqueue_batch(self, table_name: str, records: List[Dict]) -> int:
        """批量入队"""
        count = 0
        conn = sqlite3.connect(SYNC_DB)
        for record in records:
            conn.execute("""
                INSERT INTO sync_queue (table_name, record_id, operation, data)
                VALUES (?, ?, ?, ?)
            """, (
                table_name,
                str(record.get("id", "")),
                record.get("operation", "update"),
                json.dumps(record.get("data", {}), ensure_ascii=False)
            ))
            count += 1
        conn.commit()
        conn.close()
        return count
    
    def dequeue_pending(self, limit: int = 100) -> List[SyncTask]:
        """取出待处理任务"""
        conn = sqlite3.connect(SYNC_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT * FROM sync_queue 
            WHERE status = 'pending' 
            ORDER BY created_at ASC 
            LIMIT ?
        """, (limit,))
        
        tasks = []
        for row in cursor.fetchall():
            tasks.append(SyncTask(
                id=row["id"],
                table_name=row["table_name"],
                record_id=row["record_id"],
                operation=row["operation"],
                data=json.loads(row["data"]) if row["data"] else {},
                status=row["status"],
                retry_count=row["retry_count"],
                max_retries=row["max_retries"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                error_message=row["error_message"]
            ))
        
        conn.close()
        return tasks
    
    def mark_completed(self, task_id: int):
        """标记任务完成"""
        conn = sqlite3.connect(SYNC_DB)
        conn.execute("""
            UPDATE sync_queue 
            SET status = 'completed', updated_at = datetime('now')
            WHERE id = ?
        """, (task_id,))
        conn.commit()
        conn.close()
    
    def mark_batch_completed(self, task_ids: List[int]):
        """批量标记完成"""
        if not task_ids:
            return
        conn = sqlite3.connect(SYNC_DB)
        placeholders = ','.join('?' * len(task_ids))
        conn.execute(f"""
            UPDATE sync_queue 
            SET status = 'completed', updated_at = datetime('now')
            WHERE id IN ({placeholders})
        """, task_ids)
        conn.commit()
        conn.close()
    
    def mark_failed(self, task_id: int, error_message: str):
        """标记任务失败"""
        conn = sqlite3.connect(SYNC_DB)
        cursor = conn.execute("""
            UPDATE sync_queue 
            SET status = CASE 
                WHEN retry_count >= max_retries THEN 'failed'
                ELSE 'pending'
            END,
            retry_count = retry_count + 1,
            error_message = ?,
            updated_at = datetime('now')
            WHERE id = ?
        """, (error_message, task_id))
        conn.commit()
        conn.close()
    
    def get_queue_stats(self) -> Dict:
        """获取队列统计"""
        conn = sqlite3.connect(SYNC_DB)
        cursor = conn.execute("""
            SELECT 
                status,
                table_name,
                COUNT(*) as count
            FROM sync_queue 
            GROUP BY status, table_name
        """)
        stats = {}
        for row in cursor.fetchall():
            key = f"{row[0]}_{row[1]}"
            stats[key] = row[2]
        conn.close()
        return stats
    
    def get_queue_summary(self) -> Dict:
        """获取队列汇总"""
        conn = sqlite3.connect(SYNC_DB)
        cursor = conn.execute("""
            SELECT 
                status, COUNT(*) as count
            FROM sync_queue 
            GROUP BY status
        """)
        summary = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}
        for row in cursor.fetchall():
            summary[row[0]] = row[1]
        
        cursor = conn.execute("SELECT COUNT(*) FROM sync_queue WHERE status IN ('pending', 'processing')")
        summary["active"] = cursor.fetchone()[0]
        
        conn.close()
        return summary
    
    def cleanup_old(self, days: int = 7):
        """清理旧记录"""
        conn = sqlite3.connect(SYNC_DB)
        conn.execute("""
            DELETE FROM sync_queue 
            WHERE status IN ('completed', 'failed') 
            AND updated_at < datetime('now', ?)
        """, (f'-{days} days',))
        deleted = conn.total_changes
        conn.commit()
        conn.close()
        print(f"清理了 {deleted} 条旧同步记录")
        return deleted
    
    def retry_failed(self) -> int:
        """重试所有失败的任务"""
        conn = sqlite3.connect(SYNC_DB)
        conn.execute("""
            UPDATE sync_queue 
            SET status = 'pending', retry_count = 0, error_message = ''
            WHERE status = 'failed'
        """)
        count = conn.total_changes
        conn.commit()
        conn.close()
        return count
    
    def purge_queue(self):
        """清空队列"""
        conn = sqlite3.connect(SYNC_DB)
        conn.execute("DELETE FROM sync_queue")
        conn.commit()
        conn.close()


def process_queue(batch_size: int = 100) -> Dict:
    """
    处理同步队列
    返回: {"success": int, "failed": int, "processed": int}
    """
    from core.simple_sync import process_sync_queue
    
    manager = SyncQueueManager()
    
    # 取出待处理任务
    tasks = manager.dequeue_pending(batch_size)
    
    if not tasks:
        return {"success": 0, "failed": 0, "processed": 0}
    
    result = {"success": 0, "failed": 0, "processed": len(tasks)}
    
    # 按表分组
    table_tasks: Dict[str, List[SyncTask]] = {}
    for task in tasks:
        if task.table_name not in table_tasks:
            table_tasks[task.table_name] = []
        table_tasks[task.table_name].append(task)
    
    # 逐表处理
    for table_name, table_task_list in table_tasks.items():
        for task in table_task_list:
            try:
                # 同步到云端
                success = _sync_single_record(table_name, task)
                
                if success:
                    manager.mark_completed(task.id)
                    result["success"] += 1
                else:
                    manager.mark_failed(task.id, "云端同步失败")
                    result["failed"] += 1
                    
            except Exception as e:
                manager.mark_failed(task.id, str(e))
                result["failed"] += 1
    
    return result


def _sync_single_record(table_name: str, task: SyncTask) -> bool:
    """同步单条记录到云端"""
    try:
        from core.simple_sync import sync_single_record
        return sync_single_record(table_name, task.operation, task.data)
    except Exception as e:
        print(f"同步失败 [{table_name}/{task.record_id}]: {e}")
        return False


def get_sync_manager() -> SyncQueueManager:
    """获取同步队列管理器实例"""
    return SyncQueueManager()
