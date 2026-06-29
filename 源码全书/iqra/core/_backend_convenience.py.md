# `iqra/core/_backend_convenience.py`

> 路径：`iqra/core/_backend_convenience.py` | 行数：43


---


```python
"""
Iqra LLM Backend — 便捷 API

create_backend: 一行创建 LLM 后端
"""
from ._backend_models import ProviderConfig
from ._base_backend import BaseLLMBackend


def create_backend(
    provider: str = "ollama",
    api_key: str = "",
    model: str = "",
    base_url: str = "",
    temperature: float = 0.7,
    max_tokens: int = 262144,
) -> BaseLLMBackend:
    """
    一行创建 LLM 后端。

    用法:
        backend = create_backend("ollama")
        backend = create_backend("deepseek", api_key="sk-xxx")
        backend = create_backend("ollama", model="qwen2.5:7b")
        backend = create_backend("custom", base_url="http://myserver:8000/v1", model="my-model")
    """
    # 延迟导入避免循环依赖
    from ._backend_factory import BackendFactory

    try:
        return BackendFactory.from_template(provider, api_key, model, base_url)
    except ValueError:
        # 如果不是内置模板, 当作自定义 OpenAI 兼容端点
        cfg = ProviderConfig(
            name=provider,
            provider_type="openai_compatible",
            base_url=base_url or "http://localhost:11434/v1",
            api_key=api_key,
            model=model or "default",
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return BackendFactory.create(cfg)

```
