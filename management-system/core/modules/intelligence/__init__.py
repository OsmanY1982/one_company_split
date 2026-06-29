"""
Alias forwarding: redirects all submodule imports from modules.intelligence.*
to the standalone intelligence/ package at project root.

Uses __path__ injection so Python's import machinery finds
intelligence/agent_bridge.py etc. as modules.intelligence.agent_bridge etc.
"""
import sys
from pathlib import Path

# management-system/core/modules/intelligence/ → modules → core → management-system → project_root
_project_root = Path(__file__).resolve().parents[4]
_intelligence_dir = str(_project_root / "intelligence")

if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# __path__ injection: Python searches intelligence/ for submodules
__path__ = [_intelligence_dir]


def __getattr__(name):
    """Lazy re-export top-level names from the real intelligence package."""
    import importlib
    _pkg = importlib.import_module("intelligence")
    return getattr(_pkg, name)
