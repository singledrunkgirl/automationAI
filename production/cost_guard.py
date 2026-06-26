#!/usr/bin/env python3
"""Cost Guard + Rate Limiter + Alert Engine — Cost tracking, rate protection, alerting."""

import json, time, sqlite3, threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from collections import defaultdict

DATA_DIR = Path("/home/kali/HackWithAI/data/logs/production")
DATA_DIR.mkdir(parents=True, exist_ok=True)
COST_DB = DATA_DIR / "costs.db"


class CostGuard:
    """Tracks OpenRouter usage, model costs, token consumption."""

    MODEL_COSTS = {
        "deepseek/deepseek-v4-flash": {"input": 0.10, "output": 0.40},
        "deepseek/deepseek-v4-pro": {"input": 0.50, "output": 2.00},
        "google/gemini-2.5-flash": {"input": 0.15, "output": 0.60},
        "google/gemini-2.5-pro": {"input": 1.25, "output": 5.00},
        "anthropic/claude-sonnet-4": {"input": 3.00, "output": 15.00},
        "moonshotai/kimi-k2.6": {"input": 0.95, "output": 4.00},
        "x-ai/grok-4.3": {"input": 2.00, "output": 8.00},
    }

    def __init__(self):
        self._init_db()
        self.budgets: Dict[str, float] = {"daily": 10.0, "monthly": 100.0}

    def _init_db(self):
        with sqlite3.connect(COST_DB) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS cost_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, model TEXT, task_id TEXT,
                input_tokens INTEGER, output_tokens INTEGER, cost_dollars REAL,
                agent TEXT, timestamp TEXT
            )""")
            db.commit()

    def record(self, model: str, task_id: str, input_tokens: int, output_tokens: int,
               agent: str = ""):
        pricing = self.MODEL_COSTS.get(model, {"input": 0.5, "output": 1.5})
        cost = (input_tokens / 1_000_000) * pricing["input"] + (output_tokens / 1_000_000) * pricing["output"]

        with sqlite3.connect(COST_DB) as db:
            db.execute("INSERT INTO cost_log VALUES (NULL,?,?,?,?,?,?,?)",
                      (model, task_id, input_tokens, output_tokens, round(cost, 6),
                       agent, datetime.now().isoformat()))
            db.commit()
        return round(cost, 6)

    def daily_cost(self) -> float:
        with sqlite3.connect(COST_DB) as db:
            row = db.execute("""SELECT COALESCE(SUM(cost_dollars),0) FROM cost_log
                               WHERE timestamp > date('now')""").fetchone()
        return round(row[0], 4) if row else 0.0

    def by_model(self) -> Dict[str, float]:
        with sqlite3.connect(COST_DB) as db:
            rows = db.execute("""SELECT model, SUM(cost_dollars) FROM cost_log
                                GROUP BY model ORDER BY 2 DESC""").fetchall()
        return {r[0]: round(r[1], 4) for r in rows}

    def is_over_budget(self) -> bool:
        return self.daily_cost() > self.budgets["daily"]

    def recommend_cheapest(self, task_tokens: int = 1000) -> str:
        sorted_models = sorted(self.MODEL_COSTS.items(), key=lambda x: x[1]["input"])
        return sorted_models[0][0] if sorted_models else "deepseek-v4-flash"

    def stats(self) -> Dict:
        return {"daily_cost": self.daily_cost(), "budget": self.budgets["daily"],
                "over_budget": self.is_over_budget(), "by_model": self.by_model()}


class RateLimiter:
    """Protects against API abuse, infinite loops, agent recursion, task flooding."""

    def __init__(self):
        self.counters: Dict[str, Dict] = defaultdict(lambda: {"count": 0, "reset": time.time()})
        self.limits = {"api_calls_per_min": 60, "agent_calls_per_min": 20,
                       "swarm_tasks_per_min": 10, "recursion_depth": 5, "task_flood": 50}
        self._lock = threading.Lock()

    def check(self, key: str, limit_key: str = "api_calls_per_min") -> bool:
        limit = self.limits.get(limit_key, 60)
        with self._lock:
            now = time.time()
            entry = self.counters[key]
            if now - entry["reset"] > 60:
                entry["count"] = 0
                entry["reset"] = now
            if entry["count"] >= limit:
                return False
            entry["count"] += 1
            return True

    def reset(self, key: str):
        with self._lock:
            self.counters[key] = {"count": 0, "reset": time.time()}

    def stats(self) -> Dict:
        return {"limits": self.limits, "active_counters": len(self.counters)}


class AlertEngine:
    """Sends alerts for cost spikes, latency, memory, failures, recovery events."""

    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.alert_history: List[Dict] = []

    def on(self, event: str, handler: Callable):
        self.handlers[event].append(handler)

    def fire(self, event: str, data: Dict = {}):
        alert = {"event": event, "data": data, "timestamp": datetime.now().isoformat()}
        self.alert_history.append(alert)
        for handler in self.handlers.get(event, []):
            try:
                handler(alert)
            except Exception:
                pass

    def check_and_alert(self, health: Dict, cost: Dict):
        if health.get("cpu_pct", 0) > 90:
            self.fire("cpu_spike", health)
        if cost.get("over_budget"):
            self.fire("budget_exceeded", cost)
        if health.get("errors", 0) > 5:
            self.fire("error_spike", health)

    def recent(self, limit: int = 20) -> List[Dict]:
        return self.alert_history[-limit:]

    def stats(self) -> Dict:
        return {"total_alerts": len(self.alert_history), "events": list(self.handlers.keys())}
