# `iqra/core/todo_system.py`

> 路径：`iqra/core/todo_system.py` | 行数：229


---


```python
"""
Iqra Todo System - 任务清单系统

提供:
- 任务创建/更新/删除
- 状态管理 (pending/in_progress/completed)
- 任务优先级排序
- 多任务并发控制
"""

import os
import json
import time
import sqlite3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class TodoItem:
    """任务项"""
    id: str
    content: str
    status: str  # pending / in_progress / completed / cancelled
    priority: int = 0
    created_at: float = None
    updated_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = time.time()


class TodoSystem:
    """任务清单系统"""
    
    STATUS_ORDER = {
        "pending": 0,
        "in_progress": 1,
        "completed": 2,
        "cancelled": 3
    }
    
    _DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "todos.db")

    def __init__(self, db_path: str = None):
        self.db_path = db_path or self._DEFAULT_DB
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    
    def add(self, content: str, priority: int = 0) -> str:
        """添加任务"""
        import uuid
        task_id = str(uuid.uuid4())[:12]
        now = time.time()
        
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO todos VALUES (?, ?, ?, ?, ?, ?)",
            (task_id, content, "pending", priority, now, now)
        )
        conn.commit()
        conn.close()
        return task_id
    
    def update_status(self, task_id: str, status: str):
        """更新任务状态"""
        if status not in self.STATUS_ORDER:
            raise ValueError(f"无效状态：{status}")
        
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE todos SET status = ?, updated_at = ? WHERE id = ?",
            (status, time.time(), task_id)
        )
        conn.commit()
        conn.close()
    
    def mark_completed(self, task_id: str):
        """标记完成"""
        self.update_status(task_id, "completed")
    
    def mark_in_progress(self, task_id: str):
        """设为进行中"""
        # 先确保其他 in_progress 任务被恢复为 pending
        self._reset_other_in_progress(task_id)
        self.update_status(task_id, "in_progress")
    
    def _reset_other_in_progress(self, exclude_task_id: str):
        """重置其他进行中的任务"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE todos 
            SET status = 'pending', updated_at = ? 
            WHERE status = 'in_progress' AND id != ?
        """, (time.time(), exclude_task_id))
        conn.commit()
        conn.close()
    
    def cancel(self, task_id: str):
        """取消任务"""
        self.update_status(task_id, "cancelled")
    
    def delete(self, task_id: str) -> bool:
        """删除任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("DELETE FROM todos WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    def get_all(self) -> List[TodoItem]:
        """获取所有任务（按优先级和状态排序）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        rows = conn.execute("""
            SELECT * FROM todos 
            ORDER BY 
                CASE status
                    WHEN 'pending' THEN 0
                    WHEN 'in_progress' THEN 1
                    WHEN 'completed' THEN 2
                    WHEN 'cancelled' THEN 3
                END,
                priority DESC,
                created_at ASC
        """).fetchall()
        conn.close()
        
        return [
            TodoItem(
                id=row["id"],
                content=row["content"],
                status=row["status"],
                priority=row["priority"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
            for row in rows
        ]
    
    def get_pending(self) -> List[TodoItem]:
        """获取待处理任务"""
        items = self.get_all()
        return [item for item in items if item.status == "pending"]
    
    def get_in_progress(self) -> List[TodoItem]:
        """获取进行中任务"""
        items = self.get_all()
        return [item for item in items if item.status == "in_progress"]
    
    def get_completed(self) -> List[TodoItem]:
        """获取已完成任务"""
        items = self.get_all()
        return [item for item in items if item.status == "completed"]
    
    def get(self, task_id: str) -> Optional[TodoItem]:
        """获取单个任务"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (task_id,)).fetchone()
        conn.close()
        
        if row:
            return TodoItem(
                id=row["id"],
                content=row["content"],
                status=row["status"],
                priority=row["priority"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
        return None
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status='in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status='cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM todos
        """).fetchone()
        conn.close()
        
        return {
            "total": row[0],
            "pending": row[1],
            "in_progress": row[2],
            "completed": row[3],
            "cancelled": row[4],
            "completion_rate": round((row[3] / row[0] * 100) if row[0] > 0 else 0, 1)
        }


# ═══════════════════════════════════════════
# 全局实例
# ═══════════════════════════════════════════

_todo_system = None

def get_todo_system(db_path: str = None) -> TodoSystem:
    global _todo_system
    if _todo_system is None:
        _todo_system = TodoSystem(db_path)
    return _todo_system

```
