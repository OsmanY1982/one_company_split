# `iqra/core/book_search.py`

> 路径：`iqra/core/book_search.py` | 行数：318


---


```python
# -*- coding: utf-8 -*-
"""项目全书全局搜索 — 对项目全书/ 目录下 Markdown 文档做全文检索

特性:
  - 扫描 项目全书/ 目录所有 .md 文件
  - 按 ## 二级标题分块建索引（每块 = 一个 BM25 文档）
  - 标题区域加权（前 5 行 ×2 权重）+ 文档级同义词扩展
  - JSON 磁盘缓存，mtime 增量更新
  - CLI 入口: python -m iqra.core.book_search "查询词"

用法:
    from iqra.core.book_search import BookSearcher

    searcher = BookSearcher()
    searcher.build_index()  # 首次构建

    results = searcher.search("Agent 引擎架构", top_k=5)
    for r in results:
        print(f"[{r.file_name}] {r.heading} (score={r.score:.2f})")
        print(f"  {r.snippet[:100]}...")
"""

import os
import json
import time
import fnmatch
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

from ._bm25 import BM25
from ._tokenizer import Tokenizer


# ─── 常量 ─────────────────────────────────────────────
_BOOK_DIR = "/Volumes/D盘工作区/一人公司拆分版/one_company_split/项目全书"
_CACHE_PATH = os.path.join(_BOOK_DIR, ".book_index_cache.json")
_DEFAULT_TOP_K = 10


# ─── 数据结构 ─────────────────────────────────────────

@dataclass
class BookResult:
    """单条搜索结果"""
    file_path: str          # 绝对路径
    file_name: str          # 文件名（如 01_深空渲染引擎_cosmic.md）
    heading: str            # 所属 ## 标题（无标题则为 "(正文)"）
    score: float            # BM25 分数
    snippet: str            # 匹配片段的纯文本摘要（最多 250 字符）


@dataclass
class BookStats:
    """索引统计信息"""
    total_files: int = 0
    total_sections: int = 0
    index_time_ms: float = 0.0
    cache_hit: bool = False


# ─── 核心类 ──────────────────────────────────────────

class BookSearcher:
    """项目全书搜索器"""

    def __init__(self, book_dir: str = _BOOK_DIR, cache_path: str = _CACHE_PATH):
        self.book_dir = book_dir
        self.cache_path = cache_path
        self._bm25: Optional[BM25] = None
        # _sections[i] = (file_path, file_name, heading, snippet)
        self._sections: List[Tuple[str, str, str, str]] = []
        self._docs: List[str] = []           # 每个 section 的索引文本
        self._mtime_map: Dict[str, float] = {}  # 文件路径 → mtime
        self._stats = BookStats()

    # ── 公共接口 ─────────────────────────────────────

    def build_index(self, force: bool = False) -> BookStats:
        """建索引：缓存有效则直接加载，否则扫描重建"""
        if not force and self._try_load_cache():
            self._stats.cache_hit = True
            return self._stats

        t0 = time.time()
        self._sections = []
        self._docs = []
        self._mtime_map = {}

        md_files = self._scan_md_files()
        for fpath in sorted(md_files):
            sections = self._parse_sections(fpath)
            self._sections.extend(sections)
            self._docs.extend([s[3] for s in sections])
            self._mtime_map[fpath] = os.path.getmtime(fpath)

        self._bm25 = BM25(title_lines=5, title_boost=2.0)
        if self._docs:
            self._bm25.index(self._docs)

        self._stats = BookStats(
            total_files=len(md_files),
            total_sections=len(self._docs),
            index_time_ms=(time.time() - t0) * 1000,
        )
        self._save_cache()
        return self._stats

    def search(self, query: str, top_k: int = _DEFAULT_TOP_K) -> List[BookResult]:
        """全文搜索项目全书，返回 top_k 条结果"""
        if self._bm25 is None:
            self.build_index()
        if not self._docs:
            return []

        scored = self._bm25.search(query, top_k=top_k, expand_synonyms=True, phrase_boost=3.0)
        results = []
        for doc_idx, score in scored:
            fpath, fname, heading, _ = self._sections[doc_idx]
            snippet = self._extract_snippet(self._docs[doc_idx], query, max_len=250)
            results.append(BookResult(
                file_path=fpath,
                file_name=fname,
                heading=heading,
                score=round(score, 4),
                snippet=snippet,
            ))
        return results

    def reload(self) -> BookStats:
        """强制重建索引（用于文档更新后）"""
        return self.build_index(force=True)

    # ── 内部方法 ─────────────────────────────────────

    def _scan_md_files(self) -> List[str]:
        """扫描项目全书目录下所有 .md 文件（跳过隐藏文件和缓存）"""
        files = []
        for root, dirs, filenames in os.walk(self.book_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fname in filenames:
                if fname.endswith(".md") and not fname.startswith("."):
                    files.append(os.path.join(root, fname))
        return files

    def _parse_sections(self, file_path: str) -> List[Tuple[str, str, str, str]]:
        """解析单个 Markdown 文件，按 ## 标题分块

        Returns:
            [(file_path, file_name, heading, doc_text), ...]
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return []

        fname = os.path.basename(file_path)
        sections: List[Tuple[str, str, str, str]] = []

        # 按 ## 行切分（保留 # 和 ### 作为上下文但不用于切分）
        lines = content.split("\n")
        current_heading = "(正文)"
        current_start = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            # 仅 ## 开头（非 ### 等更深层级）触发切分
            if stripped.startswith("## ") and not stripped.startswith("### "):
                # 保存上一个 section
                if i > current_start:
                    doc_text = "\n".join(lines[current_start:i]).strip()
                    if doc_text:
                        sections.append((file_path, fname, current_heading, doc_text))
                current_heading = stripped[3:].strip()
                current_start = i

        # 最后一个 section
        if current_start < len(lines):
            doc_text = "\n".join(lines[current_start:]).strip()
            if doc_text:
                sections.append((file_path, fname, current_heading, doc_text))

        return sections

    def _extract_snippet(self, doc_text: str, query: str, max_len: int = 250) -> str:
        """从文档文本中提取与查询相关的摘要片段"""
        if len(doc_text) <= max_len:
            return doc_text

        # 查找包含查询关键词的最佳位置
        query_tokens = Tokenizer.tokenize(query)
        best_pos = 0
        best_score = -1

        # 滑动窗口扫描
        window = max_len
        step = max_len // 2
        for start in range(0, len(doc_text) - window + 1, step):
            window_text = doc_text[start:start + window]
            score = sum(1 for t in query_tokens if t.lower() in window_text.lower())
            if score > best_score:
                best_score = score
                best_pos = start

        snippet = doc_text[best_pos:best_pos + max_len].strip()
        # 裁剪到最近的完整行
        if best_pos > 0:
            first_nl = snippet.find("\n")
            if first_nl > 0 and first_nl < 40:
                snippet = snippet[first_nl + 1:]
        last_nl = snippet.rfind("\n")
        if last_nl > max_len * 0.7:
            snippet = snippet[:last_nl]

        return snippet + "…" if len(doc_text) > best_pos + max_len else snippet

    # ── 缓存 ─────────────────────────────────────────

    def _try_load_cache(self) -> bool:
        """尝试从磁盘缓存加载索引，同时检查 mtime 是否过期"""
        if not os.path.exists(self.cache_path):
            return False

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return False

        # 检查缓存版本和 mtime 一致性
        cached_mtimes = data.get("mtime_map", {})
        md_files = self._scan_md_files()
        if len(cached_mtimes) != len(md_files):
            return False
        for fpath in md_files:
            cached_mt = cached_mtimes.get(fpath)
            if cached_mt is None:
                return False
            try:
                actual_mt = os.path.getmtime(fpath)
            except OSError:
                return False
            if abs(actual_mt - cached_mt) > 1.0:  # 允许 1 秒偏差
                return False

        # 恢复状态
        self._sections = [(s[0], s[1], s[2], s[3]) for s in data.get("sections", [])]
        self._docs = data.get("docs", [])
        self._mtime_map = cached_mtimes

        self._bm25 = BM25(title_lines=5, title_boost=2.0)
        if self._docs:
            self._bm25.index(self._docs)

        self._stats = BookStats(
            total_files=len(md_files),
            total_sections=len(self._docs),
            cache_hit=True,
        )
        return True

    def _save_cache(self) -> None:
        """保存索引缓存到磁盘"""
        data = {
            "sections": list(self._sections),
            "docs": self._docs,
            "mtime_map": self._mtime_map,
        }
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception:
            pass  # 缓存写入失败不阻塞搜索功能


# ─── CLI 入口 ─────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="项目全书全局搜索")
    parser.add_argument("query", nargs="?", default="", help="搜索关键词")
    parser.add_argument("-k", "--top", type=int, default=_DEFAULT_TOP_K, help="返回结果数")
    parser.add_argument("--rebuild", action="store_true", help="强制重建索引")
    parser.add_argument("--stats", action="store_true", help="仅显示索引统计")
    args = parser.parse_args()

    searcher = BookSearcher()

    if args.rebuild:
        stats = searcher.reload()
    else:
        stats = searcher.build_index()

    if args.stats or not args.query:
        tag = "缓存命中" if stats.cache_hit else "重建索引"
        print(f"项目全书索引 | {tag}")
        print(f"  文件数: {stats.total_files}")
        print(f"  分块数: {stats.total_sections}")
        if stats.index_time_ms > 0:
            print(f"  耗时: {stats.index_time_ms:.0f}ms")
        if not args.query:
            sys.exit(0)

    results = searcher.search(args.query, top_k=args.top)
    if not results:
        print(f"未找到与「{args.query}」相关的内容")
        sys.exit(0)

    print(f"\n搜索「{args.query}」— 共 {len(results)} 条结果:\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r.file_name}] {r.heading}  (score={r.score:.3f})")
        lines = r.snippet.split("\n")
        for line in lines[:4]:
            print(f"   {line}")
        print()

```
