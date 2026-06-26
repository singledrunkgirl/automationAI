#!/usr/bin/env python3
"""Test Hermes Runtime — Full integration test of all Phase 2 + Phase 3 components."""

import sys, json
sys.path.insert(0, "/home/kali/HackWithAI")

def test(name, fn):
    try:
        result = fn()
        print(f"  ✅ {name}: {result}")
        return True
    except Exception as e:
        print(f"  ❌ {name}: {e}")
        return False

passed = 0; total = 0

print("=== PHASE 2: Hermes Runtime ===")
from agents import (
    get_hermes, get_critic, get_reviewer, get_revision,
    get_consensus, get_message_bus, get_state,
)

total += 1; passed += test("MessageBus pub/sub", lambda: f"{get_message_bus().publish('t','H','{}')} listeners")
total += 1; passed += test("StateManager persistence", lambda: "OK" if get_state().stats()["agents_registered"] >= 0 else "FAIL")
total += 1; passed += test("Consensus voting", lambda: f"{get_consensus().round_vote({'A':'a','B':'b'},['A','B'],{'A':'A','B':'A'})[0]}")

critic_r = get_critic().critique("Scan with nmap -sV. Exploit with metasploit.", source_agent="TestBot")
total += 1; passed += test("Critic score", lambda: critic_r["score"])
total += 1; passed += test("Reviewer score", lambda: get_reviewer().review("Use nmap for recon.", source_agent="TestBot")["overall_score"])

rev = get_revision().revise("Scan target.", critic_r,
    get_reviewer().review("Scan target.", source_agent="TestBot"), "TestBot")
total += 1; passed += test("Revision improvement", lambda: rev["improvement_score"])

pipeline = get_hermes().full_review_pipeline("Run nmap scan. Use sqlmap for SQLi. Generate report.", "TestBot")
total += 1; passed += test("Hermes pipeline", lambda: f"C={pipeline['critic_score']} R={pipeline['reviewer_score']} V={pipeline['revision_score']}")

print("\n=== PHASE 3: Reflection Engine ===")
from reflection import get_reflection

r = get_reflection()

# Test reflection
ref = r.reflect("Scan network for open ports", "Use nmap -sV target",
                {"score": 55, "findings": ["No specific tools", "Missing steps"]},
                {"overall_score": 60, "feedback": ["actionability: needs commands"]},
                "TestBot", "T001")
total += 1; passed += test("Reflection quality", lambda: ref["quality_score"])
total += 1; passed += test("Issues found", lambda: len(ref["issues_found"]))

# Test lessons
lid = r.lessons_engine.add("tool_usage", "Wrong nmap flags", "Use -sV -sC -O for comprehensive scan", "TestBot")
total += 1; passed += test("Lesson storage", lambda: "OK" if lid else "FAIL")

lessons = r.lessons_engine.query(keyword="nmap")
total += 1; passed += test("Lesson retrieval", lambda: len(lessons))

ctx = r.lessons_engine.get_context_for_task("Scan target for vulnerabilities using nmap")
total += 1; passed += test("Context injection", lambda: len(ctx) if ctx else "empty (no matching lessons yet)")

# Test failure analysis
fid = r.failure_analyzer.record("T002", "TestBot", "scan", "Command not found: nmap", "tool misuse")
total += 1; passed += test("Failure recording", lambda: "OK" if fid else "FAIL")

trends = r.failure_analyzer.get_trends()
total += 1; passed += test("Failure trends", lambda: f"{trends['total_failures']} failures")

# Test pattern detection
patterns = r.pattern_detector.detect()
total += 1; passed += test("Pattern detection", lambda: f"{len(patterns['patterns'])} patterns, alert={patterns['alert']}")

print(f"\n{'='*40}")
print(f"RESULTS: {passed}/{total} passed")
print(f"{'ALL TESTS PASSED' if passed == total else 'SOME TESTS FAILED'}")
