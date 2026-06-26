import os, subprocess, shutil

KALI_TOOLS = {
    "nmap": "nmap -sV -sC {target}",
    "sqlmap": "sqlmap -u {target} --batch",
    "gobuster": "gobuster dir -u {target} -w /usr/share/wordlists/dirb/common.txt",
    "nikto": "nikto -h {target}",
    "hydra": "hydra -l admin -P /usr/share/wordlists/rockyou.txt {target} ssh",
    "ffuf": "ffuf -u {target}/FUZZ -w /usr/share/wordlists/dirb/common.txt",
    "subfinder": "subfinder -d {target}",
    "metasploit": "msfconsole -q",
}

def list_installed_tools():
    return [name for name, cmd in KALI_TOOLS.items() if shutil.which(name.split()[0])]

def run_tool(name, target):
    if name in KALI_TOOLS:
        cmd = KALI_TOOLS[name].format(target=target)
        return subprocess.check_output(cmd, shell=True, text=True)
    return "Tool not found"
