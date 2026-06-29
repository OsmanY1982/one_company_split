# `iqra/core/rag_context.py`

> 路径：`iqra/core/rag_context.py` | 行数：347


---


```python
# -*- coding: utf-8 -*-
"""
RAGContextInjector — 工作区上下文自动注入（对标 Codex 的 Context Engine）

职责:
  1. 管理 WorkspaceIndexer 实例（单例）
  2. 在用户消息前自动注入相关代码上下文
  3. 提供 set_project / unset 切换项目
  4. 集成 HybridRetriever（BM25 + Embedding 语义搜索），BM25 作为降级后备
"""

import os
import threading
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .workspace_indexer import WorkspaceIndexer, SearchResult


# ── 可选依赖检测 ──

try:
    from .semantic_search import SemanticSearcher
    from .semantic_search.hybrid_retriever import HybridRetriever
    _HAVE_SEMANTIC_SEARCH = True
except ImportError:
    _HAVE_SEMANTIC_SEARCH = False
    SemanticSearcher = None
    HybridRetriever = None


def _get_indexer_cls():
    """延迟导入，避免 iqra/__init__.py 的 requests 依赖阻塞"""
    from .workspace_indexer import WorkspaceIndexer, SearchResult
    return WorkspaceIndexer, SearchResult


# 上下文注入提示词模板
CONTEXT_PROMPT_PREFIX = """<workspace_context>
以下是当前项目工作区的相关代码文件，请在回答时参考：

{context}

</workspace_context>

"""


class RAGContextInjector:
    """RAG 上下文注入器（线程安全单例）"""

    _instance: Optional["RAGContextInjector"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._indexer = None  # WorkspaceIndexer instance
        self._hybrid = None   # HybridRetriever（BM25 + Embedding 语义搜索）
        self._project_path: str = ""
        self._auto_context_chars: int = 4000  # 自动注入最大字符数
        self._enabled: bool = True

    # ── 项目管理 ──

    def set_project(self, project_path: str, build: bool = False) -> bool:
        """
        设置/切换项目工作区

        Args:
            project_path: 项目根目录路径
            build: 是否立即构建索引

        Returns:
            是否设置成功
        """
        if not os.path.isdir(project_path):
            return False

        self._project_path = os.path.abspath(project_path)
        WSCls, _ = _get_indexer_cls()
        self._indexer = WSCls(self._project_path)

        if build:
            self._indexer.build()

        return True

    @property
    def has_project(self) -> bool:
        return self._indexer is not None and os.path.isdir(self._project_path)

    @property
    def project_path(self) -> str:
        return self._project_path

    @property
    def indexer(self):  # → WorkspaceIndexer | None
        return self._indexer

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, val: bool) -> None:
        self._enabled = val

    @property
    def hybrid(self):
        """HybridRetriever 实例（可能为 None）"""
        return self._hybrid

    # ── 配置 ──

    def get_config(self) -> dict:
        return {
            "project_path": self._project_path,
            "enabled": self._enabled,
            "auto_context_chars": self._auto_context_chars,
            "has_indexer": self._indexer is not None,
            "has_semantic": self._hybrid is not None and self._hybrid.has_semantic,
            "search_mode": self._hybrid.mode if self._hybrid else "bm25_only",
        }

    def load_config(self, cfg: dict) -> None:
        self._enabled = cfg.get("enabled", True)
        self._auto_context_chars = cfg.get("auto_context_chars", 4000)
        if cfg.get("project_path"):
            self.set_project(cfg["project_path"])

    # ── 上下文注入 ──

    def _ensure_hybrid(self) -> bool:
        """确保 HybridRetriever 已初始化（延迟加载 semantic_search 模型）"""
        if self._hybrid is not None:
            return True
        if not _HAVE_SEMANTIC_SEARCH or not self._indexer:
            return False
        try:
            semantic = SemanticSearcher()
            self._hybrid = HybridRetriever(self._indexer, semantic_searcher=semantic)
            return True
        except Exception:
            return False

    def get_context(self, query: str, max_chars: int = 4000, top_k: int = 5, use_semantic: bool = True) -> str:
        """
        获取与查询最相关的文件上下文文本（不包装 XML，给外部注入器使用）

        优先走 HybridRetriever，失败降级 BM25。
        """
        if not self._enabled or not self._indexer:
            return ""

        if use_semantic and self._ensure_hybrid():
            return self._hybrid.get_context(query, max_chars=max_chars, top_k=top_k, use_semantic=True)

        return self._indexer.get_context(query, max_chars=max_chars, top_k=top_k, semantic=False)

    def inject_context(self, user_message: str, max_chars: int = 0) -> str:
        """
        在用户消息前注入工作区上下文 + 项目规则（IQRA.md）

        优先使用 HybridRetriever（BM25 + Embedding 语义搜索）；
        若语义搜索模块未安装或失败，自动降级为纯 BM25。

        Args:
            user_message: 原始用户消息
            max_chars: 上下文最大字符数，0 使用默认值

        Returns:
            注入后的完整消息（或无变更的原始消息）
        """
        if not self._enabled or not self._indexer:
            return user_message

        chars = max_chars or self._auto_context_chars

        # 优先走 HybridRetriever（BM25 → Embedding 精排）
        if self._ensure_hybrid():
            context = self._hybrid.get_context(user_message, max_chars=chars, top_k=5, use_semantic=True)
        else:
            # 降级：纯 BM25
            context = self._indexer.get_context(user_message, max_chars=chars, top_k=5, semantic=False)

        # 注入项目规则（IQRA.md）
        rules = self.get_project_rules()
        if rules:
            context = rules + "\n\n" + context if context else rules

        if not context:
            return user_message

        return CONTEXT_PROMPT_PREFIX.format(context=context) + user_message

    # ── 项目规则 ──

    def get_project_rules(self) -> str:
        """
        读取项目根目录的 IQRA.md（对标 Claude Code 的 CLAUDE.md）

        Returns:
            IQRA.md 内容（含标记），或空字符串
        """
        if not self._project_path:
            return ""

        rules_paths = [
            os.path.join(self._project_path, "IQRA.md"),
            os.path.join(self._project_path, "iqra", "IQRA.md"),
        ]
        for path in rules_paths:
            if os.path.isfile(path):
                try:
                    content = open(path, encoding="utf-8").read()
                    return f"<project_rules>\n{content.strip()}\n</project_rules>"
                except Exception:
                    pass
        return ""

    def search(self, query: str, top_k: int = 10, use_semantic: bool = True) -> list:
        """
        搜索工作区 — 优先走 HybridRetriever，失败降级 BM25

        Args:
            query: 查询字符串
            top_k: 返回前 k 个结果
            use_semantic: 是否启用语义精排
        """
        if not self._indexer:
            return []
        if use_semantic and self._ensure_hybrid():
            return self._hybrid.search(query, top_k=top_k, use_semantic=True)
        return self._indexer.search(query, top_k)

    def build_index(self) -> Optional[object]:
        """构建/重建索引"""
        if not self._indexer:
            return None
        return self._indexer.build()

    def update_index(self) -> Optional[object]:
        """增量更新索引"""
        if not self._indexer:
            return None
        return self._indexer.update()

    def hybrid_index_size(self) -> int:
        """返回当前 FAISS 向量索引的总向量数（无索引返回 0）"""
        if not self._hybrid or not self._hybrid.has_semantic:
            return 0
        try:
            return self._hybrid._semantic._index.ntotal if self._hybrid._semantic._index else 0
        except Exception:
            return 0

    def save_index_to_memory(self, memory_store: Any, index_name: str = "default") -> bool:
        """
        将当前 FAISS 语义索引持久化到 SmartMemoryStore。

        Args:
            memory_store: SmartMemoryStore 实例（需有 set_semantic_index() 方法）
            index_name: 索引名称

        Returns:
            是否成功
        """
        if not self._hybrid or not self._hybrid.has_semantic:
            return False
        try:
            searcher = self._hybrid._semantic
            if not searcher._index:
                return False
            # FAISS 写入临时文件再读回二进制
            import faiss
            import tempfile
            tmp = tempfile.NamedTemporaryFile(suffix=".faiss", delete=False)
            try:
                faiss.write_index(searcher._index, tmp.name)
                tmp.close()
                with open(tmp.name, "rb") as f:
                    data = f.read()
            finally:
                import os as _os
                try:
                    _os.unlink(tmp.name)
                except OSError:
                    pass
            return memory_store.set_semantic_index(data, index_name)
        except Exception as e:
            logger.debug("Failed to save semantic index to memory: %s", e)
            return False

    def load_index_from_memory(self, memory_store: Any, index_name: str = "default") -> bool:
        """
        从 SmartMemoryStore 加载之前持久化的 FAISS 索引。

        Args:
            memory_store: SmartMemoryStore 实例
            index_name: 索引名称

        Returns:
            是否加载成功
        """
        try:
            data = memory_store.get_semantic_index(index_name)
            if not data:
                return False
            if not self._hybrid or not self._hybrid.has_semantic:
                return False
            import faiss
            import tempfile
            tmp = tempfile.NamedTemporaryFile(suffix=".faiss", delete=False)
            try:
                tmp.write(data)
                tmp.flush()
                self._hybrid._semantic._index = faiss.read_index(tmp.name)
            finally:
                import os as _os
                try:
                    _os.unlink(tmp.name)
                except OSError:
                    pass
            return True
        except Exception as e:
            logger.debug("Failed to load semantic index from memory: %s", e)
            return False

    def clear(self) -> None:
        """清空当前项目"""
        self._project_path = ""
        if self._hybrid:
            self._hybrid.clear()
            self._hybrid = None
        if self._indexer:
            self._indexer.clear()
            self._indexer = None

```
