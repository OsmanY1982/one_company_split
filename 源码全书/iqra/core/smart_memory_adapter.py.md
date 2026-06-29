# `iqra/core/smart_memory_adapter.py`

> 路径：`iqra/core/smart_memory_adapter.py` | 行数：472


---


```python
"""
Smart Memory Adapter
桥接旧版 MemoryStore 与新版 SmartMemory，统一挂载 MemoryManager 插件体系
保持向后兼容的同时提供增强功能
"""

import json
import logging
import os
from typing import Optional, Dict, List, Any

from .memory_store import MemoryStore
from .smart_memory import SmartMemory

logger = logging.getLogger(__name__)


class SmartMemoryStore:
    """
    增强版记忆存储 — 唯一记忆门面

    同时兼容旧版 MemoryStore API、SmartMemory 功能和 MemoryManager 插件体系。
    所有调用方（agent_bridge / chat_engine / enhanced_core）只通过此类访问记忆。
    """

    @property
    def base_dir(self) -> str:
        return self._legacy.base_dir

    def __init__(self, base_dir: Optional[str] = None):
        # --- 旧版存储（会话持久化）---
        self._legacy = MemoryStore(base_dir)

        # --- 智能记忆 ---
        project_root = base_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "iqra"
        )
        self._smart = SmartMemory(project_root)

        # --- MemoryManager 插件体系 ---
        self._manager = None
        self._init_memory_manager()

        # --- 核心持久化记忆（IqraMemory SQLite 降级为底层存储）---
        self._core_memory = None
        try:
            from .memory import get_memory
            self._core_memory = get_memory(os.path.join(self._legacy.base_dir, "memory.db"))
        except Exception as e:
            logger.debug("IqraMemory init skipped: %s", e)

    # ================================================================
    # MemoryManager 初始化与插件发现
    # ================================================================

    def _init_memory_manager(self) -> None:
        """初始化 MemoryManager 并加载配置中指定的外部记忆插件。

        插件加载失败不阻断启动，仅记录警告。
        """
        try:
            from agent.memory_manager import MemoryManager
            self._manager = MemoryManager()
        except Exception as e:
            logger.debug("MemoryManager not available, plugin system disabled: %s", e)
            self._manager = None
            return

        # 读取活跃的外部插件名称
        active_provider = self._get_active_provider_name()
        if not active_provider:
            logger.debug("No external memory provider configured (memory.provider in config.yaml)")
            return

        # 加载并注册插件
        try:
            from plugins.memory import load_memory_provider
            provider = load_memory_provider(active_provider)
            if provider:
                self._manager.add_provider(provider)
                logger.info("Memory provider '%s' loaded and registered", active_provider)
            else:
                logger.warning("Memory provider '%s' configured but failed to load", active_provider)
        except Exception as e:
            logger.warning("Failed to load memory provider '%s': %s", active_provider, e)

    @staticmethod
    def _get_active_provider_name() -> Optional[str]:
        """从 config.yaml 读取 memory.provider 配置。"""
        try:
            from iqra_cli.config import load_config, cfg_get
            config = load_config()
            return cfg_get(config, "memory", "provider") or None
        except Exception:
            return None

    # ================================================================
    # MemoryManager 代理方法
    # ================================================================

    def prefetch_all(self, query: str, *, session_id: str = "") -> str:
        """收集所有插件的记忆上下文。"""
        if self._manager is None:
            return ""
        return self._manager.prefetch_all(query, session_id=session_id)

    def sync_all(self, user_content: str, assistant_content: str, *,
                 session_id: str = "") -> None:
        """同步一轮对话到所有插件。"""
        if self._manager is None:
            return
        self._manager.sync_all(user_content, assistant_content, session_id=session_id)

    def get_all_tool_schemas(self) -> List[Dict[str, Any]]:
        """收集所有插件的工具 schema。"""
        if self._manager is None:
            return []
        return self._manager.get_all_tool_schemas()

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any],
                         **kwargs) -> str:
        """路由工具调用到对应插件。"""
        if self._manager is None:
            return self._tool_error(f"No memory manager available for tool '{tool_name}'")
        return self._manager.handle_tool_call(tool_name, args, **kwargs)

    def on_turn_start(self, turn_number: int, message: str, **kwargs) -> None:
        """通知所有插件新一轮对话开始。"""
        if self._manager is None:
            return
        self._manager.on_turn_start(turn_number, message, **kwargs)

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        """通知所有插件会话结束。"""
        if self._manager is None:
            return
        self._manager.on_session_end(messages)

    def on_memory_write(self, action: str, target: str, content: str,
                        metadata: Optional[Dict[str, Any]] = None) -> None:
        """通知外部插件：内置记忆工具发生了写入。"""
        if self._manager is None:
            return
        self._manager.on_memory_write(action, target, content, metadata=metadata)

    @staticmethod
    def _tool_error(message: str) -> str:
        """生成工具错误返回 JSON。"""
        import json
        return json.dumps({"success": False, "error": message}, ensure_ascii=False)

    # ================================================================
    # 旧版 API（完全兼容）
    # ================================================================

    def save_session(self, messages: list[dict], session_id: str = "default") -> str:
        """保存会话（旧版）"""
        return self._legacy.save_session(messages, session_id)

    def load_session(self, session_id: str = "default") -> list[dict]:
        """加载会话（旧版）"""
        return self._legacy.load_session(session_id)

    def list_sessions(self) -> list[dict]:
        """列出会话（旧版）"""
        return self._legacy.list_sessions()

    def delete_session(self, session_id: str) -> bool:
        """删除会话（旧版）"""
        return self._legacy.delete_session(session_id)

    def rename_session(self, session_id: str, new_title: str) -> bool:
        """重命名会话（旧版）"""
        return self._legacy.rename_session(session_id, new_title)

    def toggle_pin_session(self, session_id: str) -> bool:
        """置顶/取消置顶会话（旧版）。返回 True=已置顶, False=已取消"""
        return self._legacy.toggle_pin_session(session_id)

    def get_sessions_dir(self) -> str:
        """返回会话文件的存储目录路径"""
        return self._legacy.sessions_dir

    def read_memory(self, name: str) -> str:
        """读取记忆（旧版）"""
        return self._legacy.read_memory(name)

    def write_memory(self, name: str, content: str) -> str:
        """写入记忆（旧版）"""
        return self._legacy.write_memory(name, content)

    def append_memory(self, name: str, content: str) -> str:
        """追加记忆（旧版）"""
        return self._legacy.append_memory(name, content)

    def list_memories(self) -> list[str]:
        """列出记忆（旧版）"""
        return self._legacy.list_memories()

    def save_fact(self, fact: str):
        """保存事实（旧版）"""
        # 同时写入智能记忆的检索画像
        self._smart.update_retrieval_profile({
            "stable_domains": [fact[:50]]  # 提取关键信息
        })
        return self._legacy.save_fact(fact)

    def get_facts(self) -> str:
        """获取事实（旧版）"""
        return self._legacy.get_facts()

    def save_task(self, task: str):
        """保存任务（旧版）"""
        return self._legacy.save_task(task)

    def get_tasks(self) -> str:
        """获取任务（旧版）"""
        return self._legacy.get_tasks()

    # ================================================================
    # 新增智能记忆 API
    # ================================================================

    @property
    def smart(self) -> SmartMemory:
        """访问底层 SmartMemory 实例"""
        return self._smart

    def learn_from_interaction(self, user_message: str, assistant_response: str,
                               feedback: Optional[str] = None) -> Dict:
        """
        从交互中学习

        Args:
            user_message: 用户消息
            assistant_response: 助手回复
            feedback: 用户反馈（"positive"/"negative"/None）
        """
        # 更新学习特征（简化实现）
        self._smart.update_learned_features({
            "vocabulary": {
                "high_freq_words": self._extract_keywords(user_message),
                "updated_at": __import__('datetime').datetime.now().isoformat()
            }
        })

        # 记录反馈
        if feedback == "positive":
            self._smart.record_accepted_suggestion(
                assistant_response[:100],
                "用户正面反馈"
            )
        elif feedback == "negative":
            self._smart.record_rejected_suggestion(
                assistant_response[:100],
                "用户负面反馈"
            )

        return {"success": True, "learned": True}

    def _extract_keywords(self, text: str) -> Dict[str, int]:
        """提取关键词（简化实现）"""
        # 实际应用中可以使用更复杂的NLP
        if text is None:
            text = ''
        words = text.lower().split()
        freq = {}
        for word in words:
            if len(word) > 2:
                freq[word] = freq.get(word, 0) + 1
        return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10])

    def get_personalized_context(self) -> str:
        """获取个性化上下文（用于注入到LLM提示中）"""
        profile = self._smart.get_user_profile()
        preferences = self._smart._load_preference_profile()

        context_parts = []

        # 用户偏好
        if preferences.get("writing_style"):
            style = preferences["writing_style"]
            context_parts.append(f"用户偏好语气: {style.get('tone', 'professional')}")
            context_parts.append(f"正式程度: {style.get('formality', 'medium')}")

        # 学习状态
        if preferences.get("learning_state") == "frozen":
            context_parts.append("[注意：学习系统当前已冻结]")

        # 检索画像
        retrieval = self._smart.get_retrieval_profile()
        if retrieval.get("stable_domains"):
            context_parts.append(f"稳定领域: {', '.join(retrieval['stable_domains'][:5])}")

        return "\n".join(context_parts) if context_parts else ""

    def should_adapt_content(self, content_type: str = "general") -> bool:
        """检查是否应该对内容进行个性化适配"""
        # 检查保护内容类型
        if content_type in SmartMemory.BOUNDARIES["protected_content_types"]:
            return False

        # 检查是否冻结
        profile = self._smart._load_preference_profile()
        if profile.get("learning_state") == "frozen":
            return False

        # 检查是否启用
        return self._smart.options["enabled"]

    def get_stats(self) -> Dict:
        """获取完整统计信息"""
        return {
            "legacy": {
                "sessions": len(self._legacy.list_sessions()),
                "memories": len(self._legacy.list_memories())
            },
            "smart": self._smart.get_stats()
        }

    # ================================================================
    # 核心持久化记忆代理（IqraMemory SQLite）
    # ================================================================

    @property
    def core_memory(self):
        """获取底层 IqraMemory 实例（供 enhanced_core 降级场景使用）"""
        return self._core_memory

    def add(self, category: str, content: str, priority: int = 5) -> Optional[str]:
        if self._core_memory:
            return self._core_memory.add(category, content, priority)
        return None

    def replace(self, entry_id: str, new_content: str) -> bool:
        if self._core_memory:
            return self._core_memory.replace(entry_id, new_content)
        return False

    def update(self, entry_id: str, content: str) -> bool:
        if self._core_memory:
            return self._core_memory.update(entry_id, content)
        return False

    def get(self, entry_id: str) -> Optional[Dict]:
        if self._core_memory:
            return self._core_memory.get(entry_id)
        return None

    def remove(self, entry_id: str) -> bool:
        if self._core_memory:
            return self._core_memory.remove(entry_id)
        return False

    def search(self, category: str = None, keyword: str = None, limit: int = 20) -> List[Dict]:
        if self._core_memory:
            return self._core_memory.search(category, keyword, limit)
        return []

    # ── SmartMemory 代理（供 EnhancedMemory 兼容）──

    def query(self, query_obj) -> List[Dict]:
        """MemoryQuery 兼容代理 → SmartMemory"""
        if self._smart:
            try:
                query_str = getattr(query_obj, 'query', str(query_obj))
                memory_type = getattr(query_obj, 'memory_type', 'all')
                profile = self._smart.get_user_profile()
                results = []
                if memory_type in ('all', 'preferences') and 'preferences' in profile:
                    results.append({'type': 'preferences', 'data': profile['preferences']})
                if memory_type in ('all', 'important') and hasattr(self._smart, 'get_important_memories'):
                    mems = self._smart.get_important_memories()
                    if mems:
                        results.extend([{'type': 'important', 'data': m} for m in mems])
                return results
            except Exception:
                return []
        return []

    def add_dialogue(self, role: str, content: str) -> None:
        """记录对话到智能记忆"""
        if self._smart:
            try:
                if role == 'user' and content:
                    self._smart.update_retrieval_profile({'last_query': content})
            except Exception:
                pass

    def close(self) -> None:
        """关闭智能记忆（无实际操作）"""
        pass

    # ================================================================
    # 语义搜索索引持久化
    # ================================================================

    def get_semantic_index(self, index_name: str = "default") -> Optional[bytes]:
        """
        从持久化存储中加载语义搜索索引二进制数据。

        Args:
            index_name: 索引名称（默认 "default"）

        Returns:
            索引的二进制数据（FAISS .index 格式），若不存在则返回 None
        """
        if not self._core_memory:
            return None
        try:
            import base64
            results = self._core_memory.search(
                category="semantic_search/index",
                keyword=index_name,
                limit=1,
            )
            if results:
                # results 可能是 list[dict] 或 list[str]，按内容取
                raw = results[0].get("content") if isinstance(results[0], dict) else str(results[0])
                if raw:
                    return base64.b64decode(raw)
        except Exception as e:
            logger.debug("Failed to load semantic index '%s': %s", index_name, e)
        return None

    def set_semantic_index(self, index_data: bytes, index_name: str = "default") -> bool:
        """
        将语义搜索索引持久化到存储。

        Args:
            index_data: FAISS 索引的二进制数据
            index_name: 索引名称（默认 "default"）

        Returns:
            是否成功
        """
        if not self._core_memory:
            return False
        try:
            import base64
            encoded = base64.b64encode(index_data).decode("ascii")
            self._core_memory.add(
                category="semantic_search/index",
                content=encoded,
                metadata=json.dumps({"name": index_name}),
            )
            logger.debug("Semantic index '%s' saved (%d bytes)", index_name, len(index_data))
            return True
        except Exception as e:
            logger.debug("Failed to save semantic index '%s': %s", index_name, e)
            return False

    # ================================================================
    # 生命周期
    # ================================================================

    def shutdown(self) -> None:
        """关闭所有记忆子系统。"""
        if self._manager is not None:
            try:
                self._manager.shutdown_all()
            except Exception as e:
                logger.warning("MemoryManager shutdown failed: %s", e)
        # MemoryStore 和 SmartMemory 无显式 shutdown 需要
        logger.info("SmartMemoryStore shutdown complete")


# 便捷函数
def create_memory_store(base_dir: Optional[str] = None) -> SmartMemoryStore:
    """创建增强版记忆存储实例"""
    return SmartMemoryStore(base_dir)

```
