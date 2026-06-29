# `iqra/core/_base_backend.py`

> 路径：`iqra/core/_base_backend.py` | 行数：50


---


```python
"""
Iqra LLM Backend — 抽象基类
"""
from abc import ABC, abstractmethod
from typing import Iterator, Optional

from ._backend_models import ProviderConfig, LLMResponse


class BaseLLMBackend(ABC):
    """所有 LLM 后端的抽象基类"""

    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        """
        发送消息并获取响应。

        Args:
            messages: [{"role": "user", "content": "..."}, ...]
            tools: OpenAI 格式的工具定义列表
            tool_choice: "auto" | "required" | "none" - 是否强制使用工具

        Returns:
            LLMResponse (可能包含文本或 tool_calls)
        """
        ...

    def chat_stream(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[str] = None,
    ) -> Iterator[LLMResponse]:
        """
        流式版本。默认降级为非流式。
        子类可覆盖实现真正的 SSE 流式。
        """
        yield self.chat(messages, tools, tool_choice=tool_choice)

    def supports_tools(self) -> bool:
        """是否支持原生 function calling"""
        return False

```
