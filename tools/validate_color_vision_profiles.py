"""Validate the semantic colour-vision palettes used by Blanky's QML theme.

This is a design-time check only. It measures WCAG relative-luminance contrast
and, when colorspacious is installed, checks luminance separation after an
approximate Machado et al. colour-vision-deficiency simulation. It does not
claim legal or standards conformance.
"""

from __future__ import annotations

from itertools import combinations
from math import isclose


BACKGROUND = "#07121d"
PALETTES = {
    "universal": {
        "success": "#4fc3f7", "warning": "#ffd166", "error": "#ff9f43", "inactive": "#b6c4cf",
    },
    "protan": {
        "success": "#55c8f2", "warning": "#ffe066", "error": "#ffb000", "inactive": "#c7d0d8",
    },
    "deutan": {
        "success": "#5ab4e5", "warning": "#f6c445", "error": "#f28e2b", "inactive": "#c6d0d8",
    },
    "tritan": {
        "success": "#f3f6fa", "warning": "#ffad8a", "error": "#ff5f8a", "inactive": "#cad0d8",
    },
}
SURFACES = {
    "universal": {"success": "#102a3c", "warning": "#2d2615", "error": "#321f18"},
    "protan": {"success": "#102b3d", "warning": "#332d12", "error": "#35280d"},
    "deutan": {"success": "#102a3c", "warning": "#352b12", "error": "#35220f"},
    "tritan": {"success": "#27303c", "warning": "#3a231a", "error": "#361a29"},
}


def rgb(hex_color: str) -> tuple[float, float, float]:
    value = hex_color.lstrip("#")
    return tuple(int(value[index:index + 2], 16) / 255 for index in (0, 2, 4))


def luminance(rgb_value: tuple[float, float, float]) -> float:
    def linear(channel: float) -> float:
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    red, green, blue = (linear(channel) for channel in rgb_value)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(first: str, second: str) -> float:
    light, dark = sorted((luminance(rgb(first)), luminance(rgb(second))), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def validate_wcag_contrast() -> bool:
    valid = True
    for profile, palette in PALETTES.items():
        for token, color in palette.items():
            ratio = contrast(color, BACKGROUND)
            print(f"{profile:9} {token:8} {ratio:.2f}:1")
            if ratio < 4.5:
                valid = False
                print(f"  FAIL: {token} must meet 4.5:1 against {BACKGROUND}.")
        for token, surface in SURFACES[profile].items():
            ratio = contrast(palette[token], surface)
            print(f"{profile:9} {token + '-surface':16} {ratio:.2f}:1")
            if ratio < 3.0:
                valid = False
                print(f"  FAIL: {token} must meet 3:1 against its state surface.")
    return valid


def validate_simulation() -> bool:
    try:
        from colorspacious import cspace_convert
    except ImportError:
        print("Simulation skipped: install requirements-dev.txt to run colorspacious checks.")
        return True

    valid = True
    simulations = {
        "protan": "protanomaly",
        "deutan": "deuteranomaly",
        "tritan": "tritanomaly",
    }
    for profile, cvd_type in simulations.items():
        simulated = {
            token: tuple(max(0.0, min(1.0, channel)) for channel in cspace_convert(
                rgb(color), "sRGB1", {"name": "sRGB1+CVD", "cvd_type": cvd_type, "severity": 100}
            ))
            for token, color in PALETTES[profile].items()
        }
        for first, second in combinations(simulated, 2):
            difference = abs(luminance(simulated[first]) - luminance(simulated[second]))
            if isclose(difference, 0.0, abs_tol=0.015):
                valid = False
                print(f"FAIL: {profile} simulation makes {first} and {second} too similar in luminance.")
    return valid


if __name__ == "__main__":
    contrast_ok = validate_wcag_contrast()
    simulation_ok = validate_simulation()
    raise SystemExit(0 if contrast_ok and simulation_ok else 1)
