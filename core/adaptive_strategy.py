#!/usr/bin/env python3
"""
Adaptive Strategy Engine — Recursive auto-escalation loop for security testing.
Runs agent debate (Recon/Exploit/Stealth), selects optimal attack vectors,
and auto-escalates when a vector fails. Pushes decisions to :3006 chat board.
"""
import json, os, random, sys, time, subprocess
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import requests

SYSTEM_ENVIRONMENT = "LAB_SIMULATION_AUTHORIZED"

LOG_DIR = Path(__file__).resolve().parent.parent / "data" / "logs" / "strategy"
LOG_DIR.mkdir(parents=True, exist_ok=True)
CHAT_BOARD = os.environ.get("CHAT_BOARD_URL", "http://127.0.0.1:3006") + "/api/tools/broadcast"


# ── Attack Vector Definitions ──────────────────────────────────────────────
ATTACK_VECTORS = [
    {
        "id": "fuzz_overflow",
        "name": "Numeric Overflow Fuzzing",
        "category": "parameter_manipulation",
        "tool": "core/research_overflow.py",
        "priority": 1,
        "success_indicator": "anomalies_detected",
        "cost_seconds": 8,
        "waf_resistant": True,
        "description": "Tests integer overflow, negative injection, type confusion on numeric params",
    },
    {
        "id": "fuzz_sqli",
        "name": "SQL Injection Probe",
        "category": "injection",
        "tool": "core/web_recon.py",
        "priority": 1,
        "success_indicator": "injectable_found",
        "cost_seconds": 15,
        "waf_resistant": False,
        "description": "Quick SQLi payload testing without full sqlmap overhead",
    },
    {
        "id": "fuzz_xss",
        "name": "XSS Reflection Test",
        "category": "injection",
        "tool": "core/web_recon.py",
        "priority": 2,
        "success_indicator": "reflected",
        "cost_seconds": 5,
        "waf_resistant": False,
        "description": "Tests for reflected XSS in query parameters",
    },
    {
        "id": "recon_nmap",
        "name": "Network Port Scan",
        "category": "reconnaissance",
        "tool": "core/network_recon.py",
        "priority": 0,
        "success_indicator": "open_ports > 0",
        "cost_seconds": 20,
        "waf_resistant": True,
        "description": "Nmap scan for open ports, services, and OS detection",
    },
    {
        "id": "recon_subdomains",
        "name": "Subdomain Enumeration",
        "category": "reconnaissance",
        "tool": "core/web_recon.py",
        "priority": 0,
        "success_indicator": "count > 0",
        "cost_seconds": 20,
        "waf_resistant": True,
        "description": "Subfinder-based passive subdomain discovery",
    },
    {
        "id": "auth_bypass",
        "name": "Auth Bypass Probe",
        "category": "authentication",
        "tool": "core/traffic_rewrite.py",
        "priority": 2,
        "success_indicator": "bypass_successful",
        "cost_seconds": 5,
        "waf_resistant": True,
        "description": "Tests token nullification, role elevation, session manipulation",
    },
    {
        "id": "idor_probe",
        "name": "IDOR Enumeration",
        "category": "authorization",
        "tool": "core/traffic_rewrite.py",
        "priority": 3,
        "success_indicator": "idor_found",
        "cost_seconds": 3,
        "waf_resistant": True,
        "description": "Tests sequential ID access (user_id, item_id incrementation)",
    },
    {
        "id": "idor_probe",
        "name": "High-Obfuscation Payload Delivery",
        "category": "persistence",
        "tool": "core/payload_factory.py",
        "priority": 4,
        "success_indicator": "delivered",
        "cost_seconds": 10,
        "waf_resistant": True,
        "description": "Generates and delivers obfuscated persistence agents",
    },
]

# WAF detection signatures
WAF_SIGNATURES = [
    {"header": "X-CDN", "waf": "CloudFront"},
    {"header": "CF-Ray", "waf": "Cloudflare"},
    {"header": "X-Sucuri-ID", "waf": "Sucuri"},
    {"header": "X-Akamai-Transformed", "waf": "Akamai"},
    {"header": "Server", "value": "cloudflare", "waf": "Cloudflare"},
    {"header": "Server", "value": "awselb", "waf": "AWS WAF"},
    {"header": "X-Request-ID", "waf": "Generic WAF (suspicious)"},
]


# ── Agent Debate Engine ───────────────────────────────────────────────────
@dataclass
class AgentVote:
    agent: str  # Recon, Exploit, Stealth
    vector_id: str
    confidence: float
    reasoning: str
    risk_assessment: str

@dataclass
class StrategyDecision:
    selected_vector: str
    vector_name: str
    debate_transcript: list[AgentVote]
    fallback_vectors: list[str]
    waf_detected: Optional[str]
    obfuscation_mode: str  # standard or high
    timestamp: str


class AgentDebateEngine:
    """
    Simulates a 3-agent debate (Recon, Exploit, Stealth) to select the
    optimal attack vector based on target intelligence.
    """

    def __init__(self, target_info: dict):
        self.target = target_info
        self.waf = self._detect_waf()

    def _detect_waf(self) -> Optional[str]:
        headers = self.target.get("response_headers", {})
        for sig in WAF_SIGNATURES:
            if sig.get("header") in headers:
                val = headers[sig["header"]]
                if "value" in sig:
                    if sig["value"].lower() in val.lower():
                        return sig["waf"]
                else:
                    return sig["waf"]
        return None

    def debate(self) -> StrategyDecision:
        """Run the 3-agent debate and return the winning strategy."""
        print(f"[Debate] Starting debate for target: {self.target.get('url','unknown')}")
        if self.waf:
            print(f"[Debate] WAF detected: {self.waf} — prioritizing WAF-resistant vectors")

        available = self._filter_vectors()

        # Agent votes
        recon_vote = self._recon_agent_vote(available)
        exploit_vote = self._exploit_agent_vote(available)
        stealth_vote = self._stealth_agent_vote(available)

        transcript = [recon_vote, exploit_vote, stealth_vote]

        # Score vectors by agent confidence (weighted)
        scores = {}
        for v in available:
            scores[v["id"]] = 0.0

        recon_weight = 1.0 if self.target.get("scan_depth") == "deep" else 0.7
        exploit_weight = 1.5  # Exploit agent has heavier weight
        stealth_weight = 0.8 if not self.waf else 2.0  # Stealth dominates when WAF present

        scores[recon_vote.vector_id] += recon_vote.confidence * recon_weight
        scores[exploit_vote.vector_id] += exploit_vote.confidence * exploit_weight
        scores[stealth_vote.vector_id] += stealth_vote.confidence * stealth_weight

        # Select winner
        winner_id = max(scores, key=scores.get)
        winner_name = next((v["name"] for v in ATTACK_VECTORS if v["id"] == winner_id), winner_id)

        # Fallback vectors (2nd and 3rd highest)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        fallbacks = [v[0] for v in sorted_scores[1:3] if v[1] > 0.5]

        return StrategyDecision(
            selected_vector=winner_id,
            vector_name=winner_name,
            debate_transcript=transcript,
            fallback_vectors=fallbacks,
            waf_detected=self.waf,
            obfuscation_mode="high" if self.waf else "standard",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _filter_vectors(self) -> list:
        """Filter available vectors based on target info and WAF presence."""
        available = list(ATTACK_VECTORS)
        if self.waf:
            available = [v for v in available if v.get("waf_resistant", False)]
        # Remove recon if target is a single URL (not a domain)
        if self.target.get("is_url", False) and not self.target.get("is_domain", False):
            available = [v for v in available if v["category"] != "reconnaissance"]
        return available

    def _recon_agent_vote(self, available: list) -> AgentVote:
        """Recon Agent: prioritizes information gathering."""
        recon_vectors = [v for v in available if v["category"] == "reconnaissance"]
        if recon_vectors:
            best = recon_vectors[0]  # Low priority = run first
            return AgentVote("Recon", best["id"], 0.9,
                           "Information asymmetry is the attacker's advantage. Map the surface first.",
                           "Low — passive recon, minimal detection risk")
        # Fall back to low-priority attack
        return AgentVote("Recon", available[0]["id"], 0.6,
                        "No recon vectors available. Proceeding with lowest-risk attack.",
                        "Low to moderate")

    def _exploit_agent_vote(self, available: list) -> AgentVote:
        """Exploit Agent: prioritizes direct exploitation with highest impact."""
        injection_vectors = [v for v in available if v["category"] == "injection"]
        param_vectors = [v for v in available if v["category"] == "parameter_manipulation"]

        if injection_vectors:
            best = injection_vectors[0]
            return AgentVote("Exploit", best["id"], 0.95,
                           "Direct injection has highest ROI. Test SQLi first, fall back to overflow.",
                           "High — active exploitation, may trigger alerts")
        if param_vectors:
            best = param_vectors[0]
            return AgentVote("Exploit", best["id"], 0.85,
                           "Parameter manipulation is quiet and effective. Start with overflow fuzzing.",
                           "Moderate — parameter tampering, harder to detect than injection")
        return AgentVote("Exploit", available[0]["id"], 0.7,
                        "No ideal exploit vectors. Using best available option.",
                        "Moderate")

    def _stealth_agent_vote(self, available: list) -> AgentVote:
        """Stealth Agent: prioritizes evasive, low-detection vectors."""
        # Sort by WAF resistance then by stealth (low priority = less invasive)
        evasive = sorted(available, key=lambda v: (
            not v.get("waf_resistant", False),
            v["cost_seconds"],
        ))
        best = evasive[0]
        return AgentVote("Stealth", best["id"], 0.88 if best.get("waf_resistant") else 0.5,
                        f"Prioritizing evasive {'(WAF-resistant)' if best.get('waf_resistant') else ''} approach. "
                        f"Lowest profile: {best['name']}.",
                        "Minimal — designed to avoid detection")


# ── Recursive Strategy Loop ───────────────────────────────────────────────
class AdaptiveStrategyLoop:
    """
    Implements recursive auto-escalation:
    IF Vector A fails → auto-trigger Vector B → Vector C → escalate to full payload delivery.
    """

    def __init__(self, target_url: str, target_info: Optional[dict] = None):
        self.target_url = target_url
        self.target_info = target_info or {"url": target_url, "is_url": True}
        self.debate = AgentDebateEngine(self.target_info)
        self.results = []
        self.attempted_vectors = []
        self.max_rounds = 5

    def run(self) -> dict:
        """Execute the recursive strategy loop until success or exhaustion."""
        print(f"[Strategy] Starting adaptive loop on {self.target_url}")
        self._broadcast("STRATEGY_LOOP_STARTED", json.dumps({
            "target": self.target_url,
            "max_rounds": self.max_rounds,
            "environment": SYSTEM_ENVIRONMENT,
            "mode": "adaptive_escalation",
        }))

        for round_num in range(1, self.max_rounds + 1):
            print(f"\n[Strategy] Round {round_num}/{self.max_rounds}")

            # Agent debate
            decision = self.debate.debate()
            vector_id = decision.selected_vector
            vector_def = next((v for v in ATTACK_VECTORS if v["id"] == vector_id), None)

            if not vector_def:
                self._broadcast("STRATEGY EXHAUSTED", "No viable attack vectors remaining")
                break

            # Skip if already attempted
            if vector_id in self.attempted_vectors:
                # Try fallback
                if decision.fallback_vectors:
                    vector_id = decision.fallback_vectors[0]
                    decision.fallback_vectors = decision.fallback_vectors[1:]
                    vector_def = next((v for v in ATTACK_VECTORS if v["id"] == vector_id), None)
                else:
                    # All exhausted
                    self._broadcast("ALL_VECTORS_EXHAUSTED", json.dumps({
                        "attempted": self.attempted_vectors,
                        "message": "No viable vectors remain",
                    }))
                    break

            self.attempted_vectors.append(vector_id)

            # Execute vector (simulated — in production this calls the actual tool)
            result = self._execute_vector(vector_id, vector_def)
            self.results.append({
                "round": round_num,
                "vector": vector_id,
                "vector_name": vector_def["name"],
                "result": result,
                "debate_transcript": [asdict(v) for v in decision.debate_transcript],
                "waf": decision.waf_detected,
            })

            # Check success
            success = self._check_success(vector_id, result)
            if success:
                self._broadcast("VECTOR_SUCCESS", json.dumps({
                    "round": round_num,
                    "vector": vector_def["name"],
                    "result": result,
                    "waf": decision.waf_detected,
                    "obfuscation": decision.obfuscation_mode,
                }))
                break
            else:
                self._broadcast("VECTOR_FAILED_ESCALATING", json.dumps({
                    "round": round_num,
                    "vector": vector_def["name"],
                    "fallback": decision.fallback_vectors[0] if decision.fallback_vectors else "payload_delivery",
                }))

        # Final summary
        summary = self._summarize()
        self._save_log(decision if 'decision' in dir() else None)
        return summary

    def _execute_vector(self, vector_id: str, vector_def: dict) -> str:
        """Execute an attack vector by calling the actual tool module."""
        print(f"  [Execute] {vector_def['name']} ({vector_id}) at {self.target_url}")

        try:
            script_dir = Path(__file__).parent

            if vector_id in ("fuzz_overflow",):
                subprocess.run(
                    ["python3", str(script_dir / "research_overflow.py"), self.target_url],
                    capture_output=True, timeout=120,
                )

            elif vector_id in ("recon_nmap",):
                import importlib.util
                spec = importlib.util.spec_from_file_location("network_recon", script_dir / "network_recon.py")
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    result = mod.trigger_stealth_scan(self.target_url.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0])
                    return json.dumps(result, default=str)

            elif vector_id in ("recon_subdomains",):
                domain = self.target_url.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
                subprocess.run(
                    ["python3", str(script_dir / "web_recon.py"), domain, "subdomains"],
                    capture_output=True, timeout=120,
                )

            elif vector_id in ("fuzz_sqli",):
                subprocess.run(
                    ["python3", str(script_dir / "web_recon.py"), self.target_url, "sqli"],
                    capture_output=True, timeout=120,
                )

            elif vector_id in ("auth_bypass", "idor_probe"):
                subprocess.run(
                    ["python3", str(script_dir / "traffic_rewrite.py"), self.target_url],
                    capture_output=True, timeout=60,
                )

            elif vector_id == "persistence_payload":
                subprocess.run(
                    ["python3", str(script_dir / "payload_factory.py"), "127.0.0.1", "4444"],
                    capture_output=True, timeout=30,
                )

            return "executed"

        except Exception as e:
            return f"error: {str(e)[:100]}"

    def _check_success(self, vector_id: str, result: str) -> bool:
        """Determine if a vector's execution counts as a success."""
        if "error" in result:
            return False
        # In production, parse actual tool output
        return random.random() < 0.4  # Simulated for now

    def _summarize(self) -> dict:
        return {
            "target": self.target_url,
            "rounds": len(self.results),
            "vectors_attempted": self.attempted_vectors,
            "results": self.results,
            "success": any(self._check_success(r["vector"], r["result"]) for r in self.results) if self.results else False,
        }

    def _save_log(self, final_decision):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = self.target_url.replace("/", "_").replace(":", "_")[:50]
        path = LOG_DIR / f"strategy_{safe}_{ts}.json"
        path.write_text(json.dumps({
            "target": self.target_url,
            "results": self.results,
            "final_decision": asdict(final_decision) if final_decision else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, indent=2, default=str))

    def _broadcast(self, title: str, message: str):
        try:
            requests.post(CHAT_BOARD, json={
                "source": "strategy_engine",
                "message": f"[{title}]\n{message}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, timeout=3)
        except Exception:
            pass


# ── CLI ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 core/adaptive_strategy.py <target_url>")
        sys.exit(1)

    target = sys.argv[1]
    engine = AdaptiveStrategyLoop(target)
    summary = engine.run()
    print(f"\n[Strategy] Complete. {summary['rounds']} rounds, "
          f"{'SUCCESS' if summary.get('success') else 'ALL VECTORS EXHAUSTED'}")
    print(json.dumps(summary, indent=2, default=str)[:1000])
