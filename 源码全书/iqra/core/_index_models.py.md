# `iqra/core/_index_models.py`

> 路径：`iqra/core/_index_models.py` | 行数：24


---


```python
# -*- coding: utf-8 -*-
"""WorkspaceIndexer 数据模型"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class SearchResult:
    """搜索结果"""
    file_path: str           # 文件绝对路径
    chunk_index: int         # 块序号
    score: float             # BM25 分数
    snippet: str             # 匹配内容摘要（前 300 字符）
    file_type: str = ""      # 文件类型（py/js/ts/md/...）


@dataclass
class IndexStats:
    """索引统计"""
    total_files: int = 0
    total_chunks: int = 0
    total_size_bytes: int = 0
    last_build_time: float = 0.0
    skipped_patterns: List[str] = field(default_factory=list)

```
