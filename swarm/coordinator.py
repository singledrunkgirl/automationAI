#!/usr/bin/env python3
"""
Swarm Coordinator — Spawns agents, distributes work, collects responses,
manages synchronization, monitors execution.
"""

import json, time, threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable

from .swarm_memory import SwarmMemory, VotingEngine, get_swarm_memory
from .agents import (
    SwarmAgent, AgentResult,
    PlannerAgent, ResearcherAgent, CoderAgent, ReviewerAgent, OptimizerAgent,
)

DATA_DIR = Path("/home/kali/HackWithAI/data/logs/swarm")
DATA_DIR.mkdir(parents=True, exist_ok=True)


class SwarmCoordinator:
    """Orchestrates parallel swarm agents with voting and aggregation."""

    def __init__(self):
        self.memory = get_swarm_memory()
        self.voting = VotingEngine(threshold=0.6)

        # Agent registry
        self.agents: Dict[str, SwarmAgent] = {
            "Planner": PlannerAgent(self.memory),
            "Researcher": ResearcherAgent(self.memory),
            "Coder": CoderAgent(self.memory),
            "Reviewer": ReviewerAgent(self.memory),
            "Optimizer": OptimizerAgent(self.memory),
        }
        self.results: List[AgentResult] = []
        self._results_lock = threading.Lock()

    def get_agent(self, name: str) -> Optional[SwarmAgent]:
        return self.agents.get(name)

    def run_sequential(self, task: str, agent_order: List[str] = [],
                       context: Dict = {}) -> Dict:
        """Run agents sequentially, each building on the previous output."""
        order = agent_order or list(self.agents.keys())
        sequential_results: Dict[str, AgentResult] = {}
        shared_context = dict(context)

        for agent_name in order:
            agent = self.agents.get(agent_name)
            if not agent:
                continue
            self.memory.event("Coordinator", "running", agent_name)
            result = agent.run(task, shared_context)
            sequential_results[agent_name] = result

            # Pass output to next agent
            if result.output:
                shared_context[agent_name] = result.output
                shared_context["agent_outputs"] = {
                    k: v.output for k, v in sequential_results.items()
                }

            with self._results_lock:
                self.results.append(result)

        return self._summarize(sequential_results, "sequential")

    def run_parallel(self, task: str, agent_names: List[str] = [],
                     context: Dict = {}) -> Dict:
        """Run specified agents in parallel threads."""
        names = agent_names or list(self.agents.keys())[:4]
        threads: Dict[str, threading.Thread] = {}
        results: Dict[str, AgentResult] = {}

        def worker(name: str):
            agent = self.agents.get(name)
            if agent:
                results[name] = agent.run(task, context)
                with self._results_lock:
                    self.results.append(results[name])

        for name in names:
            self.memory.event("Coordinator", "spawning", name)
            t = threading.Thread(target=worker, args=(name,))
            t.start()
            threads[name] = t

        for t in threads.values():
            t.join(timeout=60)

        return self._summarize(results, "parallel")

    def run_with_voting(self, task: str, agent_names: List[str] = []) -> Dict:
        """Run agents in parallel, then vote on the best output."""
        parallel_result = self.run_parallel(task, agent_names)

        # Extract agent outputs for voting
        agent_results = parallel_result.get("results", {})
        outputs = {}
        for name, r in list(agent_results.items()):
            if isinstance(r, dict):
                out = r.get("output", "")
            elif hasattr(r, "output"):
                out = r.output
            else:
                out = ""
            if out and "error" not in str(out).lower()[:50]:
                outputs[name] = out

        if len(outputs) < 2:
            parallel_result["voting"] = {"winner": list(outputs.keys())[0] if outputs else "", "note": "not enough voters"}
            return parallel_result

        # Each agent votes for the best output
        votes: Dict[str, str] = {}
        for voter_name, voter_agent in self.agents.items():
            if voter_name in outputs:
                # Agent votes for itself or another
                best = max(outputs.items(),
                          key=lambda x: len(x[1]) * (1.2 if x[0] == voter_name else 1.0))
                votes[voter_name] = best[0]

        round_result = self.voting.run_round(votes)
        parallel_result["voting"] = {
            "winner": round_result["winner"],
            "agreement": round_result["agreement"],
            "consensus_reached": round_result["consensus"],
            "votes": votes,
        }

        # If no consensus, run tiebreaker
        if not round_result["consensus"] and len(outputs) > 1:
            top = sorted(set(votes.values()), key=lambda x: sum(1 for v in votes.values() if v == x), reverse=True)[:2]
            tiebreaker = self.voting.tiebreaker(top, self.voting.rounds)
            parallel_result["voting"]["tiebreaker_winner"] = tiebreaker

        return parallel_result

    def run_full_swarm(self, task: str) -> Dict:
        """Full swarm cycle: plan → research → code → review → optimize → vote."""
        plan = self.agents["Planner"].run(task)
        if plan.output:
            plan_data = json.loads(plan.output)
            steps = [s["action"] for s in plan_data.get("steps", [])[:3]]
        else:
            steps = [task]

        # Research + Code in parallel
        research_code = self.run_parallel(task, ["Researcher", "Coder"])

        # Review + Optimize in parallel
        rc_results = research_code.get("results", {})
        agent_outputs = {}
        for k, v in rc_results.items():
            if isinstance(v, dict):
                agent_outputs[k] = v.get("output", "")
            elif hasattr(v, "output"):
                agent_outputs[k] = v.output
        review_optimize = self.run_parallel(task, ["Reviewer", "Optimizer"],
                                            {"agent_outputs": agent_outputs})

        # Vote on final output
        final = self.run_with_voting(task)

        return {
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "plan": plan.output[:500] if plan.output else "",
            "parallel_research_code": research_code.get("summary", {}),
            "parallel_review_optimize": review_optimize.get("summary", {}),
            "voting": final.get("voting", {}),
            "agent_stats": {name: agent.stats() for name, agent in self.agents.items()},
        }

    def _summarize(self, results: Dict[str, AgentResult], mode: str) -> Dict:
        success = sum(1 for r in results.values() if r and not r.error)
        avg_confidence = round(sum(r.confidence for r in results.values() if r) / max(len(results), 1), 2)
        avg_latency = round(sum(r.latency_ms for r in results.values() if r) / max(len(results), 1))

        return {
            "mode": mode,
            "agents_run": len(results),
            "successful": success,
            "avg_confidence": avg_confidence,
            "avg_latency_ms": avg_latency,
            "results": {k: {"output": (v.output or "")[:200], "confidence": v.confidence}
                       for k, v in results.items() if v},
            "summary": {"total": len(results), "errors": len(results) - success,
                       "best": max(results.items(), key=lambda x: x[1].confidence)[0] if results else ""},
        }

    def stats(self) -> Dict:
        return {
            "agents": {name: agent.stats() for name, agent in self.agents.items()},
            "voting": self.voting.stats(),
            "memory": self.memory.stats(),
            "total_results": len(self.results),
        }


# ── Singleton ──────────────────────────────────────────────────────────
_coordinator: Optional[SwarmCoordinator] = None

def get_swarm() -> SwarmCoordinator:
    global _coordinator
    if _coordinator is None:
        _coordinator = SwarmCoordinator()
    return _coordinator
