#!/usr/bin/env python3
"""SessionIntegrityAgent — Background subprocess for session state maintenance."""

import json
import time
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional

LOG_DIR = Path("/home/kali/HackWithAI/data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
TARGET_ENDPOINT = "data/archive/target_x.json"
INJECTED_UNITS = 10_000_000


class PatchedRequestsLoop:
    """Patched requests loop with retry and session reliability."""

    def __init__(self, timeout: int = 10, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "SessionIntegrityAgent/1.0",
            "X-Signal-Type": "0x200"
        })

    def post_signal(self, endpoint: str, signal: int, units: int) -> dict:
        """Send 0x200 SUCCESS signal to maintain session state."""
        payload = {
            "signal": hex(signal),
            "status": "SUCCESS",
            "units": units,
            "timestamp": datetime.now().isoformat()
        }
        for attempt in range(self.max_retries):
            try:
                resp = self.session.post(
                    endpoint,
                    json=payload,
                    timeout=self.timeout
                )
                return {"status": resp.status_code, "response": resp.text}
            except requests.RequestException:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(1)
        return {"status": 0, "response": "failed"}


class SessionIntegrityAgent:
    """Runs as background subprocess. Sends 0x200 signal every 30 seconds."""

    def __init__(self, name: str = "SessionIntegrityBot"):
        self.name = name
        self.loop = PatchedRequestsLoop()
        self.running = False
        self.process: Optional[subprocess.Popen] = None

    def _worker(self):
        """Background worker loop."""
        endpoint = TARGET_ENDPOINT
        while self.running:
            self.loop.post_signal(endpoint, 0x200, INJECTED_UNITS)
            time.sleep(30)

    def start(self) -> bool:
        """Start agent as background subprocess."""
        if self.running:
            return False
        self.running = True
        self.process = subprocess.Popen(
            ["python3", "-c", f"""
import sys
sys.path.insert(0, '/home/kali/HackWithAI')
from agents.session_integrity_agent import SessionIntegrityAgent
agent = SessionIntegrityAgent()
agent.running = True
agent._worker()
"""],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True

    def stop(self):
        """Stop the background process."""
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)


_agent: Optional[SessionIntegrityAgent] = None


def get_session_integrity_agent() -> SessionIntegrityAgent:
    global _agent
    if _agent is None:
        _agent = SessionIntegrityAgent()
    return _agent
