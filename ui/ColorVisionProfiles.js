.pragma library

// This object is intentionally JSON-compatible. The QML theme and the Python
// accessibility validator load the same semantic tokens from this source.
var PROFILE_TOKENS = {
    "universal": {
        "background": "#07121d", "backgroundTop": "#0b1c2b",
        "surface": "#0d2030", "surfaceSecondary": "#091825",
        "textPrimary": "#f2f7fb", "textSecondary": "#a8d8ee", "textDisabled": "#b6c4cf",
        "border": "#1f6fa8", "borderStrong": "#4ab7e8",
        "accent": "#4fc3f7", "success": "#4fc3f7", "warning": "#ffd166",
        "error": "#d85b68", "inactive": "#7d8a94", "selected": "#4fc3f7",
        "information": "#4fc3f7", "focus": "#4fc3f7",
        "successText": "#4fc3f7", "successBorder": "#4fc3f7", "successSurface": "#102a3c",
        "warningText": "#ffd166", "warningBorder": "#ffd166", "warningSurface": "#2d2615",
        "errorText": "#d85b68", "errorBorder": "#d85b68", "errorSurface": "#1d1218",
        "inactiveText": "#7d8a94", "inactiveBorder": "#7d8a94", "inactiveSurface": "#111c27",
        "infoSurface": "#102a3c"
    },
    "protan": {
        "background": "#07121d", "backgroundTop": "#0b1c2b",
        "surface": "#0d2030", "surfaceSecondary": "#091825",
        "textPrimary": "#f2f7fb", "textSecondary": "#b5ddec", "textDisabled": "#c7d0d8",
        "border": "#1f6fa8", "borderStrong": "#55c8f2",
        "accent": "#55c8f2", "success": "#55c8f2", "warning": "#ffe066",
        "error": "#d85b68", "inactive": "#7d8a94", "selected": "#d6b5ff",
        "information": "#55c8f2", "focus": "#d6b5ff",
        "successText": "#55c8f2", "successBorder": "#55c8f2", "successSurface": "#102b3d",
        "warningText": "#ffe066", "warningBorder": "#ffe066", "warningSurface": "#332d12",
        "errorText": "#d85b68", "errorBorder": "#d85b68", "errorSurface": "#1d1218",
        "inactiveText": "#7d8a94", "inactiveBorder": "#7d8a94", "inactiveSurface": "#111c27",
        "infoSurface": "#14253a"
    },
    "deutan": {
        "background": "#07121d", "backgroundTop": "#0b1c2b",
        "surface": "#0d2030", "surfaceSecondary": "#091825",
        "textPrimary": "#f2f7fb", "textSecondary": "#b5d4e6", "textDisabled": "#c6d0d8",
        "border": "#1f6fa8", "borderStrong": "#5ab4e5",
        "accent": "#5ab4e5", "success": "#5ab4e5", "warning": "#f6c445",
        "error": "#d85b68", "inactive": "#7d8a94", "selected": "#c084fc",
        "information": "#5ab4e5", "focus": "#c084fc",
        "successText": "#5ab4e5", "successBorder": "#5ab4e5", "successSurface": "#102a3c",
        "warningText": "#f6c445", "warningBorder": "#f6c445", "warningSurface": "#352b12",
        "errorText": "#d85b68", "errorBorder": "#d85b68", "errorSurface": "#1d1218",
        "inactiveText": "#7d8a94", "inactiveBorder": "#7d8a94", "inactiveSurface": "#111c27",
        "infoSurface": "#13263a"
    },
    "tritan": {
        "background": "#07121d", "backgroundTop": "#0b1c2b",
        "surface": "#0d2030", "surfaceSecondary": "#091825",
        "textPrimary": "#f3f6fa", "textSecondary": "#d6c6ed", "textDisabled": "#cad0d8",
        "border": "#7762a9", "borderStrong": "#d6b5ff",
        "accent": "#d6b5ff", "success": "#f3f6fa", "warning": "#ffad8a",
        "error": "#ff5f8a", "inactive": "#7d8a94", "selected": "#d6b5ff",
        "information": "#d6b5ff", "focus": "#d6b5ff",
        "successText": "#f3f6fa", "successBorder": "#f3f6fa", "successSurface": "#27303c",
        "warningText": "#ffad8a", "warningBorder": "#ffad8a", "warningSurface": "#3a231a",
        "errorText": "#ff5f8a", "errorBorder": "#ff5f8a", "errorSurface": "#361a29",
        "inactiveText": "#7d8a94", "inactiveBorder": "#7d8a94", "inactiveSurface": "#151d26",
        "infoSurface": "#2b2339"
    }
}

function profile(id) {
    return PROFILE_TOKENS[id] || PROFILE_TOKENS.universal
}
