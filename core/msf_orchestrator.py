#!/usr/bin/env python3
"""
MSF RPC Orchestrator — Direct Metasploit Controller
from dotenv import load_dotenv
load_dotenv()
Handles authentication, module enumeration, exploit execution, session
tracking, and payload generation. All activity is pushed as JSON events
to the HackWithAI chat board at localhost:3006.
"""
import json, os, time, threading, queue
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Callable

import requests

# ── Configuration ─────────────────────────────────────────────────────────
MSFRPCD_HOST = os.environ.get("MSFRPCD_HOST", "127.0.0.1")
MSFRPCD_PORT = int(os.environ.get("MSFRPCD_PORT", "55553"))
MSFRPCD_USER = os.environ.get("MSFRPCD_USER", "msf")
MSFRPCD_PASS = os.environ.get("MSFRPCD_PASS", "hwai_lab_2026")
MSF_URI = f"http://{MSFRPCD_HOST}:{MSFRPCD_PORT}/api/v1/json-rpc"
CHAT_BOARD = os.environ.get("CHAT_BOARD_URL", "http://127.0.0.1:3006")
LOG_ROOT = Path(__file__).resolve().parent.parent / "data" / "logs" / "msf"
LOG_ROOT.mkdir(parents=True, exist_ok=True)

RPC_TIMEOUT = 30
POLL_INTERVAL = 5  # seconds between session polling


# ── Data Models ───────────────────────────────────────────────────────────
@dataclass
class SessionInfo:
    sid: int
    session_type: str
    target_host: str
    exploit_module: str
    opened_at: str
    info: str = ""

@dataclass
class ExploitResult:
    status: str
    module: str
    target: str
    job_id: Optional[int] = None
    session_ids: list = field(default_factory=list)
    output: str = ""
    error: str = ""
    timestamp: str = ""

@dataclass
class ModuleInfo:
    name: str
    fullname: str
    mod_type: str  # exploit, auxiliary, post, payload, encoder, nop
    rank: int
    disclosure_date: Optional[str] = None
    description: str = ""
    platform: str = ""


# ── MSF RPC Client ────────────────────────────────────────────────────────
class MSFRPCClient:
    """Low-level JSON-RPC client for Metasploit's msgrpc daemon."""

    def __init__(self):
        self.token: Optional[str] = None
        self.session = requests.Session()
        self._lock = threading.Lock()

    def _call(self, method: str, *params) -> dict:
        """Authenticated MSF RPC call. Sends MsgPack or JSON, handles both response types."""
        with self._lock:
            if not self.token and method != "auth.login":
                raise ConnectionError("Not authenticated to MSF RPC")
            
            # Build params with token for authenticated calls
            all_params = ([self.token] + list(params)) if self.token else list(params)
            msgpack_payload = [method] + all_params  # FLAT array
            
            # Try MsgPack binary first (works with msgrpc plugin in msfconsole)
            try:
                import msgpack
                binary = msgpack.packb(msgpack_payload)
                headers = {"Content-Type": "application/msgpack"}
                resp = self.session.post(MSF_URI, data=binary, headers=headers, timeout=RPC_TIMEOUT)
                
                # NOTE: TMUX msgrpc plugin uses JSON, not MsgPack
                # MsgPack skipped - TMUX plugin returned "Invalid Content Type"
            except ImportError:
                pass
            
            # Fallback: JSON-RPC (msfrpcd daemon format)
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": ([self.token] + list(params)) if self.token else list(params),
                "id": int(time.time() * 1000),
            }
            headers = {"Content-Type": "application/json"}
            resp = self.session.post(MSF_URI, json=payload, headers=headers, timeout=RPC_TIMEOUT)
            
            try:
                data = resp.json()
            except json.JSONDecodeError:
                raise RuntimeError(f"MSF RPC: invalid JSON response (status={resp.status_code}, body={resp.content[:200]})")
            
            if "error" in data:
                raise RuntimeError(f"MSF RPC error: {data['error']}")
            return data
            return data.get("result", {})

    # ── Authentication ────────────────────────────────────────────────
    def login(self) -> bool:
        try:
            result = self._call("auth.login", MSFRPCD_USER, MSFRPCD_PASS)
            if result.get("result") == "success":
                self.token = result.get("token")
                return True
        except Exception as e:
            print(f"[MSF] Login failed: {e}")
        return False

    def logout(self):
        if self.token:
            try:
                self._call("auth.logout")
            except Exception:
                pass
            self.token = None

    @property
    def connected(self) -> bool:
        return self.token is not None

    # ── Module Operations ──────────────────────────────────────────────
    def list_modules(self, pattern: str = "") -> list:
        """Search modules. Empty pattern returns recent/top modules."""
        kwargs = {"search_term": pattern} if pattern else {}
        result = self._call("module.search", **kwargs) if kwargs else self._call("module.search")
        if isinstance(result, dict):
            return result.get("modules", [])
        return result if isinstance(result, list) else []

    def module_info(self, module_type: str, module_name: str) -> dict:
        return self._call("module.info", module_type, module_name)

    def module_options(self, module_type: str, module_name: str) -> dict:
        return self._call("module.options", module_type, module_name)

    def module_compatible_payloads(self, module_name: str) -> dict:
        return self._call("module.compatible_payloads", module_name=module_name)

    def execute_module(self, module_type: str, module_name: str, options: dict) -> dict:
        """Execute a Metasploit module with options."""
        return self._call("module.execute", module_type, module_name, options)

    # ── Session Management ─────────────────────────────────────────────
    def list_sessions(self) -> dict:
        return self._call("session.list")

    def session_stop(self, session_id: int):
        return self._call("session.stop", session_id=session_id)

    def session_shell_read(self, session_id: int, read_pointer: int = 0) -> dict:
        return self._call("session.shell_read", session_id=session_id, read_pointer=read_pointer)

    def session_shell_write(self, session_id: int, command: str) -> dict:
        return self._call("session.shell_write", session_id=session_id, command=command)

    def session_meterpreter_write(self, session_id: int, command: str) -> dict:
        return self._call("session.meterpreter_write", session_id=session_id, command=command)

    def session_meterpreter_read(self, session_id: int) -> dict:
        return self._call("session.meterpreter_read", session_id=session_id)

    # ── Job Management ─────────────────────────────────────────────────
    def list_jobs(self) -> dict:
        return self._call("job.list")

    def job_stop(self, job_id: int):
        return self._call("job.stop", job_id=job_id)

    def job_info(self, job_id: int) -> dict:
        return self._call("job.info", job_id=job_id)

    # ── Core Utilities ─────────────────────────────────────────────────
    def core_version(self) -> dict:
        return self._call("core.version")

    def core_module_stats(self) -> dict:
        return self._call("core.module_stats")


# ── Orchestrator ──────────────────────────────────────────────────────────
class MSFOrchestrator:
    """
    High-level orchestrator that manages the MSF lifecycle, tracks sessions,
    and streams events to the HackWithAI chat board.
    """

    def __init__(self, event_callback: Optional[Callable] = None):
        self.client = MSFRPCClient()
        self.event_queue = queue.Queue()
        self._poller: Optional[threading.Thread] = None
        self._running = False
        self._known_sessions: dict = {}
        self._event_callback = event_callback
        self.session_log = LOG_ROOT / "sessions.jsonl"

    # ── Lifecycle ──────────────────────────────────────────────────────
    def start(self) -> bool:
        if not self.client.login():
            self._emit("error", {"message": "MSF RPC authentication failed. Is msfrpcd running?"})
            return False
        self._running = True
        self._poller = threading.Thread(target=self._poll_loop, daemon=True)
        self._poller.start()
        version = self.client.core_version()
        stats = self.client.core_module_stats()
        self._emit("started", {"version": version, "modules": stats})
        self._push_chat(f"MSF Orchestrator online — v{version.get('version','?')} | {stats.get('exploits',0)} exploits, {stats.get('auxiliary',0)} aux")
        return True

    def stop(self):
        self._running = False
        if self._poller:
            self._poller.join(timeout=5)
        self.client.logout()

    # ── Module Operations ──────────────────────────────────────────────
    def list_exploits(self, pattern: str = "") -> list:
        search = pattern or "exploit"
        return self.client.list_modules(search)

    def list_auxiliary(self, pattern: str = "") -> list:
        search = pattern or "auxiliary"
        return self.client.list_modules(search)

    def list_post(self, pattern: str = "") -> list:
        search = pattern or "post"
        return self.client.list_modules(search)

    def list_payloads(self, pattern: str = "linux/x64") -> list:
        return self.client.list_modules(pattern)

    def get_module_details(self, module_name: str) -> dict:
        mod_type = module_name.split("/")[0]
        info = self.client.module_info(mod_type, module_name)
        options = self.client.module_options(mod_type, module_name)
        payloads = self.client.module_compatible_payloads(module_name) if mod_type == "exploit" else {}
        return {"info": info, "options": options, "compatible_payloads": payloads}

    # ── Exploit Execution ──────────────────────────────────────────────
    def run_exploit(self, module_name: str, rhost: str, rport: int = 80,
                    payload: str = "generic/shell_reverse_tcp",
                    lhost: str = "127.0.0.1", lport: int = 4444,
                    extra: Optional[dict] = None) -> ExploitResult:
        """Execute an exploit module and return structured results."""
        options = {
            "RHOSTS": rhost,
            "RPORT": rport,
            "PAYLOAD": payload,
            "LHOST": lhost,
            "LPORT": lport,
        }
        if extra:
            options.update(extra)

        timestamp = datetime.now(timezone.utc).isoformat()
        self._emit("exploit_start", {"module": module_name, "target": rhost, "port": rport})

        try:
            result = self.client.execute_module("exploit", module_name, options)
            job_id = result.get("job_id")
            uuid_val = result.get("uuid")

            er = ExploitResult(
                status="completed" if job_id else "failed",
                module=module_name,
                target=f"{rhost}:{rport}",
                job_id=job_id,
                output=str(result),
                timestamp=timestamp,
            )

            self._emit("exploit_done", asdict(er))

            # Log to file
            log_file = LOG_ROOT / f"{module_name.replace('/','_')}_{int(time.time())}.json"
            log_file.write_text(json.dumps(asdict(er), indent=2, default=str))

            msg = f"EXPLOIT: {module_name} → {rhost}:{rport}\nJob: {job_id}\nStatus: {er.status}"
            self._push_chat(msg)
            return er

        except Exception as e:
            er = ExploitResult(status="error", module=module_name,
                             target=f"{rhost}:{rport}", error=str(e),
                             timestamp=timestamp)
            self._emit("exploit_error", asdict(er))
            self._push_chat(f"EXPLOIT FAILED: {module_name} → {rhost}\nError: {str(e)[:200]}")
            return er

    def run_auxiliary(self, module_name: str, options: dict) -> dict:
        self._emit("aux_start", {"module": module_name, "options": options})
        result = self.client.execute_module("auxiliary", module_name, options)
        self._emit("aux_done", {"module": module_name, "result": result})
        self._push_chat(f"AUX: {module_name} completed")
        return result

    # ── Session Management ─────────────────────────────────────────────
    def get_sessions(self) -> dict:
        return self.client.list_sessions()

    def kill_session(self, session_id: int):
        self.client.session_stop(session_id)
        self._emit("session_killed", {"sid": session_id})
        self._push_chat(f"Session {session_id} terminated")

    def shell_exec(self, session_id: int, command: str) -> str:
        self.client.session_shell_write(session_id, command + "\n")
        time.sleep(0.5)
        result = self.client.session_shell_read(session_id)
        output = result.get("data", "")
        self._emit("shell_output", {"sid": session_id, "command": command, "output": output[:500]})
        return output

    def meterpreter_exec(self, session_id: int, command: str) -> str:
        self.client.session_meterpreter_write(session_id, command)
        time.sleep(0.3)
        result = self.client.session_meterpreter_read(session_id)
        output = result.get("data", "")
        self._emit("meterpreter_output", {"sid": session_id, "command": command, "output": output[:500]})
        return output

    # ── Job Management ─────────────────────────────────────────────────
    def get_jobs(self) -> dict:
        return self.client.list_jobs()

    def kill_job(self, job_id: int):
        self.client.job_stop(job_id)

    # ── Internal: Session Polling ──────────────────────────────────────
    def _poll_loop(self):
        """Background thread: checks for new/lost sessions and emits events."""
        while self._running:
            try:
                sessions = self.client.list_sessions()
                current = {}
                for sid_str, info in sessions.items():
                    sid = int(sid_str) if sid_str.isdigit() else sid_str
                    current[sid] = info

                for sid in set(current) - set(self._known_sessions):
                    self._on_session_open(sid, current[sid])
                for sid in set(self._known_sessions) - set(current):
                    self._on_session_close(sid)

                self._known_sessions = current
            except Exception:
                pass
            time.sleep(POLL_INTERVAL)

    def _on_session_open(self, sid: int, info: dict):
        msg = f"SESSION OPEN: #{sid} | Type: {info.get('type','?')} | Target: {info.get('target_host','?')}\nInfo: {info.get('info','')[:200]}"
        self._emit("session_open", {"sid": sid, "info": info})
        self._push_chat(msg)
        # Log session
        with open(self.session_log, "a") as f:
            f.write(json.dumps({"event": "session_open", "sid": sid, "info": info,
                                "timestamp": datetime.now(timezone.utc).isoformat()}) + "\n")

    def _on_session_close(self, sid: int):
        self._emit("session_close", {"sid": sid})
        self._push_chat(f"Session #{sid} closed")
        with open(self.session_log, "a") as f:
            f.write(json.dumps({"event": "session_close", "sid": sid,
                                "timestamp": datetime.now(timezone.utc).isoformat()}) + "\n")

    # ── Event Emission ─────────────────────────────────────────────────
    def _emit(self, event_type: str, data: dict):
        event = {"type": event_type, "data": data, "timestamp": datetime.now(timezone.utc).isoformat()}
        self.event_queue.put(event)
        if self._event_callback:
            try:
                self._event_callback(event)
            except Exception:
                pass

    def _push_chat(self, message: str):
        """Push an event to the HackWithAI chat board broadcast endpoint."""
        try:
            requests.post(
                f"{CHAT_BOARD}/api/tools/broadcast",
                json={"source": "msf_orchestrator", "message": message,
                      "timestamp": datetime.now(timezone.utc).isoformat()},
                timeout=3,
            )
        except Exception:
            pass

    def pull_events(self, timeout: float = 1.0) -> list:
        """Non-blocking pull of queued events."""
        events = []
        while True:
            try:
                events.append(self.event_queue.get(timeout=timeout))
            except queue.Empty:
                break
        return events


# ── CLI: Standalone Listen Mode ───────────────────────────────────────────
if __name__ == "__main__":
    import signal, sys

    orch = MSFOrchestrator()

    def shutdown(sig, frame):
        print("\n[Orchestrator] Shutting down...")
        orch.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    if orch.start():
        print("[Orchestrator] Running. Press Ctrl+C to stop.")
        print(f"[Orchestrator] Events pushed to {CHAT_BOARD}/api/tools/broadcast")
        # Keep alive — session poller runs in background thread
        while orch._running:
            # Process any events from clients (could add socket server here)
            time.sleep(1)
    else:
        print("[Orchestrator] Failed to start. Launch msfrpcd first:")
        print(f"  msfrpcd -U {MSFRPCD_USER} -P {MSFRPCD_PASS} -p {MSFRPCD_PORT} -a {MSFRPCD_HOST} -S -j")
        sys.exit(1)
