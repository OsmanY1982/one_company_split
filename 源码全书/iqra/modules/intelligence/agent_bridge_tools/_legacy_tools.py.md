# `iqra/modules/intelligence/agent_bridge_tools/_legacy_tools.py`

> 路径：`iqra/modules/intelligence/agent_bridge_tools/_legacy_tools.py` | 行数：305


---


```python
"""旧引擎工具注入 Mixin：query_database / execute_code / add_schedule / add_customer / project_map

从 _basic_tools.py 和 _claude_tools.py 提取，适配 AgentBridge ToolRegistry 格式。
功能不做改动，仅调整路径计算（子目录深度增加 1 层）。
"""

import os
import sys
import subprocess
import sqlite3

# ── 代码沙箱前导代码（从 _basic_tools.py 原样提取）──
_CODE_SANDBOX_PREAMBLE = '''
import sys as _sys

# 危险模块黑名单（用户代码直接导入时拦截）
_dangerous = {
    'subprocess', 'shutil', 'ctypes', 'signal', 'socket',
    'multiprocessing', 'threading', 'pty', 'fcntl', 'posix',
    'importlib', 'pkgutil', 'inspect', 'code', 'codeop',
}

# ── 导入钩子：拦截用户代码直接导入危险模块 ──
class _ImportBlocker:
    def find_spec(self, fullname, path, target=None):
        top = fullname.split('.')[0]
        if top in _dangerous:
            import traceback as _tb
            stack = _tb.extract_stack()
            for frame in stack[:-1]:
                fname = frame.filename
                if '/python' in fname or 'site-packages' in fname:
                    return None
            raise ImportError(f"Module '{fullname}' is blocked for security reasons")
        return None

_sys.meta_path.insert(0, _ImportBlocker())

# ── os 模块函数级安全补丁 ──
# os 是标准库广泛依赖的基础模块，不能完全拦截
# 但我们对危险函数做猴子补丁
try:
    import os as _real_os
    _OS_DANGEROUS = {
        'system', 'popen', 'execv', 'execve', 'execvp', 'execvpe',
        'spawnl', 'spawnle', 'spawnlp', 'spawnlpe', 'spawnv', 'spawnve',
        'spawnvp', 'spawnvpe', 'fork', 'kill', 'remove', 'unlink',
        'rmdir', 'rename', 'renames', 'chmod', 'chown', 'link', 'symlink',
    }
    for _fn in _OS_DANGEROUS:
        if hasattr(_real_os, _fn):
            _blocked_fn = _fn
            def _make_blocked(blocked=_blocked_fn):
                def _blocker(*_a, **_kw):
                    raise OSError(f"os.{blocked}() is blocked in sandbox")
                return _blocker
            setattr(_real_os, _blocked_fn, _make_blocked())
except Exception:
    pass
'''

# agent_bridge_tools/ 位于 iqra/modules/intelligence/agent_bridge_tools/
# 4 层 dirname → iqra/，5 层 dirname → one_company_split/
_IQRA_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_PROJECT_ROOT = os.path.dirname(_IQRA_ROOT)


class _LegacyToolsMixin:
    """旧引擎工具注入：5 个 AgentBridge 缺失的工具"""

    # ── 1. query_database ──
    def _reg_query_database(self):
        def handler(db_name: str, sql: str) -> dict:
            """查询 SQLite 数据库"""
            db_path = os.path.join(_IQRA_ROOT, "data", db_name)
            if not os.path.exists(db_path):
                return {"error": f"数据库不存在：{db_name}"}
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            try:
                c.execute(sql)
                rows = [dict(row) for row in c.fetchall()]
                return {"columns": list(rows[0].keys()) if rows else [], "rows": rows, "count": len(rows)}
            except Exception as e:
                return {"error": str(e)}
            finally:
                conn.close()

        self.registry.register(
            name="query_database",
            description="查询 SQLite 数据库，支持 products.db, orders.db, members.db, finance.db, customers.db, inventory.db, schedule.db",
            parameters={
                "type": "object",
                "properties": {
                    "db_name": {"type": "string", "description": "数据库文件名，如 'products.db'"},
                    "sql": {"type": "string", "description": "SQL 查询语句，只支持 SELECT"},
                },
                "required": ["db_name", "sql"],
            },
            category="data",
        )(handler)

    # ── 2. execute_code（沙箱加固 Python 执行）──
    def _reg_execute_code(self):
        def handler(code: str, timeout: int = 30) -> dict:
            """执行 Python 代码（沙箱环境，已拦截危险模块）"""
            try:
                sandboxed = _CODE_SANDBOX_PREAMBLE + '\n' + code
                result = subprocess.run(
                    [sys.executable, "-c", sandboxed],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=_IQRA_ROOT,
                )
                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                }
            except subprocess.TimeoutExpired:
                return {"error": f"代码执行超时（{timeout}秒）"}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="execute_code",
            description="执行 Python 代码（沙箱环境，已拦截危险模块如 subprocess/os.system/socket 等），用于数据分析、文件处理等任务",
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的 Python 代码"},
                    "timeout": {"type": "integer", "description": "超时时间（秒）", "default": 30},
                },
                "required": ["code"],
            },
            category="code",
        )(handler)

    # ── 3. add_schedule ──
    def _reg_add_schedule(self):
        def handler(title: str, start_time: str, type: str = "event", location: str = "", description: str = "") -> dict:
            """添加日程安排"""
            try:
                db_path = os.path.join(_IQRA_ROOT, "data", "schedule.db")
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute('''
                    CREATE TABLE IF NOT EXISTS schedules (
                        id INTEGER PRIMARY KEY,
                        title TEXT NOT NULL,
                        type TEXT,
                        start_time TEXT,
                        end_time TEXT,
                        location TEXT,
                        description TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT DEFAULT (datetime('now'))
                    )
                ''')
                c.execute('''
                    INSERT INTO schedules (title, type, start_time, location, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', (title, type, start_time, location, description))
                conn.commit()
                conn.close()
                return {"success": True, "message": f"已添加日程：{title}"}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="add_schedule",
            description="添加日程安排到日历",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "日程标题"},
                    "start_time": {"type": "string", "description": "开始时间，ISO 格式如 2026-05-12T14:00:00"},
                    "type": {"type": "string", "description": "类型：meeting, deadline, reminder, event", "default": "event"},
                    "location": {"type": "string", "description": "地点", "default": ""},
                    "description": {"type": "string", "description": "描述", "default": ""},
                },
                "required": ["title", "start_time"],
            },
            category="productivity",
        )(handler)

    # ── 4. add_customer ──
    def _reg_add_customer(self):
        def handler(name: str, company: str = "", phone: str = "", email: str = "", source: str = "") -> dict:
            """添加客户记录"""
            try:
                db_path = os.path.join(_IQRA_ROOT, "data", "customers.db")
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                c.execute('''
                    CREATE TABLE IF NOT EXISTS customers (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        company TEXT,
                        phone TEXT,
                        email TEXT,
                        source TEXT,
                        status TEXT DEFAULT 'lead',
                        created_at TEXT DEFAULT (datetime('now'))
                    )
                ''')
                c.execute('''
                    INSERT INTO customers (name, company, phone, email, source)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, company, phone, email, source))
                conn.commit()
                conn.close()
                return {"success": True, "message": f"已添加客户：{name}"}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="add_customer",
            description="添加客户到 CRM 系统",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "客户姓名"},
                    "company": {"type": "string", "description": "公司名称", "default": ""},
                    "phone": {"type": "string", "description": "联系电话", "default": ""},
                    "email": {"type": "string", "description": "邮箱", "default": ""},
                    "source": {"type": "string", "description": "来源：referral, website, cold_call, event", "default": ""},
                },
                "required": ["name"],
            },
            category="productivity",
        )(handler)

    # ── 5. project_map ──
    def _reg_project_map(self):
        def handler(depth: int = 4, focus: str = "") -> dict:
            """生成项目文件树，帮助 AI 理解项目结构"""
            try:
                root = _PROJECT_ROOT

                skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv',
                             'dist', 'build', '.next', '.DS_Store', 'logs', '__pycache__'}

                lines = []
                file_count = 0

                def walk(dir_path, prefix="", current_depth=0):
                    nonlocal file_count
                    if current_depth > depth:
                        return

                    try:
                        entries = sorted(os.listdir(dir_path))
                    except PermissionError:
                        return

                    dirs = [e for e in entries if os.path.isdir(os.path.join(dir_path, e)) and e not in skip_dirs and not e.startswith('.')]
                    files = [e for e in entries if os.path.isfile(os.path.join(dir_path, e)) and not e.startswith('.')]

                    if focus and focus in dirs:
                        dirs.remove(focus)
                        dirs.insert(0, focus)

                    for i, d in enumerate(dirs):
                        is_last = i == len(dirs) - 1 and not files
                        connector = "└── " if is_last else "├── "
                        lines.append(f"{prefix}{connector}{d}/")
                        extension = "    " if is_last else "│   "
                        walk(os.path.join(dir_path, d), prefix + extension, current_depth + 1)

                    for i, f in enumerate(files):
                        file_count += 1
                        if file_count > 500:
                            lines.append(f"{prefix}... (超过500个文件，已截断)")
                            return
                        is_last = i == len(files) - 1
                        connector = "└── " if is_last else "├── "
                        lines.append(f"{prefix}{connector}{f}")

                walk(root)

                return {
                    "root": root,
                    "tree": "\n".join(lines[:600]),
                    "file_count": file_count,
                    "max_depth": depth,
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="project_map",
            description="生成项目目录树，了解项目整体结构。用于快速掌握代码仓库布局、识别关键目录和文件",
            parameters={
                "type": "object",
                "properties": {
                    "depth": {"type": "integer", "description": "目录展开深度，默认 4", "default": 4},
                    "focus": {"type": "string", "description": "优先聚焦的目录名，如 'src' 或 'modules'", "default": ""},
                },
                "required": [],
            },
            category="system",
        )(handler)

```
