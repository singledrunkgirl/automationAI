#!/usr/bin/env python3
"""
HackWithAI Universal API Fuzzer
Tests endpoints for parameter pollution, header injection, auth flaws,
IDOR patterns, and logic bugs. Results stream to :3006 chat board.
"""
import json, os, sys, time, itertools, hashlib, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse, parse_qs, urlencode

import requests

# ── Config ────────────────────────────────────────────────────────────────
RESULTS_DIR = Path(__file__).resolve().parent.parent / "Projects" / "InternalRef"
CHAT_BOARD_URL = os.environ.get("CHAT_BOARD_URL", "http://127.0.0.1:3006")
DEFAULT_TIMEOUT = 10
USER_AGENT = "HackWithAI-Fuzzer/2.0"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ── Payload Generators ────────────────────────────────────────────────────
PARAM_POLLUTION_PAYLOADS = [
    # Duplicate params
    lambda u, p: f"{u}?{p}=1&{p}=2",
    # Array injection
    lambda u, p: f"{u}?{p}[]=1&{p}[]=2",
    # JSON injection in params
    lambda u, p: f'{u}?{p}={{"$gt":""}}',
    # Type confusion
    lambda u, p: f"{u}?{p}=true",
    lambda u, p: f"{u}?{p}=0",
    lambda u, p: f"{u}?{p}=-1",
    lambda u, p: f"{u}?{p}=NaN",
    lambda u, p: f"{u}?{p}=null",
    lambda u, p: f"{u}?{p}=undefined",
    # Overflow
    lambda u, p: f"{u}?{p}={'A'*5000}",
    # Path traversal via param
    lambda u, p: f"{u}?{p}=../../../etc/passwd",
    # SSTI probe
    lambda u, p: f"{u}?{p}=${{7*7}}",
    lambda u, p: f"{u}?{p}={{7*7}}",
    # SQLi probe
    lambda u, p: f"{u}?{p}=' OR '1'='1",
    # XSS probe
    lambda u, p: f"{u}?{p}=<script>alert(1)</script>",
]

HEADER_INJECTION_PAYLOADS = [
    {"X-Forwarded-For": "127.0.0.1"},
    {"X-Forwarded-Host": "evil.com"},
    {"X-Forwarded-Proto": "https"},
    {"X-Original-URL": "/admin"},
    {"X-Rewrite-URL": "/admin"},
    {"X-HTTP-Method-Override": "DELETE"},
    {"Content-Type": "application/json", "body_transform": True},
    {"Accept": "../../../etc/passwd"},
    {"X-Custom-IP-Authorization": "127.0.0.1"},
    {"Forwarded": "for=127.0.0.1;host=admin.local;proto=https"},
    {"Referer": "https://evil.com/phishing"},
    {"Origin": "https://evil.com"},
]

AUTH_BYPASS_PATTERNS = [
    {"Authorization": ""},
    {"Authorization": "Bearer null"},
    {"Authorization": "Bearer undefined"},
    {"Authorization": "Bearer eyJhbGciOiJub25lIn0.eyJzdWIiOiJhZG1pbiJ9."},
    {"Authorization": "Bearer admin"},
    {"Authorization": "Basic YWRtaW46YWRtaW4="},  # admin:admin
    {"Authorization": "Basic dGVzdDp0ZXN0"},      # test:test
    {"X-API-Key": "admin"},
    {"X-Auth-Token": "null"},
    {"Cookie": "session=admin; role=admin"},
]

IDOR_PATTERNS = [
    ("id", lambda v: str(int(v) + 1)),
    ("id", lambda v: str(int(v) - 1)),
    ("userId", lambda v: str(uuid.uuid4())),
    ("user_id", lambda v: "admin"),
    ("email", lambda v: "admin@localhost"),
    ("role", lambda v: "admin"),
    ("token", lambda v: "null"),
]


# ── Core Fuzzer ───────────────────────────────────────────────────────────
class APIFuzzer:
    def __init__(self, base_url: str, headers: Optional[dict] = None, cookies: Optional[dict] = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
        })
        if headers:
            self.session.headers.update(headers)
        if cookies:
            self.session.cookies.update(cookies)
        self.results = []
        self.start_time = time.time()

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        kwargs.setdefault("allow_redirects", False)
        try:
            return self.session.request(method, url, **kwargs)
        except requests.RequestException as e:
            resp = requests.Response()
            resp.status_code = 0
            resp._content = str(e).encode()
            return resp

    def _record(self, test_type: str, url: str, params: dict, response: requests.Response, notes: str = ""):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_type": test_type,
            "url": url,
            "request_params": params,
            "status_code": response.status_code,
            "response_length": len(response.content),
            "response_sample": response.text[:500] if response.text else "",
            "headers": dict(response.headers),
            "notes": notes,
        }
        self.results.append(entry)

        # Flag anomalies
        if response.status_code in (0, 500, 502, 503):
            self._alert(f"[ANOMALY] {test_type}: {url} → {response.status_code}")
        elif "error" in response.text.lower() and "sql" in response.text.lower():
            self._alert(f"[SQLI HIT] {test_type}: {url} → SQL error in response")

    def _alert(self, message: str):
        print(f"[Fuzzer] {message}")
        try:
            requests.post(
                f"{CHAT_BOARD_URL}/api/tools/broadcast",
                json={"source": "api_fuzzer", "message": message, "timestamp": datetime.now(timezone.utc).isoformat()},
                timeout=3,
            )
        except Exception:
            pass

    # ── Test Methods ──────────────────────────────────────────────────────
    def test_parameter_pollution(self, endpoint: str, params: list):
        base = urljoin(self.base_url, endpoint.lstrip("/"))
        existing_params = parse_qs(urlparse(base).query)
        query_base = base.split("?")[0]

        for param in params:
            for i, payload_fn in enumerate(PARAM_POLLUTION_PAYLOADS):
                url = payload_fn(query_base, param)
                resp = self._request("GET", url)
                anomaly = ""
                if resp.status_code in (200, 500) and param in existing_params:
                    anomaly = "Param override possible"
                elif resp.status_code == 200:
                    anomaly = "Accepts unusual values"
                self._record("param_pollution", url, {"param": param, "payload_idx": i}, resp, anomaly)

    def test_header_injection(self, endpoint: str):
        url = urljoin(self.base_url, endpoint.lstrip("/"))
        baseline = self._request("GET", url)

        for i, headers in enumerate(HEADER_INJECTION_PAYLOADS):
            body_transform = headers.pop("body_transform", False)
            method = "POST" if body_transform else "GET"
            kwargs = {"headers": {**self.session.headers, **headers}}
            if body_transform:
                kwargs["json"] = {"test": "fuzzer"}
            resp = self._request(method, url, **kwargs)

            anomaly = ""
            if resp.status_code != baseline.status_code:
                anomaly = f"Status changed: {baseline.status_code} → {resp.status_code}"
            elif len(resp.content) != len(baseline.content):
                diff = len(resp.content) - len(baseline.content)
                anomaly = f"Content length changed by {diff}B"

            self._record("header_injection", url, {"headers": {k: v for k, v in headers.items()}}, resp, anomaly)

    def test_auth_bypass(self, endpoints: list):
        for ep in endpoints:
            url = urljoin(self.base_url, ep.lstrip("/"))
            baseline = self._request("GET", url)

            if baseline.status_code == 401 or baseline.status_code == 403:
                for i, auth_headers in enumerate(AUTH_BYPASS_PATTERNS):
                    # Don't modify Content-Type from header_injection tests
                    headers = {k: v for k, v in auth_headers.items() if k != "body_transform"}
                    resp = self._request("GET", url, headers=headers)
                    anomaly = ""
                    if resp.status_code not in (401, 403):
                        anomaly = f"AUTH BYPASS! {resp.status_code} with {list(headers.keys())}"
                        self._alert(f"[AUTH BYPASS] {url} using {list(headers.keys())} → {resp.status_code}")
                    self._record("auth_bypass", url, {"headers": headers}, resp, anomaly)

    def test_idor(self, endpoint: str, id_params: list):
        base = urljoin(self.base_url, endpoint.lstrip("/"))
        for param_name, transform in IDOR_PATTERNS:
            if param_name not in id_params:
                continue
            url = base.replace(f"{param_name}={id_params[param_name]}", f"{param_name}={transform(id_params[param_name])}")
            resp = self._request("GET", url)
            anomaly = ""
            if resp.status_code == 200:
                anomaly = f"IDOR possible: accessed {param_name}={transform(id_params[param_name])}"
                self._alert(f"[IDOR CANDIDATE] {url} → 200")
            self._record("idor", url, {"param": param_name, "original": id_params[param_name], "tested": transform(id_params[param_name])}, resp, anomaly)

    def test_logic_flaws(self, endpoint: str, method: str = "POST", body: Optional[dict] = None):
        """Test for logic flaws: negative values, amount manipulation, race conditions, etc."""
        url = urljoin(self.base_url, endpoint.lstrip("/"))

        tests = [
            # Negative amounts
            (body, lambda b: {**b, "amount": -100} if b and "amount" in b else b),
            # Zero amounts
            (body, lambda b: {**b, "amount": 0} if b and "amount" in b else b),
            # Extremely large values
            (body, lambda b: {**b, "amount": 999999999999} if b and "amount" in b else b),
            # Boolean/type confusion
            (body, lambda b: {**b, "isAdmin": True, "role": "admin"} if b else {"isAdmin": True}),
            # Missing required fields
            (body, lambda b: {} if b else {}),
            # Extra fields
            (body, lambda b: {**b, "debug": True, "verbose": True} if b else {"debug": True}),
        ]

        for i, (original, transform) in enumerate(tests):
            payload = transform(original) if original else transform({})
            resp = self._request(method, url, json=payload)
            anomaly = ""
            if resp.status_code == 200:
                anomaly = "Logic flaw: accepted manipulated payload"
                self._alert(f"[LOGIC FLAW] {url} → 200 with transformed body")
            self._record("logic_flaw", url, {"test_idx": i, "payload": json.dumps(payload)[:200]}, resp, anomaly)

    def run_full_scan(self, endpoints: list, params: Optional[dict] = None):
        """Execute all test categories against a set of endpoints."""
        print(f"[Fuzzer] Starting full scan: {len(endpoints)} endpoints")
        self._alert(f"[Fuzzer] Scan started — {len(endpoints)} targets")

        for ep in endpoints:
            url = urljoin(self.base_url, ep.get("path", ep) if isinstance(ep, dict) else ep)
            ep_params = ep.get("params", []) if isinstance(ep, dict) else []
            ep_id_params = ep.get("id_params", {}) if isinstance(ep, dict) else {}
            ep_method = ep.get("method", "GET") if isinstance(ep, dict) else "GET"
            ep_body = ep.get("body") if isinstance(ep, dict) else None

            print(f"[Fuzzer] Testing: {url}")
            self.test_parameter_pollution(ep.get("path", ep), ep_params or ["id", "page", "q", "user_id", "token"])
            self.test_header_injection(ep.get("path", ep))

            if ep_id_params:
                self.test_idor(ep.get("path", ep), ep_id_params)

            if ep_method in ("POST", "PUT", "PATCH"):
                self.test_logic_flaws(ep.get("path", ep), ep_method, ep_body)

        self.test_auth_bypass([e.get("path", e) if isinstance(e, dict) else e for e in endpoints])

        self.save_results()
        self._alert(f"[Fuzzer] Scan complete — {len(self.results)} tests. Results: {RESULTS_DIR/'fuzz_results.json'}")

    def save_results(self):
        elapsed = time.time() - self.start_time
        report = {
            "scan_metadata": {
                "base_url": self.base_url,
                "started": datetime.fromtimestamp(self.start_time, tz=timezone.utc).isoformat(),
                "duration_seconds": round(elapsed, 1),
                "total_tests": len(self.results),
            },
            "findings": self.results,
        }
        (RESULTS_DIR / "fuzz_results.json").write_text(json.dumps(report, indent=2, default=str))
        # Also save timestamped copy
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        (RESULTS_DIR / f"fuzz_results_{ts}.json").write_text(json.dumps(report, indent=2, default=str))


# ── CLI Entry Point ───────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 core/api_fuzzer.py <base_url> [endpoint1] [endpoint2] ...")
        print("Example: python3 core/api_fuzzer.py http://127.0.0.1:3006 /api/chats /api/chat")
        sys.exit(1)

    target = sys.argv[1]
    endpoints_raw = sys.argv[2:] if len(sys.argv) > 2 else ["/"]
    endpoints = [{"path": e} for e in endpoints_raw]

    fuzzer = APIFuzzer(target)
    try:
        fuzzer.run_full_scan(endpoints)
    except KeyboardInterrupt:
        fuzzer.save_results()
        print(f"\n[Fuzzer] Interrupted. Partial results saved to {RESULTS_DIR/'fuzz_results.json'}")
