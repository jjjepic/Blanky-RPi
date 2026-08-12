from __future__ import annotations

import os
import queue
import threading
import time
from fractions import Fraction
from dataclasses import dataclass
from typing import Optional

import numpy as np
import sounddevice as sd
from scipy.signal import resample_poly

from blanky.config import (
    WAKEWORD_COOLDOWN_SECONDS,
    WAKEWORD_ENABLED,
    WAKEWORD_FRAME_MS,
    WAKEWORD_MODEL_NAME,
    WAKEWORD_MODEL_PATH,
    WAKEWORD_SAMPLE_RATE,
    WAKEWORD_THRESHOLD,
)


@dataclass
class WakeEvent:
    name: str
    score: float
    when: float


class WakeWordService:
    def __init__(self):
        self.enabled = bool(WAKEWORD_ENABLED)
        self._threshold = float(WAKEWORD_THRESHOLD)
        self._cooldown_seconds = float(WAKEWORD_COOLDOWN_SECONDS)
        self._sample_rate = int(WAKEWORD_SAMPLE_RATE)
        self._frame_ms = int(WAKEWORD_FRAME_MS)

        self._running = False
        self._paused = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        self._events: queue.Queue[WakeEvent] = queue.Queue()
        self._last_detection_ts = 0.0
        self._last_error = ""
        self._active_model_name = ""
        self._active_stream_rate = 0

    def start(self):
        if not self.enabled:
            return
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        t = self._thread
        if t is not None and t.is_alive():
            t.join(timeout=1.0)
        self._thread = None

    def set_paused(self, value: bool):
        with self._lock:
            self._paused = bool(value)

    def get_events(self) -> list[WakeEvent]:
        out: list[WakeEvent] = []
        while True:
            try:
                out.append(self._events.get_nowait())
            except queue.Empty:
                return out

    def health(self) -> dict:
        return {
            "enabled": self.enabled,
            "running": self._running,
            "paused": self._paused,
            "threshold": self._threshold,
            "model": self._active_model_name,
            "stream_rate": self._active_stream_rate,
            "last_error": self._last_error,
        }

    def _create_model(self):
        from openwakeword.model import Model

        model_path = str(WAKEWORD_MODEL_PATH or "").strip()
        if model_path and os.path.exists(model_path):
            self._active_model_name = os.path.basename(model_path)
            return Model(wakeword_models=[model_path])

        self._active_model_name = WAKEWORD_MODEL_NAME
        return Model(wakeword_models=[WAKEWORD_MODEL_NAME])

    def _run_loop(self):
        try:
            model = self._create_model()
        except Exception as exc:
            self._last_error = f"wakeword init failed: {exc}"
            self.enabled = False
            self._running = False
            return

        stream = None
        try:
            stream_sr = self._sample_rate
            candidates = [self._sample_rate, 48000, 44100, 32000]
            for candidate in candidates:
                try:
                    frame_samples = int((candidate * self._frame_ms) / 1000)
                    frame_samples = max(160, frame_samples)
                    stream = sd.InputStream(
                        samplerate=candidate,
                        channels=1,
                        dtype="int16",
                        blocksize=frame_samples,
                    )
                    stream_sr = candidate
                    break
                except Exception:
                    stream = None
                    continue

            if stream is None:
                raise RuntimeError("no supported sample rate for wakeword stream")

            self._active_stream_rate = int(stream_sr)
            frame_samples = int((stream_sr * self._frame_ms) / 1000)
            frame_samples = max(160, frame_samples)
            stream.start()
            self._last_error = ""

            while self._running:
                if self._paused:
                    time.sleep(0.05)
                    continue

                frame, overflowed = stream.read(frame_samples)
                if overflowed:
                    continue

                pcm = np.asarray(frame).reshape(-1)
                if pcm.size == 0:
                    continue
                if stream_sr != self._sample_rate:
                    ratio = Fraction(self._sample_rate, stream_sr).limit_denominator()
                    pcm = resample_poly(pcm.astype(np.float32), ratio.numerator, ratio.denominator)
                    pcm = np.clip(pcm, -32768, 32767).astype(np.int16)

                scores = model.predict(pcm)
                if not isinstance(scores, dict) or not scores:
                    continue

                name, score = max(scores.items(), key=lambda item: float(item[1]))
                score = float(score)
                now = time.monotonic()
                if score < self._threshold:
                    continue
                if now - self._last_detection_ts < self._cooldown_seconds:
                    continue

                self._last_detection_ts = now
                self._events.put(WakeEvent(name=str(name), score=score, when=now))
        except Exception as exc:
            self._last_error = f"wakeword runtime failed: {exc}"
            self.enabled = False
        finally:
            self._running = False
            self._active_stream_rate = 0
            if stream is not None:
                try:
                    stream.stop()
                    stream.close()
                except Exception:
                    pass


_WAKEWORD: Optional[WakeWordService] = None


def get_wakeword_service() -> WakeWordService:
    global _WAKEWORD
    if _WAKEWORD is None:
        _WAKEWORD = WakeWordService()
    return _WAKEWORD
