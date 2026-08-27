"""Validate Blanky's colour-vision palettes from the shared QML token source.

The script uses the Machado et al. model provided by ``colorspacious`` and the
WCAG relative-luminance contrast formula. It writes a versioned Markdown report
so that palette changes can be reviewed without relying only on screenshots.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from colorspacious import cspace_convert


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from blanky.color_vision_profiles import all_profile_tokens  # noqa: E402


REPORT_PATH = PROJECT_ROOT / "docs" / "color_profile_validation.md"
MIN_TEXT_CONTRAST = 4.5
MIN_COMPONENT_CONTRAST = 3.0
MIN_DELTA_E = 15.0
MIN_GRAYSCALE_LUMINANCE_DELTA = 0.10

STATE_PAIRS = (
    ("Sucesso / erro", "success", "error"),
    ("Sucesso / inativo", "success", "inactive"),
    ("Aviso / erro", "warning", "error"),
    ("ON / OFF", "success", "inactive"),
)
SIMULATIONS = {
    "universal": ("protanomaly", "deuteranomaly", "tritanomaly"),
    "protan": ("protanomaly",),
    "deutan": ("deuteranomaly",),
    "tritan": ("tritanomaly",),
}


def rgb(hex_color: str) -> tuple[float, float, float]:
    value = hex_color.removeprefix("#")
    if len(value) != 6:
        raise ValueError(f"Expected #RRGGBB, received {hex_color!r}")
    return tuple(int(value[index:index + 2], 16) / 255 for index in (0, 2, 4))


def relative_luminance(color: tuple[float, float, float]) -> float:
    def linear(channel: float) -> float:
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    red, green, blue = (linear(channel) for channel in color)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(first: str, second: str) -> float:
    light, dark = sorted((relative_luminance(rgb(first)), relative_luminance(rgb(second))), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def simulate(hex_color: str, deficiency: str) -> tuple[float, float, float]:
    # colorspacious exposes the simulation as a conversion *from* the CVD
    # space into display RGB. Using the reverse direction produces unstable,
    # out-of-gamut values at severity 100 and would collapse distinct colours
    # during clipping.
    converted = cspace_convert(
        rgb(hex_color),
        {"name": "sRGB1+CVD", "cvd_type": deficiency, "severity": 100},
        "sRGB1",
    )
    return tuple(max(0.0, min(1.0, float(channel))) for channel in converted)


def lab_distance(first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
    first_lab = cspace_convert(first, "sRGB1", "CIELab")
    second_lab = cspace_convert(second, "sRGB1", "CIELab")
    return math.dist(first_lab, second_lab)


def marker(passed: bool) -> str:
    return "PASS" if passed else "FAIL"


def validate_profile(profile: str, tokens: dict[str, str]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    contrast_rows: list[dict[str, object]] = []
    for state in ("success", "warning", "error", "inactive"):
        text_ratio = contrast(tokens[f"{state}Text"], tokens[f"{state}Surface"])
        contrast_rows.append({
            "profile": profile, "check": f"Texto {state} / superfície {state}",
            "ratio": text_ratio, "minimum": MIN_TEXT_CONTRAST, "passed": text_ratio >= MIN_TEXT_CONTRAST,
        })
        border_ratio = contrast(tokens[f"{state}Border"], tokens["surfaceSecondary"])
        contrast_rows.append({
            "profile": profile, "check": f"Borda {state} / superfície adjacente",
            "ratio": border_ratio, "minimum": MIN_COMPONENT_CONTRAST, "passed": border_ratio >= MIN_COMPONENT_CONTRAST,
        })

    state_rows: list[dict[str, object]] = []
    for deficiency in SIMULATIONS[profile]:
        for pair_name, first_name, second_name in STATE_PAIRS:
            first = simulate(tokens[first_name], deficiency)
            second = simulate(tokens[second_name], deficiency)
            delta_e = lab_distance(first, second)
            grayscale_delta = abs(relative_luminance(first) - relative_luminance(second))
            state_rows.append({
                "profile": profile, "simulation": deficiency, "pair": pair_name,
                "delta_e": delta_e, "grayscale_delta": grayscale_delta,
                "passed": delta_e >= MIN_DELTA_E and grayscale_delta >= MIN_GRAYSCALE_LUMINANCE_DELTA,
            })
    return contrast_rows, state_rows


def write_report(contrast_rows: list[dict[str, object]], state_rows: list[dict[str, object]]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    total = len(contrast_rows) + len(state_rows)
    failed = sum(not bool(row["passed"]) for row in contrast_rows + state_rows)
    lines = [
        "# Validação dos perfis cromáticos",
        "",
        "Relatório gerado por `tools/validate_color_profiles.py` a partir de `ui/ColorVisionProfiles.js`. ",
        "A mesma fonte de tokens é usada pelo tema QML e pelos eventos/registos renderizados em Python.",
        "",
        "## Critérios",
        "",
        f"- Contraste de texto normal: mínimo **{MIN_TEXT_CONTRAST:.1f}:1** (WCAG 2.2 SC 1.4.3).",
        f"- Contraste de componentes e bordas: mínimo **{MIN_COMPONENT_CONTRAST:.1f}:1** (WCAG 2.2 SC 1.4.11).",
        f"- Separação perceptiva após simulação: DeltaE CIELAB euclidiano mínimo **{MIN_DELTA_E:.0f}**.",
        f"- Separação em escala de cinzentos: diferença de luminância relativa mínima **{MIN_GRAYSCALE_LUMINANCE_DELTA:.2f}**.",
        "- Simulação: modelo Machado et al. 2009, via `colorspacious`, severidade 100.",
        "",
        f"**Resultado global:** {marker(failed == 0)} ({total - failed}/{total} verificações aprovadas)",
        "",
        "## Contraste WCAG",
        "",
        "| Perfil | Verificação | Contraste | Mínimo | Resultado |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    lines.extend(
        f"| {row['profile']} | {row['check']} | {row['ratio']:.2f}:1 | {row['minimum']:.1f}:1 | {marker(bool(row['passed']))} |"
        for row in contrast_rows
    )
    lines.extend([
        "",
        "## Estados após simulação",
        "",
        "| Perfil | Simulação | Par de estados | DeltaE | Delta de cinzentos | Resultado |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ])
    lines.extend(
        f"| {row['profile']} | {row['simulation']} | {row['pair']} | {row['delta_e']:.1f} | {row['grayscale_delta']:.3f} | {marker(bool(row['passed']))} |"
        for row in state_rows
    )
    lines.extend([
        "",
        "## Leitura visual",
        "",
        "A janela **Perfis de Daltonismo** inclui uma matriz de estados de exemplo. A demonstração mantém o símbolo e o texto do estado, para que nenhum estado dependa apenas da cor.",
        "",
        "Este relatório é uma verificação técnica de design e não um diagnóstico de visão cromática nem uma certificação legal.",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    contrast_rows: list[dict[str, object]] = []
    state_rows: list[dict[str, object]] = []
    for profile, tokens in all_profile_tokens().items():
        profile_contrast, profile_states = validate_profile(profile, tokens)
        contrast_rows.extend(profile_contrast)
        state_rows.extend(profile_states)
    write_report(contrast_rows, state_rows)
    failed = [row for row in contrast_rows + state_rows if not bool(row["passed"])]
    print(f"Report written to {REPORT_PATH}")
    print(f"{len(contrast_rows) + len(state_rows) - len(failed)}/{len(contrast_rows) + len(state_rows)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
