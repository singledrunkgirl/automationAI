#!/usr/bin/env python3
"""Autonomous Engine — Full self-improvement loop: evaluate → score → optimize → learn."""

import json, time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from .evaluator import Evaluator, ScoreEngine
from .optimizers import PerformanceTracker, PromptOptimizer, StrategyManager, ToolOptimizer

DATA_DIR = Path("/home/kali/HackWithAI/data/logs/autonomy")
DATA_DIR.mkdir(parents=True, exist_ok=True)


class AutonomousEngine:
    """Complete autonomous improvement system."""

    def __init__(self):
        self.evaluator = Evaluator()
        self.scores = ScoreEngine()
        self.tracker = PerformanceTracker()
        self.prompt_opt = PromptOptimizer()
        self.strategies = StrategyManager(self.tracker, self.scores)
        self.tool_opt = ToolOptimizer(self.tracker)

    def run_cycle(self, task_id: str, agent: str = "", model: str = "",
                  tool: str = "", strategy: str = "", metrics: Dict = {},
                  prompt: str = "", response: str = "") -> Dict:
        """Full improvement cycle after a task."""
        result = {"task_id": task_id, "timestamp": datetime.now().isoformat()}

        # 1. Evaluate
        eval = self.evaluator.evaluate(agent or "unknown", "agent", metrics)
        result["evaluation"] = {"overall": eval.overall, "scores": eval.scores}

        # 2. Update scores
        success = metrics.get("success", True)
        if agent:
            old_elo = self.scores.get_elo(agent, "agent")
            new_elo = self.scores.update(agent, "agent", success, old_elo)
            result["elo"] = {"agent": agent, "old": round(old_elo), "new": round(new_elo)}
        if tool:
            self.scores.update(tool, "tool", success)
        if strategy:
            self.scores.update(strategy, "strategy", success)

        # 3. Track performance
        self.tracker.record(task_id, agent=agent, model=model, tool=tool,
                           strategy=strategy, latency_ms=metrics.get("latency_ms", 0),
                           tokens=metrics.get("tokens", 0), cost=metrics.get("cost", 0),
                           success=success, quality=eval.overall)

        # 4. Record prompt
        if prompt:
            self.prompt_opt.record(prompt, agent, success, eval.overall, response)

        # 5. Recommendations
        result["recommendations"] = {
            "best_strategy": self.strategies.select_best(),
            "best_tools": self.tool_opt.recommend_best(),
            "prompt_tip": self.prompt_opt.recommend(agent),
        }

        return result

    def leaderboard(self) -> Dict:
        return {
            "agents": self.scores.leaderboard("agent"),
            "tools": self.scores.leaderboard("tool"),
            "strategies": self.strategies.compare(),
        }

    def stats(self) -> Dict:
        return {
            "evaluations": self.evaluator.get_history(limit=5),
            "scores": self.scores.stats(),
            "strategies": self.strategies.compare(),
            "top_tools": self.tool_opt.rank()[:5],
        }


# ── Singleton ──────────────────────────────────────────────────────────
_engine: Optional[AutonomousEngine] = None

def get_autonomous() -> AutonomousEngine:
    global _engine
    if _engine is None:
        _engine = AutonomousEngine()
    return _engine
