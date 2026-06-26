#!/usr/bin/env python3
"""
Revision Agent — Improves responses by merging critic and reviewer feedback.
Produces final revised answers.
"""

import json, time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

LOG_DIR = Path("/home/kali/HackWithAI/data/logs/revisions")
LOG_DIR.mkdir(parents=True, exist_ok=True)


class RevisionAgent:
    """Revises proposals based on critic and reviewer feedback."""

    def __init__(self, name: str = "RevisionBot"):
        self.name = name
        self.revision_log: List[Dict] = []

    def revise(self, original: str, critic_report: Dict, reviewer_report: Dict,
               source_agent: str = "", target: str = "") -> Dict:
        """
        Produce an improved version incorporating all feedback.
        """
        revision = {
            "original": original[:500],
            "source": source_agent,
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "changes_applied": [],
            "improvement_score": 0,
        }

        improved = original

        # Apply critic findings
        for finding in critic_report.get("findings", []):
            if "No specific tools" in finding:
                improved = self._add_tool_specificity(improved)
                revision["changes_applied"].append("Added specific tool references")
            if "No clear sequential steps" in finding:
                improved = self._add_sequential_steps(improved)
                revision["changes_applied"].append("Added sequential numbering")

        # Apply critic missing steps
        for step in critic_report.get("missing_steps", []):
            improved += f"\n\nAddressed missing phase: {step}"
            revision["changes_applied"].append(f"Addressed missing phase: {step}")

        # Apply reviewer feedback
        fb_text = " ".join(reviewer_report.get("feedback", []))
        if "completeness" in fb_text:
            improved = self._enhance_completeness(improved)
            revision["changes_applied"].append("Enhanced completeness")
        if "actionability" in fb_text:
            improved = self._enhance_actionability(improved)
            revision["changes_applied"].append("Added actionable commands")

        # Calculate improvement
        original_score = reviewer_report.get("overall_score", 50)
        revision["improvement_score"] = min(100, original_score +
                                            len(revision["changes_applied"]) * 10)

        revision["revised_text"] = improved[:2000]

        self.revision_log.append(revision)

        # Save to disk
        log_file = LOG_DIR / f"revision_{source_agent}_{int(time.time())}.json"
        with open(log_file, "w") as f:
            json.dump(revision, f, indent=2)

        return revision

    def _add_tool_specificity(self, text: str) -> str:
        if "nmap" not in text.lower():
            text += "\n\nUse nmap -sV -sC -O <target> for comprehensive scanning."
        if "gobuster" not in text.lower() and "dir" in text.lower():
            text += "\n\nUse gobuster dir -u <url> -w /usr/share/wordlists/dirb/common.txt for directory enumeration."
        return text

    def _add_sequential_steps(self, text: str) -> str:
        if "1." not in text and "Step 1" not in text:
            steps = text.split("\n")
            numbered = []
            count = 1
            for line in steps:
                stripped = line.strip()
                if stripped and len(stripped) > 10:
                    numbered.append(f"{count}. {stripped}")
                    count += 1
                else:
                    numbered.append(stripped)
            return "\n".join(numbered)
        return text

    def _enhance_completeness(self, text: str) -> str:
        return text + "\n\nEnsure all phases are covered: recon → exploit → payload → post-exploit → evasion."

    def _enhance_actionability(self, text: str) -> str:
        return text + "\n\nActionable Quick-Start: Run the first command to begin."

    def stats(self) -> Dict:
        scores = [r["improvement_score"] for r in self.revision_log[-50:]]
        return {
            "name": self.name,
            "total_revisions": len(self.revision_log),
            "avg_improvement": round(sum(scores) / max(len(scores), 1), 1),
            "log_files": len(list(LOG_DIR.glob("*.json"))),
        }


# ── Singleton ──────────────────────────────────────────────────────────
_revision: Optional[RevisionAgent] = None

def get_revision() -> RevisionAgent:
    global _revision
    if _revision is None:
        _revision = RevisionAgent()
    return _revision
