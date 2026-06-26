#!/usr/bin/env python3
"""
Consensus Engine — Voting, confidence scoring, tiebreaker, top-2 faceoff.
Integrates with DebateEngine for multi-round voting.
"""

import json, time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

LOG_DIR = Path("/home/kali/HackWithAI/data/logs/consensus")
LOG_DIR.mkdir(parents=True, exist_ok=True)


class ConsensusEngine:
    """Multi-round consensus with voting, confidence, and tiebreakers."""

    def __init__(self, threshold: float = 0.6, max_rounds: int = 5):
        self.threshold = threshold
        self.max_rounds = max_rounds
        self.rounds: List[Dict] = []

    def round_vote(self, proposals: Dict[str, str], voters: List[str],
                   votes: Dict[str, str], round_num: int = 1) -> Tuple[str, Dict, float]:
        """
        Tally votes and determine round winner.
        Returns (winner_name, tally_dict, agreement_pct).
        """
        tally: Dict[str, int] = {}
        for voter, chosen in votes.items():
            if chosen in proposals:
                tally[chosen] = tally.get(chosen, 0) + 1

        if not tally:
            # All self-votes — pick first
            winner = list(proposals.keys())[0]
            tally = {winner: len(voters)}
        else:
            winner = max(tally, key=tally.get)

        agreement = tally[winner] / max(len(voters), 1)

        round_record = {
            "round": round_num,
            "winner": winner,
            "tally": tally,
            "agreement_pct": round(agreement, 2),
            "votes": votes,
        }
        self.rounds.append(round_record)

        return winner, tally, agreement

    def run_tiebreaker(self, proposals: Dict[str, str], voters: List[str],
                       tied_agents: List[str]) -> Tuple[str, Dict]:
        """Top-2 faceoff when no clear consensus."""
        # Only present the tied agents' proposals
        top_proposals = {k: proposals[k] for k in tied_agents if k in proposals}
        if not top_proposals:
            return tied_agents[0], {}

        # Simple preference: vote for the agent with more wins in prior rounds
        scores: Dict[str, int] = {}
        for r in self.rounds:
            w = r.get("winner", "")
            if w in top_proposals:
                scores[w] = scores.get(w, 0) + 1

        if scores:
            winner = max(scores, key=scores.get)
            return winner, scores

        return tied_agents[0], {}

    def is_consensus_reached(self, agreement: float) -> bool:
        return agreement >= self.threshold

    def finalize(self, session_id: str, winner: str, proposals: Dict[str, str],
                 total_rounds: int) -> Dict:
        """Generate final consensus record."""
        record = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "winner": winner,
            "winning_proposal": proposals.get(winner, "")[:500],
            "total_rounds": total_rounds,
            "threshold": self.threshold,
            "rounds": self.rounds[-total_rounds:],
        }

        # Save to disk
        log_file = LOG_DIR / f"{session_id}_{int(time.time())}.json"
        with open(log_file, "w") as f:
            json.dump(record, f, indent=2)

        return record

    def stats(self) -> Dict:
        return {
            "threshold": self.threshold,
            "max_rounds": self.max_rounds,
            "total_rounds_run": len(self.rounds),
            "log_files": len(list(LOG_DIR.glob("*.json"))),
        }


# ── Singleton ──────────────────────────────────────────────────────────
_consensus: Optional[ConsensusEngine] = None

def get_consensus() -> ConsensusEngine:
    global _consensus
    if _consensus is None:
        _consensus = ConsensusEngine()
    return _consensus
