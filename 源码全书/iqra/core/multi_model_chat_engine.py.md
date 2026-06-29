# `iqra/core/multi_model_chat_engine.py`

> 路径：`iqra/core/multi_model_chat_engine.py` | 行数：239


---


```python
# -*- coding: utf-8 -*-
"""
MultiModelChatEngine — 多模型 ChatEngine 适配层

对 ChatWindow 完全透明，暴露与 ChatEngine 完全相同的接口。
内部使用 MultiModelRouter 根据消息内容自动选择后端。

用法:
    from iqra.core.chat_engine import ChatEngine
    from iqra.core.multi_model import MultiModelRouter

    router = MultiModelRouter()
    router.register_role("fast", fast_backend, priority=0, fallback_role="deep")
    router.register_role("deep", deep_backend, priority=10)
    router.register_role("reasoning", reasoning_backend, priority=5, fallback_role="deep")

    engine = MultiModelChatEngine(
        router=router,
        backend=primary_backend,  # 用作默认/单模型模式
        registry=tool_registry,
        system_prompt=system_prompt,
        skill_loader=skill_loader,
        memory_store=memory_store,
    )

    # 使用方式与 ChatEngine 完全一致
    response = engine.chat("帮我写一个排序算法")
    # 自动路由到 deep 模型
"""

from typing import Optional, Iterator
from PyQt5.QtCore import QObject, pyqtSignal
from .llm_backend import BaseLLMBackend
from .multi_model import MultiModelRouter
from .chat_engine import ChatEngine
from .iqra_logging import logger


class MultiModelChatEngine(QObject):
    """
    多模型 ChatEngine 包装器

    对外暴露 ChatEngine 的核心接口（chat / chat_stream / reset / save / ...），
    内部通过 MultiModelRouter 根据任务类型动态切换后端。
    """

    on_tool_start = pyqtSignal(str, dict)
    on_tool_result = pyqtSignal(str, bool, str)

    # 新增信号
    on_model_switch = pyqtSignal(str, str)  # (task_type, model_name)

    def __init__(
        self,
        router: MultiModelRouter,
        backend: BaseLLMBackend,  # 默认后端（单模型模式或 fallback）
        registry=None,
        system_prompt: str = '',
        skill_loader=None,
        memory_store=None,
        auto_save: bool = True,
        session_id: str = 'default',
    ):
        super().__init__()
        self.router = router
        self._default_backend = backend
        self._registry = registry
        self._system_prompt = system_prompt
        self._skill_loader = skill_loader
        self._memory_store = memory_store
        self._auto_save = auto_save
        self._session_id = session_id

        # 多模型模式开关：只有当 router 注册了 ≥2 个角色时才启用
        self._multi_model_enabled = router.has_multi_model()

        # 内部 ChatEngine 实例（按需重建以切换后端）
        self._engine: Optional[ChatEngine] = None
        self._current_backend: Optional[BaseLLMBackend] = None
        self._current_task_type: str = "chat"

        # 创建初始引擎
        self._create_engine(self._default_backend)

    # ── 引擎管理 ──

    def _create_engine(self, backend: BaseLLMBackend) -> None:
        """创建新的 ChatEngine 实例（切换后端时调用）"""
        # 保存旧引擎的消息历史
        old_messages = []
        if self._engine is not None:
            old_messages = self._engine.get_history()
            # 断开旧信号
            try:
                self._engine.on_tool_start.disconnect()
                self._engine.on_tool_result.disconnect()
            except Exception:
                pass

        self._engine = ChatEngine(
            backend=backend,
            registry=self._registry,
            system_prompt=self._system_prompt,
            skill_loader=self._skill_loader,
            memory_store=self._memory_store,
            auto_save=self._auto_save,
            session_id=self._session_id,
        )

        # 转发信号
        self._engine.on_tool_start.connect(self.on_tool_start.emit)
        self._engine.on_tool_result.connect(self.on_tool_result.emit)

        # 恢复消息历史（如果存在）
        if old_messages:
            self._engine.messages = old_messages
            self._engine._trim_context()

        self._current_backend = backend

    def _route_and_switch(self, message: str) -> str:
        """
        根据消息路由到合适的后端，必要时切换引擎

        Returns:
            task_type 名称
        """
        if not self._multi_model_enabled:
            return "chat"

        try:
            backend, task_type = self.router.route(message)
        except RuntimeError:
            logger.warning("多模型路由失败，使用默认后端")
            return "chat"

        if backend is not self._current_backend:
            model_name = f"{backend.config.name} ({backend.config.model})"
            logger.info(f"模型切换: {self._current_task_type} → {task_type} ({model_name})")

            self._current_task_type = task_type
            self._create_engine(backend)
            self.on_model_switch.emit(task_type, model_name)
        else:
            self._current_task_type = task_type

        return task_type

    # ── 公开接口（与 ChatEngine 一致）──

    @property
    def backend(self):
        """兼容旧代码：返回当前活跃后端"""
        return self._current_backend or self._default_backend

    @property
    def messages(self):
        return self._engine.messages if self._engine else []

    @messages.setter
    def messages(self, value):
        if self._engine:
            self._engine.messages = value

    @property
    def multi_model_enabled(self) -> bool:
        return self._multi_model_enabled

    @property
    def current_task_type(self) -> str:
        return self._current_task_type

    @property
    def current_model_name(self) -> str:
        if self._current_backend:
            return f"{self._current_backend.config.name} ({self._current_backend.config.model})"
        return "未连接"

    def chat(self, user_message: str) -> str:
        self._route_and_switch(user_message)
        return self._engine.chat(user_message)

    def chat_stream(self, user_message: str) -> Iterator[str]:
        self._route_and_switch(user_message)
        return self._engine.chat_stream(user_message)

    def reset(self) -> None:
        if self._engine:
            self._engine.reset()
        self._current_task_type = "chat"

    def save(self) -> bool:
        return self._engine.save() if self._engine else False

    def get_history(self) -> list:
        return self._engine.get_history() if self._engine else []

    def message_count(self) -> int:
        return self._engine.message_count() if self._engine else 0

    def inject_context(self, text: str) -> None:
        if self._engine:
            self._engine.inject_context(text)

    def inject_skill(self, skill_name: str) -> bool:
        return self._engine.inject_skill(skill_name) if self._engine else False

    def refresh_skills(self) -> int:
        return self._engine.refresh_skills() if self._engine else 0

    def inject_relevant_skills(self, user_query: str, max_count: int = 5) -> int:
        return self._engine.inject_relevant_skills(user_query, max_count) if self._engine else 0

    def initialize_session(self) -> None:
        if self._engine:
            self._engine.initialize_session()

    # ── 多模型管理 ──

    def set_multi_model_enabled(self, enabled: bool) -> None:
        """启用/禁用多模型模式"""
        if enabled and not self.router.has_multi_model():
            logger.warning("无法启用多模型：需要至少注册 2 个模型角色")
            return
        self._multi_model_enabled = enabled
        if not enabled and self._current_backend is not self._default_backend:
            self._create_engine(self._default_backend)

    def get_active_model_display(self) -> str:
        """用于 UI 显示的当前模型信息"""
        if self._multi_model_enabled:
            task_names = {
                "chat": "聊天", "code": "编程",
                "analysis": "分析", "reasoning": "推理",
                "tools": "工具", "vision": "视觉",
            }
            task_cn = task_names.get(self._current_task_type, self._current_task_type)
            return f"多模型 · {task_cn} · {self.current_model_name}"
        return self.current_model_name

```
