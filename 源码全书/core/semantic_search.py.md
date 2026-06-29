# `core/semantic_search.py`

> 路径：`core/semantic_search.py` | 行数：12


---


```python
"""桥接存根: core.semantic_search → iqra.core.semantic_search"""

from iqra.core.semantic_search import SemanticReranker

# agent_bridge 期望 SemanticSearcher（即 SemanticReranker）
SemanticSearcher = SemanticReranker


class HybridRetriever(SemanticReranker):
    """HybridRetriever = BM25 初筛 + Embedding 精排（当前用 SemanticReranker 兜底）"""
    def search(self, query, top_k=5, **kwargs):
        return self.rerank(query, [], top_k=top_k)

```
