#!/usr/bin/env python3
"""Graph Store — Unified entity + relationship graph with queries."""

import json, time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from .entities import Entity, EntityStore, get_entity_store
from .relationships import RelationshipStore, get_relationship_store, RELATIONSHIP_TYPES

DATA_DIR = Path("/home/kali/HackWithAI/data/knowledge")
DATA_DIR.mkdir(parents=True, exist_ok=True)


class EntityResolver:
    """Merges duplicate entities and maintains aliases."""

    def __init__(self, store: EntityStore):
        self.store = store

    def merge(self, keep_id: str, merge_id: str) -> bool:
        """Merge merge_id into keep_id."""
        keep = self.store.get(keep_id)
        merged = self.store.get(merge_id)
        if not keep or not merged:
            return False

        # Combine metadata
        keep.metadata.update(merged.metadata)
        keep.confidence = max(keep.confidence, merged.confidence)
        keep.aliases = list(set(keep.aliases + merged.aliases + [merged.name]))

        self.store.update(keep_id, metadata=keep.metadata,
                         confidence=keep.confidence, aliases=keep.aliases)
        return True

    def find_duplicates(self, name: str, entity_type: str = "") -> List[Entity]:
        """Find potential duplicate entities."""
        matches = self.store.find_by_name(name, entity_type)
        return [m for m in matches if name.lower() in m.name.lower() or
                any(name.lower() in a.lower() for a in m.aliases)]


class ContextLinker:
    """Automatically connects entities based on context patterns."""

    def __init__(self, entity_store: EntityStore, rel_store: RelationshipStore):
        self.entities = entity_store
        self.rels = rel_store

    def link(self, source_name: str, source_type: str,
             target_name: str, target_type: str, rel_type: str) -> str:
        s = self._get_or_create(source_name, source_type)
        t = self._get_or_create(target_name, target_type)
        return self.rels.create(s.id, t.id, rel_type)

    def _get_or_create(self, name: str, entity_type: str) -> Entity:
        existing = self.entities.find_by_name(name, entity_type)
        if existing:
            return existing[0]
        return self.entities.create(name, entity_type)

    def auto_link_mission(self, task_id: str, agent: str, tool: str,
                          target: str, success: bool):
        """Auto-link a completed mission: agent→tool→target→result."""
        self.link(agent, "agent", tool, "tool", "USES")
        self.link(tool, "tool", target, "target", "TARGETS")
        if success:
            self.link(agent, "agent", f"success_{task_id}", "memory", "GENERATED")
        else:
            self.link(agent, "agent", f"failure_{task_id}", "failure", "FAILED_WITH")


class KnowledgeGraph:
    """Unified knowledge graph — entities + relationships + queries."""

    def __init__(self):
        self.entities = get_entity_store()
        self.relationships = get_relationship_store()
        self.resolver = EntityResolver(self.entities)
        self.linker = ContextLinker(self.entities, self.relationships)

    def add_entity(self, name: str, entity_type: str, **kwargs) -> Entity:
        return self.entities.create(name, entity_type, **kwargs)

    def link(self, source: str, target: str, rel_type: str) -> str:
        return self.relationships.create(source, target, rel_type)

    def query_related(self, entity_id: str, depth: int = 2) -> List[Dict]:
        return self.relationships.get_connected(entity_id, depth)

    def find_path(self, source_name: str, target_name: str) -> List[str]:
        s = self.entities.find_by_name(source_name)
        t = self.entities.find_by_name(target_name)
        if not s or not t:
            return []
        return self.relationships.find_path(s[0].id, t[0].id)

    def get_recommendations(self, entity_type: str) -> Dict:
        entities = self.entities.query(entity_type=entity_type)
        if not entities:
            return {"count": 0, "recommended": []}

        # Find most-connected entities
        scores: Dict[str, float] = {}
        for e in entities[:20]:
            rels = self.relationships.query(e.id)
            scores[e.name] = len(rels)

        return {
            "count": len(entities),
            "recommended": sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10],
        }

    def stats(self) -> Dict:
        return {
            "entities": self.entities.stats(),
            "relationships": self.relationships.stats(),
        }


# ── Singleton ──────────────────────────────────────────────────────────
_kg: Optional[KnowledgeGraph] = None

def get_knowledge_graph() -> KnowledgeGraph:
    global _kg
    if _kg is None:
        _kg = KnowledgeGraph()
    return _kg
