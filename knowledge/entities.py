#!/usr/bin/env python3
"""Entity System — Track projects, agents, tools, tasks, workflows, lessons, failures."""

import json, time, sqlite3, hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

DATA_DIR = Path("/home/kali/HackWithAI/data/knowledge")
DATA_DIR.mkdir(parents=True, exist_ok=True)
ENTITY_DB = DATA_DIR / "entities.db"

ENTITY_TYPES = ["project", "agent", "tool", "task", "user",
                "document", "workflow", "lesson", "failure", "memory", "target"]


@dataclass
class Entity:
    id: str = ""
    name: str = ""
    entity_type: str = ""
    metadata: Dict = field(default_factory=dict)
    confidence: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    aliases: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, d: Dict) -> "Entity":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class EntityStore:
    """Persistent entity storage with deduplication."""

    def __init__(self, db_path: Path = ENTITY_DB):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY, name TEXT, entity_type TEXT,
                metadata TEXT, confidence REAL, timestamp TEXT,
                aliases TEXT
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_entity_name ON entities(name)")
            db.commit()

    def create(self, name: str, entity_type: str, metadata: Dict = {},
               confidence: float = 0.5, aliases: List[str] = []) -> Entity:
        eid = hashlib.md5(f"{name}{entity_type}{time.time()}".encode()).hexdigest()[:12]

        entity = Entity(id=eid, name=name, entity_type=entity_type,
                       metadata=metadata, confidence=confidence, aliases=aliases)

        with sqlite3.connect(self.db_path) as db:
            db.execute("INSERT INTO entities VALUES (?,?,?,?,?,?,?)",
                      (eid, name, entity_type, json.dumps(metadata),
                       confidence, entity.timestamp, json.dumps(aliases)))
            db.commit()
        return entity

    def get(self, entity_id: str) -> Optional[Entity]:
        with sqlite3.connect(self.db_path) as db:
            row = db.execute("SELECT * FROM entities WHERE id=?", (entity_id,)).fetchone()
        if not row:
            return None
        return Entity(id=row[0], name=row[1], entity_type=row[2],
                     metadata=json.loads(row[3]) if row[3] else {},
                     confidence=row[4], timestamp=row[5],
                     aliases=json.loads(row[6]) if row[6] else [])

    def find_by_name(self, name: str, entity_type: str = "") -> List[Entity]:
        with sqlite3.connect(self.db_path) as db:
            if entity_type:
                rows = db.execute("SELECT * FROM entities WHERE name LIKE ? AND entity_type=?",
                                 (f"%{name}%", entity_type)).fetchall()
            else:
                rows = db.execute("SELECT * FROM entities WHERE name LIKE ? OR aliases LIKE ?",
                                 (f"%{name}%", f"%{name}%")).fetchall()
        return [Entity(id=r[0], name=r[1], entity_type=r[2],
                      metadata=json.loads(r[3]) if r[3] else {},
                      confidence=r[4], timestamp=r[5],
                      aliases=json.loads(r[6]) if r[6] else []) for r in rows]

    def query(self, entity_type: str = "", keyword: str = "",
              min_confidence: float = 0.0, limit: int = 50) -> List[Entity]:
        sql = "SELECT * FROM entities WHERE 1=1"
        params: List = []
        if entity_type:
            sql += " AND entity_type=?"; params.append(entity_type)
        if keyword:
            sql += " AND (name LIKE ? OR metadata LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if min_confidence > 0:
            sql += " AND confidence >= ?"; params.append(min_confidence)
        sql += " ORDER BY timestamp DESC LIMIT ?"; params.append(limit)

        with sqlite3.connect(self.db_path) as db:
            rows = db.execute(sql, params).fetchall()
        return [Entity(id=r[0], name=r[1], entity_type=r[2],
                      metadata=json.loads(r[3]) if r[3] else {},
                      confidence=r[4], timestamp=r[5],
                      aliases=json.loads(r[6]) if r[6] else []) for r in rows]

    def update(self, entity_id: str, **kwargs):
        updates = {k: v for k, v in kwargs.items() if k in ("name", "confidence", "metadata", "aliases")}
        if not updates:
            return
        sets = ", ".join(f"{k}=?" for k in updates)
        vals = list(updates.values()) + [entity_id]
        with sqlite3.connect(self.db_path) as db:
            db.execute(f"UPDATE entities SET {sets} WHERE id=?", vals)
            db.commit()

    def stats(self) -> Dict:
        with sqlite3.connect(self.db_path) as db:
            total = db.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            types = db.execute("SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type").fetchall()
        return {"total": total, "by_type": {t[0]: t[1] for t in types},
                "db_size": f"{self.db_path.stat().st_size / 1024:.0f}KB" if self.db_path.exists() else "0KB"}


# ── Singleton ──────────────────────────────────────────────────────────
_store: Optional[EntityStore] = None

def get_entity_store() -> EntityStore:
    global _store
    if _store is None:
        _store = EntityStore()
    return _store
