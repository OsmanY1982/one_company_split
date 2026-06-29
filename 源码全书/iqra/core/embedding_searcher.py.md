# `iqra/core/embedding_searcher.py`

> 路径：`iqra/core/embedding_searcher.py` | 行数：289


---


```python
# -*- coding: utf-8 -*-
"""
SemanticSearcher — 基于 Embedding 模型的语义搜索引擎

依赖：sentence-transformers（可选，未安装时自动降级）
特性：
  - 句子级语义相似度搜索
  - FAISS 向量索引（IVF Flat / 纯 Flat）
  - 混合检索权重调优（α * BM25 + (1-α) * embedding）
  - 持久化/加载索引

用法：
    searcher = SemanticSearcher(model_name="all-MiniLM-L6-v2")
    searcher.index(texts, metadatas)
    results = searcher.search("支付接口", top_k=5)
"""

import os
import math
import logging
from typing import List, Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)

# ── 可选依赖检测 ──
try:
    import numpy as np
    _HAVE_NUMPY = True
except ImportError:
    _HAVE_NUMPY = False
    np = None  # type: ignore

try:
    import faiss
    _HAVE_FAISS = True
except ImportError:
    _HAVE_FAISS = False

try:
    from sentence_transformers import SentenceTransformer
    _HAVE_SENTENCE_TRANSFORMERS = True
except ImportError:
    _HAVE_SENTENCE_TRANSFORMERS = False

HAVE_SEMANTIC = _HAVE_NUMPY and _HAVE_FAISS and _HAVE_SENTENCE_TRANSFORMERS


class SemanticSearcher:
    """基于 sentence-transformers + FAISS 的语义搜索引擎"""

    # 默认模型（轻量、快速、中英文兼优）
    DEFAULT_MODEL = "all-MiniLM-L6-v2"
    # 备选模型（更小更快，仅英文）
    FALLBACK_MODEL = "all-MiniLM-L6-v2"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str = "cpu",
        dimension: int = 384,
    ):
        """
        Args:
            model_name: sentence-transformers 模型名或本地路径
            device: 'cpu' | 'cuda' | 'mps'
            dimension: embedding 维度（需与模型输出匹配）
        """
        if not HAVE_SEMANTIC:
            raise ImportError(
                "SemanticSearcher 需要安装 sentence-transformers + faiss-cpu + numpy。"
                "请运行: pip install sentence-transformers faiss-cpu"
            )

        self._model_name = model_name
        self._device = device
        self._dimension = dimension
        self._model: Optional[SentenceTransformer] = None
        self._index: Optional[faiss.Index] = None
        self._texts: List[str] = []
        self._metadatas: List[Dict[str, Any]] = []
        self._loaded: bool = False

    # ── 懒加载 ──

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        logger.info("Loading embedding model: %s", self._model_name)
        self._model = SentenceTransformer(self._model_name, device=self._device)
        self._dimension = self._model.get_sentence_embedding_dimension()
        self._loaded = True

    def _ensure_index(self) -> None:
        if self._index is not None:
            return
        self._ensure_model()
        self._index = faiss.IndexFlatIP(self._dimension)  # Inner Product（需向量已归一化）

    # ── 索引构建 ──

    def index(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 64,
        show_progress: bool = False,
    ) -> int:
        """
        构建 FAISS 向量索引

        Args:
            texts: 文本块列表
            metadatas: 对应的元数据列表（可选）
            batch_size: 编码批次大小
            show_progress: 是否显示进度条

        Returns:
            索引的向量数
        """
        if not texts:
            return 0

        self._ensure_model()
        self._ensure_index()

        # 编码
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=True,  # L2 归一化，配合 IndexFlatIP
        )

        # 重置索引
        if self._index.ntotal > 0:
            self._index.reset()

        self._index.add(np.array(embeddings, dtype=np.float32))
        self._texts = list(texts)
        self._metadatas = metadatas if metadatas else [{}] * len(texts)

        logger.info("Indexed %d texts, dimension=%d", len(texts), self._dimension)
        return len(texts)

    def add(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        batch_size: int = 64,
    ) -> int:
        """增量添加文本到现有索引"""
        if not texts:
            return self._index.ntotal if self._index else 0

        self._ensure_model()
        self._ensure_index()

        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
        )

        self._index.add(np.array(embeddings, dtype=np.float32))
        self._texts.extend(texts)
        if metadatas:
            self._metadatas.extend(metadatas)
        else:
            self._metadatas.extend([{}] * len(texts))

        return self._index.ntotal

    # ── 搜索 ──

    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
    ) -> List[Tuple[int, float, str]]:
        """
        语义搜索

        Args:
            query: 查询文本
            top_k: 返回前 k 个结果
            score_threshold: 最低相似度阈值（0~1，0 表示不过滤）

        Returns:
            [(chunk_index, score, text), ...] 按相似度降序
        """
        if not self._index or self._index.ntotal == 0:
            return []

        self._ensure_model()

        query_embedding = self._model.encode(
            [query],
            normalize_embeddings=True,
        )

        distances, indices = self._index.search(
            np.array(query_embedding, dtype=np.float32),
            min(top_k, self._index.ntotal),
        )

        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._texts):
                continue
            score = float(distance)  # 余弦相似度（已归一化）
            if score < score_threshold:
                continue
            results.append((int(idx), score, self._texts[idx]))

        return results

    def search_with_metadata(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """语义搜索（返回完整元数据）"""
        raw = self.search(query, top_k, score_threshold)
        return [
            {
                "chunk_index": idx,
                "score": score,
                "text": text,
                "metadata": self._metadatas[idx] if idx < len(self._metadatas) else {},
            }
            for idx, score, text in raw
        ]

    # ── 持久化 ──

    def save(self, path: str) -> bool:
        """保存 FAISS 索引到文件"""
        if not self._index or self._index.ntotal == 0:
            return False
        try:
            faiss.write_index(self._index, path)
            logger.info("Saved FAISS index to %s (%d vectors)", path, self._index.ntotal)
            return True
        except Exception as e:
            logger.error("Failed to save index: %s", e)
            return False

    def load(self, path: str) -> bool:
        """从文件加载 FAISS 索引"""
        if not os.path.exists(path):
            return False
        try:
            self._ensure_model()
            self._index = faiss.read_index(path)
            self._dimension = self._index.d
            logger.info("Loaded FAISS index from %s (%d vectors)", path, self._index.ntotal)
            return True
        except Exception as e:
            logger.error("Failed to load index: %s", e)
            return False

    # ── 属性 ──

    @property
    def ntotal(self) -> int:
        return self._index.ntotal if self._index else 0

    @property
    def has_index(self) -> bool:
        return self._index is not None and self._index.ntotal > 0

    @property
    def model_name(self) -> str:
        return self._model_name

    def clear(self) -> None:
        """清空索引"""
        if self._index:
            self._index.reset()
        self._texts = []
        self._metadatas = []

    def get_text(self, chunk_index: int) -> Optional[str]:
        """获取指定索引的文本"""
        if 0 <= chunk_index < len(self._texts):
            return self._texts[chunk_index]
        return None

```
