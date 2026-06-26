#!/usr/bin/env python3
"""
Reviewer Agent — Evaluates quality, checks completeness, scores responses.
"""

import json, time, re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

LOG_DIR = Path("/home/kali/HackWithAI/data/logs")


class ReviewerAgent:
    """Reviews proposals and responses, providing quality scores and feedback."""

    def __init__(self, name: str = "ReviewerBot"):
        self.name = name
        self.review_log: List[Dict] = []

    def review(self, content: str, criteria: List[str] = [],
               context: str = "", source_agent: str = "") -> Dict:
        """
        Review content against quality criteria and return a structured review.
        """
        if not criteria:
            criteria = ["completeness", "clarity", "correctness", "conciseness", "actionability"]

        review = {
            "source": source_agent,
            "timestamp": datetime.now().isoformat(),
            "overall_score": 0,
            "criteria_scores": {},
            "feedback": [],
            "verdict": "NEEDS_WORK",
        }

        scores = {}
        word_count = len(content.split())

        for criterion in criteria:
            if criterion == "completeness":
                s = min(100, max(0, word_count * 2)) if word_count > 10 else 20
            elif criterion == "clarity":
                has_structure = any(kw in content.lower() for kw in
                                   ["1.", "step", "first", ":", "strategy", "recommend"])
                s = 75 if has_structure and word_count > 20 else 40
            elif criterion == "correctness":
                errors = ["undefined", "null", "error", "exception", "failed", "cannot"]
                error_count = sum(1 for e in errors if e in content.lower())
                s = max(10, 100 - error_count * 15)
            elif criterion == "conciseness":
                s = 90 if word_count < 300 else max(30, 100 - (word_count - 300) // 5)
            elif criterion == "actionability":
                has_commands = bool(re.search(r"(nmap|sqlmap|hydra|msf|curl|ssh|python|bash)", content.lower()))
                s = 85 if has_commands else 30
            else:
                s = 50
            scores[criterion] = min(100, max(0, s))

        review["criteria_scores"] = scores
        review["overall_score"] = round(sum(scores.values()) / max(len(scores), 1), 1)

        # Feedback
        for criterion, score in scores.items():
            if score < 50:
                review["feedback"].append(f"{criterion}: needs significant improvement (score: {score})")
            elif score < 75:
                review["feedback"].append(f"{criterion}: acceptable but could improve (score: {score})")

        if review["overall_score"] >= 85:
            review["verdict"] = "EXCELLENT"
        elif review["overall_score"] >= 70:
            review["verdict"] = "GOOD"
        elif review["overall_score"] >= 50:
            review["verdict"] = "NEEDS_WORK"
        else:
            review["verdict"] = "POOR — requires revision"

        self.review_log.append(review)
        return review

    def compare(self, proposal_a: str, proposal_b: str,
                context: str = "") -> Dict[str, Dict]:
        """Compare two proposals and determine the better one."""
        review_a = self.review(proposal_a)
        review_b = self.review(proposal_b)

        winner = "proposal_a" if review_a["overall_score"] > review_b["overall_score"] else "proposal_b"
        if review_a["overall_score"] == review_b["overall_score"]:
            winner = "tie"

        return {
            "proposal_a": review_a,
            "proposal_b": review_b,
            "winner": winner,
            "margin": abs(review_a["overall_score"] - review_b["overall_score"]),
        }

    def stats(self) -> Dict:
        scores = [r["overall_score"] for r in self.review_log[-50:]]
        return {
            "name": self.name,
            "total_reviews": len(self.review_log),
            "avg_score": round(sum(scores) / max(len(scores), 1), 1),
            "verdicts": {v: sum(1 for r in self.review_log if r["verdict"] == v)
                        for v in ["EXCELLENT", "GOOD", "NEEDS_WORK", "POOR — requires revision"]},
        }


# ── Singleton ──────────────────────────────────────────────────────────
_reviewer: Optional[ReviewerAgent] = None

def get_reviewer() -> ReviewerAgent:
    global _reviewer
    if _reviewer is None:
        _reviewer = ReviewerAgent()
    return _reviewer
