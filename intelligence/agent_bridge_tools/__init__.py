"""AgentBridge 工具注册 Mixin（模块化子目录）

v5.1 — 合并旧引擎工具
"""

from ._file_tools import _FileToolsMixin
from ._code_tools import _CodeToolsMixin
from ._system_tools import _SystemToolsMixin
from ._web_tools import _WebToolsMixin
from ._task_tools import _TaskToolsMixin
from ._image_tools import _ImageToolsMixin
from ._convert_tools import _ConvertToolsMixin
from ._legacy_tools import _LegacyToolsMixin


class AgentBridgeToolsMixin(
    _FileToolsMixin,
    _CodeToolsMixin,
    _SystemToolsMixin,
    _WebToolsMixin,
    _TaskToolsMixin,
    _ImageToolsMixin,
    _ConvertToolsMixin,
    _LegacyToolsMixin,
):
    """工具注册"""

    def _register_tools(self):
        # ── 文件系统工具 ──
        self._reg_read_file()
        self._reg_write_file()
        self._reg_edit_file()
        self._reg_list_directory()
        self._reg_search_files()
        self._reg_search_file_content()
        # ── 图片工具 ──
        self._reg_search_image()
        self._reg_analyze_image()
        # ── 格式转换工具 ──
        self._reg_pdf_to_docx()
        self._reg_docx_to_pdf()
        self._reg_convert_image()
        self._reg_images_to_pdf()
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
        # ── 任务 ──
        self._reg_todo()
        self._reg_task_scheduler()
        self._reg_search_sessions()
        # ── 旧引擎注入 ──
        self._reg_query_database()
        self._reg_execute_code()
        self._reg_add_schedule()
        self._reg_add_customer()
        self._reg_project_map()
