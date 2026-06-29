# `planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/__init__.py`

> 路径：`planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/__init__.py` | 行数：61


---


```python
"""AgentBridge 工具注册 Mixin（模块化子目录）

将原 844 行单文件拆为 5 个 Mixin + __init__ 多重继承组合器。
AgentBridge 继承 AgentBridgeToolsMixin 后即可通过 registry.register() 注册全部 LLM 工具。
"""


import sys as _sys, os as _os
_dir = _os.path.dirname(_os.path.abspath(__file__))
for _ in range(10):
    if _os.path.exists(_os.path.join(_dir, 'dark_theme.py')):
        _parent = _os.path.dirname(_dir)
        if _parent not in _sys.path:
            _sys.path.insert(0, _parent)
        break
    _dir = _os.path.dirname(_dir)

from ._file_tools import _FileToolsMixin
from ._code_tools import _CodeToolsMixin
from ._system_tools import _SystemToolsMixin
from ._web_tools import _WebToolsMixin
from ._task_tools import _TaskToolsMixin


class AgentBridgeToolsMixin(
    _FileToolsMixin,
    _CodeToolsMixin,
    _SystemToolsMixin,
    _WebToolsMixin,
    _TaskToolsMixin,
):
    """工具注册：文件 / 代码 / 系统 / 网络 / 任务 组合 Mixin"""

    def _register_tools(self):
        """注册全部 19 个 LLM 工具"""
        # ── 文件系统工具 ──
        self._reg_read_file()
        self._reg_write_file()
        self._reg_edit_file()
        self._reg_list_directory()
        self._reg_search_files()
        # ── 代码工具 ──
        self._reg_search_code()
        self._reg_run_tests()
        self._reg_execute_python()
        self._reg_analyze_code()
        self._reg_search_codebase()
        self._reg_apply_patch()
        # ── 系统工具 ──
        self._reg_execute_shell()
        self._reg_desktop_control()
        self._reg_git_operation()
        # ── 网络 ──
        self._reg_web_search()
        self._reg_web_fetch_page()
        self._reg_web_scrape()
        self._reg_batch_scrape()
        # ── 任务 / 生产力 ──
        self._reg_todo()
        self._reg_task_scheduler()
        self._reg_search_sessions()

```
