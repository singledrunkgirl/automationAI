#!/usr/bin/env python3
"""Checkpoint Manager — Persistent workflow, agent, swarm, and task state with recovery."""

import json, sqlite3, time, hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

DATA_DIR = Path("/home/kali/HackWithAI/data/logs/state")
DATA_DIR.mkdir(parents=True, exist_ok=True)
CKPT_DB = DATA_DIR / "checkpoints.db"


class CheckpointManager:
    """Persists and restores system state: workflows, agents, swarm, tasks, messages."""

    def __init__(self):
        self._init_db()
        self.checkpoints: Dict[str, Dict] = {}

    def _init_db(self):
        with sqlite3.connect(CKPT_DB) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS checkpoints (
                id TEXT PRIMARY KEY, component TEXT, state_json TEXT,
                timestamp TEXT, metadata TEXT
            )""")
            db.commit()

    def save(self, component: str, state: Dict, metadata: Dict = {}) -> str:
        cid = hashlib.md5(f"{component}{time.time()}".encode()).hexdigest()[:10]
        record = {"id": cid, "component": component, "state": state,
                  "timestamp": datetime.now().isoformat(), "metadata": metadata}

        with sqlite3.connect(CKPT_DB) as db:
            db.execute("INSERT INTO checkpoints VALUES (?,?,?,?,?)",
                      (cid, component, json.dumps(state), record["timestamp"],
                       json.dumps(metadata)))
            db.commit()

        self.checkpoints[cid] = record
        return cid

    def save_all(self, components: Dict[str, Dict]) -> List[str]:
        """Save multiple components at once."""
        ids = []
        for comp, state in components.items():
            ids.append(self.save(comp, state))
        return ids

    def load(self, checkpoint_id: str) -> Optional[Dict]:
        with sqlite3.connect(CKPT_DB) as db:
            row = db.execute("SELECT * FROM checkpoints WHERE id=?", (checkpoint_id,)).fetchone()
        if not row:
            return None
        return {"id": row[0], "component": row[1],
                "state": json.loads(row[2]), "timestamp": row[3],
                "metadata": json.loads(row[4]) if row[4] else {}}

    def latest(self, component: str = "") -> Optional[Dict]:
        with sqlite3.connect(CKPT_DB) as db:
            if component:
                row = db.execute("SELECT * FROM checkpoints WHERE component=? ORDER BY timestamp DESC LIMIT 1",
                                (component,)).fetchone()
            else:
                row = db.execute("SELECT * FROM checkpoints ORDER BY timestamp DESC LIMIT 1").fetchone()
        if not row:
            return None
        return {"id": row[0], "component": row[1],
                "state": json.loads(row[2]), "timestamp": row[3],
                "metadata": json.loads(row[4]) if row[4] else {}}

    def list_components(self) -> List[str]:
        with sqlite3.connect(CKPT_DB) as db:
            rows = db.execute("SELECT DISTINCT component FROM checkpoints").fetchall()
        return [r[0] for r in rows]

    def stats(self) -> Dict:
        with sqlite3.connect(CKPT_DB) as db:
            total = db.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0]
            recent = db.execute("SELECT COUNT(*) FROM checkpoints WHERE timestamp > datetime('now','-1 hour')").fetchone()[0]
        return {"total": total, "recent_1h": recent, "components": len(self.list_components()),
                "db_size": f"{CKPT_DB.stat().st_size / 1024:.0f}KB" if CKPT_DB.exists() else "0KB"}


class SessionManager:
    """Persists active sessions with context, history, and execution state."""

    def __init__(self):
        self.sessions: Dict[str, Dict] = {}

    def start(self, session_id: str, context: Dict = {}) -> str:
        sid = session_id or hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        self.sessions[sid] = {
            "session_id": sid, "started": datetime.now().isoformat(),
            "status": "active", "context": context, "phases": [], "results": {},
        }
        return sid

    def log(self, session_id: str, phase: str, detail: str = ""):
        if session_id in self.sessions:
            self.sessions[session_id]["phases"].append({
                "phase": phase, "detail": detail, "time": datetime.now().isoformat(),
            })

    def set_result(self, session_id: str, key: str, value: Any):
        if session_id in self.sessions:
            self.sessions[session_id]["results"][key] = value

    def complete(self, session_id: str, success: bool = True):
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "completed" if success else "failed"
            self.sessions[session_id]["completed"] = datetime.now().isoformat()

    def get_active(self) -> List[Dict]:
        return [s for s in self.sessions.values() if s["status"] == "active"]

    def get(self, session_id: str) -> Optional[Dict]:
        return self.sessions.get(session_id)

    def resume_context(self, session_id: str) -> Dict:
        session = self.sessions.get(session_id, {})
        return {
            "session_id": session_id,
            "status": session.get("status", "unknown"),
            "last_phase": session.get("phases", [])[-1] if session.get("phases") else None,
            "results": session.get("results", {}),
            "context": session.get("context", {}),
            "phases_count": len(session.get("phases", [])),
        }

    def stats(self) -> Dict:
        active = self.get_active()
        return {"total": len(self.sessions), "active": len(active),
                "completed": sum(1 for s in self.sessions.values() if s["status"] == "completed"),
                "failed": sum(1 for s in self.sessions.values() if s["status"] == "failed")}
