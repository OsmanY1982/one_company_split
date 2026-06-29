# `iqra/core/_claude_tools.py`

> 路径：`iqra/core/_claude_tools.py` | 行数：300


---


```python
"""5个 Claude Code 对标工具 - 从 core_engine.py 拆分"""

import fnmatch
import os
import subprocess

# 项目根目录 = iqra 所在目录的父目录（即 one_company_desktop）
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _resolve_path(rel_path: str) -> str:
    """将相对路径解析为绝对路径（相对项目根目录）"""
    p = os.path.join(_project_root, rel_path)
    return os.path.abspath(p)


def _register_claude_tools(registry):
    """注册 5 个 Claude Code 对标工具"""
    
    # 8. Shell 命令执行 (对标 Claude Code terminal)
    def shell_execute(command: str, cwd: str = "", timeout: int = 60) -> dict:
        """执行 Shell 命令（bash），覆盖 git/npm/pip/build/test/lint 等所有 CLI 操作"""
        try:
            work_dir = _resolve_path(cwd) if cwd else _project_root
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=work_dir,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )
            output = result.stdout
            if result.stderr:
                output += "\n[stderr]\n" + result.stderr
            return {
                "stdout": result.stdout[:8000],
                "stderr": result.stderr[:4000],
                "returncode": result.returncode,
                "cwd": work_dir
            }
        except subprocess.TimeoutExpired:
            return {"error": f"命令超时（{timeout}秒）"}
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="shell_execute",
        description="执行 Shell 命令。可用于 git 操作、npm/pip 包管理、运行测试/构建/格式化/lint、系统命令等所有终端操作。命令在项目根目录执行",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的 Shell 命令，如 'git diff' 或 'npm install'"},
                "cwd": {"type": "string", "description": "工作目录路径，默认为项目根目录", "default": ""},
                "timeout": {"type": "integer", "description": "超时秒数", "default": 60}
            },
            "required": ["command"]
        },
        handler=shell_execute
    )
    
    # 9. 文件列表 (对标 Claude Code ls/dir)
    def file_list(path: str = ".", pattern: str = "*", recursive: bool = False, max_depth: int = 3) -> dict:
        """列出目录下的文件和子目录"""
        try:
            abs_path = _resolve_path(path)
            if not os.path.exists(abs_path):
                return {"error": f"路径不存在: {abs_path}"}
            
            entries = []
            if recursive:
                for root, dirs, files in os.walk(abs_path):
                    depth = root[len(abs_path):].count(os.sep)
                    if depth >= max_depth:
                        dirs.clear()
                        continue
                    for f in files:
                        if fnmatch.fnmatch(f, pattern):
                            entries.append(os.path.relpath(os.path.join(root, f), abs_path))
            else:
                for f in sorted(os.listdir(abs_path)):
                    if fnmatch.fnmatch(f, pattern):
                        p = os.path.relpath(os.path.join(abs_path, f), abs_path)
                        entries.append(p + ("/" if os.path.isdir(os.path.join(abs_path, f)) else ""))
            
            return {
                "path": abs_path,
                "entries": entries[:200],
                "count": len(entries),
                "truncated": len(entries) > 200
            }
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="file_list",
        description="列出目录内容，支持文件名匹配和递归。用于了解项目结构、查找文件",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "目录路径，相对项目根目录", "default": "."},
                "pattern": {"type": "string", "description": "文件名匹配模式，如 *.py 或 test_*", "default": "*"},
                "recursive": {"type": "boolean", "description": "是否递归列出子目录", "default": False},
                "max_depth": {"type": "integer", "description": "递归最大深度", "default": 3}
            },
            "required": []
        },
        handler=file_list
    )
    
    # 10. 文件内容搜索 (对标 Claude Code grep)
    def file_search(query: str, path: str = ".", file_pattern: str = "*", max_results: int = 30) -> dict:
        """在文件中搜索文本内容"""
        try:
            abs_path = _resolve_path(path)
            if not os.path.exists(abs_path):
                return {"error": f"路径不存在: {abs_path}"}
            
            results = []
            for root, dirs, files in os.walk(abs_path):
                # 跳过隐藏目录和常见忽略目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'venv', '.git', 'dist', 'build', '.next')]
                
                for f in files:
                    if not fnmatch.fnmatch(f, file_pattern):
                        continue
                    if len(results) >= max_results:
                        break
                    
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                            for i, line in enumerate(fh, 1):
                                if query.lower() in line.lower():
                                    rel = os.path.relpath(fp, abs_path)
                                    results.append({
                                        "file": rel,
                                        "line": i,
                                        "content": line.strip()[:200]
                                    })
                                    if len(results) >= max_results:
                                        break
                    except Exception:
                        continue
                
                if len(results) >= max_results:
                    break
            
            return {
                "query": query,
                "matches": results[:max_results],
                "count": len(results),
                "truncated": len(results) >= max_results
            }
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="file_search",
        description="在文件中搜索文本内容（grep）。用于查找函数定义、变量引用、TODO 注释、错误信息等",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词（不区分大小写）"},
                "path": {"type": "string", "description": "搜索目录，相对项目根目录", "default": "."},
                "file_pattern": {"type": "string", "description": "限定文件类型，如 *.py 或 *.js", "default": "*"},
                "max_results": {"type": "integer", "description": "最大结果数", "default": 30}
            },
            "required": ["query"]
        },
        handler=file_search
    )
    
    # 11. 文件编辑 (对标 Claude Code edit)
    def edit_file(path: str, old_str: str, new_str: str, replace_all: bool = False) -> dict:
        """精确替换文件中的文本片段"""
        try:
            abs_path = _resolve_path(path)
            if not os.path.exists(abs_path):
                return {"error": f"文件不存在: {abs_path}"}
            
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_encoding = 'utf-8'
            
            count = content.count(old_str)
            if count == 0:
                return {"error": f"未找到要替换的文本片段（old_str 在文件中不存在）"}
            if count > 1 and not replace_all:
                return {
                    "error": f"找到 {count} 处匹配，需要替换多少处？请设置 replace_all=true 替换全部，或缩小 old_str 范围确保唯一匹配",
                    "count": count
                }
            
            if replace_all:
                new_content = content.replace(old_str, new_str)
                replacements = count
            else:
                new_content = content.replace(old_str, new_str, 1)
                replacements = 1
            
            with open(abs_path, 'w', encoding=original_encoding) as f:
                f.write(new_content)
            
            return {
                "success": True,
                "path": abs_path,
                "replacements": replacements
            }
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="edit_file",
        description="精确替换文件中的文本片段。用于修改代码、修复 bug、更新配置。old_str 必须与文件中内容完全一致（含缩进和换行）。支持 replace_all=true 替换所有匹配项",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "要编辑的文件路径，相对项目根目录"},
                "old_str": {"type": "string", "description": "要被替换的原始文本，必须与文件内容完全一致"},
                "new_str": {"type": "string", "description": "替换后的新文本"},
                "replace_all": {"type": "boolean", "description": "是否替换所有匹配项", "default": False}
            },
            "required": ["path", "old_str", "new_str"]
        },
        handler=edit_file
    )
    
    # 12. 项目结构映射 (对标 Claude Code 项目上下文)
    def project_map(depth: int = 4, focus: str = "") -> dict:
        """生成项目文件树，帮助 AI 理解项目结构"""
        try:
            root = _project_root
            
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
                
                # 如果有 focus，优先展示相关目录
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
                "max_depth": depth
            }
        except Exception as e:
            return {"error": str(e)}
    
    registry.register(
        name="project_map",
        description="生成项目目录树，了解项目整体结构。用于快速掌握代码仓库布局、识别关键目录和文件",
        parameters={
            "type": "object",
            "properties": {
                "depth": {"type": "integer", "description": "目录展开深度，默认 4", "default": 4},
                "focus": {"type": "string", "description": "优先聚焦的目录名，如 'src' 或 'modules'", "default": ""}
            },
            "required": []
        },
        handler=project_map
    )

```
