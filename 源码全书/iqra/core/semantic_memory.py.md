# `iqra/core/semantic_memory.py`

> 路径：`iqra/core/semantic_memory.py` | 行数：275


---


```python
"""
iQra 语义记忆引擎 — 从对话中提取实体/关系并存入知识图谱。

零 LLM 依赖，全部基于启发式规则：
  - 英文大写词序列 → 实体
  - 中文引号内容 → 实体
  - 「实体A + 动词 + 实体B」→ 关系
  - 显式陈述句（"X 是 Y"）→ fact

检索：BM25 全文匹配 + 知识图谱 BFS 关联子图。
"""

import re
import math
from collections import defaultdict
from typing import Optional

from iqra.core.knowledge_graph import KnowledgeGraph


# ── 启发式提取正则 ─────────────────────────────────────────

_RE_CAPITAL_WORD = re.compile(
    r'\b[A-Z][a-z]*(?:[A-Z][a-z]*)+\b'           # PascalCase / camelCase
    r'|\b[A-Z]{2,}(?:\d+)?\b'                     # 全大写缩写
)

_RE_CHINESE_QUOTE = re.compile(r'[「『""]([^」』""]{1,40})[」』""]')

_RE_CHINESE_QUOTE_SINGLE = re.compile(r'[『\u2018]([^\u2019]{1,40})[\u2019』]')

# 常见中文停用动词（不被当作关系候选）
_STOP_VERBS = {
    "是", "的", "了", "在", "有", "和", "与", "或", "也", "就", "都",
    "而", "及", "把", "被", "让", "从", "以", "对", "向", "到", "为",
    "上", "下", "中", "内", "外", "前", "后", "能", "会", "要", "可以",
    "这个", "那个", "什么", "怎么", "如何", "为什么", "哪个",
}

# 实体字符集：中文字符 + 英文字母数字 + 连字符
_EW = r'[\w\u4e00-\u9fff-]'

# 关系陈述模式：(pattern, relation_type)
_RELATION_PATTERNS = [
    (re.compile(rf'({_EW}{{1,24}}?)\s*(?:是一种|属于一种|定义为)\s*({_EW}{{1,24}}?)(?:[，,。；;]|$)'), "是一种"),
    (re.compile(rf'({_EW}{{1,24}}?)\s*(?:包含|包括|含有)\s*({_EW}{{1,24}}?)(?:[，,。；;]|$)'), "包含"),
    (re.compile(rf'({_EW}{{1,24}}?)\s*(?:使用|采用|利用|基于|调用|依赖)\s*({_EW}{{1,24}}?)(?:[，,。；;]|$)'), "使用"),
    (re.compile(rf'({_EW}{{1,24}}?)\s*(?:定义|实现|提供|输出|负责)\s*({_EW}{{1,24}}?)(?:[，,。；;]|$)'), "负责"),
    (re.compile(rf'({_EW}{{1,24}}?)\s*(?:属于|归于|归属)\s*({_EW}{{1,24}}?)(?:[，,。；;]|$)'), "属于"),
    (re.compile(rf'({_EW}{{1,24}}?)\s*(?:构成|组成)\s*({_EW}{{1,24}}?)(?:[，,。；;]|$)'), "构成"),
]

# 清洗提取到的实体名称
_CLEAN_ENTITY = re.compile(r'^[\s,，。；;：:！!？?、""''「」『』()（）\[\]【】]+|[\s,，。；;：:！!？?、""''「」『』()（）\[\]【】]+$')

# 实体质量过滤
_INVALID_ENTITY = re.compile(
    r'^[\s,，。；;：:！!？?、""''「」『』()（）\[\]【】\d]+$'  # 纯标点/数字
    r'|^[的地得了着过吗呢吧啊]{1,2}$'                     # 纯助词
    r'|^[这那哪什怎][么样个些]$'                          # 纯指示词
)

def _is_valid_entity(name: str) -> bool:
    """过滤无效实体名称。"""
    name = _CLEAN_ENTITY.sub("", name).strip()
    if len(name) < 2 or len(name) > 40:
        return False
    if _INVALID_ENTITY.match(name):
        return False
    if name in _STOP_VERBS:
        return False
    return True


# ── 简易 BM25 ──────────────────────────────────────────────

class _BM25:
    """极简 BM25 实现，零依赖。"""

    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.docs: list[dict] = []          # [{id, name, type, tokens}]
        self.doc_len: list[int] = []
        self.avgdl: float = 0.0
        self.df: dict[str, int] = defaultdict(int)
        self._tokenize = re.compile(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+').findall

    def add(self, doc_id: int, text: str, meta: dict) -> None:
        tokens = [t.lower() for t in self._tokenize(text) if len(t) > 1]
        self.docs.append({"id": doc_id, **meta, "tokens": tokens})
        self.doc_len.append(len(tokens))
        seen: set[str] = set()
        for t in tokens:
            if t not in seen:
                self.df[t] += 1
                seen.add(t)
        total = sum(self.doc_len)
        self.avgdl = total / max(len(self.doc_len), 1)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        q_tokens = [t.lower() for t in self._tokenize(query) if len(t) > 1]
        if not q_tokens or not self.docs:
            return []
        N = len(self.docs)
        scores: list[tuple[float, dict]] = []
        for i, doc in enumerate(self.docs):
            score = 0.0
            dl = self.doc_len[i]
            for qt in q_tokens:
                n = self.df.get(qt, 0)
                if n == 0:
                    continue
                tf = doc["tokens"].count(qt)
                idf = math.log((N - n + 0.5) / (n + 0.5) + 1.0)
                score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            if score > 0:
                scores.append((score, {k: v for k, v in doc.items() if k != "tokens"}))
        scores.sort(key=lambda x: -x[0])
        return [s[1] for s in scores[:top_k]]


# ── SemanticMemory ─────────────────────────────────────────

class SemanticMemory:
    """语义记忆引擎：对话 → 实体关系提取 → 知识图谱存储 → 检索。"""

    def __init__(self, db_path: Optional[str] = None):
        self._kg = KnowledgeGraph(db_path) if db_path else KnowledgeGraph()
        self._bm25 = _BM25()
        self._rebuild_bm25()

    # ── 公开 API ────────────────────────────────────────────

    def extract_from_message(self, role: str, content: str) -> list[dict]:
        """从单条消息中提取实体和关系，自动 upsert 到知识图谱。"""
        entities: list[dict] = []
        text = f"{role}: {content}" if role else content

        # 1. 英文大写词 → 实体
        for m in _RE_CAPITAL_WORD.finditer(content):
            name = m.group(0)
            if _is_valid_entity(name):
                eid = self._kg.upsert_entity(name, type="概念")
                entities.append({"id": eid, "name": name, "source": "capital_word"})

        # 2. 中文引号内容 → 实体
        for m in _RE_CHINESE_QUOTE.finditer(content):
            name = _CLEAN_ENTITY.sub("", m.group(1)).strip()
            if _is_valid_entity(name):
                eid = self._kg.upsert_entity(name, type="概念")
                entities.append({"id": eid, "name": name, "source": "quote"})

        # 3. 关系陈述模式 → relation + fact
        for pattern, rel_type in _RELATION_PATTERNS:
            for m in pattern.finditer(content):
                a_raw = _CLEAN_ENTITY.sub("", m.group(1)).strip()
                b_raw = _CLEAN_ENTITY.sub("", m.group(2)).strip()
                if not _is_valid_entity(a_raw) or not _is_valid_entity(b_raw):
                    continue
                ea = self._kg.upsert_entity(a_raw, type="概念")
                eb = self._kg.upsert_entity(b_raw, type="概念")
                rel_id = self._kg.upsert_relation(ea, eb, rel_type)
                self._kg.add_fact(ea, rel_id, eb, confidence=0.8)
                entities.append({"id": ea, "name": a_raw, "source": "relation_a"})
                entities.append({"id": eb, "name": b_raw, "source": "relation_b"})

        # 4. 更新 BM25 索引（去重）
        seen_ids = set()
        for ent in entities:
            if ent["id"] not in seen_ids:
                seen_ids.add(ent["id"])
                self._bm25.add(ent["id"], ent["name"],
                               {"name": ent["name"], "type": "概念"})  # type: ignore

        return entities

    def extract_from_conversation(self, messages: list[dict]) -> list[dict]:
        """批量处理对话历史。messages 每项含 role/content。"""
        all_entities: list[dict] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            all_entities.extend(self.extract_from_message(role, content))
        return all_entities

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        BM25 全文检索 + 知识图谱关联检索。
        返回包含 entity、score、subgraph 的结果列表。
        """
        bm25_results = self._bm25.search(query, top_k=top_k)
        results: list[dict] = []
        for item in bm25_results:
            eid = item["id"]
            subgraph = self._kg.query_related(eid, depth=1)
            # 尝试从子图中获取事实
            entity = self._kg.search_entity(item["name"])
            context = {}
            if entity:
                ctx = self._kg.get_entity_context(item["name"], depth=1)
                context = {"facts": ctx.get("facts", [])}
            results.append({
                "entity": item,
                "subgraph": subgraph,
                "context": context,
            })
        return results

    def get_context(self, query: str, top_k: int = 3) -> str:
        """
        返回格式化上下文文本，可直接注入 LLM prompt。
        格式：
          相关实体：A, B, C
          关联事实：
            - A 使用 B
            - B 是一种 C
        """
        results = self.search(query, top_k=top_k)
        if not results:
            return ""

        lines: list[str] = []
        all_facts: list[str] = []
        entity_names: list[str] = []
        seen_names: set[str] = set()

        for r in results:
            name = r["entity"]["name"]
            if name not in seen_names:
                seen_names.add(name)
                entity_names.append(name)
            for f in r.get("context", {}).get("facts", []):
                fact_str = f"- {f['entity_a']} {f['relation']} {f['entity_b']}"
                if fact_str not in all_facts:
                    all_facts.append(fact_str)

        if entity_names:
            lines.append(f"相关实体：{', '.join(entity_names)}")
        if all_facts:
            lines.append("关联事实：")
            lines.extend(all_facts[:10])

        return "\n".join(lines)

    def stats(self) -> dict:
        """返回存储统计。"""
        import sqlite3
        conn = self._kg._conn  # noqa: SLF001
        entity_count = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        relation_count = conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
        fact_count = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
        return {
            "entity_count": entity_count,
            "relation_count": relation_count,
            "fact_count": fact_count,
        }

    # ── 内部 ────────────────────────────────────────────────

    def _rebuild_bm25(self) -> None:
        """从知识图谱重建 BM25 索引（启动时调用）。"""
        entities = self._kg._conn.execute("SELECT id, name, type FROM entities").fetchall()  # noqa: SLF001
        for row in entities:
            self._bm25.add(row["id"], row["name"],
                           {"name": row["name"], "type": row["type"] or "概念"})

    def close(self) -> None:
        self._kg.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

```
