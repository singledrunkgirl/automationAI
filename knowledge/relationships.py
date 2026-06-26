#!/usr/bin/env python3
"""Relationship Engine — USES, CREATED, DEPENDS_ON, FAILED_WITH, IMPROVED_BY, etc."""

import json, sqlite3, time, hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

DATA_DIR = Path("/home/kali/HackWithAI/data/knowledge")
DATA_DIR.mkdir(parents=True, exist_ok=True)
EDGE_DB = DATA_DIR / "relationships.db"

RELATIONSHIP_TYPES = [
    "USES", "CREATED", "DEPENDS_ON", "RELATED_TO",
    "FAILED_WITH", "IMPROVED_BY", "GENERATED", "PART_OF", "LINKED_TO"
]

class RelationshipStore:
    """Persistent edge/relationship storage."""

    def __init__(self, db_path: Path = EDGE_DB):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY, source_id TEXT, target_id TEXT,
                rel_type TEXT, confidence REAL, metadata TEXT, timestamp TEXT
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_rel_source ON relationships(source_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_rel_target ON relationships(target_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships(rel_type)")
            db.commit()

    def create(self, source_id: str, target_id: str, rel_type: str,
               confidence: float = 0.7, metadata: Dict = {}) -> str:
        rid = hashlib.md5(f"{source_id}{target_id}{rel_type}{time.time()}".encode()).hexdigest()[:12]
        with sqlite3.connect(self.db_path) as db:
            db.execute("INSERT INTO relationships VALUES (?,?,?,?,?,?,?)",
                      (rid, source_id, target_id, rel_type, confidence,
                       json.dumps(metadata), datetime.now().isoformat()))
            db.commit()
        return rid

    def query(self, entity_id: str, rel_type: str = "", direction: str = "both",
              limit: int = 50) -> List[Dict]:
        sql = "SELECT * FROM relationships WHERE "
        params: List = []
        if direction == "out":
            sql += "source_id=?"; params.append(entity_id)
        elif direction == "in":
            sql += "target_id=?"; params.append(entity_id)
        else:
            sql += "(source_id=? OR target_id=?)"; params.extend([entity_id, entity_id])

        if rel_type:
            sql += " AND rel_type=?"; params.append(rel_type)

        sql += " ORDER BY timestamp DESC LIMIT ?"; params.append(limit)

        with sqlite3.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(sql, params).fetchall()

        results = []
        for r in rows:
            row_dict = dict(r)
            row_dict["metadata"] = json.loads(row_dict.get("metadata", "{}") or "{}")
            results.append(row_dict)
        return results

    def get_connected(self, entity_id: str, depth: int = 2) -> List[Dict]:
        """BFS traversal."""
        visited: set = {entity_id}
        frontier = [entity_id]
        results: List[Dict] = []

        for _ in range(depth):
            next_frontier: List[str] = []
            for current in frontier:
                for rel in self.query(current):
                    other = rel["target_id"] if rel["source_id"] == current else rel["source_id"]
                    if other not in visited:
                        visited.add(other)
                        next_frontier.append(other)
                        results.append({"entity_id": other, "relationship": rel["rel_type"],
                                       "confidence": rel["confidence"]})
            frontier = next_frontier
        return results

    def find_path(self, source: str, target: str, max_depth: int = 4) -> List[str]:
        """BFS path finding."""
        if source == target:
            return [source]
        from collections import deque
        q = deque([(source, [source])])
        visited = {source}
        while q:
            node, path = q.popleft()
            if len(path) > max_depth:
                continue
            for rel in self.query(node):
                other = rel["target_id"] if rel["source_id"] == node else rel["source_id"]
                if other == target:
                    return path + [target]
                if other not in visited:
                    visited.add(other)
                    q.append((other, path + [other]))
        return []

    def stats(self) -> Dict:
        with sqlite3.connect(self.db_path) as db:
            total = db.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]
            types = db.execute("SELECT rel_type, COUNT(*) FROM relationships GROUP BY rel_type").fetchall()
        return {"total": total, "by_type": {t[0]: t[1] for t in types},
                "db_size": f"{self.db_path.stat().st_size / 1024:.0f}KB" if self.db_path.exists() else "0KB"}


# ── Singleton ──────────────────────────────────────────────────────────
_rel_store: Optional[RelationshipStore] = None

def get_relationship_store() -> RelationshipStore:
    global _rel_store
    if _rel_store is None:
        _rel_store = RelationshipStore()
    return _rel_store
