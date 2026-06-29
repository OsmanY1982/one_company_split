# `iqra/core/knowledge_graph.py`

> 路径：`iqra/core/knowledge_graph.py` | 行数：273


---


```python
"""
iQra 语义记忆层 — 知识图谱存储
零外部依赖，仅用 Python 标准库 sqlite3。

三表设计：
  - entities:  实体节点（名称、类型、属性 JSON）
  - relations: 关系边（A→B 有向边，带类型和属性）
  - facts:     事实三元组（实体A - 关系 - 实体B，带置信度）

支持：upsert 去重、关联度评分（深度衰减）、广度优先子图遍历。
"""

import sqlite3
import json
import os
from typing import Optional, Any

_DEFAULT_DB = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_graph.db")


class KnowledgeGraph:
    """本地知识图谱存储引擎。"""

    def __init__(self, db_path: str = _DEFAULT_DB):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.row_factory = sqlite3.Row
        self._migrate()

    # ── schema ──────────────────────────────────────────────

    def _migrate(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS entities (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL,
                type       TEXT    DEFAULT '',
                properties TEXT    DEFAULT '{}',
                created_at TEXT    DEFAULT (datetime('now')),
                UNIQUE(name, type)
            );

            CREATE TABLE IF NOT EXISTS relations (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_a_id   INTEGER NOT NULL REFERENCES entities(id),
                entity_b_id   INTEGER NOT NULL REFERENCES entities(id),
                relation_type TEXT    NOT NULL,
                properties    TEXT    DEFAULT '{}',
                created_at    TEXT    DEFAULT (datetime('now')),
                UNIQUE(entity_a_id, entity_b_id, relation_type)
            );

            CREATE TABLE IF NOT EXISTS facts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_a_id INTEGER NOT NULL REFERENCES entities(id),
                relation_id INTEGER NOT NULL REFERENCES relations(id),
                entity_b_id INTEGER NOT NULL REFERENCES entities(id),
                confidence  REAL    DEFAULT 1.0,
                created_at  TEXT    DEFAULT (datetime('now')),
                UNIQUE(entity_a_id, relation_id, entity_b_id)
            );

            CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
            CREATE INDEX IF NOT EXISTS idx_relations_a   ON relations(entity_a_id);
            CREATE INDEX IF NOT EXISTS idx_relations_b   ON relations(entity_b_id);
            CREATE INDEX IF NOT EXISTS idx_facts_a       ON facts(entity_a_id);
            CREATE INDEX IF NOT EXISTS idx_facts_b       ON facts(entity_b_id);
        """)
        self._conn.commit()

    # ── helpers ─────────────────────────────────────────────

    @staticmethod
    def _json_dumps(obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False, default=str)

    @staticmethod
    def _json_loads(raw: Any) -> Any:
        if raw is None:
            return {}
        return json.loads(raw) if isinstance(raw, str) else raw

    # ── public API ──────────────────────────────────────────

    def upsert_entity(self, name: str, type: Optional[str] = None,
                      properties: Optional[dict] = None) -> int:
        """插入或更新实体，返回 entity_id。"""
        type_ = type or ""
        props = self._json_dumps(properties or {})
        row = self._conn.execute(
            "INSERT INTO entities (name, type, properties) VALUES (?, ?, ?)"
            " ON CONFLICT(name, type) DO UPDATE SET properties=excluded.properties"
            " RETURNING id",
            (name, type_, props),
        ).fetchone()
        self._conn.commit()
        return row["id"]

    def upsert_relation(self, entity_a: int, entity_b: int,
                        relation_type: str, properties: Optional[dict] = None) -> int:
        """插入或更新关系边，返回 relation_id。"""
        props = self._json_dumps(properties or {})
        row = self._conn.execute(
            "INSERT INTO relations (entity_a_id, entity_b_id, relation_type, properties)"
            " VALUES (?, ?, ?, ?)"
            " ON CONFLICT(entity_a_id, entity_b_id, relation_type)"
            " DO UPDATE SET properties=excluded.properties"
            " RETURNING id",
            (entity_a, entity_b, relation_type, props),
        ).fetchone()
        self._conn.commit()
        return row["id"]

    def add_fact(self, entity_a: int, relation: int, entity_b: int,
                 confidence: float = 1.0) -> int:
        """添加事实三元组，返回 fact_id。"""
        row = self._conn.execute(
            "INSERT INTO facts (entity_a_id, relation_id, entity_b_id, confidence)"
            " VALUES (?, ?, ?, ?)"
            " ON CONFLICT(entity_a_id, relation_id, entity_b_id)"
            " DO UPDATE SET confidence=excluded.confidence"
            " RETURNING id",
            (entity_a, relation, entity_b, confidence),
        ).fetchone()
        self._conn.commit()
        return row["id"]

    def search_entity(self, name: str) -> list[dict]:
        """按名称模糊搜索实体，返回匹配实体列表。"""
        rows = self._conn.execute(
            "SELECT * FROM entities WHERE name LIKE ? ORDER BY name",
            (f"%{name}%",),
        ).fetchall()
        return [self._row_to_entity(r) for r in rows]

    def query_related(self, entity_id: int, depth: int = 2) -> dict:
        """BFS 遍历获取子图，depth=0 为自身节点，每层衰减 0.5。"""
        visited: dict[int, float] = {entity_id: 1.0}
        frontier = [entity_id]
        edges: list[dict] = []
        nodes: dict[int, dict] = {}

        # 首节点
        root = self._conn.execute(
            "SELECT * FROM entities WHERE id=?", (entity_id,)
        ).fetchone()
        if root:
            nodes[entity_id] = self._row_to_entity(root)
            nodes[entity_id]["score"] = 1.0

        for d in range(depth):
            if not frontier:
                break
            next_frontier: list[int] = []
            score = 1.0 - (d + 1) * 0.5
            if score <= 0:
                break

            placeholders = ",".join("?" for _ in frontier)
            # 出边
            rows = self._conn.execute(
                f"SELECT * FROM relations WHERE entity_a_id IN ({placeholders})",
                frontier,
            ).fetchall()
            for rel in rows:
                rid = rel["entity_b_id"]
                if rid not in visited:
                    visited[rid] = score
                    next_frontier.append(rid)
                    e = self._conn.execute(
                        "SELECT * FROM entities WHERE id=?", (rid,)
                    ).fetchone()
                    if e:
                        nodes[rid] = self._row_to_entity(e)
                        nodes[rid]["score"] = score
                edges.append({"relation_id": rel["id"], "from": rel["entity_a_id"],
                              "to": rel["entity_b_id"], "type": rel["relation_type"],
                              "properties": self._json_loads(rel["properties"])})

            # 入边
            rows = self._conn.execute(
                f"SELECT * FROM relations WHERE entity_b_id IN ({placeholders})",
                frontier,
            ).fetchall()
            for rel in rows:
                lid = rel["entity_a_id"]
                if lid not in visited:
                    visited[lid] = score
                    next_frontier.append(lid)
                    e = self._conn.execute(
                        "SELECT * FROM entities WHERE id=?", (lid,)
                    ).fetchone()
                    if e:
                        nodes[lid] = self._row_to_entity(e)
                        nodes[lid]["score"] = score
                edges.append({"relation_id": rel["id"], "from": rel["entity_a_id"],
                              "to": rel["entity_b_id"], "type": rel["relation_type"],
                              "properties": self._json_loads(rel["properties"])})

            frontier = next_frontier

        return {"nodes": list(nodes.values()), "edges": edges}

    def get_entity_context(self, entity_name: str, depth: int = 2) -> dict:
        """
        获取实体的关联子图和事实。
        先搜索实体，再 BFS 遍历子图，最后拉取涉及子图中实体的所有事实。
        """
        matches = self.search_entity(entity_name)
        if not matches:
            return {"entity": None, "subgraph": {"nodes": [], "edges": []}, "facts": []}

        entity = matches[0]
        eid = entity["id"]
        subgraph = self.query_related(eid, depth)

        # 收集子图中出现的所有实体 id
        node_ids = [n["id"] for n in subgraph["nodes"]]
        if not node_ids:
            node_ids = [eid]

        placeholders = ",".join("?" for _ in node_ids)
        fact_rows = self._conn.execute(
            f"SELECT f.*, r.relation_type,"
            f" ea.name AS a_name, eb.name AS b_name"
            f" FROM facts f"
            f" JOIN relations r ON r.id = f.relation_id"
            f" JOIN entities  ea ON ea.id = f.entity_a_id"
            f" JOIN entities  eb ON eb.id = f.entity_b_id"
            f" WHERE f.entity_a_id IN ({placeholders})"
            f"    OR f.entity_b_id IN ({placeholders})",
            node_ids + node_ids,
        ).fetchall()

        facts = [self._row_to_fact(r) for r in fact_rows]

        return {"entity": entity, "subgraph": subgraph, "facts": facts}

    # ── internal ────────────────────────────────────────────

    def _row_to_entity(self, row: sqlite3.Row) -> dict:
        return {
            "id":         row["id"],
            "name":       row["name"],
            "type":       row["type"],
            "properties": self._json_loads(row["properties"]),
            "created_at": row["created_at"],
        }

    def _row_to_fact(self, row: sqlite3.Row) -> dict:
        return {
            "id":           row["id"],
            "entity_a":     row["a_name"],
            "relation":     row["relation_type"],
            "entity_b":     row["b_name"],
            "confidence":   row["confidence"],
            "entity_a_id":  row["entity_a_id"],
            "relation_id":  row["relation_id"],
            "entity_b_id":  row["entity_b_id"],
            "created_at":   row["created_at"],
        }

    def close(self) -> None:
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

```
