# `core/llm_client.py`

> 路径：`core/llm_client.py` | 行数：246


---


```python
"""
LLM 客户端 — 统一的本地/云端大模型接口
支持：Ollama(本地) / OpenAI / DeepSeek / Claude / 通义千问 / 自定义OpenAI兼容
"""
import traceback
import json
from typing import Optional, AsyncIterator, Dict, List
from dataclasses import dataclass, field

from deps.install_deps import ensure
ensure("httpx")
import httpx


@dataclass
class ModelConfig:
    provider: str = "llama_proxy"        # llama_proxy / openai / deepseek / claude / qwen / custom
    api_key: str = ""
    base_url: str = "http://localhost:8080"
    model_name: str = "qwen3.6-35b-iq2m"
    temperature: float = 0.7
    max_tokens: int = 2048
    extra_headers: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ModelConfig":
        return cls(**{k: d.get(k, v) for k, v in cls.__dataclass_fields__.items()
                       if k in d})


# ── 预置提供商 ──
PROVIDERS = {
    "llama_proxy": {
        "name": "llama.cpp (本地)",
        "base_url": "http://localhost:8080",
        "api_path": "/v1/chat/completions",
        "needs_key": False,
        "needs_model_list": True,
        "list_path": "/v1/models",
        "description": "本地运行，数据不出设备",
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com",
        "api_path": "/v1/chat/completions",
        "needs_key": True,
        "needs_model_list": False,
        "description": "GPT-4o / GPT-4o-mini",
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "api_path": "/v1/chat/completions",
        "needs_key": True,
        "needs_model_list": False,
        "description": "DeepSeek-V3 / R1",
    },
    "claude": {
        "name": "Anthropic Claude",
        "base_url": "https://api.anthropic.com",
        "api_path": "/v1/messages",
        "needs_key": True,
        "needs_model_list": False,
        "description": "Claude 3.5 Sonnet / Opus",
    },
    "qwen": {
        "name": "通义千问",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode",
        "api_path": "/v1/chat/completions",
        "needs_key": True,
        "needs_model_list": False,
        "description": "Qwen-Max / Qwen-Plus",
    },
    "custom": {
        "name": "自定义 OpenAI 兼容",
        "base_url": "http://localhost:8080",
        "api_path": "/v1/chat/completions",
        "needs_key": True,
        "needs_model_list": False,
        "description": "兼容 OpenAI API 格式的任意服务",
    },
}


class LLMClient:
    """统一大模型调用客户端"""

    def __init__(self, config: ModelConfig):
        self.config = config
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                p = self.config.provider
                if p == "claude":
                    headers["x-api-key"] = self.config.api_key
                    headers["anthropic-version"] = "2023-06-01"
                elif p == "qwen":
                    headers["Authorization"] = f"Bearer {self.config.api_key}"
                else:
                    headers["Authorization"] = f"Bearer {self.config.api_key}"

            if self.config.extra_headers:
                headers.update(self.config.extra_headers)

            self._client = httpx.Client(
                base_url=self.config.base_url,
                headers=headers,
                timeout=60.0,
            )
        return self._client

    def test_connection(self) -> dict:
        """测试连接并返回结果"""
        p = self.config.provider
        info = PROVIDERS.get(p, PROVIDERS["custom"])

        try:
            if info.get("needs_model_list") and p == "ollama":
                # Ollama: 拉取模型列表来验证连接
                resp = self.client.get(info["list_path"])
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return {"ok": True, "models": models, "message": f"已连接，找到 {len(models)} 个模型"}
                else:
                    return {"ok": False, "message": f"Ollama 返回 {resp.status_code}"}

            # 通用：发一个空测试请求
            path = info["api_path"]
            if p == "claude":
                body = {
                    "model": self.config.model_name,
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "hi"}],
                }
            else:
                body = {
                    "model": self.config.model_name,
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "hi"}],
                }

            resp = self.client.post(path, json=body)
            if resp.status_code == 200:
                return {"ok": True, "message": "连接成功"}
            elif resp.status_code == 401:
                return {"ok": False, "message": "API Key 无效或未授权"}
            elif resp.status_code == 404:
                return {"ok": False, "message": f"模型 {self.config.model_name} 不存在"}
            else:
                error_body = resp.text[:200]
                return {"ok": False, "message": f"错误 {resp.status_code}: {error_body}"}

        except httpx.ConnectError:
            return {"ok": False, "message": "无法连接到服务，请检查地址和网络"}
        except httpx.TimeoutException:
            return {"ok": False, "message": "连接超时"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def chat(self, messages: List[dict], stream: bool = False) -> str:
        """发送对话请求"""
        p = self.config.provider
        info = PROVIDERS.get(p, PROVIDERS["custom"])
        path = info["api_path"]

        if p == "claude":
            system_msg = ""
            user_msgs = []
            for m in messages:
                if m["role"] == "system":
                    system_msg = m["content"]
                else:
                    user_msgs.append(m)
            body = {
                "model": self.config.model_name,
                "max_tokens": self.config.max_tokens,
                "messages": user_msgs,
            }
            if system_msg:
                body["system"] = system_msg
        else:
            body = {
                "model": self.config.model_name,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "messages": messages,
            }

        resp = self.client.post(path, json=body, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        # 提取响应文本
        if p == "claude":
            return data["content"][0]["text"]
        else:
            return data["choices"][0]["message"]["content"]

    def fetch_ollama_models(self) -> List[str]:
        """获取 llama.cpp 已加载的模型列表"""
        try:
            resp = self.client.get("/v1/models")
            if resp.status_code == 200:
                models = [m["id"] for m in resp.json().get("data", [])]
                return models
        except Exception:
            traceback.print_exc()
        return []

    @staticmethod
    def discover_ollama_models() -> List[dict]:
        """静态方法：自动发现本地 llama.cpp 模型，返回含名称/大小的列表"""
        try:
            import urllib.request
            resp = urllib.request.urlopen("http://localhost:8080/v1/models", timeout=3)
            raw = json.loads(resp.read())
            result = []
            for m in raw.get("data", []):
                entry = {
                    "name": m["id"],
                    "size_mb": 0,
                    "param_size": "?",
                    "context_length": 0,
                    "capabilities": [],
                    "modified": "",
                }
                result.append(entry)
            return result
        except Exception:
            traceback.print_exc()
        return []
```
