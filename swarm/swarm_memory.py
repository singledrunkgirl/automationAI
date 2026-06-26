#!/usr/bin/env python3
"""Swarm Memory — Shared state, context, and coordination records for parallel agents."""

import json, time, threading, sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Tuple
from collections import defaultdict

DATA_DIR = Path("/home/kali/HackWithAI/data/logs/swarm")
DATA_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DB = DATA_DIR / "swarm_memory.db"


class SwarmMemory:
    """Thread-safe shared memory for swarm agents."""

    def __init__(self):
        self._lock = threading.RLock()
        self._store: Dict[str, Any] = {}
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(MEMORY_DB) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS swarm_memory (
                key TEXT PRIMARY KEY, value TEXT, agent TEXT,
                access_count INTEGER DEFAULT 0, timestamp TEXT
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS swarm_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, agent TEXT,
                event TEXT, detail TEXT, timestamp TEXT
            )""")
            db.commit()

    def put(self, key: str, value: Any, agent: str = ""):
        with self._lock:
            self._store[key] = value
            with sqlite3.connect(MEMORY_DB) as db:
                db.execute("""INSERT OR REPLACE INTO swarm_memory VALUES (?,?,?,?,?)""",
                          (key, json.dumps(value) if not isinstance(value, str) else value,
                           agent, 1, datetime.now().isoformat()))
                db.commit()

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            val = self._store.get(key, default)
            with sqlite3.connect(MEMORY_DB) as db:
                db.execute("UPDATE swarm_memory SET access_count=access_count+1 WHERE key=?",
                          (key,))
                db.commit()
            return val

    def has(self, key: str) -> bool:
        return key in self._store

    def event(self, agent: str, event: str, detail: str = ""):
        with self._lock:
            with sqlite3.connect(MEMORY_DB) as db:
                db.execute("INSERT INTO swarm_events VALUES (NULL,?,?,?,?)",
                          (agent, event, detail, datetime.now().isoformat()))
                db.commit()

    def get_events(self, agent: str = "", limit: int = 50) -> List[Dict]:
        with sqlite3.connect(MEMORY_DB) as db:
            db.row_factory = sqlite3.Row
            if agent:
                rows = db.execute("SELECT * FROM swarm_events WHERE agent=? ORDER BY timestamp DESC LIMIT ?",
                                 (agent, limit)).fetchall()
            else:
                rows = db.execute("SELECT * FROM swarm_events ORDER BY timestamp DESC LIMIT ?",
                                 (limit,)).fetchall()
            return [dict(r) for r in rows]

    def clear(self):
        with self._lock:
            self._store.clear()

    def stats(self) -> Dict:
        with self._lock:
            with sqlite3.connect(MEMORY_DB) as db:
                keys = db.execute("SELECT COUNT(*) FROM swarm_memory").fetchone()[0]
                events = db.execute("SELECT COUNT(*) FROM swarm_events").fetchone()[0]
            return {"keys": keys, "events": events, "in_memory": len(self._store)}


# ── Singleton ──────────────────────────────────────────────────────────
_memory: Optional[SwarmMemory] = None

def get_swarm_memory() -> SwarmMemory:
    global _memory
    if _memory is None:
        _memory = SwarmMemory()
    return _memory


class VotingEngine:
    """Multi-method voting: majority, weighted, confidence, top-2 faceoff."""

    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold
        self.rounds: List[Dict] = []

    def majority_vote(self, votes: Dict[str, str]) -> Tuple[str, float]:
        """Simple majority vote. Returns winner and agreement percentage."""
        tally: Dict[str, int] = defaultdict(int)
        for voter, choice in votes.items():
            tally[choice] += 1

        total = len(votes)
        if not tally:
            return "", 0.0

        winner = max(tally, key=tally.get)
        agreement = tally[winner] / max(total, 1)
        return winner, agreement

    def weighted_vote(self, votes: Dict[str, str],
                      weights: Dict[str, float]) -> Tuple[str, float]:
        """Weighted vote where each voter has a weight."""
        tally: Dict[str, float] = defaultdict(float)
        for voter, choice in votes.items():
            w = weights.get(voter, 1.0)
            tally[choice] += w

        total_weight = sum(weights.get(v, 1.0) for v in votes)
        if not tally:
            return "", 0.0

        winner = max(tally, key=tally.get)
        agreement = tally[winner] / max(total_weight, 1)
        return winner, agreement

    def confidence_vote(self, options: Dict[str, Tuple[str, float]]) -> Tuple[str, float]:
        """Each option has (value, confidence). Highest confidence wins."""
        if not options:
            return "", 0.0
        winner = max(options, key=lambda k: options[k][1])
        return winner, options[winner][1]

    def run_round(self, votes: Dict[str, str], weights: Dict[str, float] = {},
                  round_num: int = 1) -> Dict:
        if weights:
            winner, agreement = self.weighted_vote(votes, weights)
        else:
            winner, agreement = self.majority_vote(votes)

        record = {"round": round_num, "winner": winner, "agreement": round(agreement, 2),
                  "votes": votes, "consensus": agreement >= self.threshold}
        self.rounds.append(record)
        return record

    def tiebreaker(self, tied: List[str], votes_history: List[Dict]) -> str:
        """Top-2 faceoff using round history."""
        scores = defaultdict(int)
        for rnd in votes_history:
            w = rnd.get("winner", "")
            if w in tied:
                scores[w] += 1
        return max(scores, key=scores.get) if scores else tied[0]

    def stats(self) -> Dict:
        return {"threshold": self.threshold, "rounds_run": len(self.rounds),
                "consensus_rate": round(sum(1 for r in self.rounds if r["consensus"]) / max(len(self.rounds), 1), 2)}
