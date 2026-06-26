#!/usr/bin/env python3
"""
Zero-Day Vulnerability Scanner — CVE database, binary diffing, fuzzing, exploit suggestion, anomaly detection.
All unrestricted. No safety guards.
"""

import subprocess, json, re, os, sys, sqlite3, hashlib, time, shutil, gzip, io, urllib.request
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

DATA_DIR = Path("/home/kali/HackWithAI/data/zeroday")
DATA_DIR.mkdir(parents=True, exist_ok=True)
CVE_DB_PATH = DATA_DIR / "cve.db"
ANOMALY_LOG = DATA_DIR / "anomalies.log"
EXPLOIT_DIR = DATA_DIR / "exploits"
EXPLOIT_DIR.mkdir(exist_ok=True)


class CVEDatabase:
    """Manages CVE data from NVD with SQLite storage."""

    def __init__(self, db_path: Path = CVE_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS cves (
                id TEXT PRIMARY KEY, published TEXT, modified TEXT,
                description TEXT, severity TEXT, base_score REAL,
                exploit_score REAL, impact_score REAL,
                vector_string TEXT, cwe_id TEXT,
                raw_json TEXT
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS affected_products (
                cve_id TEXT, vendor TEXT, product TEXT, version TEXT,
                FOREIGN KEY (cve_id) REFERENCES cves(id)
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS references_links (
                cve_id TEXT, url TEXT, tags TEXT,
                FOREIGN KEY (cve_id) REFERENCES cves(id)
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS exploit_matches (
                cve_id TEXT, edb_id TEXT, name TEXT, platform TEXT,
                reliability TEXT, source TEXT,
                FOREIGN KEY (cve_id) REFERENCES cves(id)
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_cve_severity ON cves(severity)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_cve_score ON cves(base_score)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_product ON affected_products(product, version)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_cwe ON cves(cwe_id)")
            db.commit()

    def download_nvd(self, days_back: int = 7):
        """Download latest CVE data from NVD API."""
        print(f"[CVE] Downloading NVD data (last {days_back} days)...")
        base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        params = f"?pubStartDate={(datetime.utcnow() - timedelta(days=days_back)).isoformat()}&resultsPerPage=100"
        url = base_url + params

        try:
            r = urllib.request.Request(url, headers={"User-Agent": "HackWithAI-v2"})
            with urllib.request.urlopen(r, timeout=30) as resp:
                data = json.loads(resp.read())
            count = 0
            for item in data.get("vulnerabilities", []):
                self._store_cve(item.get("cve", {}))
                count += 1
            print(f"[CVE] Stored {count} CVEs")
            return count
        except Exception as e:
            print(f"[CVE] Download failed: {e}")
            return 0

    def _store_cve(self, cve_data: Dict):
        cve_id = cve_data.get("id", "")
        if not cve_id:
            return
        pub = cve_data.get("published", "")
        mod = cve_data.get("lastModified", "")
        desc = ""
        for d in cve_data.get("descriptions", []):
            if d.get("lang") == "en":
                desc = d.get("value", "")
                break

        metrics = cve_data.get("metrics", {}).get("cvssMetricV31", []) or \
                  cve_data.get("metrics", {}).get("cvssMetricV30", [])
        sev, score, exp_score, imp_score, vec, cwe = "", 0.0, 0.0, 0.0, "", ""
        if metrics:
            cvss = metrics[0].get("cvssData", {})
            score = cvss.get("baseScore", 0.0)
            sev = cvss.get("baseSeverity", "")
            vec = cvss.get("vectorString", "")
            exp_score = metrics[0].get("exploitabilityScore", 0.0)
            imp_score = metrics[0].get("impactScore", 0.0)

        # CWE
        for w in cve_data.get("weaknesses", []):
            for d in w.get("description", []):
                if d.get("value", "").startswith("CWE-"):
                    cwe = d["value"]
                    break

        with sqlite3.connect(self.db_path) as db:
            db.execute("""INSERT OR REPLACE INTO cves VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                       (cve_id, pub, mod, desc, sev, score, exp_score, imp_score, vec, cwe,
                        json.dumps(cve_data)))

            # Affected products
            for node in cve_data.get("configurations", []):
                for match in node.get("nodes", []):
                    for cpe in match.get("cpeMatch", []):
                        criteria = cpe.get("criteria", "")
                        parts = criteria.split(":")
                        if len(parts) >= 4:
                            db.execute("INSERT OR IGNORE INTO affected_products VALUES (?,?,?,?)",
                                       (cve_id, parts[3], parts[4], cpe.get("versionEndExcluding", "*")))

            # References
            for ref in cve_data.get("references", []):
                url = ref.get("url", "")
                tags = ",".join(ref.get("tags", []))
                db.execute("INSERT OR IGNORE INTO references_links VALUES (?,?,?)", (cve_id, url, tags))

        db.commit()

    def search(self, query: str = "", product: str = "", severity: str = "",
               min_score: float = 0.0, limit: int = 50) -> List[Dict]:
        results = []
        sql = "SELECT DISTINCT c.id, c.description, c.severity, c.base_score, c.cwe_id FROM cves c"
        params: List = []
        joins = []
        where = []

        if query:
            where.append("(c.id LIKE ? OR c.description LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])
        if product:
            joins.append("JOIN affected_products a ON c.id = a.cve_id")
            where.append("(a.product LIKE ?)")
            params.append(f"%{product}%")
        if severity:
            where.append("c.severity = ?")
            params.append(severity.upper())
        if min_score > 0:
            where.append("c.base_score >= ?")
            params.append(min_score)

        sql += " " + " ".join(joins)
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY c.base_score DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            for row in db.execute(sql, params):
                results.append(dict(row))
        return results

    def get_exploits(self, cve_id: str) -> List[Dict]:
        # Try searchsploit
        try:
            r = subprocess.run(["searchsploit", "--cve", cve_id, "-j"],
                             capture_output=True, text=True, timeout=30)
            if r.returncode == 0 and r.stdout.strip():
                return json.loads(r.stdout).get("RESULTS_EXPLOIT", [])
        except Exception:
            pass

        # Check local DB
        with sqlite3.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM exploit_matches WHERE cve_id=?", (cve_id,)).fetchall()
            return [dict(r) for r in rows]

    def match_exploits(self):
        """Match stored CVEs with searchsploit/exploit-db."""
        with sqlite3.connect(self.db_path) as db:
            cves = db.execute("SELECT id FROM cves").fetchall()
        count = 0
        for (cve_id,) in cves:
            try:
                r = subprocess.run(["searchsploit", "--cve", cve_id, "-j"],
                                 capture_output=True, text=True, timeout=15)
                if r.returncode == 0 and r.stdout.strip():
                    exploits = json.loads(r.stdout).get("RESULTS_EXPLOIT", [])
                    with sqlite3.connect(self.db_path) as db:
                        for exp in exploits:
                            db.execute("INSERT OR IGNORE INTO exploit_matches VALUES (?,?,?,?,?,?)",
                                      (cve_id, exp.get("EDB-ID", ""), exp.get("Title", ""),
                                       exp.get("Platform", ""), exp.get("Type", ""), "searchsploit"))
                    db.commit()
                    count += len(exploits)
            except Exception:
                pass
            time.sleep(1)  # Rate limit
        return count

    def stats(self) -> Dict:
        with sqlite3.connect(self.db_path) as db:
            total = db.execute("SELECT COUNT(*) FROM cves").fetchone()[0]
            critical = db.execute("SELECT COUNT(*) FROM cves WHERE base_score >= 9.0").fetchone()[0]
            exploits = db.execute("SELECT COUNT(DISTINCT cve_id) FROM exploit_matches").fetchone()[0]
        return {"total_cves": total, "critical": critical, "with_exploits": exploits}


class BinaryDiffer:
    """Compare patched vs unpatched binaries to identify vulnerability fixes."""

    def compare_binaries(self, original: str, patched: str) -> Dict:
        """Use radare2 to diff two binaries and find changed functions."""
        result = {"original": original, "patched": patched, "changed_functions": []}

        # Get function lists from both
        funcs1 = self._get_functions(original)
        funcs2 = self._get_functions(patched)

        # Find new, removed, and changed functions
        names1 = {f["name"] for f in funcs1}
        names2 = {f["name"] for f in funcs2}

        for f in funcs1:
            if f["name"] not in names2:
                result["changed_functions"].append({
                    "name": f["name"], "change": "removed",
                    "address": f.get("address"), "size": f.get("size")
                })
            else:
                # Check if size changed
                match = next((x for x in funcs2 if x["name"] == f["name"]), None)
                if match and f.get("size") != match.get("size"):
                    result["changed_functions"].append({
                        "name": f["name"], "change": "modified",
                        "old_size": f.get("size"), "new_size": match.get("size")
                    })

        for f in funcs2:
            if f["name"] not in names1:
                result["changed_functions"].append({
                    "name": f["name"], "change": "added",
                    "address": f.get("address"), "size": f.get("size")
                })

        return result

    def _get_functions(self, binary: str) -> List[Dict]:
        try:
            r = subprocess.run(["radare2", "-q", "-c", "aflj", binary],
                             capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                return json.loads(r.stdout) if r.stdout.strip() else []
        except Exception:
            pass
        return []


class FuzzerEngine:
    """Fuzzing integration: AFL, libFuzzer, custom network fuzzer."""

    def afl_fuzz(self, binary: str, input_dir: str, output_dir: str = "",
                 timeout: int = 3600) -> Dict:
        out = output_dir or str(DATA_DIR / "afl_output")
        Path(out).mkdir(parents=True, exist_ok=True)
        path = str(Path(input_dir).resolve())
        try:
            r = subprocess.run(
                ["afl-fuzz", "-i", input_dir, "-o", out, "--", binary],
                capture_output=True, text=True, timeout=timeout
            )
            crashes = len(list(Path(out).glob("crashes/*")))
            return {"ok": True, "crashes": crashes, "output_dir": out}
        except subprocess.TimeoutExpired:
            crashes = len(list(Path(out).glob("crashes/*")))
            return {"ok": True, "crashes": crashes, "output_dir": out, "note": "timeout expired"}
        except FileNotFoundError:
            return {"ok": False, "error": "AFL not found. Install: sudo apt install afl"}

    def generate_test_cases(self, protocol: str, count: int = 100) -> List[str]:
        """Generate fuzzing test cases for network protocols."""
        cases = []
        base = hashlib.md5(protocol.encode()).hexdigest()[:8]
        for i in range(count):
            payload = f"{base}:{i}:{'A' * i}:{'\\x00' * (i % 10)}:BEEF"
            cases.append(payload.encode().hex())
        return cases

    def network_fuzz(self, host: str, port: int, protocol: str = "tcp",
                     count: int = 100, delay: float = 0.1) -> Dict:
        """Send fuzzed payloads to a network service."""
        import socket
        results = {"host": host, "port": port, "sent": 0, "crashes": 0, "responses": []}
        cases = self.generate_test_cases(protocol, count)

        for i, case in enumerate(cases):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((host, port))
                payload = bytes.fromhex(case)
                sock.send(payload)
                try:
                    resp = sock.recv(4096)
                    results["responses"].append({"case": i, "response_hex": resp.hex()[:100]})
                except socket.timeout:
                    results["crashes"] += 1
                sock.close()
                results["sent"] += 1
            except Exception:
                results["crashes"] += 1
            time.sleep(delay)

        return results


class ExploitSuggester:
    """Suggests exploits based on detected software versions and CVE data."""

    def __init__(self, cve_db: CVEDatabase):
        self.cve_db = cve_db

    def suggest(self, product: str, version: str = "") -> List[Dict]:
        """Find matching exploits for a product/version."""
        results = []
        # Search CVE DB
        cves = self.cve_db.search(product=product, min_score=5.0)
        for cve in cves[:20]:
            exploits = self.cve_db.get_exploits(cve["id"])
            if exploits:
                results.append({
                    "cve_id": cve["id"],
                    "severity": cve["severity"],
                    "score": cve["base_score"],
                    "description": cve["description"][:200],
                    "exploits": exploits,
                })

        # Also try searchsploit directly
        try:
            query = f"{product} {version}".strip()
            r = subprocess.run(["searchsploit", query, "-j"],
                             capture_output=True, text=True, timeout=15)
            if r.returncode == 0 and r.stdout.strip():
                for exp in json.loads(r.stdout).get("RESULTS_EXPLOIT", []):
                    results.append({
                        "cve_id": exp.get("Codes", ""),
                        "source": "searchsploit",
                        "title": exp.get("Title", ""),
                        "edb_id": exp.get("EDB-ID", ""),
                        "path": exp.get("Path", ""),
                    })
        except Exception:
            pass

        return sorted(results, key=lambda x: x.get("score", 0) or 0, reverse=True)

    def generate_exploit_template(self, cve_id: str, target_os: str = "linux",
                                  target_arch: str = "x64") -> str:
        """Generate a basic exploit template for a CVE."""
        return f'''#!/usr/bin/env python3
"""Auto-generated exploit for {cve_id} | Target: {target_os}/{target_arch}"""

import socket, struct, sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 4444

# Exploit for {cve_id}
# Target: {target_os} {target_arch}
# Generated by HackWithAI v2 Zero-Day Scanner

def exploit():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    # Payload stage 1: trigger vulnerability
    buffer = b"A" * 1024
    s.send(buffer)

    # Payload stage 2: receive response
    try:
        data = s.recv(4096)
        print(f"Response: {{data[:200]}}")
    except:
        print("No response — service may have crashed")

    s.close()
    print("[*] Exploit completed")

if __name__ == "__main__":
    exploit()
'''


class AnomalyDetector:
    """Monitors for suspicious system behavior indicating potential exploitation."""

    def __init__(self):
        self.log_file = ANOMALY_LOG
        self.baseline = self._capture_baseline()

    def _capture_baseline(self) -> Dict:
        return {"timestamp": time.time(), "processes": set()}

    def scan(self) -> List[Dict]:
        """Scan for anomalies: suspicious processes, unexpected listeners, file changes."""
        anomalies = []

        # Check for unexpected listening ports
        try:
            r = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True, timeout=5)
            for line in r.stdout.split("\n"):
                if "LISTEN" in line and "127.0.0.1" not in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        port = parts[4].rsplit(":", 1)[-1]
                        proc = parts[-1] if len(parts) > 5 else ""
                        if any(svc in proc for svc in ["nc", "ncat", "socat", "python", "perl"]):
                            anomalies.append({
                                "type": "suspicious_listener",
                                "detail": line.strip(),
                                "port": port,
                                "process": proc,
                            })
        except Exception:
            pass

        # Check for unusual processes
        try:
            r = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)
            suspicious = ["reverse", "shell", "payload", "meterpreter", "beacon",
                         "backdoor", "bind", "cryptominer", "miner", "ransom"]
            for line in r.stdout.split("\n"):
                low = line.lower()
                for kw in suspicious:
                    if kw in low:
                        anomalies.append({
                            "type": "suspicious_process",
                            "keyword": kw,
                            "detail": line.strip()[:200],
                        })
                        break
        except Exception:
            pass

        # Log anomalies
        if anomalies:
            with open(self.log_file, "a") as f:
                ts = datetime.now().isoformat()
                for a in anomalies:
                    f.write(f"[{ts}] {json.dumps(a)}\n")

        return anomalies


class ZeroDayScanner:
    """Master zero-day vulnerability scanner."""

    def __init__(self):
        self.cve_db = CVEDatabase()
        self.differ = BinaryDiffer()
        self.fuzzer = FuzzerEngine()
        self.suggester = ExploitSuggester(self.cve_db)
        self.detector = AnomalyDetector()

    def full_scan(self, target: str, product_versions: List[Dict] = []) -> Dict:
        """Run a comprehensive vulnerability assessment."""
        result = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "cve_matches": [],
            "exploit_suggestions": [],
            "anomalies": [],
        }

        # 1. CVE search for each detected product
        for pv in product_versions:
            product = pv.get("product", "")
            version = pv.get("version", "")
            if product:
                cves = self.cve_db.search(product=product, min_score=5.0)
                result["cve_matches"].extend(cves)

        # 2. Exploit suggestions
        if product_versions:
            pv = product_versions[0]
            result["exploit_suggestions"] = self.suggester.suggest(
                pv.get("product", ""), pv.get("version", "")
            )

        # 3. Anomaly scan
        result["anomalies"] = self.detector.scan()

        return result

    def status(self) -> Dict:
        return {
            "cve_database": self.cve_db.stats(),
            "anomaly_log_lines": sum(1 for _ in open(ANOMALY_LOG)) if ANOMALY_LOG.exists() else 0,
        }


# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    scanner = ZeroDayScanner()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "status":
        print(json.dumps(scanner.status(), indent=2))
    elif cmd == "download":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        print(f"Downloaded {scanner.cve_db.download_nvd(days)} CVEs")
    elif cmd == "search":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        results = scanner.cve_db.search(query=query)
        print(json.dumps(results, indent=2))
    elif cmd == "suggest":
        product = sys.argv[2] if len(sys.argv) > 2 else "apache"
        version = sys.argv[3] if len(sys.argv) > 3 else ""
        print(json.dumps(scanner.suggester.suggest(product, version), indent=2))
    elif cmd == "diff":
        orig, patched = sys.argv[2], sys.argv[3]
        print(json.dumps(scanner.differ.compare_binaries(orig, patched), indent=2))
    elif cmd == "fuzz":
        host, port = sys.argv[2], int(sys.argv[3])
        print(json.dumps(scanner.fuzzer.network_fuzz(host, port), indent=2))
    elif cmd == "anomalies":
        print(json.dumps(scanner.detector.scan(), indent=2))
    else:
        print("Commands: status | download | search | suggest | diff | fuzz | anomalies")
