# `iqra/core/semantic_search.py`

> 路径：`iqra/core/semantic_search.py` | 行数：128


---


```python
# -*- coding: utf-8 -*-
"""
SemanticReranker — BM25 语义重排序（对标 Claude Code 的混合检索）

纯 Python / numpy，零新依赖。

算法：
  1. BM25 召回 top-K（30 个候选）
  2. IDF 加权余弦相似度重排序 → top-N（5 个）
  3. 混合分数 = 0.7 × BM25 + 0.3 × cosine

效果：
  - "支付接口" 能匹配到 "支付宝集成"、"微信支付回调"等 BM25 漏掉的文档
  - 因为 IDF 给"支付"低权重、"接口"低权重时，文档中"支付宝"的高 IDF
    会在余弦空间中拉近距离
"""

import math
from collections import defaultdict
from typing import List, Dict, Tuple


class SemanticReranker:
    """
    基于 IDF 加权余弦相似度的语义重排序器

    用法:
        reranker = SemanticReranker()
        reranker.fit(doc_tokens, df, num_docs)  # 传入 BM25 已计算好的统计量
        results = reranker.rerank(query_tokens, bm25_candidates, top_k=5, alpha=0.3)
    """

    def __init__(self):
        self._doc_tokens: List[List[str]] = []
        self._idf: Dict[str, float] = {}
        self._num_docs: int = 0

    def fit(self, doc_tokens: List[List[str]], df: Dict[str, int], num_docs: int) -> None:
        """
        拟合重排序器（复用 BM25 的文档频率统计）

        Args:
            doc_tokens: 所有文档的 token 列表
            df: token → 文档频率
            num_docs: 总文档数
        """
        self._doc_tokens = doc_tokens
        self._num_docs = num_docs

        # 复用 DF 计算 IDF（与 BM25 一致公式）
        self._idf = {}
        for token, doc_freq in df.items():
            self._idf[token] = math.log(1 + (num_docs - doc_freq + 0.5) / (doc_freq + 0.5))

    def rerank(
        self,
        query_tokens: List[str],
        bm25_candidates: List[Tuple[int, float]],
        top_k: int = 5,
        alpha: float = 0.3,
    ) -> List[Tuple[int, float]]:
        """
        对 BM25 候选集进行语义重排序

        Args:
            query_tokens: 查询的分词结果
            bm25_candidates: [(doc_idx, bm25_score), ...]
            top_k: 最终返回数量
            alpha: 语义权重（0 = 纯 BM25，1 = 纯余弦）

        Returns:
            重排序后的 [(doc_idx, combined_score), ...]
        """
        if not bm25_candidates or not self._idf:
            return bm25_candidates[:top_k]

        # ── BM25 分数 min-max 归一化到 [0, 1] ──
        bm25_scores = [s for _, s in bm25_candidates]
        bm25_min = min(bm25_scores)
        bm25_max = max(bm25_scores)
        bm25_range = bm25_max - bm25_min if bm25_max > bm25_min else 1.0

        # 构建查询的 IDF 加权向量
        query_vec = self._build_vector(query_tokens)

        # 对每个候选文档计算余弦相似度
        reranked = []
        for doc_idx, bm25_score in bm25_candidates:
            if doc_idx >= len(self._doc_tokens):
                continue
            doc_tokens = self._doc_tokens[doc_idx]
            doc_vec = self._build_vector(doc_tokens)
            cosine = self._cosine_similarity(query_vec, doc_vec)

            # 归一化 BM25 + 加权混合
            norm_bm25 = (bm25_score - bm25_min) / bm25_range
            combined = (1 - alpha) * norm_bm25 + alpha * cosine
            reranked.append((doc_idx, round(combined, 6)))

        # 按组合分数降序
        reranked.sort(key=lambda x: -x[1])
        return reranked[:top_k]

    def _build_vector(self, tokens: List[str]) -> Dict[str, float]:
        """构建 IDF 加权向量（归一化后的稀疏表示）"""
        vec = defaultdict(float)
        for token in tokens:
            if token in self._idf:
                vec[token] += self._idf[token]

        # L2 归一化
        norm = math.sqrt(sum(v * v for v in vec.values()))
        if norm > 0:
            for token in vec:
                vec[token] /= norm
        return vec

    def _cosine_similarity(self, vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        """稀疏向量余弦相似度（向量已预归一化时点积即为余弦）"""
        # 小遍历大
        if len(vec_a) > len(vec_b):
            vec_a, vec_b = vec_b, vec_a

        dot = 0.0
        for token, weight in vec_a.items():
            if token in vec_b:
                dot += weight * vec_b[token]
        return dot  # 已归一化，点积 = 余弦

```
