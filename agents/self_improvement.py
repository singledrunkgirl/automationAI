#!/usr/bin/env python3
"""
Self-Improvement System — Agents learn from outcomes, refine strategies.
Tracks success/failure, adapts tool selections, builds knowledge base.
"""

import json, time, os, hashlib, subprocess, shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from collections import defaultdict

if TYPE_CHECKING:
    from .debate_engine import DebateEngine

KNOWLEDGE_DIR = Path("/home/kali/HackWithAI/data/knowledge")
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class SkillRecord:
    """Record of a tool execution and its outcome."""
    tool: str
    target: str
    command: str
    success: bool
    output_preview: str = ""
    duration_ms: int = 0
    lessons: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class StrategyPattern:
    """Learned attack pattern from successful operations."""
    pattern_id: str
    target_type: str  # e.g., "web_app", "windows_host", "linux_server"
    steps: List[str]  # ordered tool sequence
    success_rate: float = 0.0
    uses: int = 0
    avg_duration_ms: int = 0
    tags: List[str] = field(default_factory=list)


class SelfImprovement:
    """
    Tracks all tool executions, learns from outcomes, and adapts strategies.
    Builds a knowledge base of successful attack patterns.
    """

    def __init__(self):
        self.skills: List[SkillRecord] = self._load_skills()
        self.patterns: Dict[str, StrategyPattern] = self._load_patterns()
        self.tool_stats: Dict[str, Dict] = self._compute_tool_stats()
        self.target_types: Dict[str, List[str]] = defaultdict(list)

    def record_execution(self, tool: str, target: str, command: str,
                         success: bool, output: str = "", duration_ms: int = 0,
                         lessons: List[str] = []) -> SkillRecord:
        """Record a tool execution for learning."""
        record = SkillRecord(
            tool=tool, target=target, command=command,
            success=success, output_preview=output[:500],
            duration_ms=duration_ms, lessons=lessons,
        )
        self.skills.append(record)
        self._save_skills()
        self._update_stats(record)
        return record

    def learn_pattern(self, target_type: str, successful_steps: List[str],
                      duration_ms: int = 0) -> StrategyPattern:
        """Create or update a learned attack pattern."""
        # Generate deterministic pattern ID
        key = f"{target_type}:{'|'.join(successful_steps[:5])}"
        pid = hashlib.md5(key.encode()).hexdigest()[:12]

        if pid in self.patterns:
            pattern = self.patterns[pid]
            pattern.uses += 1
            pattern.success_rate = (pattern.success_rate * (pattern.uses - 1) + 1.0) / pattern.uses
            pattern.avg_duration_ms = (pattern.avg_duration_ms * (pattern.uses - 1) + duration_ms) // pattern.uses
        else:
            pattern = StrategyPattern(
                pattern_id=pid, target_type=target_type,
                steps=successful_steps, success_rate=1.0, uses=1,
                avg_duration_ms=duration_ms,
            )
            self.patterns[pid] = pattern

        self._save_patterns()
        return pattern

    def recommend_strategy(self, target: str, target_type: str = "") -> Dict:
        """Recommend the best strategy for a target based on past successes."""
        # Find matching patterns
        candidates = []
        for pid, pattern in self.patterns.items():
            if not target_type or pattern.target_type == target_type:
                score = pattern.success_rate * pattern.uses * 100
                candidates.append((score, pattern))

        candidates.sort(key=lambda x: x[0], reverse=True)

        # Get best tools for this target type
        best_tools = self.get_best_tools(target_type, top_k=5)

        return {
            "target": target,
            "target_type": target_type or "unknown",
            "recommended_patterns": [
                {"id": p.pattern_id, "steps": p.steps, "success_rate": p.success_rate,
                 "uses": p.uses, "avg_duration_ms": p.avg_duration_ms}
                for _, p in candidates[:3]
            ],
            "top_tools": best_tools,
            "total_skills": len(self.skills),
            "total_patterns": len(self.patterns),
        }

    def get_best_tools(self, target_type: str = "", top_k: int = 10) -> List[Dict]:
        """Get tools ranked by success rate for a target type."""
        filtered = [s for s in self.skills if not target_type or target_type in s.target]
        tool_counts: Dict[str, Dict] = {}
        for s in filtered:
            if s.tool not in tool_counts:
                tool_counts[s.tool] = {"total": 0, "successes": 0}
            tool_counts[s.tool]["total"] += 1
            if s.success:
                tool_counts[s.tool]["successes"] += 1

        ranked = []
        for tool, stats in tool_counts.items():
            rate = stats["successes"] / max(stats["total"], 1)
            ranked.append({"tool": tool, "success_rate": round(rate, 2),
                          "total_uses": stats["total"], "successes": stats["successes"]})

        return sorted(ranked, key=lambda x: (x["success_rate"], x["total_uses"]), reverse=True)[:top_k]

    def generate_lessons(self) -> List[str]:
        """Generate lessons learned from all recorded executions."""
        lessons = []
        for skill in self.skills[-100:]:
            if not skill.success:
                lessons.append(f"FAIL @ {skill.tool}: {skill.output_preview[:200]}")
            if skill.lessons:
                lessons.extend(skill.lessons)
        return lessons

    def auto_add_tools(self) -> List[str]:
        """Automatically detect new tools installed in Kali and return their names."""
        # Common Kali tools to detect
        known = [
            "nmap", "masscan", "nc", "tcpdump", "bettercap", "responder", "dnsrecon",
            "msfconsole", "searchsploit", "sqlmap", "hydra", "john", "hashcat",
            "gobuster", "ffuf", "dirsearch", "wpscan", "nikto", "wafw00f", "whatweb",
            "aircrack-ng", "reaver", "wifite", "kismet", "bully", "hcxdumptool",
            "checksec", "radare2", "gdb", "xxd", "strings", "objdump", "upx",
            "exiftool", "theHarvester", "sherlock", "holehe", "h8mail", "dmitry",
            "waybackurls", "gau", "hakrawler", "tor", "torsocks", "proxychains4",
            "cewl", "socat", "chisel", "openssl", "gpg", "hashid", "xortool",
            "evil-winrm", "bloodhound-python", "mimikatz", "smbclient", "enum4linux",
            "msfvenom", "veil", "shellter", "pyarmor", "pyinstaller", "donut",
            "ligolo", "sliver", "empire", "covenant", "nuclei", "trivy", "zaproxy",
            "amass", "subfinder", "naabu", "httpx", "katana", "xsstrike",
        ]
        new_tools = []
        for tool in known:
            try:
                r = subprocess.run(["which", tool], capture_output=True, text=True, timeout=3)
                if r.returncode == 0 and tool not in self.tool_stats:
                    new_tools.append(tool)
                    self.tool_stats[tool] = {"total": 0, "successes": 0}
            except Exception:
                pass
        if new_tools:
            self._save_skills()
        return new_tools

    def evolve_prompts(self, debate_engine: "DebateEngine") -> Dict:
        """Check agent win rates; if any agent below 30% win rate, update prompts."""
        updates = {}
        for agent in debate_engine.agents:
            total = agent.wins + agent.losses
            if total < 3:
                continue
            win_rate = agent.wins / total
            if win_rate < 0.30:
                old_personality = agent.personality
                agent.personality = f"aggressive and adaptive (was: {old_personality})"
                agent.confidence = max(0.3, agent.confidence)
                updates[agent.name] = {
                    "old_win_rate": round(win_rate, 2),
                    "old_personality": old_personality,
                    "new_personality": agent.personality,
                }
        return updates

    def analyze_mission(self, debate_result: Dict) -> List[str]:
        """Analyze a completed debate mission and return improvement notes."""
        notes = []
        winner = debate_result.get("final_winner", "")
        target = debate_result.get("target", "unknown")

        # Check if consensus was low
        if debate_result.get("consensus_pct", 0) < 0.5:
            notes.append(f"Low consensus ({debate_result['consensus_pct']:.0%}) on {target} — "
                        f"agents disagreed significantly")

        # Check round-by-round for fluctuations
        rounds = debate_result.get("rounds", [])
        if len(rounds) >= 2:
            winners = [r.get("winner") for r in rounds]
            if len(set(winners)) > 1:
                notes.append(f"Split voting on {target} — rounds had different winners: {winners}")

        # Record winning strategy length as a metric
        strategy = debate_result.get("winning_strategy", "")
        if len(strategy) < 50:
            notes.append(f"Short strategy for {target} — may need more detail")

        return notes

    def stats(self) -> Dict:
        return {
            "total_executions": len(self.skills),
            "success_rate": round(
                sum(1 for s in self.skills if s.success) / max(len(self.skills), 1), 2
            ),
            "total_patterns": len(self.patterns),
            "top_tools": self.get_best_tools(top_k=10),
            "recent_failures": len([s for s in self.skills[-20:] if not s.success]),
            "knowledge_files": len(list(KNOWLEDGE_DIR.glob("*.json"))),
        }

    # ── Internal helpers ─────────────────────────────────────────────────

    def _update_stats(self, record: SkillRecord):
        if record.tool not in self.tool_stats:
            self.tool_stats[record.tool] = {"total": 0, "successes": 0}
        self.tool_stats[record.tool]["total"] += 1
        if record.success:
            self.tool_stats[record.tool]["successes"] += 1

    def _compute_tool_stats(self) -> Dict:
        stats = {}
        for s in self.skills:
            if s.tool not in stats:
                stats[s.tool] = {"total": 0, "successes": 0}
            stats[s.tool]["total"] += 1
            if s.success:
                stats[s.tool]["successes"] += 1
        return stats

    def _save_skills(self):
        with open(KNOWLEDGE_DIR / "skills.json", "w") as f:
            json.dump(
                [{"tool": s.tool, "target": s.target, "command": s.command,
                  "success": s.success, "output": s.output_preview,
                  "duration_ms": s.duration_ms, "lessons": s.lessons,
                  "timestamp": s.timestamp}
                 for s in self.skills[-1000:]],  # Keep last 1000
                f, indent=2)

    def _load_skills(self) -> List[SkillRecord]:
        path = KNOWLEDGE_DIR / "skills.json"
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                return [SkillRecord(**d) for d in data]
            except Exception:
                pass
        return []

    def _save_patterns(self):
        with open(KNOWLEDGE_DIR / "patterns.json", "w") as f:
            json.dump({
                pid: {"pattern_id": p.pattern_id, "target_type": p.target_type,
                      "steps": p.steps, "success_rate": p.success_rate,
                      "uses": p.uses, "avg_duration_ms": p.avg_duration_ms,
                      "tags": p.tags}
                for pid, p in self.patterns.items()
            }, f, indent=2)

    def _load_patterns(self) -> Dict[str, StrategyPattern]:
        path = KNOWLEDGE_DIR / "patterns.json"
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                return {pid: StrategyPattern(**d) for pid, d in data.items()}
            except Exception:
                pass
        return {}


# ── Singleton ────────────────────────────────────────────────────────────
_improver: Optional[SelfImprovement] = None

def get_improver() -> SelfImprovement:
    global _improver
    if _improver is None:
        _improver = SelfImprovement()
    return _improver


# ── SelfImprovementEngine wrapper ───────────────────────────────────────

class SelfImprovementEngine:
    """High-level wrapper around SelfImprovement for debate integration."""

    def __init__(self, debate_engine: "DebateEngine" = None):
        self.core = get_improver()
        self.debate_engine = debate_engine
        self.improvement_log: List[Dict] = []

    def analyze_mission(self, debate_result: Dict) -> List[str]:
        """Analyze completed mission and return improvement notes."""
        notes = self.core.analyze_mission(debate_result)
        self.improvement_log.append({
            "timestamp": datetime.now().isoformat(),
            "debate_id": debate_result.get("debate_id", ""),
            "target": debate_result.get("target", ""),
            "notes": notes,
        })
        return notes

    def learn_from_result(self, debate_result: Dict, execution_success: bool):
        """Learn from a completed debate + execution outcome."""
        winner = debate_result.get("final_winner", "")
        if execution_success:
            self.core.record_execution(
                tool="debate_strategy", target=debate_result.get("target", ""),
                command=debate_result.get("winning_strategy", ""),
                success=True,
                lessons=[f"Agent {winner} strategy worked"],
            )
            if self.debate_engine:
                agent = self.debate_engine.get_agent(winner)
                if agent:
                    agent.confidence = min(1.0, agent.confidence + 0.15)
        else:
            self.core.record_execution(
                tool="debate_strategy", target=debate_result.get("target", ""),
                command=debate_result.get("winning_strategy", ""),
                success=False,
                lessons=[f"Agent {winner} strategy failed — need improvement"],
            )
            self.evolve_prompts()

    def evolve_prompts(self) -> Dict:
        """Check agent win rates and evolve prompts for underperformers."""
        if not self.debate_engine:
            return {}
        result = self.core.evolve_prompts(self.debate_engine)
        if result:
            self.improvement_log.append({
                "timestamp": datetime.now().isoformat(),
                "action": "evolve_prompts",
                "updates": result,
            })
        return result

    def auto_add_tools(self) -> List[str]:
        """Detect and register newly installed Kali tools."""
        return self.core.auto_add_tools()

    def stats(self) -> Dict:
        return {
            "core_stats": self.core.stats(),
            "improvement_entries": len(self.improvement_log),
        }


# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    si = SelfImprovement()

    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if cmd == "stats":
        print(json.dumps(si.stats(), indent=2))
    elif cmd == "recommend":
        target = sys.argv[2] if len(sys.argv) > 2 else "example.com"
        target_type = sys.argv[3] if len(sys.argv) > 3 else ""
        print(json.dumps(si.recommend_strategy(target, target_type), indent=2))
    elif cmd == "record":
        si.record_execution(
            tool=sys.argv[2], target=sys.argv[3], command=sys.argv[4],
            success=sys.argv[5].lower() == "true",
            lessons=sys.argv[6:] if len(sys.argv) > 6 else [],
        )
        print("Recorded")
    elif cmd == "lessons":
        print("\n".join(si.generate_lessons()[:20]))
    else:
        print("Commands: stats | recommend <target> | record <tool> <target> <cmd> <true|false> | lessons")
