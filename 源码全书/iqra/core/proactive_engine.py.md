# `iqra/core/proactive_engine.py`

> 路径：`iqra/core/proactive_engine.py` | 行数：235


---


```python
"""
ProactiveEngine — 主动巡检与告警引擎
接入 WorkspaceWatcher + CodeHealthChecker，定期检查并持久化告警。
"""

import os
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "proactive_alerts.db"
CHECK_INTERVAL = 300  # 5 分钟

CORE_FILES = [
    "cosmic.py", "agent.py", "data.py", "llm_client.py", "voice.py",
]

CREATE_ALERTS_SQL = """
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL DEFAULT 'warning',
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    file_path TEXT DEFAULT '',
    timestamp REAL NOT NULL,
    dismissed INTEGER DEFAULT 0
)
"""

CREATE_SNAPS_SQL = """
CREATE TABLE IF NOT EXISTS core_file_snapshots (
    file_path TEXT PRIMARY KEY,
    mtime REAL NOT NULL
)
"""


@dataclass
class Alert:
    alert_id: int = -1
    level: str = "warning"
    title: str = ""
    message: str = ""
    file_path: str = ""
    timestamp: float = field(default_factory=time.time)
    dismissed: bool = False


class ProactiveEngine:
    """主动巡检引擎：定期检查核心文件变更 + 导入链断裂，生成告警。"""

    def __init__(self):
        os.makedirs(DB_PATH.parent, exist_ok=True)
        self._init_db()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # 懒加载 checker（避免初始化时扫描全项目）
        self._health_checker = None

    # ------------------------------------------------------------------ 公开方法

    def start(self) -> None:
        """启动后台监控线程，每 5 分钟检查一轮。"""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._do_check()  # 启动时立即执行一轮
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def check_now(self) -> list[Alert]:
        """立即执行一轮检查，返回本轮新告警。"""
        return self._do_check()

    def get_alerts(self, include_dismissed: bool = False) -> list[Alert]:
        """返回告警列表。"""
        sql = "SELECT * FROM alerts" if include_dismissed else "SELECT * FROM alerts WHERE dismissed=0"
        return self._query_alerts(sql + " ORDER BY timestamp DESC")

    def clear_alert(self, alert_id: int) -> bool:
        """清除指定告警（标记 dismissed=1）。"""
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("UPDATE alerts SET dismissed=1 WHERE id=?", (alert_id,))
        conn.commit()
        conn.close()
        return True

    # ------------------------------------------------------------------ 内部方法

    def _init_db(self) -> None:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute(CREATE_ALERTS_SQL)
        conn.execute(CREATE_SNAPS_SQL)
        conn.commit()
        conn.close()

    def _monitor_loop(self) -> None:
        while not self._stop_event.wait(CHECK_INTERVAL):
            self._do_check()

    def _do_check(self) -> list[Alert]:
        alerts: list[Alert] = []
        alerts.extend(self._check_core_files())
        alerts.extend(self._check_import_chain())
        self._save_alerts(alerts)
        return alerts

    # ── 检查项 ──

    def _check_core_files(self) -> list[Alert]:
        """检测核心文件是否被意外修改（mtime 与快照对比）。"""
        alerts: list[Alert] = []
        for fname in CORE_FILES:
            fp = PROJECT_ROOT / "core" / fname
            if not fp.exists():
                alerts.append(Alert(
                    level="error", title="核心文件缺失",
                    message=f"core/{fname} 不存在",
                    file_path=str(fp),
                ))
                continue
            current_mtime = fp.stat().st_mtime
            prev = self._get_snapshot(str(fp))
            if prev is not None and prev != current_mtime:
                alerts.append(Alert(
                    level="warning", title="核心文件已被修改",
                    message=f"core/{fname} 的修改时间发生变化（{time.ctime(prev)} → {time.ctime(current_mtime)}）",
                    file_path=str(fp),
                ))
            self._set_snapshot(str(fp), current_mtime)
        return alerts

    def _check_import_chain(self) -> list[Alert]:
        """检测导入链断裂（调用 CodeHealthChecker 快速检查）。"""
        if self._health_checker is None:
            try:
                from iqra.core.code_health_checker import CodeHealthChecker
                self._health_checker = CodeHealthChecker()
            except Exception:
                return []
        try:
            report = self._health_checker.run_quick_check()
        except Exception:
            return []
        alerts: list[Alert] = []
        if report.broken_imports:
            for item in report.broken_imports:
                alerts.append(Alert(
                    level="error", title="导入链断裂",
                    message=f"语法错误: {item['error']}",
                    file_path=item["path"],
                ))
        if report.oversized_files:
            for item in report.oversized_files:
                alerts.append(Alert(
                    level="info", title="文件行数超标",
                    message=f"{item['path']} 共 {item['lines']} 行（阈值 500）",
                    file_path=item["path"],
                ))
        return alerts

    # ── 快照持久化 ──

    def _get_snapshot(self, file_path: str) -> Optional[float]:
        conn = sqlite3.connect(str(DB_PATH))
        row = conn.execute(
            "SELECT mtime FROM core_file_snapshots WHERE file_path=?",
            (file_path,),
        ).fetchone()
        conn.close()
        return row[0] if row else None

    def _set_snapshot(self, file_path: str, mtime: float) -> None:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute(
            "INSERT OR REPLACE INTO core_file_snapshots (file_path, mtime) VALUES (?, ?)",
            (file_path, mtime),
        )
        conn.commit()
        conn.close()

    # ── 告警持久化 ──

    def _save_alerts(self, alerts: list[Alert]) -> None:
        if not alerts:
            return
        conn = sqlite3.connect(str(DB_PATH))
        now = time.time()
        conn.executemany(
            "INSERT INTO alerts (level, title, message, file_path, timestamp) VALUES (?,?,?,?,?)",
            [(a.level, a.title, a.message, a.file_path, now) for a in alerts],
        )
        conn.commit()
        conn.close()

    def _query_alerts(self, sql: str) -> list[Alert]:
        conn = sqlite3.connect(str(DB_PATH))
        rows = conn.execute(sql).fetchall()
        conn.close()
        return [
            Alert(alert_id=r[0], level=r[1], title=r[2], message=r[3],
                  file_path=r[4], timestamp=r[5], dismissed=bool(r[6]))
            for r in rows
        ]


# ═══════════════════════════════════════════
# 全局单例
# ═══════════════════════════════════════════

_proactive: Optional[ProactiveEngine] = None


def get_proactive_engine() -> ProactiveEngine:
    global _proactive
    if _proactive is None:
        _proactive = ProactiveEngine()
    return _proactive


def reset_proactive_engine() -> None:
    global _proactive
    if _proactive:
        _proactive.stop()
    _proactive = None

```
