#!/usr/bin/env python3
"""
RAG Pipeline — Retrieval-Augmented Generation for HackWithAI.
Combines embedding engine + vector store for context-aware responses.
"""

import json, math, re, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from memory.embeddings.engine import EmbeddingEngine, get_embedding_engine
from memory.vector_store.store import VectorStore, get_vector_store

DATA_DIR = Path("/home/kali/HackWithAI/data/rag")
DATA_DIR.mkdir(parents=True, exist_ok=True)
RAG_LOG = DATA_DIR / "rag_queries.jsonl"


class RAGPipeline:
    """Full RAG pipeline: ingest → chunk → embed → store → retrieve → augment."""

    def __init__(self):
        self.embedding = get_embedding_engine()
        self.store = get_vector_store()
        self.query_history: List[Dict] = []

    # ── Ingestion ───────────────────────────────────────────────────────

    def ingest_text(self, text: str, doc_id: str = "", category: str = "general",
                    source: str = "manual", metadata: Dict = {}) -> str:
        """Ingest text into the RAG pipeline."""
        doc_id = doc_id or f"doc_{int(time.time())}_{hash(text) % 10000}"

        # Add to embedding engine (BM25)
        self.embedding.add(doc_id, text, metadata)

        # Add to vector store (SQLite + chunks)
        self.store.add(doc_id, text, category, source, metadata)

        return doc_id

    def ingest_file(self, filepath: str, category: str = "file") -> str:
        """Ingest a file into RAG."""
        try:
            with open(filepath, "r", errors="ignore") as f:
                text = f.read()
            doc_id = f"file_{Path(filepath).stem}_{int(time.time())}"
            return self.ingest_text(text, doc_id, category, source=filepath)
        except Exception as e:
            return f"error: {e}"

    def ingest_conversation(self, messages: List[Dict], chat_id: str) -> str:
        """Ingest chat messages as context."""
        text = "\n".join(f"{m.get('role','')}: {m.get('content','')[:500]}" for m in messages)
        return self.ingest_text(text, f"chat_{chat_id}", category="conversation", source=chat_id)

    # ── Retrieval ──────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = 5,
                 category: str = "", method: str = "bm25") -> List[Dict]:
        """Retrieve relevant context for a query."""
        if method == "bm25":
            results = self.embedding.search(query, top_k)
        else:
            results = self.store.search(query, category, top_k)

        # Log query
        self.query_history.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "results": len(results),
            "method": method,
        })
        if len(self.query_history) > 1000:
            self.query_history = self.query_history[-500:]

        return results[:top_k]

    def retrieve_combined(self, query: str, top_k: int = 5) -> List[Dict]:
        """Hybrid retrieval: combine BM25 + keyword results."""
        bm25_results = {r["doc_id"]: r for r in self.embedding.search(query, top_k * 2)}
        keyword_results = {r["doc_id"]: r for r in self.store.search(query, top_k=top_k * 2)}

        # Merge scores
        combined = {}
        all_ids = set(bm25_results) | set(keyword_results)
        for doc_id in all_ids:
            bm25_score = bm25_results.get(doc_id, {}).get("score", 0)
            kw_score = keyword_results.get(doc_id, {}).get("score", 0)
            combined[doc_id] = {
                **bm25_results.get(doc_id, {}),
                **keyword_results.get(doc_id, {}),
                "combined_score": round(bm25_score * 0.6 + kw_score * 0.4, 4),
            }

        return sorted(combined.values(), key=lambda x: x.get("combined_score", 0), reverse=True)[:top_k]

    # ── Augmentation ───────────────────────────────────────────────────

    def build_context(self, query: str, top_k: int = 5,
                      max_tokens: int = 4000, method: str = "hybrid") -> str:
        """Build context string for augmenting a prompt."""
        if method == "hybrid":
            results = self.retrieve_combined(query, top_k)
        else:
            results = self.retrieve(query, top_k, method=method)

        context_parts = []
        token_count = 0

        for r in results:
            text = r.get("text", "") or r.get("text_preview", "") or ""
            chunk_texts = []
            # Get chunks if available
            doc_id = r.get("doc_id", "")
            if doc_id:
                for chunk in self.store.get_chunks(doc_id):
                    chunk_texts.append(chunk.get("text", ""))

            full_text = text + "\n" + "\n".join(chunk_texts)
            words = len(full_text.split())
            if token_count + words <= max_tokens:
                context_parts.append(full_text)
                token_count += words
            else:
                break

        return "\n\n---\n\n".join(context_parts)

    def augment_prompt(self, base_prompt: str, query: str, top_k: int = 5) -> str:
        """Augment a prompt with RAG context."""
        context = self.build_context(query, top_k)
        if context:
            return f"""<context>
{context}
</context>

{base_prompt}

Use the context above to inform your response. Cite specific sources when applicable."""
        return base_prompt

    # ── Memory Compression ─────────────────────────────────────────────

    def compress_memories(self, doc_ids: List[str]) -> Dict:
        """Compress documents by keeping top-N chunks."""
        result = {"compressed": 0, "total_chunks_before": 0, "total_chunks_after": 0}
        for doc_id in doc_ids:
            chunks = self.store.get_chunks(doc_id)
            result["total_chunks_before"] += len(chunks)
            if len(chunks) > 10:
                # Keep first 3 and last 3 chunks
                kept = chunks[:3] + chunks[-3:]
                result["total_chunks_after"] += len(kept)
                result["compressed"] += 1
        return result

    # ── Stats ──────────────────────────────────────────────────────────

    def stats(self) -> Dict:
        return {
            "embedding_engine": self.embedding.stats(),
            "vector_store": self.store.stats(),
            "queries_today": len([q for q in self.query_history
                                  if q["timestamp"][:10] == datetime.now().strftime("%Y-%m-%d")]),
            "total_queries": len(self.query_history),
        }


# ── Singleton ──────────────────────────────────────────────────────────
_rag: Optional[RAGPipeline] = None

def get_rag() -> RAGPipeline:
    global _rag
    if _rag is None:
        _rag = RAGPipeline()
    return _rag


# ── CLI ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    rag = RAGPipeline()

    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "ingest":
        path = sys.argv[2]
        doc_id = rag.ingest_file(path)
        print(f"Ingested: {doc_id}")
    elif cmd == "search":
        query = " ".join(sys.argv[2:])
        results = rag.retrieve_combined(query)
        for r in results[:5]:
            print(f"  [{r.get('combined_score',0):.2f}] {r.get('text_preview','')[:100]}")
    elif cmd == "context":
        query = " ".join(sys.argv[2:])
        ctx = rag.build_context(query)
        print(f"Context length: {len(ctx)} chars")
        print(ctx[:500])
    elif cmd == "augment":
        query = sys.argv[2]
        prompt = sys.argv[3] if len(sys.argv) > 3 else "Answer the question."
        result = rag.augment_prompt(prompt, query)
        print(result[:1000])
    elif cmd == "stats":
        print(json.dumps(rag.stats(), indent=2))
    else:
        print("Commands: ingest <file> | search <query> | context <query> | augment <query> [prompt] | stats")
