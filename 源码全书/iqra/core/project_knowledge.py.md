# `iqra/core/project_knowledge.py`

> 路径：`iqra/core/project_knowledge.py` | 行数：219


---


```python
"""
ProjectKnowledge — 项目知识库索引器。自动扫描 AI设计规范.txt / 项目全书 / 源码全书，
按 ## 标题分块建 BM25 索引，结果缓存到 SQLite。
"""

import os, re, sqlite3, time
from typing import Optional

from iqra.core._tokenizer import Tokenizer
from iqra.core._bm25 import BM25

_SOURCE_PATHS = [
    "/Volumes/E盘存储区/脚本与文档/AI设计规范.txt",
    "/Volumes/D盘工作区/一人公司拆分版/one_company_split/项目全书/",
    "/Volumes/D盘工作区/一人公司拆分版/one_company_split/源码全书/",
]
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_REL_PATH = os.path.join("data", "project_knowledge.db")

_HEADING_RE = re.compile(r'^##\s+(.*)', re.MULTILINE)
_TEXT_EXTS = {".txt", ".md", ".markdown"}


def _split_by_headings(text: str) -> list[tuple[str, str]]:
    """按 ## 标题分块，返回 [(title, chunk_text), ...] 列表。"""
    chunks: list[tuple[str, str]] = []
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        stripped = text.strip()
        if stripped:
            chunks.append(("", stripped))
        return chunks
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            chunks.append((title, body))
    return chunks


def _collect_files() -> list[str]:
    """收集所有待索引文件路径。"""
    files: list[str] = []
    for sp in _SOURCE_PATHS:
        sp = os.path.normpath(sp)
        if os.path.isfile(sp):
            if os.path.splitext(sp)[1].lower() in _TEXT_EXTS:
                files.append(sp)
        elif os.path.isdir(sp):
            for root, _dirs, fnames in os.walk(sp):
                for fn in fnames:
                    if os.path.splitext(fn)[1].lower() in _TEXT_EXTS:
                        files.append(os.path.join(root, fn))
    return sorted(set(files))


# ── ProjectKnowledge ──────────────────────────────────────

class ProjectKnowledge:
    """项目知识库索引与检索。"""

    def __init__(self, db_path: Optional[str] = None):
        db = db_path or os.path.join(_PROJECT_ROOT, _DB_REL_PATH)
        os.makedirs(os.path.dirname(db), exist_ok=True)
        self._db_path = db
        self._conn = sqlite3.connect(db)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS project_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT NOT NULL, chunk_id TEXT NOT NULL,
                title TEXT DEFAULT '', content TEXT NOT NULL,
                mtime REAL, indexed_at REAL,
                UNIQUE(source_file, chunk_id)
            );
            CREATE INDEX IF NOT EXISTS idx_chunks_source ON project_chunks(source_file);
        """)
        self._conn.commit()
        self._bm25 = BM25()
        self._chunk_meta: list[dict] = []

    # ── 公开 API ────────────────────────────────────────────

    def build_index(self, force: bool = False) -> dict:
        """全量扫描知识源文件，按 ## 标题分块建 BM25 索引。"""
        if not force and self._conn.execute(
            "SELECT COUNT(*) as c FROM project_chunks"
        ).fetchone()["c"] > 0:
            self._load_from_db()
            return self.stats()
        self._conn.execute("DELETE FROM project_chunks")
        self._conn.commit()
        return self._index_files(_collect_files())

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """BM25 检索最相关的文档分块。"""
        if not self._chunk_meta:
            self._load_from_db()
        if not self._chunk_meta:
            return []
        results = self._bm25.search(query, top_k=top_k)
        output: list[dict] = []
        for doc_idx, score in results:
            meta = self._chunk_meta[doc_idx]
            row = self._conn.execute(
                "SELECT content FROM project_chunks WHERE source_file=? AND chunk_id=?",
                (meta["source_file"], meta["chunk_id"]),
            ).fetchone()
            content = row["content"] if row else ""
            snippet = content[:300] + ("..." if len(content) > 300 else "")
            output.append({
                "source_file": meta["source_file"], "chunk_id": meta["chunk_id"],
                "title": meta["title"], "score": round(score, 4), "snippet": snippet,
            })
        return output

    def get_relevant_context(self, query: str, top_k: int = 3) -> str:
        """返回格式化上下文文本，可直接注入 LLM。"""
        results = self.search(query, top_k=top_k)
        if not results:
            return ""
        lines: list[str] = []
        for r in results:
            lines.append(f"## [{r['title'] or r['chunk_id']}] ({r['source_file']})")
            row = self._conn.execute(
                "SELECT content FROM project_chunks WHERE source_file=? AND chunk_id=?",
                (r["source_file"], r["chunk_id"]),
            ).fetchone()
            if row:
                lines.append(row["content"] + "\n")
        return "\n".join(lines).strip()

    def refresh(self) -> dict:
        """增量更新：检查文件 mtime，只重建变更文件的分块。"""
        files = _collect_files()
        changed = []
        for fpath in files:
            try:
                disk_mtime = os.path.getmtime(fpath)
            except OSError:
                continue
            row = self._conn.execute(
                "SELECT mtime FROM project_chunks WHERE source_file=? LIMIT 1",
                (fpath,),
            ).fetchone()
            if not row or abs(row["mtime"] - disk_mtime) > 1.0:
                changed.append(fpath)
        if not changed:
            return {"changed_files": 0, "message": "所有文件均为最新"}
        for fpath in changed:
            self._conn.execute("DELETE FROM project_chunks WHERE source_file=?", (fpath,))
        self._conn.commit()
        self._index_files(changed)
        return {"changed_files": len(changed), "message": f"已更新 {len(changed)} 个文件"}

    def stats(self) -> dict:
        """返回 (file_count, chunk_count, index_size)。"""
        fc = self._conn.execute(
            "SELECT COUNT(DISTINCT source_file) as c FROM project_chunks").fetchone()["c"]
        cc = self._conn.execute(
            "SELECT COUNT(*) as c FROM project_chunks").fetchone()["c"]
        sz = os.path.getsize(self._db_path) if os.path.exists(self._db_path) else 0
        return {"file_count": fc, "chunk_count": cc, "index_size": sz}

    # ── 内部 ────────────────────────────────────────────────

    def _index_files(self, files: list[str]) -> dict:
        """索引指定文件列表，重建 BM25。"""
        now = time.time()
        documents: list[str] = []
        self._chunk_meta = []
        for fpath in files:
            try:
                with open(fpath, "r", encoding="utf-8") as fh:
                    text = fh.read()
            except Exception:
                continue
            mtime = os.path.getmtime(fpath)
            for title, body in _split_by_headings(text):
                cid = title if title else f"_untitled_{len(self._chunk_meta)}"
                self._conn.execute(
                    "INSERT OR REPLACE INTO project_chunks"
                    " (source_file, chunk_id, title, content, mtime, indexed_at)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    (fpath, cid, title, body, mtime, now),
                )
                documents.append(body)
                self._chunk_meta.append(
                    {"source_file": fpath, "chunk_id": cid, "title": title})
        self._conn.commit()
        if documents:
            self._bm25.index(documents)
        return self.stats()

    def _load_from_db(self) -> None:
        """从 SQLite 加载所有分块到内存，重建 BM25 索引。"""
        rows = self._conn.execute(
            "SELECT source_file, chunk_id, title, content FROM project_chunks ORDER BY id"
        ).fetchall()
        self._chunk_meta = []
        docs = []
        for r in rows:
            self._chunk_meta.append(
                {"source_file": r["source_file"], "chunk_id": r["chunk_id"], "title": r["title"]})
            docs.append(r["content"])
        if docs:
            self._bm25.index(docs)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

```
