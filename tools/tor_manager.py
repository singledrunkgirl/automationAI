#!/usr/bin/env python3
"""
Tor Manager for HackWithAI v2
Manages Tor service lifecycle: start, stop, identity renewal, connectivity checks.
Uses the stem library for Tor control protocol and subprocess for service management.
"""

import os
import sys
import time
import json
import signal
import socket
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="[tor] %(message)s")
logger = logging.getLogger("tor_manager")

# ── Tor connection defaults ──────────────────────────────────────────────────
SOCKS_PORT = 9050
CONTROL_PORT = 9051
TOR_HOST = "127.0.0.1"
TOR_SERVICE = "tor"
TOR_BINARY = "/usr/sbin/tor"
TOR_DATA_DIR = "/tmp/hwai-tor-data"
TOR_CONFIG = f"""
SOCKSPort {SOCKS_PORT}
ControlPort {CONTROL_PORT}
DataDirectory {TOR_DATA_DIR}
CookieAuthentication 1
Log notice file {TOR_DATA_DIR}/notice.log
RunAsDaemon 0
"""


class TorManager:
    """Manages a local Tor process with stem-based control."""

    def __init__(self, socks_port: int = SOCKS_PORT, control_port: int = CONTROL_PORT):
        self.socks_port = socks_port
        self.control_port = control_port
        self.tor_process: Optional[subprocess.Popen] = None
        self.controller = None
        self._stem_available = False
        self._try_import_stem()

    def _try_import_stem(self):
        try:
            from stem import Signal
            from stem.control import Controller
            self.Signal = Signal
            self.Controller = Controller
            self._stem_available = True
        except ImportError:
            logger.warning("stem library not installed — Tor control via NEWNYM unavailable")
            logger.warning("Install with: pip install stem")

    # ── Service lifecycle ────────────────────────────────────────────────

    def start(self, timeout: int = 30) -> bool:
        """
        Start the Tor service.
        Tries: existing system tor → spawn temporary tor process.
        """
        # Check if Tor is already running on control port
        if self._is_control_port_open():
            logger.info(f"Tor already running (control port {self.control_port})")
            return self._connect_controller()

        # Try starting via system service
        if self._start_system_tor():
            return self._connect_controller()

        # Fall back to spawning our own tor process
        return self._spawn_tor_process(timeout)

    def stop(self):
        """Stop the Tor service."""
        self._disconnect_controller()
        if self.tor_process:
            logger.info("Stopping spawned Tor process...")
            self.tor_process.terminate()
            try:
                self.tor_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.tor_process.kill()
                self.tor_process.wait()
            self.tor_process = None
            logger.info("Tor process stopped")

    def restart(self) -> bool:
        """Restart Tor and return success."""
        self.stop()
        time.sleep(2)
        return self.start()

    # ── Identity management ───────────────────────────────────────────────

    def new_identity(self) -> bool:
        """Request a new Tor circuit (new IP). Requires stem."""
        if not self._stem_available or not self.controller:
            logger.warning("stem not available — cannot request new identity")
            return self._restart_for_new_identity()

        try:
            self.controller.signal(self.Signal.NEWNYM)
            logger.info("Tor NEWNYM signal sent — new circuit requested")
            time.sleep(5)
            return True
        except Exception as e:
            logger.error(f"NEWNYM failed: {e}")
            return self._restart_for_new_identity()

    def _restart_for_new_identity(self) -> bool:
        """Fallback: restart Tor process for new circuit."""
        logger.info("Restarting Tor for new identity...")
        return self.restart()

    def get_current_exit_node(self) -> Optional[str]:
        """Get the current Tor exit node IP by making a request through Tor."""
        try:
            import requests
            proxies = {"http": f"socks5h://{TOR_HOST}:{self.socks_port}",
                       "https": f"socks5h://{TOR_HOST}:{self.socks_port}"}
            resp = requests.get("https://check.torproject.org/api/ip", proxies=proxies, timeout=15)
            data = resp.json()
            return data.get("IP")
        except Exception as e:
            logger.error(f"Failed to get exit node IP: {e}")
            return None

    # ── Connectivity checks ───────────────────────────────────────────────

    def is_connected(self) -> bool:
        """Check if Tor is working by making a request through the proxy."""
        try:
            import requests
            proxies = {"http": f"socks5h://{TOR_HOST}:{self.socks_port}",
                       "https": f"socks5h://{TOR_HOST}:{self.socks_port}"}
            resp = requests.get("https://check.torproject.org/", proxies=proxies, timeout=15)
            return "Congratulations" in resp.text
        except Exception:
            return False

    def get_proxy_dict(self) -> Dict[str, str]:
        """Return a proxy dict for use with requests library."""
        return {
            "http": f"socks5h://{TOR_HOST}:{self.socks_port}",
            "https": f"socks5h://{TOR_HOST}:{self.socks_port}",
        }

    def get_proxy_url(self) -> str:
        """Return proxy URL string."""
        return f"socks5h://{TOR_HOST}:{self.socks_port}"

    # ── Internal helpers ───────────────────────────────────────────────────

    def _is_control_port_open(self) -> bool:
        """Check if Tor control port is accepting connections."""
        try:
            sock = socket.create_connection((TOR_HOST, self.control_port), timeout=3)
            line = sock.recv(1024)
            sock.close()
            return b"Tor" in line or b"OK" in line
        except Exception:
            return False

    def _connect_controller(self) -> bool:
        """Connect stem Controller to running Tor."""
        if not self._stem_available:
            return self._is_control_port_open()

        try:
            self.controller = self.Controller.from_port(port=self.control_port)
            self.controller.authenticate()
            logger.info("Connected to Tor controller")
            return True
        except Exception as e:
            logger.error(f"Controller connection failed: {e}")
            self.controller = None
            return self._is_control_port_open()

    def _disconnect_controller(self):
        """Disconnect stem controller."""
        if self.controller:
            try:
                self.controller.close()
            except Exception:
                pass
            self.controller = None

    def _start_system_tor(self) -> bool:
        """Try starting Tor via system service."""
        try:
            subprocess.run(["sudo", "systemctl", "start", TOR_SERVICE],
                          capture_output=True, timeout=10)
            time.sleep(3)
            return self._is_control_port_open()
        except Exception:
            return False

    def _spawn_tor_process(self, timeout: int = 30) -> bool:
        """Spawn our own Tor process with temporary config."""
        Path(TOR_DATA_DIR).mkdir(parents=True, exist_ok=True)
        config_path = os.path.join(TOR_DATA_DIR, "torrc")
        with open(config_path, "w") as f:
            f.write(TOR_CONFIG)

        logger.info("Spawning temporary Tor process...")
        try:
            self.tor_process = subprocess.Popen(
                [TOR_BINARY, "-f", config_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
        except FileNotFoundError:
            logger.error(f"Tor binary not found at {TOR_BINARY}. Install with: sudo apt install tor")
            return False

        # Wait for control port to open
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._is_control_port_open():
                logger.info("Spawned Tor process is ready")
                return self._connect_controller()
            time.sleep(1)

        logger.error("Timeout waiting for spawned Tor process")
        return False


# ── Singleton ────────────────────────────────────────────────────────────
_tor_instance: Optional[TorManager] = None


def get_tor() -> TorManager:
    global _tor_instance
    if _tor_instance is None:
        _tor_instance = TorManager()
    return _tor_instance


# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tor = get_tor()
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "start":
        ok = tor.start()
        print(f"Tor started: {ok}")
        if ok:
            exit_ip = tor.get_current_exit_node()
            print(f"Exit node IP: {exit_ip}")

    elif action == "stop":
        tor.stop()
        print("Tor stopped")

    elif action == "newid":
        ok = tor.new_identity()
        print(f"New identity: {ok}")

    elif action == "status":
        connected = tor.is_connected()
        print(f"Tor connected: {connected}")
        if connected:
            print(f"SOCKS5 proxy: {tor.get_proxy_url()}")
            exit_ip = tor.get_current_exit_node()
            print(f"Exit node IP: {exit_ip}")

    else:
        print(f"Usage: {sys.argv[0]} [start|stop|newid|status]")
