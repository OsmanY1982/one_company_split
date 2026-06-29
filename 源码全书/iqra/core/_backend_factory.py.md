# `iqra/core/_backend_factory.py`

> 路径：`iqra/core/_backend_factory.py` | 行数：86


---


```python
"""
Iqra LLM Backend — 后端工厂

BackendFactory: 根据配置创建对应的 LLM 后端实例
"""
from ._backend_models import ProviderConfig
from ._base_backend import BaseLLMBackend
from ._backend_providers import PROVIDER_TEMPLATES


class BackendFactory:
    """根据配置创建对应的 LLM 后端实例"""

    @staticmethod
    def create(config: ProviderConfig) -> BaseLLMBackend:
        # 延迟导入避免循环依赖
        from .llm_backend import OpenAICompatibleBackend

        pt = config.provider_type
        if pt == "openai_compatible":
            return OpenAICompatibleBackend(config)
        else:
            raise ValueError(
                f"不支持的供应商类型: {pt}\n"
                f"当前支持: openai_compatible (覆盖 OpenAI/DeepSeek/Ollama 等)"
            )

    @staticmethod
    def from_template(
        template_name: str,
        api_key: str = "",
        model: str = "",
        base_url: str = "",
    ) -> BaseLLMBackend:
        """
        从内置模板创建后端。

        用法:
            be = BackendFactory.from_template("deepseek", api_key="sk-xxx")
            be = BackendFactory.from_template("ollama")  # 无需 api_key
            be = BackendFactory.from_template("ollama", model="llama3:8b")
        """
        template = PROVIDER_TEMPLATES.get(template_name)
        if not template:
            available = ", ".join(PROVIDER_TEMPLATES.keys())
            raise ValueError(
                f"未知模板: '{template_name}'\n可用: {available}"
            )

        config = ProviderConfig(
            name=template.name,
            provider_type=template.provider_type,
            base_url=base_url or template.base_url,
            api_key=api_key or template.api_key,
            model=model or template.model,
            temperature=template.temperature,
            max_tokens=template.max_tokens,
            extra_headers=dict(template.extra_headers),
            description=template.description,
        )
        return BackendFactory.create(config)

    @staticmethod
    def from_dict(config_dict: dict) -> BaseLLMBackend:
        """从字典恢复后端 (用于设置持久化)"""
        # 过滤掉不在 ProviderConfig 中的键
        valid_keys = {f.name for f in ProviderConfig.__dataclass_fields__.values()}
        filtered = {k: v for k, v in config_dict.items() if k in valid_keys}
        config = ProviderConfig(**filtered)
        return BackendFactory.create(config)

    @staticmethod
    def list_templates() -> list[dict]:
        """列出所有可用供应商模板"""
        result = []
        for key, cfg in PROVIDER_TEMPLATES.items():
            is_local = any(h in cfg.base_url for h in ("localhost", "127.0.0.1", "0.0.0.0"))
            result.append({
                "id": key,
                "name": cfg.name,
                "model": cfg.model,
                "description": cfg.description,
                "local": is_local,
                "needs_api_key": not is_local and key != "custom",
            })
        return result

```
