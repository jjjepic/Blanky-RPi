"""Thread-safe diagnostics for actual OpenAI requests, without probe traffic."""

import threading
import time
from contextlib import contextmanager

_lock = threading.Lock()
_active = 0
_last_result = None


@contextmanager
def measure_request(operation: str):
    global _active, _last_result
    started = time.perf_counter()
    with _lock:
        _active += 1
    try:
        yield
    except Exception:
        with _lock:
            _last_result = {"operation": operation, "ok": False, "ms": round((time.perf_counter() - started) * 1000)}
        raise
    else:
        with _lock:
            _last_result = {"operation": operation, "ok": True, "ms": round((time.perf_counter() - started) * 1000)}
    finally:
        with _lock:
            _active -= 1


def activity_snapshot() -> dict:
    with _lock:
        return {"active": _active, "last": dict(_last_result) if _last_result else None}
