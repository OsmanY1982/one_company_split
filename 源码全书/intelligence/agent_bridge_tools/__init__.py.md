# `intelligence/agent_bridge_tools/__init__.py`

> 路径：`intelligence/agent_bridge_tools/__init__.py` | 行数：62


---


```python
"""AgentBridge 工具注册 Mixin（模块化子目录）

将原 844 行单文件拆为 6 个 Mixin + __init__ 多重继承组合器。
AgentBridge 继承 AgentBridgeToolsMixin 后即可通过 registry.register() 注册全部 LLM 工具。

v5.1 — 合并旧引擎工具：注入 _LegacyToolsMixin（query_database / execute_code / add_schedule / add_customer / project_map）
"""

from ._file_tools import _FileToolsMixin
from ._code_tools import _CodeToolsMixin
from ._system_tools import _SystemToolsMixin
from ._web_tools import _WebToolsMixin
from ._task_tools import _TaskToolsMixin
from ._legacy_tools import _LegacyToolsMixin


class AgentBridgeToolsMixin(
    _FileToolsMixin,
    _CodeToolsMixin,
    _SystemToolsMixin,
    _WebToolsMixin,
    _TaskToolsMixin,
    _LegacyToolsMixin,
):
    """工具注册：文件 / 代码 / 系统 / 网络 / 任务 / 旧引擎 组合 Mixin"""

    def _register_tools(self):
        """注册全部 27 个 LLM 工具（21 原有 + 5 旧引擎注入 + 1 generate_diff）"""
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
        self._reg_search_project_book()
        self._reg_generate_diff()
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
        # ── 旧引擎注入（v5.1 合并）──
        self._reg_query_database()
        self._reg_execute_code()
        self._reg_add_schedule()
        self._reg_add_customer()
        self._reg_project_map()

```
