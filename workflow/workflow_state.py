#!/usr/bin/env python3
"""Workflow State — Persistent workflow state, checkpoints, crash recovery."""

import json, time, sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from .planner import ExecutionPlan, Task

DATA_DIR = Path("/home/kali/HackWithAI/data/logs/workflow")
DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_DB = DATA_DIR / "workflow_state.db"


class WorkflowState:
    """Persistent workflow state with checkpoint and crash recovery."""

    def __init__(self):
        self._init_db()
        self.active_workflows: Dict[str, ExecutionPlan] = {}
        self.checkpoints: Dict[str, Dict] = {}

    def _init_db(self):
        with sqlite3.connect(STATE_DB) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY, target TEXT, status TEXT,
                plan_json TEXT, created TEXT, updated TEXT,
                task_count INTEGER, completed_count INTEGER
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS checkpoints (
                workflow_id TEXT, checkpoint_time TEXT, state_json TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id)
            )""")
            db.commit()

    def start_workflow(self, plan: ExecutionPlan):
        plan.status = "running"
        self.active_workflows[plan.id] = plan
        self.save(plan)

    def update_task(self, workflow_id: str, task_id: str, status: str, result: str = ""):
        plan = self.active_workflows.get(workflow_id)
        if not plan:
            return
        for t in plan.tasks:
            if t.id == task_id:
                t.status = status
                t.result = result
                if status in ("completed", "failed"):
                    t.completed = datetime.now().isoformat()
                break
        self.save(plan)

    def progress(self, workflow_id: str) -> Dict:
        plan = self.active_workflows.get(workflow_id)
        if not plan:
            return {"error": "not found"}
        total = len(plan.tasks)
        done = sum(1 for t in plan.tasks if t.status == "completed")
        failed = sum(1 for t in plan.tasks if t.status == "failed")
        return {"total": total, "done": done, "failed": failed, "pending": total - done - failed,
                "percent": round(done / max(total, 1) * 100, 1)}

    def save(self, plan: ExecutionPlan):
        with sqlite3.connect(STATE_DB) as db:
            db.execute("""INSERT OR REPLACE INTO workflows VALUES (?,?,?,?,?,?,?,?)""",
                      (plan.id, plan.target, plan.status, json.dumps([t.__dict__ for t in plan.tasks]),
                       plan.created, datetime.now().isoformat(),
                       len(plan.tasks), sum(1 for t in plan.tasks if t.status == "completed")))
            db.commit()

    def checkpoint(self, workflow_id: str):
        plan = self.active_workflows.get(workflow_id)
        if not plan:
            return
        state = {"tasks": {t.id: t.status for t in plan.tasks}, "time": datetime.now().isoformat()}
        with sqlite3.connect(STATE_DB) as db:
            db.execute("INSERT INTO checkpoints VALUES (?,?,?)",
                      (workflow_id, state["time"], json.dumps(state)))
            db.commit()
        self.checkpoints[workflow_id] = state

    def recover(self, workflow_id: str) -> Optional[ExecutionPlan]:
        """Recover workflow from last checkpoint."""
        with sqlite3.connect(STATE_DB) as db:
            row = db.execute("SELECT plan_json, status FROM workflows WHERE id=?",
                           (workflow_id,)).fetchone()
        if not row:
            return None

        tasks_data = json.loads(row[0])
        plan = ExecutionPlan(id=workflow_id, target="recovered", tasks=[], status=row[1])
        plan.tasks = [Task(**t) for t in tasks_data]

        # Reset running tasks to pending
        for t in plan.tasks:
            if t.status == "running":
                t.status = "pending"

        self.active_workflows[workflow_id] = plan
        return plan

    def complete_workflow(self, workflow_id: str, success: bool = True):
        plan = self.active_workflows.get(workflow_id)
        if plan:
            plan.status = "completed" if success else "failed"
            self.save(plan)
            self.active_workflows.pop(workflow_id, None)

    def stats(self) -> Dict:
        with sqlite3.connect(STATE_DB) as db:
            total = db.execute("SELECT COUNT(*) FROM workflows").fetchone()[0]
            active = db.execute("SELECT COUNT(*) FROM workflows WHERE status='running'").fetchone()[0]
            checkpoints = db.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0]
        return {
            "total_workflows": total,
            "active": active,
            "in_memory": len(self.active_workflows),
            "checkpoints": checkpoints,
            "db_size": f"{STATE_DB.stat().st_size / 1024:.0f}KB" if STATE_DB.exists() else "0KB",
        }


# ── Singleton ──────────────────────────────────────────────────────────
_state: Optional[WorkflowState] = None

def get_workflow_state() -> WorkflowState:
    global _state
    if _state is None:
        _state = WorkflowState()
    return _state
