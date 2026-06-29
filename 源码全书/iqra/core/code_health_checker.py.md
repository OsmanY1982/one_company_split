# `iqra/core/code_health_checker.py`

> 路径：`iqra/core/code_health_checker.py` | 行数：215


---


```python
"""
CodeHealthChecker — 代码健康巡检器
扫描拆分版项目，产出 HealthReport。
"""

import ast
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

# --- 配置 ---
PROJECT_ROOT = Path("/Volumes/D盘工作区/一人公司拆分版/one_company_split")
REPORTS_DIR = PROJECT_ROOT / "iqra" / "data" / "health_reports"
OVER_SIZE_LIMIT = 500
STUB_PATTERN = re.compile(r"^from\s+(\S+)\s+import\s+\*\s*$")
STUB_MAX_LINES = 5


@dataclass
class HealthReport:
    """代码健康报告数据类。"""
    timestamp: float = field(default_factory=time.time)
    file_count: int = 0
    oversized_files: list[dict] = field(default_factory=list)   # [{path, lines}]
    dead_code: list[str] = field(default_factory=list)           # 未被引用的模块路径
    broken_imports: list[dict] = field(default_factory=list)     # [{path, error}]
    stale_stubs: list[dict] = field(default_factory=list)        # [{stub_path, target, exists}]
    stale_docs: list[dict] = field(default_factory=list)         # [{md_path, py_path, md_mtime, py_mtime}]
    summary: str = ""


class CodeHealthChecker:
    """代码健康巡检器。"""

    def __init__(self):
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self._last_report: HealthReport | None = None
        self._py_files: list[Path] = []

    # ------------------------------------------------------------------ 公开方法

    def run_full_check(self) -> HealthReport:
        self._scan_py_files()
        r = HealthReport(file_count=len(self._py_files))
        r.oversized_files = self._check_oversized()
        r.dead_code = self._check_dead_code()
        r.broken_imports = self._check_broken_imports()
        r.stale_stubs = self._check_stale_stubs()
        r.stale_docs = self._check_stale_docs()
        r.summary = self._build_summary(r)
        self._last_report = r
        return r

    def run_quick_check(self) -> HealthReport:
        self._scan_py_files()
        r = HealthReport(file_count=len(self._py_files))
        r.oversized_files = self._check_oversized()
        r.broken_imports = self._check_broken_imports()
        r.summary = self._build_summary(r)
        self._last_report = r
        return r

    def get_last_report(self) -> HealthReport | None:
        if self._last_report:
            return self._last_report
        reports = sorted(REPORTS_DIR.glob("health_*.json"), reverse=True)
        if not reports:
            return None
        return self._load_report(reports[0])

    def save_report(self, report: HealthReport) -> Path:
        ts = time.strftime("%Y%m%d_%H%M%S", time.localtime(report.timestamp))
        path = REPORTS_DIR / f"health_{ts}.json"
        path.write_text(json.dumps(self._report_to_dict(report), ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    # ------------------------------------------------------------------ 巡检项

    def _check_oversized(self) -> list[dict]:
        results = []
        for fp in self._py_files:
            try:
                lines = sum(1 for _ in open(fp, encoding="utf-8", errors="ignore"))
            except OSError:
                lines = 0
            if lines > OVER_SIZE_LIMIT:
                results.append({"path": str(fp), "lines": lines})
        results.sort(key=lambda x: x["lines"], reverse=True)
        return results

    def _check_dead_code(self) -> list[str]:
        # 构建 {stem: full_path} 与被引用 stem 集合
        module_map: dict[str, str] = {}
        imported: set[str] = set()
        for fp in self._py_files:
            stem = fp.stem
            module_map[stem] = str(fp)
            try:
                tree = ast.parse(fp.read_text(encoding="utf-8", errors="ignore"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported.add(node.module.split(".")[0])
        dead = []
        for stem, path in module_map.items():
            if stem in ("__init__", "main"):
                continue
            if stem not in imported:
                dead.append(path)
        return sorted(dead)

    def _check_broken_imports(self) -> list[dict]:
        results = []
        for fp in self._py_files:
            try:
                ast.parse(fp.read_text(encoding="utf-8", errors="ignore"))
            except SyntaxError as e:
                results.append({"path": str(fp), "error": str(e)})
        return results

    def _check_stale_stubs(self) -> list[dict]:
        results = []
        for fp in self._py_files:
            try:
                lines_list = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue
            if len(lines_list) > STUB_MAX_LINES:
                continue
            body = "\n".join(lines_list).strip()
            m = STUB_PATTERN.match(body)
            if not m:
                continue
            target = m.group(1)
            # 验证目标模块是否存在：把 . 换成 / 查找
            target_path = PROJECT_ROOT / (target.replace(".", "/") + ".py")
            exists = target_path.exists()
            results.append({"stub_path": str(fp), "target": target, "exists": exists})
        return results

    def _check_stale_docs(self) -> list[dict]:
        results = []
        md_dir = PROJECT_ROOT / "项目全书"
        if not md_dir.exists():
            return results
        md_files = {p.stem: p for p in md_dir.rglob("*.md")}
        py_files = {p.stem: p for p in self._py_files}
        for stem, md_path in md_files.items():
            if stem not in py_files:
                continue
            py_path = py_files[stem]
            md_mtime = md_path.stat().st_mtime
            py_mtime = py_path.stat().st_mtime
            if md_mtime < py_mtime:
                results.append({
                    "md_path": str(md_path),
                    "py_path": str(py_path),
                    "md_mtime": md_mtime,
                    "py_mtime": py_mtime,
                })
        return results

    # ------------------------------------------------------------------ 辅助

    def _scan_py_files(self) -> None:
        self._py_files = sorted(p for p in PROJECT_ROOT.rglob("*.py") if p.is_file())

    def _build_summary(self, r: HealthReport) -> str:
        parts = [f"总文件: {r.file_count}"]
        if r.oversized_files:
            parts.append(f"超行文件: {len(r.oversized_files)}")
        if r.dead_code:
            parts.append(f"零引用死代码: {len(r.dead_code)}")
        if r.broken_imports:
            parts.append(f"导入链断裂: {len(r.broken_imports)}")
        if r.stale_stubs:
            parts.append(f"存根文件: {len(r.stale_stubs)}（其中失效 {sum(1 for s in r.stale_stubs if not s['exists'])}）")
        if r.stale_docs:
            parts.append(f"过期文档: {len(r.stale_docs)}")
        if len(parts) == 1:
            parts.append("一切正常")
        return "；".join(parts)

    def _report_to_dict(self, r: HealthReport) -> dict:
        return {
            "timestamp": r.timestamp,
            "file_count": r.file_count,
            "oversized_files": r.oversized_files,
            "dead_code": r.dead_code,
            "broken_imports": r.broken_imports,
            "stale_stubs": r.stale_stubs,
            "stale_docs": r.stale_docs,
            "summary": r.summary,
        }

    def _load_report(self, path: Path) -> HealthReport:
        data = json.loads(path.read_text(encoding="utf-8"))
        return HealthReport(
            timestamp=data.get("timestamp", 0),
            file_count=data.get("file_count", 0),
            oversized_files=data.get("oversized_files", []),
            dead_code=data.get("dead_code", []),
            broken_imports=data.get("broken_imports", []),
            stale_stubs=data.get("stale_stubs", []),
            stale_docs=data.get("stale_docs", []),
            summary=data.get("summary", ""),
        )

```
