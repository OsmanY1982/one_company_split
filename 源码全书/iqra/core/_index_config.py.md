# `iqra/core/_index_config.py`

> 路径：`iqra/core/_index_config.py` | 行数：56


---


```python
# -*- coding: utf-8 -*-
"""WorkspaceIndexer 配置常量"""

# 默认跳过的目录/文件模式
DEFAULT_SKIP_PATTERNS = [
    # VCS
    ".git", ".svn", ".hg",
    # 依赖
    "node_modules", "vendor", "bower_components",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "venv", ".venv", "env", ".env", "virtualenv",
    ".tox", ".eggs", "*.egg-info",
    # 构建产物
    "dist", "build", "target", "out", ".next", ".nuxt",
    "*.pyc", "*.pyo", "*.class", "*.o", "*.so", "*.dylib",
    "*.exe", "*.dll",
    # 缓存
    ".cache", ".npm", ".yarn",
    # IDE
    ".idea", ".vscode", ".vs", "*.sublime-*",
    # 大文件
    "*.zip", "*.tar.gz", "*.7z", "*.rar",
    "*.jpg", "*.jpeg", "*.png", "*.gif", "*.svg", "*.ico",
    "*.mp3", "*.mp4", "*.wav", "*.avi", "*.mov",
    "*.pdf", "*.docx", "*.xlsx", "*.pptx",
    "*.ttf", "*.woff", "*.woff2", "*.eot",
    "*.lock", "package-lock.json", "yarn.lock",
    # 数据文件
    "*.csv", "*.tsv", "*.jsonl",
]

# 需要索引的代码文件扩展名
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs",
    ".java", ".kt", ".kts", ".scala",
    ".c", ".cpp", ".h", ".hpp", ".cc", ".cxx",
    ".go", ".rs", ".rb", ".php",
    ".swift", ".m", ".mm",
    ".sh", ".bash", ".zsh", ".fish",
    ".sql", ".r", ".lua",
}

# 需要索引的文本文档扩展名
DOC_EXTENSIONS = {
    ".md", ".markdown", ".rst", ".txt",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".json", ".xml", ".html", ".css", ".scss", ".less",
    ".dockerfile", ".makefile", ".cmake",
}

# 分块大小（字符数）
DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 400  # 上下文重叠窗口，确保跨块语义不丢失

# 最大文件大小（字节），超过此大小不分块索引
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

```
