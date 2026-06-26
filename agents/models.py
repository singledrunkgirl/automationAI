#!/usr/bin/env python3
"""AI Model Abstraction — Remote via OpenRouter/OpenAI, local via Ollama."""

import os, json, subprocess, time, logging
from typing import Optional, Dict, List
from abc import ABC, abstractmethod

# Load .env at module level
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="[model] %(message)s")
logger = logging.getLogger("agent_models")


class BaseModel(ABC):
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        raise NotImplementedError

    @abstractmethod
    def available(self) -> bool:
        raise NotImplementedError


class OllamaModel(BaseModel):
    """Local Ollama model."""
    def __init__(self, model_name: str = "deepseek-coder:6.7b"):
        self.model = model_name

    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        try:
            r = subprocess.run(
                ["ollama", "run", self.model, prompt],
                capture_output=True, text=True, timeout=120
            )
            return r.stdout.strip() if r.returncode == 0 else (r.stderr or "Ollama error")
        except Exception as e:
            return f"Ollama error: {e}"

    def available(self) -> bool:
        try:
            r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
            return self.model in r.stdout
        except Exception:
            return False


class OpenRouterModel(BaseModel):
    """OpenRouter API model (DeepSeek, Claude, Gemini, etc.) with optional Tor SOCKS5 routing."""
    def __init__(self, model_id: str = "deepseek/deepseek-v4-pro"):
        self.model_id = model_id
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.proxies = None

    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        if not self.api_key:
            return "[OpenRouter: no API key]"
        try:
            import urllib.request
            body = json.dumps({
                "model": self.model_id,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }).encode()
            req = urllib.request.Request(
                self.base_url,
                data=body,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": os.environ.get("HTTP_REFERER", "https://github.com/HackWithAI"),
                    "X-Title": os.environ.get("X_TITLE", "HackWithAI v2"),
                }
            )
            resp = urllib.request.urlopen(req, timeout=60)
            data = json.loads(resp.read())
            return data.get("choices", [{}])[0].get("message", {}).get("content", "[No response]")
        except urllib.request.HTTPError as e:
            err_body = e.read().decode(errors="replace")[:300]
            return f"[OpenRouter error: HTTP {e.code} - {err_body}]"
        except Exception as e:
            return f"[OpenRouter error: {e}]"

    def available(self) -> bool:
        return bool(self.api_key)


class RuleBasedModel(BaseModel):
    """Simple pattern-matching fallback when models are offline."""
    def __init__(self, role: str = "general"):
        self.role = role

    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
        responses = {
            "http": "Try: GET /, OPTIONS /, HEAD /, TRACE /, PUT /test.txt, DELETE /admin",
            "sql": "Test: ' OR 1=1--, ' UNION SELECT NULL--, ' AND SLEEP(5)--, ' WAITFOR DELAY '0:0:5'--",
            "xss": "Test: <script>alert(1)</script>, <img src=x onerror=alert(1)>, javascript:alert(1)",
            "port": "Common ports: 21(FTP), 22(SSH), 23(Telnet), 25(SMTP), 53(DNS), 80(HTTP), 443(HTTPS), 445(SMB), 3306(MySQL), 3389(RDP), 5432(PostgreSQL), 8080(HTTP-Alt), 8443(HTTPS-Alt)",
        }
        for key, val in responses.items():
            if key in prompt.lower():
                return val
        return f"[RuleBased] '{prompt}' — no matching rule. Try: HTTP, SQL, XSS, or port scanning."

    def available(self) -> bool:
        return True


def create_model(model_type: str = "openrouter", model_name: str = None) -> BaseModel:
    """Factory: returns the appropriate model instance."""
    if model_type == "openrouter":
        key = model_name or os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-v4-pro")
        return OpenRouterModel(key)
    elif model_type == "ollama":
        return OllamaModel(model_name or "deepseek-coder:6.7b")
    elif model_type == "auto" and os.environ.get("OPENROUTER_API_KEY"):
        key = model_name or os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-v4-pro")
        return OpenRouterModel(key)
    else:
        return RuleBasedModel()
