# `iqra/core/_basic_tools.py`

> 路径：`iqra/core/_basic_tools.py` | 行数：311


---


```python
"""7个基础内置工具 - 从 core_engine.py 拆分"""

import json
import re
import sqlite3
import subprocess
import sys
import os

# ── 代码沙箱前导代码 ──
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


def _register_basic_tools(registry):
    """注册 7 个基础内置工具"""
    
    # 1. 数据库查询工具
    def query_database(db_name: str, sql: str) -> dict:
        """查询 SQLite 数据库"""
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", db_name)
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
    
    registry.register(
        name="query_database",
        description="查询 SQLite 数据库，支持 products.db, orders.db, members.db, finance.db, customers.db, inventory.db, schedule.db",
        parameters={
            "type": "object",
            "properties": {
                "db_name": {"type": "string", "description": "数据库文件名，如 'products.db'"},
                "sql": {"type": "string", "description": "SQL 查询语句，只支持 SELECT"}
            },
            "required": ["db_name", "sql"]
        },
        handler=query_database
    )
    
    # 2. 文件读取工具
    def read_file(path: str, limit: int = 100) -> dict:
        """读取文件内容"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:limit]
            return {"content": "".join(lines), "total_lines": len(lines)}
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="read_file",
        description="读取文本文件内容",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "limit": {"type": "integer", "description": "最大读取行数", "default": 100}
            },
            "required": ["path"]
        },
        handler=read_file
    )
    
    # 3. 文件写入工具
    def write_file(path: str, content: str) -> dict:
        """写入文件内容"""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"success": True, "path": path, "bytes": len(content)}
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="write_file",
        description="写入内容到文件",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "文件内容"}
            },
            "required": ["path", "content"]
        },
        handler=write_file
    )
    
    # 4. 代码执行工具（沙箱加固）
    def execute_code(code: str, timeout: int = 30) -> dict:
        """执行 Python 代码（沙箱环境，已拦截危险模块）"""
        try:
            # 注入沙箱前导代码
            sandboxed = _CODE_SANDBOX_PREAMBLE + '\n' + code
            
            result = subprocess.run(
                [sys.executable, "-c", sandboxed],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": f"代码执行超时（{timeout}秒）"}
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="execute_code",
        description="执行 Python 代码，用于数据分析、文件处理等任务",
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "要执行的 Python 代码"},
                "timeout": {"type": "integer", "description": "超时时间（秒）", "default": 30}
            },
            "required": ["code"]
        },
        handler=execute_code
    )
    
    # 5. 网络搜索工具
    def web_search(query: str, max_results: int = 5) -> dict:
        """联网搜索获取实时信息"""
        try:
            import urllib.request
            import urllib.parse
            encoded = urllib.parse.quote(query)
            url = f"https://cn.bing.com/search?q={encoded}&count={max_results}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
            # 简单提取标题
            titles = re.findall(r'<h2[^>]*>.*?<a[^>]*>(.*?)</a>', html, re.S)[:max_results]
            snippets = re.findall(r'<p[^>]*>(.*?)</p>', html, re.S)[:max_results]
            results = []
            for t, s in zip(titles, snippets):
                t_clean = re.sub(r'<[^>]+>', '', t)
                s_clean = re.sub(r'<[^>]+>', '', s)
                results.append({"title": t_clean.strip(), "snippet": s_clean.strip()})
            return {"results": results, "query": query}
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="web_search",
        description="联网搜索获取实时信息，用于查询新闻、天气、股票等",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "max_results": {"type": "integer", "description": "最大结果数", "default": 5}
            },
            "required": ["query"]
        },
        handler=web_search
    )
    
    # 6. 日程添加工具
    def add_schedule(title: str, start_time: str, type: str = "event", location: str = "", description: str = "") -> dict:
        """添加日程安排"""
        try:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "schedule.db")
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
    
    registry.register(
        name="add_schedule",
        description="添加日程安排到日历",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "日程标题"},
                "start_time": {"type": "string", "description": "开始时间，ISO 格式如 2026-05-12T14:00:00"},
                "type": {"type": "string", "description": "类型：meeting, deadline, reminder, event", "default": "event"},
                "location": {"type": "string", "description": "地点", "default": ""},
                "description": {"type": "string", "description": "描述", "default": ""}
            },
            "required": ["title", "start_time"]
        },
        handler=add_schedule
    )
    
    # 7. 客户管理工具
    def add_customer(name: str, company: str = "", phone: str = "", email: str = "", source: str = "") -> dict:
        """添加客户记录"""
        try:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "customers.db")
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
    
    registry.register(
        name="add_customer",
        description="添加客户到 CRM 系统",
        parameters={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "客户姓名"},
                "company": {"type": "string", "description": "公司名称", "default": ""},
                "phone": {"type": "string", "description": "联系电话", "default": ""},
                "email": {"type": "string", "description": "邮箱", "default": ""},
                "source": {"type": "string", "description": "来源：referral, website, cold_call, event", "default": ""}
            },
            "required": ["name"]
        },
        handler=add_customer
    )

```
