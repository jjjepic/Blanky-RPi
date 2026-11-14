"""Non-blocking, single-owner speech synthesis and playback."""

import heapq
import logging
import os
import tempfile
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable


PRIORITY = {"informative": 10, "operational": 20, "requested": 30, "critical": 40}
_LOG = logging.getLogger(__name__)


@dataclass
class SpeechJob:
    text: str
    voice: str
    speed: float
    language: str
    priority: int
    generation: int
    sequence: int
    remember: bool = True
    localized: dict[str, str] = field(default_factory=dict)
    cancel: threading.Event = field(default_factory=threading.Event)
    created_at: float = field(default_factory=time.monotonic)


class AudioCoordinator:
    def __init__(self, synthesize: Callable, play: Callable, on_state: Callable,
                 on_delivered: Callable, *, group_window: float = 0.30,
                 max_group_wait: float = 0.85, cache_entries: int = 8):
        self._synthesize = synthesize
        self._play = play
        self._on_state = on_state
        self._on_delivered = on_delivered
        self._window = max(0.05, float(group_window))
        self._max_wait = max(self._window, float(max_group_wait))
        self._cache_limit = max(0, int(cache_entries))
        self._cache: OrderedDict[tuple, bytes] = OrderedDict()
        self._condition = threading.Condition()
        self._normal_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="blanky-tts-normal")
        self._urgent_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="blanky-tts-urgent")
        self._ready: list[tuple[int, int, SpeechJob, str]] = []
        self._inflight: dict[int, SpeechJob] = {}
        self._order_wait = 2.0
        self._pending_group: list[tuple[str, str, dict[str, str]]] = []
        self._group_started = 0.0
        self._group_updated = 0.0
        self._group_options: tuple[str, float, str] | None = None
        self._group_timer: threading.Timer | None = None
        self._active: SpeechJob | None = None
        self._capturing = False
        self._generation = 0
        self._sequence = 0
        self._closed = False
        self._player = threading.Thread(target=self._playback_loop, name="blanky-playback", daemon=True)
        self._player.start()

    def submit(self, text: str, *, voice: str, speed: float, language: str,
               priority: str = "requested", group: bool = False, remember: bool = True,
               group_key: str = "", localized: dict[str, str] | None = None):
        text = (text or "").strip()
        if not text:
            return
        if priority not in PRIORITY:
            raise ValueError("Unknown audio priority")
        localized = dict(localized or {language: text})
        with self._condition:
            if self._closed:
                return
            if group and priority == "operational":
                options = (voice, float(speed), language)
                if self._pending_group and options != self._group_options:
                    self._flush_group_locked()
                now = time.monotonic()
                if not self._pending_group:
                    self._group_started = now
                    self._group_options = options
                self._pending_group.append((text, group_key or f"event-{self._sequence}-{len(self._pending_group)}",
                                            localized))
                self._group_updated = now
                self._schedule_group_locked()
            else:
                self._create_job_locked(text, voice, speed, language, priority, remember, localized)

    def _schedule_group_locked(self):
        if self._group_timer:
            self._group_timer.cancel()
        due = min(self._group_updated + self._window, self._group_started + self._max_wait)
        self._group_timer = threading.Timer(max(0.0, due - time.monotonic()), self._flush_group)
        self._group_timer.daemon = True
        self._group_timer.start()

    def _flush_group(self):
        with self._condition:
            if not self._pending_group or self._closed:
                return
            due = min(self._group_updated + self._window, self._group_started + self._max_wait)
            if time.monotonic() + 0.002 < due:
                self._schedule_group_locked()
                return
            self._flush_group_locked()

    def _flush_group_locked(self):
        if not self._pending_group:
            return
        seen = set()
        latest = []
        for part, key, localized in reversed(self._pending_group):
            if key not in seen:
                latest.append((part, localized))
                seen.add(key)
        latest.reverse()
        voice, speed, language = self._group_options
        translations = {}
        for locale in ("pt", "en"):
            parts = [variants.get(locale, part) for part, variants in latest]
            if len(parts) > 3:
                translations[locale] = (f"{len(parts)} pedidos aceites. Último: {parts[-1]}" if locale == "pt" else
                                        f"{len(parts)} requests accepted. Latest: {parts[-1]}")
            else:
                translations[locale] = "; ".join(part.rstrip(". ") for part in parts) + "."
        text = translations[language]
        self._pending_group = []
        self._group_options = None
        if self._group_timer:
            self._group_timer.cancel()
            self._group_timer = None
        self._create_job_locked(text, voice, speed, language, "operational", True, translations)

    def _create_job_locked(self, text, voice, speed, language, priority, remember, localized):
        self._sequence += 1
        job = SpeechJob(text, voice, float(speed), language, PRIORITY[priority],
                        self._generation, self._sequence, remember, localized)
        self._inflight[job.sequence] = job
        executor = self._urgent_executor if job.priority >= PRIORITY["requested"] else self._normal_executor
        executor.submit(self._synthesize_job, job)

    def _synthesize_job(self, job: SpeechJob):
        path = ""
        try:
            with self._condition:
                if self._closed or job.cancel.is_set() or job.generation != self._generation:
                    return
                key = (job.text, job.voice, job.speed, job.language)
                cached = self._cache.get(key)
                if cached is not None:
                    self._cache.move_to_end(key)
            fd, path = tempfile.mkstemp(prefix="blanky_tts_", suffix=".wav")
            os.close(fd)
            if cached is None:
                self._synthesize(job.text, path, job.voice, job.speed, job.language)
                if self._cache_limit:
                    with open(path, "rb") as handle:
                        data = handle.read()
                    if len(data) <= 4_000_000:
                        with self._condition:
                            self._cache[key] = data
                            self._cache.move_to_end(key)
                            while len(self._cache) > self._cache_limit:
                                self._cache.popitem(last=False)
            else:
                with open(path, "wb") as handle:
                    handle.write(cached)
            with self._condition:
                if self._closed or job.cancel.is_set() or job.generation != self._generation:
                    return
                heapq.heappush(self._ready, (-job.priority, job.sequence, job, path))
                path = ""
                if self._active and job.priority > self._active.priority:
                    self._active.cancel.set()
                self._condition.notify_all()
        except Exception as exc:
            self._report("error", f"TTS: {type(exc).__name__}: {exc}")
        finally:
            with self._condition:
                self._inflight.pop(job.sequence, None)
                self._condition.notify_all()
            if path:
                self._unlink(path)

    def _playback_loop(self):
        while True:
            with self._condition:
                while not self._closed and (self._capturing or not self._ready):
                    self._condition.wait()
                if self._closed:
                    return
                _, _, candidate, _ = self._ready[0]
                earlier = [job for job in self._inflight.values()
                           if job.generation == self._generation and not job.cancel.is_set()
                           and job.priority == candidate.priority and job.sequence < candidate.sequence]
                if earlier:
                    deadline = min(job.created_at + self._order_wait for job in earlier)
                    remaining = deadline - time.monotonic()
                    if remaining > 0:
                        self._condition.wait(timeout=remaining)
                        continue
                    for job in earlier:
                        if job.created_at + self._order_wait <= time.monotonic():
                            job.cancel.set()
                            self._report("stale", "TTS: older response exceeded ordering deadline")
                    continue
                _, _, job, path = heapq.heappop(self._ready)
                if job.generation != self._generation:
                    self._unlink(path)
                    continue
                self._active = job
            delivered = False

            def started():
                nonlocal delivered
                with self._condition:
                    if job.cancel.is_set() or job.generation != self._generation or self._capturing:
                        return
                    delivered = True
                if job.remember:
                    try:
                        self._on_delivered({"text": job.text, "language": job.language,
                                            "localized": dict(job.localized)})
                    except RuntimeError as exc:
                        _LOG.warning("Audio delivery notification unavailable: %s", exc)

            try:
                self._report("playing", job.text)
                played = self._play(path, job.cancel, started)
                if played is False and not delivered and not job.cancel.is_set():
                    self._report("skipped", "Audio output is muted or unavailable")
                elif not delivered and not job.cancel.is_set():
                    self._report("error", "Playback: audio was not delivered")
            except Exception as exc:
                self._report("error", f"Playback: {type(exc).__name__}: {exc}")
            finally:
                self._unlink(path)
                with self._condition:
                    if self._active is job:
                        self._active = None
                    self._condition.notify_all()
                self._report("idle", "")

    def _report(self, state: str, message: str):
        with self._condition:
            if self._closed:
                return
        try:
            self._on_state(state, message)
        except RuntimeError as exc:
            _LOG.warning("Audio state notification unavailable: %s", exc)

    def cancel_pending(self, *, capture: bool | None = None):
        """Invalidate queued/late TTS without waiting in the caller's thread."""
        with self._condition:
            self._generation += 1
            if capture is not None:
                self._capturing = capture
            if self._active:
                self._active.cancel.set()
            if self._group_timer:
                self._group_timer.cancel()
                self._group_timer = None
            self._pending_group = []
            self._group_options = None
            for _, _, _, path in self._ready:
                self._unlink(path)
            self._ready = []
            self._condition.notify_all()

    def begin_capture(self):
        self.cancel_pending(capture=True)

    def wait_for_quiet(self, timeout: float = 3.0) -> bool:
        deadline = time.monotonic() + timeout
        with self._condition:
            while self._active is not None and time.monotonic() < deadline:
                self._condition.wait(timeout=max(0.0, deadline - time.monotonic()))
            return self._active is None

    def end_capture(self):
        with self._condition:
            self._capturing = False
            self._condition.notify_all()

    def close(self):
        self.cancel_pending()
        with self._condition:
            self._closed = True
            self._condition.notify_all()
        self._normal_executor.shutdown(wait=False, cancel_futures=True)
        self._urgent_executor.shutdown(wait=False, cancel_futures=True)

    @staticmethod
    def _unlink(path: str):
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
