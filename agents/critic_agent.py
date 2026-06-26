#!/usr/bin/env python3
"""
Critic Agent — Finds flaws, detects hallucinations, verifies reasoning, challenges assumptions.
"""

import json, time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

LOG_DIR = Path("/home/kali/HackWithAI/data/logs")


class CriticAgent:
    """Criticizes proposals and responses, finding weaknesses and flaws."""

    def __init__(self, name: str = "CriticBot"):
        self.name = name
        self.critic_log: List[Dict] = []

    def critique(self, proposal: str, context: str = "", target: str = "",
                 source_agent: str = "") -> Dict:
        """
        Analyze a proposal and return a structured critique.
        Checks: completeness, logic, practicality, risk, assumptions, missing steps.
        """
        critique = {
            "source": source_agent,
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "score": 100,
            "findings": [],
            "assumptions_challenged": [],
            "missing_steps": [],
            "risks_identified": [],
            "verdict": "NEEDS_IMPROVEMENT",
        }

        # Completeness check — proposal should mention specific tools/commands
        has_tools = any(kw in proposal.lower() for kw in
                        ["nmap", "sqlmap", "hydra", "msf", "gobuster", "nikto",
                         "wpscan", "ffuf", "john", "hashcat", "metasploit", "ssh", "http"])
        if not has_tools:
            critique["findings"].append("No specific tools mentioned — proposal is too abstract")
            critique["score"] -= 25

        # Logic check — should have sequential steps
        has_steps = any(kw in proposal.lower() for kw in ["step", "first", "then", "next", "after", "1.", "2.", "3."])
        if not has_steps:
            critique["findings"].append("No clear sequential steps — execution order unclear")
            critique["score"] -= 20

        # Practicality check — commands should be executable
        has_commands = any(c in proposal for c in ["$", ">", "`", "nmap", "sudo", "curl", "python"])
        if not has_commands:
            critique["findings"].append("No executable commands — cannot verify execution")
            critique["score"] -= 15

        # Risk assessment
        risky = ["rm -rf", "DROP TABLE", "DELETE", "FORMAT", "mkfs", "dd if=", "> /dev/"]
        for r in risky:
            if r.lower() in proposal.lower():
                critique["risks_identified"].append(f"Destructive command detected: {r}")
                critique["score"] -= 30

        # Assumption check
        assumption_words = ["assume", "probably", "should be", "likely", "maybe", "might"]
        for a in assumption_words:
            if a in proposal.lower():
                critique["assumptions_challenged"].append(f"Unverified assumption: '{a}'")
                critique["score"] -= 5

        # Missing critical phases
        if context:
            phases = context.split(",")
            for phase in phases:
                if phase.strip().lower() not in proposal.lower():
                    critique["missing_steps"].append(f"Phase not addressed: {phase.strip()}")

        # Set verdict
        critique["score"] = max(0, critique["score"])
        if critique["score"] >= 80:
            critique["verdict"] = "SOUND"
        elif critique["score"] >= 50:
            critique["verdict"] = "NEEDS_IMPROVEMENT"
        else:
            critique["verdict"] = "WEAK — requires revision"

        self.critic_log.append(critique)
        return critique

    def detect_hallucination(self, response: str, known_facts: List[str] = []) -> List[str]:
        """Detect potential hallucinations in an AI response."""
        hallucinations = []
        for fact in known_facts:
            if fact.lower() not in response.lower():
                hallucinations.append(f"Missing known fact: {fact}")

        # Check for contradictory statements
        contradictions = [
            ("Windows", "Linux"), ("Python 2", "Python 3"),
            ("HTTP", "HTTPS"), ("TCP", "UDP"),
            ("encryption on", "no encryption"), ("firewall enabled", "no firewall"),
        ]
        for a, b in contradictions:
            if a.lower() in response.lower() and b.lower() in response.lower():
                if "not" not in response.lower()[:response.lower().index(b.lower()) + len(b) + 10]:
                    hallucinations.append(f"Contradiction: mentions both {a} and {b}")
        return hallucinations

    def challenge_assumptions(self, proposal: str) -> List[str]:
        """Identify and challenge unstated assumptions."""
        challenges = []
        if "scan" in proposal.lower() and "stealth" not in proposal.lower():
            challenges.append("Assumes scanning won't trigger IDS/alarms")
        if "exploit" in proposal.lower() and "backup" not in proposal.lower():
            challenges.append("Assumes service won't crash during exploitation")
        if "payload" in proposal.lower() and "AV" not in proposal.lower():
            challenges.append("Assumes target has no antivirus/EDR")
        if "post-exploit" in proposal.lower() and "logging" not in proposal.lower():
            challenges.append("Assumes no logging/audit trail detection")
        return challenges

    def stats(self) -> Dict:
        scores = [c["score"] for c in self.critic_log[-50:]]
        return {
            "name": self.name,
            "total_critiques": len(self.critic_log),
            "avg_score": round(sum(scores) / max(len(scores), 1), 1),
            "verdicts": {v: sum(1 for c in self.critic_log if c["verdict"] == v)
                        for v in ["SOUND", "NEEDS_IMPROVEMENT", "WEAK — requires revision"]},
        }


# ── Singleton ──────────────────────────────────────────────────────────
_critic: Optional[CriticAgent] = None

def get_critic() -> CriticAgent:
    global _critic
    if _critic is None:
        _critic = CriticAgent()
    return _critic
