"""Load Blanky's central colour-vision tokens for Python-rendered output."""

from __future__ import annotations

import json
import re
from pathlib import Path


_PROFILE_FILE = Path(__file__).resolve().parents[1] / "ui" / "ColorVisionProfiles.js"


def all_profile_tokens() -> dict[str, dict[str, str]]:
    """Return the JSON-compatible palette embedded in the QML source."""
    source = _PROFILE_FILE.read_text(encoding="utf-8")
    match = re.search(r"var PROFILE_TOKENS = (\{.*?\})\s*\n\s*function profile", source, re.DOTALL)
    if not match:
        raise RuntimeError(f"Could not read colour-vision tokens from {_PROFILE_FILE}")
    return json.loads(match.group(1))


def get_profile_tokens(profile: str) -> dict[str, str]:
    palettes = all_profile_tokens()
    return palettes.get(profile, palettes["universal"])
