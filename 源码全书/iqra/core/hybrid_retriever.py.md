# `iqra/core/hybrid_retriever.py`

> 路径：`iqra/core/hybrid_retriever.py` | 行数：237


---


```python
# -*- coding: utf-8 -*-
"""
HybridRetriever — BM25 + Embedding 混合检索器

将 WorkspaceIndexer 的 BM25 召回与 SemanticSearcher 的 embedding 精排融合，
实现 Marvis 级的混合检索质量。

算法：
  1. BM25 召回 top-K（宽召回）
  2. Embedding 语义精排（窄精排）
  3. 加权融合：score = α × BM25_norm + (1-α) × embedding_score

特性：
  - 零依赖回退：无 sentence-transformers 时自动降级为纯 BM25
  - 无缝集成：与 WorkspaceIndexer + RAGContextInjector 兼容
  - 可配置权重和召回策略
"""

import logging
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .workspace_indexer import WorkspaceIndexer, SearchResult
    from .embedding_searcher import SemanticSearcher

logger = logging.getLogger(__name__)


class HybridRetriever:
    """BM25 + Embedding 混合检索引擎"""

    def __init__(
        self,
        indexer: "WorkspaceIndexer",
        semantic_searcher: Optional["SemanticSearcher"] = None,
        bm25_recall_k: int = 30,
        semantic_top_k: int = 10,
        fusion_alpha: float = 0.4,
    ):
        """
        Args:
            indexer: WorkspaceIndexer 实例（提供 BM25 检索）
            semantic_searcher: SemanticSearcher 实例（提供 embedding 检索），
                               None 时降级为纯 BM25
            bm25_recall_k: BM25 召回候选数
            semantic_top_k: 语义搜索最终返回数
            fusion_alpha: 融合权重（0=纯 embedding, 1=纯 BM25, 默认 0.4）
        """
        self._indexer = indexer
        self._semantic = semantic_searcher
        self._bm25_recall_k = bm25_recall_k
        self._semantic_top_k = semantic_top_k
        self._fusion_alpha = fusion_alpha

    # ── 状态 ──

    @property
    def has_semantic(self) -> bool:
        """是否启用了 embedding 语义搜索"""
        if self._semantic is None:
            return False
        try:
            return self._semantic.has_index
        except Exception:
            return False

    @property
    def mode(self) -> str:
        """当前检索模式"""
        if self.has_semantic:
            return "hybrid"
        return "bm25_only"

    # ── 搜索 ──

    def search(
        self,
        query: str,
        top_k: int = 10,
        use_semantic: bool = True,
    ) -> List:
        """
        混合搜索

        Args:
            query: 查询文本
            top_k: 返回前 k 个结果
            use_semantic: 是否启用语义精排

        Returns:
            SearchResult 列表
        """
        if not self._indexer:
            return []

        # Phase 1: BM25 宽召回
        bm25_results = self._indexer.search(query, top_k=self._bm25_recall_k)
        if not bm25_results:
            return []

        # 无语义或禁用 → 纯 BM25
        if not use_semantic or not self.has_semantic:
            return bm25_results[:top_k]

        # Phase 2: Embedding 精排 + 融合
        return self._fuse_results(query, bm25_results, top_k)

    def _fuse_results(self, query: str, bm25_results: List, top_k: int) -> List:
        """加权融合 BM25 和 embedding 结果"""
        try:
            semantic_results = self._semantic.search_with_metadata(
                query, top_k=self._semantic_top_k
            )
        except Exception as e:
            logger.warning("Semantic search failed, falling back to BM25: %s", e)
            return bm25_results[:top_k]

        if not semantic_results:
            return bm25_results[:top_k]

        # 构建 chunk_idx → embedding score 映射
        embedding_scores: dict = {}
        for r in semantic_results:
            chunk_idx = r.get("chunk_index", -1)
            if chunk_idx >= 0:
                embedding_scores[chunk_idx] = r["score"]

        # 归一化 BM25 分数
        bm25_scores = [r.score for r in bm25_results]
        bm25_max = max(bm25_scores) if bm25_scores else 1.0
        bm25_min = min(bm25_scores) if bm25_scores else 0.0
        bm25_range = bm25_max - bm25_min if bm25_max > bm25_min else 1.0

        # 创建 doc_idx → 融合分数
        fused: dict = {}
        for i, result in enumerate(bm25_results):
            norm_bm25 = (result.score - bm25_min) / bm25_range
            embed_score = embedding_scores.get(i, 0.0)
            fused[i] = self._fusion_alpha * norm_bm25 + (1 - self._fusion_alpha) * embed_score

        # 对纯 embedding 召回但 BM25 未覆盖的结果（通过文本匹配）
        if self._semantic and len(self._semantic._texts) > 0:
            bm25_texts = {r.snippet[:50] for r in bm25_results}  # 去重标准
            for r in semantic_results:
                chunk_idx = r.get("chunk_index", -1)
                if chunk_idx < 0 or chunk_idx in fused:
                    continue
                text = self._semantic.get_text(chunk_idx)
                if text and text[:50] not in bm25_texts:
                    fused[chunk_idx] = (1 - self._fusion_alpha) * r["score"]

        # 按分数降序返回
        sorted_indices = sorted(fused.keys(), key=lambda k: fused[k], reverse=True)[:top_k]

        # 构建结果（需要 WorkspaceIndexer 的 _chunks）
        output = []
        for idx in sorted_indices:
            if 0 <= idx < len(self._indexer._chunks):
                chunk = self._indexer._chunks[idx]
                snippet = chunk["content"][:300].replace("\n", " ")
                # 使用 SearchResult 类
                from ._index_models import SearchResult as SR
                output.append(SR(
                    file_path=chunk["file_path"],
                    chunk_index=chunk["chunk_index"],
                    score=round(fused[idx], 4),
                    snippet=snippet,
                    file_type=chunk.get("file_type", ""),
                ))
        return output

    # ── 上下文注入 ──

    def get_context(
        self,
        query: str,
        max_chars: int = 4000,
        top_k: int = 5,
        use_semantic: bool = True,
    ) -> str:
        """
        获取与查询最相关的文件上下文文本

        委托给 WorkspaceIndexer.get_context()，但使用混合搜索的排序结果。
        """
        if not self._indexer:
            return ""

        results = self.search(query, top_k=max(top_k, 10), use_semantic=use_semantic)
        if not results:
            return ""

        # 按文件去重
        seen_files = set()
        top_results = []
        for r in results:
            if r.file_path not in seen_files and len(top_results) < top_k:
                seen_files.add(r.file_path)
                top_results.append(r)

        # 构建上下文
        parts = []
        char_budget = max_chars // max(len(top_results), 1)

        for sr in top_results:
            try:
                with open(sr.file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception:
                continue

            total_len = sum(len(p) for p in parts)
            if total_len + len(content) <= max_chars:
                parts.append(f"## {sr.file_path}\n```\n{content}\n```\n")
            else:
                trimmed = content[:char_budget]
                parts.append(f"## {sr.file_path} (preview)\n```\n{trimmed}\n...\n```\n")

        return "\n".join(parts)

    # ── 索引管理 ──

    def build_semantic_index(self, texts: List[str], metadatas: List[dict] = None) -> bool:
        """构建语义索引"""
        if not self._semantic:
            return False
        try:
            self._semantic.index(texts, metadatas, show_progress=True)
            return True
        except Exception as e:
            logger.error("Failed to build semantic index: %s", e)
            return False

    def clear(self) -> None:
        """清空检索器状态"""
        if self._semantic:
            self._semantic.clear()

```
