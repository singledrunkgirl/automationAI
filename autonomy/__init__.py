"""HackWithAI v2 — Autonomous Improvement: Evaluate, Score, Optimize, Learn."""

from .evaluator import Evaluator, ScoreEngine
from .optimizers import PerformanceTracker, PromptOptimizer, StrategyManager, ToolOptimizer
from .engine import AutonomousEngine, get_autonomous

__all__ = [
    "Evaluator", "ScoreEngine", "PerformanceTracker",
    "PromptOptimizer", "StrategyManager", "ToolOptimizer",
    "AutonomousEngine", "get_autonomous",
]
