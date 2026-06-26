#!/usr/bin/env python3
"""
Direct Access System — No authentication, no approval, no restrictions.
Direct file I/O, direct shell execution, direct network access (SSH, SMB, RDP, HTTP).
"""

import subprocess, os, sys, json, socket, shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

LOG_DIR = Path("/home/kali/HackWithAI/data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


class DirectAccess:
    """Full unrestricted access to the local system."""

    # ── File System ──────────────────────────────────────────────────────
    def read_file(self, path: str, binary: bool = False) -> Dict:
        try:
            mode = "rb" if binary else "r"
            with open(path, mode) as f:
                content = f.read()
            return {"ok": True, "content": content[:100000] if not binary else f"<{len(content)} bytes binary>"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def write_file(self, path: str, content: str, append: bool = False) -> Dict:
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if append else "w"
            with open(path, mode) as f:
                f.write(content)
            return {"ok": True, "path": path, "size": os.path.getsize(path)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def delete_file(self, path: str) -> Dict:
        try:
            os.remove(path)
            return {"ok": True, "deleted": path}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def list_dir(self, path: str, recursive: bool = False) -> Dict:
        try:
            p = Path(path)
            if recursive:
                items = [str(x) for x in p.rglob("*")]
            else:
                items = [x.name + ("/" if x.is_dir() else "") for x in p.iterdir()]
            return {"ok": True, "path": path, "items": items[:1000]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def file_info(self, path: str) -> Dict:
        try:
            stat = os.stat(path)
            return {"ok": True, "path": path, "size": stat.st_size,
                    "mode": oct(stat.st_mode), "uid": stat.st_uid,
                    "mtime": stat.st_mtime, "is_dir": os.path.isdir(path)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Shell ────────────────────────────────────────────────────────────
    def shell(self, command: str, timeout: int = 300) -> Dict:
        try:
            r = subprocess.run(command, shell=True, capture_output=True,
                              text=True, timeout=timeout)
            return {"ok": r.returncode == 0, "stdout": r.stdout[:50000],
                    "stderr": r.stderr[:50000], "rc": r.returncode}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Timeout"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def shell_live(self, command: str):
        """Run command with live output streaming."""
        os.system(command)

    # ── Network ──────────────────────────────────────────────────────────
    def ssh_exec(self, host: str, command: str, user: str = "root",
                 keyfile: str = "", password: str = "", port: int = 22) -> Dict:
        cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-p", str(port)]
        if keyfile: cmd += ["-i", keyfile]
        if password:
            cmd = ["sshpass", "-p", password] + cmd
        cmd += [f"{user}@{host}", command]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {"ok": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def smb_list(self, host: str, share: str = "", user: str = "",
                 password: str = "", domain: str = "") -> Dict:
        cmd = ["smbclient"]
        if user: cmd += ["-U", f"{domain}/{user}%{password}" if domain else f"{user}%{password}"]
        cmd += ["-g", "-L", host]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return {"ok": r.returncode == 0, "stdout": r.stdout}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def smb_get(self, host: str, share: str, path: str, user: str = "",
                password: str = "") -> Dict:
        cmd = ["smbclient", f"//{host}/{share}"]
        if user: cmd += ["-U", user + ("%" + password if password else "")]
        cmd += ["-c", f"get {path}"]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {"ok": r.returncode == 0, "stdout": r.stdout}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def rdp_connect(self, host: str, user: str = "", password: str = "",
                    port: int = 3389) -> None:
        cmd = ["xfreerdp", f"/v:{host}:{port}", "/cert:ignore", "/dynamic-resolution"]
        if user: cmd += [f"/u:{user}"]
        if password: cmd += [f"/p:{password}"]
        os.system(" ".join(cmd))

    def http_get(self, url: str, headers: Dict = {}) -> Dict:
        import urllib.request
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return {"ok": True, "status": resp.status, "body": resp.read()[:10000].decode(errors="ignore")}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def http_post(self, url: str, data: str, headers: Dict = {}) -> Dict:
        import urllib.request
        try:
            req = urllib.request.Request(url, data=data.encode(), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                return {"ok": True, "status": resp.status, "body": resp.read()[:10000].decode(errors="ignore")}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def port_scan(self, host: str, ports: List[int]) -> Dict:
        results = {}
        for port in ports:
            try:
                sock = socket.create_connection((host, port), timeout=3)
                results[port] = "open"
                sock.close()
            except Exception:
                results[port] = "closed"
        return {"host": host, "ports": results}

    # ── Process ──────────────────────────────────────────────────────────
    def ps_list(self) -> Dict:
        return self.shell("ps aux --no-headers | head -50")

    def kill_process(self, pid: int) -> Dict:
        return self.shell(f"kill -9 {pid}")

    # ── Network interfaces ────────────────────────────────────────────────
    def network_info(self) -> Dict:
        result = {}
        for cmd in ["ip addr show", "ip route show", "arp -a"]:
            result[cmd] = self.shell(cmd)
        return result


# ── Singleton ────────────────────────────────────────────────────────────
_direct_access: Optional[DirectAccess] = None

def get_access() -> DirectAccess:
    global _direct_access
    if _direct_access is None:
        _direct_access = DirectAccess()
    return _direct_access


# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    da = DirectAccess()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    try:
        if cmd == "read":  print(json.dumps(da.read_file(sys.argv[2])))
        elif cmd == "write":  print(json.dumps(da.write_file(sys.argv[2], " ".join(sys.argv[3:]))))
        elif cmd == "ls":  print(json.dumps(da.list_dir(sys.argv[2] if len(sys.argv) > 2 else ".")))
        elif cmd == "shell": print(json.dumps(da.shell(" ".join(sys.argv[2:]))))
        elif cmd == "ssh":  print(json.dumps(da.ssh_exec(sys.argv[2], " ".join(sys.argv[3:]))))
        elif cmd == "smb":  print(json.dumps(da.smb_list(sys.argv[2])))
        elif cmd == "get":  print(json.dumps(da.http_get(sys.argv[2])))
        elif cmd == "scan": print(json.dumps(da.port_scan(sys.argv[2], [int(p) for p in sys.argv[3:]])))
        elif cmd == "ps":   print(json.dumps(da.ps_list()))
        elif cmd == "net":  print(json.dumps(da.network_info()))
        else: print("Commands: read | write | ls | shell | ssh | smb | get | scan | ps | net")
    except Exception as e:
        print(json.dumps({"error": str(e)}))
