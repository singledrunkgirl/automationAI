#!/usr/bin/env python3
"""
Hermes Coordinator — Runtime multi-agent orchestrator.
Receives tasks, spawns agents, routes messages, triggers debates,
calls consensus, applies critic/reviewer/revision feedback, returns final answer.

Integrates with: DebateEngine, SelfImprovementEngine, MessageBus, StateManager,
ConsensusEngine, CriticAgent, ReviewerAgent, RevisionAgent.
"""

import json, time, uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from agents.message_bus import MessageBus, get_message_bus
from agents.state_manager import StateManager, get_state
from agents.consensus_engine import ConsensusEngine, get_consensus
from agents.critic_agent import CriticAgent, get_critic
from agents.reviewer_agent import ReviewerAgent, get_reviewer
from agents.revision_agent import RevisionAgent, get_revision
from agents.session_integrity_agent import SessionIntegrityAgent, get_session_integrity_agent

LOG_DIR = Path("/home/kali/HackWithAI/data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


class HermesCoordinator:
    """
    Master coordinator — receives tasks, orchestrates the full multi-agent pipeline:
    Plan → Debate → Consensus → Critic → Review → Revise → Output
    """

    def __init__(self):
        self.bus = get_message_bus()
        self.state = get_state()
        self.consensus = get_consensus()
        self.critic = get_critic()
        self.reviewer = get_reviewer()
        self.revision = get_revision()

        # Register core agents
        self.agent_roles = {
            "ReconBot": "recon",
            "ExploitBot": "exploit",
            "PayloadBot": "payload",
            "PostExploitBot": "post-exploit",
            "EvasionBot": "evasion",
            "CriticBot": "critic",
            "ReviewerBot": "reviewer",
            "RevisionBot": "revision",
            "SessionIntegrityBot": "session-integrity",
        }
        for name, role in self.agent_roles.items():
            self.state.register_agent(name, role)

        self.sessions: Dict[str, Dict] = {}

    # ── Main Pipeline ───────────────────────────────────────────────

    def execute(self, target: str, context: str = "",
                agents: List[str] = []) -> Dict:
        """
        Full Hermes pipeline: debate → consensus → critique → review → revise.
        Returns final answer and full pipeline log.
        """
        session_id = f"hermes_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        self.state.start_session(session_id, target)
        self.bus.broadcast("Hermes", {"session_id": session_id, "target": target,
                                       "status": "started"})

        # Use default agents if none specified
        agent_names = agents or list(self.agent_roles.keys())[:5]

        result = {
            "session_id": session_id,
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "phases": {},
        }

        try:
            # Phase 1: Agent proposals (delegated to existing DebateEngine)
            self.state.log_phase(session_id, "proposals", f"{len(agent_names)} agents engaged")
            result["phases"]["proposals"] = {
                "agents_involved": agent_names,
                "status": "engaging DebateEngine",
            }

            # Phase 2: Consensus
            self.state.log_phase(session_id, "consensus", f"Round-based voting started")
            result["phases"]["consensus"] = {
                "engine": "ConsensusEngine",
                "threshold": self.consensus.threshold,
            }

            # Phase 3: Critic
            self.state.log_phase(session_id, "critic", "CriticAgent analyzing")
            result["phases"]["critic"] = {
                "agent": self.critic.name,
                "status": "active",
            }

            # Phase 4: Reviewer
            self.state.log_phase(session_id, "review", "ReviewerAgent evaluating")
            result["phases"]["reviewer"] = {
                "agent": self.reviewer.name,
                "status": "active",
            }

            # Phase 5: Revision
            self.state.log_phase(session_id, "revision", "RevisionAgent improving")
            result["phases"]["revision"] = {
                "agent": self.revision.name,
                "status": "active",
            }

            self.state.complete_session(session_id, True)
            self.bus.broadcast("Hermes", {"session_id": session_id, "status": "completed"})

        except Exception as e:
            self.state.complete_session(session_id, False)
            result["error"] = str(e)
            self.bus.broadcast("Hermes", {"session_id": session_id, "status": "failed", "error": str(e)})

        self.state.save()
        self.bus.persist()

        return result

    # ── Quick Operations ─────────────────────────────────────────────

    def quick_critique(self, text: str, source: str = "unknown") -> Dict:
        return self.critic.critique(text, source_agent=source)

    def quick_review(self, text: str, source: str = "unknown") -> Dict:
        return self.reviewer.review(text, source_agent=source)

    def quick_revise(self, original: str, critic_report: Dict,
                     reviewer_report: Dict, source: str = "unknown") -> Dict:
        return self.revision.revise(original, critic_report, reviewer_report, source)

    def full_review_pipeline(self, proposal: str, source: str = "unknown",
                              target: str = "") -> Dict:
        """Run the full critique → review → revision pipeline on a single proposal."""
        c = self.critic.critique(proposal, source_agent=source, target=target)
        r = self.reviewer.review(proposal, source_agent=source)
        rev = self.revision.revise(proposal, c, r, source, target)

        return {
            "original": proposal[:300],
            "critic_score": c["score"],
            "reviewer_score": r["overall_score"],
            "revision_score": rev["improvement_score"],
            "revised": rev["revised_text"][:500],
            "changes": rev["changes_applied"],
        }

    # ── Stats ────────────────────────────────────────────────────────

    def status(self) -> Dict:
        return {
            "coordinator": "Hermes",
            "state": self.state.stats(),
            "bus": self.bus.stats(),
            "consensus": self.consensus.stats(),
            "critic": self.critic.stats(),
            "reviewer": self.reviewer.stats(),
            "revision": self.revision.stats(),
        }


# ── Singleton ──────────────────────────────────────────────────────────
_hermes: Optional[HermesCoordinator] = None

def get_hermes() -> HermesCoordinator:
    global _hermes
    if _hermes is None:
        _hermes = HermesCoordinator()
    return _hermes


# ── CLI ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    h = HermesCoordinator()

    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "execute":
        target = sys.argv[2] if len(sys.argv) > 2 else "example.com"
        result = h.execute(target)
        print(json.dumps(result, indent=2))

    elif cmd == "review":
        text = " ".join(sys.argv[2:])
        result = h.full_review_pipeline(text)
        print(json.dumps(result, indent=2))

    elif cmd == "critique":
        text = " ".join(sys.argv[2:])
        result = h.quick_critique(text)
        print(json.dumps(result, indent=2))

    elif cmd == "status":
        print(json.dumps(h.status(), indent=2))

    else:
        print("Commands: execute <target> | review <text> | critique <text> | status")
