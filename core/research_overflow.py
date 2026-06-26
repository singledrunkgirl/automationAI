#!/usr/bin/env python3
"""
Research Automation: Numeric Parameter Stress-Test Engine
Tests API endpoints for integer overflow, negative value injection, type confusion,
and arithmetic logic flaws. Generates Burp Suite JSON rules for live MITM rewriting.
"""
import json, sys, os, time
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

import requests

# ── Config ────────────────────────────────────────────────────────────────
REPORT_DIR = Path(__file__).resolve().parent.parent / "Projects" / "research"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ── Parameter Profile: defines what to test for a given API param ─────────
@dataclass
class ParamProfile:
    """Describes a numeric parameter and how to stress-test it."""
    name: str                         # e.g. "amount", "diamonds", "credits"
    expected_range: tuple = (1, 9999) # min/max expected in normal use
    data_type: str = "int"            # int, float, stringified-int
    location: str = "body"            # query, body, header
    http_method: str = "POST"

    def overflow_values(self) -> list:
        """Generate integer overflow test payloads."""
        return [
            # Boundary overflow
            ("MAX_UINT32 + 1", 0xFFFFFFFF + 1),
            ("MAX_INT32 + 1", 0x7FFFFFFF + 1),
            ("MAX_UINT64", 0xFFFFFFFFFFFFFFFF),
            # Negative boundary
            ("negative_small", -1),
            ("negative_large", -999999999),
            ("MIN_INT32", -0x80000000),
            # Zero and null-ish
            ("zero", 0),
            ("null_value", None),
            ("false_bool", False),
            ("true_bool", True),
            # Type confusion
            ("string_number", "999999999"),
            ("float_overflow", 9.999999e99),
            ("scientific", "1e309"),
            ("negative_scientific", "-1e309"),
            ("hex_overflow", "0xFFFFFFFFFFFFFFFF"),
            ("octal_overflow", "0o37777777777"),
            # Arithmetic edge cases
            ("minus_one", -1),
            ("very_large_int", 10**18),
            ("very_large_negative", -(10**18)),
            # NaN / Infinity variants
            ("nan", "NaN"),
            ("inf", "Infinity"),
            ("neg_inf", "-Infinity"),
        ]

    def burp_rewrite_rules(self) -> list[dict]:
        """Generate Burp-compatible Search & Replace rules for live MITM."""
        return [
            {
                "description": f"Overflow: {self.name} → MAX_UINT32",
                "match_type": "regex",
                "param": self.name,
                "find": r'"' + self.name + r'":\s*\d+',
                "replace": f'"{self.name}": 4294967295',
                "enabled": True,
                "severity": "HIGH",
            },
            {
                "description": f"Overflow: {self.name} → MAX_INT32",
                "match_type": "regex",
                "param": self.name,
                "find": r'"' + self.name + r'":\s*\d+',
                "replace": f'"{self.name}": 2147483647',
                "enabled": True,
                "severity": "HIGH",
            },
            {
                "description": f"Negative injection: {self.name} → -1",
                "match_type": "regex",
                "param": self.name,
                "find": r'"' + self.name + r'":\s*\d+',
                "replace": f'"{self.name}": -1',
                "enabled": True,
                "severity": "CRITICAL",
            },
            {
                "description": f"Negative injection: {self.name} → MIN_INT32",
                "match_type": "regex",
                "param": self.name,
                "find": r'"' + self.name + r'":\s*\d+',
                "replace": f'"{self.name}": -2147483648',
                "enabled": True,
                "severity": "CRITICAL",
            },
            {
                "description": f"Zero bypass: {self.name} → 0",
                "match_type": "regex",
                "param": self.name,
                "find": r'"' + self.name + r'":\s*\d+',
                "replace": f'"{self.name}": 0',
                "enabled": True,
                "severity": "MEDIUM",
            },
            {
                "description": f"Type confusion: {self.name} → string '0'",
                "match_type": "regex",
                "param": self.name,
                "find": r'"' + self.name + r'":\s*(\d+)',
                "replace": f'"{self.name}": "0"',
                "enabled": True,
                "severity": "MEDIUM",
            },
            {
                "description": f"Type confusion: {self.name} → null",
                "match_type": "regex",
                "param": self.name,
                "find": r'"' + self.name + r'":\s*\d+',
                "replace": f'"{self.name}": null',
                "enabled": True,
                "severity": "HIGH",
            },
            {
                "description": f"Arithmetic: {self.name} × 100",
                "match_type": "regex",
                "param": self.name,
                "find": r'"' + self.name + r'":\s*(\d+)',
                "replace": f'"{self.name}": $1',  # placeholder — engine computes
                "enabled": False,
                "severity": "LOW",
                "note": "Requires dynamic compute in rewrite engine",
            },
        ]


# ── Fuzzing Engine ────────────────────────────────────────────────────────
class NumericOverflowTester:
    """Standalone fuzzer that sends requests with manipulated numeric params."""

    def __init__(self, base_url: str, session: Optional[requests.Session] = None):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.results = []

    def test_endpoint(self, endpoint: str, profiles: list[ParamProfile],
                      body_template: dict, method: str = "POST") -> list:
        """Run full overflow test suite against one endpoint."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        findings = []

        # 1. Baseline — normal request
        try:
            baseline = self.session.request(method, url, json=body_template, timeout=10)
            baseline_status = baseline.status_code
            baseline_len = len(baseline.content)
        except Exception as e:
            baseline_status = 0
            baseline_len = 0
            print(f"  [!] Baseline failed: {e}")

        for profile in profiles:
            for label, value in profile.overflow_values():
                body = json.loads(json.dumps(body_template))  # deep copy
                if profile.name in body:
                    body[profile.name] = value

                try:
                    resp = self.session.request(method, url, json=body, timeout=10)
                    anomaly = False
                    notes = []

                    # Anomaly detection heuristics
                    if resp.status_code != baseline_status:
                        anomaly = True
                        notes.append(f"Status changed: {baseline_status}→{resp.status_code}")

                    if abs(len(resp.content) - baseline_len) > 100:
                        anomaly = True
                        notes.append(f"Content length changed by {len(resp.content) - baseline_len}B")

                    if resp.status_code == 200:
                        # Check for error messages in response
                        body_text = resp.text.lower()
                        error_keywords = ["error", "exception", "traceback", "sql", "stack"]
                        for kw in error_keywords:
                            if kw in body_text and kw not in (json.dumps(body_template).lower()):
                                anomaly = True
                                notes.append(f"Error keyword '{kw}' in response")
                                break

                    finding = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "endpoint": endpoint,
                        "param": profile.name,
                        "test_label": label,
                        "value_sent": str(value),
                        "status_code": resp.status_code,
                        "response_len": len(resp.content),
                        "anomaly": anomaly,
                        "notes": "; ".join(notes) if notes else "OK",
                        "response_snippet": resp.text[:300] if anomaly else "",
                    }
                    findings.append(finding)
                    if anomaly:
                        print(f"  [!] {profile.name}={value} → {resp.status_code} | {notes}")

                except Exception as e:
                    findings.append({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "endpoint": endpoint,
                        "param": profile.name,
                        "test_label": label,
                        "value_sent": str(value),
                        "status_code": 0,
                        "response_len": 0,
                        "anomaly": True,
                        "notes": f"Request failed: {str(e)[:100]}",
                    })

        self.results.extend(findings)
        print(f"  [{endpoint}] {len(findings)} tests complete, {sum(1 for f in findings if f.get('anomaly'))} anomalies")
        return findings

    def save_report(self, name: str = ""):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        tag = f"{name}_" if name else ""
        path = REPORT_DIR / f"overflow_test_{tag}{ts}.json"
        path.write_text(json.dumps(self.results, indent=2))
        print(f"  Report saved → {path}")
        return path


# ── Burp JSON Rule Set Generator ──────────────────────────────────────────
def generate_burp_rules(profiles: list[ParamProfile]) -> dict:
    """Produce a complete Burp-compatible ruleset for proxy import."""
    all_rules = []
    for p in profiles:
        all_rules.extend(p.burp_rewrite_rules())

    ruleset = {
        "name": "Numeric Overflow & Logic Flaw Detection",
        "version": "1.0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "description": (
            "Automated parameter manipulation rules for integer overflow testing. "
            "Tests MAX_UINT32, negative injection, type confusion, null bypass, and "
            "arithmetic boundary conditions on numeric API parameters."
        ),
        "target_params": [p.name for p in profiles],
        "rule_count": len(all_rules),
        "rules": all_rules,
        "usage": "Import into Burp Suite → Proxy → Options → Match and Replace",
    }

    path = REPORT_DIR / "burp_overflow_rules.json"
    path.write_text(json.dumps(ruleset, indent=2))
    print(f"  Burp rules exported → {path}")
    return ruleset


# ── Generic API Profile Templates ─────────────────────────────────────────
def generic_payment_api_profiles() -> list[ParamProfile]:
    """Standard profiles for payment/game-currency style APIs."""
    return [
        ParamProfile("amount", (1, 999999), "int", "body", "POST"),
        ParamProfile("credits", (1, 10000), "int", "body", "POST"),
        ParamProfile("diamonds", (1, 5000), "int", "body", "POST"),
        ParamProfile("coins", (1, 100000), "int", "body", "POST"),
        ParamProfile("quantity", (1, 99), "int", "body", "POST"),
        ParamProfile("price", (1, 99999), "int", "body", "POST"),
        ParamProfile("balance", (0, 999999), "int", "body", "POST"),
        ParamProfile("user_id", (1, 999999), "int", "body", "POST"),
        ParamProfile("item_id", (1, 99999), "int", "body", "POST"),
        ParamProfile("discount_percent", (0, 100), "int", "body", "POST"),
    ]


# ── CLI / Main ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 core/research_overflow.py <target_url> [endpoint]")
        print("Example: python3 core/research_overflow.py http://127.0.0.1:3000 /api/purchase")
        print("\nGenerates: Burp rules + overflow test report")
        sys.exit(0)

    target = sys.argv[1]
    endpoint = sys.argv[2] if len(sys.argv) > 2 else "/"

    profiles = generic_payment_api_profiles()
    tester = NumericOverflowTester(target)

    print(f"\n[Research] Numeric Overflow Stress Test")
    print(f"  Target: {target}{endpoint}")
    print(f"  Profiles: {len(profiles)} parameters")
    print(f"  Tests per param: {len(profiles[0].overflow_values())}")
    print(f"  Total test cases: ~{len(profiles) * len(profiles[0].overflow_values())}\n")

    # 1. Generate Burp rules
    print("[1/3] Generating Burp JSON rules...")
    ruleset = generate_burp_rules(profiles)

    # 2. Build a sample body
    sample_body = {p.name: p.expected_range[0] for p in profiles}

    # 3. Run fuzzing
    print(f"\n[2/3] Testing endpoint {endpoint}...")
    findings = tester.test_endpoint(endpoint, profiles, sample_body)

    # 4. Save reports
    print(f"\n[3/3] Saving results...")
    report_path = tester.save_report("generic_api")

    anomalies = [f for f in findings if f.get("anomaly")]
    print(f"\n{'='*60}")
    print(f"RESULTS: {len(findings)} tests | {len(anomalies)} anomalies detected")
    if anomalies:
        print(f"\nTop anomalies:")
        for a in anomalies[:8]:
            print(f"  [{a['param']}] {a['test_label']} = {a['value_sent']} → {a['status_code']} | {a['notes']}")
    print(f"\nBurp rules: {REPORT_DIR}/burp_overflow_rules.json")
    print(f"Test report: {report_path}")
