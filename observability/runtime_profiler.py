#!/usr/bin/env python3
"""
Runtime Profiler + Reality Audit — Verifies which subsystems are actually used.
Determines REAL RUNTIME vs PARTIAL vs UNUSED for every AI OS component.
"""

import json, time, sys, subprocess, inspect, importlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

DATA_DIR = Path("/home/kali/HackWithAI/data/logs/observability")
DATA_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_ROOT = Path("/home/kali/HackWithAI")

# ── Module Registry ───────────────────────────────────────────────────
SUBSYSTEMS = {
    "hermes": {"path": "agents/hermes_coordinator.py", "classes": ["HermesCoordinator"], "score": 0},
    "debate": {"path": "agents/debate_engine.py", "classes": ["DebateEngine", "DebateAgent"], "score": 0},
    "critic": {"path": "agents/critic_agent.py", "classes": ["CriticAgent"], "score": 0},
    "reviewer": {"path": "agents/reviewer_agent.py", "classes": ["ReviewerAgent"], "score": 0},
    "revision": {"path": "agents/revision_agent.py", "classes": ["RevisionAgent"], "score": 0},
    "consensus": {"path": "agents/consensus_engine.py", "classes": ["ConsensusEngine"], "score": 0},
    "message_bus": {"path": "agents/message_bus.py", "classes": ["MessageBus"], "score": 0},
    "state": {"path": "agents/state_manager.py", "classes": ["StateManager"], "score": 0},
    "self_improvement": {"path": "agents/self_improvement.py", "classes": ["SelfImprovementEngine"], "score": 0},
    "workflow": {"path": "workflow/planner.py", "classes": ["Planner", "TaskQueue", "Executor"], "score": 0},
    "swarm": {"path": "swarm/coordinator.py", "classes": ["SwarmCoordinator"], "score": 0},
    "memory": {"path": "memory/rag/pipeline.py", "classes": ["RAGPipeline"], "score": 0},
    "knowledge": {"path": "knowledge/graph.py", "classes": ["KnowledgeGraph"], "score": 0},
    "reflection": {"path": "reflection/reflection_engine.py", "classes": ["ReflectionEngine"], "score": 0},
    "autonomy": {"path": "autonomy/engine.py", "classes": ["AutonomousEngine"], "score": 0},
    "recovery": {"path": "state/recovery_engine.py", "classes": ["RecoveryEngine"], "score": 0},
    "c2": {"path": "tools/c2_framework.py", "classes": ["C2Framework"], "score": 0},
    "darkweb": {"path": "tools/darkweb_intelligence.py", "classes": ["DarkWebMarketScanner"], "score": 0},
    "tor": {"path": "tools/tor_manager.py", "classes": ["TorManager"], "score": 0},
    "zeroday": {"path": "tools/zeroday_scanner.py", "classes": ["ZeroDayScanner"], "score": 0},
    "playwright": {"path": "tools/playwright_automation.py", "classes": ["BrowserAutomation"], "score": 0},
    "network_tools": {"path": "tools/network_tools.py", "score": 0},
    "exploitation": {"path": "tools/exploitation_tools.py", "score": 0},
    "post_exploitation": {"path": "tools/post_exploitation_tools.py", "score": 0},
    "web_tools": {"path": "tools/web_tools.py", "score": 0},
    "wireless_tools": {"path": "tools/wireless_tools.py", "score": 0},
    "binary_tools": {"path": "tools/binary_tools.py", "score": 0},
    "crypt_tools": {"path": "tools/crypt_tools.py", "score": 0},
    "osint_tools": {"path": "tools/osint_tools.py", "score": 0},
    "evasion_tools": {"path": "tools/evasion_tools.py", "score": 0},
    "orchestrator": {"path": "orchestrator/unrestricted_orchestrator.py", "score": 0},
    "direct_access": {"path": "core/direct_access.py", "classes": ["DirectAccess"], "score": 0},
    "autonomous_loop": {"path": "core/autonomous_loop.py", "classes": ["AutonomousHackAI"], "score": 0},
}


class RuntimeProfiler:
    """Profiles which modules are actually loaded and executed."""

    def __init__(self):
        self.loaded_modules: List[str] = []
        self.execution_traces: List[Dict] = []
        self.dead_modules: List[str] = []

    def scan_loaded(self):
        """Scan sys.modules for project modules."""
        self.loaded_modules = []
        for name, mod in sorted(sys.modules.items()):
            if "HackWithAI" in str(getattr(mod, "__file__", "")) or \
               any(p in name for p in ["agents", "workflow", "swarm", "memory", "reflection",
                                       "knowledge", "autonomy", "state", "tools", "core", "orchestrator"]):
                self.loaded_modules.append(name)

    def profile_subsystem(self, name: str, subsystem: Dict) -> int:
        """Score a subsystem: 0=missing, 1=file exists, 2=importable, 3=runtime active."""
        path = PROJECT_ROOT / subsystem["path"]
        score = 0

        # File exists
        if path.exists():
            score = 1

        # Importable
        if "classes" in subsystem:
            for cls_name in subsystem["classes"]:
                try:
                    mod_path = str(path.relative_to(PROJECT_ROOT)).replace("/", ".").replace(".py", "")
                    __import__(mod_path, fromlist=[cls_name])
                    score = max(score, 2)
                except Exception:
                    pass

        # Runtime active (check if any function was actually called)
        module_name = str(path.relative_to(PROJECT_ROOT)).replace("/", ".").replace(".py", "")
        if module_name in str(self.loaded_modules):
            score = max(score, 3)

        subsystem["score"] = score
        return score

    def detect_dead_code(self) -> List[str]:
        """Find modules that exist but are never imported."""
        dead = []
        for name, sub in SUBSYSTEMS.items():
            path = PROJECT_ROOT / sub["path"]
            if path.exists() and sub["score"] < 2:
                dead.append(name)
        self.dead_modules = dead
        return dead

    def trace(self, component: str, action: str, duration_ms: int = 0):
        self.execution_traces.append({
            "component": component, "action": action,
            "duration_ms": duration_ms, "timestamp": datetime.now().isoformat(),
        })

    def stats(self) -> Dict:
        return {"loaded": len(self.loaded_modules), "traces": len(self.execution_traces),
                "dead": len(self.dead_modules)}


class AuditEngine:
    """Verifies REAL RUNTIME vs PARTIAL vs UNUSED for every subsystem."""

    def __init__(self, profiler: RuntimeProfiler):
        self.profiler = profiler
        self.results: Dict[str, Dict] = {}

    def full_audit(self) -> Dict:
        self.profiler.scan_loaded()

        for name, sub in SUBSYSTEMS.items():
            score = self.profiler.profile_subsystem(name, sub)
            sub["score"] = score

        self.profiler.detect_dead_code()

        # Classify
        real = {}; partial = {}; unused = {}
        for name, sub in SUBSYSTEMS.items():
            s = sub["score"]
            if s >= 3: real[name] = sub
            elif s >= 1: partial[name] = sub
            else: unused[name] = sub

        self.results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {"total": len(SUBSYSTEMS), "real_runtime": len(real),
                        "partial": len(partial), "unused": len(unused)},
            "real_runtime": {k: v["path"] for k, v in sorted(real.items())},
            "partial": {k: {"path": v["path"], "score": v["score"]} for k, v in sorted(partial.items())},
            "unused": {k: v["path"] for k, v in sorted(unused.items())},
            "dead_code": self.profiler.dead_modules,
        }

        # Save report
        report_path = DATA_DIR / "reality_audit.json"
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)

        return self.results

    def report_card(self) -> str:
        audit = self.full_audit()
        s = audit["summary"]
        lines = [
            "=" * 60,
            "  HackWithAI v2 — Reality Audit",
            "=" * 60,
            f"  Total subsystems: {s['total']}",
            f"  REAL RUNTIME:     {s['real_runtime']} ✅",
            f"  PARTIAL:          {s['partial']} ⚠️",
            f"  UNUSED:           {s['unused']} ❌",
            "=" * 60,
            "",
            "REAL RUNTIME:",
        ]
        for k, v in audit["real_runtime"].items():
            lines.append(f"  ✅ {k}: {v}")
        if audit["partial"]:
            lines.append("\nPARTIAL:")
            for k, v in audit["partial"].items():
                lines.append(f"  ⚠️ {k}: {v['path']} (score={v['score']})")
        if audit["unused"]:
            lines.append("\nUNUSED:")
            for k, v in audit["unused"].items():
                lines.append(f"  ❌ {k}: {v}")
        return "\n".join(lines)


# ── Singleton ──────────────────────────────────────────────────────────
_profiler: Optional[RuntimeProfiler] = None
_audit: Optional[AuditEngine] = None

def get_profiler() -> RuntimeProfiler:
    global _profiler
    if _profiler is None:
        _profiler = RuntimeProfiler()
    return _profiler

def get_audit() -> AuditEngine:
    global _audit
    if _audit is None:
        _audit = AuditEngine(get_profiler())
    return _audit
