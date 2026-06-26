#!/usr/bin/env python3
"""
Reflection Engine — Self-critique, failure analysis, lessons learned.
Integrates with Hermes pipeline for continuous improvement.
"""

import json, time, sqlite3, hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

DATA_DIR = Path("/home/kali/HackWithAI/data/logs/reflections")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "reflections.db"


class FailureAnalyzer:
    """Classifies failures into categories with root cause analysis."""

    CATEGORIES = [
        "hallucination", "missing_steps", "tool_misuse",
        "insufficient_context", "low_confidence", "logic_error",
        "provider_error", "timeout", "unknown"
    ]

    def __init__(self):
        self.failures: List[Dict] = []
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS failures (
                id TEXT PRIMARY KEY, category TEXT, task_id TEXT,
                agent TEXT, target TEXT, description TEXT,
                root_cause TEXT, timestamp TEXT
            )""")
            db.commit()

    def classify(self, error_text: str, context: str = "") -> Dict:
        """Classify a failure into a category and suggest root cause."""
        low = (error_text + " " + context).lower()

        classification = None
        root_cause = ""

        if any(w in low for w in ["hallucinat", "made up", "fabricat", "invent"]):
            classification = "hallucination"
            root_cause = "AI generated content without factual basis"
        elif any(w in low for w in ["missing step", "skipped", "not covered", "forgot"]):
            classification = "missing_steps"
            root_cause = "Incomplete task decomposition"
        elif any(w in low for w in ["tool", "command not found", "execution fail", "error code"]):
            classification = "tool_misuse"
            root_cause = "Incorrect tool usage or parameters"
        elif any(w in low for w in ["context", "not enough info", "unclear", "ambiguous"]):
            classification = "insufficient_context"
            root_cause = "Insufficient information provided to agent"
        elif any(w in low for w in ["confidence", "uncertain", "might", "maybe", "not sure"]):
            classification = "low_confidence"
            root_cause = "Agent reported low confidence in response"
        elif any(w in low for w in ["logic", "contradict", "inconsist", "wrong answer"]):
            classification = "logic_error"
            root_cause = "Logical flaw in reasoning chain"
        elif any(w in low for w in ["api key", "provider", "openrouter", "timeout", "rate limit"]):
            classification = "provider_error"
            root_cause = "AI provider API failure"
        elif any(w in low for w in ["timeout", "timed out"]):
            classification = "timeout"
            root_cause = "Operation exceeded time limit"
        else:
            classification = "unknown"
            root_cause = "Unclassified error"

        return {"category": classification, "root_cause": root_cause}

    def record(self, task_id: str, agent: str, target: str,
               error: str, context: str = "") -> str:
        """Record a failure for analysis."""
        analysis = self.classify(error, context)
        fid = hashlib.md5(f"{task_id}{agent}{time.time()}".encode()).hexdigest()[:12]

        record = {
            "id": fid, "category": analysis["category"],
            "task_id": task_id, "agent": agent, "target": target,
            "description": error[:500], "root_cause": analysis["root_cause"],
            "timestamp": datetime.now().isoformat(),
        }
        self.failures.append(record)

        with sqlite3.connect(DB_PATH) as db:
            db.execute("INSERT INTO failures VALUES (?,?,?,?,?,?,?,?)",
                      (fid, analysis["category"], task_id, agent, target,
                       error[:500], analysis["root_cause"], record["timestamp"]))
            db.commit()

        return fid

    def get_by_category(self, category: str = "", limit: int = 50) -> List[Dict]:
        with sqlite3.connect(DB_PATH) as db:
            db.row_factory = sqlite3.Row
            if category:
                rows = db.execute("SELECT * FROM failures WHERE category=? ORDER BY timestamp DESC LIMIT ?",
                                 (category, limit)).fetchall()
            else:
                rows = db.execute("SELECT * FROM failures ORDER BY timestamp DESC LIMIT ?",
                                 (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_trends(self) -> Dict:
        """Get failure trends by category."""
        with sqlite3.connect(DB_PATH) as db:
            rows = db.execute(
                "SELECT category, COUNT(*) as cnt FROM failures GROUP BY category ORDER BY cnt DESC"
            ).fetchall()
            categories = {r[0]: r[1] for r in rows}
            total = sum(categories.values())

            # Top 3 root causes
            top_rows = db.execute(
                "SELECT root_cause, COUNT(*) as cnt FROM failures GROUP BY root_cause ORDER BY cnt DESC LIMIT 5"
            ).fetchall()

        return {
            "total_failures": total,
            "by_category": categories,
            "most_common": categories.get(max(categories, key=categories.get), "") if categories else "",
            "top_root_causes": [{"cause": r[0], "count": r[1]} for r in top_rows],
        }


class LessonsEngine:
    """Persists and retrieves lessons learned from past operations."""

    def __init__(self):
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS lessons (
                lesson_id TEXT PRIMARY KEY, category TEXT,
                problem TEXT, solution TEXT, agent TEXT,
                confidence REAL, source_task TEXT, timestamp TEXT
            )""")
            db.commit()

    def add(self, category: str, problem: str, solution: str,
            agent: str = "", confidence: float = 0.7, source_task: str = "") -> str:
        lid = hashlib.md5(f"{category}{problem}{time.time()}".encode()).hexdigest()[:12]

        with sqlite3.connect(DB_PATH) as db:
            db.execute("INSERT INTO lessons VALUES (?,?,?,?,?,?,?,?)",
                      (lid, category, problem[:500], solution[:500], agent,
                       confidence, source_task, datetime.now().isoformat()))
            db.commit()
        return lid

    def query(self, category: str = "", keyword: str = "",
              min_confidence: float = 0.0, limit: int = 20) -> List[Dict]:
        sql = "SELECT * FROM lessons WHERE 1=1"
        params: List = []

        if category:
            sql += " AND category = ?"; params.append(category)
        if keyword:
            sql += " AND (problem LIKE ? OR solution LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if min_confidence > 0:
            sql += " AND confidence >= ?"; params.append(min_confidence)

        sql += " ORDER BY timestamp DESC LIMIT ?"; params.append(limit)

        with sqlite3.connect(DB_PATH) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def get_context_for_task(self, task_description: str, top_k: int = 5) -> str:
        """Retrieve relevant lessons for injection into a new task."""
        words = task_description.split()[:10]
        results = []
        for w in words:
            lessons = self.query(keyword=w, min_confidence=0.5, limit=3)
            results.extend(lessons)

        # Deduplicate by lesson_id
        seen = set()
        unique = []
        for r in results:
            if r["lesson_id"] not in seen:
                seen.add(r["lesson_id"])
                unique.append(r)
                if len(unique) >= top_k:
                    break

        if not unique:
            return ""

        context = "Past lessons relevant to this task:\n"
        for u in unique:
            context += f"- [{u['category']}] {u['problem']} → Solution: {u['solution']}\n"
        return context

    def stats(self) -> Dict:
        with sqlite3.connect(DB_PATH) as db:
            total = db.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
            cats = db.execute("SELECT category, COUNT(*) FROM lessons GROUP BY category").fetchall()
        return {
            "total_lessons": total,
            "categories": {c[0]: c[1] for c in cats},
        }


class PatternDetector:
    """Detects repeated mistakes, frequent tool failures, common weaknesses."""

    def __init__(self, failure_analyzer: FailureAnalyzer):
        self.analyzer = failure_analyzer

    def detect(self, window: int = 50) -> Dict:
        """Analyze recent failures for patterns."""
        failures = self.analyzer.get_by_category(limit=window)
        if not failures:
            return {"patterns": [], "alert": False}

        # Frequency analysis
        cat_counts: Dict[str, int] = defaultdict(int)
        agent_counts: Dict[str, int] = defaultdict(int)
        for f in failures:
            cat_counts[f["category"]] += 1
            agent_counts[f.get("agent", "unknown")] += 1

        patterns = []
        total = len(failures)

        # Category patterns
        for cat, count in cat_counts.items():
            rate = count / max(total, 1)
            if rate > 0.3:
                patterns.append({
                    "type": "repeated_category",
                    "category": cat,
                    "count": count,
                    "rate": round(rate, 2),
                    "severity": "HIGH" if rate > 0.5 else "MEDIUM",
                })

        # Agent patterns
        for agent, count in agent_counts.items():
            rate = count / max(total, 1)
            if rate > 0.3 and agent != "unknown":
                patterns.append({
                    "type": "agent_weakness",
                    "agent": agent,
                    "failure_rate": round(rate, 2),
                })

        return {
            "patterns": patterns,
            "alert": len(patterns) > 0,
            "total_failures": total,
            "window": window,
        }

    def trend_report(self) -> str:
        analysis = self.detect()
        if not analysis["alert"]:
            return "No significant failure patterns detected."

        lines = ["Failure Pattern Analysis:", ""]
        for p in analysis["patterns"]:
            if p["type"] == "repeated_category":
                lines.append(f"  [{p['severity']}] {p['category']}: {p['count']}/{analysis['total_failures']} failures ({p['rate']:.0%})")
            elif p["type"] == "agent_weakness":
                lines.append(f"  [WEAKNESS] {p['agent']}: {p['failure_rate']:.0%} failure rate")
        return "\n".join(lines)


class ReflectionEngine:
    """Central reflection system — evaluates quality, identifies weaknesses, recommends improvements."""

    def __init__(self):
        self.failure_analyzer = FailureAnalyzer()
        self.lessons_engine = LessonsEngine()
        self.pattern_detector = PatternDetector(self.failure_analyzer)

    def reflect(self, task: str, response: str, critic_report: Dict = {},
                reviewer_report: Dict = {}, agent: str = "", task_id: str = "") -> Dict:
        """
        Full reflection: evaluate quality, detect issues, derive lessons, store.
        """
        reflection = {
            "task_id": task_id or hashlib.md5(task.encode()).hexdigest()[:10],
            "agent": agent,
            "timestamp": datetime.now().isoformat(),
            "quality_score": reviewer_report.get("overall_score", 50),
            "issues_found": [],
            "lessons_derived": [],
            "recommendations": [],
            "context_for_next": "",
        }

        # Quality evaluation
        critic_score = critic_report.get("score", 50)
        reviewer_score = reviewer_report.get("overall_score", 50)
        reflection["quality_score"] = round((critic_score + reviewer_score) / 2, 1)

        # Identify issues from critic
        for finding in critic_report.get("findings", []):
            reflection["issues_found"].append({"source": "critic", "issue": finding})

        # Identify issues from reviewer
        for fb in reviewer_report.get("feedback", []):
            reflection["issues_found"].append({"source": "reviewer", "issue": fb})

        # Record failures if quality is low
        if reflection["quality_score"] < 60:
            error_desc = "; ".join(i["issue"] for i in reflection["issues_found"])
            fid = self.failure_analyzer.record(
                task_id or f"task_{int(time.time())}",
                agent, task, error_desc, response
            )
            reflection["failure_id"] = fid

        # Derive lessons
        for issue in reflection["issues_found"]:
            if "tool" in issue["issue"].lower() or "command" in issue["issue"].lower():
                lid = self.lessons_engine.add(
                    "tool_usage", issue["issue"],
                    "Verify tool parameters and check documentation before execution",
                    agent, 0.6, task_id
                )
                reflection["lessons_derived"].append(lid)
            elif "step" in issue["issue"].lower() or "missing" in issue["issue"].lower():
                lid = self.lessons_engine.add(
                    "task_planning", issue["issue"],
                    "Break tasks into smaller sequential steps with clear tool assignments",
                    agent, 0.7, task_id
                )
                reflection["lessons_derived"].append(lid)
            elif "logic" in issue["issue"].lower() or "reasoning" in issue["issue"].lower():
                lid = self.lessons_engine.add(
                    "logic", issue["issue"],
                    "Cross-check reasoning with established facts and known-good patterns",
                    agent, 0.8, task_id
                )
                reflection["lessons_derived"].append(lid)

        # Recommendations
        patterns = self.pattern_detector.detect()
        if patterns["alert"]:
            reflection["recommendations"].append("Review failure patterns and adjust agent prompts")
            reflection["recommendations"].append(patterns)

        # Context for next task
        if task_id:
            reflection["context_for_next"] = self.lessons_engine.get_context_for_task(task)

        return reflection

    def stats(self) -> Dict:
        return {
            "failure_analyzer": self.failure_analyzer.get_trends(),
            "lessons_engine": self.lessons_engine.stats(),
            "pattern_detector": self.pattern_detector.detect(),
        }


# ── Singleton ──────────────────────────────────────────────────────────
_engine: Optional[ReflectionEngine] = None

def get_reflection() -> ReflectionEngine:
    global _engine
    if _engine is None:
        _engine = ReflectionEngine()
    return _engine


# ── CLI ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    r = ReflectionEngine()

    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"

    if cmd == "reflect":
        task = " ".join(sys.argv[2:]) or "test task"
        result = r.reflect(task, task,
                          {"score": 70, "findings": ["No specific tools mentioned"]},
                          {"overall_score": 65, "feedback": ["clarity: needs improvement"]})
        print(json.dumps(result, indent=2))

    elif cmd == "stats":
        print(json.dumps(r.stats(), indent=2))

    elif cmd == "lessons":
        keyword = sys.argv[2] if len(sys.argv) > 2 else ""
        lessons = r.lessons_engine.query(keyword=keyword)
        print(f"Found {len(lessons)} lessons")
        for l in lessons[:10]:
            print(f"  [{l['category']}] {l['problem'][:80]} → {l['solution'][:80]}")

    elif cmd == "failures":
        trends = r.failure_analyzer.get_trends()
        print(json.dumps(trends, indent=2))

    elif cmd == "patterns":
        print(r.pattern_detector.trend_report())

    else:
        print("Commands: reflect <task> | stats | lessons | failures | patterns")
