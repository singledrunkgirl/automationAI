#!/usr/bin/env python3
"""
Vector Store — NumPy-based dense + SQLite-based sparse hybrid store.
Supports add, search, delete, and similarity queries.
"""

import json, sqlite3, math, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DATA_DIR = Path("/home/kali/HackWithAI/data/vector_store")
DATA_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DB_PATH = DATA_DIR / "vectors.sqlite"


class VectorStore:
    """Hybrid vector store — SQLite metadata + NumPy sparse vectors."""

    def __init__(self, db_path: Path = VECTOR_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS vectors (
                doc_id TEXT PRIMARY KEY,
                text_preview TEXT,
                category TEXT,
                source TEXT,
                tokens INTEGER,
                source_hash TEXT,
                added TEXT,
                last_accessed TEXT,
                access_count INTEGER DEFAULT 0
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT,
                chunk_index INTEGER,
                text TEXT,
                tokens INTEGER
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_category ON vectors(category)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_source ON vectors(source)")
            db.commit()

    def add(self, doc_id: str, text: str, category: str = "general",
            source: str = "manual", metadata: Dict = {}):
        tokens = len(text.split())
        now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        source_hash = str(hash(text))
        preview = text[:300]

        with sqlite3.connect(self.db_path) as db:
            db.execute("""INSERT OR REPLACE INTO vectors VALUES (?,?,?,?,?,?,?,?,?)""",
                       (doc_id, preview, category, source, tokens, source_hash, now, now, 0))

            # Chunk large documents
            if tokens > 500:
                chunks = self._chunk_text(text, 200)
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{doc_id}_chunk_{i}"
                    db.execute("INSERT OR REPLACE INTO chunks VALUES (?,?,?,?,?)",
                              (chunk_id, doc_id, i, chunk, len(chunk.split())))
            db.commit()

    def _chunk_text(self, text: str, chunk_size: int = 200) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i + chunk_size]))
        return chunks

    def search(self, query: str, category: str = "", top_k: int = 10) -> List[Dict]:
        """Simple keyword search with ranking."""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        with sqlite3.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            sql = "SELECT * FROM vectors WHERE " + " OR ".join(["text_preview LIKE ?"] * len(query_words))
            params = [f"%{w}%" for w in query_words]
            if category:
                sql += " AND category = ?"
                params.append(category)
            sql += " LIMIT ?"
            params.append(top_k * 3)

            rows = db.execute(sql, params).fetchall()

        results = []
        for row in rows:
            row_dict = dict(row)
            # Score by keyword density
            text = (row_dict.get("text_preview", "") or "").lower()
            score = sum(1 for w in query_words if w in text) / max(len(text.split()), 1) * 100
            row_dict["score"] = round(score, 4)
            results.append(row_dict)

        # Update access
        with sqlite3.connect(self.db_path) as db:
            now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
            for r in results[:top_k]:
                db.execute("UPDATE vectors SET last_accessed=?, access_count=access_count+1 WHERE doc_id=?",
                          (now, r["doc_id"]))
            db.commit()

        return sorted(results, key=lambda x: x.get("score", 0), reverse=True)[:top_k]

    def get_chunks(self, doc_id: str) -> List[Dict]:
        with sqlite3.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM chunks WHERE doc_id=? ORDER BY chunk_index", (doc_id,)).fetchall()
            return [dict(r) for r in rows]

    def delete(self, doc_id: str):
        with sqlite3.connect(self.db_path) as db:
            db.execute("DELETE FROM vectors WHERE doc_id=?", (doc_id,))
            db.execute("DELETE FROM chunks WHERE doc_id=?", (doc_id,))
            db.commit()

    def list_by_category(self, category: str = "") -> List[Dict]:
        with sqlite3.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            if category:
                rows = db.execute("SELECT doc_id,category,source,tokens,added FROM vectors WHERE category=? ORDER BY added DESC", (category,)).fetchall()
            else:
                rows = db.execute("SELECT doc_id,category,source,tokens,added FROM vectors ORDER BY added DESC LIMIT 100").fetchall()
            return [dict(r) for r in rows]

    def stats(self) -> Dict:
        with sqlite3.connect(self.db_path) as db:
            total = db.execute("SELECT COUNT(*) FROM vectors").fetchone()[0]
            chunks = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            cats = db.execute("SELECT category, COUNT(*) as cnt FROM vectors GROUP BY category ORDER BY cnt DESC").fetchall()
        return {
            "total_documents": total,
            "total_chunks": chunks,
            "categories": {c[0]: c[1] for c in cats},
            "db_size": f"{self.db_path.stat().st_size / 1024:.0f}KB" if self.db_path.exists() else "0KB",
        }


# ── Singleton ──────────────────────────────────────────────────────────
_store: Optional[VectorStore] = None

def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
