import requests, json, time
from typing import Dict, List, Optional

class BurpSuiteAPI:
    def __init__(self, base_url="http://127.0.0.1:1337", api_key=""):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({"Accept":"application/json","Content-Type":"application/json","Authorization":f"Bearer {api_key}"})

    def _verify_connection(self):
        try:
            r = self.session.get(f"{self.base_url}/burp/api/v2/proxy/history", timeout=5)
            return r.status_code == 200
        except: return False

    def get_proxy_history(self, limit=100): return self.session.get(f"{self.base_url}/burp/api/v2/proxy/history", params={"limit":limit}).json().get("data",[]) if self.session.get(f"{self.base_url}/burp/api/v2/proxy/history", params={"limit":limit}).ok else []

    def start_scan(self, url, scan_config="light"):
        r = self.session.post(f"{self.base_url}/burp/api/v2/scan/", json={"url":url,"scanConfiguration":scan_config})
        return r.json().get("scanId") if r.ok else None

    def get_scan_status(self, scan_id):
        r = self.session.get(f"{self.base_url}/burp/api/v2/scan/{scan_id}")
        return r.json() if r.ok else {}

    def get_scan_issues(self, scan_id):
        r = self.session.get(f"{self.base_url}/burp/api/v2/scan/{scan_id}/issues")
        return r.json().get("issues",[]) if r.ok else []

    def run_full_audit(self, target_url, scan_config="crawl_and_audit", wait=True):
        print(f"[Burp] Starting scan on {target_url}")
        self.session.put(f"{self.base_url}/burp/api/v2/target/scope", json={"urls":[target_url]})
        scan_id = self.start_scan(target_url, scan_config)
        if not scan_id: return {"error":"Failed to start scan"}
        if wait:
            while True:
                s = self.get_scan_status(scan_id)
                pct = s.get("scanProgress",{}).get("percentage",0)
                n = s.get("scanProgress",{}).get("totalIssues",0)
                print(f"[Burp] {pct}% | {n} issues")
                if s.get("scanStatus") in ["succeeded","failed","cancelled"]: break
                time.sleep(5)
        issues = self.get_scan_issues(scan_id)
        return {"scan_id":scan_id,"target":target_url,"vulnerabilities":issues,"status":"succeeded"}

class BurpSuiteAgentTools:
    def __init__(self, burp): self.burp = burp
    def quick_scan(self, url): return self.burp.run_full_audit(url, "light")
    def deep_scan(self, url): return self.burp.run_full_audit(url, "crawl_and_audit")
    def check_sql_injection(self, url):
        sid = self.burp.start_scan(url, "sql_injection")
        return self.burp.get_scan_issues(sid) if sid else []
    def check_xss(self, url):
        sid = self.burp.start_scan(url, "xss")
        return self.burp.get_scan_issues(sid) if sid else []
