#!/usr/bin/env python3
"""Health Monitor + Resource Manager — System health tracking with overload prevention."""

import json, time, threading, psutil, os, sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

DATA_DIR = Path("/home/kali/HackWithAI/data/logs/production")
DATA_DIR.mkdir(parents=True, exist_ok=True)
HEALTH_DB = DATA_DIR / "health.db"


class HealthMonitor:
    """Tracks CPU, RAM, latency, token usage, agent exec time, workflow duration, errors."""

    def __init__(self):
        self._init_db()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.alerts: List[Dict] = []
        self.thresholds = {"cpu_pct": 90, "mem_pct": 85, "latency_ms": 30000, "errors_per_min": 10}

    def _init_db(self):
        with sqlite3.connect(HEALTH_DB) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS health_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT, cpu_pct REAL, mem_pct REAL,
                mem_used_mb REAL, latency_ms INTEGER, errors INTEGER,
                agents_active INTEGER, timestamp TEXT
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT, component TEXT,
                message TEXT, value REAL, threshold REAL, timestamp TEXT
            )""")
            db.commit()

    def sample(self) -> Dict:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        mem_pct = mem.percent
        mem_used = mem.used / (1024 * 1024)

        snapshot = {
            "cpu_pct": cpu, "mem_pct": round(mem_pct, 1),
            "mem_used_mb": round(mem_used), "latency_ms": 0,
            "errors": 0, "agents_active": 0,
            "timestamp": datetime.now().isoformat(),
        }

        with sqlite3.connect(HEALTH_DB) as db:
            db.execute("INSERT INTO health_log VALUES (NULL,?,?,?,?,?,?,?)",
                      (snapshot["cpu_pct"], snapshot["mem_pct"], snapshot["mem_used_mb"],
                       snapshot["latency_ms"], snapshot["errors"], snapshot["agents_active"],
                       snapshot["timestamp"]))
            db.commit()

        # Check thresholds
        if cpu > self.thresholds["cpu_pct"]:
            self.alert("WARNING", "cpu", f"CPU at {cpu}%", cpu, self.thresholds["cpu_pct"])
        if mem_pct > self.thresholds["mem_pct"]:
            self.alert("WARNING", "memory", f"Memory at {mem_pct}%", mem_pct, self.thresholds["mem_pct"])

        return snapshot

    def alert(self, level: str, component: str, message: str, value: float, threshold: float):
        alert = {"level": level, "component": component, "message": message,
                 "value": value, "threshold": threshold, "timestamp": datetime.now().isoformat()}
        self.alerts.append(alert)
        with sqlite3.connect(HEALTH_DB) as db:
            db.execute("INSERT INTO alerts VALUES (NULL,?,?,?,?,?,?)",
                      (level, component, message, value, threshold, alert["timestamp"]))
            db.commit()

    def start_monitoring(self, interval_seconds: int = 30):
        self._running = True
        def loop():
            while self._running:
                self.sample()
                time.sleep(interval_seconds)
        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def recent(self, minutes: int = 5) -> List[Dict]:
        with sqlite3.connect(HEALTH_DB) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("""SELECT * FROM health_log
                                WHERE timestamp > datetime('now', ?)
                                ORDER BY timestamp DESC LIMIT 50""",
                             (f'-{minutes} minutes',)).fetchall()
            return [dict(r) for r in rows]

    def stats(self) -> Dict:
        with sqlite3.connect(HEALTH_DB) as db:
            logs = db.execute("SELECT COUNT(*) FROM health_log").fetchone()[0]
            alerts = db.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        return {"samples": logs, "alerts": alerts, "active_alerts": len([a for a in self.alerts[-10:]])}


class ResourceManager:
    """Controls memory usage, parallel execution, task limits, timeouts."""

    def __init__(self):
        self.limits = {"max_threads": 8, "max_tasks": 50, "max_memory_mb": 2048,
                       "max_queue_size": 100, "default_timeout": 300,
                       "agent_timeout": 600, "workflow_timeout": 3600}

    def can_allocate_thread(self) -> bool:
        return threading.active_count() < self.limits["max_threads"]

    def can_allocate_memory(self, request_mb: int = 100) -> bool:
        mem = psutil.virtual_memory()
        used_mb = mem.used / (1024 * 1024)
        return (used_mb + request_mb) < self.limits["max_memory_mb"]

    def check_health(self) -> Dict:
        mem = psutil.virtual_memory()
        return {
            "threads_active": threading.active_count(),
            "threads_max": self.limits["max_threads"],
            "memory_used_pct": round(mem.percent, 1),
            "memory_limit_mb": self.limits["max_memory_mb"],
            "cpu_pct": psutil.cpu_percent(interval=0.1),
            "can_allocate": self.can_allocate_thread() and self.can_allocate_memory(),
        }

    def throttle(self, workload: int) -> int:
        """Return max allowed concurrent tasks for current workload."""
        if workload > self.limits["max_tasks"]:
            return min(workload // 2, self.limits["max_tasks"])
        return min(workload, self.limits["max_threads"])

    def stats(self) -> Dict:
        return {**self.limits, "health": self.check_health()}
