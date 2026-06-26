#!/usr/bin/env python3
"""Evaluator + Score Engine — Multi-metric evaluation with ELO tracking."""

import json, time, sqlite3, math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

DATA_DIR = Path("/home/kali/HackWithAI/data/logs/autonomy")
DATA_DIR.mkdir(parents=True, exist_ok=True)
SCORE_DB = DATA_DIR / "scores.db"

EVAL_WEIGHTS = {"quality": 0.25, "completeness": 0.2, "speed": 0.15,
                "tool_usage": 0.15, "reasoning": 0.15, "cost": 0.1}


@dataclass
class Evaluation:
    subject: str
    category: str
    scores: Dict[str, float]
    overall: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class Evaluator:
    """Multi-metric evaluation for agents, tools, models, strategies."""

    def __init__(self):
        self.history: List[Evaluation] = []
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(SCORE_DB) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT, category TEXT,
                quality REAL, completeness REAL, speed REAL, tool_usage REAL,
                reasoning REAL, cost REAL, overall REAL, timestamp TEXT
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS elo_ratings (
                subject TEXT, category TEXT, elo REAL DEFAULT 1000,
                matches INTEGER DEFAULT 0, wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0,
                PRIMARY KEY (subject, category)
            )""")

    def evaluate(self, subject: str, category: str, metrics: Dict[str, float]) -> Evaluation:
        scores = {"quality": metrics.get("quality", 0.5),
                  "completeness": metrics.get("completeness", 0.5),
                  "speed": metrics.get("speed", 1.0 - metrics.get("latency_ms", 5000) / 10000),
                  "tool_usage": metrics.get("tool_success", 0.5),
                  "reasoning": metrics.get("reasoning_depth", 0.5),
                  "cost": 1.0 - metrics.get("cost_dollars", 0.01) * 10}

        overall = round(sum(scores[k] * EVAL_WEIGHTS.get(k, 0) for k in scores), 3)

        eval = Evaluation(subject=subject, category=category, scores=scores, overall=overall)
        self.history.append(eval)

        with sqlite3.connect(SCORE_DB) as db:
            db.execute("INSERT INTO evaluations VALUES (NULL,?,?,?,?,?,?,?,?,?,?)",
                      (subject, category, *[round(scores[k], 3) for k in
                       ("quality","completeness","speed","tool_usage","reasoning","cost")],
                       overall, eval.timestamp))
            db.commit()
        return eval

    def get_history(self, subject: str = "", category: str = "", limit: int = 20) -> List[Dict]:
        sql = "SELECT * FROM evaluations WHERE 1=1"
        params: List = []
        if subject: sql += " AND subject LIKE ?"; params.append(f"%{subject}%")
        if category: sql += " AND category=?"; params.append(category)
        sql += " ORDER BY timestamp DESC LIMIT ?"; params.append(limit)
        with sqlite3.connect(SCORE_DB) as db:
            db.row_factory = sqlite3.Row
            return [dict(r) for r in db.execute(sql, params)]


class ScoreEngine:
    """ELO-style rating system for agents, tools, models, strategies."""

    def __init__(self):
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(SCORE_DB) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS elo_ratings (
                subject TEXT, category TEXT, elo REAL DEFAULT 1000,
                matches INTEGER DEFAULT 0, wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0,
                PRIMARY KEY (subject, category)
            )""")
            db.commit()

    def get_elo(self, subject: str, category: str = "") -> float:
        with sqlite3.connect(SCORE_DB) as db:
            if category:
                row = db.execute("SELECT elo FROM elo_ratings WHERE subject=? AND category=?",
                                (subject, category)).fetchone()
            else:
                row = db.execute("SELECT AVG(elo) FROM elo_ratings WHERE subject=?",
                                (subject,)).fetchone()
        return row[0] if row and row[0] else 1000.0

    def update(self, subject: str, category: str, won: bool, opponent_elo: float = 1000):
        current = self.get_elo(subject, category)
        expected = 1.0 / (1.0 + math.pow(10, (opponent_elo - current) / 400))
        new_elo = current + 32 * ((1 if won else 0) - expected)

        with sqlite3.connect(SCORE_DB) as db:
            db.execute("""INSERT INTO elo_ratings VALUES (?,?,?,1,?,?)
                         ON CONFLICT(subject,category) DO UPDATE SET
                         elo=?, matches=matches+1, wins=wins+?, losses=losses+?""",
                      (subject, category, new_elo, 1 if won else 0, 0 if won else 1,
                       new_elo, 1 if won else 0, 0 if won else 1))
            db.commit()
        return new_elo

    def leaderboard(self, category: str = "", limit: int = 10) -> List[Dict]:
        with sqlite3.connect(SCORE_DB) as db:
            db.row_factory = sqlite3.Row
            if category:
                rows = db.execute("SELECT * FROM elo_ratings WHERE category=? ORDER BY elo DESC LIMIT ?",
                                 (category, limit)).fetchall()
            else:
                rows = db.execute("SELECT * FROM elo_ratings ORDER BY elo DESC LIMIT ?",
                                 (limit,)).fetchall()
        return [dict(r) for r in rows]

    def stats(self) -> Dict:
        with sqlite3.connect(SCORE_DB) as db:
            total = db.execute("SELECT COUNT(*) FROM elo_ratings").fetchone()[0]
            cats = db.execute("SELECT category, COUNT(*) FROM elo_ratings GROUP BY category").fetchall()
        return {"total_rated": total, "by_category": {c[0]: c[1] for c in cats}}
