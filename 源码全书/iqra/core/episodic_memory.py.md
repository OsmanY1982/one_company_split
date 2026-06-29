# `iqra/core/episodic_memory.py`

> 路径：`iqra/core/episodic_memory.py` | 行数：533


---


```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EpisodicMemory — 跨会话情节记忆层

将历史会话摘要向量化后存入 BM25 + SQLite 索引，新会话开始时自动检索
相关记忆并注入 LLM 上下文。解决 AI Agent "跨会话失忆"痛点。

设计：
  L1 工作记忆（LLM Context）     ← session 内已有
  L2 情节记忆（本模块）           ← 历史会话摘要 + BM25 检索
  L3 语义记忆（semantic_search） ← IDF 加权余弦重排序
  L4 程序性记忆（ToolRegistry）  ← 工具定义，已实现

检索流程：
  用户提问 → BM25 召回 top-15 历史情节
           → SemanticReranker 重排序 → top-5
           → 注入 LLM 上下文 prefixed as <episodic_memory>

压缩策略：
  超过 max_episodes 时，将最旧的两条合并为一条摘要，减少存储但保留信息。

用法:
    from iqra.core.episodic_memory import EpisodicMemory

    mem = EpisodicMemory("/path/to/iqra_data")
    mem.record("帮我重构登录模块", "已完成：提取 AuthService、迁移 3 个调用方...")
    relevant = mem.retrieve("登录模块还有什么问题", top_k=5)
    context = mem.get_context("登录模块还有什么问题")
    # → "<episodic_memory>\n## 历史会话 2026-06-28\n重构登录模块...\n</episodic_memory>"

不引入新依赖——纯 Python stdlib + sqlite3 + 复用 workspace_indexer BM25/Tokenizer。
"""

import json
import logging
import os
import sqlite3
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from .workspace_indexer import BM25, Tokenizer

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────
# 常量
# ──────────────────────────────────────────────────────

DEFAULT_MAX_EPISODES = 50        # 最多保留的情节数
DEFAULT_TOP_K = 5                # 检索返回数
DEFAULT_EPISODE_TTL = 90         # 情节过期天数（0=永不过期）
CONTEXT_PREFIX = "<episodic_memory>\n以下是此前相关会话的操作记录，请在回答时参考：\n\n"


# ──────────────────────────────────────────────────────
# 数据类
# ──────────────────────────────────────────────────────


@dataclass
class Episode:
    """单条情节记忆"""
    id: int = 0
    session_id: str = ""
    timestamp: str = ""           # ISO 时间戳
    user_query: str = ""          # 用户原始提问（前 500 字符）
    summary: str = ""             # AI 执行摘要（前 2000 字符）
    tools_used: str = ""          # 用过的工具列表，逗号分隔
    project: str = ""             # 关联项目路径
    importance: float = 0.0       # 重要性分数（0-1）


@dataclass
class RetrievalResult:
    """检索结果"""
    episode: Episode
    score: float
    query_match: str              # 匹配的查询片段


# ──────────────────────────────────────────────────────
# SQLite 持久化
# ──────────────────────────────────────────────────────


_SQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS episodes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    timestamp   TEXT NOT NULL,
    user_query  TEXT NOT NULL,
    summary     TEXT NOT NULL,
    tools_used  TEXT DEFAULT '',
    project     TEXT DEFAULT '',
    importance  REAL DEFAULT 0.0
);

CREATE INDEX IF NOT EXISTS idx_episodes_session ON episodes(session_id);
CREATE INDEX IF NOT EXISTS idx_episodes_ts ON episodes(timestamp);
CREATE INDEX IF NOT EXISTS idx_episodes_project ON episodes(project);
"""


class EpisodicDB:
    """情节记忆的 SQLite 持久层"""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.executescript(_SQL_SCHEMA)
            conn.commit()
            conn.close()

    def insert(self, episode: Episode) -> int:
        """插入情节，返回自增 id"""
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            cur = conn.execute(
                """INSERT INTO episodes (session_id, timestamp, user_query, summary, tools_used, project, importance)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (episode.session_id, episode.timestamp, episode.user_query,
                 episode.summary, episode.tools_used, episode.project, episode.importance),
            )
            row_id = cur.lastrowid
            conn.commit()
            conn.close()
            return row_id

    def get_all(self, project: str = "", limit: int = DEFAULT_MAX_EPISODES) -> List[Episode]:
        """获取所有情节（按时间倒序）"""
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            if project:
                rows = conn.execute(
                    "SELECT * FROM episodes WHERE project = ? ORDER BY timestamp DESC LIMIT ?",
                    (project, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM episodes ORDER BY timestamp DESC LIMIT ?", (limit,)
                ).fetchall()
            conn.close()
        return [_row_to_episode(dict(r)) for r in rows]

    def get_by_id(self, episode_id: int) -> Optional[Episode]:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM episodes WHERE id = ?", (episode_id,)).fetchone()
            conn.close()
        return _row_to_episode(dict(row)) if row else None

    def get_oldest(self, project: str = "", n: int = 2) -> List[Episode]:
        """获取最旧的 n 条（用于压缩）"""
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            if project:
                rows = conn.execute(
                    "SELECT * FROM episodes WHERE project = ? ORDER BY timestamp ASC LIMIT ?",
                    (project, n),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM episodes ORDER BY timestamp ASC LIMIT ?", (n,)
                ).fetchall()
            conn.close()
        return [_row_to_episode(dict(r)) for r in rows]

    def update_summary(self, episode_id: int, new_summary: str, new_importance: float = 0.0):
        """更新摘要（用于压缩合并）"""
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.execute(
                "UPDATE episodes SET summary = ?, importance = ? WHERE id = ?",
                (new_summary, new_importance, episode_id),
            )
            conn.commit()
            conn.close()

    def delete(self, episode_id: int):
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            conn.execute("DELETE FROM episodes WHERE id = ?", (episode_id,))
            conn.commit()
            conn.close()

    def delete_old(self, project: str = "", ttl_days: int = DEFAULT_EPISODE_TTL):
        """删除过期情节"""
        if ttl_days <= 0:
            return
        cutoff = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        # 通过 Python 计算 cutoff 日期——简化处理，直接在 SQL 中比较
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            if project:
                conn.execute(
                    "DELETE FROM episodes WHERE project = ? AND timestamp < datetime('now', ?)",
                    (project, f'-{ttl_days} days'),
                )
            else:
                conn.execute(
                    "DELETE FROM episodes WHERE timestamp < datetime('now', ?)",
                    (f'-{ttl_days} days',),
                )
            deleted = conn.total_changes
            conn.commit()
            conn.close()
        if deleted:
            logger.info("EpisodicMemory: pruned %d expired episodes (TTL=%dd)", deleted, ttl_days)

    def count(self, project: str = "") -> int:
        with self._lock:
            conn = sqlite3.connect(self._db_path)
            if project:
                row = conn.execute(
                    "SELECT COUNT(*) FROM episodes WHERE project = ?", (project,)
                ).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()
            conn.close()
        return row[0] if row else 0

    def close(self):
        pass  # SQLite 每次操作后自动关闭连接


def _row_to_episode(row: dict) -> Episode:
    return Episode(
        id=row.get("id", 0),
        session_id=row.get("session_id", ""),
        timestamp=row.get("timestamp", ""),
        user_query=row.get("user_query", ""),
        summary=row.get("summary", ""),
        tools_used=row.get("tools_used", ""),
        project=row.get("project", ""),
        importance=row.get("importance", 0.0),
    )


# ──────────────────────────────────────────────────────
# 情节记忆引擎
# ──────────────────────────────────────────────────────


class EpisodicMemory:
    """
    跨会话情节记忆引擎。

    核心职责：
      record()  — 记录一次会话摘要
      retrieve() — 检索与当前问题相关的历史情节
      get_context() — 返回可直接注入 LLM 的上下文文本
      compress() — 合并最旧记忆，控制总量
    """

    def __init__(self, data_dir: str, project: str = ""):
        """
        Args:
            data_dir:  数据目录（如 /path/to/iqra/data/episodic/）
            project:   关联项目路径（用于多项目隔离）
        """
        self._project = project
        self._data_dir = os.path.join(data_dir, "episodic")
        os.makedirs(self._data_dir, exist_ok=True)

        db_path = os.path.join(self._data_dir, "episodes.db")
        self._db = EpisodicDB(db_path)

        # 检索引擎（懒构建）
        self._bm25: Optional[BM25] = None
        self._index_dirty: bool = True

        # 配置
        self.max_episodes = DEFAULT_MAX_EPISODES
        self.top_k = DEFAULT_TOP_K
        self.ttl_days = DEFAULT_EPISODE_TTL

        # 统计
        self._record_count: int = 0
        self._retrieve_count: int = 0

    # ── 记录 ──────────────────────────────────────

    def record(
        self,
        user_query: str,
        summary: str,
        session_id: str = "",
        tools_used: List[str] = None,
        importance: float = 0.0,
    ) -> int:
        """
        记录一次会话的情节。

        Args:
            user_query: 用户提问（前 500 字符自动截断）
            summary:    AI 执行摘要
            session_id: 会话标识
            tools_used: 用到的工具名列表
            importance: 重要性 0-1

        Returns:
            情节 ID
        """
        episode = Episode(
            session_id=session_id or _default_session_id(),
            timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            user_query=user_query[:500],
            summary=summary[:2000],
            tools_used=", ".join(tools_used) if tools_used else "",
            project=self._project,
            importance=importance,
        )
        eid = self._db.insert(episode)
        self._index_dirty = True
        self._record_count += 1

        # 超量压缩
        if self._db.count(self._project) > self.max_episodes:
            self.compress()

        # 清理过期
        self._db.delete_old(self._project, self.ttl_days)

        return eid

    # ── 检索 ──────────────────────────────────────

    def retrieve(self, query: str, top_k: int = None) -> List[RetrievalResult]:
        """
        检索与当前问题相关的历史情节。BM25 全文检索。
        """
        top_k = top_k or self.top_k
        self._ensure_index()

        episodes = self._db.get_all(self._project, self.max_episodes)
        if not episodes:
            return []

        # BM25 检索
        bm25_results = self._bm25.search(query, top_k=min(top_k, len(episodes)))
        if not bm25_results:
            return []

        # 构建结果
        results = []
        for doc_idx, score in bm25_results:
            if doc_idx >= len(episodes):
                continue
            ep = episodes[doc_idx]
            results.append(RetrievalResult(
                episode=ep,
                score=round(score, 4),
                query_match=_highlight_match(ep.user_query, query)[:120],
            ))

        self._retrieve_count += 1
        return results

    def get_context(self, query: str, top_k: int = None, max_chars: int = 3000) -> str:
        """
        检索并格式化为 LLM 上下文注入文本。

        返回格式:
            <episodic_memory>
            ## 历史会话 2026-06-28
            提问: 重构登录模块
            执行: 提取 AuthService、迁移 3 个调用方...
            ---
            ## 历史会话 2026-06-27
            ...
            </episodic_memory>
        """
        results = self.retrieve(query, top_k)
        if not results:
            return ""

        lines = [CONTEXT_PREFIX]
        total = 0
        for r in results:
            ep = r.episode
            # 提取日期部分
            date_str = ep.timestamp[:10] if len(ep.timestamp) >= 10 else ep.timestamp
            block = (
                f"## 历史会话 {date_str}\n"
                f"提问: {ep.user_query[:200]}\n"
                f"执行: {ep.summary[:300]}\n"
            )
            if ep.tools_used:
                block += f"工具: {ep.tools_used}\n"
            block += "---\n"
            if total + len(block) > max_chars:
                break
            lines.append(block)
            total += len(block)

        lines.append("</episodic_memory>")
        return "\n".join(lines)

    # ── 压缩 ──────────────────────────────────────

    def compress(self, n: int = 2):
        """
        将最旧的 n 条情节合并为一条摘要，减少存储。
        合并方式：取第一条的 timestamp，拼接摘要并用 --- 分隔。
        """
        oldest = self._db.get_oldest(self._project, n)
        if len(oldest) < 2:
            return

        # 以第一条为容器，合并摘要
        keeper = oldest[0]
        merged = keeper.summary
        for ep in oldest[1:]:
            merged += f"\n---\n{ep.user_query[:100]}: {ep.summary[:200]}"

        self._db.update_summary(
            keeper.id,
            merged[:2000],
            max(keeper.importance, *(e.importance for e in oldest[1:])),
        )
        # 删除被合并的
        for ep in oldest[1:]:
            self._db.delete(ep.id)

        self._index_dirty = True
        logger.debug(
            "EpisodicMemory: compressed %d episodes → id=%d (%d chars)",
            n, keeper.id, len(merged),
        )

    # ── 内部方法 ──────────────────────────────────

    def _ensure_index(self):
        """保证 BM25 索引与数据库同步"""
        if not self._index_dirty and self._bm25 is not None:
            return

        episodes = self._db.get_all(self._project, self.max_episodes)
        if not episodes:
            self._bm25 = BM25()
            self._bm25.index([])
            self._index_dirty = False
            return

        # 构建文档：user_query + " " + summary 作为索引文本
        docs = []
        for ep in episodes:
            docs.append(f"{ep.user_query} {ep.summary}")

        self._bm25 = BM25()
        self._bm25.index(docs)
        self._index_dirty = False

    @property
    def stats(self) -> dict:
        return {
            "total_episodes": self._db.count(self._project),
            "record_count": self._record_count,
            "retrieve_count": self._retrieve_count,
            "max_episodes": self.max_episodes,
            "top_k": self.top_k,
            "ttl_days": self.ttl_days,
            "project": self._project,
            "index_dirty": self._index_dirty,
        }


# ──────────────────────────────────────────────────────
# 上下文注入器（对齐 RAGContextInjector 接口）
# ──────────────────────────────────────────────────────


class EpisodicContextInjector:
    """
    情节记忆上下文注入器。

    在 AgentLoop 每次执行前调用 inject()，将相关历史情节
    注入用户消息前缀。

    用法:
        injector = EpisodicContextInjector(memory)
        augmented = injector.inject("帮我检查登录模块的 bug")
        # → "<episodic_memory>...此前修复过登录模块超时问题...</episodic_memory>\n帮我检查登录模块的 bug"
    """

    def __init__(self, memory: EpisodicMemory, max_context_chars: int = 2000):
        self._memory = memory
        self._max_context_chars = max_context_chars

    def inject(self, user_message: str) -> str:
        """在用户消息前注入相关历史情节"""
        context = self._memory.get_context(user_message, top_k=3, max_chars=self._max_context_chars)
        if not context:
            return user_message
        return context + "\n" + user_message


# ──────────────────────────────────────────────────────
# 辅助
# ──────────────────────────────────────────────────────


def _default_session_id() -> str:
    """生成默认 session ID"""
    return datetime.now().strftime("session_%Y%m%d_%H%M%S")


def _highlight_match(text: str, query: str, window: int = 60) -> str:
    """高亮匹配片段：在 text 中找到 query 关键词附近的文本"""
    if not query:
        return text[:window]
    query_lower = query.lower()
    text_lower = text.lower()
    pos = text_lower.find(query_lower)
    if pos >= 0:
        start = max(0, pos - window // 2)
        end = min(len(text), pos + len(query) + window // 2)
        return text[start:end]
    # 没有精确匹配，返回开头
    return text[:window * 2]

```
