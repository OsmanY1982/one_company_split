# `iqra/core/model_status.py`

> 路径：`iqra/core/model_status.py` | 行数：37


---


```python
"""
Bridge module: model_status -> model_status_manager
Fixes import mismatch in llm_backend.py
"""
from iqra.core.model_status_manager import (
    ModelStatusManager,
    get_model_status_manager,
)


def mark_model_no_token(model: str, provider: str = "", error_message: str = ""):
    """Mark a model as having no remaining tokens/quota."""
    manager = get_model_status_manager()
    manager.mark_failed(
        model=model,
        error_type="no_token",
        error_message=error_message or "Token 用尽或额度不足",
        provider=provider,
    )


def mark_model_failed(model: str, error_type: str = "api_error",
                      error_message: str = "", provider: str = ""):
    """Mark a model as failed."""
    manager = get_model_status_manager()
    manager.mark_failed(
        model=model,
        error_type=error_type,
        error_message=error_message,
        provider=provider,
    )


def is_model_available(model: str, provider: str = "") -> bool:
    """Check if a model is available."""
    manager = get_model_status_manager()
    return manager.is_model_available(model, provider)

```
