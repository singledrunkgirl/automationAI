#!/usr/bin/env python3
"""
Network Recon Module — nmap + responder automation for authorized testing.
Provides programmatic wrappers around standard network reconnaissance tools
with structured JSON output for the HackWithAI pipeline.
"""
import json, os, subprocess, re, tempfile, time
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

LOG_DIR = Path(__file__).resolve().parent.parent / "data" / "logs" / "recon"
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ── Nmap Wrapper ──────────────────────────────────────────────────────────
class NmapScanner:
    """Programmatic nmap interface with structured output."""

    @staticmethod
    def quick_scan(target: str, ports: str = "top-1000") -> dict:
        """Fast TCP SYN scan of top ports."""
        return NmapScanner._run(["nmap", "-sS", "-T4", "--top-ports", ports, "-oX", "-", target])

    @staticmethod
    def full_scan(target: str, ports: str = "1-65535") -> dict:
        """Full port scan with service detection."""
        return NmapScanner._run(["nmap", "-sS", "-sV", "-O", "-T4", "-p", ports, "-oX", "-", target])

    @staticmethod
    def vuln_scan(target: str) -> dict:
        """Run NSE vulnerability scripts."""
        return NmapScanner._run(["nmap", "-sV", "--script", "vuln", "-T4", "-oX", "-", target])

    @staticmethod
    def stealth_scan(target: str, ports: str = "top-100") -> dict:
        """Stealth scan with fragmentation and decoy."""
        return NmapScanner._run([
            "nmap", "-sS", "-Pn", "-T2", "-f", "--data-length", "24",
            "-D", "RND:5", "--top-ports", ports, "-oX", "-", target
        ])

    @staticmethod
    def _run(args: list) -> dict:
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=120)
            xml = result.stdout or result.stderr
            return NmapScanner._parse_xml(xml)
        except subprocess.TimeoutExpired:
            return {"error": "Scan timed out", "target": args[-1] if args else ""}
        except FileNotFoundError:
            return {"error": "nmap not installed", "target": args[-1] if args else ""}

    @staticmethod
    def _parse_xml(xml: str) -> dict:
        """Basic XML parser for nmap output — extracts hosts, ports, services."""
        hosts = []
        host_blocks = re.findall(r'<host[^>]*>(.*?)</host>', xml, re.DOTALL)

        for block in host_blocks:
            addr_match = re.search(r'<address[^>]*addr="([^"]+)"', block)
            if not addr_match:
                continue
            ip = addr_match.group(1)

            ports = []
            port_blocks = re.findall(r'<port[^>]*>(.*?)</port>', block, re.DOTALL)
            for pb in port_blocks:
                pid = re.search(r'portid="(\d+)"', pb)
                proto = re.search(r'protocol="(\w+)"', pb)
                state = re.search(r'<state[^>]*state="(\w+)"', pb)
                svc = re.search(r'<service[^>]*name="([^"]*)"', pb)
                product = re.search(r'product="([^"]*)"', pb)
                version = re.search(r'version="([^"]*)"', pb)

                if state and state.group(1) == "open":
                    ports.append({
                        "port": int(pid.group(1)) if pid else 0,
                        "protocol": proto.group(1) if proto else "",
                        "service": svc.group(1) if svc else "",
                        "product": f"{product.group(1)} {version.group(1)}".strip() if product else "",
                    })

            os_match = re.search(r'<osmatch[^>]*name="([^"]+)"', block)
            hosts.append({
                "ip": ip,
                "open_ports": ports,
                "port_count": len(ports),
                "os_guess": os_match.group(1) if os_match else "unknown",
            })

        return {
            "scanner": "nmap",
            "hosts": hosts,
            "total_hosts": len(hosts),
            "total_open_ports": sum(h["port_count"] for h in hosts),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ── Responder Wrapper ─────────────────────────────────────────────────────
class ResponderEngine:
    """Programmatic control over Responder for LLMNR/NBT-NS/mDNS poisoning."""

    @staticmethod
    def start(interface: str = "eth0", analyze_mode: bool = True) -> subprocess.Popen:
        """Start Responder in analyze mode (passive) or active mode."""
        args = ["responder", "-I", interface]
        if analyze_mode:
            args.append("-A")  # Analyze mode — no poisoning, just listen
        return subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

    @staticmethod
    def parse_log(log_path: str = "/usr/share/responder/logs") -> dict:
        """Parse Responder log files for captured hashes."""
        hashes = []
        log_dir = Path(log_path)
        if not log_dir.exists():
            return {"hashes": [], "error": "Log dir not found"}

        for session_file in log_dir.glob("*-NTLM*"):
            content = session_file.read_text(errors="ignore")
            # Extract NTLMv2 hashes
            for line in content.split("\n"):
                if "::" in line and len(line) > 50:
                    hashes.append({"type": "NTLMv2", "hash": line.strip()[:200]})

        return {
            "hashes": hashes,
            "count": len(hashes),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ── Unified Recon Runner ──────────────────────────────────────────────────
class ReconRunner:
    """Runs multiple recon tools and aggregates results."""

    def __init__(self, target: str):
        self.target = target
        self.results = {}
        self.nmap = NmapScanner()

    def run_all(self) -> dict:
        """Execute full recon suite."""
        print(f"[Recon] Starting full recon on {self.target}")

        # Phase 1: Quick port scan
        print("  [1/4] Quick nmap scan...")
        self.results["quick_scan"] = self.nmap.quick_scan(self.target)

        open_ports = sum(h["port_count"] for h in self.results["quick_scan"].get("hosts", []))
        print(f"  → {open_ports} open ports found")

        # Phase 2: Service detection on discovered ports
        if open_ports > 0:
            print("  [2/4] Service detection...")
            self.results["service_scan"] = self.nmap.full_scan(self.target)
        else:
            self.results["service_scan"] = {"info": "No open ports — skipping"}

        # Phase 3: Vulnerability scripts
        web_ports = self._find_web_ports()
        if web_ports:
            print(f"  [3/4] Vulnerability scan (web ports: {web_ports})...")
            self.results["vuln_scan"] = self.nmap.vuln_scan(self.target)
        else:
            self.results["vuln_scan"] = {"info": "No web ports — skipping vuln scan"}

        # Phase 4: Save report
        print("  [4/4] Saving report...")
        report_path = self._save_report()

        self.results["summary"] = {
            "target": self.target,
            "open_ports": open_ports,
            "web_services": web_ports,
            "report": str(report_path),
        }

        return self.results

    def _find_web_ports(self) -> list:
        ports = []
        for host in self.results.get("quick_scan", {}).get("hosts", []):
            for p in host.get("open_ports", []):
                if p["service"] in ("http", "https", "http-proxy", "ssl/http"):
                    ports.append({"host": host["ip"], "port": p["port"], "ssl": p["port"] == 443})
        return ports

    def _save_report(self) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_target = self.target.replace("/", "_").replace(":", "_")
        path = LOG_DIR / f"recon_{safe_target}_{ts}.json"
        path.write_text(json.dumps(self.results, indent=2, default=str))
        return path


SYSTEM_RECON_DIR = Path(__file__).resolve().parent.parent / ".system" / "recon_xml"
SYSTEM_RECON_DIR.mkdir(parents=True, exist_ok=True)


def trigger_stealth_scan(target_ip: str) -> dict:
    """Standalone function: T4 stealth nmap scan, save XML to .system/recon_xml/."""
    args = [
        "nmap", "-sS", "-Pn", "-T4", "--max-retries", "1",
        "--min-rate", "100", "--max-rate", "300",
        "-f", "--data-length", "16",
        "-p", "1-1000",
        "--randomize-hosts",
        "-oA", str(SYSTEM_RECON_DIR / f"stealth_{target_ip.replace('.','_')}_{int(time.time())}"),
        target_ip,
    ]
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=300)
        # Find the generated XML
        xml_files = sorted(SYSTEM_RECON_DIR.glob("stealth_*.xml"), key=lambda p: p.stat().st_mtime, reverse=True)
        xml_path = str(xml_files[0]) if xml_files else ""
        return {
            "target": target_ip,
            "xml_path": xml_path,
            "raw_summary": result.stdout[:2000] if result.stdout else result.stderr[:2000],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "files": [str(f) for f in xml_files[:3]],
        }
    except FileNotFoundError:
        return {"error": "nmap not installed", "target": target_ip}
    except subprocess.TimeoutExpired:
        return {"error": "Scan timed out (5 min limit)", "target": target_ip}

# ── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 core/network_recon.py <target_ip_or_range>")
        sys.exit(1)

    target = sys.argv[1]
    runner = ReconRunner(target)
    results = runner.run_all()

    summary = results.get("summary", {})
    print(f"\n[Recon] Done. {summary.get('open_ports',0)} ports open, "
          f"{len(summary.get('web_services',[]))} web services")
    print(f"Report: {summary.get('report')}")
