import QtQuick
import "ColorVisionProfiles.js" as ColorVisionProfiles

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

    readonly property var colorVisionTokens: ColorVisionProfiles.profile(colorVisionProfile)

    readonly property color background: mode === "custom" ? Qt.hsla(customHue / 360, 0.38, 0.06 + customBrightness / 100 * 0.24, 1)
        : mode === "light" ? "#d7e3ea"
        : mode === "high_contrast" ? "#000000"
        : mode === "colorblind" ? colorVisionTokens.background
        : mode === "monochrome" ? "#101010" : "#02060d"
    readonly property color backgroundTop: mode === "custom" ? Qt.lighter(background, 1.22)
        : mode === "light" ? "#e3edf2"
        : mode === "high_contrast" ? "#080808"
        : mode === "colorblind" ? colorVisionTokens.backgroundTop
        : mode === "monochrome" ? "#1b1b1b" : "#03101b"
    readonly property color surface: mode === "custom" ? Qt.lighter(background, 1.16)
        : mode === "light" ? "#c5d8e4"
        : mode === "high_contrast" ? "#111111"
        : mode === "colorblind" ? colorVisionTokens.surface
        : mode === "monochrome" ? "#181818" : "#091722"
    readonly property color surfaceSecondary: mode === "custom" ? Qt.lighter(background, 1.08)
        : mode === "light" ? "#e3edf2"
        : mode === "high_contrast" ? "#050505"
        : mode === "colorblind" ? colorVisionTokens.surfaceSecondary
        : mode === "monochrome" ? "#252525" : "#07111a"
    readonly property color textPrimary: mode === "custom" ? Qt.hsla(customHue / 360, 0.08, 0.45 + customContrast / 100 * 0.50, 1)
        : mode === "light" ? "#16384c" : mode === "colorblind" ? colorVisionTokens.textPrimary : "#f2f7fb"
    readonly property color textSecondary: mode === "custom" ? Qt.hsla(customHue / 360, 0.18, 0.34 + customContrast / 100 * 0.38, 1)
        : mode === "light" ? "#386b85"
        : mode === "high_contrast" ? "#d2d2d2"
        : mode === "colorblind" ? colorVisionTokens.textSecondary : mode === "monochrome" ? "#c5c5c5" : "#a8d8ee"
    readonly property color textDisabled: mode === "custom" ? Qt.hsla(customHue / 360, 0.12, 0.38 + customContrast / 100 * 0.25, 1)
        : mode === "light" ? "#526e7d" : mode === "colorblind" ? colorVisionTokens.textDisabled : "#8fa8b8"
    readonly property color border: mode === "custom" ? Qt.hsla(customHue / 360, 0.65, 0.40 + customContrast / 100 * 0.18, 1)
        : mode === "light" ? "#5f98b8"
        : mode === "high_contrast" ? "#f2f2f2"
        : mode === "colorblind" ? colorVisionTokens.border : mode === "monochrome" ? "#c8c8c8" : "#1f6fa8"
    readonly property color borderStrong: mode === "custom" ? Qt.lighter(border, 1.25)
        : mode === "light" ? "#0d5d8b"
        : mode === "high_contrast" ? "#ffffff"
        : mode === "colorblind" ? colorVisionTokens.borderStrong : mode === "monochrome" ? "#ffffff" : "#4ab7e8"
    readonly property color accent: mode === "custom" ? Qt.hsla(customHue / 360, 0.82, 0.62, 1)
        : mode === "light" ? "#0d5d8b"
        : mode === "high_contrast" ? "#00e5ff"
        : mode === "colorblind" ? colorVisionTokens.accent
        : mode === "monochrome" ? "#ffffff" : "#63cbff"
    readonly property color success: mode === "custom" ? accent
        : mode === "light" ? "#147a3d"
        : mode === "high_contrast" ? "#00e5ff"
        : mode === "colorblind" ? colorVisionTokens.success
        : mode === "monochrome" ? "#f2f2f2" : "#48d66b"
    readonly property color warning: mode === "custom" ? Qt.hsla(((customHue + 45) % 360) / 360, 0.78, 0.64, 1)
        : mode === "light" ? "#8a5b00"
        : mode === "high_contrast" ? "#ffd740"
        : mode === "colorblind" ? colorVisionTokens.warning
        : mode === "monochrome" ? "#d8d8d8" : "#f8c25d"
    readonly property color error: mode === "custom" ? Qt.hsla(((customHue + 320) % 360) / 360, 0.78, 0.65, 1)
        : mode === "light" ? "#b32635"
        : mode === "high_contrast" ? "#ff8a65"
        : mode === "colorblind" ? colorVisionTokens.error
        : mode === "monochrome" ? "#ffffff" : "#ff6b6b"
    readonly property color inactive: mode === "custom" ? Qt.hsla(customHue / 360, 0.16, 0.55, 1)
        : mode === "light" ? "#526e7d"
        : mode === "high_contrast" ? "#c0c0c0"
        : mode === "colorblind" ? colorVisionTokens.inactive
        : mode === "monochrome" ? "#a8a8a8" : "#8fa8b8"
    readonly property color selected: mode === "custom" ? accent
        : mode === "light" ? "#146f9e"
        : mode === "high_contrast" ? "#00e5ff"
        : mode === "colorblind" ? colorVisionTokens.selected
        : mode === "monochrome" ? "#ffffff" : "#9dd9ff"
    readonly property color successSurface: mode === "custom" ? Qt.lighter(surfaceSecondary, 1.18)
        : mode === "light" ? "#d7f4df"
        : mode === "high_contrast" ? "#111111"
        : mode === "colorblind" ? colorVisionTokens.successSurface
        : mode === "monochrome" ? "#252525" : "#0c3423"
    readonly property color infoSurface: mode === "custom" ? Qt.lighter(surfaceSecondary, 1.14)
        : mode === "light" ? "#d9effa"
        : mode === "high_contrast" ? "#111111"
        : mode === "colorblind" ? colorVisionTokens.infoSurface
        : mode === "monochrome" ? "#252525" : "#0b3040"
    readonly property color warningSurface: mode === "custom" ? Qt.lighter(surfaceSecondary, 1.10)
        : mode === "light" ? "#fff0c5"
        : mode === "high_contrast" ? "#111111"
        : mode === "colorblind" ? colorVisionTokens.warningSurface
        : mode === "monochrome" ? "#252525" : "#382c0d"
    readonly property color errorSurface: mode === "custom" ? Qt.lighter(surfaceSecondary, 1.06)
        : mode === "light" ? "#ffe0e3"
        : mode === "high_contrast" ? "#111111"
        : mode === "colorblind" ? colorVisionTokens.errorSurface
        : mode === "monochrome" ? "#252525" : "#38161d"

    // Semantic aliases keep state meaning independent from a concrete palette.
    readonly property color successText: mode === "colorblind" ? colorVisionTokens.successText : success
    readonly property color successBorder: mode === "colorblind" ? colorVisionTokens.successBorder : success
    readonly property color warningText: mode === "colorblind" ? colorVisionTokens.warningText : warning
    readonly property color warningBorder: mode === "colorblind" ? colorVisionTokens.warningBorder : warning
    readonly property color errorText: mode === "colorblind" ? colorVisionTokens.errorText : error
    readonly property color errorBorder: mode === "colorblind" ? colorVisionTokens.errorBorder : error
    readonly property color inactiveText: mode === "colorblind" ? colorVisionTokens.inactiveText : inactive
    readonly property color inactiveBorder: mode === "colorblind" ? colorVisionTokens.inactiveBorder : inactive
    readonly property color information: mode === "colorblind" ? colorVisionTokens.information : accent
    readonly property color focus: mode === "colorblind" ? colorVisionTokens.focus : selected
}
