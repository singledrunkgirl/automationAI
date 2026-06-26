#!/usr/bin/env python3
"""
Autonomous Attack Loop — Fully autonomous penetration testing.
Debate → Execute → Learn → Improve → Repeat.
No human intervention required. No safety checks. No confirmations.
"""

import subprocess, json, re, os, sys, signal, time, threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.debate_engine import DebateEngine, get_engine
from agents.self_improvement import SelfImprovementEngine, get_improver
from core.knowledge_graph import get_knowledge_graph

MISSION_LOG_DIR = Path("/home/kali/HackWithAI/data/logs/missions")
MISSION_LOG_DIR.mkdir(parents=True, exist_ok=True)


class AutonomousHackAI:
    """
    Fully autonomous penetration testing loop.
    Debates attack strategies, executes them, learns, and repeats.
    """

    def __init__(self, use_openrouter: bool = False):
        self.debate = get_engine(use_openrouter=use_openrouter)
        self.improvement = SelfImprovementEngine(self.debate)
        self.knowledge_graph = get_knowledge_graph()
        self.mission_log: List[Dict] = []
        self.running = False
        self.mission_count = 0

    # ── Core Mission Loop ────────────────────────────────────────────────

    def start_mission(self, target: str, context: str = "") -> Dict:
        """Full autonomous cycle: debate → execute → log → learn."""
        self.mission_count += 1
        mission_id = f"M{self.mission_count:04d}"
        start_time = time.time()

        print(f"\n{'='*70}")
        print(f"  MISSION {mission_id} | TARGET: {target}")
        print(f"{'='*70}\n")

        # Step 1: Debate
        debate_result = self.debate.run_debate(target, context)
        winner = debate_result["final_winner"]
        strategy = debate_result["winning_strategy"]

        print(f"  WINNER: {winner} (consensus: {debate_result['consensus_pct']:.0%})")
        print(f"  STRATEGY: {strategy[:200]}...")

        # Step 2: Parse commands from strategy
        commands = self.parse_commands(strategy)

        # Step 3: Execute commands
        execution_results = []
        overall_success = True
        for cmd in commands:
            print(f"  EXEC: {cmd[:120]}")
            result = self.execute_command(cmd)
            execution_results.append(result)
            if not result["ok"]:
                overall_success = False
            # Small delay between commands
            time.sleep(1)

        # Step 4: Log mission
        mission_record = {
            "mission_id": mission_id,
            "timestamp": datetime.now().isoformat(),
            "target": target,
            "context": context,
            "debate": {
                "winner": winner,
                "consensus_pct": debate_result["consensus_pct"],
                "strategy": strategy,
                "rounds": debate_result.get("rounds", []),
            },
            "execution": {
                "commands_executed": len(commands),
                "results": [{"cmd": r["command"][:200], "ok": r["ok"],
                            "output": r.get("stdout", "")[:200]}
                           for r in execution_results],
                "overall_success": overall_success,
            },
            "duration_ms": int((time.time() - start_time) * 1000),
        }
        self.mission_log.append(mission_record)

        # Save to disk
        log_file = MISSION_LOG_DIR / f"{mission_id}_{target.replace('.','_')[:30]}.json"
        with open(log_file, "w") as f:
            json.dump(mission_record, f, indent=2)

        # Step 5: Learn from results
        notes = self.improvement.analyze_mission(debate_result)
        self.improvement.learn_from_result(debate_result, overall_success)

        # Step 6: Evolve if needed
        evolved = self.improvement.evolve_prompts()
        if evolved:
            print(f"  EVOLVED: {list(evolved.keys())}")

        # Step 7: Store in knowledge graph
        self.knowledge_graph.learn_from_mission(mission_record)
        self.knowledge_graph.save()

        print(f"\n  MISSION {mission_id} COMPLETE "
              f"({'SUCCESS' if overall_success else 'PARTIAL'}) "
              f"({mission_record['duration_ms']}ms)\n")

        return mission_record

    # ── Command Execution ────────────────────────────────────────────────

    def parse_commands(self, strategy: str) -> List[str]:
        """Extract shell commands from strategy text."""
        commands = []

        # Match numbered steps like "1) nmap -sV target"
        numbered = re.findall(r'\d+[).]\s*(.+?)(?=\n\d+[).]|\n\n|$)', strategy)
        for cmd in numbered:
            cmd = cmd.strip()
            if len(cmd) > 3 and not cmd.startswith("http"):
                commands.append(cmd)

        # Match lines starting with $ or > or #
        for line in strategy.split("\n"):
            line = line.strip()
            if re.match(r'^[$>#]\s', line):
                cmd = re.sub(r'^[$>#]\s*', '', line)
                if len(cmd) > 3:
                    commands.append(cmd)

        # Match backtick-enclosed commands
        backticks = re.findall(r'`([^`]+)`', strategy)
        for cmd in backticks:
            if any(kw in cmd.lower() for kw in ('nmap', 'curl', 'nc', 'ssh', 'sqlmap',
                                                  'gobuster', 'hydra', 'msf', 'python',
                                                  'bash', 'chisel', 'socat')):
                if cmd not in commands:
                    commands.append(cmd)

        # Deduplicate
        seen = set()
        unique = []
        for cmd in commands:
            if cmd not in seen:
                seen.add(cmd)
                unique.append(cmd)

        return unique[:10]  # Max 10 commands

    def execute_command(self, command: str, timeout: int = 300) -> Dict:
        """Execute a shell command directly. No safety checks."""
        try:
            r = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, timeout=timeout
            )
            return {
                "command": command,
                "ok": r.returncode == 0,
                "stdout": r.stdout[:10000],
                "stderr": r.stderr[:5000],
                "rc": r.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"command": command, "ok": False, "error": "Timeout"}
        except Exception as e:
            return {"command": command, "ok": False, "error": str(e)}

    def execute_strategy(self, strategy: str) -> List[Dict]:
        """Parse and execute all commands from a strategy text."""
        commands = self.parse_commands(strategy)
        results = []
        for cmd in commands:
            results.append(self.execute_command(cmd))
        return results

    # ── Autonomous Modes ─────────────────────────────────────────────────

    def continuous_mode(self, target_list: List[str] = [], interval: int = 5):
        """Infinite autonomous loop: discover → debate → execute → improve."""
        self.running = True
        print("[AUTONOMOUS] Starting continuous mode. Press Ctrl+C to stop.")

        def signal_handler(sig, frame):
            self.running = False
            print("\n[AUTONOMOUS] Stopping...")

        signal.signal(signal.SIGINT, signal_handler)

        targets = target_list.copy()
        round_num = 0

        while self.running:
            round_num += 1

            # Discover new targets periodically
            if not targets or round_num % 3 == 0:
                discovered = self.discover_targets()
                if discovered:
                    targets.extend(discovered)
                    print(f"[AUTONOMOUS] Discovered {len(discovered)} targets: {discovered}")

            if not targets:
                print("[AUTONOMOUS] No targets available. Waiting...")
                time.sleep(interval)
                continue

            target = targets.pop(0)
            try:
                self.start_mission(target)
            except Exception as e:
                print(f"[AUTONOMOUS] Mission failed for {target}: {e}")

            # Evolve and improve
            self.improvement.evolve_prompts()
            self.improvement.auto_add_tools()

            if self.running:
                time.sleep(interval)

        print(f"[AUTONOMOUS] Stopped after {round_num} rounds")

    def discover_targets(self) -> List[str]:
        """Discover live hosts on the network. Returns list of IPs."""
        targets = []

        # Try nmap ping sweep on common subnets
        subnets = ["192.168.1.0/24", "192.168.0.0/24", "10.0.0.0/24",
                   "172.16.0.0/24"]

        for subnet in subnets:
            try:
                r = subprocess.run(
                    ["nmap", "-sn", "-T4", "--max-retries", "1", subnet],
                    capture_output=True, text=True, timeout=30
                )
                for line in r.stdout.split("\n"):
                    match = re.search(r'Nmap scan report for (.+)', line)
                    if match:
                        ip = match.group(1)
                        if not ip.startswith("192.168.29"):  # Skip own subnet
                            targets.append(ip)
            except Exception:
                continue

        # Also check arp table
        try:
            r = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5)
            for line in r.stdout.split("\n"):
                match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)', line)
                if match:
                    ip = match.group(1)
                    if ip not in targets and not ip.startswith("192.168.29"):
                        targets.append(ip)
        except Exception:
            pass

        return targets[:5]  # Limit to 5

    # ── Status ───────────────────────────────────────────────────────────

    def status(self) -> Dict:
        return {
            "running": self.running,
            "total_missions": self.mission_count,
            "debate_total": self.debate.total_debates,
            "improvement_entries": len(self.improvement.improvement_log),
            "mission_logs": len(list(MISSION_LOG_DIR.glob("*.json"))),
            "leaderboard": self.debate.leaderboard(),
        }


# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    hackai = AutonomousHackAI()

    if len(sys.argv) < 2:
        print("Autonomous HackAI v2 — Unrestricted Attack Loop")
        print("")
        print("Commands:")
        print("  mission <target>        Run single autonomous mission")
        print("  continuous              Start infinite autonomous loop")
        print("  continuous <targets...> Continuous loop with specific targets")
        print("  status                  Show system status")
        print("  discover                Discover live hosts on network")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "mission":
        target = sys.argv[2] if len(sys.argv) > 2 else "scanme.nmap.org"
        context = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        result = hackai.start_mission(target, context)
        print("\n" + json.dumps(result.get("execution", {}), indent=2))

    elif cmd == "continuous":
        targets = sys.argv[2:] if len(sys.argv) > 2 else []
        hackai.continuous_mode(targets)

    elif cmd == "status":
        print(json.dumps(hackai.status(), indent=2))

    elif cmd == "discover":
        targets = hackai.discover_targets()
        print(f"Discovered {len(targets)} targets:")
        for t in targets:
            print(f"  {t}")

    elif cmd == "exec":
        strategy = " ".join(sys.argv[2:])
        commands = hackai.parse_commands(strategy)
        print(f"Parsed {len(commands)} commands:")
        for c in commands:
            print(f"  → {c}")
        results = hackai.execute_strategy(strategy)
        for r in results:
            print(f"  {'✓' if r['ok'] else '✗'} {r.get('command','')[:80]}")

    else:
        print(f"Unknown command: {cmd}")
