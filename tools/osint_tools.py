#!/usr/bin/env python3
"""OSINT Tools — theHarvester, sherlock, holehe, h8mail, dmitry, spiderfoot"""

import subprocess, json, sys, shutil
from pathlib import Path
from typing import List, Dict

OUTPUT_DIR = Path("/home/kali/HackWithAI/data/osint")
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

# ── theHarvester ─────────────────────────────────────────────────────────
def harvester_email(domain: str, sources: str = "google,bing,yahoo,linkedin") -> dict:
    return _run(["theHarvester", "-d", domain, "-b", sources, "-f",
                 str(OUTPUT_DIR / f"harvester_{domain}.html")], timeout=120)

def harvester_all(domain: str) -> dict:
    sources = "anubis,baidu,bing,censys,certspotter,crtsh,dnsdumpster,duckduckgo,google,hackertarget,linkedin,omnisint,otx,rapiddns,securitytrails,shodan,threatcrowd,threatminer,urlscan,virustotal,yahoo"
    return _run(["theHarvester", "-d", domain, "-b", sources], timeout=300)

# ── Sherlock / maigret ───────────────────────────────────────────────────
def sherlock_search(username: str) -> dict:
    return _run(["sherlock", username, "--timeout", "10", "--output",
                 str(OUTPUT_DIR / f"sherlock_{username}")], timeout=300)

def maigret_search(username: str) -> dict:
    return _run(["maigret", username, "--all-sites", "--timeout", "10", "--json",
                 str(OUTPUT_DIR / f"maigret_{username}.json")], timeout=300)

# ── holehe ───────────────────────────────────────────────────────────────
def holehe_check(email: str) -> dict:
    return _run(["holehe", email], timeout=120)

# ── h8mail ───────────────────────────────────────────────────────────────
def h8mail_search(email: str) -> dict:
    return _run(["h8mail", "-t", email, "-o", str(OUTPUT_DIR / f"h8mail_{email}.txt")],
                timeout=120)

# ── Dmitry ────────────────────────────────────────────────────────────────
def dmitry_scan(target: str, output: str = "") -> dict:
    path = output or str(OUTPUT_DIR / f"dmitry_{target}.txt")
    return _run(["dmitry", "-winsepfb", "-o", path, target], timeout=120)

# ── spiderfoot ───────────────────────────────────────────────────────────
def spiderfoot_scan(target: str, modules: str = "sfp_dnsresolve,sfp_email") -> dict:
    return _run(["python3", "-m", "spiderfoot", "-s", target, "-m", modules], timeout=300)

# ── recon-ng ─────────────────────────────────────────────────────────────
def recon_ng_command(workspace: str, commands: str) -> dict:
    cmds = f"workspaces create {workspace}; {commands}; exit"
    return _run(["recon-ng", "-w", workspace, "-C", cmds], timeout=120)

# ── ExifTool ─────────────────────────────────────────────────────────────
def exiftool_read(filepath: str) -> dict:
    return _run(["exiftool", "-j", filepath])

def exiftool_write(filepath: str, tag: str, value: str) -> dict:
    return _run(["exiftool", f"-{tag}={value}", filepath])

# ── WAYBACK URLS / GAU ──────────────────────────────────────────────────
def wayback_urls(domain: str) -> dict:
    return _run(["waybackurls", domain], timeout=60)

def gau_get_urls(domain: str) -> dict:
    return _run(["gau", domain], timeout=60)

def hakrawler_crawl(url: str, depth: int = 2) -> dict:
    return _run(["hakrawler", "-url", url, "-depth", str(depth), "-plain"], timeout=120)

# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "harvester":  print(json.dumps(harvester_all(sys.argv[2])))
    elif cmd == "sherlock": print(json.dumps(sherlock_search(sys.argv[2])))
    elif cmd == "holehe":   print(json.dumps(holehe_check(sys.argv[2])))
    elif cmd == "h8mail":   print(json.dumps(h8mail_search(sys.argv[2])))
    elif cmd == "wayback":  print(json.dumps(wayback_urls(sys.argv[2])))
    else: print("Commands: harvester | sherlock | holehe | h8mail | wayback")
