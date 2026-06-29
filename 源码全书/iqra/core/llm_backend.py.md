# `iqra/core/llm_backend.py`

> 路径：`iqra/core/llm_backend.py` | 行数：428


---


```python
"""
Iqra LLM Backend - 多供应商统一接口
Universal multi-provider LLM interface with function calling.

内置模板: DeepSeek(V3/R1) | OpenAI | 通义千问 | 智谱GLM | Moonshot |
          百度千帆 | 讯飞星火 | Groq | Together AI | OpenRouter | SiliconFlow |
          Mistral | Perplexity | Fireworks | Cohere | MiniMax | 阶跃星辰 |
          Ollama | LM Studio | vLLM | llama.cpp | 自定义

特性:
- 统一 chat() / chat_stream() 接口
- 原生 Function Calling 支持
- 自动供应商检测
- 本地模型 SSL 自签证书兼容
- 纯标准库实现, 零额外依赖
"""

import json
import urllib.request
import urllib.error
import ssl
import os
from typing import Iterator, Optional

from ._backend_models import ProviderConfig, ToolDefinition, ToolCall, LLMResponse, TokenSaverMode, optimize_messages
from ._base_backend import BaseLLMBackend
from ._backend_providers import PROVIDER_TEMPLATES
from ._backend_utils import list_all_providers, get_available_models, batch_scan_platforms
from ._backend_factory import BackendFactory
from ._backend_convenience import create_backend


# ═══════════════════════════════════════════
# OpenAI 兼容后端 (覆盖 95% 场景)
# ═══════════════════════════════════════════

class OpenAICompatibleBackend(BaseLLMBackend):
    """
    通用 OpenAI 兼容后端。

    支持: OpenAI, DeepSeek, Ollama, vLLM, LM Studio,
          通义千问, 智谱GLM, Moonshot, 百度文心, 讯飞星火,
          Groq, Together AI, OpenRouter, SiliconFlow, 任意自定义端点
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        # SSL: 本地模型自签证书 / 阿里云百炼 hostname mismatch
        _insecure_hosts = ("localhost", "127.0.0.1", "0.0.0.0")  # maas.aliyuncs.com 已移除
        if any(h in config.base_url for h in _insecure_hosts):
            self._ssl_context = ssl._create_unverified_context()
        else:
            self._ssl_context = ssl.create_default_context()

    def supports_tools(self) -> bool:
        return True

    # ── URL 构造 ──

    def _build_url(self) -> str:
        base = self.config.base_url.rstrip("/")
        # 自动补全 /v1 前缀
        if "/v1" not in base:
            base += "/v1"
        return f"{base}/chat/completions"

    # ── 请求构造 ──

    def _build_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        headers.update(self.config.extra_headers)
        return headers

    def _sanitize_messages(self, messages: list[dict]) -> list[dict]:
        """清洗消息列表，确保 content 字段不为 None/null。
        
        Ollama 及部分 OpenAI 兼容端点拒绝 content=null 的请求体（400），
        但 ChatEngine 在 tool_calls 场景下会将 assistant 消息的 content 置为 None。
        此处将 None 转为空字符串 ""，保留其他字段不变。
        """
        cleaned = []
        for m in messages:
            msg = dict(m)
            if msg.get("content") is None:
                msg["content"] = ""
            cleaned.append(msg)
        return cleaned

    def _build_payload(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        stream: bool = False,
        tool_choice: Optional[str] = None,
    ) -> dict:
        payload = {
            "model": self.config.model,
            "messages": self._sanitize_messages(messages),
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": stream,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice or "auto"
        return payload

    # ── HTTP 请求 ──

    def _make_request(self, payload: dict, timeout: int = 600) -> dict:
        """发送 HTTP POST 请求并返回解析后的 JSON"""
        url = self._build_url()
        headers = self._build_headers()
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, context=self._ssl_context, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            
            # 检测 token 用尽错误
            is_no_token = self._check_no_token_error(e.code, error_body)
            if is_no_token:
                # 标记模型为失效
                try:
                    from iqra.core.model_status import mark_model_no_token
                    mark_model_no_token(self.config.model, self.config.name)
                except ImportError:
                    pass
                
                raise RuntimeError(
                    f"[{self.config.name}] Token 用尽或额度不足: {error_body[:300]}"
                )
            
            raise RuntimeError(
                f"[{self.config.name}] API error {e.code}: {error_body[:500]}"
            )
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"[{self.config.name}] 连接失败: {e.reason}\n"
                f"请检查: 1) 网络连接 2) base_url 是否正确 ({self.config.base_url})"
            )
        except Exception as e:
            raise RuntimeError(f"[{self.config.name}] 请求异常: {e}")
    
    def _check_no_token_error(self, code: int, error_body: str) -> bool:
        """
        检查是否为 token 用尽错误
        
        Args:
            code: HTTP 状态码
            error_body: 错误响应体
            
        Returns:
            True 表示 token 用尽
        """
        # HTTP 400 = 参数错误（如 max_tokens 超限），绝对不是额度问题
        if code == 400:
            return False
        
        # 检查状态码
        if code == 401:  # Unauthorized - 通常表示 token 失效
            return True
        if code == 403:  # Forbidden - 可能表示额度不足
            return True
        if code == 429:  # Too Many Requests - 速率限制
            return True
        
        # 检查错误消息中的关键字
        error_lower = error_body.lower()
        token_keywords = [
            "token",
            "quota",
            "额度",
            "余额不足",
            "credit",
            "insufficient",
            "exceed",
            "限制",
            "用尽",
        ]
        
        if any(kw in error_lower for kw in token_keywords):
            return True
        
        return False

    # ── 响应解析 ──

    def _parse_response(self, data: dict) -> LLMResponse:
        """解析 API JSON 响应 -> LLMResponse"""
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        finish_reason = choice.get("finish_reason", "stop")

        # 文本内容 (可能为空字符串)
        content = message.get("content") or None

        # 工具调用
        tool_calls = None
        raw_tool_calls = message.get("tool_calls", [])
        if raw_tool_calls:
            parsed = []
            for tc in raw_tool_calls:
                func = tc.get("function", {})
                try:
                    args = json.loads(func.get("arguments", "{}"))
                except (json.JSONDecodeError, TypeError):
                    args = {}
                parsed.append(ToolCall(
                    id=tc.get("id", ""),
                    name=func.get("name", ""),
                    arguments=args,
                ))
            if parsed:
                tool_calls = parsed

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            model=data.get("model", self.config.model),
            usage=data.get("usage", {}),
            is_tool_call=finish_reason == "tool_calls" or bool(tool_calls),
        )

    # ── 公开接口 ──

    def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        token_saver_mode: str = "balanced",  # Token 节约模式
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        """聊天接口，可选 Token 优化和强制工具调用
        
        对本地模型（如 Ollama）使用内部流式读取，防止大模型（35b+）生成长链推理时
        因 ollama 全量缓存导致 socket 超时。
        """
        is_local = self._is_local_provider()
        
        # 应用 Token 优化
        if token_saver_mode != "disabled":
            messages = optimize_messages(messages, mode=token_saver_mode)
        
        if is_local and not tools:
            # 本地模型走内部流式，逐 chunk 消费防止 socket timeout
            return self._chat_stream_accumulate(
                messages, tools, token_saver_mode, tool_choice
            )
        
        payload = self._build_payload(messages, tools, stream=False, tool_choice=tool_choice)
        data = self._make_request(payload)
        return self._parse_response(data)
    
    def _is_local_provider(self) -> bool:
        """检测是否为本地供应商（Ollama/localhost）"""
        try:
            return (
                self.config.name == "llama.cpp"
                or "ollama" in self.config.provider_type.lower()
                or "llama.cpp" in self.config.name.lower()
                or "localhost" in self.config.base_url
                or "127.0.0.1" in self.config.base_url
            )
        except Exception:
            return False
    
    def _chat_stream_accumulate(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        token_saver_mode: str = "balanced",
        tool_choice: Optional[str] = None,
    ) -> LLMResponse:
        """内部流式读取（逐 chunk 消费防止 socket timeout），
        聚合完整响应后以 LLMResponse 返回。"""
        import json as _json
        
        if token_saver_mode != "disabled":
            messages = optimize_messages(messages, mode=token_saver_mode)
        
        payload = self._build_payload(messages, tools, stream=True, tool_choice=tool_choice)
        url = self._build_url()
        headers = self._build_headers()
        data_bytes = _json.dumps(payload, ensure_ascii=False).encode("utf-8")
        
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
        
        accumulated_content = ""
        accumulated_reasoning = ""
        model_name = ""
        usage = {}
        finish_reason = "stop"
        tool_calls_raw = []
        
        try:
            with urllib.request.urlopen(req, context=self._ssl_context, timeout=600) as resp:
                for line_bytes in resp:
                    line = line_bytes.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = _json.loads(data_str)
                    except _json.JSONDecodeError:
                        continue
                    
                    choice = chunk.get("choices", [{}])[0]
                    delta = choice.get("delta", {})
                    if "content" in delta and delta["content"]:
                        accumulated_content += delta["content"]
                    if "reasoning_content" in delta and delta["reasoning_content"]:
                        accumulated_reasoning += delta["reasoning_content"]
                    if "tool_calls" in delta:
                        tool_calls_raw = delta["tool_calls"]
                    if choice.get("finish_reason"):
                        finish_reason = choice.get("finish_reason", "stop")
                    if chunk.get("model"):
                        model_name = chunk.get("model", "")
                    if chunk.get("usage"):
                        usage = chunk.get("usage", {})
        
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"[{self.config.name}] API error {e.code}: {error_body[:500]}"
            )
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"[{self.config.name}] 连接失败: {e.reason}\n"
                f"请检查: 1) 网络连接 2) base_url 是否正确 ({self.config.base_url})"
            )
        except Exception as e:
            raise RuntimeError(f"[{self.config.name}] 请求异常: {e}")
        
        # 构造返回
        parsed_tool_calls = None
        if tool_calls_raw:
            parsed = []
            for tc in tool_calls_raw:
                func = tc.get("function", {})
                try:
                    args = _json.loads(func.get("arguments", "{}"))
                except (_json.JSONDecodeError, TypeError):
                    args = {}
                parsed.append(ToolCall(
                    id=tc.get("id", ""),
                    name=func.get("name", ""),
                    arguments=args,
                ))
            if parsed:
                parsed_tool_calls = parsed
        
        return LLMResponse(
            content=accumulated_content or None,
            reasoning=accumulated_reasoning or None,
            tool_calls=parsed_tool_calls,
            finish_reason=finish_reason,
            model=model_name or self.config.model,
            usage=usage,
            is_tool_call=finish_reason == "tool_calls" or bool(parsed_tool_calls),
        )

    def chat_stream(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        token_saver_mode: str = "balanced",  # Token 节约模式
        tool_choice: Optional[str] = None,
    ) -> Iterator[LLMResponse]:
        """SSE 流式响应。工具调用时不流式, 降级为普通请求。"""
        
        # 如果带有工具, 工具调用结果通常不流式
        if tools:
            yield self.chat(messages, tools, token_saver_mode, tool_choice=tool_choice)
            return
        
        # 应用 Token 优化
        if token_saver_mode != "disabled":
            messages = optimize_messages(messages, mode=token_saver_mode)
        
        payload = self._build_payload(messages, tools=None, stream=True)
        url = self._build_url()
        headers = self._build_headers()
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        accumulated = ""
        try:
            with urllib.request.urlopen(req, context=self._ssl_context, timeout=600) as resp:
                for line_bytes in resp:
                    line = line_bytes.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]  # 去掉 "data: " 前缀
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    if "content" in delta and delta["content"]:
                        accumulated += delta["content"]
                        yield LLMResponse(
                            content=delta["content"],
                            model=chunk.get("model", ""),
                        )

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            yield LLMResponse(
                content=f"[Error {e.code}: {error_body[:300]}]"
            )
        except Exception as e:
            yield LLMResponse(content=f"[连接错误: {e}]")

```
