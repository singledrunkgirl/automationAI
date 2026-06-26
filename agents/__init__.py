"""HackWithAI — Agent Debate Engine + Self-Improvement + Autonomous Loop + Hermes Runtime"""

from .models import create_model, BaseModel, OllamaModel, OpenRouterModel, RuleBasedModel
from .debate_engine import DebateEngine, DebateAgent, get_engine
from .self_improvement import (
    SelfImprovement, SelfImprovementEngine,
    get_improver, SkillRecord, StrategyPattern,
)
from .message_bus import MessageBus, get_message_bus
from .state_manager import StateManager, AgentState, get_state
from .consensus_engine import ConsensusEngine, get_consensus
from .critic_agent import CriticAgent, get_critic
from .reviewer_agent import ReviewerAgent, get_reviewer
from .revision_agent import RevisionAgent, get_revision
from .hermes_coordinator import HermesCoordinator, get_hermes

__all__ = [
    "create_model", "BaseModel", "OllamaModel", "OpenRouterModel", "RuleBasedModel",
    "DebateEngine", "DebateAgent", "get_engine",
    "SelfImprovement", "SelfImprovementEngine", "get_improver",
    "SkillRecord", "StrategyPattern",
    "MessageBus", "get_message_bus",
    "StateManager", "AgentState", "get_state",
    "ConsensusEngine", "get_consensus",
    "CriticAgent", "get_critic",
    "ReviewerAgent", "get_reviewer",
    "RevisionAgent", "get_revision",
    "HermesCoordinator", "get_hermes",
]
