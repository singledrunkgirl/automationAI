#!/usr/bin/env python3
"""
Dark Web Tools for HackWithAI v2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Modules:
  - OnionScraper      → Scrape .onion websites via Tor SOCKS5 proxy
  - DarkWebSearch     → Ahmia.fi, Torch, DuckDuckGo dark web search
  - LeakedCredsChecker→ HIBP, Dehashed API, local breach DB
  - CryptoScanner     → Bitcoin/Monero address scanner, blockchain explorer
  - DarkWebMonitor    → Track dark web markets for new listings

Usage:
  python darkweb_tools.py scrape <onion_url>
  python darkweb_tools.py search <query>
  python darkweb_tools.py check-leaks <email|username>
  python darkweb_tools.py scan-crypto <btc_address>
  python darkweb_tools.py monitor [--daemon]
"""

import os
import re
import sys
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from urllib.parse import urlparse, quote_plus

import requests
from bs4 import BeautifulSoup

try:
    from .tor_manager import TorManager, get_tor
except ImportError:
    from tor_manager import TorManager, get_tor

logging.basicConfig(level=logging.INFO, format="[darkweb] %(message)s")
logger = logging.getLogger("darkweb")

DATA_DIR = Path("/home/kali/HackWithAI/data/darkweb")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Constants ──────────────────────────────────────────────────────────────
AHMIA_API = "https://ahmia.fi/search/?q={query}"
AHMIA_ONION = "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion"
TORCH_ONION = "http://torchdeedp3i2jigzjdmfpn5ttjhthh5wbmda2rr3jvqjg5p77c54dqd.onion"
DUCKDUCKGO_ONION = "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion"
HIBP_API = "https://haveibeenpwned.com/api/v3/breachedaccount/{account}"
HIBP_PASTE_API = "https://haveibeenpwned.com/api/v3/pasteaccount/{account}"
BLOCKCHAIN_API = "https://blockchain.info/rawaddr/{address}"
BLOCKCHAIR_API = "https://api.blockchair.com/bitcoin/dashboards/address/{address}"
MONERO_BLOCKS_API = "https://localmonero.co/blocks/api"

# ── User agent rotations ────────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.2 Safari/605.1.15",
]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ONION SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════

class OnionScraper:
    """
    Scrape .onion websites through Tor SOCKS5 proxy.
    Extracts emails, credentials, cryptocurrency addresses, and links.
    """

    def __init__(self, tor: TorManager):
        self.tor = tor
        self.session = self._create_session()
        self.results_dir = DATA_DIR / "scraped"
        self.results_dir.mkdir(exist_ok=True)

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        proxy_url = self.tor.get_proxy_url()
        session.proxies = {"http": proxy_url, "https": proxy_url}
        session.headers.update({"User-Agent": USER_AGENTS[0]})
        return session

    def scrape(self, url: str, depth: int = 1, extract_files: bool = True) -> Dict[str, Any]:
        """
        Scrape an .onion URL and extract intelligence.

        Args:
            url: The .onion URL to scrape
            depth: Recursion depth for link following (default 1)
            extract_files: Whether to download linked files (default True)

        Returns:
            Dict with scraped data: emails, credentials, crypto addresses, links, files
        """
        logger.info(f"Scraping: {url} (depth={depth})")
        visited = set()
        all_results = {
            "url": url,
            "timestamp": datetime.utcnow().isoformat(),
            "emails": [],
            "credentials": [],
            "crypto_addresses": [],
            "links": [],
            "onion_links": [],
            "forms": [],
            "raw_pages": [],
        }

        self._scrape_recursive(url, depth, visited, all_results)

        # Deduplicate
        for key in ["emails", "credentials", "crypto_addresses", "links", "onion_links"]:
            all_results[key] = list(set(all_results[key]))

        # Save results
        domain = urlparse(url).netloc.replace(".onion", "")
        out_file = self.results_dir / f"{domain}_{int(time.time())}.json"
        with open(out_file, "w") as f:
            json.dump(all_results, f, indent=2)

        logger.info(f"Saved {len(all_results['emails'])} emails, "
                    f"{len(all_results['credentials'])} creds, "
                    f"{len(all_results['onion_links'])} onion links → {out_file}")
        return all_results

    def _scrape_recursive(self, url: str, depth: int, visited: set, results: Dict):
        if depth < 0 or url in visited:
            return
        visited.add(url)

        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return

        html = resp.text
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text()

        results["raw_pages"].append({"url": url, "title": soup.title.string if soup.title else "", "size": len(html)})

        # Extract emails
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        results["emails"].extend(emails)

        # Extract credentials (username:password patterns in text/forms)
        creds = re.findall(r"(?:user(?:name)?|login|email)[\s:]*[\"']?([^\"'\s]+)[\"']?[\s,]*"
                          r"(?:pass(?:word)?|pwd)[\s:]*[\"']?([^\"'\s]+)", text, re.IGNORECASE)
        results["credentials"].extend([f"{u}:{p}" for u, p in creds])

        # Also check form inputs for login forms
        for form in soup.find_all("form"):
            inputs = {inp.get("name", ""): inp.get("type", "text")
                     for inp in form.find_all("input") if inp.get("name")}
            if any(k.lower() in ("user", "username", "login", "email") for k in inputs):
                results["forms"].append({
                    "action": form.get("action", ""),
                    "method": form.get("method", "GET"),
                    "fields": list(inputs.keys()),
                })

        # Extract cryptocurrency addresses
        btc_addrs = re.findall(r"[13][a-km-zA-HJ-NP-Z1-9]{25,34}", text)
        eth_addrs = re.findall(r"0x[a-fA-F0-9]{40}", text)
        xmr_addrs = re.findall(r"[48][0-9AB][1-9A-HJ-NP-Za-km-z]{93}", text)
        results["crypto_addresses"].extend(btc_addrs + eth_addrs + xmr_addrs)

        # Extract links
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith("http"):
                results["links"].append(href)
                if ".onion" in href:
                    results["onion_links"].append(href)

        # Recurse
        if depth > 0:
            for onion_link in results["onion_links"]:
                self._scrape_recursive(onion_link, depth - 1, visited, results)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DARK WEB SEARCH
# ═══════════════════════════════════════════════════════════════════════════════

class DarkWebSearch:
    """Search dark web via Ahmia.fi, Torch, and DuckDuckGo .onion."""

    def __init__(self, tor: TorManager):
        self.tor = tor

    def search_ahmia(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search Ahmia.fi (clearnet + .onion)."""
        results = []
        try:
            url = AHMIA_API.format(query=quote_plus(query))
            resp = requests.get(url, timeout=20, headers={"User-Agent": USER_AGENTS[0]})
            soup = BeautifulSoup(resp.text, "html.parser")

            for result in soup.select(".result"):
                title_el = result.select_one("h4 a, .title a")
                desc_el = result.select_one("p, .description")
                link = title_el.get("href", "") if title_el else ""
                results.append({
                    "title": title_el.get_text(strip=True) if title_el else "",
                    "url": link,
                    "description": desc_el.get_text(strip=True) if desc_el else "",
                    "source": "ahmia",
                })
                if len(results) >= max_results:
                    break
        except Exception as e:
            logger.warning(f"Ahmia search failed: {e}")
        return results

    def search_torch(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search Torch search engine (.onion). Requires Tor."""
        results = []
        try:
            session = requests.Session()
            session.proxies = self.tor.get_proxy_dict()
            session.headers.update({"User-Agent": USER_AGENTS[0]})

            resp = session.get(TORCH_ONION, params={"q": query}, timeout=30)
            soup = BeautifulSoup(resp.text, "html.parser")

            for result in soup.select("dl dt a, .result a"):
                title = result.get_text(strip=True)
                link = result.get("href", "")
                results.append({"title": title, "url": link, "source": "torch"})
                if len(results) >= max_results:
                    break
        except Exception as e:
            logger.warning(f"Torch search failed: {e}")
        return results

    def search_duckduckgo_onion(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search DuckDuckGo via its .onion address."""
        results = []
        try:
            session = requests.Session()
            session.proxies = self.tor.get_proxy_dict()
            session.headers.update({"User-Agent": USER_AGENTS[0]})

            resp = session.get(DUCKDUCKGO_ONION, params={"q": query, "ia": "web"}, timeout=30)
            soup = BeautifulSoup(resp.text, "html.parser")

            for result in soup.select(".result__body, .result"):
                title_el = result.select_one(".result__title, .result__a")
                desc_el = result.select_one(".result__snippet")
                link = title_el.get("href", "") if title_el else ""
                results.append({
                    "title": title_el.get_text(strip=True) if title_el else "",
                    "url": link,
                    "description": desc_el.get_text(strip=True) if desc_el else "",
                    "source": "duckduckgo-onion",
                })
                if len(results) >= max_results:
                    break
        except Exception as e:
            logger.warning(f"DuckDuckGo .onion search failed: {e}")
        return results

    def search_all(self, query: str) -> Dict[str, List]:
        """Run all search engines and combine results."""
        return {
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "ahmia": self.search_ahmia(query),
            "torch": self.search_torch(query),
            "duckduckgo_onion": self.search_duckduckgo_onion(query),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 3. LEAKED CREDENTIALS CHECKER
# ═══════════════════════════════════════════════════════════════════════════════

class LeakedCredsChecker:
    """
    Check if credentials have been exposed in data breaches.
    Sources: HaveIBeenPwned, Dehashed (optional), local breach database.
    """

    def __init__(self, dehashed_email: str = "", dehashed_api_key: str = ""):
        self.dehashed_email = dehashed_email
        self.dehashed_key = dehashed_api_key
        self.breach_db_path = DATA_DIR / "breaches"

    def check_hibp(self, account: str, check_pastes: bool = True) -> Dict:
        """
        Check HaveIBeenPwned for breached accounts.
        Uses k-anonymity (first 5 chars of SHA-1 hash).
        """
        import hashlib

        sha1 = hashlib.sha1(account.encode()).hexdigest().upper()
        prefix = sha1[:5]
        suffix = sha1[5:]

        result = {
            "account": account,
            "breached": False,
            "breaches": [],
            "pastes": [],
        }

        try:
            resp = requests.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                headers={"User-Agent": "HackWithAI-v2"},
                timeout=10,
            )
            if resp.status_code != 200:
                return result

            for line in resp.text.splitlines():
                hash_suffix, count = line.split(":")
                if hash_suffix == suffix:
                    result["breached"] = True
                    result["pwned_count"] = int(count)
                    break

        except Exception as e:
            logger.warning(f"HIBP check failed: {e}")

        # Check named breaches
        if result["breached"] or True:  # Always check named breaches
            try:
                resp = requests.get(
                    HIBP_API.format(account=quote_plus(account)),
                    headers={"hibp-api-key": ""},
                    timeout=10,
                )
                if resp.status_code == 200:
                    result["breaches"] = [b["Name"] for b in resp.json()]
                    result["breached"] = True
            except Exception:
                pass

        # Check pastes
        if check_pastes:
            try:
                resp = requests.get(
                    HIBP_PASTE_API.format(account=quote_plus(account)),
                    headers={"hibp-api-key": ""},
                    timeout=10,
                )
                if resp.status_code == 200:
                    result["pastes"] = resp.json()
            except Exception:
                pass

        return result

    def check_dehashed(self, query: str, query_type: str = "email") -> Dict:
        """Query Dehashed API for leaked credentials (requires API key)."""
        if not self.dehashed_key:
            return {"error": "Dehashed API key not configured"}

        try:
            resp = requests.get(
                "https://api.dehashed.com/search",
                params={"query": query},
                auth=(self.dehashed_email, self.dehashed_key),
                headers={"Accept": "application/json"},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                entries = data.get("entries", [])
                return {
                    "query": query,
                    "results": len(entries),
                    "entries": entries[:50],  # Limit to 50
                }
            return {"error": f"Status {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def search_local_breaches(self, keyword: str) -> List[Dict]:
        """Search local breach database files."""
        results = []
        if not self.breach_db_path.exists():
            return results

        for f in self.breach_db_path.glob("*.txt"):
            try:
                content = f.read_text(errors="ignore")
                if keyword.lower() in content.lower():
                    for line in content.splitlines():
                        if keyword.lower() in line.lower():
                            results.append({"file": str(f), "match": line.strip()[:200]})
                            if len(results) >= 100:
                                return results
            except Exception:
                continue
        return results

    def full_check(self, target: str) -> Dict:
        """Run all credential checks for a target."""
        email = target if "@" in target else f"{target}@gmail.com"
        username = target.split("@")[0] if "@" in target else target

        return {
            "target": target,
            "timestamp": datetime.utcnow().isoformat(),
            "hibp": self.check_hibp(email),
            "local_breaches": self.search_local_breaches(username),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 4. CRYPTOCURRENCY SCANNER
# ═══════════════════════════════════════════════════════════════════════════════

class CryptoScanner:
    """Scan Bitcoin and Monero blockchain for address activity."""

    def scan_bitcoin_address(self, address: str) -> Dict:
        """Get Bitcoin address info from blockchain.info."""
        result = {"address": address, "found": False, "data": {}}

        # blockchain.info
        try:
            resp = requests.get(BLOCKCHAIN_API.format(address=address), timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                result["found"] = True
                result["data"] = {
                    "total_received": data.get("total_received", 0) / 1e8,
                    "total_sent": data.get("total_sent", 0) / 1e8,
                    "final_balance": data.get("final_balance", 0) / 1e8,
                    "n_tx": data.get("n_tx", 0),
                    "source": "blockchain.info",
                }
        except Exception as e:
            logger.warning(f"blockchain.info failed: {e}")

        # blockchair.com (backup)
        if not result["found"]:
            try:
                resp = requests.get(BLOCKCHAIR_API.format(address=address), timeout=15)
                if resp.status_code == 200:
                    data = resp.json().get("data", {}).get(address, {})
                    addr_data = data.get("address", {})
                    result["found"] = bool(data)
                    result["data"] = {
                        "total_received": addr_data.get("received", 0) / 1e8,
                        "total_sent": addr_data.get("spent", 0) / 1e8,
                        "balance": addr_data.get("balance", 0) / 1e8,
                        "n_tx": addr_data.get("transaction_count", 0),
                        "source": "blockchair.com",
                    }
            except Exception as e:
                logger.warning(f"blockchair.com failed: {e}")

        return result

    def scan_monero(self, address: str = "") -> Dict:
        """Get Monero network info (block height, difficulty)."""
        result = {"network": "monero", "address": address}
        try:
            resp = requests.get(MONERO_BLOCKS_API, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                result["block_height"] = data.get("height", 0)
                result["difficulty"] = data.get("difficulty", 0)
                result["hash_rate"] = data.get("hash_rate", 0)
        except Exception as e:
            logger.warning(f"Monero API failed: {e}")
        return result

    def scan_address(self, address: str) -> Dict:
        """Auto-detect cryptocurrency type and scan."""
        if re.match(r"[13][a-km-zA-HJ-NP-Z1-9]{25,34}", address):
            return self.scan_bitcoin_address(address)
        if re.match(r"0x[a-fA-F0-9]{40}", address):
            return {"type": "ethereum", "address": address, "note": "Use etherscan.io"}
        if re.match(r"[48][0-9AB][1-9A-HJ-NP-Za-km-z]{93}", address):
            return self.scan_monero(address)
        return {"error": f"Unknown address format: {address}"}


# ═══════════════════════════════════════════════════════════════════════════════
# 5. DARK WEB MARKET MONITOR
# ═══════════════════════════════════════════════════════════════════════════════

KNOWN_MARKETS = {
    # Add known market URLs here. These change frequently.
    # Format: "market_name": "onion_url"
}

class DarkWebMonitor:
    """
    Monitor dark web markets for new listings, products, and vendors.
    Stores snapshots in data/darkweb/monitor/.
    """

    def __init__(self, tor: TorManager):
        self.tor = tor
        self.monitor_dir = DATA_DIR / "monitor"
        self.monitor_dir.mkdir(exist_ok=True)
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.proxies = self.tor.get_proxy_dict()
        session.headers.update({"User-Agent": USER_AGENTS[0]})
        return session

    def add_market(self, name: str, url: str):
        """Register a market to monitor."""
        KNOWN_MARKETS[name] = url
        with open(self.monitor_dir / "markets.json", "w") as f:
            json.dump(KNOWN_MARKETS, f, indent=2)
        logger.info(f"Added market: {name} → {url}")

    def list_markets(self) -> Dict:
        """List all monitored markets."""
        return dict(KNOWN_MARKETS)

    def check_market(self, name: str) -> Optional[Dict]:
        """Check if a specific market is online and scrape its landing page."""
        url = KNOWN_MARKETS.get(name)
        if not url:
            return None

        try:
            resp = self.session.get(url, timeout=30)
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text()[:5000]

            snapshot = {
                "market": name,
                "url": url,
                "timestamp": datetime.utcnow().isoformat(),
                "online": resp.status_code == 200,
                "status_code": resp.status_code,
                "title": soup.title.string if soup.title else "",
                "text_preview": text,
            }

            # Save snapshot
            snap_file = self.monitor_dir / f"{name}_{int(time.time())}.json"
            with open(snap_file, "w") as f:
                json.dump(snapshot, f, indent=2)

            return snapshot

        except Exception as e:
            logger.warning(f"Market check failed for {name}: {e}")
            return {"market": name, "online": False, "error": str(e)}

    def check_all_markets(self) -> List[Dict]:
        """Check all monitored markets."""
        results = []
        for name in KNOWN_MARKETS:
            result = self.check_market(name)
            if result:
                results.append(result)
            time.sleep(2)  # Rate limit
        return results

    def compare_snapshots(self, name: str) -> List[str]:
        """Compare the two most recent snapshots and return new items."""
        snapshots = sorted(self.monitor_dir.glob(f"{name}_*.json"),
                          key=os.path.getmtime, reverse=True)
        if len(snapshots) < 2:
            return ["Need at least 2 snapshots to compare"]

        with open(snapshots[0]) as f:
            new = json.load(f)
        with open(snapshots[1]) as f:
            old = json.load(f)

        changes = []
        if new["online"] != old["online"]:
            changes.append(f"Status changed: {old['online']} → {new['online']}")
        if new.get("title") != old.get("title"):
            changes.append(f"Title changed: {old.get('title')} → {new.get('title')}")

        return changes


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    tor = get_tor()
    cmd = sys.argv[1]

    if cmd == "scrape":
        if len(sys.argv) < 3:
            print("Usage: darkweb_tools.py scrape <onion_url> [depth]")
            return
        if not tor.start():
            print("ERROR: Tor not available")
            return
        scraper = OnionScraper(tor)
        depth = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        result = scraper.scrape(sys.argv[2], depth=depth)
        print(json.dumps(result, indent=2))

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: darkweb_tools.py search <query>")
            return
        if not tor.start():
            print("ERROR: Tor not available")
            return
        searcher = DarkWebSearch(tor)
        result = searcher.search_all(" ".join(sys.argv[2:]))
        print(json.dumps(result, indent=2))

    elif cmd == "check-leaks":
        if len(sys.argv) < 3:
            print("Usage: darkweb_tools.py check-leaks <email|username>")
            return
        checker = LeakedCredsChecker()
        result = checker.full_check(sys.argv[2])
        print(json.dumps(result, indent=2))

    elif cmd == "scan-crypto":
        if len(sys.argv) < 3:
            print("Usage: darkweb_tools.py scan-crypto <address>")
            return
        scanner = CryptoScanner()
        result = scanner.scan_address(sys.argv[2])
        print(json.dumps(result, indent=2))

    elif cmd == "monitor":
        if not tor.start():
            print("ERROR: Tor not available")
            return
        monitor = DarkWebMonitor(tor)
        if len(sys.argv) > 2 and sys.argv[2] == "--add" and len(sys.argv) >= 5:
            monitor.add_market(sys.argv[3], sys.argv[4])
        elif len(sys.argv) > 2 and sys.argv[2] == "--list":
            print(json.dumps(monitor.list_markets(), indent=2))
        else:
            results = monitor.check_all_markets()
            print(json.dumps(results, indent=2))

    elif cmd == "tor-status":
        connected = tor.is_connected()
        print(f"Tor connected: {connected}")
        if connected:
            exit_ip = tor.get_current_exit_node()
            print(f"Exit IP: {exit_ip}")
            print(f"Proxy: {tor.get_proxy_url()}")

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
