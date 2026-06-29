# `iqra/core/memory.py`

> 路径：`iqra/core/memory.py` | 行数：227


---


```python
"""
Iqra Memory - 跨会话持久化记忆系统

提供:
- 用户偏好持久化
- 环境/项目事实存储
- 记忆分类管理 (user / system)
- 自动压缩与淘汰
"""

import os
import json
import time
import sqlite3
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    category: str  # user / system
    content: str
    priority: int  # 0-10, 10 最高
    created_at: float
    last_accessed: float
    access_count: int


class IqraMemory:
    """跨会话持久化记忆"""
    
    _DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "memory.db")

    def __init__(self, db_path: str = None):
        self.db_path = db_path or self._DEFAULT_DB
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                priority INTEGER DEFAULT 5,
                created_at REAL NOT NULL,
                last_accessed REAL NOT NULL,
                access_count INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()
    
    def add(self, category: str, content: str, priority: int = 5) -> str:
        """添加记忆"""
        import uuid
        entry_id = str(uuid.uuid4())[:12]
        now = time.time()
        
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?, 0)",
            (entry_id, category, content, priority, now, now)
        )
        conn.commit()
        conn.close()
        return entry_id
    
    def replace(self, entry_id: str, new_content: str):
        """替换记忆内容"""
        # 检查记忆是否存在
        old_entry = self.get(entry_id)
        if not old_entry:
            raise ValueError(f"记忆不存在：{entry_id}")
        
        now = time.time()
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE memories SET content = ?, last_accessed = ? WHERE id = ?
        """, (new_content, now, entry_id))
        conn.commit()
        conn.close()
    
    def get(self, entry_id: str) -> Optional[Dict]:
        """获取单个记忆"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        row = conn.execute("SELECT * FROM memories WHERE id = ?", (entry_id,)).fetchone()
        conn.close()
        
        if row:
            return {
                "id": row["id"],
                "category": row["category"],
                "content": row["content"],
                "priority": row["priority"],
                "created_at": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(row["created_at"])),
                "last_accessed": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(row["last_accessed"])),
                "access_count": row["access_count"]
            }
        return None
    
    def update(self, entry_id: str, content: str):
        """更新记忆"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE memories SET content = ?, last_accessed = ? WHERE id = ?",
            (content, time.time(), entry_id)
        )
        conn.commit()
        conn.close()
    
    def remove(self, entry_id: str) -> bool:
        """删除记忆"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("DELETE FROM memories WHERE id = ?", (entry_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    def search(self, category: str = None, keyword: str = None, limit: int = 20) -> List[Dict]:
        """搜索记忆"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        query = "SELECT * FROM memories WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if keyword:
            query += " AND content LIKE ?"
            params.append(f"%{keyword}%")
        
        query += " ORDER BY priority DESC, last_accessed DESC LIMIT ?"
        params.append(limit)
        
        rows = conn.execute(query, params).fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "id": row["id"],
                "category": row["category"],
                "content": row["content"],
                "priority": row["priority"],
                "created_at": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(row["created_at"])),
                "last_accessed": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(row["last_accessed"])),
                "access_count": row["access_count"]
            })
            # 更新访问统计
            self._increment_access(row["id"])
        
        return results
    
    def _increment_access(self, entry_id: str):
        """增加访问计数"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE memories SET last_accessed = ?, access_count = access_count + 1 WHERE id = ?",
            (time.time(), entry_id)
        )
        conn.commit()
        conn.close()
    
    def get_recent(self, category: str = None, limit: int = 10) -> List[Dict]:
        """获取最近记忆"""
        return self.search(category=category, limit=limit)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN category='user' THEN 1 ELSE 0 END) as user_count,
                SUM(CASE WHEN category='system' THEN 1 ELSE 0 END) as system_count,
                AVG(priority) as avg_priority
            FROM memories
        """).fetchone()
        conn.close()
        
        return {
            "total": row[0],
            "user_memories": row[1],
            "system_memories": row[2],
            "avg_priority": round(row[3], 1) if row[3] else 0
        }
    
    def compact(self, max_entries: int = 100):
        """压缩记忆，保留高优先级/高访问量的"""
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        
        if count > max_entries:
            # 删除低优先级且访问量低的
            conn.execute("""
                DELETE FROM memories WHERE id IN (
                    SELECT id FROM memories 
                    ORDER BY priority ASC, access_count ASC, last_accessed ASC 
                    LIMIT ?
                )
            """, (count - max_entries,))
            conn.commit()
        
        conn.close()


# ═══════════════════════════════════════════
# 全局实例
# ═══════════════════════════════════════════

_memory = None

def get_memory(db_path: str = None) -> IqraMemory:
    global _memory
    if _memory is None:
        _memory = IqraMemory(db_path)
    return _memory

```
