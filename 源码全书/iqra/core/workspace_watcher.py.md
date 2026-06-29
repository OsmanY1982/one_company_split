# `iqra/core/workspace_watcher.py`

> 路径：`iqra/core/workspace_watcher.py` | 行数：205


---


```python
"""
WorkspaceWatcher — 工作区文件变更监视器
基于 watchdog，监控 /Volumes/D盘工作区/ 下 .py/.json/.md/.yaml 的新增/修改/删除，
变更事件经 5 秒去重窗口后写入 SQLite。
"""

import hashlib
import os
import sqlite3
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

WATCH_ROOT = "/Volumes/D盘工作区/"
WATCH_PATTERNS = ["*.py", "*.json", "*.md", "*.yaml"]
DEBOUNCE_SECONDS = 5
FLUSH_INTERVAL = 2  # 后台刷新间隔（秒）
DB_DIR = Path(__file__).resolve().parents[1] / "data"
DB_PATH = DB_DIR / "file_events.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS file_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    timestamp REAL NOT NULL,
    size INTEGER DEFAULT -1,
    hash TEXT DEFAULT ''
)
"""


def _file_hash(path: str) -> str:
    """快速 SHA256 摘要，文件不存在或不可读返回空字符串。"""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return ""


def _safe_file_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return -1


def _priority_event(a: str, b: str) -> str:
    """合并事件类型：created + modified → created；deleted 优先。"""
    if "deleted" in (a, b):
        return "deleted"
    if "created" in (a, b):
        return "created"
    return "modified"


class _Handler(FileSystemEventHandler):
    """watchdog 事件处理器：将事件推入 WorkspaceWatcher 的待处理队列。"""

    def __init__(self, watcher: "WorkspaceWatcher"):
        super().__init__()
        self._w = watcher

    def on_created(self, event):
        if not event.is_directory:
            self._w._enqueue("created", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._w._enqueue("modified", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self._w._enqueue("deleted", event.src_path)


class WorkspaceWatcher:
    """工作区文件变更监视器。"""

    def __init__(self):
        DB_DIR.mkdir(parents=True, exist_ok=True)
        self._observer = Observer()
        self._handler = _Handler(self)
        self._lock = threading.Lock()
        # _pending: { file_path: {"type": str, "ts": float} }
        self._pending: dict[str, dict] = {}
        self._flush_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._init_db()

    # ------------------------------------------------------------------ 公开方法

    def start(self) -> None:
        """启动后台守护线程监听文件变更。"""
        self._observer.schedule(
            self._handler, WATCH_ROOT, recursive=True
        )
        self._observer.start()
        self._stop_event.clear()
        self._flush_thread = threading.Thread(
            target=self._flush_loop, daemon=True
        )
        self._flush_thread.start()

    def stop(self) -> None:
        """停止监听并等待线程退出。"""
        self._stop_event.set()
        if self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=5)
        if self._flush_thread and self._flush_thread.is_alive():
            self._flush_thread.join(timeout=5)

    def get_recent_changes(self, since_seconds: float = 3600) -> list[dict]:
        """获取最近 N 秒内的变更列表。"""
        since = time.time() - since_seconds
        return self._query(
            "SELECT * FROM file_events WHERE timestamp >= ? ORDER BY timestamp DESC",
            (since,),
        )

    def get_changes_summary(self, since_seconds: float = 86400) -> dict:
        """返回变更摘要：{created: N, modified: N, deleted: N}。"""
        since = time.time() - since_seconds
        rows = self._query(
            "SELECT event_type, COUNT(*) AS cnt FROM file_events "
            "WHERE timestamp >= ? GROUP BY event_type",
            (since,),
        )
        summary = {"created": 0, "modified": 0, "deleted": 0}
        for r in rows:
            summary[r["event_type"]] = r["cnt"]
        return summary

    def get_file_history(self, file_path: str, limit: int = 20) -> list[dict]:
        """获取指定文件的变更历史。"""
        return self._query(
            "SELECT * FROM file_events WHERE file_path = ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (file_path, limit),
        )

    # ------------------------------------------------------------------ 内部方法

    def _init_db(self) -> None:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()
        conn.close()

    def _enqueue(self, event_type: str, file_path: str) -> None:
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        if f"*.{ext}" not in WATCH_PATTERNS:
            return
        now = time.time()
        with self._lock:
            prev = self._pending.get(file_path)
            if prev and (now - prev["ts"]) < DEBOUNCE_SECONDS:
                prev["type"] = _priority_event(prev["type"], event_type)
                prev["ts"] = now
            else:
                self._pending[file_path] = {"type": event_type, "ts": now}

    def _flush_loop(self) -> None:
        """后台线程：周期性将去重窗口外的待处理事件写入 DB。"""
        while not self._stop_event.wait(FLUSH_INTERVAL):
            self._flush_due()

    def _flush_due(self) -> None:
        threshold = time.time() - DEBOUNCE_SECONDS
        ready: list[tuple[str, str, float]] = []
        with self._lock:
            keys_to_pop = [
                fp for fp, v in self._pending.items() if v["ts"] <= threshold
            ]
            for fp in keys_to_pop:
                v = self._pending.pop(fp)
                ready.append((v["type"], fp, v["ts"]))
        if not ready:
            return
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        for event_type, fp, ts in ready:
            cur.execute(
                "INSERT INTO file_events (event_type, file_path, timestamp, size, hash) "
                "VALUES (?, ?, ?, ?, ?)",
                (event_type, fp, ts, _safe_file_size(fp), _file_hash(fp)),
            )
        conn.commit()
        conn.close()

    def _query(self, sql: str, params: tuple = ()) -> list[dict]:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

```
