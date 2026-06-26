#!/usr/bin/env python3
"""
Message Bus — Agent-to-agent communication with pub/sub, broadcast, and persistence.
"""

import json, time, threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable, Set
from collections import defaultdict

LOG_DIR = Path("/home/kali/HackWithAI/data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


class MessageBus:
    """Pub/sub message bus for agent-to-agent communication."""

    def __init__(self):
        self.subscribers: Dict[str, Set[Callable]] = defaultdict(set)
        self.message_history: List[Dict] = []
        self.lock = threading.Lock()

    def subscribe(self, topic: str, callback: Callable):
        with self.lock:
            self.subscribers[topic].add(callback)

    def unsubscribe(self, topic: str, callback: Callable):
        with self.lock:
            self.subscribers[topic].discard(callback)

    def publish(self, topic: str, sender: str, content: Dict) -> int:
        """Publish a message. Returns number of subscribers notified."""
        message = {
            "topic": topic,
            "sender": sender,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        with self.lock:
            self.message_history.append(message)
            listeners = self.subscribers.get(topic, set()) | self.subscribers.get("*", set())

        for callback in listeners:
            try:
                callback(message)
            except Exception:
                pass
        return len(listeners)

    def broadcast(self, sender: str, content: Dict) -> int:
        """Broadcast to ALL topics."""
        return self.publish("*", sender, content)

    def get_history(self, topic: str = "", limit: int = 100) -> List[Dict]:
        if topic:
            return [m for m in self.message_history[-limit:] if m["topic"] == topic]
        return self.message_history[-limit:]

    def get_conversation(self, session_id: str) -> List[Dict]:
        return [m for m in self.message_history if m.get("content", {}).get("session_id") == session_id]

    def persist(self, path: str = ""):
        path = path or str(LOG_DIR / "message_bus.json")
        with open(path, "w") as f:
            json.dump(self.message_history[-5000:], f, indent=2, default=str)

    def stats(self) -> Dict:
        return {
            "total_messages": len(self.message_history),
            "topics": list(self.subscribers.keys()),
            "subscriber_count": sum(len(v) for v in self.subscribers.values()),
        }


# ── Singleton ──────────────────────────────────────────────────────────
_bus: Optional[MessageBus] = None

def get_message_bus() -> MessageBus:
    global _bus
    if _bus is None:
        _bus = MessageBus()
    return _bus
