# `iqra/core/_backend_models.py`

> 路径：`iqra/core/_backend_models.py` | 行数：97


---


```python
"""
Iqra LLM Backend — 数据模型

ProviderConfig / ToolDefinition / ToolCall / LLMResponse
"""
from dataclasses import dataclass, field
from typing import Optional


# Token 优化系统
try:
    from iqra.core.token_optimizer import TokenSaverMode, optimize_messages
except ImportError:
    class TokenSaverMode:
        def __init__(self, mode="balanced"):
            self.mode = mode

        def optimize(self, messages):
            return messages

    def optimize_messages(messages, mode="balanced"):
        return messages


@dataclass
class ProviderConfig:
    """LLM 供应商配置"""
    name: str                        # 显示名称
    provider_type: str               # "openai_compatible" | "anthropic" | "google"
    base_url: str = ""               # API 端点
    api_key: str = ""                # API Key (本地模型可为空)
    model: str = ""                  # 默认模型名
    temperature: float = 0.7
    max_tokens: int = 262144
    extra_headers: dict = field(default_factory=dict)
    description: str = ""            # 描述文字
    available_models: list = field(default_factory=list)  # 已知模型列表 (UI 下拉预填)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "provider_type": self.provider_type,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "extra_headers": self.extra_headers,
            "description": self.description,
            "available_models": self.available_models,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProviderConfig":
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in valid_keys})


@dataclass
class ToolDefinition:
    """工具函数定义"""
    name: str                        # 函数名
    description: str                 # 功能描述
    parameters: dict                 # JSON Schema 参数定义
    handler: Optional[callable] = None  # 实际执行的 Python 函数
    category: str = ""               # 工具分类（可选）

    def to_openai_schema(self) -> dict:
        """转为 OpenAI function calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }


@dataclass
class ToolCall:
    """LLM 请求的工具调用"""
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: Optional[str] = None          # 文本内容
    reasoning: Optional[str] = None        # 推理内容（qwen3.6 等 reasoning 模型）
    tool_calls: Optional[list[ToolCall]] = None  # 工具调用列表
    finish_reason: str = "stop"
    model: str = ""
    usage: dict = field(default_factory=dict)
    is_tool_call: bool = False             # 是否为工具调用响应

```
