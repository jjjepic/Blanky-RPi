"""Bounded in-memory interpretation diagnostics for voice and Text-Bot."""

from collections import deque
from datetime import datetime
from threading import Lock


_entries = deque(maxlen=200)
_lock = Lock()


def record_interpretation(text: str, items: list[dict], mode: str):
    entry = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "mode": mode,
        "text": (text or "")[:1000],
        "items": [dict(item) for item in items],
    }
    with _lock:
        _entries.append(entry)


def interpretation_snapshot() -> list[dict]:
    with _lock:
        return [{**entry, "items": [dict(item) for item in entry["items"]]} for entry in _entries]
