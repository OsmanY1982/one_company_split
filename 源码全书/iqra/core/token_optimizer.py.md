# `iqra/core/token_optimizer.py`

> 路径：`iqra/core/token_optimizer.py` | 行数：51


---


```python
"""
Token Optimizer - Bridge module to token_saver
Fixes import mismatch in llm_backend.py and provides enhanced token optimization.

Features:
- Compatibility wrapper for llm_backend.py expected interface
- Lazy import to avoid circular dependencies
- Graceful fallback when token_saver is unavailable
"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TokenSaverMode:
    """Compatibility wrapper matching llm_backend.py's expected interface"""
    
    def __init__(self, mode: str = "balanced"):
        self.mode = mode
        self._optimizer = None
        self._load_optimizer()
    
    def _load_optimizer(self):
        """Lazy load optimizer to avoid circular imports"""
        try:
            from .token_saver import get_token_optimizer
            self._optimizer = get_token_optimizer(self.mode)
        except ImportError:
            try:
                from core.token_saver import get_token_optimizer
                self._optimizer = get_token_optimizer(self.mode)
            except ImportError:
                logger.warning("TokenSaver unavailable, using passthrough mode")
                self._optimizer = None
    
    def optimize(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize messages to reduce token usage"""
        if self._optimizer is None:
            return messages
        try:
            return self._optimizer.optimize_messages(messages)
        except Exception as e:
            logger.warning(f"Token optimization failed: {e}")
            return messages


def optimize_messages(messages: List[Dict[str, Any]], mode: str = "balanced") -> List[Dict[str, Any]]:
    """Top-level convenience function for token optimization"""
    optimizer = TokenSaverMode(mode)
    return optimizer.optimize(messages)

```
