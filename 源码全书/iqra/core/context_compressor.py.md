# `iqra/core/context_compressor.py`

> 路径：`iqra/core/context_compressor.py` | 行数：157


---


```python
"""
ContextCompressor — 上下文压缩器。三级渐进压缩：L1 去噪 → L2 摘要化 → L3 关键词。
接收 ContextFragment 或 dict 列表，输出 CompressedContext。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

_FRAG_LIKE = Union[Dict[str, Any], Any]

# 预编译正则
_RE_BLANK_LINE = re.compile(r'\n{3,}')
_RE_COMMENT_LINE = re.compile(r'^\s*#.*$', re.MULTILINE)
_RE_MULTI_SPACE = re.compile(r' {2,}')
_RE_HEADING = re.compile(r'^##\s+', re.MULTILINE)


@dataclass
class CompressedFragment:
    source: str
    content: str
    level: str  # 'L0' / 'L1' / 'L2' / 'L3'


@dataclass
class CompressedContext:
    original_chars: int
    compressed_chars: int
    fragments: List[CompressedFragment] = field(default_factory=list)

    @property
    def ratio(self) -> float:
        return self.compressed_chars / max(self.original_chars, 1)


def _get(f: _FRAG_LIKE, key: str, default: Any = "") -> Any:
    return f.get(key, default) if isinstance(f, dict) else getattr(f, key, default)


def _l1_clean(text: str) -> str:
    """L1 去噪声：去注释、合并空行、压缩空格、去首尾空白。"""
    t = _RE_COMMENT_LINE.sub("", text)
    t = _RE_BLANK_LINE.sub("\n\n", t)
    t = _RE_MULTI_SPACE.sub(" ", t)
    return t.strip()


def _summarize_long(text: str) -> str:
    """L2 摘要：提取前 3 个 ## 标题 + 每段首句（最多 5 段）。"""
    headings: List[str] = []
    firsts: List[str] = []
    for para in re.split(r'\n\s*\n', text):
        s = para.strip()
        if not s or len(s) < 10:
            continue
        if s.startswith("#"):
            if _RE_HEADING.match(s) and len(headings) < 3:
                headings.append(s)
            continue
        sent = re.split(r'[。！？\n]', s)[0].strip()
        if sent and len(sent) > 5:
            firsts.append(sent)
    parts: List[str] = []
    if headings:
        parts.append("\n".join(headings))
    if firsts:
        parts.append("; ".join(firsts[:5]))
    return "\n".join(parts) if parts else text[:300].strip()


class ContextCompressor:
    """三级渐进上下文压缩器。不可用 jieba 时 L3 自动降级 L2。"""

    def __init__(self):
        self._jieba_ok: Optional[bool] = None

    def compress(self, fragments: List[_FRAG_LIKE], target_chars: int = 3000) -> CompressedContext:
        org = sum(len(_get(f, "content")) for f in fragments)

        if org <= target_chars:
            return CompressedContext(org, org, [
                CompressedFragment(_get(f, "source"), _get(f, "content"), "L0")
                for f in fragments
            ])

        for level_fn, level_name in [(self._l1, "L1"), (self._l2, "L2"), (self._l3, "L3")]:
            cfrags = level_fn(fragments)
            total = sum(len(c.content) for c in cfrags)
            if total <= target_chars:
                return CompressedContext(org, total, cfrags)
        # 保底：L3 结果即使超标也返回
        cfrags = self._l3(fragments)
        return CompressedContext(org, sum(len(c.content) for c in cfrags), cfrags)

    # ── 三级压缩 ────────────────────────────────────────────

    def _l1(self, fragments: List[_FRAG_LIKE]) -> List[CompressedFragment]:
        result: List[CompressedFragment] = []
        for f in fragments:
            cleaned = _l1_clean(_get(f, "content"))
            if cleaned:
                result.append(CompressedFragment(_get(f, "source"), cleaned, "L1"))
        return result

    def _l2(self, fragments: List[_FRAG_LIKE]) -> List[CompressedFragment]:
        result: List[CompressedFragment] = []
        for f in fragments:
            content = _get(f, "content")
            if len(content) <= 2000:
                cleaned = _l1_clean(content)
                if cleaned:
                    result.append(CompressedFragment(_get(f, "source"), cleaned, "L2"))
            else:
                result.append(CompressedFragment(_get(f, "source"), _summarize_long(content), "L2"))
        return result

    def _l3(self, fragments: List[_FRAG_LIKE]) -> List[CompressedFragment]:
        if not self._ensure_jieba():
            return self._l2(fragments)
        result: List[CompressedFragment] = []
        for f in fragments:
            content = _get(f, "content")
            if len(content) <= 300:
                s = content.strip()
                if s:
                    result.append(CompressedFragment(_get(f, "source"), s, "L3"))
            else:
                kw = self._keywords(content)
                if kw:
                    result.append(CompressedFragment(
                        _get(f, "source"), f"[关键词] {' '.join(kw)}", "L3"))
                elif content.strip():
                    result.append(CompressedFragment(
                        _get(f, "source"), content[:200].strip(), "L3"))
        return result

    # ── 内部 ────────────────────────────────────────────────

    def _ensure_jieba(self) -> bool:
        if self._jieba_ok is None:
            try:
                import jieba  # noqa: F401
                self._jieba_ok = True
            except ImportError:
                self._jieba_ok = False
        return self._jieba_ok

    @staticmethod
    def _keywords(text: str, top_n: int = 10) -> List[str]:
        try:
            import jieba.analyse
            return jieba.analyse.extract_tags(text, topK=top_n)
        except Exception:
            return []

```
