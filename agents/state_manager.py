#!/usr/bin/env python3
"""
State Manager — Persistent agent state, task history, debate records, consensus logs.
Survives interruptions and allows resume.
"""

import json, time, os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

STATE_DIR = Path("/home/kali/HackWithAI/data/logs/state")
STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = STATE_DIR / "agent_state.json"


class AgentState:
    """State for a single agent."""
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.elo = 1000
        self.wins = 0
        self.losses = 0
        self.confidence = 0.5
        self.last_active = ""
        self.tasks_completed: List[str] = []

    def to_dict(self) -> Dict:
        return {"name": self.name, "role": self.role, "elo": self.elo,
                "wins": self.wins, "losses": self.losses, "confidence": self.confidence,
                "last_active": self.last_active, "tasks": self.tasks_completed[-10:]}

    @classmethod
    def from_dict(cls, d: Dict) -> "AgentState":
        a = cls(d["name"], d["role"])
        for k in ("elo", "wins", "losses", "confidence", "last_active"):
            setattr(a, k, d.get(k, getattr(a, k)))
        a.tasks_completed = d.get("tasks", [])
        return a


class StateManager:
    """Persistent state manager for the multi-agent system."""

    def __init__(self):
        self.agents: Dict[str, AgentState] = {}
        self.task_history: List[Dict] = []
        self.debate_records: List[str] = []
        self.consensus_records: List[Dict] = []
        self.revision_records: List[Dict] = []
        self.sessions: Dict[str, Dict] = {}
        self._load()

    def register_agent(self, name: str, role: str) -> AgentState:
        if name not in self.agents:
            self.agents[name] = AgentState(name, role)
        return self.agents[name]

    def get_agent(self, name: str) -> Optional[AgentState]:
        return self.agents.get(name)

    def record_task(self, task_id: str, target: str, agent: str, outcome: str):
        self.task_history.append({
            "task_id": task_id, "target": target, "agent": agent,
            "outcome": outcome, "timestamp": datetime.now().isoformat(),
        })
        if agent in self.agents:
            self.agents[agent].last_active = datetime.now().isoformat()
            self.agents[agent].tasks_completed.append(task_id)

    def record_debate(self, debate_id: str):
        self.debate_records.append(debate_id)

    def record_consensus(self, record: Dict):
        self.consensus_records.append({**record, "timestamp": datetime.now().isoformat()})

    def record_revision(self, record: Dict):
        self.revision_records.append({**record, "timestamp": datetime.now().isoformat()})

    def start_session(self, session_id: str, target: str):
        self.sessions[session_id] = {
            "session_id": session_id, "target": target,
            "started": datetime.now().isoformat(), "status": "active",
            "phases": [],
        }

    def log_phase(self, session_id: str, phase: str, detail: str):
        if session_id in self.sessions:
            self.sessions[session_id]["phases"].append({
                "phase": phase, "detail": detail, "time": datetime.now().isoformat(),
            })

    def complete_session(self, session_id: str, success: bool):
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "completed" if success else "failed"
            self.sessions[session_id]["completed"] = datetime.now().isoformat()

    def save(self):
        data = {
            "agents": {k: v.to_dict() for k, v in self.agents.items()},
            "tasks": self.task_history[-200:],
            "debates": self.debate_records[-100:],
            "consensus": self.consensus_records[-50:],
            "revisions": self.revision_records[-50:],
            "sessions": {k: v for k, v in list(self.sessions.items())[-10:]},
        }
        with open(STATE_FILE, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _load(self):
        if not STATE_FILE.exists():
            return
        try:
            with open(STATE_FILE) as f:
                data = json.load(f)
            for k, v in data.get("agents", {}).items():
                self.agents[k] = AgentState.from_dict(v)
            self.task_history = data.get("tasks", [])
            self.debate_records = data.get("debates", [])
            self.consensus_records = data.get("consensus", [])
            self.revision_records = data.get("revisions", [])
            self.sessions = data.get("sessions", {})
        except Exception:
            pass

    def stats(self) -> Dict:
        return {
            "agents_registered": len(self.agents),
            "tasks_completed": len(self.task_history),
            "debates_recorded": len(self.debate_records),
            "consensus_records": len(self.consensus_records),
            "revisions": len(self.revision_records),
            "active_sessions": sum(1 for s in self.sessions.values() if s.get("status") == "active"),
        }


# ── Singleton ──────────────────────────────────────────────────────────
_state: Optional[StateManager] = None

def get_state() -> StateManager:
    global _state
    if _state is None:
        _state = StateManager()
    return _state
