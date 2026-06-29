# `iqra/core/_quick_funcs.py`

> 路径：`iqra/core/_quick_funcs.py` | 行数：31


---


```python
"""快捷函数 - 从 core_engine.py 拆分"""

from ._config_helpers import _get_default_model
from iqra.core.llm_backend import ProviderConfig


def create_engine(model: str = None, base_url: str = "http://localhost:11434/v1"):
    """创建引擎实例（默认从配置文件读取模型名）"""
    # 延迟导入避免循环依赖
    from .core_engine import IqraCoreEngine

    if model is None:
        model = _get_default_model()
    config = ProviderConfig(
        name="Ollama",
        provider_type="openai_compatible",
        base_url=base_url,
        model=model,
        temperature=0.7,
        max_tokens=262144
    )
    return IqraCoreEngine(config)


def quick_chat(question: str, model: str = None) -> str:
    """快速对话（无状态，默认从配置文件读取模型名）"""
    if model is None:
        model = _get_default_model()
    engine = create_engine(model=model)
    return engine.chat(question)


```
