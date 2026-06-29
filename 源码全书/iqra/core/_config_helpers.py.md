# `iqra/core/_config_helpers.py`

> 路径：`iqra/core/_config_helpers.py` | 行数：45


---


```python
"""配置读取辅助函数 - 从 core_engine.py 拆分"""

import json
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from iqra.core.llm_backend import ProviderConfig


def _get_default_model(fallback: str = "qwen2.5:7b") -> str:
    """优先从 ConfigManager（登录后模型设置）读取，失败则回退到直接读 JSON 文件"""
    cfg = _get_active_provider_config(fallback)
    return cfg.model if cfg else fallback


def _get_active_provider_config(fallback_model: str = "qwen2.5:7b") -> Optional[ProviderConfig]:
    """从 ConfigManager 读取当前激活的供应商配置（含 model / base_url / api_key 等）。
    失败时回退到直接读 JSON 构建最小配置（仅 model+base_url）。
    返回 None 表示完全读取失败。
    """
    try:
        from iqra.modules.config_manager import ConfigManager
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config = ConfigManager(project_root)
        active = config.get_active_provider()
        if active:
            return active
    except Exception:
        pass
    # 回退：直接读 JSON
    try:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "iqra_config.json"
        )
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        ollama = cfg.get("local_providers", {}).get("ollama", {})
        model = ollama.get("model", fallback_model)
        base_url = ollama.get("base_url", "http://localhost:11434")
        return ProviderConfig(provider="ollama", base_url=base_url, model=model)
    except Exception:
        return None

```
