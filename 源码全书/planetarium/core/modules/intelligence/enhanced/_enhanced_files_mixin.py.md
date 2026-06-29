# `planetarium/core/modules/intelligence/enhanced/_enhanced_files_mixin.py`

> 路径：`planetarium/core/modules/intelligence/enhanced/_enhanced_files_mixin.py` | 行数：141


---


```python
# -*- coding: utf-8 -*-
"""
增强 AI 工具集 — 文件操作 Mixin（file_read / file_write / multi_search）
"""

import os
from typing import Dict, Any

# 与基座模块共享的路径常量，从基座导入以保持一致性
from ._enhanced_base import _safe_path, _PROJECT_ROOT


class EnhancedFilesMixin:
    """文件操作工具集"""

    def _tool_file_read(self, path: str, encoding: str = "auto") -> Dict[str, Any]:
        """读取文件"""
        path = _safe_path(path)
        if not os.path.exists(path):
            return {"success": False, "error": f"文件不存在: {path}"}
        if os.path.isdir(path):
            return {"success": False, "error": f"路径是目录: {path}"}

        content = None
        errors_list = []

        if encoding == "auto":
            for enc in ["utf-8", "gbk", "gb2312", "latin-1"]:
                try:
                    with open(path, "r", encoding=enc) as f:
                        content = f.read()
                    encoding = enc
                    break
                except (UnicodeDecodeError, UnicodeError):
                    errors_list.append(enc)
                    continue
            if content is None:
                return {"success": False, "error": f"无法解码文件，尝试编码: {errors_list}"}
        else:
            with open(path, "r", encoding=encoding) as f:
                content = f.read()

        # 截断过长的内容
        if len(content) > 50000:
            content = content[:50000] + f"\n\n... [已截断，共 {len(content)} 字符]"

        file_size = os.path.getsize(path)
        return {
            "success": True,
            "content": content,
            "path": path,
            "encoding": encoding,
            "size": file_size,
            "size_human": f"{file_size / 1024:.1f} KB" if file_size < 1048576 else f"{file_size / 1048576:.1f} MB",
        }

    def _tool_file_write(self, path: str, content: str) -> Dict[str, Any]:
        """写入文件（原子写入）"""
        path = _safe_path(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, path)

        file_size = os.path.getsize(path)
        return {
            "success": True,
            "path": path,
            "size": file_size,
            "message": f"写入成功，{file_size} 字节",
        }

    def _tool_multi_search(self, query: str, directory: str = "auto") -> Dict[str, Any]:
        """本地全文搜索"""
        if directory == "auto":
            directory = _PROJECT_ROOT
        directory = _safe_path(directory)

        if not os.path.isdir(directory):
            return {"success": False, "error": f"目录不存在: {directory}"}

        query_lower = query.lower()
        results = []
        max_results = 50
        searched = 0

        exclude_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", ".idea", ".DS_Store", "dist", "build", "__MACOSX"}

        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]

            for filename in files:
                if len(results) >= max_results:
                    break
                searched += 1
                filepath = os.path.join(root, filename)

                name_match = query_lower in filename.lower()

                content_match = False
                matched_line = ""
                if not name_match:
                    _, ext = os.path.splitext(filename)
                    ext = ext.lower()
                    text_exts = {".py", ".txt", ".md", ".json", ".xml", ".html", ".css", ".js",
                                 ".yaml", ".yml", ".toml", ".ini", ".cfg", ".csv", ".log", ".sh"}
                    if ext in text_exts:
                        try:
                            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                                for line_num, line in enumerate(f, 1):
                                    if query_lower in line.lower():
                                        content_match = True
                                        matched_line = line.strip()[:200]
                                        break
                        except Exception:
                            pass

                if name_match or content_match:
                    match_type = "文件名匹配" if name_match else "内容匹配"
                    results.append({
                        "path": filepath,
                        "filename": filename,
                        "match_type": match_type,
                        "matched_line": matched_line if content_match else "",
                        "size": os.path.getsize(filepath),
                    })

            if len(results) >= max_results:
                break

        return {
            "success": True,
            "query": query,
            "directory": directory,
            "results": results,
            "count": len(results),
            "searched": searched,
            "message": f"搜索 {searched} 个文件，找到 {len(results)} 个结果",
        }

```
