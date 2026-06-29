# `iqra/core/modules/intelligence/__init__.py`

> 路径：`iqra/core/modules/intelligence/__init__.py` | 行数：24


---


```python
"""
Forwarding: iqra/core/modules/intelligence/ → project_root/intelligence/

When agent_bridge.py (loaded via SourceFileLoader with iqra/ as cwd) does
  from core.modules.intelligence.session_context import session_ctx
and core resolves to iqra/core/, this forwarding ensures the import succeeds.
"""
import sys
from pathlib import Path

# iqra/core/modules/intelligence/ → modules → core → iqra → project_root
_project_root = Path(__file__).resolve().parents[4]
_intelligence_dir = str(_project_root / "intelligence")

if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

__path__ = [_intelligence_dir]


def __getattr__(name):
    import importlib
    _pkg = importlib.import_module("intelligence")
    return getattr(_pkg, name)

```
