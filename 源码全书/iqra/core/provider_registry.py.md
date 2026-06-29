# `iqra/core/provider_registry.py`

> 路径：`iqra/core/provider_registry.py` | 行数：174


---


```python
"""
供应商注册表：PROVIDERS 字典 + ModelConfig 数据类。
从 core/llm_client.py 提取（原文件已废弃）。
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import os
import json
import httpx

class ModelConfig:
    provider: str = "custom"        # ollama / openai / deepseek / claude / qwen / custom
    api_key: str = ""
    base_url: str = "http://localhost:11434/v1"
    model_name: str = "qwen2.5:7b"
    temperature: float = 0.7
    max_tokens: int = 262144
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
    "ollama": {
        "name": "Ollama (本地)",
        "base_url": "http://localhost:11434",
        "api_path": "/v1/chat/completions",
        "needs_key": False,
        "needs_model_list": True,
        "list_path": "/api/tags",
        "description": "本地 Ollama 运行，数据不出设备",
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
        "base_url": "http://localhost:11434",
        "api_path": "/v1/chat/completions",
        "needs_key": True,
        "needs_model_list": False,
        "description": "兼容 OpenAI API 格式的任意服务",
    },
}


def discover_ollama_models() -> List[dict]:
    """自动发现本地 Ollama 模型"""
    try:
        import urllib.request
        resp = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        raw = json.loads(resp.read())
        result = []
        for m in raw.get("models", []):
            model_id = m.get("name", "")
            size_bytes = m.get("size", 0)
            size_mb = round(size_bytes / (1024 * 1024), 1) if size_bytes else 0
            entry = {
                "name": model_id,
                "display_name": model_id,
                "size_mb": size_mb,
                "param_size": m.get("details", {}).get("parameter_size", "?"),
                "context_length": 16384,
                "capabilities": [],
                "modified": m.get("modified_at", ""),
            }
            result.append(entry)
        return result
    except Exception:
        import traceback
        traceback.print_exc()
    return []


def test_provider_connection(config: ModelConfig) -> dict:
    """测试连接并返回结果。替代已删除的 LLMClient.test_connection。"""
    import httpx
    p = config.provider
    info = PROVIDERS.get(p, PROVIDERS["custom"])

    timeout = httpx.Timeout(15.0, connect=10.0)
    try:
        with httpx.Client(timeout=timeout) as client:
            if info.get("needs_model_list") and p == "ollama":
                resp = client.get(info["list_path"])
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return {"ok": True, "models": models, "message": f"已连接，找到 {len(models)} 个模型"}
                else:
                    return {"ok": False, "message": f"Ollama 返回 {resp.status_code}"}

            path = info["api_path"]
            body = {
                "model": config.model_name,
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "hi"}],
            }
            headers = {}
            if info.get("needs_key") and config.api_key:
                headers["Authorization"] = f"Bearer {config.api_key}"
            elif info.get("needs_key"):
                headers["Authorization"] = "Bearer no-key"

            url = config.base_url.rstrip("/").rstrip("/v1").rstrip("/chat/completions")
            if not url.endswith(path.rstrip("/")):
                url = url.rstrip("/") + "/" + path.lstrip("/")
            url = url.rstrip("/") + "/chat/completions"

            resp = client.post(url, json=body, headers=headers)
            if resp.status_code == 200:
                return {"ok": True, "message": "连接成功"}
            elif resp.status_code == 401:
                return {"ok": False, "message": "API Key 无效或未授权"}
            elif resp.status_code == 404:
                return {"ok": False, "message": f"模型 {config.model_name} 不存在"}
            else:
                error_body = resp.text[:200]
                return {"ok": False, "message": f"错误 {resp.status_code}: {error_body}"}
    except httpx.ConnectError:
        return {"ok": False, "message": "无法连接到服务器"}
    except httpx.TimeoutException:
        return {"ok": False, "message": "连接超时"}
    except Exception as e:
        return {"ok": False, "message": str(e)}


__all__ = ["ModelConfig", "PROVIDERS", "discover_ollama_models", "test_provider_connection"]

```
