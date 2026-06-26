#!/usr/bin/env python3
"""Web Hacking Tools — nikto, wpscan, dirb/gobuster/ffuf, xsstrike, wafw00f"""

import subprocess, json, sys, shutil
from pathlib import Path
from typing import List, Dict

OUTPUT_DIR = Path("/home/kali/HackWithAI/data/scans")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _run(cmd: List[str], timeout: int = 300, capture: bool = True) -> dict:
    try:
        r = subprocess.run(cmd, capture_output=capture, text=True, timeout=timeout)
        return {"ok": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr, "rc": r.returncode}
    except FileNotFoundError:
        return {"ok": False, "error": f"Tool not found: {cmd[0]}"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Timeout"}

def _which(tool: str) -> bool: return shutil.which(tool) is not None

# ── nikto ────────────────────────────────────────────────────────────────
def nikto_scan(url: str, ssl: bool = False, tuning: str = "") -> dict:
    cmd = ["nikto", "-h", url]
    if ssl: cmd.append("-ssl")
    if tuning: cmd += ["-Tuning", tuning]
    cmd += ["-Format", "json", "-output", str(OUTPUT_DIR / "nikto_scan.json")]
    return _run(cmd, timeout=600)

# ── wpscan ───────────────────────────────────────────────────────────────
def wpscan_scan(url: str, api_token: str = "", enumerate: str = "vp,vt,u") -> dict:
    cmd = ["wpscan", "--url", url, "-e", enumerate, "--format", "json",
           "-o", str(OUTPUT_DIR / "wpscan.json"), "--random-user-agent"]
    if api_token: cmd += ["--api-token", api_token]
    return _run(cmd, timeout=600)

# ── Dirbuster / Gobuster / FFUF ──────────────────────────────────────────
def gobuster_dir(url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt",
                 extensions: str = "php,html,txt") -> dict:
    return _run(["gobuster", "dir", "-u", url, "-w", wordlist, "-x", extensions, "-t", "50"],
                timeout=300)

def gobuster_dns(domain: str, wordlist: str = "/usr/share/wordlists/dns.txt") -> dict:
    return _run(["gobuster", "dns", "-d", domain, "-w", wordlist, "-t", "50"], timeout=300)

def gobuster_vhost(url: str, wordlist: str) -> dict:
    return _run(["gobuster", "vhost", "-u", url, "-w", wordlist, "-t", "50"], timeout=300)

def ffuf_fuzz(url: str, wordlist: str, match_codes: str = "200,204,301,302,307,401,403,405",
              fuzz_keyword: str = "FUZZ") -> dict:
    return _run(["ffuf", "-u", url.replace(fuzz_keyword, "FUZZ"), "-w", wordlist,
                 "-mc", match_codes, "-t", "50", "-o", str(OUTPUT_DIR / "ffuf.json"),
                 "-of", "json"], timeout=300)

def dirsearch(url: str, wordlist: str = "", extensions: str = "php,html,txt") -> dict:
    cmd = ["dirsearch", "-u", url, "-e", extensions, "--format", "json",
           "-o", str(OUTPUT_DIR / "dirsearch.json")]
    if wordlist: cmd += ["-w", wordlist]
    return _run(cmd, timeout=300)

# ── CMS Scanners ─────────────────────────────────────────────────────────
def joomscan(url: str) -> dict:
    return _run(["joomscan", "--url", url], timeout=120)

def droopescan(cms_type: str, url: str) -> dict:
    """cms_type: drupal, silverstripe, wordpress"""
    return _run(["droopescan", "scan", cms_type, "-u", url], timeout=120)

# ── WAF Detection ────────────────────────────────────────────────────────
def wafw00f_detect(url: str) -> dict:
    return _run(["wafw00f", url], timeout=60)

def whatweb_scan(url: str, aggression: int = 3) -> dict:
    """aggression: 1-4 (stealth to heavy)"""
    return _run(["whatweb", "-a", str(aggression), url], timeout=120)

# ── XSStrike ─────────────────────────────────────────────────────────────
def xsstrike(url: str, data: str = "", crawl: bool = False) -> dict:
    cmd = ["python3", "/opt/xsstrike/xsstrike.py", "-u", url]
    if data: cmd += ["--data", data]
    if crawl: cmd.append("--crawl")
    return _run(cmd, timeout=120)

# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "nikto":    print(json.dumps(nikto_scan(sys.argv[2])))
    elif cmd == "wpscan": print(json.dumps(wpscan_scan(sys.argv[2])))
    elif cmd == "gobuster": print(json.dumps(gobuster_dir(sys.argv[2])))
    elif cmd == "ffuf":   print(json.dumps(ffuf_fuzz(sys.argv[2], sys.argv[3])))
    elif cmd == "whatweb": print(json.dumps(whatweb_scan(sys.argv[2])))
    else: print("Commands: nikto | wpscan | gobuster | ffuf | whatweb")
