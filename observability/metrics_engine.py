#!/usr/bin/env python3
"""
Metrics Engine + Benchmark Engine — Track latency, tokens, usage, and run benchmarks.
"""

import json, time, sqlite3, threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict

DATA_DIR = Path("/home/kali/HackWithAI/data/logs/observability")
DATA_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DB = DATA_DIR / "metrics.db"


class MetricsEngine:
    """Tracks latency, token usage, memory, agent calls, workflow duration, tool usage."""

    def __init__(self):
        self._init_db()
        self._lock = threading.Lock()
        self.buffer: List[Dict] = []

    def _init_db(self):
        with sqlite3.connect(METRICS_DB) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, name TEXT,
                value REAL, unit TEXT, metadata TEXT, timestamp TEXT
            )""")
            db.commit()

    def record(self, category: str, name: str, value: float, unit: str = "ms",
               metadata: Dict = {}):
        with self._lock:
            self.buffer.append({"category": category, "name": name, "value": value,
                               "unit": unit, "metadata": metadata,
                               "timestamp": datetime.now().isoformat()})
            if len(self.buffer) > 20:
                self._flush()

    def _flush(self):
        with self._lock:
            if not self.buffer:
                return
            with sqlite3.connect(METRICS_DB) as db:
                for m in self.buffer:
                    db.execute("INSERT INTO metrics VALUES (NULL,?,?,?,?,?,?)",
                              (m["category"], m["name"], m["value"], m["unit"],
                               json.dumps(m["metadata"]), m["timestamp"]))
                db.commit()
            self.buffer.clear()

    def query(self, category: str = "", name: str = "", limit: int = 50) -> List[Dict]:
        self._flush()
        sql = "SELECT * FROM metrics WHERE 1=1"
        params: List = []
        if category: sql += " AND category=?"; params.append(category)
        if name: sql += " AND name=?"; params.append(name)
        sql += " ORDER BY timestamp DESC LIMIT ?"; params.append(limit)
        with sqlite3.connect(METRICS_DB) as db:
            db.row_factory = sqlite3.Row
            return [dict(r) for r in db.execute(sql, params)]

    def summary(self, category: str = "") -> Dict:
        self._flush()
        with sqlite3.connect(METRICS_DB) as db:
            if category:
                rows = db.execute("""SELECT name, COUNT(*) as cnt, ROUND(AVG(value),2) as avg,
                                    MIN(value) as min, MAX(value) as max
                                    FROM metrics WHERE category=? GROUP BY name""",
                                 (category,)).fetchall()
            else:
                rows = db.execute("""SELECT category, name, COUNT(*) as cnt,
                                    ROUND(AVG(value),2) as avg
                                    FROM metrics GROUP BY category, name""").fetchall()
        return {"by_name": [{"name": r[0], "count": r[1], "avg": r[2]}
                           for r in rows]}

    def stats(self) -> Dict:
        self._flush()
        with sqlite3.connect(METRICS_DB) as db:
            total = db.execute("SELECT COUNT(*) FROM metrics").fetchone()[0]
            cats = db.execute("SELECT category, COUNT(*) FROM metrics GROUP BY category").fetchall()
        return {"total": total, "by_category": {c[0]: c[1] for c in cats}}


class BenchmarkEngine:
    """Measures performance across task types."""

    def __init__(self, metrics: MetricsEngine):
        self.metrics = metrics
        self.results: List[Dict] = []

    def run_benchmark(self, name: str, fn: Callable, args: tuple = (),
                      kwargs: Dict = {}, iterations: int = 3) -> Dict:
        """Run a benchmark and record metrics."""
        latencies = []
        for _ in range(iterations):
            start = time.time()
            try:
                fn(*args, **kwargs)
            except Exception as e:
                self.metrics.record("benchmark", name, -1, "error", {"error": str(e)})
                return {"name": name, "status": "error", "error": str(e)}
            latencies.append((time.time() - start) * 1000)

        avg_latency = sum(latencies) / len(latencies)

        self.metrics.record("benchmark", f"{name}_latency", round(avg_latency), "ms")
        result = {"name": name, "iterations": iterations, "avg_latency_ms": round(avg_latency),
                  "min_ms": round(min(latencies)), "max_ms": round(max(latencies)),
                  "timestamp": datetime.now().isoformat()}
        self.results.append(result)
        return result

    def run_full_suite(self) -> Dict:
        """Run all standard benchmarks."""
        suite = {}

        # Simple task
        def simple(): time.sleep(0.001)
        suite["simple"] = self.run_benchmark("simple_task", simple, iterations=5)

        # Search task
        def search(): "nmap sqlmap hydra metasploit".find("sqlmap")
        suite["search"] = self.run_benchmark("search_task", search, iterations=10)

        # Data task
        data = {"a": 1, "b": 2}
        def data_task(): return json.dumps(data)
        suite["data"] = self.run_benchmark("data_task", data_task, iterations=10)

        return {"suite": suite, "metrics": self.metrics.stats()}

    def stats(self) -> Dict:
        return {"benchmarks_run": len(self.results), "metrics": self.metrics.stats()}


# ── Singleton ──────────────────────────────────────────────────────────
_metrics: Optional[MetricsEngine] = None
_benchmark: Optional[BenchmarkEngine] = None

def get_metrics() -> MetricsEngine:
    global _metrics
    if _metrics is None:
        _metrics = MetricsEngine()
    return _metrics

def get_benchmark() -> BenchmarkEngine:
    global _benchmark
    if _benchmark is None:
        _benchmark = BenchmarkEngine(get_metrics())
    return _benchmark
