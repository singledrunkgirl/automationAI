#!/usr/bin/env python3
"""Performance Tracker + Optimizers — Prompt, Model, Tool, Strategy optimization."""

import json, time, sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

DATA_DIR = Path("/home/kali/HackWithAI/data/logs/autonomy")
DATA_DIR.mkdir(parents=True, exist_ok=True)
PERF_DB = DATA_DIR / "performance.db"

from .evaluator import ScoreEngine, Evaluator


class PerformanceTracker:
    """Tracks task metrics, latency, token usage, quality over time."""

    def __init__(self):
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(PERF_DB) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, agent TEXT,
                model TEXT, tool TEXT, strategy TEXT, latency_ms INTEGER,
                tokens_used INTEGER, cost_dollars REAL, success INTEGER,
                quality_score REAL, timestamp TEXT
            )""")
            db.commit()

    def record(self, task_id: str, agent: str = "", model: str = "", tool: str = "",
               strategy: str = "", latency_ms: int = 0, tokens: int = 0,
               cost: float = 0.0, success: bool = True, quality: float = 0.5):
        with sqlite3.connect(PERF_DB) as db:
            db.execute("INSERT INTO metrics VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?)",
                      (task_id, agent, model, tool, strategy, latency_ms, tokens,
                       cost, 1 if success else 0, quality, datetime.now().isoformat()))
            db.commit()

    def get_stats(self, subject: str = "", field: str = "agent", limit: int = 10) -> List[Dict]:
        with sqlite3.connect(PERF_DB) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(f"""
                SELECT {field}, COUNT(*) as tasks, ROUND(AVG(latency_ms)) as avg_latency_ms,
                ROUND(AVG(tokens_used)) as avg_tokens, ROUND(AVG(cost_dollars),4) as avg_cost,
                ROUND(AVG(success)*100,1) as success_rate, ROUND(AVG(quality_score),2) as avg_quality
                FROM metrics WHERE {field} != '' GROUP BY {field}
                ORDER BY avg_quality DESC LIMIT ?
            """, (limit,)).fetchall()
        return [dict(r) for r in rows]

    def trend(self, field: str = "agent", days: int = 7) -> List[Dict]:
        with sqlite3.connect(PERF_DB) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(f"""
                SELECT date(timestamp) as day, {field}, COUNT(*) as tasks,
                ROUND(AVG(success)*100,1) as success_rate, ROUND(AVG(quality_score),2) as avg_quality
                FROM metrics WHERE {field} != ''
                AND timestamp > datetime('now','-{days} days')
                GROUP BY day, {field} ORDER BY day DESC LIMIT 50
            """).fetchall()
        return [dict(r) for r in rows]


class PromptOptimizer:
    """Tracks prompt patterns and recommends improvements."""

    def __init__(self):
        self.prompt_history: List[Dict] = []

    def record(self, prompt: str, agent: str = "", success: bool = True,
               quality: float = 0.5, response: str = ""):
        self.prompt_history.append({
            "prompt": prompt[:500], "agent": agent, "success": success,
            "quality": quality, "response": response[:500],
            "timestamp": datetime.now().isoformat(),
        })
        if len(self.prompt_history) > 200:
            self.prompt_history = self.prompt_history[-100:]

    def get_best_prompts(self, agent: str = "", top_k: int = 5) -> List[Dict]:
        filtered = [p for p in self.prompt_history if (not agent or p["agent"] == agent) and p["success"]]
        sorted_prompts = sorted(filtered, key=lambda x: x["quality"], reverse=True)
        return sorted_prompts[:top_k]

    def get_worst_patterns(self, agent: str = "") -> List[str]:
        failures = [p for p in self.prompt_history if (not agent or p["agent"] == agent) and not p["success"]]
        patterns: Dict[str, int] = defaultdict(int)
        for f in failures:
            words = f["prompt"].lower().split()
            for w in words:
                if len(w) > 4:
                    patterns[w] += 1
        return sorted(patterns, key=patterns.get, reverse=True)[:10]

    def recommend(self, agent: str = "") -> str:
        best = self.get_best_prompts(agent, 3)
        if best:
            return f"Recommended patterns: {', '.join(p['prompt'][:80] for p in best)}"
        return "Not enough data for recommendations."


class StrategyManager:
    """Compares and selects best attack strategies."""

    STRATEGIES = ["single-agent", "multi-agent", "debate", "fast", "deep"]

    def __init__(self, tracker: PerformanceTracker, scores: ScoreEngine):
        self.tracker = tracker
        self.scores = scores

    def compare(self) -> List[Dict]:
        results = []
        for strat in self.STRATEGIES:
            elo = self.scores.get_elo(strat, "strategy")
            stats = self.tracker.get_stats(strat, "strategy")
            results.append({"strategy": strat, "elo": round(elo), "stats": stats[0] if stats else {}})
        return sorted(results, key=lambda x: x["elo"], reverse=True)

    def select_best(self) -> str:
        comparison = self.compare()
        return comparison[0]["strategy"] if comparison else "debate"

    def auto_select(self, context: Dict) -> str:
        """Auto-select strategy based on task context."""
        complexity = context.get("complexity", 3)
        urgency = context.get("urgency", 3)
        if complexity > 7:
            return "deep"
        if complexity > 4:
            return "debate"
        if urgency > 7:
            return "fast"
        return "multi-agent"


class ToolOptimizer:
    """Ranks tools by performance and disables underperformers."""

    def __init__(self, tracker: PerformanceTracker):
        self.tracker = tracker
        self.disabled: set = set()

    def rank(self) -> List[Dict]:
        return self.tracker.get_stats(field="tool", limit=20)

    def disable(self, tool: str):
        self.disabled.add(tool)

    def enable(self, tool: str):
        self.disabled.discard(tool)

    def is_enabled(self, tool: str) -> bool:
        return tool not in self.disabled

    def recommend_best(self, phase: str = "", top_k: int = 3) -> List[str]:
        ranked = self.rank()
        return [r["tool"] for r in ranked[:top_k]]
