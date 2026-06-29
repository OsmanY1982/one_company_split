"""
LLM Backend - 统一的 LLM 后端抽象层
支持 OpenAI 兼容 API（包括 Ollama、LM Studio 等本地模型）
"""
import json
import requests
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class ProviderConfig:
    """LLM 提供商配置"""
    name: str = "Ollama"
    provider_type: str = "openai_compatible"
    base_url: str = "http://localhost:8080/v1"
    model: str = "qwen2.5:7b"
    temperature: float = 0.7
    max_tokens: int = 4096
    api_key: Optional[str] = None


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: Optional[str] = None
    tool_calls: Optional[List["ToolCall"]] = None
    finish_reason: str = "stop"


@dataclass
class ToolCall:
    """工具调用"""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)


class OpenAICompatibleBackend:
    """OpenAI 兼容 API 后端"""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self._session = requests.Session()
        if config.api_key:
            self._session.headers["Authorization"] = f"Bearer {config.api_key}"
        self._session.headers["Content-Type"] = "application/json"

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
    ) -> LLMResponse:
        """发送聊天请求到 LLM"""
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": stream,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            resp = self._session.post(url, json=payload, timeout=600)
            resp.raise_for_status()
            data = resp.json()

            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            content = message.get("content")
            raw_tool_calls = message.get("tool_calls", [])

            # 解析工具调用
            tool_calls = None
            if raw_tool_calls:
                tool_calls = []
                for tc in raw_tool_calls:
                    func = tc.get("function", {})
                    try:
                        args = json.loads(func.get("arguments", "{}"))
                    except json.JSONDecodeError:
                        args = {}
                    tool_calls.append(
                        ToolCall(
                            id=tc.get("id", ""),
                            name=func.get("name", ""),
                            arguments=args,
                        )
                    )

            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                finish_reason=choice.get("finish_reason", "stop"),
            )

        except requests.exceptions.ConnectionError:
            return LLMResponse(
                content=f"[连接错误] 无法连接到 {self.config.name} ({self.config.base_url})，请确认服务已启动。",
                finish_reason="error",
            )
        except requests.exceptions.Timeout:
            return LLMResponse(
                content=f"[超时] {self.config.name} 请求超时，请检查网络或降低 max_tokens。",
                finish_reason="error",
            )
        except Exception as e:
            return LLMResponse(
                content=f"[错误] {self.config.name} 请求失败：{e}",
                finish_reason="error",
            )

    def health_check(self) -> bool:
        """检查服务是否可用"""
        try:
            url = f"{self.config.base_url.rstrip('/')}/models"
            resp = self._session.get(url, timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
