# `planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_file_tools.py`

> 路径：`planetarium/core/modules/intelligence/agent_bridge/agent_bridge_tools/_file_tools.py` | 行数：173


---


```python
"""文件系统工具 Mixin：read_file / write_file / edit_file / list_directory / search_files"""

import os
import fnmatch


class _FileToolsMixin:
    """文件系统工具注册"""

    # ── 1. read_file ──
    def _reg_read_file(self):
        def handler(path: str, limit: int = 200) -> dict:
            try:
                if not os.path.exists(path):
                    return {"error": f"文件不存在: {path}"}
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()[:limit]
                return {
                    "content": "".join(lines),
                    "total_lines": len(lines),
                    "truncated": len(lines) >= limit,
                    "path": path,
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="read_file",
            description="读取文本文件内容，返回行数和全文",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件绝对路径"},
                    "limit": {"type": "integer", "description": "最大读取行数，默认200", "default": 200},
                },
                "required": ["path"],
            },
            category="file",
        )(handler)

    # ── 2. write_file ──
    def _reg_write_file(self):
        def handler(path: str, content: str) -> dict:
            try:
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return {"success": True, "path": path, "bytes": len(content)}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="write_file",
            description="创建或覆盖写入文件（自动创建目录）",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件绝对路径"},
                    "content": {"type": "string", "description": "要写入的全部内容"},
                },
                "required": ["path", "content"],
            },
            category="file",
        )(handler)

    # ── 3. edit_file（精准行级编辑，对标 Claude Code）──
    def _reg_edit_file(self):
        def handler(path: str, old_str: str, new_str: str, replace_all: bool = False) -> dict:
            try:
                if not os.path.exists(path):
                    return {"error": f"文件不存在: {path}"}
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                count = content.count(old_str)
                if count == 0:
                    return {"error": f"未找到匹配文本。请确认 old_str 与文件中内容完全一致（含空格/换行）"}
                if not replace_all and count > 1:
                    return {
                        "error": f"找到 {count} 处匹配，请设置 replace_all=true 或提供更精确的 old_str",
                        "matches": count,
                    }
                new_content = content.replace(old_str, new_str) if replace_all else content.replace(old_str, new_str, 1)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return {
                    "success": True,
                    "path": path,
                    "replacements": count if replace_all else 1,
                    "old_bytes": len(content),
                    "new_bytes": len(new_content),
                }
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="edit_file",
            description="精准替换文件中的文本片段（行级编辑）。old_str 必须与文件内容完全一致（含空格/换行）",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件绝对路径"},
                    "old_str": {"type": "string", "description": "要替换的原始文本，必须完全匹配"},
                    "new_str": {"type": "string", "description": "替换后的新文本"},
                    "replace_all": {"type": "boolean", "description": "是否替换所有匹配项", "default": False},
                },
                "required": ["path", "old_str", "new_str"],
            },
            category="file",
        )(handler)

    # ── 4. list_directory ──
    def _reg_list_directory(self):
        def handler(path: str, pattern: str = "*") -> dict:
            try:
                if not os.path.isdir(path):
                    return {"error": f"不是有效目录: {path}"}
                items = []
                for entry in sorted(os.listdir(path)):
                    full = os.path.join(path, entry)
                    is_dir = os.path.isdir(full)
                    items.append({
                        "name": entry,
                        "type": "dir" if is_dir else "file",
                        "size": os.path.getsize(full) if not is_dir else 0,
                    })
                if pattern != "*":
                    items = [i for i in items if fnmatch.fnmatch(i["name"], pattern)]
                return {"path": path, "count": len(items), "items": items[:200]}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="list_directory",
            description="列出目录内容。支持 fnmatch 过滤（如 *.py, test_*）",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "目录绝对路径"},
                    "pattern": {"type": "string", "description": "文件名通配符，默认 *", "default": "*"},
                },
                "required": ["path"],
            },
            category="file",
        )(handler)

    # ── 5. search_files（glob 搜索）──
    def _reg_search_files(self):
        def handler(directory: str, pattern: str, recursive: bool = True) -> dict:
            import glob
            try:
                if recursive:
                    search_pattern = os.path.join(directory, "**", pattern)
                else:
                    search_pattern = os.path.join(directory, pattern)
                results = glob.glob(search_pattern, recursive=recursive)
                return {"pattern": pattern, "count": len(results), "files": results[:100]}
            except Exception as e:
                return {"error": str(e)}

        self.registry.register(
            name="search_files",
            description="按通配符模式搜索文件（如 **/*.py 递归搜索所有 .py 文件）",
            parameters={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "搜索根目录"},
                    "pattern": {"type": "string", "description": "glob 模式（如 *.py, test_*.py, **/*.json）"},
                    "recursive": {"type": "boolean", "description": "是否递归子目录", "default": True},
                },
                "required": ["directory", "pattern"],
            },
            category="file",
        )(handler)

```
