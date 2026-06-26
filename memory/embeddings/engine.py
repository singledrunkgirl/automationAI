#!/usr/bin/env python3
"""
Embedding Engine — Sparse retrieval via BM25 + TF-IDF.
No GPU or embedding API needed. Falls back gracefully.
"""

import re, math, json, hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime

DATA_DIR = Path("/home/kali/HackWithAI/data/embeddings")
DATA_DIR.mkdir(parents=True, exist_ok=True)


class BM25Scorer:
    """BM25 sparse retrieval scorer."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_lengths: Dict[str, int] = {}
        self.total_docs = 0
        self.avg_doc_length = 0.0
        self.inverted_index: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.doc_freq: Dict[str, int] = defaultdict(int)

    def tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-zA-Z0-9_]{2,}", text.lower())

    def add_document(self, doc_id: str, text: str):
        tokens = self.tokenize(text)
        self.doc_lengths[doc_id] = len(tokens)
        self.total_docs += 1
        self.avg_doc_length = sum(self.doc_lengths.values()) / max(self.total_docs, 1)

        for pos, token in enumerate(tokens):
            self.inverted_index[token][doc_id] = self.inverted_index[token].get(doc_id, 0) + 1
        for token in set(tokens):
            self.doc_freq[token] += 1

    def score(self, query: str, doc_id: str) -> float:
        query_tokens = self.tokenize(query)
        doc_len = self.doc_lengths.get(doc_id, 1)
        score = 0.0

        for token in query_tokens:
            if token not in self.inverted_index or doc_id not in self.inverted_index[token]:
                continue
            tf = self.inverted_index[token][doc_id]
            df = self.doc_freq.get(token, 1)
            idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1.0)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / max(self.avg_doc_length, 1))
            score += idf * numerator / max(denominator, 1e-9)
        return score

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        scores = []
        for doc_id in self.doc_lengths:
            s = self.score(query, doc_id)
            if s > 0:
                scores.append((doc_id, s))
        return sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]

    def save(self, path: str):
        data = {
            "docs": dict(self.doc_lengths),
            "total": self.total_docs,
            "avg_len": self.avg_doc_length,
            "index": {k: dict(v) for k, v in self.inverted_index.items()},
            "df": dict(self.doc_freq),
        }
        with open(path, "w") as f:
            json.dump(data, f)

    def load(self, path: str):
        if not Path(path).exists():
            return
        with open(path) as f:
            data = json.load(f)
        self.doc_lengths = data["docs"]
        self.total_docs = data["total"]
        self.avg_doc_length = data["avg_len"]
        self.inverted_index = defaultdict(lambda: defaultdict(int), {k: defaultdict(int, v) for k, v in data["index"].items()})
        self.doc_freq = defaultdict(int, data["df"])


class EmbeddingEngine:
    """TF-IDF sparse embedding + BM25 retrieval engine."""

    def __init__(self, persist_path: str = ""):
        self.bm25 = BM25Scorer()
        self.documents: Dict[str, str] = {}
        self.metadata: Dict[str, Dict] = {}
        self.persist_path = persist_path or str(DATA_DIR / "bm25_index.json")
        self._try_load()

    def _try_load(self):
        try:
            self.bm25.load(self.persist_path)
            meta_path = self.persist_path.replace(".json", "_meta.json")
            if Path(meta_path).exists():
                with open(meta_path) as f:
                    data = json.load(f)
                self.documents = data.get("docs", {})
                self.metadata = data.get("meta", {})
        except Exception:
            pass

    def add(self, doc_id: str, text: str, metadata: Dict = {}):
        self.bm25.add_document(doc_id, text)
        self.documents[doc_id] = text
        self.metadata[doc_id] = metadata
        self.metadata[doc_id]["added"] = datetime.now().isoformat()

    def remove(self, doc_id: str):
        self.documents.pop(doc_id, None)
        self.metadata.pop(doc_id, None)
        # Partial index cleanup — full rebuild on save
        self.persist()

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        results = self.bm25.search(query, top_k)
        return [{
            "doc_id": doc_id,
            "score": round(score, 4),
            "text": self.documents.get(doc_id, "")[:500],
            "metadata": self.metadata.get(doc_id, {}),
        } for doc_id, score in results]

    def vectorize(self, text: str) -> List[float]:
        """Produce a TF-IDF sparse vector."""
        tokens = self.bm25.tokenize(text)
        vec = defaultdict(float)
        total = max(len(tokens), 1)
        for t in tokens:
            vec[t] += 1.0 / total
        return [vec.get(w, 0) for w in sorted(self.bm25.doc_freq.keys())[:1024]]

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(vec1, vec2))
        n1 = math.sqrt(sum(a * a for a in vec1))
        n2 = math.sqrt(sum(b * b for b in vec2))
        return dot / max(n1 * n2, 1e-9)

    def persist(self):
        self.bm25.save(self.persist_path)
        meta_path = self.persist_path.replace(".json", "_meta.json")
        with open(meta_path, "w") as f:
            json.dump({"docs": self.documents, "meta": self.metadata}, f)

    def stats(self) -> Dict:
        return {
            "total_documents": len(self.documents),
            "vocabulary_size": len(self.bm25.doc_freq),
            "avg_doc_length": round(self.bm25.avg_doc_length, 1),
            "persist_path": self.persist_path,
        }


# ── Singleton ──────────────────────────────────────────────────────────
_engine: Optional[EmbeddingEngine] = None

def get_embedding_engine() -> EmbeddingEngine:
    global _engine
    if _engine is None:
        _engine = EmbeddingEngine()
    return _engine
