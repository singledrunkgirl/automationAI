#!/usr/bin/env python3
"""
Playwright + OpenCLAW Browser Automation for HackWithAI.
Headless browser testing, form filling, XSS detection, anti-bot bypass.
Proxy support (HTTP, SOCKS5, Tor). .onion scraping integration.
"""

import os, sys, json, time, base64, subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse

OUTPUT_DIR = Path("/home/kali/HackWithAI/data/scans/browser")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class BrowserAutomation:
    """Playwright-based browser automation with anti-detection."""

    def __init__(self, headless: bool = True, proxy: str = ""):
        self.headless = headless
        self.proxy = proxy
        self.browser = None
        self.context = None
        self.page = None
        self._playwright = None

    def _get_playwright(self):
        if self._playwright is None:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
        return self._playwright

    def launch(self) -> bool:
        try:
            pw = self._get_playwright()
            launch_args = {
                "headless": self.headless,
                "args": [
                    "--no-sandbox", "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                ]
            }
            if self.proxy:
                launch_args["proxy"] = {"server": self.proxy}
            self.browser = pw.chromium.launch(**launch_args)
            self.context = self.browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            )
            self.page = self.context.new_page()
            # Anti-detection script
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => false});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
                window.chrome = {runtime: {}};
            """)
            return True
        except Exception as e:
            print(f"[Browser] Launch failed: {e}")
            return False

    def navigate(self, url: str) -> Dict:
        try:
            self.page.goto(url, wait_until="networkidle", timeout=30000)
            return {"ok": True, "url": self.page.url, "title": self.page.title()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def fill_form(self, fields: Dict[str, str], submit_selector: str = "") -> Dict:
        results = {}
        for selector, value in fields.items():
            try:
                self.page.fill(selector, value)
                results[selector] = "filled"
            except Exception as e:
                results[selector] = f"error: {e}"
        if submit_selector:
            try:
                self.page.click(submit_selector)
                self.page.wait_for_load_state("networkidle", timeout=10000)
                results["_submitted"] = True
            except Exception as e:
                results["_submitted"] = str(e)
        return results

    def extract_text(self, selector: str = "body") -> str:
        try:
            return self.page.text_content(selector)
        except Exception:
            return ""

    def extract_links(self) -> List[str]:
        try:
            return self.page.evaluate("""
                Array.from(document.querySelectorAll('a[href]')).map(a => a.href)
            """)
        except Exception:
            return []

    def extract_forms(self) -> List[Dict]:
        try:
            return self.page.evaluate("""
                Array.from(document.querySelectorAll('form')).map(form => ({
                    action: form.action,
                    method: form.method,
                    inputs: Array.from(form.querySelectorAll('input,textarea,select')).map(inp => ({
                        name: inp.name, type: inp.type || inp.tagName.toLowerCase(),
                        placeholder: inp.placeholder
                    }))
                }))
            """)
        except Exception:
            return []

    def screenshot(self, filename: str = "") -> str:
        path = filename or str(OUTPUT_DIR / f"screenshot_{int(time.time())}.png")
        self.page.screenshot(path=path, full_page=True)
        return path

    def execute_js(self, script: str) -> str:
        try:
            return str(self.page.evaluate(script))
        except Exception as e:
            return f"JS Error: {e}"

    def detect_xss(self, url: str, param: str = "q", payloads: List[str] = []) -> Dict:
        """Test a URL parameter for XSS vulnerability."""
        if not payloads:
            payloads = [
                "<script>alert(1)</script>",
                "\"><script>alert(1)</script>",
                "'><img src=x onerror=alert(1)>",
                "<svg onload=alert(1)>",
            ]
        results = {"url": url, "parameter": param, "tests": []}
        for payload in payloads:
            test_url = url.replace(f"{param}=", f"{param}={payload}")
            try:
                self.page.goto(test_url, wait_until="domcontentloaded", timeout=10000)
                dialog_appeared = False
                def handle_dialog(dialog):
                    nonlocal dialog_appeared
                    dialog_appeared = True
                    dialog.dismiss()
                self.page.on("dialog", handle_dialog)
                self.page.wait_for_timeout(2000)
                results["tests"].append({"payload": payload, "alert_triggered": dialog_appeared})
            except Exception:
                results["tests"].append({"payload": payload, "alert_triggered": False})
        return results

    def brute_force_login(self, url: str, user_field: str, pass_field: str,
                          submit_btn: str, users: List[str], passwords: List[str],
                          failure_indicator: str = "") -> List[Dict]:
        """Attempt login brute force via browser."""
        results = []
        for user in users[:20]:
            for pwd in passwords[:20]:
                try:
                    self.page.goto(url, wait_until="domcontentloaded")
                    self.page.fill(user_field, user)
                    self.page.fill(pass_field, pwd)
                    self.page.click(submit_btn)
                    self.page.wait_for_load_state("networkidle", timeout=10000)
                    success = failure_indicator not in self.page.content() if failure_indicator else self.page.url != url
                    results.append({"user": user, "password": pwd, "success": success})
                    if success:
                        return results  # Stop on first success
                except Exception:
                    results.append({"user": user, "password": pwd, "success": False})
        return results

    def close(self):
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self._playwright:
            self._playwright.stop()


class WebCrawler:
    """Deep web crawler with OpenCLAW-style metadata extraction."""

    def __init__(self, browser: BrowserAutomation):
        self.browser = browser
        self.visited: set = set()
        self.results: List[Dict] = []

    def crawl(self, start_url: str, depth: int = 2, max_pages: int = 50) -> List[Dict]:
        self._crawl_recursive(start_url, depth, max_pages)
        return self.results

    def _crawl_recursive(self, url: str, depth: int, max_pages: int):
        if depth < 0 or url in self.visited or len(self.results) >= max_pages:
            return
        self.visited.add(url)
        nav = self.browser.navigate(url)
        if not nav.get("ok"):
            return
        metadata = {
            "url": url,
            "title": self.browser.page.title() if self.browser.page else "",
            "links": [],
            "forms": self.browser.extract_forms(),
            "screenshot": self.browser.screenshot(),
        }
        links = self.browser.extract_links()
        metadata["links"] = links[:50]
        self.results.append(metadata)
        if depth > 0:
            for link in links[:10]:
                self._crawl_recursive(link, depth - 1, max_pages)

    def export(self, filename: str = "") -> str:
        path = filename or str(OUTPUT_DIR / f"crawl_{int(time.time())}.json")
        with open(path, "w") as f:
            json.dump(self.results, f, indent=2)
        return path


# ── CLI ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "navigate":
        ba = BrowserAutomation(headless=True)
        if ba.launch():
            result = ba.navigate(sys.argv[2])
            print(json.dumps(result, indent=2))
            if result.get("ok"):
                print(f"Links: {len(ba.extract_links())}")
                print(f"Forms: {len(ba.extract_forms())}")
            ba.close()

    elif cmd == "screenshot":
        ba = BrowserAutomation(headless=True)
        if ba.launch():
            ba.navigate(sys.argv[2])
            path = ba.screenshot()
            print(f"Screenshot: {path}")
            ba.close()

    elif cmd == "xss":
        ba = BrowserAutomation(headless=True)
        if ba.launch():
            result = ba.detect_xss(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "q")
            print(json.dumps(result, indent=2))
            ba.close()

    elif cmd == "crawl":
        ba = BrowserAutomation(headless=True)
        if ba.launch():
            crawler = WebCrawler(ba)
            results = crawler.crawl(sys.argv[2], depth=int(sys.argv[3]) if len(sys.argv) > 3 else 1)
            path = crawler.export()
            print(f"Crawled {len(results)} pages → {path}")
            ba.close()

    elif cmd == "forms":
        ba = BrowserAutomation(headless=True)
        if ba.launch():
            ba.navigate(sys.argv[2])
            forms = ba.extract_forms()
            print(json.dumps(forms, indent=2))
            ba.close()

    else:
        print("Commands:")
        print("  navigate <url>          Navigate and extract metadata")
        print("  screenshot <url>        Take full-page screenshot")
        print("  xss <url> [param]       Test for XSS vulnerabilities")
        print("  crawl <url> [depth]     Deep crawl with metadata extraction")
        print("  forms <url>             Extract all forms from page")
