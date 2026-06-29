# `iqra/core/session_search.py`

> 路径：`iqra/core/session_search.py` | 行数：202


---


```python
"""
Iqra Session Search - 历史会话搜索

提供:
- 历史会话全文搜索
- 会话标题/摘要检索
- 时间范围过滤
- 关键词高亮
"""

import os
import json
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional


class SessionSearch:
    """历史会话搜索引擎"""
    
    _DEFAULT_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "sessions.db")

    def __init__(self, db_path: str = None):
        self.db_path = db_path or self._DEFAULT_DB
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT,
                summary TEXT,
                created_at REAL,
                updated_at REAL,
                message_count INTEGER DEFAULT 0,
                tags TEXT,
                content_snapshot TEXT
            )
        """)
        # FTS5 全文搜索
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(
                title, summary, content_snapshot,
                content='sessions', content_rowid='rowid'
            )
        """)
        conn.commit()
        conn.close()
    
    def save_session(self, session_id: str, title: str = "", summary: str = "", 
                    message_count: int = 0, tags: List[str] = None, content: str = ""):
        """保存会话索引"""
        conn = sqlite3.connect(self.db_path)
        now = time.time()
        
        conn.execute("""
            INSERT OR REPLACE INTO sessions 
            (id, title, summary, created_at, updated_at, message_count, tags, content_snapshot)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, title, summary, now, now, message_count,
            json.dumps(tags or []), content[:5000]  # 限制快照长度
        ))
        
        # 更新 FTS 索引
        conn.execute("""
            INSERT OR REPLACE INTO sessions_fts (rowid, title, summary, content_snapshot)
            SELECT rowid, title, summary, content_snapshot FROM sessions WHERE id = ?
        """, (session_id,))
        
        conn.commit()
        conn.close()
    
    def search(self, query: str, limit: int = 10, days: int = None) -> List[Dict]:
        """搜索历史会话"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        if days:
            cutoff = time.time() - (days * 86400)
            date_filter = "AND s.updated_at > ?"
            params = [query, cutoff, limit]
        else:
            date_filter = ""
            params = [query, limit]
        
        rows = conn.execute(f"""
            SELECT s.*, rank
            FROM sessions_fts f
            JOIN sessions s ON f.rowid = s.rowid
            WHERE sessions_fts MATCH ?
            {date_filter}
            ORDER BY rank
            LIMIT ?
        """, params).fetchall()
        
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                "id": row["id"],
                "title": row["title"],
                "summary": row["summary"],
                "created_at": datetime.fromtimestamp(row["created_at"]).isoformat(),
                "updated_at": datetime.fromtimestamp(row["updated_at"]).isoformat(),
                "message_count": row["message_count"],
                "tags": json.loads(row["tags"] or "[]"),
                "relevance": max(0, 1.0 - row["rank"])
            })
        
        return results
    
    def get_recent(self, limit: int = 10) -> List[Dict]:
        """获取最近会话"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        rows = conn.execute("""
            SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "summary": row["summary"],
                "created_at": datetime.fromtimestamp(row["created_at"]).isoformat(),
                "updated_at": datetime.fromtimestamp(row["updated_at"]).isoformat(),
                "message_count": row["message_count"],
                "tags": json.loads(row["tags"] or "[]")
            }
            for row in rows
        ]
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取单个会话详情"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        conn.close()
        
        if row:
            return {
                "id": row["id"],
                "title": row["title"],
                "summary": row["summary"],
                "created_at": datetime.fromtimestamp(row["created_at"]).isoformat(),
                "updated_at": datetime.fromtimestamp(row["updated_at"]).isoformat(),
                "message_count": row["message_count"],
                "tags": json.loads(row["tags"] or "[]"),
                "content_snapshot": row["content_snapshot"]
            }
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.execute("DELETE FROM sessions_fts WHERE rowid NOT IN (SELECT rowid FROM sessions)")
        conn.commit()
        conn.close()
        return True
    
    def get_stats(self) -> Dict:
        """获取统计"""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(message_count) as avg_messages,
                MIN(created_at) as oldest,
                MAX(updated_at) as newest
            FROM sessions
        """).fetchone()
        conn.close()
        
        return {
            "total_sessions": row[0] or 0,
            "avg_messages": round(row[1] or 0, 1),
            "oldest_session": datetime.fromtimestamp(row[2]).isoformat() if row[2] else None,
            "newest_session": datetime.fromtimestamp(row[3]).isoformat() if row[3] else None
        }


# ═══════════════════════════════════════════
# 全局实例
# ═══════════════════════════════════════════

_session_search = None

def get_session_search(db_path: str = None) -> SessionSearch:
    global _session_search
    if _session_search is None:
        _session_search = SessionSearch(db_path)
    return _session_search

```
