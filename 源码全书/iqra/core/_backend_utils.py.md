# `iqra/core/_backend_utils.py`

> 路径：`iqra/core/_backend_utils.py` | 行数：164


---


```python
"""
Iqra LLM Backend — 供应商查询工具

list_all_providers / get_available_models / batch_scan_platforms
"""
import json
import ssl
import urllib.request
import urllib.error

from ._backend_providers import PROVIDER_TEMPLATES
from ._backend_models import ProviderConfig


def list_all_providers() -> dict[str, dict]:
    """
    列出所有内置供应商的元数据。
    返回 {id: {name, is_local, needs_key, default_model, base_url, description}}
    供 UI 层直接使用，无需导入 ProviderConfig。
    """
    result = {}
    for key, cfg in PROVIDER_TEMPLATES.items():
        is_local = any(h in cfg.base_url for h in ("localhost", "127.0.0.1", "0.0.0.0"))
        result[key] = {
            "id": key,
            "name": cfg.name,
            "is_local": is_local,
            "needs_key": not is_local and key != "custom",
            "default_model": cfg.model,
            "base_url": cfg.base_url,
            "description": cfg.description,
        }
    return result


def get_available_models(base_url: str, api_key: str = "", timeout: int = 15) -> list[str]:
    """
    从 OpenAI 兼容端点获取可用模型列表。
    大多数云端平台都有几十到几百个模型，
    此函数列出所有可用模型供用户切换。

    Args:
        base_url: API 端点地址 (如 https://api.deepseek.com/v1)
        api_key: API Key
        timeout: 请求超时秒数

    Returns:
        模型 ID 列表 (按字母排序)

    Raises:
        RuntimeError: 网络错误或 API 返回异常

    Usage:
        models = get_available_models("https://dashscope.aliyuncs.com/compatible-mode/v1", api_key="sk-xxx")
        # ['qwen-max', 'qwen-plus', 'qwen-turbo', ...]
    """
    url = base_url.rstrip("/")
    if "/v1" not in url:
        url += "/v1"
    url += "/models"

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        ctx = ssl.create_default_context()
        if any(h in base_url for h in ("localhost", "127.0.0.1", "0.0.0.0")):
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m["id"] for m in data.get("data", [])]
            models.sort()
            return models
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"HTTP {e.code}: {body}")
    except Exception as e:
        raise RuntimeError(f"获取模型列表失败: {e}")


def batch_scan_platforms(providers: dict[str, dict], timeout: int = 15) -> dict[str, dict]:
    """
    批量探测多个平台的连通性、模型列表和测试对话。
    自动区分: 缺Key / Key无效(401) / 网络不通 / 成功。

    Args:
        providers: {platform_id: {"name":str, "base_url":str, "api_key":str, "model":str}}
        timeout: 请求超时(秒)

    Returns:
        {platform_id: {
            "status": "ok"|"no_key"|"invalid_key"|"network_error"|"http_error",
            "model_count": int,
            "models": list[str],         # 前5个示例
            "test_response": str,         # 测试回复
            "error": str,                 # 错误信息
            "http_code": int,             # HTTP状态码(如有)
        }}
    """
    import time

    # 延迟导入避免循环依赖
    from ._backend_factory import BackendFactory

    results = {}

    for pid, info in providers.items():
        base_url = info.get("base_url", "").strip()
        api_key = info.get("api_key", "").strip()
        model = info.get("model", "").strip()
        name = info.get("name", pid)

        if not api_key:
            results[pid] = {"status": "no_key", "name": name,
                             "model_count": 0, "models": [],
                             "test_response": "", "error": "API Key not provided"}
            continue

        result = {"status": "unknown", "name": name,
                  "model_count": 0, "models": [],
                  "test_response": "", "error": ""}

        # 1) 获取模型列表
        try:
            models = get_available_models(base_url, api_key, timeout=timeout)
            result["model_count"] = len(models)
            result["models"] = models[:5]
            result["status"] = "ok"
        except RuntimeError as re:
            msg = str(re)
            if "401" in msg or "invalid_api_key" in msg.lower():
                result["status"] = "invalid_key"
                result["error"] = msg[:200]
            elif "403" in msg:
                result["status"] = "http_error"
                result["error"] = "403 Forbidden - check permissions"
            else:
                result["status"] = "http_error"
                result["error"] = msg[:200]
        except Exception as e:
            result["status"] = "network_error"
            result["error"] = str(e)[:200]

        # 2) 测试聊天 (仅当模型列表成功时)
        if result["status"] == "ok" and model:
            try:
                cfg = ProviderConfig(name=name, provider_type="openai_compatible",
                                     base_url=base_url, api_key=api_key, model=model)
                backend = BackendFactory.create(cfg)
                resp = backend.chat([{"role": "user", "content": "Hi"}], tools=None)
                result["test_response"] = (resp.content or "")[:100]
            except RuntimeError as re:
                result["test_response"] = f"[Error] {str(re)[:100]}"
            except Exception as e:
                result["test_response"] = f"[Error] {str(e)[:100]}"

        results[pid] = result
        time.sleep(0.2)  # 避免限流

    return results

```
