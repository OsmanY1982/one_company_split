"""
离线队列服务
网络断开时暂存操作，恢复后批量同步
"""

import json
import sqlite3
import threading
from typing import Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum


class QueueStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OfflineQueue:
    """离线队列"""

    def __init__(self, db_path: str = "data/offline_queue.db"):
        self.db_path = db_path
        self._is_online = True
        self._processors: Dict[str, Callable] = {}
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    data TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP
                )
            """)
            conn.commit()

    def register_processor(self, operation: str, processor: Callable):
        """注册处理器"""
        self._processors[operation] = processor

    def enqueue(self, operation: str, data: Dict) -> Dict:
        """入队"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO queue (operation, data) VALUES (?, ?)",
                (operation, json.dumps(data))
            )
            queue_id = cursor.lastrowid
            conn.commit()

        # 如果在线，立即处理
        if self._is_online:
            self._process_item(queue_id)

        return {"success": True, "queue_id": queue_id}

    def _process_item(self, queue_id: int):
        """处理单个队列项"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM queue WHERE id = ?", (queue_id,))
                item = cursor.fetchone()

                if not item:
                    return

                item = dict(item)

                if item["status"] != "pending":
                    return

                # 标记处理中
                conn.execute(
                    "UPDATE queue SET status = ? WHERE id = ?",
                    (QueueStatus.PROCESSING.value, queue_id)
                )
                conn.commit()

            processor = self._processors.get(item["operation"])
            if not processor:
                self._update_status(queue_id, QueueStatus.FAILED, "未注册的处理器")
                return

            try:
                data = json.loads(item["data"])
                result = processor(data)

                self._update_status(queue_id, QueueStatus.COMPLETED)

            except Exception as e:
                retry_count = item["retry_count"] + 1
                max_retries = item["max_retries"]

                if retry_count >= max_retries:
                    self._update_status(queue_id, QueueStatus.FAILED, str(e))
                else:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute(
                            "UPDATE queue SET retry_count = ?, error_message = ?, status = ? WHERE id = ?",
                            (retry_count, str(e), QueueStatus.PENDING.value, queue_id)
                        )
                        conn.commit()

    def _update_status(self, queue_id: int, status: QueueStatus, error: Optional[str] = None):
        """更新状态"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE queue SET status = ?, error_message = ?, processed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status.value, error, queue_id)
            )
            conn.commit()

    def process_pending(self):
        """处理所有待处理项"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id FROM queue WHERE status = ?",
                (QueueStatus.PENDING.value,)
            )
            items = cursor.fetchall()

        for item in items:
            self._process_item(item["id"])

    def set_online_status(self, is_online: bool):
        """设置在线状态"""
        was_offline = not self._is_online
        self._is_online = is_online

        # 恢复在线时处理队列
        if was_offline and is_online:
            self.process_pending()

    def get_queue_stats(self) -> Dict:
        """获取队列统计"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM queue 
                GROUP BY status
            """)
            stats = {row[0]: row[1] for row in cursor.fetchall()}

        return {
            "pending": stats.get("pending", 0),
            "processing": stats.get("processing", 0),
            "completed": stats.get("completed", 0),
            "failed": stats.get("failed", 0),
        }

    def get_failed_items(self) -> List[Dict]:
        """获取失败项"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM queue WHERE status = ? ORDER BY created_at DESC",
                (QueueStatus.FAILED.value,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def retry_failed(self):
        """重试失败项"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE queue SET status = ?, retry_count = 0, error_message = NULL WHERE status = ?",
                (QueueStatus.PENDING.value, QueueStatus.FAILED.value)
            )
            conn.commit()

        self.process_pending()

    def clear_completed(self):
        """清除已完成项"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM queue WHERE status = ?", (QueueStatus.COMPLETED.value,))
            conn.commit()

    def clear_all(self):
        """清空队列"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM queue")
            conn.commit()


class QueuedOperation:
    """队列操作数据模型"""

    def __init__(self, operation: str, data: Dict, priority: int = 0):
        self.operation = operation
        self.data = data
        self.priority = priority
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "operation": self.operation,
            "data": self.data,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
        }

