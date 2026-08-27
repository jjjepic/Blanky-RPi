import QtQuick

QtObject {
    id: theme

    property string mode: "dark"
    property string colorVisionProfile: "universal"
    property real readabilityScale: 1.0
    property real customHue: 205.0
    property real customBrightness: 46.0
    property real customContrast: 88.0
    readonly property bool dark: mode !== "light"
    readonly property bool colorIndependent: mode === "monochrome"
    readonly property bool highContrast: mode === "high_contrast"
    readonly property real textScale: readabilityScale
    readonly property real controlScale: 1.0 + (readabilityScale - 1.0) * 0.55
    readonly property real spacingScale: 1.0 + (readabilityScale - 1.0) * 0.60

    function profileColor(universal, protan, deutan, tritan) {
        if (colorVisionProfile === "protan")
            return protan
        if (colorVisionProfile === "deutan")
            return deutan
        if (colorVisionProfile === "tritan")
            return tritan
        return universal
    }

    readonly property color background: mode === "custom" ? Qt.hsla(customHue / 360, 0.38, 0.06 + customBrightness / 100 * 0.24, 1)
        : mode === "light" ? "#d7e3ea"
        : mode === "high_contrast" ? "#000000"
        : mode === "colorblind" ? "#07121d"
        : mode === "monochrome" ? "#101010" : "#02060d"
    readonly property color backgroundTop: mode === "custom" ? Qt.lighter(background, 1.22)
        : mode === "light" ? "#e3edf2"
        : mode === "high_contrast" ? "#080808"
        : mode === "colorblind" ? "#0b1c2b"
        : mode === "monochrome" ? "#1b1b1b" : "#03101b"
    readonly property color surface: mode === "custom" ? Qt.lighter(background, 1.16)
        : mode === "light" ? "#c5d8e4"
        : mode === "high_contrast" ? "#111111"
        : mode === "colorblind" ? "#0d2030"
        : mode === "monochrome" ? "#181818" : "#091722"
    readonly property color surfaceSecondary: mode === "custom" ? Qt.lighter(background, 1.08)
        : mode === "light" ? "#e3edf2"
        : mode === "high_contrast" ? "#050505"
        : mode === "colorblind" ? "#091825"
        : mode === "monochrome" ? "#252525" : "#07111a"
    readonly property color textPrimary: mode === "custom" ? Qt.hsla(customHue / 360, 0.08, 0.45 + customContrast / 100 * 0.50, 1)
        : mode === "light" ? "#16384c" : "#f2f7fb"
    readonly property color textSecondary: mode === "custom" ? Qt.hsla(customHue / 360, 0.18, 0.34 + customContrast / 100 * 0.38, 1)
        : mode === "light" ? "#386b85"
        : mode === "high_contrast" ? "#d2d2d2"
        : mode === "monochrome" ? "#c5c5c5" : "#a8d8ee"
    readonly property color textDisabled: mode === "custom" ? Qt.hsla(customHue / 360, 0.12, 0.38 + customContrast / 100 * 0.25, 1)
        : mode === "light" ? "#526e7d" : "#8fa8b8"
    readonly property color border: mode === "custom" ? Qt.hsla(customHue / 360, 0.65, 0.40 + customContrast / 100 * 0.18, 1)
        : mode === "light" ? "#5f98b8"
        : mode === "high_contrast" ? "#f2f2f2"
        : mode === "monochrome" ? "#c8c8c8" : "#1f6fa8"
    readonly property color borderStrong: mode === "custom" ? Qt.lighter(border, 1.25)
        : mode === "light" ? "#0d5d8b"
        : mode === "high_contrast" ? "#ffffff"
        : mode === "monochrome" ? "#ffffff" : "#4ab7e8"
    readonly property color accent: mode === "custom" ? Qt.hsla(customHue / 360, 0.82, 0.62, 1)
        : mode === "light" ? "#0d5d8b"
        : mode === "high_contrast" ? "#00e5ff"
        : mode === "colorblind" ? profileColor("#4fc3f7", "#55c8f2", "#5ab4e5", "#d6b5ff")
        : mode === "monochrome" ? "#ffffff" : "#63cbff"
    readonly property color success: mode === "custom" ? accent
        : mode === "light" ? "#147a3d"
        : mode === "high_contrast" ? "#00e5ff"
        : mode === "colorblind" ? profileColor("#4fc3f7", "#55c8f2", "#5ab4e5", "#f3f6fa")
        : mode === "monochrome" ? "#f2f2f2" : "#48d66b"
    readonly property color warning: mode === "custom" ? Qt.hsla(((customHue + 45) % 360) / 360, 0.78, 0.64, 1)
        : mode === "light" ? "#8a5b00"
        : mode === "high_contrast" ? "#ffd740"
        : mode === "colorblind" ? profileColor("#ffd166", "#ffe066", "#f6c445", "#ffad8a")
        : mode === "monochrome" ? "#d8d8d8" : "#f8c25d"
    readonly property color error: mode === "custom" ? Qt.hsla(((customHue + 320) % 360) / 360, 0.78, 0.65, 1)
        : mode === "light" ? "#b32635"
        : mode === "high_contrast" ? "#ff8a65"
        : mode === "colorblind" ? profileColor("#ff9f43", "#ffb000", "#f28e2b", "#ff5f8a")
        : mode === "monochrome" ? "#ffffff" : "#ff6b6b"
    readonly property color inactive: mode === "custom" ? Qt.hsla(customHue / 360, 0.16, 0.55, 1)
        : mode === "light" ? "#526e7d"
        : mode === "high_contrast" ? "#c0c0c0"
        : mode === "colorblind" ? profileColor("#b6c4cf", "#c7d0d8", "#c6d0d8", "#cad0d8")
        : mode === "monochrome" ? "#a8a8a8" : "#8fa8b8"
    readonly property color selected: mode === "custom" ? accent
        : mode === "light" ? "#146f9e"
        : mode === "high_contrast" ? "#00e5ff"
        : mode === "colorblind" ? profileColor("#4fc3f7", "#55c8f2", "#5ab4e5", "#d6b5ff")
        : mode === "monochrome" ? "#ffffff" : "#9dd9ff"
    readonly property color successSurface: mode === "custom" ? Qt.lighter(surfaceSecondary, 1.18)
        : mode === "light" ? "#d7f4df"
        : mode === "high_contrast" ? "#111111"
        : mode === "colorblind" ? profileColor("#102a3c", "#102b3d", "#102a3c", "#27303c")
        : mode === "monochrome" ? "#252525" : "#0c3423"
    readonly property color infoSurface: mode === "custom" ? Qt.lighter(surfaceSecondary, 1.14)
        : mode === "light" ? "#d9effa"
        : mode === "high_contrast" ? "#111111"
        : mode === "colorblind" ? profileColor("#102a3c", "#102b3d", "#102a3c", "#2b2339")
        : mode === "monochrome" ? "#252525" : "#0b3040"
    readonly property color warningSurface: mode === "custom" ? Qt.lighter(surfaceSecondary, 1.10)
        : mode === "light" ? "#fff0c5"
        : mode === "high_contrast" ? "#111111"
        : mode === "colorblind" ? profileColor("#2d2615", "#332d12", "#352b12", "#3a231a")
        : mode === "monochrome" ? "#252525" : "#382c0d"
    readonly property color errorSurface: mode === "custom" ? Qt.lighter(surfaceSecondary, 1.06)
        : mode === "light" ? "#ffe0e3"
        : mode === "high_contrast" ? "#111111"
        : mode === "colorblind" ? profileColor("#321f18", "#35280d", "#35220f", "#361a29")
        : mode === "monochrome" ? "#252525" : "#38161d"

    // Semantic aliases keep state meaning independent from a concrete palette.
    readonly property color successText: success
    readonly property color successBorder: success
    readonly property color warningText: warning
    readonly property color warningBorder: warning
    readonly property color errorText: error
    readonly property color errorBorder: error
    readonly property color inactiveText: inactive
    readonly property color inactiveBorder: inactive
    readonly property color information: accent
    readonly property color focus: selected
}
