import os
import subprocess
import tempfile
import threading
from collections import deque
from typing import Optional

import numpy as np
import scipy.io.wavfile as wav
import sounddevice as sd
from scipy.signal import butter, istft, lfilter, stft

from blanky.config import (
    AUDIO_FILTER_ENABLED,
    AUDIO_HIGHPASS_HZ,
    AUDIO_MAX_GAIN,
    AUDIO_NOISE_FLOOR_KEEP,
    AUDIO_NOISE_GATE_BLEND,
    AUDIO_NOISE_GATE_FACTOR,
    AUDIO_NOISE_PROFILE_SUBTRACT_ENABLED,
    AUDIO_NOISE_SUBTRACT_FACTOR,
    AUDIO_VAD_CALIBRATION_SECONDS,
    AUDIO_VAD_MAX_RECORD_SECONDS,
    AUDIO_VAD_MIN_RECORD_SECONDS,
    AUDIO_VAD_MIN_RMS,
    AUDIO_VAD_SILENCE_HOLD_SECONDS,
    AUDIO_VAD_TRIGGER_FACTOR,
    AUDIO_VAD_WAIT_FOR_SPEECH_SECONDS,
    BEEP_WAV,
    DEVICE_ID,
    FS,
    SECONDS,
)

_ACTIVE_INPUT_DEVICE: Optional[int] = None
_ACTIVE_FS: Optional[int] = None
_FALLBACK_SAMPLE_RATES = (16000, 48000, 44100, 32000, 22050, 8000)
_LAST_RECORD_DIAG: dict = {}
_AUDIO_OUTPUT_ENABLED = True
_AUDIO_OUTPUT_VOLUME = 1.0
_PLAYBACK_LOCK = threading.Lock()

_SETTINGS_LIMITS = {
    "calibration_seconds": (0.08, 1.20),
    "wait_for_speech_seconds": (0.35, 2.50),
    "min_record_seconds": (0.25, 2.20),
    "max_record_seconds": (1.00, 6.00),
    "silence_hold_seconds": (0.18, 1.20),
    "trigger_factor": (1.20, 2.60),
    "min_rms": (0.0010, 0.0300),
    "max_gain": (1.00, 6.00),
    "highpass_hz": (40.0, 220.0),
    "noise_gate_factor": (1.10, 3.20),
    "noise_gate_blend": (0.05, 0.90),
    "noise_subtract_factor": (0.10, 1.20),
    "noise_floor_keep": (0.00, 0.40),
}

_AUDIO_INPUT_PRESETS = {
    "simple": {
        "calibration_seconds": 0.18,
        "wait_for_speech_seconds": 0.70,
        "min_record_seconds": 0.55,
        "max_record_seconds": 3.20,
        "silence_hold_seconds": 0.35,
        "trigger_factor": 1.65,
        "min_rms": 0.0020,
        "max_gain": 4.50,
        "highpass_enabled": False,
        "highpass_hz": 90.0,
        "noise_gate_enabled": False,
        "noise_gate_factor": 1.90,
        "noise_gate_blend": 0.18,
        "noise_reduction_enabled": False,
        "noise_subtract_factor": 0.25,
        "noise_floor_keep": 0.10,
    },
    "balanced": {
        "calibration_seconds": 0.22,
        "wait_for_speech_seconds": 0.85,
        "min_record_seconds": 0.60,
        "max_record_seconds": 3.50,
        "silence_hold_seconds": 0.40,
        "trigger_factor": 1.80,
        "min_rms": 0.0025,
        "max_gain": 4.10,
        "highpass_enabled": bool(AUDIO_FILTER_ENABLED),
        "highpass_hz": 100.0,
        "noise_gate_enabled": False,
        "noise_gate_factor": 2.00,
        "noise_gate_blend": 0.16,
        "noise_reduction_enabled": False,
        "noise_subtract_factor": 0.28,
        "noise_floor_keep": 0.10,
    },
    "noisy": {
        "calibration_seconds": 0.28,
        "wait_for_speech_seconds": 1.00,
        "min_record_seconds": 0.70,
        "max_record_seconds": 3.80,
        "silence_hold_seconds": 0.48,
        "trigger_factor": 1.95,
        "min_rms": 0.0038,
        "max_gain": 3.40,
        "highpass_enabled": True,
        "highpass_hz": 110.0,
        "noise_gate_enabled": False,
        "noise_gate_factor": 2.10,
        "noise_gate_blend": 0.15,
        "noise_reduction_enabled": True,
        "noise_subtract_factor": 0.30,
        "noise_floor_keep": 0.12,
    },
}

_AUDIO_INPUT_PRESET = "simple"
_AUDIO_INPUT_SETTINGS: dict[str, float | bool] = {}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _coerce_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _sanitize_audio_input_settings(raw: dict) -> dict[str, float | bool]:
    settings = dict(raw or {})
    out = {
        "calibration_seconds": _clamp(
            settings.get("calibration_seconds", AUDIO_VAD_CALIBRATION_SECONDS),
            *_SETTINGS_LIMITS["calibration_seconds"],
        ),
        "wait_for_speech_seconds": _clamp(
            settings.get("wait_for_speech_seconds", AUDIO_VAD_WAIT_FOR_SPEECH_SECONDS),
            *_SETTINGS_LIMITS["wait_for_speech_seconds"],
        ),
        "min_record_seconds": _clamp(
            settings.get("min_record_seconds", AUDIO_VAD_MIN_RECORD_SECONDS),
            *_SETTINGS_LIMITS["min_record_seconds"],
        ),
        "max_record_seconds": _clamp(
            settings.get("max_record_seconds", AUDIO_VAD_MAX_RECORD_SECONDS),
            *_SETTINGS_LIMITS["max_record_seconds"],
        ),
        "silence_hold_seconds": _clamp(
            settings.get("silence_hold_seconds", AUDIO_VAD_SILENCE_HOLD_SECONDS),
            *_SETTINGS_LIMITS["silence_hold_seconds"],
        ),
        "trigger_factor": _clamp(
            settings.get("trigger_factor", AUDIO_VAD_TRIGGER_FACTOR),
            *_SETTINGS_LIMITS["trigger_factor"],
        ),
        "min_rms": _clamp(settings.get("min_rms", AUDIO_VAD_MIN_RMS), *_SETTINGS_LIMITS["min_rms"]),
        "max_gain": _clamp(settings.get("max_gain", AUDIO_MAX_GAIN), *_SETTINGS_LIMITS["max_gain"]),
        "highpass_enabled": _coerce_bool(settings.get("highpass_enabled", AUDIO_FILTER_ENABLED)),
        "highpass_hz": _clamp(settings.get("highpass_hz", AUDIO_HIGHPASS_HZ), *_SETTINGS_LIMITS["highpass_hz"]),
        "noise_gate_enabled": _coerce_bool(settings.get("noise_gate_enabled", False)),
        "noise_gate_factor": _clamp(
            settings.get("noise_gate_factor", AUDIO_NOISE_GATE_FACTOR),
            *_SETTINGS_LIMITS["noise_gate_factor"],
        ),
        "noise_gate_blend": _clamp(
            settings.get("noise_gate_blend", AUDIO_NOISE_GATE_BLEND),
            *_SETTINGS_LIMITS["noise_gate_blend"],
        ),
        "noise_reduction_enabled": _coerce_bool(
            settings.get("noise_reduction_enabled", AUDIO_NOISE_PROFILE_SUBTRACT_ENABLED)
        ),
        "noise_subtract_factor": _clamp(
            settings.get("noise_subtract_factor", AUDIO_NOISE_SUBTRACT_FACTOR),
            *_SETTINGS_LIMITS["noise_subtract_factor"],
        ),
        "noise_floor_keep": _clamp(
            settings.get("noise_floor_keep", AUDIO_NOISE_FLOOR_KEEP),
            *_SETTINGS_LIMITS["noise_floor_keep"],
        ),
    }

    if out["max_record_seconds"] <= out["min_record_seconds"]:
        out["max_record_seconds"] = min(
            _SETTINGS_LIMITS["max_record_seconds"][1],
            float(out["min_record_seconds"]) + 0.80,
        )

    return out


def _init_audio_input_settings():
    global _AUDIO_INPUT_SETTINGS, _AUDIO_INPUT_PRESET
    preset = "noisy" if AUDIO_NOISE_PROFILE_SUBTRACT_ENABLED else "simple"
    _AUDIO_INPUT_PRESET = preset
    _AUDIO_INPUT_SETTINGS = _sanitize_audio_input_settings(_AUDIO_INPUT_PRESETS[preset])


_init_audio_input_settings()


def get_audio_input_preset() -> str:
    return _AUDIO_INPUT_PRESET


def get_audio_input_settings() -> dict:
    return dict(_AUDIO_INPUT_SETTINGS)


def apply_audio_input_preset(preset: str) -> dict:
    global _AUDIO_INPUT_PRESET, _AUDIO_INPUT_SETTINGS
    target = (preset or "").strip().lower()
    if target not in _AUDIO_INPUT_PRESETS:
        target = "simple"
    _AUDIO_INPUT_PRESET = target
    _AUDIO_INPUT_SETTINGS = _sanitize_audio_input_settings(_AUDIO_INPUT_PRESETS[target])
    return get_audio_input_settings()


def update_audio_input_settings(**updates) -> dict:
    global _AUDIO_INPUT_PRESET, _AUDIO_INPUT_SETTINGS
    merged = dict(_AUDIO_INPUT_SETTINGS)
    for key, value in updates.items():
        if value is None or key not in {
            "calibration_seconds",
            "wait_for_speech_seconds",
            "min_record_seconds",
            "max_record_seconds",
            "silence_hold_seconds",
            "trigger_factor",
            "min_rms",
            "max_gain",
            "highpass_enabled",
            "highpass_hz",
            "noise_gate_enabled",
            "noise_gate_factor",
            "noise_gate_blend",
            "noise_reduction_enabled",
            "noise_subtract_factor",
            "noise_floor_keep",
        }:
            continue
        merged[key] = value
    _AUDIO_INPUT_SETTINGS = _sanitize_audio_input_settings(merged)
    _AUDIO_INPUT_PRESET = "custom"
    return get_audio_input_settings()


def _highpass_filter(signal_f32: np.ndarray, fs: int, cutoff_hz: float) -> np.ndarray:
    if signal_f32.size == 0:
        return signal_f32
    nyquist = 0.5 * float(fs)
    norm = float(cutoff_hz) / max(nyquist, 1e-9)
    norm = min(max(norm, 1e-5), 0.95)
    b, a = butter(2, norm, btype="highpass")
    return lfilter(b, a, signal_f32).astype(np.float32)


def _noise_gate(signal_f32: np.ndarray, noise_floor_rms: float, gate_factor: float, gate_blend: float) -> np.ndarray:
    if signal_f32.size == 0:
        return signal_f32
    gate = float(noise_floor_rms) * float(gate_factor)
    if gate <= 0.0:
        return signal_f32
    abs_x = np.abs(signal_f32)
    atten = np.where(abs_x < gate, float(gate_blend), 1.0).astype(np.float32)
    return (signal_f32 * atten).astype(np.float32)


def _spectral_subtract(
    signal_f32: np.ndarray,
    noise_ref_f32: np.ndarray,
    fs: int,
    subtract_factor: float,
    floor_keep: float,
) -> np.ndarray:
    if signal_f32.size == 0 or noise_ref_f32.size == 0:
        return signal_f32

    nperseg = 512
    noverlap = 256

    _, _, z_noise = stft(noise_ref_f32, fs=fs, nperseg=nperseg, noverlap=noverlap)
    if z_noise.size == 0:
        return signal_f32
    noise_mag = np.mean(np.abs(z_noise), axis=1, keepdims=True)

    _, _, z_sig = stft(signal_f32, fs=fs, nperseg=nperseg, noverlap=noverlap)
    if z_sig.size == 0:
        return signal_f32

    sig_mag = np.abs(z_sig)
    sig_phase = np.angle(z_sig)

    cleaned_mag = sig_mag - float(subtract_factor) * noise_mag
    floor = float(floor_keep) * sig_mag
    cleaned_mag = np.maximum(cleaned_mag, floor)

    z_clean = cleaned_mag * np.exp(1j * sig_phase)
    _, cleaned = istft(z_clean, fs=fs, nperseg=nperseg, noverlap=noverlap, input_onesided=True)
    if cleaned.size == 0:
        return signal_f32

    cleaned = cleaned.astype(np.float32)
    if cleaned.size > signal_f32.size:
        cleaned = cleaned[: signal_f32.size]
    elif cleaned.size < signal_f32.size:
        cleaned = np.pad(cleaned, (0, signal_f32.size - cleaned.size))
    return cleaned


def _resolve_input_device() -> Optional[int]:
    if DEVICE_ID is not None:
        return int(DEVICE_ID)

    default = sd.default.device
    if isinstance(default, (tuple, list)) and len(default) >= 1 and default[0] is not None:
        return int(default[0])
    if isinstance(default, int):
        return int(default)
    return None


def _choose_sample_rate(device: Optional[int]) -> int:
    candidates = []
    try:
        info = sd.query_devices(device, "input")
        default_sr = int(float(info.get("default_samplerate") or 0))
        if default_sr > 0:
            candidates.append(default_sr)
    except Exception:
        pass

    candidates.append(int(FS))
    candidates.extend(_FALLBACK_SAMPLE_RATES)

    seen = set()
    for sr in candidates:
        if sr in seen or sr <= 0:
            continue
        seen.add(sr)
        try:
            sd.check_input_settings(device=device, samplerate=sr, channels=1, dtype="float32")
            return sr
        except Exception:
            continue

    raise RuntimeError(
        "Nao foi possivel encontrar uma sample rate valida para o microfone. "
        "Verifica o dispositivo de captura no Raspberry."
    )


def init_audio():
    global _ACTIVE_INPUT_DEVICE, _ACTIVE_FS
    _ACTIVE_INPUT_DEVICE = _resolve_input_device()
    _ACTIVE_FS = _choose_sample_rate(_ACTIVE_INPUT_DEVICE)
    sd.default.device = (_ACTIVE_INPUT_DEVICE, None)
    sd.default.samplerate = _ACTIVE_FS


def record_wav(path: str, seconds: int = SECONDS, fs: Optional[int] = None):
    global _LAST_RECORD_DIAG
    if _ACTIVE_FS is None:
        init_audio()

    settings = get_audio_input_settings()
    current_fs = int(fs or _ACTIVE_FS or FS)
    frame_ms = 20
    frame_samples = max(1, int((current_fs * frame_ms) / 1000))
    frame_seconds = frame_samples / float(current_fs)

    calibration_frames = max(1, int(float(settings["calibration_seconds"]) / frame_seconds))
    wait_for_speech_frames = max(1, int(float(settings["wait_for_speech_seconds"]) / frame_seconds))
    min_record_frames = max(1, int(float(settings["min_record_seconds"]) / frame_seconds))
    max_record_frames = max(min_record_frames + 1, int(float(settings["max_record_seconds"]) / frame_seconds))
    silence_hold_frames = max(1, int(float(settings["silence_hold_seconds"]) / frame_seconds))
    pre_roll_frames_limit = max(1, int(0.18 / frame_seconds))

    noise_floor = 0.0
    noise_std = 0.0
    trigger_rms = float(settings["min_rms"])
    release_rms = float(settings["min_rms"]) * 0.85

    noise_rms_values: list[float] = []
    noise_frames: list[np.ndarray] = []
    captured_frames: list[np.ndarray] = []
    pre_roll_frames: deque[np.ndarray] = deque(maxlen=pre_roll_frames_limit)
    speech_started = False
    frames_since_speech = 0
    silent_frames_after_speech = 0
    waited_frames = 0
    fallback_started = False
    end_reason = "max_record_reached"
    attack_frames = 0
    attack_confirm_frames = 2

    with sd.InputStream(
        samplerate=current_fs,
        channels=1,
        dtype="float32",
        blocksize=frame_samples,
        device=_ACTIVE_INPUT_DEVICE,
    ) as stream:
        while len(noise_rms_values) < calibration_frames:
            block, overflowed = stream.read(frame_samples)
            if overflowed:
                continue
            arr = np.asarray(block, dtype=np.float32).reshape(-1)
            if arr.size == 0:
                continue
            noise_rms_values.append(float(np.sqrt(np.mean(np.square(arr))) + 1e-12))
            noise_frames.append(arr.copy())

        noise_floor = float(np.median(noise_rms_values)) if noise_rms_values else 0.0
        noise_std = float(np.std(noise_rms_values)) if noise_rms_values else 0.0
        trigger_rms = max(
            float(settings["min_rms"]),
            noise_floor * float(settings["trigger_factor"]),
            noise_floor + max(0.008, noise_std * 1.8),
        )
        trigger_rms = min(trigger_rms, 0.95)
        release_rms = max(
            float(settings["min_rms"]) * 0.85,
            min(trigger_rms * 0.78, noise_floor + max(0.004, noise_std * 0.9)),
        )
        release_rms = min(release_rms, trigger_rms * 0.95)

        while frames_since_speech < max_record_frames:
            block, overflowed = stream.read(frame_samples)
            if overflowed:
                continue

            arr = np.asarray(block, dtype=np.float32).reshape(-1)
            if arr.size == 0:
                continue

            rms = float(np.sqrt(np.mean(np.square(arr))) + 1e-12)

            if not speech_started:
                pre_roll_frames.append(arr.copy())
                if rms >= trigger_rms:
                    attack_frames += 1
                    if attack_frames >= attack_confirm_frames:
                        speech_started = True
                        captured_frames.extend(list(pre_roll_frames))
                        frames_since_speech = len(captured_frames)
                        waited_frames = 0
                        attack_frames = 0
                        continue
                else:
                    attack_frames = 0
                waited_frames += 1
                if waited_frames >= wait_for_speech_frames:
                    speech_started = True
                    fallback_started = True
                    captured_frames.extend(list(pre_roll_frames))
                    frames_since_speech = len(captured_frames)
                continue

            captured_frames.append(arr.copy())
            frames_since_speech += 1

            if rms < release_rms:
                silent_frames_after_speech += 1
            else:
                silent_frames_after_speech = 0

            if frames_since_speech >= min_record_frames and silent_frames_after_speech >= silence_hold_frames:
                end_reason = "silence_after_speech"
                break

    if not captured_frames:
        audio_i16 = np.zeros((0, 1), dtype=np.int16)
        captured_peak = 0.0
        applied_gain = 1.0
    else:
        audio_float = np.concatenate(captured_frames).astype(np.float32)
        noise_ref = np.concatenate(noise_frames).astype(np.float32) if noise_frames else np.zeros((0,), dtype=np.float32)

        if bool(settings["noise_reduction_enabled"]) and noise_ref.size >= frame_samples * 2:
            audio_float = _spectral_subtract(
                signal_f32=audio_float,
                noise_ref_f32=noise_ref,
                fs=current_fs,
                subtract_factor=float(settings["noise_subtract_factor"]),
                floor_keep=float(settings["noise_floor_keep"]),
            )

        peak_post = float(np.max(np.abs(audio_float))) + 1e-9
        if peak_post > 1.0:
            audio_float = (audio_float / peak_post).astype(np.float32)

        if bool(settings["highpass_enabled"]) and float(settings["highpass_hz"]) > 0.0:
            audio_float = _highpass_filter(audio_float, current_fs, float(settings["highpass_hz"]))

        if bool(settings["noise_gate_enabled"]):
            audio_float = _noise_gate(
                audio_float,
                noise_floor,
                float(settings["noise_gate_factor"]),
                float(settings["noise_gate_blend"]),
            )

        peak = float(np.max(np.abs(audio_float))) + 1e-9
        captured_peak = peak
        applied_gain = 1.0
        if peak > 0:
            applied_gain = min(float(settings["max_gain"]), 0.92 / peak)
            audio_float = audio_float * applied_gain
        audio_i16 = (audio_float * 32767.0).clip(-32768, 32767).astype(np.int16).reshape(-1, 1)

    total_duration_s = (waited_frames + frames_since_speech) * frame_seconds
    speech_duration_s = frames_since_speech * frame_seconds
    wait_duration_s = waited_frames * frame_seconds
    _LAST_RECORD_DIAG = {
        "sample_rate": current_fs,
        "frame_ms": frame_ms,
        "noise_floor_rms": noise_floor,
        "trigger_rms": trigger_rms,
        "release_rms": release_rms,
        "noise_std_rms": noise_std,
        "waited_for_speech_s": wait_duration_s,
        "speech_duration_s": speech_duration_s,
        "total_duration_s": total_duration_s,
        "captured_frames": frames_since_speech,
        "fallback_started": fallback_started,
        "end_reason": end_reason if frames_since_speech < max_record_frames else "max_record_reached",
        "captured_peak": captured_peak,
        "applied_gain": applied_gain,
        "pre_roll_ms": int(pre_roll_frames_limit * frame_ms),
        "audio_input_preset": _AUDIO_INPUT_PRESET,
        "audio_input_settings": get_audio_input_settings(),
        "highpass_enabled": bool(settings["highpass_enabled"]),
        "noise_gate_enabled": bool(settings["noise_gate_enabled"]),
        "noise_reduction_enabled": bool(settings["noise_reduction_enabled"]),
        "noise_subtract_factor": float(settings["noise_subtract_factor"]),
    }

    os.makedirs(os.path.dirname(path), exist_ok=True)
    wav.write(path, current_fs, audio_i16)


def _normalize_audio_for_playback(data) -> tuple[np.ndarray, int]:
    sr, raw = data
    arr = np.asarray(raw)
    if arr.size == 0:
        return np.zeros((0,), dtype=np.float32), int(sr)

    if arr.dtype.kind in {"i", "u"}:
        maxv = float(np.iinfo(arr.dtype).max or 1)
        audio = arr.astype(np.float32) / maxv
    else:
        audio = arr.astype(np.float32)

    audio = np.clip(audio * float(_AUDIO_OUTPUT_VOLUME), -1.0, 1.0)
    return audio, int(sr)


def _play_with_system_fallback(audio: np.ndarray, sr: int):
    if audio.size == 0:
        return
    tmp_path = os.path.join(tempfile.gettempdir(), "blanky_playback.wav")
    audio_i16 = (np.clip(audio, -1.0, 1.0) * 32767.0).astype(np.int16)
    wav.write(tmp_path, int(sr), audio_i16)
    try:
        subprocess.run(
            ["aplay", tmp_path],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def play_wav(path: str):
    if not _AUDIO_OUTPUT_ENABLED or float(_AUDIO_OUTPUT_VOLUME) <= 0.0:
        return
    if not os.path.exists(path):
        return
    with _PLAYBACK_LOCK:
        audio = np.zeros((0,), dtype=np.float32)
        sr = int(_ACTIVE_FS or FS)
        try:
            audio, sr = _normalize_audio_for_playback(wav.read(path))
            if audio.size == 0:
                return
            sd.stop()
            sd.play(audio, samplerate=sr, blocking=True)
        except Exception:
            try:
                _play_with_system_fallback(audio, sr)
            except Exception:
                pass


def stop_playback():
    with _PLAYBACK_LOCK:
        try:
            sd.stop()
        except Exception:
            pass


def set_audio_output_enabled(enabled: bool):
    global _AUDIO_OUTPUT_ENABLED
    _AUDIO_OUTPUT_ENABLED = bool(enabled)
    if not _AUDIO_OUTPUT_ENABLED:
        stop_playback()


def is_audio_output_enabled() -> bool:
    return _AUDIO_OUTPUT_ENABLED


def set_audio_output_volume(volume: float):
    global _AUDIO_OUTPUT_VOLUME
    _AUDIO_OUTPUT_VOLUME = float(_clamp(volume, 0.0, 1.0))


def get_audio_output_volume() -> float:
    return _AUDIO_OUTPUT_VOLUME


def _ensure_beep(path: str = BEEP_WAV):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fs = 16000
    duration = 0.34
    t = np.linspace(0.0, duration, int(fs * duration), endpoint=False)
    tone = (0.62 * np.sin(2.0 * np.pi * 920.0 * t)) + (0.22 * np.sin(2.0 * np.pi * 1420.0 * t))
    pulse = np.ones_like(t)
    gap_start = int(fs * 0.14)
    gap_end = int(fs * 0.18)
    pulse[gap_start:gap_end] *= 0.35
    tone *= pulse
    attack = max(1, int(fs * 0.012))
    release = max(1, int(fs * 0.040))
    tone[:attack] *= np.linspace(0.0, 1.0, attack, endpoint=False)
    tone[-release:] *= np.linspace(1.0, 0.0, release, endpoint=False)
    tone_i16 = (np.clip(tone, -1.0, 1.0) * 32767.0).astype(np.int16).reshape(-1, 1)
    wav.write(path, fs, tone_i16)


def play_beep():
    try:
        if not _AUDIO_OUTPUT_ENABLED or float(_AUDIO_OUTPUT_VOLUME) <= 0.0:
            return
        _ensure_beep(BEEP_WAV)
        play_wav(BEEP_WAV)
    except Exception:
        pass


def is_audio_ready() -> bool:
    return _ACTIVE_FS is not None


def audio_info() -> dict:
    return {
        "ready": is_audio_ready(),
        "input_device": _ACTIVE_INPUT_DEVICE,
        "sample_rate": _ACTIVE_FS,
        "last_record_diag": dict(_LAST_RECORD_DIAG),
        "sound_enabled": _AUDIO_OUTPUT_ENABLED,
        "sound_volume": _AUDIO_OUTPUT_VOLUME,
        "input_preset": _AUDIO_INPUT_PRESET,
        "input_settings": get_audio_input_settings(),
    }
