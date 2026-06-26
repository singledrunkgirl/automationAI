"""HackWithAI v2 — Swarm Intelligence: Parallel agents, voting, coordination."""

from .swarm_memory import SwarmMemory, VotingEngine, get_swarm_memory
from .agents import (
    SwarmAgent, AgentResult,
    PlannerAgent, ResearcherAgent, CoderAgent, ReviewerAgent, OptimizerAgent,
)
from .coordinator import SwarmCoordinator, get_swarm

__all__ = [
    "SwarmMemory", "VotingEngine", "get_swarm_memory",
    "SwarmAgent", "AgentResult",
    "PlannerAgent", "ResearcherAgent", "CoderAgent", "ReviewerAgent", "OptimizerAgent",
    "SwarmCoordinator", "get_swarm",
]
