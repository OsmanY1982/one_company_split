# `iqra/core/_chunker.py`

> 路径：`iqra/core/_chunker.py` | 行数：200


---


```python
# -*- coding: utf-8 -*-
"""智能代码分块器 — 语义边界 + 重叠窗口 + 句子感知截断"""
from __future__ import annotations
import re
from pathlib import Path
from typing import List

from ._index_config import CODE_EXTENSIONS, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP


# 句子结束标记（用于非代码文本的智能截断）
_SENTENCE_END_RE = re.compile(r'[。！？.!?\n]{2,}|[。！？.!?]\s*\n')


class CodeChunker:
    """智能代码分块：按函数/类边界分割，支持缩进感知和重叠窗口"""

    # 函数/类定义模式（多种语言）
    _DEF_PATTERNS = [
        # Python（包含装饰器行）
        re.compile(r'^\s*(def |class |async def )', re.MULTILINE),
        # JavaScript/TypeScript
        re.compile(r'^\s*(function |class |const \w+ = \(.*\) =>|export (default )?(function|class) )', re.MULTILINE),
        # Java/Kotlin/Scala
        re.compile(r'^\s*(public |private |protected )?(class |interface |enum |fun |def )', re.MULTILINE),
        # Go
        re.compile(r'^\s*func ', re.MULTILINE),
        # Rust
        re.compile(r'^\s*(pub )?fn |^\s*(pub )?struct |^\s*(pub )?impl |^\s*(pub )?trait ', re.MULTILINE),
        # C/C++
        re.compile(r'^\s*\w[\w:*&<>\s]+\s+\w+\s*\([^)]*\)\s*\{', re.MULTILINE),
    ]

    # 文档标题模式
    _HEADING_RE = re.compile(r'^#{1,6}\s+.+$', re.MULTILINE)

    @classmethod
    def chunk_file(cls, content: str, file_path: str,
                   chunk_size: int = DEFAULT_CHUNK_SIZE,
                   overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[str]:
        """将文件内容分块"""
        ext = Path(file_path).suffix.lower()

        # 代码文件：尝试按函数/类边界分块
        if ext in CODE_EXTENSIONS:
            return cls._chunk_by_boundaries(content, chunk_size, overlap)

        # Markdown：按标题分块
        if ext in {".md", ".markdown", ".rst", ".txt"}:
            return cls._chunk_by_headings(content, chunk_size)

        # 默认：固定大小分块（句子边界感知）
        return cls._chunk_fixed(content, chunk_size, overlap)

    # ─── 边界模式分块 ─────────────────────────────────

    @classmethod
    def _chunk_by_boundaries(cls, content: str, chunk_size: int, overlap: int) -> List[str]:
        """按代码结构边界分块，含缩进感知和重叠窗口"""
        boundaries = cls._collect_boundaries(content)

        raw_chunks = []
        prev_tail = ""

        for i in range(len(boundaries)):
            start = boundaries[i]
            end = boundaries[i + 1] if i + 1 < len(boundaries) else len(content)
            block = content[start:end]

            # 块太大：优先缩进拆分，失败则固定大小拆分
            if len(block) > chunk_size * 2:
                sub_chunks = cls._try_indent_split(block, chunk_size) or \
                             cls._chunk_fixed(block, chunk_size, overlap)
                for sc in sub_chunks:
                    full = (prev_tail + "\n" + sc).strip() if prev_tail else sc.strip()
                    if len(full) > 50:
                        raw_chunks.append(full)
                    prev_tail = sc[-overlap:] if len(sc) > overlap * 2 else ""
                continue

            # 正常大小块：添加前一块的尾部上下文
            full = (prev_tail + "\n" + block).strip() if prev_tail else block.strip()
            if len(full) > 50:
                raw_chunks.append(full)
            prev_tail = block[-overlap:] if len(block) > overlap * 2 else ""

        return raw_chunks

    @classmethod
    def _collect_boundaries(cls, content: str) -> List[int]:
        """收集所有定义边界，含缩进感知的二级边界（类内方法）"""
        boundaries = {0}
        is_python_like = bool(re.search(r'^\s*(def |class )', content, re.MULTILINE))

        for pattern in cls._DEF_PATTERNS:
            for m in pattern.finditer(content):
                boundaries.add(m.start())

        # Python 类内方法：缩进 4 空格或 1 tab 以上的定义视为二级边界
        if is_python_like:
            for m in re.finditer(r'^\s{4,}(def |async def |class )', content, re.MULTILINE):
                boundaries.add(m.start())

        return sorted(boundaries)

    @classmethod
    def _try_indent_split(cls, block: str, chunk_size: int) -> List[str] | None:
        """对超大块尝试按缩进变化做二级拆分（类内方法/嵌套结构）"""
        # 找出块内所有缩进级别变化点（从高缩进跳到低缩进 = 方法边界）
        lines = block.split('\n')
        if len(lines) < 10:
            return None

        split_points = [0]
        prev_indent = 0
        for i, line in enumerate(lines):
            stripped = line
            indent = len(line) - len(line.lstrip())
            if indent == 0 and prev_indent > 0 and i > 1:
                split_points.append(i)
            prev_indent = indent

        if len(split_points) < 3:
            return None  # 拆分点太少，不值得二级拆分

        chunks = []
        for j in range(len(split_points)):
            s = split_points[j]
            e = split_points[j + 1] if j + 1 < len(split_points) else len(lines)
            sub = '\n'.join(lines[s:e]).strip()
            if len(sub) > 50:
                chunks.append(sub)

        return chunks if len(chunks) > 1 else None

    # ─── 标题模式分块 ─────────────────────────────────

    @classmethod
    def _chunk_by_headings(cls, content: str, chunk_size: int) -> List[str]:
        """按 Markdown 标题分块，超大段继续细分"""
        sections = cls._HEADING_RE.split(content)
        chunks = []
        current = ""
        for section in sections:
            merged = current + "\n" + section if current else section
            if len(merged) > chunk_size and current:
                chunks.append(current.strip())
                current = section
            else:
                current = merged

        if current.strip():
            # 最后一段如果仍超大，句子边界拆分
            if len(current) > chunk_size * 2:
                chunks.extend(cls._chunk_fixed(current, chunk_size, DEFAULT_CHUNK_OVERLAP))
            else:
                chunks.append(current.strip())

        return [c for c in chunks if len(c) > 30]

    # ─── 固定大小分块（句子边界感知） ──────────────────

    @classmethod
    def _chunk_fixed(cls, content: str, chunk_size: int, overlap: int) -> List[str]:
        """固定大小滑动窗口分块，优先在句子/段落边界处截断"""
        if len(content) <= chunk_size:
            return [content] if content.strip() else []

        chunks = []
        start = 0
        while start < len(content):
            end = min(start + chunk_size, len(content))
            if end < len(content):
                end = cls._find_best_cut(content, start, end, chunk_size)
            chunk = content[start:end].strip()
            if len(chunk) > 50:
                chunks.append(chunk)
            start = end - overlap if end < len(content) else end
        return chunks

    @classmethod
    def _find_best_cut(cls, content: str, start: int, end: int, chunk_size: int) -> int:
        """在 [start+chunk_size//2, end] 区间找最佳截断点"""
        search_start = start + chunk_size // 2
        window = content[search_start:end]

        # 优先级 1：空行（段落边界）
        for m in re.finditer(r'\n\s*\n', window):
            return search_start + m.start() + 1

        # 优先级 2：句子边界
        for m in _SENTENCE_END_RE.finditer(window):
            return search_start + m.start() + 1

        # 优先级 3：普通换行
        nl = content.rfind('\n', search_start, end)
        if nl > search_start:
            return nl + 1

        return end

```
