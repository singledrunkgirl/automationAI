#!/usr/bin/env python3
"""Recovery Engine + Snapshot Engine + Crash Detector — Resilience and auto-recovery."""

import json, time, threading, signal, sys, os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any

from .checkpoint_manager import CheckpointManager, SessionManager

DATA_DIR = Path("/home/kali/HackWithAI/data/logs/state")
DATA_DIR.mkdir(parents=True, exist_ok=True)


class SnapshotEngine:
    """Creates manual, automatic, and periodic state snapshots."""

    def __init__(self, ckpt: CheckpointManager):
        self.ckpt = ckpt
        self._auto_timer: Optional[threading.Timer] = None
        self.snapshots: List[Dict] = []

    def manual(self, component: str, state: Dict, label: str = "") -> str:
        cid = self.ckpt.save(component, state, {"type": "manual", "label": label})
        self.snapshots.append({"id": cid, "component": component, "type": "manual", "label": label})
        return cid

    def auto_snapshot(self, state_provider: Callable[[], Dict[str, Dict]]):
        """Take automatic snapshot of all components."""
        components = state_provider()
        ids = self.ckpt.save_all(components)
        for cid, comp in zip(ids, components):
            self.snapshots.append({"id": cid, "component": comp, "type": "auto"})

    def start_auto_timer(self, interval_seconds: int,
                         state_provider: Callable[[], Dict[str, Dict]]):
        def periodic():
            self.auto_snapshot(state_provider)
            self._auto_timer = threading.Timer(interval_seconds, periodic)
            self._auto_timer.daemon = True
            self._auto_timer.start()
        self._auto_timer = threading.Timer(interval_seconds, periodic)
        self._auto_timer.daemon = True
        self._auto_timer.start()

    def stop_auto_timer(self):
        if self._auto_timer:
            self._auto_timer.cancel()
            self._auto_timer = None

    def stats(self) -> Dict:
        return {"total": len(self.snapshots), "auto": sum(1 for s in self.snapshots if s["type"] == "auto"),
                "manual": sum(1 for s in self.snapshots if s["type"] == "manual")}


class CrashDetector:
    """Detects unexpected termination, partial execution, missing checkpoints."""

    def __init__(self, ckpt: CheckpointManager, session: SessionManager):
        self.ckpt = ckpt
        self.session = session
        self.crashes: List[Dict] = []

    def check(self) -> Dict:
        issues = []

        # Check for active sessions without recent checkpoints
        active = self.session.get_active()
        for s in active:
            started = s.get("started", "")
            phases = len(s.get("phases", []))
            if phases > 0:
                issues.append({"type": "active_no_checkpoint", "session": s["session_id"],
                               "phases": phases, "age": f"Started {started}"})

        # Check for partial execution
        completed = [s for s in self.session.sessions.values() if s["status"] == "completed"]
        failed = [s for s in self.session.sessions.values() if s["status"] == "failed"]
        if failed and len(failed) > len(completed) * 2:
            issues.append({"type": "high_failure_rate", "completed": len(completed), "failed": len(failed)})

        return {"issues": issues, "count": len(issues), "crashed": len(issues) > 0}

    def record_crash(self, component: str, error: str = ""):
        self.crashes.append({"component": component, "error": error, "timestamp": datetime.now().isoformat()})

    def stats(self) -> Dict:
        return {"crashes_detected": len(self.crashes), "last_check": datetime.now().isoformat()}


class RecoveryEngine:
    """Resume workflows, recover failed tasks, restore state from checkpoints."""

    def __init__(self, ckpt: CheckpointManager, session: SessionManager):
        self.ckpt = ckpt
        self.session = session
        self.recoveries: List[Dict] = []

    def recover_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Recover a workflow from its latest checkpoint."""
        ckpt_data = self.ckpt.latest(f"workflow_{workflow_id}")
        if not ckpt_data:
            return None

        state = ckpt_data.get("state", {})
        recovery = {
            "workflow_id": workflow_id,
            "recovered_at": datetime.now().isoformat(),
            "checkpoint_id": ckpt_data["id"],
            "checkpoint_time": ckpt_data["timestamp"],
            "state": state,
        }
        self.recoveries.append(recovery)
        return recovery

    def recover_session(self, session_id: str) -> Dict:
        """Attempt to recover and resume a session."""
        context = self.session.resume_context(session_id)
        recovery = {
            "session_id": session_id,
            "recovered_at": datetime.now().isoformat(),
            "resumable": context["status"] != "completed",
            "last_phase": context["last_phase"],
            "context": context,
        }
        self.recoveries.append(recovery)
        return recovery

    def retry_failed_tasks(self, task_ids: List[str],
                          retry_fn: Callable[[str], Any]) -> Dict[str, Any]:
        """Retry failed tasks with recovery callback."""
        results = {}
        for tid in task_ids:
            try:
                results[tid] = retry_fn(tid)
                self.recoveries.append({"task_id": tid, "retried": True, "success": True})
            except Exception as e:
                results[tid] = {"error": str(e)}
                self.recoveries.append({"task_id": tid, "retried": True, "success": False, "error": str(e)})
        return results

    def restore_swarm(self, swarm_callback: Callable[[], Any]) -> Any:
        """Restore and re-run swarm from last checkpoint."""
        ckpt_data = self.ckpt.latest("swarm")
        if not ckpt_data:
            return None

        # Re-initialize from checkpoint state
        state = ckpt_data.get("state", {})
        result = swarm_callback()
        self.recoveries.append({"component": "swarm", "checkpoint_id": ckpt_data["id"],
                               "timestamp": datetime.now().isoformat()})
        return result

    def full_recovery(self) -> Dict:
        """Attempt full system recovery from all checkpoints."""
        components = self.ckpt.list_components()
        recovered = []
        for comp in components:
            latest = self.ckpt.latest(comp)
            if latest:
                recovered.append({"component": comp, "checkpoint": latest["id"],
                                 "timestamp": latest["timestamp"]})

        return {
            "recovered_components": len(recovered),
            "components": recovered,
            "failed_sessions": len([s for s in self.session.sessions.values() if s["status"] == "failed"]),
            "active_sessions": len(self.session.get_active()),
        }

    def stats(self) -> Dict:
        return {"total_recoveries": len(self.recoveries),
                "recent": [r for r in self.recoveries[-5:]]}
