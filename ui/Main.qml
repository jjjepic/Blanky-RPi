import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "Translations.js" as I18n
import "ColorVisionProfiles.js" as ColorVisionProfiles

ApplicationWindow {
    id: root
    visible: true
    width: 1540
    height: 860
    minimumWidth: 1540
    minimumHeight: 850
    title: "Blanky"

    ThemePalette {
        id: theme
        mode: blanky.appearanceMode
        colorVisionProfile: blanky.colorVisionProfile
        readabilityScale: blanky.appearanceTextScale
        customHue: blanky.customHue
        customBrightness: blanky.customBrightness
        customContrast: blanky.customContrast
    }
    readonly property bool dark: theme.dark
    readonly property color bgColor: theme.background
    readonly property color panelColor: theme.surface
    readonly property color panelAltColor: theme.surfaceSecondary
    readonly property color borderColor: theme.border
    readonly property color textColor: theme.textPrimary
    readonly property color mutedText: theme.textSecondary
    readonly property color accentColor: theme.accent
    readonly property color successColor: theme.success
    readonly property color warningColor: theme.warning
    readonly property color errorColor: theme.error
    readonly property color inactiveColor: theme.inactive
    readonly property real textScale: theme.textScale
    readonly property real controlScale: theme.controlScale
    readonly property real spacingScale: theme.spacingScale
    property var ttsVoiceModel: blanky.ttsVoiceOptions ? blanky.ttsVoiceOptions.split("|") : []
    property var stateMap: ({})
    property var commStateMap: ({})
    property bool popupBackdropVisible: false
    property bool systemTransitionActive: false
    property string systemTransitionAction: ""
    property int systemTransitionProgress: 0
    property double systemTransitionStartedAt: 0
    property string textBotMode: "online"
    property var audioManualOverrides: ({})
    readonly property int rightPanelWidth: 660

    function formatPercent(value) {
        return Math.round(Number(value) * 100) + "%"
    }

    function formatFixed(value, digits) {
        return Number(value).toFixed(digits)
    }

    function eventsHeaderText() {
        if (blanky.language === "en")
            return "ID    | Time     | Source     | Command            | State     | Description"
        return "ID    | Hora     | Origem     | Comando            | Estado    | Descri\u00e7\u00e3o"
    }

    function eventsHeaderDivider() {
        return "----- | -------- | ---------- | ------------------ | --------- | --------------------------------------------------------"
    }

    function t(key, values) {
        return I18n.text(blanky.language, key, values)
    }

    function appearanceIcon() {
        if (blanky.appearanceMode === "light")
            return "\u2600"
        if (blanky.appearanceMode === "high_contrast")
            return "\u25D0"
        if (blanky.appearanceMode === "colorblind")
            return "\u25C9"
        if (blanky.appearanceMode === "monochrome")
            return "\u25FB"
        if (blanky.appearanceMode === "custom")
            return "\u2699"
        return "\u263E"
    }

    function logoSource() {
        if (blanky.appearanceMode === "light")
            return "../assets/blanky_logo_light.png"
        if (blanky.appearanceMode === "high_contrast")
            return "../assets/blanky_logo_high_contrast.png"
        if (blanky.appearanceMode === "colorblind")
            return "../assets/blanky_logo_colorblind.png"
        if (blanky.appearanceMode === "monochrome")
            return "../assets/blanky_logo_monochrome.png"
        // Custom keeps the dark logo as a neutral base while the interface palette is personalised.
        return "../assets/blanky_logo_dark.png"
    }

    function appearanceOptions() {
        return [
            { id: "dark", icon: "☾", tone: "#91a1b5", title: t("darkAppearance"), description: blanky.language === "pt" ? "Interface escura atual." : "Current dark interface." },
            { id: "light", icon: "☀", tone: "#f8c25d", title: t("lightAppearance"), description: blanky.language === "pt" ? "Interface clara e equilibrada." : "Balanced light interface." },
            { id: "high_contrast", icon: "◐", tone: "#00e5ff", title: t("highContrast"), description: blanky.language === "pt" ? "Máxima legibilidade e contornos fortes." : "Maximum legibility and strong borders." },
            { id: "colorblind", icon: "◉", tone: theme.accent, title: t("colorblindUniversal"), description: t("colorVisionProfileSelected", { profile: colorVisionProfileName(blanky.colorVisionProfile) }) },
            { id: "monochrome", icon: "◻", tone: "#d7d7d7", title: t("monochrome"), description: blanky.language === "pt" ? "Estados compreensíveis sem depender da cor." : "States that do not depend on colour." },
            { id: "custom", icon: "⚙", tone: "#cf8cff", title: t("customAppearance"), description: t("customAppearanceDescription") }
        ]
    }

    function colorVisionProfileName(profile) {
        if (profile === "protan")
            return t("colorVisionProtan")
        if (profile === "deutan")
            return t("colorVisionDeutan")
        if (profile === "tritan")
            return t("colorVisionTritan")
        return t("colorVisionUniversal")
    }

    function colorVisionProfiles() {
        return [
            { id: "universal", icon: "◉", tone: ColorVisionProfiles.profile("universal").information, title: t("colorVisionUniversal"), description: t("colorVisionUniversalDescription"), recommended: true },
            { id: "protan", icon: "P", tone: ColorVisionProfiles.profile("protan").information, title: t("colorVisionProtan"), description: t("colorVisionProtanDescription"), recommended: false },
            { id: "deutan", icon: "D", tone: ColorVisionProfiles.profile("deutan").information, title: t("colorVisionDeutan"), description: t("colorVisionDeutanDescription"), recommended: false },
            { id: "tritan", icon: "T", tone: ColorVisionProfiles.profile("tritan").information, title: t("colorVisionTritan"), description: t("colorVisionTritanDescription"), recommended: false }
        ]
    }

    function audioSettingIsEditable(key) {
        return blanky.audioSettingsMode === "manual" || audioManualOverrides[key] === true
    }

    function unlockAudioSetting(key) {
        var overrides = ({})
        for (var existingKey in audioManualOverrides)
            overrides[existingKey] = audioManualOverrides[existingKey]
        overrides[key] = true
        audioManualOverrides = overrides
    }

    function selectAudioProfile(profile) {
        audioManualOverrides = ({})
        blanky.setAudioInputPreset(profile)
    }

    function selectAudioMode(mode) {
        audioManualOverrides = ({})
        blanky.setAudioSettingsMode(mode)
    }

    function toggleVolumePopover() {
        if (volumePopover.opened)
            volumePopover.close()
        else
            volumePopover.open()
    }

    function beginSystemTransition(action) {
        if (systemTransitionActive)
            return

        volumePopover.close()
        ttsSpeedPopover.close()
        systemTransitionAction = action
        systemTransitionProgress = 0
        systemTransitionStartedAt = Date.now()
        systemTransitionActive = true
        systemTransitionTimer.start()
    }

    function finishSystemTransition() {
        systemTransitionProgress = 100
        systemTransitionTimer.stop()
        if (systemTransitionAction === "shutdown") {
            blanky.shutdownApplication()
            return
        }

        blanky.resetSystem()
        systemTransitionActive = false
        systemTransitionAction = ""
    }

    function volumeGlyph() {
        if (!blanky.soundEnabled || blanky.soundVolume <= 0.01)
            return "\uD83D\uDD07"
        if (blanky.soundVolume < 0.34)
            return "\uD83D\uDD08"
        if (blanky.soundVolume < 0.67)
            return "\uD83D\uDD09"
        return "\uD83D\uDD0A"
    }

    function ttsSpeedLabel() {
        if (blanky.ttsSpeed < 0.9)
            return t("slow")
        if (blanky.ttsSpeed > 1.1)
            return t("fast")
        return t("normal")
    }

    function ttsSpeedGlyph() {
        if (blanky.ttsSpeed < 0.9)
            return "\uD83D\uDC22"
        if (blanky.ttsSpeed > 1.1)
            return "\u26A1"
        return "\u25B6"
    }

    function voiceLabel() {
        return voiceName(blanky.ttsVoice)
    }

    function voiceName(voice) {
        voice = voice || ""
        if (!voice)
            return ""
        return voice.charAt(0).toUpperCase() + voice.slice(1).toLowerCase()
    }

    function commandHelpGroups() {
        var pt = blanky.language === "pt"
        return [
            { title: pt ? "Sistema" : "System", commands: [
                { icon: "\u25B6", color: "#48d66b", title: pt ? "Iniciar sistema" : "Start system", code: "START", input: pt ? "iniciar" : "start", description: pt ? "Inicia o funcionamento do sistema." : "Starts system operation.", examples: pt ? "iniciar · arrancar · come\u00e7ar" : "start · begin · launch" },
                { icon: "\u23F9", color: "#ff6b6b", title: pt ? "Parar sistema" : "Stop system", code: "STOP", input: pt ? "parar" : "stop", description: pt ? "Para o sistema e rep\u00f5e os componentes." : "Stops the system and resets components.", examples: pt ? "parar · pausar · terminar" : "stop · halt · pause" }
            ]},
            { title: pt ? "Modos" : "Modes", commands: [
                { icon: "\u26A1", color: "#f8c25d", title: pt ? "Modo r\u00e1pido" : "Fast mode", code: "MODE_FAST", input: pt ? "modo r\u00e1pido" : "fast mode", description: pt ? "Seleciona a opera\u00e7\u00e3o r\u00e1pida." : "Selects fast operation.", examples: pt ? "modo r\u00e1pido · alta velocidade · acelerado" : "fast mode · quick mode · high speed" },
                { icon: "\uD83C\uDFAF", color: "#63cbff", title: pt ? "Modo ideal" : "Ideal mode", code: "MODE_IDEAL", input: pt ? "modo ideal" : "ideal mode", description: pt ? "Seleciona a opera\u00e7\u00e3o ideal." : "Selects ideal operation.", examples: pt ? "modo ideal · modo auto · modo normal" : "ideal mode · auto mode · normal mode" },
                { icon: "\uD83D\uDD79", color: "#b7f7d4", title: pt ? "Modo manual" : "Manual mode", code: "MODE_MANUAL", input: pt ? "modo manual" : "manual mode", description: pt ? "Ativa os controlos manuais." : "Enables manual controls.", examples: pt ? "modo manual · opera\u00e7\u00e3o manual · manual" : "manual mode · operator mode · manual" },
                { icon: "\u21C4", color: "#9dd9ff", title: pt ? "Trocar modo" : "Change mode", code: "MODE_UNSPEC", input: pt ? "trocar modo" : "change mode", description: pt ? "Permite escolher outro modo." : "Allows selecting another mode.", examples: pt ? "trocar modo · mudar modo · alterar modo" : "change mode · switch mode · set mode" }
            ]},
            { title: pt ? "Motores" : "Motors", commands: [
                { icon: "\u2699", color: "#63cbff", title: pt ? "Controlar motores" : "Control motors", code: "MOTOR_n_ON / MOTOR_n_OFF", input: pt ? "ligar motor 1" : "turn on motor 1", description: pt ? "Liga ou desliga o motor indicado." : "Turns the selected motor on or off.", examples: pt ? "ligar motor 1 · desligar motor 2 · ativar motor 3" : "turn on motor 1 · disable motor 2 · start motor 3" }
            ]},
            { title: pt ? "Cilindros" : "Cylinders", commands: [
                { icon: "\u25B0", color: "#63cbff", title: pt ? "Controlar cilindros" : "Control cylinders", code: "CYL_X_EXTEND / CYL_X_RETRACT", input: pt ? "ligar cilindro A" : "turn on cylinder A", description: pt ? "Avan\u00e7a ou recolhe o cilindro indicado." : "Extends or retracts the selected cylinder.", examples: pt ? "avan\u00e7ar cilindro A · recolher cilindro B · cilindro C recuar" : "extend cylinder A · retract cylinder B · cylinder C back" }
            ]},
            { title: pt ? "Luzes" : "Lights", commands: [
                { icon: "\u25CF", color: "#48d66b", title: pt ? "Luz verde" : "Green light", code: "GREEN_ON / GREEN_OFF", input: pt ? "ligar luz verde" : "turn on green light", description: pt ? "Liga ou desliga a luz verde." : "Turns the green light on or off.", examples: pt ? "ligar luz verde · apagar verde · ativar verde" : "turn on green light · switch green off · enable green" },
                { icon: "\u25CF", color: "#ff6b6b", title: pt ? "Luz vermelha" : "Red light", code: "RED_ON / RED_OFF", input: pt ? "ligar luz vermelha" : "turn on red light", description: pt ? "Liga ou desliga a luz vermelha." : "Turns the red light on or off.", examples: pt ? "ligar luz vermelha · apagar vermelha · desativar vermelho" : "turn on red light · switch red off · disable red" }
            ]},
            { title: pt ? "Rob\u00f4" : "Robot", commands: [
                { icon: "\uD83E\uDD16", color: "#b7f7d4", title: pt ? "Enviar rob\u00f4" : "Move robot", code: "ROBOT_TO_METAL / ROBOT_TO_NONMETAL", input: pt ? "rob\u00f4 vai metal" : "send robot to metal", description: pt ? "Envia o rob\u00f4 para metal ou n\u00e3o metal." : "Sends the robot to metal or non-metal.", examples: pt ? "rob\u00f4 para metal · mandar rob\u00f4 para n\u00e3o metal · rob\u00f4 vai para metal" : "robot to metal · send robot to non-metal · move robot to metal" }
            ]}
        ]
    }

    function sendTextBot() {
        var raw = eventsTextBotEditor.text.trim()
        if (!raw)
            return
        blanky.submitTextCommands(raw, textBotMode)
        eventsTextBotEditor.text = ""
        eventsTextBotEditor.forceActiveFocus()
    }

    function prepareTextBot(commandText) {
        eventsTextBotEditor.text = commandText
        eventsTextBotEditor.cursorPosition = commandText.length
        commandsPanel.close()
        eventsTextBotEditor.forceActiveFocus()
    }

    function chooseExportDestination(kind, format) {
        exportFileDialog.exportKind = kind
        exportFileDialog.exportFormat = format
        var now = new Date()
        var stamp = now.getFullYear().toString()
            + ("0" + (now.getMonth() + 1)).slice(-2)
            + ("0" + now.getDate()).slice(-2)
            + "_" + ("0" + now.getHours()).slice(-2)
            + ("0" + now.getMinutes()).slice(-2)
            + ("0" + now.getSeconds()).slice(-2)
        var prefix = kind === "audio" ? "blanky_diagnostico_audio_" : "blanky_eventos_"
        exportFileDialog.currentFile = blanky.defaultExportFolder.toString() + "/" + prefix + stamp + "." + format
        exportFileDialog.open()
    }

    function parseStateCompact(raw) {
        var out = {}
        var parts = String(raw || "").split("|")
        for (var i = 0; i < parts.length; i++) {
            var pair = parts[i].split("=")
            if (pair.length === 2)
                out[pair[0]] = Number(pair[1])
        }
        return out
    }

    function parseCommCompact(raw) {
        var out = {}
        var parts = String(raw || "").split("|")
        for (var i = 0; i < parts.length; i++) {
            var pair = parts[i].split("=")
            if (pair.length === 2)
                out[pair[0]] = pair[1]
        }
        return out
    }

    function stateValue(key) {
        return Number(root.stateMap[key] || 0)
    }

    function toggleCommand(key, onCommand, offCommand) {
        return root.stateValue(key) === 1 ? offCommand : onCommand
    }

    function toggleStateText(key, onText, offText) {
        return root.stateValue(key) === 1 ? onText : offText
    }

    function commState(key) {
        return root.commStateMap[key] || "checking"
    }

    function commStateText(state) {
        if (state === "connected")
            return t("connected")
        if (state === "communicating")
            return t("communicating")
        if (state === "standby")
            return t("standby")
        if (state === "silent")
            return t("noCommunication")
        if (state === "checking")
            return t("checking")
        if (state === "error")
            return t("error")
        return t("offline")
    }

    function commStateColor(state) {
        if (state === "connected")
            return root.successColor
        if (state === "communicating")
            return root.accentColor
        if (state === "standby")
            return root.inactiveColor
        if (state === "silent")
            return root.warningColor
        if (state === "checking")
            return root.inactiveColor
        return root.errorColor
    }

    function commStateGlyph(state) {
        if (state === "communicating")
            return "⇄"
        if (state === "standby")
            return "◷"
        if (state === "silent")
            return "◌"
        if (state === "error")
            return "⚠"
        if (state === "offline")
            return "×"
        return "●"
    }

    function voiceMood(voice) {
        return I18n.voiceMood(blanky.language, voice)
    }

    function voiceDescription(voice) {
        return I18n.voiceDescription(blanky.language, voice)
    }

    function scrollEventsToBottom() {
        eventsScroll.contentItem.contentY = Math.max(0, eventsContent.height - eventsScroll.availableHeight)
    }

    Connections {
        target: blanky
        function onStateCompactChanged() {
            root.stateMap = root.parseStateCompact(blanky.stateCompact)
        }
        function onCommStatusCompactChanged() {
            root.commStateMap = root.parseCommCompact(blanky.commStatusCompact)
        }
        function onTtsVoiceOptionsChanged() {
            root.ttsVoiceModel = blanky.ttsVoiceOptions ? blanky.ttsVoiceOptions.split("|") : []
        }
        function onMonitorEventsTextChanged() {
            eventsAutoscrollTimer.restart()
        }
        function onTextOnlineFallbackRequested() {
            root.textBotMode = "offline"
        }
    }

    Timer {
        id: eventsAutoscrollTimer
        interval: 1
        repeat: false
        onTriggered: root.scrollEventsToBottom()
    }

    Timer {
        id: systemTransitionTimer
        interval: 30
        repeat: true
        onTriggered: {
            var elapsed = Date.now() - root.systemTransitionStartedAt
            root.systemTransitionProgress = Math.min(100, Math.round((elapsed / 3000) * 100))
            if (root.systemTransitionProgress >= 100)
                root.finishSystemTransition()
        }
    }

    Component.onCompleted: {
        root.stateMap = root.parseStateCompact(blanky.stateCompact)
        root.commStateMap = root.parseCommCompact(blanky.commStatusCompact)
    }

    color: bgColor

    Item {
        id: dashboardLayer
        anchors.fill: parent

        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
            GradientStop { position: 0.0; color: theme.backgroundTop }
            GradientStop { position: 1.0; color: root.bgColor }
        }
    }

    ColumnLayout {
        id: mainColumn
        anchors.fill: parent
        anchors.margins: 18
        spacing: Math.round(12 * root.spacingScale)

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 50

            Row {
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                spacing: 7

                MenuActionButton {
                    iconText: root.appearanceIcon()
                    width: 50
                    height: 44
                    textPixelSize: 22
                    accentColor: root.accentColor
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: t("tooltipAppearance")
                    onClicked: appearancePanel.open()
                }

                MenuActionButton {
                    text: "\uD83C\uDDF5\uD83C\uDDF9"
                    width: 54
                    height: 44
                    textPixelSize: 20
                    accentColor: blanky.language === "pt" ? root.successColor : root.inactiveColor
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: blanky.language === "pt" ? "Portugu\u00eas" : "Portuguese"
                    onClicked: blanky.setLanguage("pt")
                }

                MenuActionButton {
                    text: "\uD83C\uDDEC\uD83C\uDDE7"
                    width: 54
                    height: 44
                    textPixelSize: 20
                    accentColor: blanky.language === "en" ? root.successColor : root.inactiveColor
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: blanky.language === "pt" ? "Ingl\u00eas" : "English"
                    onClicked: blanky.setLanguage("en")
                }

                MenuActionButton {
                    text: "?"
                    width: 54
                    height: 44
                    textPixelSize: 22
                    accentColor: root.accentColor
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: blanky.language === "pt" ? "Ajuda / Tutorial" : "Help / Tutorial"
                    onClicked: {
                        helpPanel.showHome()
                        helpPanel.open()
                    }
                }
            }

            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.verticalCenter: parent.verticalCenter
                width: 230
                height: 42
                color: root.panelColor
                border.color: root.borderColor
                border.width: 1
                radius: 10

                Label {
                    anchors.centerIn: parent
                    text: blanky.dateTimeText
                    color: root.textColor
                    font.pixelSize: 14
                    font.bold: true
                }
            }

            Row {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                spacing: 7

                MenuActionButton {
                    iconText: root.volumeGlyph()
                    width: 50
                    height: 44
                    textPixelSize: 22
                    accentColor: blanky.soundEnabled ? root.accentColor : root.inactiveColor
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: t("tooltipVolume")
                    onClicked: root.toggleVolumePopover()
                }

                MenuActionButton {
                    iconText: "\u2699"
                    width: 50
                    height: 44
                    textPixelSize: 21
                    accentColor: root.accentColor
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: t("tooltipSettings")
                    onClicked: settingsPanel.open()
                }

                MenuActionButton {
                    iconText: "\u21BB"
                    width: 50
                    height: 44
                    textPixelSize: 22
                    accentColor: root.warningColor
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: t("tooltipReset")
                    onClicked: root.beginSystemTransition("reset")
                }

                MenuActionButton {
                    iconText: "\u23FB"
                    width: 50
                    height: 44
                    textPixelSize: 21
                    accentColor: root.errorColor
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: t("tooltipShutdown")
                    onClicked: root.beginSystemTransition("shutdown")
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 14

            Item { Layout.fillWidth: true }

            Image {
                source: root.logoSource()
                Layout.preferredWidth: 58
                Layout.preferredHeight: 58
                fillMode: Image.PreserveAspectFit
                smooth: true
            }

            Label {
                text: "Blanky"
                color: root.accentColor
                font.pixelSize: 36
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
            }

            Item { Layout.fillWidth: true }
        }

        Rectangle {
            id: horizontalCommPanel
            Layout.fillWidth: true
            visible: false
            Layout.preferredHeight: 0
            Layout.maximumHeight: 0
            implicitHeight: 0
            color: root.panelColor
            border.color: root.borderColor
            border.width: 1
            radius: 12

            ColumnLayout {
                id: commColumn
                anchors.fill: parent
                anchors.margins: 11
                spacing: 9

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: root.borderColor
                    }

                    Label {
                        text: t("communications").toUpperCase()
                        color: root.dark ? "#82d6ff" : "#0d5d8b"
                        font.pixelSize: 15
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: root.borderColor
                    }
                }

                Flow {
                    id: commFlow
                    Layout.fillWidth: true
                    spacing: 8

                    Repeater {
                        model: [
                            { key: "microphone", icon: "🎙", label: t("microphone") },
                            { key: "mqtt_base", icon: "📡", label: t("mqttBase") },
                            { key: "mqtt_phone", icon: "📱", label: t("mqttPhone") },
                            { key: "opcua", icon: "🔗", label: t("opcua") },
                            { key: "wakeword", icon: "🎤", label: t("wakeWord") }
                        ]

                        Rectangle {
                            readonly property string state: root.commState(modelData.key)
                            width: Math.max(150, Math.floor((commFlow.width - 32) / 5))
                            height: 62
                            radius: 9
                            color: root.dark ? "#06121d" : "#e4edf2"
                            border.color: root.commStateColor(state)
                            border.width: 1

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                spacing: 8

                                Label {
                                    text: modelData.icon
                                    color: root.commStateColor(state)
                                    font.pixelSize: 18
                                    Layout.preferredWidth: 22
                                    horizontalAlignment: Text.AlignHCenter
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2

                                    Label {
                                        text: modelData.label.toUpperCase()
                                        color: root.mutedText
                                        font.pixelSize: 10
                                        font.bold: true
                                        elide: Text.ElideRight
                                        Layout.fillWidth: true
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 6

                                        Label {
                                            text: root.commStateGlyph(state)
                                            color: root.commStateColor(state)
                                            font.pixelSize: 16
                                            font.bold: true
                                        }

                                        Label {
                                            text: root.commStateText(state)
                                            color: root.textColor
                                    font.pixelSize: Math.round(12 * root.textScale)
                                            font.bold: true
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    visible: blanky.commText.length > 0
                    Layout.fillWidth: true
                    Layout.preferredHeight: visible ? 30 : 0
                    radius: 7
                    color: root.dark ? "#251015" : "#fff2f3"
                    border.color: "#d75b65"
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        spacing: 7

                        Label {
                            text: "⚠"
                            color: "#ff717b"
                            font.pixelSize: 16
                            font.bold: true
                        }

                        Label {
                            text: blanky.commText
                            color: root.textColor
                            font.pixelSize: 11
                            font.bold: true
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }

        Rectangle {
            id: statusPanel
            Layout.fillWidth: true
            Layout.rightMargin: root.rightPanelWidth + 12
            Layout.preferredHeight: 174
            color: root.panelColor
            border.color: root.borderColor
            border.width: 2
            radius: 16

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: Math.round(10 * root.spacingScale)

                Label {
                    text: blanky.statusText
                    color: root.accentColor
                    font.pixelSize: 22
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }

                Label {
                    text: t("response")
                    color: root.mutedText
                    font.pixelSize: 13
                    horizontalAlignment: Text.AlignHCenter
                    Layout.fillWidth: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: root.panelAltColor
                    border.color: root.borderColor
                    border.width: 1
                    radius: 12

                    Label {
                        anchors.centerIn: parent
                        width: parent.width - 24
                        text: blanky.recognizedText
                        wrapMode: Text.WordWrap
                        horizontalAlignment: Text.AlignHCenter
                        color: root.textColor
                        font.pixelSize: 18
                        font.bold: true
                    }
                }
            }
        }

        Rectangle {
            id: primaryControlsPanel
            Layout.fillWidth: true
            Layout.rightMargin: root.rightPanelWidth + 12
            color: root.panelColor
            border.color: root.borderColor
            border.width: 1
            radius: 14
            implicitHeight: actionControls.implicitHeight + 24

            RowLayout {
                id: actionControls
                anchors.fill: parent
                anchors.margins: 12
                spacing: 10

                MenuActionButton {
                    text: blanky.listening ? "\uD83D\uDD34 " + t("listening") : "\uD83C\uDFA4 " + t("listen")
                    enabled: !blanky.listening
                    Layout.fillWidth: true
                    Layout.preferredWidth: 155
                    Layout.minimumWidth: 135
                    Layout.preferredHeight: Math.round(44 * root.controlScale)
                    prominent: true
                    textPixelSize: 16
                    accentColor: root.successColor
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: t("tooltipListen")
                    onClicked: blanky.startVoice()
                }

                MenuActionButton {
                    iconText: "\uD83D\uDDE3"
                    labelText: t("voiceButton") + ": <b>" + root.voiceLabel() + "</b>"
                    Layout.fillWidth: true
                    Layout.preferredWidth: 170
                    Layout.minimumWidth: 150
                    Layout.preferredHeight: Math.round(44 * root.controlScale)
                    prominent: true
                    accentColor: root.warningColor
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: t("tooltipVoice")
                    onClicked: voicePanel.open()
                }

                MenuActionButton {
                    id: voiceSpeedButton
                    iconText: root.ttsSpeedGlyph()
                    labelText: t("voiceSpeed") + ": <b>" + root.ttsSpeedLabel() + "</b>"
                    Layout.fillWidth: true
                    Layout.preferredWidth: 205
                    Layout.minimumWidth: 175
                    Layout.preferredHeight: Math.round(44 * root.controlScale)
                    prominent: true
                    accentColor: root.accentColor
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: t("tooltipVoiceSpeed")
                    onClicked: ttsSpeedPopover.open()
                }

                MenuActionButton {
                    iconText: "\uD83D\uDD0A"
                    labelText: t("repeatTts")
                    enabled: blanky.canRepeatTts
                    Layout.fillWidth: true
                    Layout.preferredWidth: 135
                    Layout.minimumWidth: 115
                    Layout.preferredHeight: Math.round(44 * root.controlScale)
                    prominent: true
                    accentColor: root.successColor
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: t("tooltipRepeatTts")
                    onClicked: blanky.repeatLastTts()
                }

                MenuActionButton {
                    text: "\uD83E\uDDF9 " + t("clearInteraction")
                    Layout.fillWidth: true
                    Layout.preferredWidth: 110
                    Layout.minimumWidth: 95
                    Layout.preferredHeight: Math.round(44 * root.controlScale)
                    prominent: true
                    accentColor: root.borderColor
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: t("tooltipClearInteraction")
                    onClicked: blanky.clearInteraction()
                }

            }
        }

        Rectangle {
            id: workspacePanel
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "transparent"
            border.width: 0

            RowLayout {
                id: workspaceContent
                anchors.fill: parent
                anchors.leftMargin: 0
                anchors.rightMargin: 0
                anchors.topMargin: 10
                anchors.bottomMargin: 10
                spacing: 12

                Rectangle {
                    visible: false
                    Layout.fillHeight: true
                    Layout.minimumWidth: 0
                    Layout.preferredWidth: 0
                    Layout.maximumWidth: 0
                    color: root.panelColor
                    border.color: root.borderColor
                    border.width: 1
                    radius: 10

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: root.borderColor }
                            Label {
                                text: t("communications").toUpperCase()
                                color: root.dark ? "#82d6ff" : "#0d5d8b"
                                font.pixelSize: 14
                                font.bold: true
                            }
                            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: root.borderColor }
                        }

                        ScrollView {
                            id: sideCommScroll
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                            ScrollBar.vertical.policy: ScrollBar.AlwaysOn

                            Column {
                                width: Math.max(sideCommScroll.width - 18, 320)
                                spacing: 8

                                Repeater {
                                    model: [
                                        { key: "microphone", icon: "🎙", label: t("microphone") },
                                        { key: "mqtt_base", icon: "📡", label: t("mqttBase") },
                                        { key: "mqtt_phone", icon: "📱", label: t("mqttPhone") },
                                        { key: "opcua", icon: "🔗", label: t("opcua") },
                                        { key: "wakeword", icon: "🎤", label: t("wakeWord") }
                                    ]

                                    Rectangle {
                                        readonly property string state: root.commState(modelData.key)
                                        width: parent.width
                                        height: 54
                                        radius: 9
                                        color: root.dark ? "#06121d" : "#e4edf2"
                                        border.color: root.commStateColor(state)
                                        border.width: 1

                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.leftMargin: 12
                                            anchors.rightMargin: 12
                                            spacing: 10

                                            Label {
                                                text: modelData.icon
                                                color: root.commStateColor(state)
                                                font.pixelSize: 19
                                                Layout.preferredWidth: 24
                                                horizontalAlignment: Text.AlignHCenter
                                            }

                                            Label {
                                                text: modelData.label.toUpperCase()
                                                color: root.mutedText
                                                font.pixelSize: 10
                                                font.bold: true
                                                elide: Text.ElideRight
                                                Layout.fillWidth: true
                                            }

                                            Label {
                                                text: root.commStateGlyph(state)
                                                color: root.commStateColor(state)
                                                font.pixelSize: 17
                                                font.bold: true
                                            }

                                            Label {
                                                text: root.commStateText(state)
                                                color: root.textColor
                                                font.pixelSize: 12
                                                font.bold: true
                                                elide: Text.ElideRight
                                                Layout.preferredWidth: 108
                                            }
                                        }
                                    }
                                }

                                Rectangle {
                                    visible: blanky.commText.length > 0
                                    width: parent.width
                                    height: visible ? 38 : 0
                                    radius: 7
                                    color: root.dark ? "#251015" : "#fff2f3"
                                    border.color: "#d75b65"
                                    border.width: 1

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 10
                                        anchors.rightMargin: 10
                                        spacing: 7

                                        Label { text: "⚠"; color: "#ff717b"; font.pixelSize: 16; font.bold: true }
                                        Label {
                                            text: blanky.commText
                                            color: root.textColor
                                            font.pixelSize: 11
                                            font.bold: true
                                            wrapMode: Text.WordWrap
                                            elide: Text.ElideRight
                                            Layout.fillWidth: true
                                        }
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 88
                            color: root.panelAltColor
                            border.color: root.borderColor
                            border.width: 1
                            radius: 10

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 6

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 6

                                    Label {
                                        text: t("textBot")
                                        color: root.textColor
                                        font.bold: true
                                        font.pixelSize: 13
                                    }
                                    Item { Layout.fillWidth: true }

                                    MenuActionButton {
                                        text: t("textBotOffline")
                                        Layout.preferredWidth: 82
                                        Layout.preferredHeight: 28
                                        accentColor: root.textBotMode === "offline" ? root.successColor : root.inactiveColor
                                        textColor: root.textColor
                                        mutedText: root.mutedText
                                        borderColor: root.borderColor
                                        panelColor: root.panelColor
                                        onClicked: root.textBotMode = "offline"
                                    }

                                    MenuActionButton {
                                        text: t("textBotOnline")
                                        Layout.preferredWidth: 82
                                        Layout.preferredHeight: 28
                                        accentColor: root.textBotMode === "online" ? root.accentColor : root.inactiveColor
                                        textColor: root.textColor
                                        mutedText: root.mutedText
                                        borderColor: root.borderColor
                                        panelColor: root.panelColor
                                        onClicked: root.textBotMode = "online"
                                    }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    spacing: 7

                                    TextArea {
                                        id: textBotInput
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        wrapMode: TextEdit.WordWrap
                                        placeholderText: t("textBotPlaceholder")
                                        placeholderTextColor: root.mutedText
                                        color: root.textColor
                                        background: Rectangle {
                                            color: root.dark ? "#081a2b" : "#d7e6ed"
                                            border.color: root.borderColor
                                            border.width: 1
                                            radius: 7
                                        }
                                        Keys.onPressed: function(event) {
                                            var isEnter = event.key === Qt.Key_Return || event.key === Qt.Key_Enter
                                            var hasShift = (event.modifiers & Qt.ShiftModifier) !== 0
                                            if (isEnter && !hasShift) {
                                                root.sendTextBot()
                                                event.accepted = true
                                            }
                                        }
                                    }

                                    MenuActionButton {
                                        text: "\u2139"
                                        iconOnly: true
                                        textPixelSize: 17
                                        Layout.preferredWidth: 40
                                        Layout.fillHeight: true
                                        accentColor: root.accentColor
                                        textColor: root.textColor
                                        mutedText: root.mutedText
                                        borderColor: root.borderColor
                                        panelColor: root.panelColor
                                        toolTip: t("tooltipTextBotInfo")
                                        onClicked: commandsPanel.open()
                                    }

                                    MenuActionButton {
                                        text: "\u27A4 " + t("send")
                                        Layout.preferredWidth: 92
                                        Layout.fillHeight: true
                                        accentColor: root.successColor
                                        textColor: root.textColor
                                        mutedText: root.mutedText
                                        borderColor: root.borderColor
                                        panelColor: root.panelColor
                                        toolTip: t("tooltipTextBotSend")
                                        onClicked: root.sendTextBot()
                                    }
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 88
                            color: root.panelAltColor
                            border.color: root.borderColor
                            border.width: 1
                            radius: 10

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 6

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 6

                                    Label {
                                        text: t("textBot")
                                        color: root.textColor
                                        font.bold: true
                                        font.pixelSize: 13
                                    }
                                    Item { Layout.fillWidth: true }

                                    MenuActionButton {
                                        text: t("textBotOffline")
                                        Layout.preferredWidth: 82
                                        Layout.preferredHeight: 28
                                        accentColor: root.textBotMode === "offline" ? root.successColor : root.inactiveColor
                                        textColor: root.textColor
                                        mutedText: root.mutedText
                                        borderColor: root.borderColor
                                        panelColor: root.panelColor
                                        onClicked: root.textBotMode = "offline"
                                    }

                                    MenuActionButton {
                                        text: t("textBotOnline")
                                        Layout.preferredWidth: 82
                                        Layout.preferredHeight: 28
                                        accentColor: root.textBotMode === "online" ? root.accentColor : root.inactiveColor
                                        textColor: root.textColor
                                        mutedText: root.mutedText
                                        borderColor: root.borderColor
                                        panelColor: root.panelColor
                                        onClicked: root.textBotMode = "online"
                                    }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    spacing: 7

                                    TextArea {
                                        id: eventsTextBotInput
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        wrapMode: TextEdit.WordWrap
                                        placeholderText: t("textBotPlaceholder")
                                        placeholderTextColor: root.mutedText
                                        color: root.textColor
                                        background: Rectangle {
                                            color: root.dark ? "#081a2b" : "#d7e6ed"
                                            border.color: root.borderColor
                                            border.width: 1
                                            radius: 7
                                        }
                                        Keys.onPressed: function(event) {
                                            var isEnter = event.key === Qt.Key_Return || event.key === Qt.Key_Enter
                                            var hasShift = (event.modifiers & Qt.ShiftModifier) !== 0
                                            if (isEnter && !hasShift) {
                                                root.sendTextBot()
                                                event.accepted = true
                                            }
                                        }
                                    }

                                    MenuActionButton {
                                        text: "\u2139"
                                        iconOnly: true
                                        textPixelSize: 17
                                        Layout.preferredWidth: 40
                                        Layout.fillHeight: true
                                        accentColor: root.accentColor
                                        textColor: root.textColor
                                        mutedText: root.mutedText
                                        borderColor: root.borderColor
                                        panelColor: root.panelColor
                                        toolTip: t("tooltipTextBotInfo")
                                        onClicked: commandsPanel.open()
                                    }

                                    MenuActionButton {
                                        text: "\u27A4 " + t("send")
                                        Layout.preferredWidth: 92
                                        Layout.fillHeight: true
                                        accentColor: root.successColor
                                        textColor: root.textColor
                                        mutedText: root.mutedText
                                        borderColor: root.borderColor
                                        panelColor: root.panelColor
                                        toolTip: t("tooltipTextBotSend")
                                        onClicked: root.sendTextBot()
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: root.panelColor
                    border.color: root.borderColor
                    border.width: 1
                    radius: 10

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: root.borderColor }
                                Label {
                                    text: t("events").toUpperCase()
                                    color: root.accentColor
                                    font.pixelSize: 14
                                    font.bold: true
                                }
                                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: root.borderColor }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                Item {
                                    Layout.fillWidth: true
                                    Layout.minimumWidth: 0
                                    Layout.preferredHeight: Math.round(38 * root.controlScale)
                                    clip: true

                                    Text {
                                        anchors.verticalCenter: parent.verticalCenter
                                        text: root.eventsHeaderText() + "\n" + root.eventsHeaderDivider()
                                        color: root.mutedText
                                        font.family: "Consolas"
                                        font.pixelSize: Math.round(12 * root.textScale)
                                        font.bold: true
                                        textFormat: Text.PlainText
                                    }
                                }

                                MenuActionButton {
                                    text: t("exportData")
                                    toolTip: t("tooltipExportData")
                                    Layout.preferredWidth: 130
                                    Layout.preferredHeight: Math.round(38 * root.controlScale)
                                    accentColor: root.successColor
                                    textColor: root.textColor
                                    mutedText: root.mutedText
                                    borderColor: root.borderColor
                                    panelColor: root.panelAltColor
                                    onClicked: root.chooseExportDestination("events", "csv")
                                }

                                MenuActionButton {
                                    text: t("exportReport")
                                    toolTip: t("tooltipExportReport")
                                    Layout.preferredWidth: 130
                                    Layout.preferredHeight: Math.round(38 * root.controlScale)
                                    accentColor: root.accentColor
                                    textColor: root.textColor
                                    mutedText: root.mutedText
                                    borderColor: root.borderColor
                                    panelColor: root.panelAltColor
                                    onClicked: root.chooseExportDestination("events", "pdf")
                                }
                            }
                        }

                        ScrollView {
                            id: eventsScroll
                            visible: !root.systemTransitionActive
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                            ScrollBar.vertical.policy: ScrollBar.AlwaysOn

                            TextEdit {
                                id: eventsContent
                                width: eventsScroll.availableWidth
                                height: Math.max(eventsScroll.availableHeight, contentHeight + 6)
                                text: blanky.monitorEventsRichText
                                readOnly: true
                                selectByMouse: true
                                wrapMode: TextEdit.NoWrap
                                color: root.textColor
                                font.family: "Consolas"
                                font.pixelSize: Math.round(12 * root.textScale)
                                textFormat: TextEdit.RichText
                            }
                        }

                        Rectangle {
                            visible: !root.systemTransitionActive
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.round(88 * root.controlScale + (root.textScale - 1.0) * 34)
                            Layout.minimumHeight: Layout.preferredHeight
                            color: root.panelAltColor
                            border.color: root.borderColor
                            border.width: 1
                            radius: 10

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 6

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 8

                                    Rectangle { Layout.preferredWidth: 18; Layout.preferredHeight: 1; color: root.borderColor }
                                    Label {
                                        text: t("textBot").toUpperCase()
                                        color: root.accentColor
                                        font.bold: true
                                        font.pixelSize: Math.round(14 * root.textScale)
                                    }
                                    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: root.borderColor }
                                    MenuActionButton {
                                        text: t("textBotOffline")
                                        Layout.preferredWidth: 82; Layout.preferredHeight: Math.round(28 * root.controlScale)
                                        accentColor: root.textBotMode === "offline" ? root.successColor : root.inactiveColor
                                        textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor
                                        onClicked: root.textBotMode = "offline"
                                    }
                                    MenuActionButton {
                                        text: t("textBotOnline")
                                        Layout.preferredWidth: 82; Layout.preferredHeight: Math.round(28 * root.controlScale)
                                        accentColor: root.textBotMode === "online" ? root.accentColor : root.inactiveColor
                                        textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor
                                        onClicked: root.textBotMode = "online"
                                    }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    spacing: 7
                                    ScrollView {
                                        id: eventsTextBotScroll
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        clip: true
                                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                                        ScrollBar.vertical.policy: ScrollBar.AsNeeded

                                        TextArea {
                                            id: eventsTextBotEditor
                                            width: eventsTextBotScroll.availableWidth
                                            height: Math.max(eventsTextBotScroll.availableHeight, contentHeight + topPadding + bottomPadding)
                                            wrapMode: TextEdit.WordWrap
                                            placeholderText: t("textBotPlaceholder")
                                            placeholderTextColor: root.mutedText
                                            color: root.textColor
                                            font.pixelSize: Math.round(12 * root.textScale)
                                            background: Rectangle {
                                                color: root.panelColor
                                                border.color: root.borderColor
                                                border.width: 1
                                                radius: 7
                                            }
                                            Keys.onPressed: function(event) {
                                                var isEnter = event.key === Qt.Key_Return || event.key === Qt.Key_Enter
                                                if (isEnter && (event.modifiers & Qt.ShiftModifier) === 0) {
                                                    root.sendTextBot()
                                                    event.accepted = true
                                                }
                                            }
                                        }
                                    }
                                    MenuActionButton {
                                        text: "\u2139"; iconOnly: true; textPixelSize: 17
                                        Layout.preferredWidth: 40; Layout.fillHeight: true
                                        accentColor: root.accentColor; textColor: root.textColor; mutedText: root.mutedText
                                        borderColor: root.borderColor; panelColor: root.panelColor
                                        toolTip: t("tooltipTextBotInfo")
                                        onClicked: commandsPanel.open()
                                    }
                                    MenuActionButton {
                                        text: "\u27A4 " + t("send")
                                        Layout.preferredWidth: 92; Layout.fillHeight: true
                                        accentColor: root.successColor; textColor: root.textColor; mutedText: root.mutedText
                                        borderColor: root.borderColor; panelColor: root.panelColor
                                        toolTip: t("tooltipTextBotSend")
                                        onClicked: root.sendTextBot()
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    visible: false
                    Layout.fillHeight: true
                    Layout.minimumWidth: 0
                    Layout.preferredWidth: 0
                    Layout.maximumWidth: 0
                    color: root.panelColor
                    border.color: root.borderColor
                    border.width: 1
                    radius: 10

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Label {
                            text: t("manualControl")
                            color: root.textColor
                            font.pixelSize: 14
                            font.bold: true
                        }

                        ScrollView {
                            id: manualScroll
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            ScrollBar.horizontal.policy: ScrollBar.AlwaysOn
                            ScrollBar.vertical.policy: ScrollBar.AlwaysOn

                            Column {
                                width: Math.max(manualScroll.width - 24, 320)
                                spacing: 10

                                Label { width: parent.width; text: t("system"); color: root.mutedText; font.bold: true }
                                Flow {
                                    width: parent.width
                                    spacing: 8
                                    ManualCommandButton { width: parent.width; label: t("startStop"); iconText: root.stateValue("start") === 1 ? "⏹" : "▶"; command: root.toggleCommand("start", "START", "STOP"); active: root.stateValue("start") === 1; stateText: root.toggleStateText("start", "ON", "OFF"); iconColor: active ? "#48d66b" : "#ff6b6b"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor; onTriggered: function(command) { blanky.submitButtonCommand(command) } }
                                }

                                Label { width: parent.width; text: t("modes"); color: root.mutedText; font.bold: true }
                                Flow {
                                    width: parent.width
                                    spacing: 8
                                    ManualCommandButton { width: (parent.width - 8) / 2; label: t("fast"); iconText: "⚡"; command: "MODE_FAST"; active: root.stateValue("mode_fast") === 1; stateText: active ? "ON" : ""; iconColor: "#f8c25d"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor; onTriggered: function(command) { blanky.submitButtonCommand(command) } }
                                    ManualCommandButton { width: (parent.width - 8) / 2; label: t("ideal"); iconText: "🎯"; command: "MODE_IDEAL"; active: root.stateValue("mode_ideal") === 1; stateText: active ? "ON" : ""; iconColor: "#63cbff"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor; onTriggered: function(command) { blanky.submitButtonCommand(command) } }
                                    ManualCommandButton { width: (parent.width - 8) / 2; label: t("manual"); iconText: "🕹"; command: "MODE_MANUAL"; active: root.stateValue("mode_manual") === 1; stateText: active ? "ON" : ""; iconColor: "#b7f7d4"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor; onTriggered: function(command) { blanky.submitButtonCommand(command) } }
                                    ManualCommandButton { width: (parent.width - 8) / 2; label: t("change"); iconText: "🔁"; command: "MODE_UNSPEC"; active: root.stateValue("mode_change") === 1; stateText: active ? "ON" : ""; iconColor: "#9dd9ff"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor; onTriggered: function(command) { blanky.submitButtonCommand(command) } }
                                }

                                Label { width: parent.width; text: t("motors"); color: root.mutedText; font.bold: true }
                                Flow {
                                    width: parent.width
                                    spacing: 8
                                    ManualCommandButton { width: (parent.width - 8) / 2; label: t("motor", { number: 1 }); iconText: "⚙"; command: root.toggleCommand("motor_1", "MOTOR_1_ON", "MOTOR_1_OFF"); active: root.stateValue("motor_1") === 1; stateText: root.toggleStateText("motor_1", "ON", "OFF"); iconColor: active ? "#63cbff" : "#8fa8b8"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor; onTriggered: function(command) { blanky.submitButtonCommand(command) } }
                                    ManualCommandButton { width: (parent.width - 8) / 2; label: t("motor", { number: 2 }); iconText: "⚙"; command: root.toggleCommand("motor_2", "MOTOR_2_ON", "MOTOR_2_OFF"); active: root.stateValue("motor_2") === 1; stateText: root.toggleStateText("motor_2", "ON", "OFF"); iconColor: active ? "#63cbff" : "#8fa8b8"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor; onTriggered: function(command) { blanky.submitButtonCommand(command) } }
                                    ManualCommandButton { width: (parent.width - 8) / 2; label: t("motor", { number: 3 }); iconText: "⚙"; command: root.toggleCommand("motor_3", "MOTOR_3_ON", "MOTOR_3_OFF"); active: root.stateValue("motor_3") === 1; stateText: root.toggleStateText("motor_3", "ON", "OFF"); iconColor: active ? "#63cbff" : "#8fa8b8"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor; onTriggered: function(command) { blanky.submitButtonCommand(command) } }
                                }

                                Label { width: parent.width; text: t("cylinders"); color: root.mutedText; font.bold: true }
                                Flow {
                                    width: parent.width
                                    spacing: 8
                                    ManualCommandButton { width: (parent.width - 8) / 2; label: t("cylinder", { letter: "A" }); iconText: "▰"; command: root.toggleCommand("cyl_a", "CYL_A_EXTEND", "CYL_A_RETRACT"); active: root.stateValue("cyl_a") === 1; stateText: root.toggleStateText("cyl_a", t("forward"), t("backward")); iconColor: active ? "#63cbff" : "#8fa8b8"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor; onTriggered: function(command) { blanky.submitButtonCommand(command) } }
                                    ManualCommandButton { width: (parent.width - 8) / 2; label: t("cylinder", { letter: "B" }); iconText: "▰"; command: root.toggleCommand("cyl_b", "CYL_B_EXTEND", "CYL_B_RETRACT"); active: root.stateValue("cyl_b") === 1; stateText: root.toggleStateText("cyl_b", t("forward"), t("backward")); iconColor: active ? "#63cbff" : "#8fa8b8"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor; onTriggered: function(command) { blanky.submitButtonCommand(command) } }
                                    ManualCommandButton { width: (parent.width - 8) / 2; label: t("cylinder", { letter: "C" }); iconText: "▰"; command: root.toggleCommand("cyl_c", "CYL_C_EXTEND", "CYL_C_RETRACT"); active: root.stateValue("cyl_c") === 1; stateText: root.toggleStateText("cyl_c", t("forward"), t("backward")); iconColor: active ? "#63cbff" : "#8fa8b8"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor; onTriggered: function(command) { blanky.submitButtonCommand(command) } }
                                    ManualCommandButton { width: (parent.width - 8) / 2; label: t("cylinder", { letter: "D" }); iconText: "▰"; command: root.toggleCommand("cyl_d", "CYL_D_EXTEND", "CYL_D_RETRACT"); active: root.stateValue("cyl_d") === 1; stateText: root.toggleStateText("cyl_d", t("forward"), t("backward")); iconColor: active ? "#63cbff" : "#8fa8b8"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor; onTriggered: function(command) { blanky.submitButtonCommand(command) } }
                                }

                                Label { width: parent.width; text: t("lightsRobot"); color: root.mutedText; font.bold: true }
                                Flow {
                                    width: parent.width
                                    spacing: 8
                                    ManualCommandButton { width: (parent.width - 8) / 2; label: t("greenLight"); iconText: "●"; command: root.toggleCommand("light_green", "GREEN_ON", "GREEN_OFF"); active: root.stateValue("light_green") === 1; stateText: root.toggleStateText("light_green", "ON", "OFF"); iconColor: active ? "#48d66b" : "#4e6f58"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor; onTriggered: function(command) { blanky.submitButtonCommand(command) } }
                                    ManualCommandButton { width: (parent.width - 8) / 2; label: t("redLight"); iconText: "●"; command: root.toggleCommand("light_red", "RED_ON", "RED_OFF"); active: root.stateValue("light_red") === 1; stateText: root.toggleStateText("light_red", "ON", "OFF"); iconColor: active ? "#ff5c5c" : "#7d5151"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor; onTriggered: function(command) { blanky.submitButtonCommand(command) } }
                                    ManualCommandButton { width: (parent.width - 8) / 2; label: t("robotMetal"); iconText: "🤖"; command: "ROBOT_TO_METAL"; active: root.stateValue("robot_metal") === 1; stateText: active ? "ON" : ""; iconColor: "#63cbff"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor; onTriggered: function(command) { blanky.submitButtonCommand(command) } }
                                    ManualCommandButton { width: (parent.width - 8) / 2; label: t("robotNonMetal"); iconText: "🤖"; command: "ROBOT_TO_NONMETAL"; active: root.stateValue("robot_nonmetal") === 1; stateText: active ? "ON" : ""; iconColor: "#b7f7d4"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor; onTriggered: function(command) { blanky.submitButtonCommand(command) } }
                                }
                            }
                        }
                    }
                }

                DirectControlPanel {
                    id: directControlPanel
                    Layout.alignment: Qt.AlignTop
                    Layout.fillHeight: true
                    Layout.topMargin: 0
                    Layout.minimumWidth: root.rightPanelWidth
                    Layout.preferredWidth: root.rightPanelWidth
                    Layout.maximumWidth: root.rightPanelWidth
                    Layout.minimumHeight: 0
                    controller: blanky
                    language: blanky.language
                    dark: root.dark
                    panelColor: root.panelColor
                    panelAltColor: root.panelAltColor
                    borderColor: root.borderColor
                    textColor: root.textColor
                    mutedText: root.mutedText
                    accentColor: root.accentColor
                    successColor: root.successColor
                    warningColor: root.warningColor
                    errorColor: root.errorColor
                    inactiveColor: root.inactiveColor
                    stateMap: root.stateMap
                }
            }
        }
    }

    CommunicationsPanel {
        id: rightCommunicationsPanel
        parent: dashboardLayer
        x: root.width - width - 18
        y: mainColumn.y + statusPanel.y
        width: root.rightPanelWidth
        height: mainColumn.y + primaryControlsPanel.y + primaryControlsPanel.height - y
        z: 3
        controller: blanky
        language: blanky.language
        dark: root.dark
        panelColor: root.panelColor
        panelAltColor: root.panelAltColor
        borderColor: root.borderColor
        textColor: root.textColor
        mutedText: root.mutedText
        accentColor: root.accentColor
        successColor: root.successColor
        warningColor: root.warningColor
        errorColor: root.errorColor
        inactiveColor: root.inactiveColor
        colorIndependent: theme.colorIndependent
        successSurface: theme.successSurface
        infoSurface: theme.infoSurface
        warningSurface: theme.warningSurface
        errorSurface: theme.errorSurface
        stateMap: root.commStateMap
    }

    }

    Rectangle {
        id: systemTransitionOverlay
        anchors.fill: parent
        z: 200
        visible: root.systemTransitionActive || opacity > 0.01
        opacity: root.systemTransitionActive ? 1 : 0
        color: root.bgColor

        Behavior on opacity {
            NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
        }

        Column {
            anchors.centerIn: parent
            width: Math.min(parent.width - 48, 440)
            spacing: 16

            Label {
                width: parent.width
                text: root.systemTransitionAction === "shutdown" ? t("shuttingDownSystem") : t("restartingSystem")
                color: root.textColor
                font.pixelSize: 24
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
            }

            Label {
                width: parent.width
                text: t("transitionWait")
                color: root.mutedText
                font.pixelSize: 14
                horizontalAlignment: Text.AlignHCenter
            }

            Rectangle {
                width: parent.width
                height: 12
                radius: 6
                color: root.dark ? "#0a1a26" : "#b4cad8"
                border.color: root.borderColor
                border.width: 1

                Rectangle {
                    width: parent.width * root.systemTransitionProgress / 100
                    height: parent.height
                    radius: parent.radius
                    color: root.systemTransitionAction === "shutdown" ? "#ff6b6b" : "#48d66b"
                    Behavior on width { NumberAnimation { duration: 60 } }
                }
            }

            Label {
                width: parent.width
                text: root.systemTransitionProgress + "%"
                color: root.textColor
                font.pixelSize: 18
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
            }
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
        }
    }

    Item {
        id: modalBackdrop
        anchors.fill: parent
        z: 100
        visible: root.popupBackdropVisible || opacity > 0.01
        opacity: root.popupBackdropVisible ? 1 : 0
        property url snapshotUrl: ""

        Behavior on opacity {
            NumberAnimation {
                duration: 220
                easing.type: Easing.OutCubic
            }
        }

        function refreshSnapshot() {
            dashboardLayer.grabToImage(function(result) {
                modalBackdrop.snapshotUrl = result.url
            }, Qt.size(Math.max(1, Math.round(width / 5)), Math.max(1, Math.round(height / 5))))
        }

        function scheduleSnapshot() {
            snapshotTimer.restart()
        }

        Timer {
            id: snapshotTimer
            interval: 20
            repeat: false
            onTriggered: modalBackdrop.refreshSnapshot()
        }

        Image {
            anchors.fill: parent
            source: modalBackdrop.snapshotUrl
            fillMode: Image.Stretch
            smooth: true
            mipmap: true
            cache: false
            asynchronous: false
        }

        Rectangle {
            anchors.fill: parent
            color: root.dark ? "#000308" : "#18384d"
            opacity: root.dark ? 0.45 : 0.28
        }

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
        }
    }

    Popup {
        id: ttsSpeedPopover
        parent: Overlay.overlay
        width: 390
        height: 104
        x: {
            var point = voiceSpeedButton.mapToItem(Overlay.overlay, voiceSpeedButton.width / 2, voiceSpeedButton.height)
            return Math.max(12, Math.min(root.width - width - 12, point.x - width / 2))
        }
        y: {
            var point = voiceSpeedButton.mapToItem(Overlay.overlay, voiceSpeedButton.width / 2, voiceSpeedButton.height)
            return Math.min(root.height - height - 12, point.y + 8)
        }
        modal: false
        focus: true
        padding: 0
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        background: Rectangle {
            radius: 14
            color: root.panelColor
            border.color: root.borderColor
            border.width: 1
        }

        contentItem: ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8

            Label {
                text: t("voiceSpeed")
                color: root.textColor
                font.pixelSize: 15
                font.bold: true
                Layout.fillWidth: true
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                MenuActionButton {
                    text: "\uD83D\uDC22 " + t("slow")
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    accentColor: blanky.ttsSpeed < 0.9 ? "#48d66b" : root.borderColor
                    textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor
                    onClicked: { blanky.setTtsSpeed(0.8); ttsSpeedPopover.close() }
                }
                MenuActionButton {
                    text: "\u25B6 " + t("normal")
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    accentColor: blanky.ttsSpeed >= 0.9 && blanky.ttsSpeed <= 1.1 ? "#48d66b" : root.borderColor
                    textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor
                    onClicked: { blanky.setTtsSpeed(1.0); ttsSpeedPopover.close() }
                }
                MenuActionButton {
                    text: "\u26A1 " + t("fast")
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    accentColor: blanky.ttsSpeed > 1.1 ? "#48d66b" : root.borderColor
                    textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor
                    onClicked: { blanky.setTtsSpeed(1.2); ttsSpeedPopover.close() }
                }
            }
        }
    }

    Popup {
        id: volumePopover
        parent: Overlay.overlay
        width: 255
        height: 94
        x: Math.max(12, root.width - width - 20)
        y: 68
        modal: false
        focus: true
        padding: 0
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        background: Rectangle {
            radius: 14
            color: root.panelColor
            border.color: root.borderColor
            border.width: 1
        }

        contentItem: ColumnLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            anchors.topMargin: 10
            anchors.bottomMargin: 9
            spacing: 5

            RowLayout {
                Layout.fillWidth: true
                Label {
                    text: t("volume")
                    color: root.textColor
                    font.pixelSize: 14
                    font.bold: true
                    Layout.fillWidth: true
                }
                Label {
                    text: formatPercent(blanky.soundVolume)
                    color: root.mutedText
                    font.pixelSize: 12
                    font.bold: true
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 10

                MenuActionButton {
                    text: root.volumeGlyph()
                    iconOnly: true
                    textPixelSize: 15
                    Layout.preferredWidth: 34
                    Layout.preferredHeight: 34
                    accentColor: blanky.soundEnabled ? "#63cbff" : "#ff6b6b"
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: blanky.soundEnabled ? t("tooltipMute") : t("tooltipUnmute")
                    onClicked: blanky.toggleSound()
                }

                Slider {
                    id: volumePopoverSlider
                    Layout.fillWidth: true
                    Layout.preferredHeight: 34
                    Layout.minimumWidth: 150
                    from: 0.0
                    to: 1.0
                    stepSize: 0.05
                    value: blanky.soundVolume
                    onMoved: blanky.setSoundVolume(value)
                    onValueChanged: {
                        if (pressed)
                            blanky.setSoundVolume(value)
                    }

                    background: Rectangle {
                        x: volumePopoverSlider.leftPadding
                        y: volumePopoverSlider.topPadding + volumePopoverSlider.availableHeight / 2 - height / 2
                        width: volumePopoverSlider.availableWidth
                        implicitWidth: 150
                        implicitHeight: 6
                        height: implicitHeight
                        radius: 3
                        color: root.dark ? "#40515e" : "#91a5b3"

                        Rectangle {
                            width: parent.width * volumePopoverSlider.visualPosition
                            height: parent.height
                            radius: parent.radius
                            color: "#49bdf4"
                        }
                    }

                    handle: Rectangle {
                        x: volumePopoverSlider.leftPadding + volumePopoverSlider.visualPosition * (volumePopoverSlider.availableWidth - width)
                        y: volumePopoverSlider.topPadding + volumePopoverSlider.availableHeight / 2 - height / 2
                        width: 15
                        height: 15
                        radius: 7.5
                        color: root.dark ? "#edf9ff" : "#145f88"
                        border.color: "#49bdf4"
                        border.width: 2
                    }
                }
            }
        }
    }

    FloatingPanel {
        id: commandsPanel
        width: 980
        height: 680
        panelTitle: t("commandListTitle")
        panelColor: root.panelColor
        borderColor: root.borderColor
        titleColor: root.textColor
        onOpening: { root.popupBackdropVisible = true; modalBackdrop.scheduleSnapshot() }
        onOpenedForBackdrop: modalBackdrop.scheduleSnapshot()
        onClosedForBackdrop: root.popupBackdropVisible = false

        ColumnLayout {
            anchors.fill: parent
            spacing: 10

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: commandHelpIntro.implicitHeight + 22
                color: root.panelAltColor
                border.color: root.borderColor
                border.width: 1
                radius: 12

                Label {
                    id: commandHelpIntro
                    anchors.fill: parent
                    anchors.margins: 11
                    wrapMode: Text.WordWrap
                    text: blanky.language === "pt"
                        ? "Pode utilizar frases naturais para controlar o sistema. A IA interpreta o pedido e executa apenas comandos v\u00e1lidos e permitidos pelas regras de seguran\u00e7a."
                        : "You can use natural phrases to control the system. AI interprets the request and executes only valid commands allowed by safety rules."
                    color: root.textColor
                    font.pixelSize: 13
                }
            }

            ScrollView {
                id: commandHelpScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                // Keep the overlay scrollbar outside the command cards.
                rightPadding: Math.round(14 * root.textScale)
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ScrollBar.vertical.policy: ScrollBar.AlwaysOn

                Column {
                    width: Math.max(commandHelpScroll.availableWidth - Math.round(12 * root.textScale), 720)
                    spacing: 16

                    Repeater {
                        model: root.commandHelpGroups()

                        Column {
                            required property var modelData
                            width: parent.width
                            spacing: 8

                            RowLayout {
                                width: parent.width
                                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: root.borderColor }
                                Label {
                                    text: modelData.title
                                    color: root.dark ? "#82d6ff" : "#0d5d8b"
                                    font.pixelSize: 15
                                    font.bold: true
                                }
                                Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: root.borderColor }
                            }

                            GridLayout {
                                width: parent.width
                                columns: 2
                                columnSpacing: 10
                                rowSpacing: 10

                                Repeater {
                                    model: modelData.commands

                                    Rectangle {
                                        Layout.preferredWidth: (parent.width - parent.columnSpacing) / 2
                                        Layout.preferredHeight: 122
                                        radius: 11
                                        color: root.panelAltColor
                                        border.color: root.borderColor
                                        border.width: 1

                                        ColumnLayout {
                                            anchors.fill: parent
                                            anchors.margins: 11
                                            spacing: 5

                                            RowLayout {
                                                Layout.fillWidth: true
                                                spacing: 7
                                                Label { text: modelData.icon; color: modelData.color; font.pixelSize: 18; font.bold: true }
                                                Label { text: modelData.title; color: root.textColor; font.pixelSize: 14; font.bold: true; Layout.fillWidth: true }
                                                Label { text: modelData.code; color: root.mutedText; font.pixelSize: 9; font.bold: true; elide: Text.ElideLeft }
                                            }
                                            Label {
                                                Layout.fillWidth: true
                                                text: modelData.description
                                                color: root.textColor
                                                font.pixelSize: 12
                                                wrapMode: Text.WordWrap
                                            }
                                            Label {
                                                Layout.fillWidth: true
                                                Layout.fillHeight: true
                                                text: (blanky.language === "pt" ? "Exemplos: " : "Examples: ") + modelData.examples
                                                color: root.mutedText
                                                font.pixelSize: 11
                                                wrapMode: Text.WordWrap
                                            }
                                        }

                                        MouseArea {
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: root.prepareTextBot(modelData.input)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    HelpDialog {
        id: helpPanel
        language: blanky.language
        panelColor: root.panelColor
        panelAltColor: root.panelAltColor
        borderColor: root.borderColor
        titleColor: root.textColor
        textColor: root.textColor
        mutedText: root.mutedText
        accentColor: root.accentColor
        successColor: root.successColor
        warningColor: root.warningColor
        errorColor: root.errorColor
        inactiveColor: root.inactiveColor
        textScale: root.textScale
        onOpening: { root.popupBackdropVisible = true; modalBackdrop.scheduleSnapshot() }
        onOpenedForBackdrop: modalBackdrop.scheduleSnapshot()
        onClosedForBackdrop: root.popupBackdropVisible = false
    }

    FloatingPanel {
        id: appearancePanel
        width: 680
        height: 520
        panelTitle: t("appearanceAccessibility")
        panelColor: root.panelColor
        borderColor: root.borderColor
        titleColor: root.textColor
        textColor: root.textColor
        rememberPosition: false
        onOpening: { root.popupBackdropVisible = true; modalBackdrop.scheduleSnapshot() }
        onOpenedForBackdrop: modalBackdrop.scheduleSnapshot()
        onClosedForBackdrop: root.popupBackdropVisible = customAppearancePanel.visible || colorVisionProfilesPanel.visible

        ColumnLayout {
            anchors.fill: parent
            spacing: 12

            Label {
                Layout.fillWidth: true
                text: blanky.language === "pt"
                    ? "Escolha um modo visual. A alteração é aplicada imediatamente e fica guardada para o próximo arranque."
                    : "Choose a visual mode. It applies immediately and is saved for the next start."
                color: root.mutedText
                font.pixelSize: Math.round(12 * root.textScale)
                wrapMode: Text.WordWrap
            }

            GridLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                columns: 2
                columnSpacing: 10
                rowSpacing: 10

                Repeater {
                    model: root.appearanceOptions()

                    Rectangle {
                        required property var modelData
                        readonly property bool selected: blanky.appearanceMode === modelData.id
                        readonly property color modeColor: modelData.tone
                        Layout.fillWidth: true
                        Layout.preferredHeight: Math.round(74 * (root.textScale > 1 ? 1.06 : 1.0))
                        radius: 10
                        color: selected ? Qt.lighter(root.panelAltColor, root.dark ? 1.16 : 1.03) : root.panelAltColor
                        border.color: selected ? modeColor : Qt.darker(modeColor, root.dark ? 1.65 : 1.18)
                        border.width: selected ? 2 : 1

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10

                            Rectangle {
                                Layout.preferredWidth: 4
                                Layout.fillHeight: true
                                radius: 2
                                color: modeColor
                            }
                            Label { text: modelData.icon; color: modeColor; font.pixelSize: Math.round(23 * root.textScale) }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 3
                                Label { text: modelData.title; color: selected ? modeColor : root.textColor; font.bold: true; font.pixelSize: Math.round(14 * root.textScale); Layout.fillWidth: true }
                                Label { text: modelData.description; color: root.mutedText; font.pixelSize: Math.round(10 * root.textScale); Layout.fillWidth: true; elide: Text.ElideRight }
                            }
                            Label { text: selected ? "✓" : "○"; color: selected ? modeColor : root.inactiveColor; font.pixelSize: Math.round(18 * root.textScale); font.bold: true }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                if (modelData.id === "colorblind") {
                                    colorVisionProfilesPanel.open()
                                } else if (modelData.id === "custom") {
                                    blanky.setAppearanceMode(modelData.id)
                                    appearancePanel.close()
                                    customAppearancePanel.open()
                                } else {
                                    blanky.setAppearanceMode(modelData.id)
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: Math.round(72 * root.controlScale)
                radius: 9
                color: root.panelAltColor
                border.color: root.borderColor
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 5

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: "🔎 " + t("readabilitySize"); color: root.textColor; font.bold: true; font.pixelSize: Math.round(12 * root.textScale); Layout.fillWidth: true }
                        Label { text: Math.round(blanky.appearanceTextScale * 100) + "%"; color: root.accentColor; font.bold: true; font.pixelSize: Math.round(12 * root.textScale) }
                        MenuActionButton {
                            text: t("resetSize")
                            Layout.preferredWidth: 58
                            Layout.preferredHeight: 24
                            accentColor: root.inactiveColor
                            textColor: root.textColor
                            mutedText: root.mutedText
                            borderColor: root.borderColor
                            panelColor: root.panelColor
                            onClicked: blanky.setAppearanceTextScale(1.0)
                        }
                    }

                    Slider {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 22
                        Layout.bottomMargin: 4
                        from: 1.0
                        to: 1.25
                        stepSize: 0.01
                        value: blanky.appearanceTextScale
                        onMoved: blanky.setAppearanceTextScale(value)
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: Math.round(74 * root.controlScale)
                radius: 9
                color: root.panelAltColor
                border.color: root.borderColor
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 4
                    Label { text: t("appearancePreview"); color: root.textColor; font.bold: true; font.pixelSize: Math.round(12 * root.textScale); Layout.fillWidth: true }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 14
                        Label { text: "✓ " + t("connected"); color: root.successColor; font.bold: true; font.pixelSize: Math.round(12 * root.textScale) }
                        Label { text: "! " + t("warning"); color: root.warningColor; font.bold: true; font.pixelSize: Math.round(12 * root.textScale) }
                        Label { text: "✕ " + t("error"); color: root.errorColor; font.bold: true; font.pixelSize: Math.round(12 * root.textScale) }
                        Label { text: "○ " + t("inactive"); color: root.inactiveColor; font.bold: true; font.pixelSize: Math.round(12 * root.textScale) }
                        Label { text: "✓ ON"; color: root.successColor; font.bold: true; font.pixelSize: Math.round(12 * root.textScale) }
                        Label { text: "○ OFF"; color: root.inactiveColor; font.bold: true; font.pixelSize: Math.round(12 * root.textScale) }
                    }
                }
            }
        }
    }

    FloatingPanel {
        id: colorVisionProfilesPanel
        width: 650
        height: 490
        panelTitle: t("colorVisionProfilesTitle")
        panelColor: root.panelColor
        borderColor: root.borderColor
        titleColor: root.textColor
        textColor: root.textColor
        rememberPosition: false
        onOpening: { root.popupBackdropVisible = true; modalBackdrop.scheduleSnapshot() }
        onOpenedForBackdrop: modalBackdrop.scheduleSnapshot()
        onClosedForBackdrop: root.popupBackdropVisible = appearancePanel.visible

        ColumnLayout {
            anchors.fill: parent
            spacing: 12

            Label {
                Layout.fillWidth: true
                text: t("colorVisionProfileIntro")
                color: root.mutedText
                font.pixelSize: Math.round(12 * root.textScale)
                wrapMode: Text.WordWrap
            }

            GridLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                columns: 2
                columnSpacing: 10
                rowSpacing: 10

                Repeater {
                    model: root.colorVisionProfiles()

                    Rectangle {
                        required property var modelData
                        readonly property bool selected: blanky.colorVisionProfile === modelData.id
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumHeight: 102
                        radius: 10
                        color: selected ? Qt.lighter(root.panelAltColor, root.dark ? 1.18 : 1.04) : root.panelAltColor
                        border.color: selected ? modelData.tone : Qt.darker(modelData.tone, root.dark ? 1.55 : 1.12)
                        border.width: selected ? 2 : 1

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 10

                            Rectangle {
                                Layout.preferredWidth: 36
                                Layout.preferredHeight: 36
                                radius: 18
                                color: Qt.darker(modelData.tone, root.dark ? 2.8 : 1.18)
                                border.color: modelData.tone
                                border.width: 1
                                Label { anchors.centerIn: parent; text: modelData.icon; color: modelData.tone; font.bold: true; font.pixelSize: Math.round(17 * root.textScale) }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4
                                RowLayout {
                                    Layout.fillWidth: true
                                    Label { text: modelData.title; color: selected ? modelData.tone : root.textColor; font.bold: true; font.pixelSize: Math.round(14 * root.textScale); Layout.fillWidth: true }
                                    Label { visible: modelData.recommended; text: t("recommended"); color: root.warningColor; font.bold: true; font.pixelSize: Math.round(9 * root.textScale) }
                                }
                                Label { text: modelData.description; color: root.mutedText; font.pixelSize: Math.round(10 * root.textScale); Layout.fillWidth: true; wrapMode: Text.WordWrap; maximumLineCount: 2; elide: Text.ElideRight }
                                Label { text: selected ? "✓ " + t("active") : "○ " + t("inactive"); color: selected ? modelData.tone : root.inactiveColor; font.bold: true; font.pixelSize: Math.round(10 * root.textScale) }
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                blanky.setColorVisionProfile(modelData.id)
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 86
                radius: 8
                color: root.panelAltColor
                border.color: root.borderColor
                border.width: 1
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 4
                    Label { text: t("colorVisionStateMatrix"); color: root.textColor; font.bold: true; font.pixelSize: Math.round(11 * root.textScale) }
                    GridLayout {
                        Layout.fillWidth: true
                        columns: 3
                        columnSpacing: 10
                        rowSpacing: 3
                        Label { text: "✓ ON"; color: root.successColor; font.bold: true; font.pixelSize: Math.round(11 * root.textScale) }
                        Label { text: "! " + t("warning"); color: root.warningColor; font.bold: true; font.pixelSize: Math.round(11 * root.textScale) }
                        Label { text: "✕ " + t("error"); color: root.errorColor; font.bold: true; font.pixelSize: Math.round(11 * root.textScale) }
                        Label { text: "○ OFF"; color: root.inactiveColor; font.bold: true; font.pixelSize: Math.round(11 * root.textScale) }
                        Label { text: "✓ " + t("eventOk"); color: root.successColor; font.bold: true; font.pixelSize: Math.round(11 * root.textScale) }
                        Label { text: "✕ " + t("eventReject"); color: root.errorColor; font.bold: true; font.pixelSize: Math.round(11 * root.textScale) }
                    }
                    Label { text: t("colorVisionDisclaimer"); color: root.mutedText; font.pixelSize: Math.round(9 * root.textScale); Layout.fillWidth: true; wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignRight }
                }
            }
        }
    }

    FloatingPanel {
        id: customAppearancePanel
        width: 540
        height: 390
        panelTitle: t("customAppearanceTitle")
        panelColor: root.panelColor
        borderColor: root.borderColor
        titleColor: root.textColor
        textColor: root.textColor
        rememberPosition: false
        onOpening: { root.popupBackdropVisible = true; modalBackdrop.scheduleSnapshot() }
        onOpenedForBackdrop: modalBackdrop.scheduleSnapshot()
        onClosedForBackdrop: root.popupBackdropVisible = false

        ColumnLayout {
            anchors.fill: parent
            spacing: 14

            Label {
                Layout.fillWidth: true
                text: t("customAppearanceIntro")
                color: root.mutedText
                font.pixelSize: Math.round(12 * root.textScale)
                wrapMode: Text.WordWrap
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 72
                radius: 10
                color: root.panelAltColor
                border.color: root.borderColor
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 3
                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: t("accentHue"); color: root.textColor; font.bold: true; Layout.fillWidth: true }
                        Label { text: Math.round(blanky.customHue) + "°"; color: root.accentColor; font.bold: true }
                    }
                    Slider { Layout.fillWidth: true; from: 0; to: 360; stepSize: 1; value: blanky.customHue; onMoved: blanky.setCustomHue(value) }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 72
                radius: 10
                color: root.panelAltColor
                border.color: root.borderColor
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 3
                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: t("interfaceBrightness"); color: root.textColor; font.bold: true; Layout.fillWidth: true }
                        Label { text: Math.round(blanky.customBrightness) + "%"; color: root.accentColor; font.bold: true }
                    }
                    Slider { Layout.fillWidth: true; from: 20; to: 80; stepSize: 1; value: blanky.customBrightness; onMoved: blanky.setCustomBrightness(value) }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 72
                radius: 10
                color: root.panelAltColor
                border.color: root.borderColor
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 3
                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: t("textContrast"); color: root.textColor; font.bold: true; Layout.fillWidth: true }
                        Label { text: Math.round(blanky.customContrast) + "%"; color: root.accentColor; font.bold: true }
                    }
                    Slider { Layout.fillWidth: true; from: 60; to: 100; stepSize: 1; value: blanky.customContrast; onMoved: blanky.setCustomContrast(value) }
                }
            }
        }
    }

    FloatingPanel {
        id: voicePanel
        width: 980
        height: 590
        panelTitle: t("voiceTitle")
        panelColor: root.panelColor
        borderColor: root.borderColor
        titleColor: root.textColor
        onOpening: { root.popupBackdropVisible = true; modalBackdrop.scheduleSnapshot() }
        onOpenedForBackdrop: modalBackdrop.scheduleSnapshot()
        onClosedForBackdrop: root.popupBackdropVisible = false

        ColumnLayout {
            anchors.fill: parent
            spacing: 12

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: voiceIntro.implicitHeight + 24
                color: root.panelAltColor
                border.color: root.borderColor
                border.width: 1
                radius: 14

                Column {
                    id: voiceIntro
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 12
                    spacing: 6

                    Label {
                        width: parent.width
                        text: t("voiceIntroTitle")
                        color: root.textColor
                        font.pixelSize: 16
                        font.bold: true
                    }

                    Label {
                        width: parent.width
                        wrapMode: Text.WordWrap
                        text: t("voiceIntroText")
                        color: root.mutedText
                        font.pixelSize: 13
                    }
                }
            }

            GridLayout {
                id: voiceGrid
                Layout.fillWidth: true
                Layout.fillHeight: true
                columns: 3
                columnSpacing: 10
                rowSpacing: 10

                Repeater {
                    model: root.ttsVoiceModel

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumHeight: 168
                        radius: 14
                        readonly property bool selectedVoice: modelData === blanky.ttsVoice
                        color: selectedVoice ? Qt.lighter(root.panelAltColor, 1.35) : root.panelAltColor
                        border.color: selectedVoice ? "#48d66b" : root.borderColor
                        border.width: selectedVoice ? 2 : 1

                        MouseArea {
                            anchors.fill: parent
                            z: 0
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: blanky.setTtsVoice(modelData)
                        }

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 6
                            z: 1

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 7

                                Label {
                                    text: selectedVoice ? "●" : "○"
                                    color: selectedVoice ? "#48d66b" : root.mutedText
                                    font.pixelSize: 18
                                    font.bold: true
                                }

                                Label {
                                    text: root.voiceName(modelData)
                                    color: root.textColor
                                    font.pixelSize: 17
                                    font.bold: true
                                    Layout.fillWidth: true
                                }

                                Label {
                                    visible: selectedVoice
                                    text: t("selected")
                                    color: "#48d66b"
                                    font.pixelSize: 10
                                    font.bold: true
                                }
                            }

                            Label {
                                Layout.fillWidth: true
                                text: root.voiceMood(modelData)
                                color: root.mutedText
                                font.pixelSize: 11
                                font.bold: true
                                elide: Text.ElideRight
                            }

                            Label {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                wrapMode: Text.WordWrap
                                text: root.voiceDescription(modelData)
                                color: root.textColor
                                font.pixelSize: 12
                            }

                            MenuActionButton {
                                Layout.alignment: Qt.AlignRight
                                Layout.preferredWidth: 150
                                Layout.preferredHeight: 34
                                text: "\u25B6 " + t("previewVoice")
                                        accentColor: root.accentColor
                                textColor: root.textColor
                                mutedText: root.mutedText
                                borderColor: root.borderColor
                                panelColor: root.panelColor
                                onClicked: blanky.previewTtsVoice(modelData)
                            }
                        }
                    }
                }
            }
        }
    }

    FloatingPanel {
        id: audioSettingsLegacyPanel
        visible: false
        width: 780
        height: 650
        panelTitle: t("audioTitle")
        panelColor: root.panelColor
        borderColor: root.borderColor
        titleColor: root.textColor
        onOpening: { root.popupBackdropVisible = true; modalBackdrop.scheduleSnapshot() }
        onOpenedForBackdrop: modalBackdrop.scheduleSnapshot()
        onClosedForBackdrop: root.popupBackdropVisible = false

        ScrollView {
            id: audioScroll
            anchors.fill: parent
            clip: true
            rightPadding: Math.round(8 * root.textScale)
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical.policy: ScrollBar.AlwaysOn

            Column {
                width: Math.max(audioScroll.width - 20, 680)
                spacing: 12

                Rectangle {
                    width: parent.width
                    color: root.panelAltColor
                    border.color: root.borderColor
                    border.width: 1
                    radius: 14
                    implicitHeight: introCol.implicitHeight + 24

                    Column {
                        id: introCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 12
                        spacing: 8

                        Label {
                            width: parent.width
                            wrapMode: Text.WordWrap
                            text: t("audioRecommended")
                            color: root.textColor
                            font.pixelSize: 14
                            font.bold: true
                        }

                        Label {
                            width: parent.width
                            wrapMode: Text.WordWrap
                            text: t("audioGuidance")
                            color: root.mutedText
                            font.pixelSize: 13
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    color: root.panelAltColor
                    border.color: root.borderColor
                    border.width: 1
                    radius: 14
                    implicitHeight: profileCol.implicitHeight + 24

                    Column {
                        id: profileCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 12
                        spacing: 10

                        Label {
                            text: t("profiles")
                            color: root.textColor
                            font.pixelSize: 15
                            font.bold: true
                        }

                        RowLayout {
                            width: parent.width
                            spacing: 8

                            Button {
                                text: (blanky.audioInputPreset === "simple" ? "\u2022 " : "") + t("simple")
                                Layout.fillWidth: true
                                onClicked: blanky.setAudioInputPreset("simple")
                            }

                            Button {
                                text: (blanky.audioInputPreset === "balanced" ? "\u2022 " : "") + t("balanced")
                                Layout.fillWidth: true
                                onClicked: blanky.setAudioInputPreset("balanced")
                            }

                            Button {
                                text: (blanky.audioInputPreset === "noisy" ? "\u2022 " : "") + t("noisy")
                                Layout.fillWidth: true
                                onClicked: blanky.setAudioInputPreset("noisy")
                            }
                        }

                        Label {
                            width: parent.width
                            wrapMode: Text.WordWrap
                            color: root.mutedText
                            text: t("profileHelp")
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    color: root.panelAltColor
                    border.color: root.borderColor
                    border.width: 1
                    radius: 14
                    implicitHeight: sensitivityCol.implicitHeight + 24

                    Column {
                        id: sensitivityCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 12
                        spacing: 8

                        RowLayout {
                            width: parent.width

                            Label {
                                text: t("startSensitivity")
                                color: root.textColor
                                font.pixelSize: 15
                                font.bold: true
                                Layout.fillWidth: true
                            }

                            Label {
                                text: Math.round(blanky.micSensitivity)
                                color: root.mutedText
                                font.pixelSize: 14
                                font.bold: true
                            }
                        }

                        Slider {
                            width: parent.width
                            from: 0
                            to: 100
                            stepSize: 1
                            value: blanky.micSensitivity
                            onMoved: blanky.setMicSensitivity(value)
                        }

                        Label {
                            width: parent.width
                            wrapMode: Text.WordWrap
                            color: root.mutedText
                            text: t("sensitivityHelp")
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    color: root.panelAltColor
                    border.color: root.borderColor
                    border.width: 1
                    radius: 14
                    implicitHeight: timingCol.implicitHeight + 24

                    Column {
                        id: timingCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 12
                        spacing: 12

                        Label {
                            text: t("captureTiming")
                            color: root.textColor
                            font.pixelSize: 15
                            font.bold: true
                        }

                        Label {
                            text: t("maxWait") + ": " + formatFixed(blanky.micWaitForSpeech, 2) + " s"
                            color: root.textColor
                            font.bold: true
                        }

                        Slider {
                            width: parent.width
                            from: 0.35
                            to: 2.50
                            stepSize: 0.05
                            value: blanky.micWaitForSpeech
                            onMoved: blanky.setMicWaitForSpeech(value)
                        }

                        Label {
                            width: parent.width
                            wrapMode: Text.WordWrap
                            color: root.mutedText
                            text: t("maxWaitHelp")
                        }

                        Label {
                            text: t("minimumCommand") + ": " + formatFixed(blanky.micMinCommand, 2) + " s"
                            color: root.textColor
                            font.bold: true
                        }

                        Slider {
                            width: parent.width
                            from: 0.25
                            to: 1.80
                            stepSize: 0.05
                            value: blanky.micMinCommand
                            onMoved: blanky.setMicMinCommand(value)
                        }

                        Label {
                            width: parent.width
                            wrapMode: Text.WordWrap
                            color: root.mutedText
                            text: t("minimumCommandHelp")
                        }

                        Label {
                            text: t("silenceHold") + ": " + formatFixed(blanky.micSilenceHold, 2) + " s"
                            color: root.textColor
                            font.bold: true
                        }

                        Slider {
                            width: parent.width
                            from: 0.18
                            to: 1.00
                            stepSize: 0.05
                            value: blanky.micSilenceHold
                            onMoved: blanky.setMicSilenceHold(value)
                        }

                        Label {
                            width: parent.width
                            wrapMode: Text.WordWrap
                            color: root.mutedText
                            text: t("silenceHelp")
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    color: root.panelAltColor
                    border.color: root.borderColor
                    border.width: 1
                    radius: 14
                    implicitHeight: gainCol.implicitHeight + 24

                    Column {
                        id: gainCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 12
                        spacing: 8

                        Label {
                            text: t("microphoneGain") + ": " + formatFixed(blanky.micMaxGain, 2) + "x"
                            color: root.textColor
                            font.pixelSize: 15
                            font.bold: true
                        }

                        Slider {
                            width: parent.width
                            from: 1.0
                            to: 6.0
                            stepSize: 0.1
                            value: blanky.micMaxGain
                            onMoved: blanky.setMicMaxGain(value)
                        }

                        Label {
                            width: parent.width
                            wrapMode: Text.WordWrap
                            color: root.mutedText
                            text: t("gainHelp")
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    color: root.panelAltColor
                    border.color: root.borderColor
                    border.width: 1
                    radius: 14
                    implicitHeight: filtersCol.implicitHeight + 24

                    Column {
                        id: filtersCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 12
                        spacing: 12

                        Label {
                            text: t("optionalFilters")
                            color: root.textColor
                            font.pixelSize: 15
                            font.bold: true
                        }

                        RowLayout {
                            width: parent.width
                            spacing: 10

                            Switch {
                                checked: blanky.micHighpassEnabled
                                onClicked: blanky.setMicHighpassEnabled(checked)
                            }

                            Column {
                                Layout.fillWidth: true
                                spacing: 4

                                Label {
                                    text: t("highPass")
                                    color: root.textColor
                                    font.bold: true
                                }

                                Label {
                                    width: parent.width
                                    wrapMode: Text.WordWrap
                                    color: root.mutedText
                                    text: t("highPassHelp")
                                }
                            }
                        }

                        RowLayout {
                            width: parent.width
                            spacing: 10

                            Switch {
                                checked: blanky.micNoiseGateEnabled
                                onClicked: blanky.setMicNoiseGateEnabled(checked)
                            }

                            Column {
                                Layout.fillWidth: true
                                spacing: 4

                                Label {
                                    text: t("noiseGate")
                                    color: root.textColor
                                    font.bold: true
                                }

                                Label {
                                    width: parent.width
                                    wrapMode: Text.WordWrap
                                    color: root.mutedText
                                    text: t("noiseGateHelp")
                                }
                            }
                        }

                        RowLayout {
                            width: parent.width
                            spacing: 10

                            Switch {
                                checked: blanky.micNoiseReductionEnabled
                                onClicked: blanky.setMicNoiseReductionEnabled(checked)
                            }

                            Column {
                                Layout.fillWidth: true
                                spacing: 4

                                Label {
                                    text: t("noiseReduction")
                                    color: root.textColor
                                    font.bold: true
                                }

                                Label {
                                    width: parent.width
                                    wrapMode: Text.WordWrap
                                    color: root.mutedText
                                    text: t("noiseReductionHelp")
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    color: root.panelAltColor
                    border.color: root.borderColor
                    border.width: 1
                    radius: 14
                    implicitHeight: actionCol.implicitHeight + 24

                    Column {
                        id: actionCol
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 12
                        spacing: 10

                        Label {
                            text: t("quickActions")
                            color: root.textColor
                            font.pixelSize: 15
                            font.bold: true
                        }

                        RowLayout {
                            width: parent.width
                            spacing: 10

                            Button {
                                text: t("testBeep")
                                Layout.preferredWidth: 150
                                onClicked: blanky.testBeep()
                            }

                            Button {
                                text: t("resetRecommended")
                                Layout.preferredWidth: 170
                                onClicked: blanky.resetAudioInputSettings()
                            }

                            Item { Layout.fillWidth: true }
                        }
                    }
                }
            }
        }
    }

    FloatingPanel {
        id: audioSettingsPanel
        width: 840
        height: 700
        panelTitle: t("audioTitle")
        panelColor: root.panelColor
        borderColor: root.borderColor
        titleColor: root.textColor
        onOpening: { root.popupBackdropVisible = true; modalBackdrop.scheduleSnapshot() }
        onOpenedForBackdrop: modalBackdrop.scheduleSnapshot()
        onClosedForBackdrop: root.popupBackdropVisible = settingsPanel.visible

        MenuActionButton {
            anchors.left: parent.left
            anchors.top: parent.top
            z: 2
            text: "\u2190 " + t("backToSettings")
            width: 150
            height: 30
            accentColor: root.accentColor
            textColor: root.textColor
            mutedText: root.mutedText
            borderColor: root.borderColor
            panelColor: root.panelAltColor
            onClicked: { audioSettingsPanel.close(); settingsPanel.open() }
        }

        ScrollView {
            id: redesignedAudioScroll
            anchors.fill: parent
            anchors.topMargin: 38
            clip: true
            rightPadding: Math.round(14 * root.textScale)
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical.policy: ScrollBar.AlwaysOn

            Column {
                width: Math.max(redesignedAudioScroll.availableWidth - Math.round(22 * root.textScale), 740)
                spacing: 12

                Rectangle {
                    width: parent.width
                    implicitHeight: modeColumn.implicitHeight + 24
                    radius: 14
                    color: root.panelAltColor
                    border.color: root.borderColor
                    border.width: 1

                    Column {
                        id: modeColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 12
                        spacing: 10

                        RowLayout {
                            width: parent.width
                            Label {
                                text: t("audioMode")
                                color: root.textColor
                                font.pixelSize: 16
                                font.bold: true
                                Layout.fillWidth: true
                            }
                        }

                        RowLayout {
                            width: parent.width
                            spacing: 8
                            MenuActionButton {
                                text: "\u25CF " + t("automaticMode")
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                accentColor: blanky.audioSettingsMode === "auto" ? "#48d66b" : root.borderColor
                                textColor: root.textColor
                                mutedText: root.mutedText
                                borderColor: root.borderColor
                                panelColor: root.panelColor
                                toolTip: t("automaticModeHelp")
                                onClicked: root.selectAudioMode("auto")
                            }
                            MenuActionButton {
                                text: "\u270E " + t("manualMode")
                                Layout.fillWidth: true
                                Layout.preferredHeight: 36
                                accentColor: blanky.audioSettingsMode === "manual" ? "#f8c25d" : root.borderColor
                                textColor: root.textColor
                                mutedText: root.mutedText
                                borderColor: root.borderColor
                                panelColor: root.panelColor
                                toolTip: t("manualModeHelp")
                                onClicked: root.selectAudioMode("manual")
                            }
                        }

                        Label {
                            visible: blanky.audioSettingsMode === "auto"
                            text: t("profiles")
                            color: root.mutedText
                            font.pixelSize: 13
                            font.bold: true
                        }

                        RowLayout {
                            visible: blanky.audioSettingsMode === "auto"
                            width: parent.width
                            spacing: 8
                            MenuActionButton {
                                text: t("simple")
                                Layout.fillWidth: true
                                Layout.preferredHeight: 34
                                accentColor: blanky.audioSelectedProfile === "simple" ? "#48d66b" : root.borderColor
                                textColor: root.textColor
                                mutedText: root.mutedText
                                borderColor: root.borderColor
                                panelColor: root.panelColor
                                toolTip: t("simpleProfileHelp")
                                onClicked: root.selectAudioProfile("simple")
                            }
                            MenuActionButton {
                                text: t("balanced")
                                Layout.fillWidth: true
                                Layout.preferredHeight: 34
                                accentColor: blanky.audioSelectedProfile === "balanced" ? "#63cbff" : root.borderColor
                                textColor: root.textColor
                                mutedText: root.mutedText
                                borderColor: root.borderColor
                                panelColor: root.panelColor
                                toolTip: t("balancedProfileHelp")
                                onClicked: root.selectAudioProfile("balanced")
                            }
                            MenuActionButton {
                                text: t("noisy")
                                Layout.fillWidth: true
                                Layout.preferredHeight: 34
                                accentColor: blanky.audioSelectedProfile === "noisy" ? "#f8c25d" : root.borderColor
                                textColor: root.textColor
                                mutedText: root.mutedText
                                borderColor: root.borderColor
                                panelColor: root.panelColor
                                toolTip: t("noisyProfileHelp")
                                onClicked: root.selectAudioProfile("noisy")
                            }
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    implicitHeight: adjustmentsColumn.implicitHeight + 24
                    radius: 14
                    color: root.panelAltColor
                    border.color: root.borderColor
                    border.width: 1

                    Column {
                        id: adjustmentsColumn
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 12
                        spacing: 10

                        RowLayout {
                            width: parent.width
                            Label {
                                text: t("audioAdjustments")
                                color: root.textColor
                                font.pixelSize: 16
                                font.bold: true
                                Layout.fillWidth: true
                            }
                            Label {
                                text: blanky.audioSettingsMode === "manual" ? t("manualMode") : t("automaticMode")
                                color: blanky.audioSettingsMode === "manual" ? "#f8c25d" : "#48d66b"
                                font.pixelSize: 12
                                font.bold: true
                            }
                        }

                        Rectangle {
                            width: parent.width; height: 72; radius: 10
                            color: root.panelColor; border.color: root.borderColor; border.width: 1
                            opacity: root.audioSettingIsEditable("sensitivity") ? 1 : 0.56
                            HoverHandler { id: sensitivityHintHover; enabled: !sensitivityUnlock.hovered }
                            BlankyToolTip { visible: sensitivityHintHover.hovered && !sensitivityUnlock.hovered; text: t("sensitivityHelp"); surfaceColor: root.panelAltColor; outlineColor: root.borderColor; foregroundColor: root.textColor }
                            Column {
                                anchors.fill: parent; anchors.margins: 9; spacing: 4
                                RowLayout {
                                    width: parent.width
                                    Label { text: t("startSensitivity"); color: root.textColor; font.bold: true; Layout.fillWidth: true }
                                    MenuActionButton { id: sensitivityUnlock; visible: !root.audioSettingIsEditable("sensitivity"); text: "\u270E"; iconOnly: true; textPixelSize: 13; Layout.preferredWidth: 25; Layout.preferredHeight: 24; accentColor: "#f8c25d"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor; toolTip: t("unlockAudioSetting"); onClicked: root.unlockAudioSetting("sensitivity") }
                                    Label { text: Math.round(blanky.micSensitivity); color: root.mutedText; font.bold: true }
                                }
                                Slider { width: parent.width; from: 0; to: 100; stepSize: 1; value: blanky.micSensitivity; enabled: root.audioSettingIsEditable("sensitivity"); onMoved: blanky.setMicSensitivity(value) }
                            }
                        }

                        Rectangle {
                            width: parent.width; height: 72; radius: 10
                            color: root.panelColor; border.color: root.borderColor; border.width: 1
                            opacity: root.audioSettingIsEditable("wait") ? 1 : 0.56
                            HoverHandler { id: waitHintHover; enabled: !waitUnlock.hovered }
                            BlankyToolTip { visible: waitHintHover.hovered && !waitUnlock.hovered; text: t("maxWaitHelp"); surfaceColor: root.panelAltColor; outlineColor: root.borderColor; foregroundColor: root.textColor }
                            Column {
                                anchors.fill: parent; anchors.margins: 9; spacing: 4
                                RowLayout {
                                    width: parent.width
                                    Label { text: t("maxWait"); color: root.textColor; font.bold: true; Layout.fillWidth: true }
                                    MenuActionButton { id: waitUnlock; visible: !root.audioSettingIsEditable("wait"); text: "\u270E"; iconOnly: true; textPixelSize: 13; Layout.preferredWidth: 25; Layout.preferredHeight: 24; accentColor: "#f8c25d"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor; toolTip: t("unlockAudioSetting"); onClicked: root.unlockAudioSetting("wait") }
                                    Label { text: formatFixed(blanky.micWaitForSpeech, 2) + " s"; color: root.mutedText; font.bold: true }
                                }
                                Slider { width: parent.width; from: 0.35; to: 2.50; stepSize: 0.05; value: blanky.micWaitForSpeech; enabled: root.audioSettingIsEditable("wait"); onMoved: blanky.setMicWaitForSpeech(value) }
                            }
                        }

                        Rectangle {
                            width: parent.width; height: 72; radius: 10
                            color: root.panelColor; border.color: root.borderColor; border.width: 1
                            opacity: root.audioSettingIsEditable("minimum") ? 1 : 0.56
                            HoverHandler { id: minimumHintHover; enabled: !minimumUnlock.hovered }
                            BlankyToolTip { visible: minimumHintHover.hovered && !minimumUnlock.hovered; text: t("minimumCommandHelp"); surfaceColor: root.panelAltColor; outlineColor: root.borderColor; foregroundColor: root.textColor }
                            Column {
                                anchors.fill: parent; anchors.margins: 9; spacing: 4
                                RowLayout {
                                    width: parent.width
                                    Label { text: t("minimumCommand"); color: root.textColor; font.bold: true; Layout.fillWidth: true }
                                    MenuActionButton { id: minimumUnlock; visible: !root.audioSettingIsEditable("minimum"); text: "\u270E"; iconOnly: true; textPixelSize: 13; Layout.preferredWidth: 25; Layout.preferredHeight: 24; accentColor: "#f8c25d"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor; toolTip: t("unlockAudioSetting"); onClicked: root.unlockAudioSetting("minimum") }
                                    Label { text: formatFixed(blanky.micMinCommand, 2) + " s"; color: root.mutedText; font.bold: true }
                                }
                                Slider { width: parent.width; from: 0.25; to: 1.80; stepSize: 0.05; value: blanky.micMinCommand; enabled: root.audioSettingIsEditable("minimum"); onMoved: blanky.setMicMinCommand(value) }
                            }
                        }

                        Rectangle {
                            width: parent.width; height: 72; radius: 10
                            color: root.panelColor; border.color: root.borderColor; border.width: 1
                            opacity: root.audioSettingIsEditable("silence") ? 1 : 0.56
                            HoverHandler { id: silenceHintHover; enabled: !silenceUnlock.hovered }
                            BlankyToolTip { visible: silenceHintHover.hovered && !silenceUnlock.hovered; text: t("silenceHelp"); surfaceColor: root.panelAltColor; outlineColor: root.borderColor; foregroundColor: root.textColor }
                            Column {
                                anchors.fill: parent; anchors.margins: 9; spacing: 4
                                RowLayout {
                                    width: parent.width
                                    Label { text: t("silenceHold"); color: root.textColor; font.bold: true; Layout.fillWidth: true }
                                    MenuActionButton { id: silenceUnlock; visible: !root.audioSettingIsEditable("silence"); text: "\u270E"; iconOnly: true; textPixelSize: 13; Layout.preferredWidth: 25; Layout.preferredHeight: 24; accentColor: "#f8c25d"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor; toolTip: t("unlockAudioSetting"); onClicked: root.unlockAudioSetting("silence") }
                                    Label { text: formatFixed(blanky.micSilenceHold, 2) + " s"; color: root.mutedText; font.bold: true }
                                }
                                Slider { width: parent.width; from: 0.18; to: 1.00; stepSize: 0.05; value: blanky.micSilenceHold; enabled: root.audioSettingIsEditable("silence"); onMoved: blanky.setMicSilenceHold(value) }
                            }
                        }

                        Rectangle {
                            width: parent.width; height: 72; radius: 10
                            color: root.panelColor; border.color: root.borderColor; border.width: 1
                            opacity: root.audioSettingIsEditable("gain") ? 1 : 0.56
                            HoverHandler { id: gainHintHover; enabled: !gainUnlock.hovered }
                            BlankyToolTip { visible: gainHintHover.hovered && !gainUnlock.hovered; text: t("gainHelp"); surfaceColor: root.panelAltColor; outlineColor: root.borderColor; foregroundColor: root.textColor }
                            Column {
                                anchors.fill: parent; anchors.margins: 9; spacing: 4
                                RowLayout {
                                    width: parent.width
                                    Label { text: t("microphoneGain"); color: root.textColor; font.bold: true; Layout.fillWidth: true }
                                    MenuActionButton { id: gainUnlock; visible: !root.audioSettingIsEditable("gain"); text: "\u270E"; iconOnly: true; textPixelSize: 13; Layout.preferredWidth: 25; Layout.preferredHeight: 24; accentColor: "#f8c25d"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor; toolTip: t("unlockAudioSetting"); onClicked: root.unlockAudioSetting("gain") }
                                    Label { text: formatFixed(blanky.micMaxGain, 2) + "x"; color: root.mutedText; font.bold: true }
                                }
                                Slider { width: parent.width; from: 1.0; to: 6.0; stepSize: 0.1; value: blanky.micMaxGain; enabled: root.audioSettingIsEditable("gain"); onMoved: blanky.setMicMaxGain(value) }
                            }
                        }

                        Label { text: t("optionalFilters"); color: root.textColor; font.pixelSize: 14; font.bold: true; topPadding: 4 }

                        RowLayout {
                            width: parent.width
                            opacity: root.audioSettingIsEditable("highpass") ? 1 : 0.56
                            HoverHandler { id: highPassHintHover; enabled: !highPassUnlock.hovered }
                            BlankyToolTip { visible: highPassHintHover.hovered && !highPassUnlock.hovered; text: t("highPassHelp"); surfaceColor: root.panelAltColor; outlineColor: root.borderColor; foregroundColor: root.textColor }
                            Switch { checked: blanky.micHighpassEnabled; enabled: root.audioSettingIsEditable("highpass"); onClicked: blanky.setMicHighpassEnabled(checked) }
                            Label { text: t("highPass"); color: root.textColor; Layout.fillWidth: true }
                            MenuActionButton { id: highPassUnlock; visible: !root.audioSettingIsEditable("highpass"); text: "\u270E"; iconOnly: true; textPixelSize: 13; Layout.preferredWidth: 25; Layout.preferredHeight: 24; accentColor: "#f8c25d"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor; toolTip: t("unlockAudioSetting"); onClicked: root.unlockAudioSetting("highpass") }
                        }
                        RowLayout {
                            width: parent.width
                            opacity: root.audioSettingIsEditable("gate") ? 1 : 0.56
                            HoverHandler { id: noiseGateHintHover; enabled: !noiseGateUnlock.hovered }
                            BlankyToolTip { visible: noiseGateHintHover.hovered && !noiseGateUnlock.hovered; text: t("noiseGateHelp"); surfaceColor: root.panelAltColor; outlineColor: root.borderColor; foregroundColor: root.textColor }
                            Switch { checked: blanky.micNoiseGateEnabled; enabled: root.audioSettingIsEditable("gate"); onClicked: blanky.setMicNoiseGateEnabled(checked) }
                            Label { text: t("noiseGate"); color: root.textColor; Layout.fillWidth: true }
                            MenuActionButton { id: noiseGateUnlock; visible: !root.audioSettingIsEditable("gate"); text: "\u270E"; iconOnly: true; textPixelSize: 13; Layout.preferredWidth: 25; Layout.preferredHeight: 24; accentColor: "#f8c25d"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor; toolTip: t("unlockAudioSetting"); onClicked: root.unlockAudioSetting("gate") }
                        }
                        RowLayout {
                            width: parent.width
                            opacity: root.audioSettingIsEditable("reduction") ? 1 : 0.56
                            HoverHandler { id: noiseReductionHintHover; enabled: !noiseReductionUnlock.hovered }
                            BlankyToolTip { visible: noiseReductionHintHover.hovered && !noiseReductionUnlock.hovered; text: t("noiseReductionHelp"); surfaceColor: root.panelAltColor; outlineColor: root.borderColor; foregroundColor: root.textColor }
                            Switch { checked: blanky.micNoiseReductionEnabled; enabled: root.audioSettingIsEditable("reduction"); onClicked: blanky.setMicNoiseReductionEnabled(checked) }
                            Label { text: t("noiseReduction"); color: root.textColor; Layout.fillWidth: true }
                            MenuActionButton { id: noiseReductionUnlock; visible: !root.audioSettingIsEditable("reduction"); text: "\u270E"; iconOnly: true; textPixelSize: 13; Layout.preferredWidth: 25; Layout.preferredHeight: 24; accentColor: "#f8c25d"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor; toolTip: t("unlockAudioSetting"); onClicked: root.unlockAudioSetting("reduction") }
                        }
                    }
                }

                RowLayout {
                    width: parent.width
                    spacing: 10
                    MenuActionButton {
                        text: "\u266B " + t("testBeep")
                        Layout.preferredWidth: 150
                        Layout.preferredHeight: 36
                        accentColor: "#63cbff"
                        textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor
                        onClicked: blanky.testBeep()
                    }
                    MenuActionButton {
                        text: "\u21BA " + t("resetRecommended")
                        Layout.preferredWidth: 190
                        Layout.preferredHeight: 36
                                        accentColor: root.successColor
                        textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor
                        onClicked: { root.audioManualOverrides = ({}); blanky.resetAudioInputSettings() }
                    }
                    Item { Layout.fillWidth: true }
                    MenuActionButton {
                        text: "\u2261 " + t("viewAudioLogs")
                        Layout.preferredWidth: 135
                        Layout.preferredHeight: 36
                        accentColor: "#f8c25d"
                        textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor
                        onClicked: audioLogsPanel.open()
                    }
                }
            }
        }
    }

    FloatingPanel {
        id: settingsPanel
        width: 700
        height: 390
        panelTitle: t("settingsTitle")
        panelColor: root.panelColor
        borderColor: root.borderColor
        titleColor: root.textColor
        textColor: root.textColor
        onOpening: { root.popupBackdropVisible = true; modalBackdrop.scheduleSnapshot() }
        onOpenedForBackdrop: modalBackdrop.scheduleSnapshot()
        onClosedForBackdrop: root.popupBackdropVisible = audioSettingsPanel.visible || communicationsSettingsPanel.visible

        ColumnLayout {
            anchors.fill: parent
            spacing: 14

            Label {
                Layout.fillWidth: true
                text: t("settingsIntro")
                color: root.mutedText
                wrapMode: Text.WordWrap
                font.pixelSize: 13
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 14

                Rectangle {
                    id: audioSettingsCard
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 14
                    property bool hovered: audioSettingsCardMouse.containsMouse
                    color: hovered ? Qt.lighter(root.panelAltColor, 1.08) : root.panelAltColor
                    border.color: hovered ? root.textColor : root.accentColor
                    border.width: hovered ? 2 : 1
                    scale: hovered ? 1.015 : 1.0
                    Behavior on color { ColorAnimation { duration: 150 } }
                    Behavior on scale { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 11
                        RowLayout {
                            Layout.fillWidth: true
                            Rectangle {
                                Layout.preferredWidth: 58
                                Layout.preferredHeight: 58
                                radius: 29
                                color: Qt.darker(root.accentColor, 1.65)
                                border.color: root.accentColor
                                border.width: 1
                                Label { anchors.centerIn: parent; text: "\uD83C\uDFA4"; color: root.textColor; font.pixelSize: 28 }
                            }
                            Item { Layout.fillWidth: true }
                            Label { text: "\u203A"; color: root.accentColor; font.pixelSize: 34; font.bold: true }
                        }
                        Label { text: t("audioTitle"); color: root.textColor; font.bold: true; font.pixelSize: 19; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                        Label { text: t("audioSettingsCardInfo"); color: root.mutedText; Layout.fillWidth: true; wrapMode: Text.WordWrap; font.pixelSize: 13 }
                        Item { Layout.fillWidth: true; Layout.fillHeight: true }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 32
                            radius: 8
                            color: audioSettingsCard.hovered ? root.accentColor : Qt.darker(root.panelColor, 1.05)
                            border.color: root.accentColor
                            border.width: 1
                            RowLayout {
                                anchors.fill: parent; anchors.leftMargin: 10; anchors.rightMargin: 10
                                Label { text: t("openSettingsCard"); color: audioSettingsCard.hovered ? root.panelColor : root.textColor; font.bold: true; font.pixelSize: 12; Layout.fillWidth: true }
                                Label { text: "\u2192"; color: audioSettingsCard.hovered ? root.panelColor : root.accentColor; font.bold: true; font.pixelSize: 15 }
                            }
                        }
                    }
                    MouseArea { id: audioSettingsCardMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { settingsPanel.close(); audioSettingsPanel.open() } }
                }

                Rectangle {
                    id: communicationsSettingsCard
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 14
                    property bool hovered: communicationsSettingsCardMouse.containsMouse
                    color: hovered ? Qt.lighter(root.panelAltColor, 1.08) : root.panelAltColor
                    border.color: hovered ? root.textColor : root.successColor
                    border.width: hovered ? 2 : 1
                    scale: hovered ? 1.015 : 1.0
                    Behavior on color { ColorAnimation { duration: 150 } }
                    Behavior on scale { NumberAnimation { duration: 150; easing.type: Easing.OutCubic } }
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 11
                        RowLayout {
                            Layout.fillWidth: true
                            Rectangle {
                                Layout.preferredWidth: 58
                                Layout.preferredHeight: 58
                                radius: 29
                                color: Qt.darker(root.successColor, 1.65)
                                border.color: root.successColor
                                border.width: 1
                                Label { anchors.centerIn: parent; text: "\uD83D\uDD17"; color: root.textColor; font.pixelSize: 28 }
                            }
                            Item { Layout.fillWidth: true }
                            Label { text: "\u203A"; color: root.successColor; font.pixelSize: 34; font.bold: true }
                        }
                        Label { text: t("communicationsSettings"); color: root.textColor; font.bold: true; font.pixelSize: 19; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                        Label { text: t("communicationsSettingsCardInfo"); color: root.mutedText; Layout.fillWidth: true; wrapMode: Text.WordWrap; font.pixelSize: 13 }
                        Item { Layout.fillWidth: true; Layout.fillHeight: true }
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 32
                            radius: 8
                            color: communicationsSettingsCard.hovered ? root.successColor : Qt.darker(root.panelColor, 1.05)
                            border.color: root.successColor
                            border.width: 1
                            RowLayout {
                                anchors.fill: parent; anchors.leftMargin: 10; anchors.rightMargin: 10
                                Label { text: t("openSettingsCard"); color: communicationsSettingsCard.hovered ? root.panelColor : root.textColor; font.bold: true; font.pixelSize: 12; Layout.fillWidth: true }
                                Label { text: "\u2192"; color: communicationsSettingsCard.hovered ? root.panelColor : root.successColor; font.bold: true; font.pixelSize: 15 }
                            }
                        }
                    }
                    MouseArea { id: communicationsSettingsCardMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { settingsPanel.close(); communicationsSettingsPanel.open() } }
                }
            }
        }
    }

    FloatingPanel {
        id: communicationsSettingsPanel
        width: 760
        height: 650
        panelTitle: t("communicationsSettings")
        panelColor: root.panelColor
        borderColor: root.borderColor
        titleColor: root.textColor
        textColor: root.textColor
        property bool mqttEditable: false
        property bool opcuaEditable: false
        property bool aiEditable: false
        onOpening: {
            mqttEditable = false
            opcuaEditable = false
            aiEditable = false
            mqttHostField.text = blanky.mqttBrokerHost
            mqttPortField.text = String(blanky.mqttBrokerPort)
            mqttPrefixField.text = blanky.mqttTopicPrefix
            opcuaUrlField.text = blanky.opcuaUrl
            openAiKeyField.text = ""
            root.popupBackdropVisible = true
            modalBackdrop.scheduleSnapshot()
        }
        onOpenedForBackdrop: modalBackdrop.scheduleSnapshot()
        onClosedForBackdrop: root.popupBackdropVisible = settingsPanel.visible

        MenuActionButton {
            anchors.left: parent.left
            anchors.top: parent.top
            z: 2
            text: "\u2190 " + t("backToSettings")
            width: 150
            height: 30
            accentColor: root.accentColor
            textColor: root.textColor
            mutedText: root.mutedText
            borderColor: root.borderColor
            panelColor: root.panelAltColor
            onClicked: { communicationsSettingsPanel.close(); settingsPanel.open() }
        }

        ScrollView {
            id: communicationsSettingsScroll
            anchors.fill: parent
            anchors.topMargin: 38
            clip: true
            rightPadding: Math.round(14 * root.textScale)
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical.policy: ScrollBar.AsNeeded

            Column {
                width: Math.max(communicationsSettingsScroll.availableWidth - Math.round(22 * root.textScale), 650)
                spacing: 12

                Rectangle {
                    width: parent.width
                    implicitHeight: communicationsIntro.implicitHeight + 22
                    radius: 12
                    color: root.panelAltColor
                    border.color: root.borderColor
                    border.width: 1
                    Label {
                        id: communicationsIntro
                        anchors.fill: parent
                        anchors.margins: 11
                        text: t("communicationsSettingsIntro")
                        color: root.textColor
                        wrapMode: Text.WordWrap
                        font.pixelSize: 13
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                Label { text: t("automaticConnections"); color: root.textColor; font.pixelSize: 16; font.bold: true }

                RowLayout {
                    width: parent.width
                    spacing: 10
                    Rectangle {
                        Layout.fillWidth: true; Layout.preferredHeight: 88; radius: 12
                        color: root.panelAltColor; border.color: root.borderColor; border.width: 1
                        Column { anchors.fill: parent; anchors.margins: 11; spacing: 5
                            Label { text: "\uD83C\uDFA4 " + t("microphone"); color: root.textColor; font.bold: true; font.pixelSize: 14 }
                            Label { text: t("automaticMicrophoneInfo"); color: root.mutedText; wrapMode: Text.WordWrap; width: parent.width; font.pixelSize: 12 }
                        }
                    }
                    Rectangle {
                        Layout.fillWidth: true; Layout.preferredHeight: 88; radius: 12
                        color: root.panelAltColor; border.color: root.borderColor; border.width: 1
                        Column { anchors.fill: parent; anchors.margins: 11; spacing: 5
                            Label { text: "\uD83D\uDCF1 " + t("mqttPhone"); color: root.textColor; font.bold: true; font.pixelSize: 14 }
                            Label { text: t("automaticPhoneInfo"); color: root.mutedText; wrapMode: Text.WordWrap; width: parent.width; font.pixelSize: 12 }
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    implicitHeight: automaticDetails.implicitHeight + 22
                    radius: 12
                    color: root.panelAltColor
                    border.color: root.borderColor
                    border.width: 1
                    Column {
                        id: automaticDetails
                        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 11
                        spacing: 5
                        Label { text: t("connectionGuidance"); color: root.textColor; font.bold: true; font.pixelSize: 14 }
                        Label { text: t("connectionGuidanceInfo"); color: root.mutedText; wrapMode: Text.WordWrap; width: parent.width; font.pixelSize: 12 }
                    }
                }

                Label { text: t("manualConnections"); color: root.textColor; font.pixelSize: 16; font.bold: true; topPadding: 4 }

                Rectangle {
                    width: parent.width
                    implicitHeight: mqttSettingsColumn.implicitHeight + 22
                    radius: 12
                    color: root.panelAltColor
                    opacity: communicationsSettingsPanel.mqttEditable ? 1 : 0.56
                    border.color: communicationsSettingsPanel.mqttEditable ? root.warningColor : root.borderColor
                    border.width: 1
                    Column {
                        id: mqttSettingsColumn
                        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 11
                        spacing: 8
                        RowLayout { width: parent.width
                            Label { text: "\uD83D\uDCE1 " + t("mqttBrokerSettings"); color: root.textColor; font.bold: true; font.pixelSize: 14; Layout.fillWidth: true }
                            MenuActionButton { text: communicationsSettingsPanel.mqttEditable ? "\u2713" : "\u270E"; iconOnly: true; textPixelSize: 13; Layout.preferredWidth: 28; Layout.preferredHeight: 26; accentColor: communicationsSettingsPanel.mqttEditable ? root.successColor : "#f8c25d"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor; toolTip: t("unlockCommunicationSetting"); onClicked: communicationsSettingsPanel.mqttEditable = !communicationsSettingsPanel.mqttEditable }
                        }
                        Label { text: t("mqttBrokerHelp"); color: root.mutedText; width: parent.width; wrapMode: Text.WordWrap; font.pixelSize: 12 }
                        RowLayout { width: parent.width; spacing: 8
                            TextField { id: mqttHostField; Layout.fillWidth: true; enabled: communicationsSettingsPanel.mqttEditable; placeholderText: t("mqttHost"); color: root.textColor; placeholderTextColor: root.mutedText; background: Rectangle { radius: 7; color: mqttHostField.enabled ? root.panelColor : root.panelAltColor; border.color: mqttHostField.enabled ? root.warningColor : root.borderColor; border.width: 1 } }
                            TextField { id: mqttPortField; Layout.preferredWidth: 96; enabled: communicationsSettingsPanel.mqttEditable; inputMethodHints: Qt.ImhDigitsOnly; placeholderText: t("mqttPort"); color: root.textColor; placeholderTextColor: root.mutedText; background: Rectangle { radius: 7; color: mqttPortField.enabled ? root.panelColor : root.panelAltColor; border.color: mqttPortField.enabled ? root.warningColor : root.borderColor; border.width: 1 } }
                            TextField { id: mqttPrefixField; Layout.preferredWidth: 130; enabled: communicationsSettingsPanel.mqttEditable; placeholderText: t("mqttPrefix"); color: root.textColor; placeholderTextColor: root.mutedText; background: Rectangle { radius: 7; color: mqttPrefixField.enabled ? root.panelColor : root.panelAltColor; border.color: mqttPrefixField.enabled ? root.warningColor : root.borderColor; border.width: 1 } }
                        }
                    }
                }

                Rectangle {
                    width: parent.width
                    implicitHeight: opcuaSettingsColumn.implicitHeight + 22
                    radius: 12
                    color: root.panelAltColor
                    opacity: communicationsSettingsPanel.opcuaEditable ? 1 : 0.56
                    border.color: communicationsSettingsPanel.opcuaEditable ? root.warningColor : root.borderColor
                    border.width: 1
                    Column {
                        id: opcuaSettingsColumn
                        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 11
                        spacing: 8
                        RowLayout { width: parent.width
                            Label { text: "\uD83D\uDD17 " + t("opcuaSettings"); color: root.textColor; font.bold: true; font.pixelSize: 14; Layout.fillWidth: true }
                            MenuActionButton { text: communicationsSettingsPanel.opcuaEditable ? "\u2713" : "\u270E"; iconOnly: true; textPixelSize: 13; Layout.preferredWidth: 28; Layout.preferredHeight: 26; accentColor: communicationsSettingsPanel.opcuaEditable ? root.successColor : "#f8c25d"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor; toolTip: t("unlockCommunicationSetting"); onClicked: communicationsSettingsPanel.opcuaEditable = !communicationsSettingsPanel.opcuaEditable }
                        }
                        Label { text: t("opcuaHelp"); color: root.mutedText; width: parent.width; wrapMode: Text.WordWrap; font.pixelSize: 12 }
                        TextField { id: opcuaUrlField; width: parent.width; enabled: communicationsSettingsPanel.opcuaEditable; placeholderText: t("opcuaEndpoint"); color: root.textColor; placeholderTextColor: root.mutedText; background: Rectangle { radius: 7; color: opcuaUrlField.enabled ? root.panelColor : root.panelAltColor; border.color: opcuaUrlField.enabled ? root.warningColor : root.borderColor; border.width: 1 } }
                    }
                }

                Rectangle {
                    width: parent.width
                    implicitHeight: openAiSettingsColumn.implicitHeight + 22
                    radius: 12
                    color: root.panelAltColor
                    opacity: communicationsSettingsPanel.aiEditable ? 1 : 0.56
                    border.color: communicationsSettingsPanel.aiEditable ? root.warningColor : root.borderColor
                    border.width: 1
                    Column {
                        id: openAiSettingsColumn
                        anchors.left: parent.left; anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 11
                        spacing: 8
                        RowLayout { width: parent.width
                            Label { text: "\u2728 " + t("openAiSettings"); color: root.textColor; font.bold: true; font.pixelSize: 14; Layout.fillWidth: true }
                            Label { text: blanky.openAiKeyConfigured ? t("apiKeyConfigured") : t("apiKeyMissing"); color: blanky.openAiKeyConfigured ? root.successColor : root.warningColor; font.bold: true; font.pixelSize: 12 }
                            MenuActionButton { text: communicationsSettingsPanel.aiEditable ? "\u2713" : "\u270E"; iconOnly: true; textPixelSize: 13; Layout.preferredWidth: 28; Layout.preferredHeight: 26; accentColor: communicationsSettingsPanel.aiEditable ? root.successColor : "#f8c25d"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor; toolTip: t("unlockCommunicationSetting"); onClicked: communicationsSettingsPanel.aiEditable = !communicationsSettingsPanel.aiEditable }
                        }
                        Label { text: t("openAiKeyHelp"); color: root.mutedText; width: parent.width; wrapMode: Text.WordWrap; font.pixelSize: 12 }
                        RowLayout { width: parent.width; spacing: 8
                            TextField { id: openAiKeyField; Layout.fillWidth: true; enabled: communicationsSettingsPanel.aiEditable; echoMode: TextInput.Password; placeholderText: t("openAiKeyPlaceholder"); color: root.textColor; placeholderTextColor: root.mutedText; background: Rectangle { radius: 7; color: openAiKeyField.enabled ? root.panelColor : root.panelAltColor; border.color: openAiKeyField.enabled ? root.warningColor : root.borderColor; border.width: 1 } }
                            MenuActionButton { text: t("applyApiKey"); Layout.preferredWidth: 110; Layout.preferredHeight: 34; enabled: communicationsSettingsPanel.aiEditable && openAiKeyField.text.length > 0; accentColor: root.successColor; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor; onClicked: { blanky.setOpenAiApiKey(openAiKeyField.text); openAiKeyField.text = ""; communicationsSettingsPanel.aiEditable = false } }
                        }
                    }
                }

                RowLayout {
                    width: parent.width
                    spacing: 10
                    MenuActionButton { text: "\u21BA " + t("restoreCommunicationDefaults"); Layout.preferredWidth: 215; Layout.preferredHeight: 36; accentColor: root.warningColor; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor; onClicked: { blanky.resetCommunicationSettings(); mqttHostField.text = blanky.mqttBrokerHost; mqttPortField.text = String(blanky.mqttBrokerPort); mqttPrefixField.text = blanky.mqttTopicPrefix; opcuaUrlField.text = blanky.opcuaUrl } }
                    Item { Layout.fillWidth: true }
                    MenuActionButton { text: "\u2713 " + t("applyCommunicationSettings"); Layout.preferredWidth: 170; Layout.preferredHeight: 36; accentColor: root.successColor; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor; onClicked: { blanky.saveCommunicationSettings(mqttHostField.text, Number(mqttPortField.text), mqttPrefixField.text, opcuaUrlField.text); communicationsSettingsPanel.mqttEditable = false; communicationsSettingsPanel.opcuaEditable = false } }
                }
            }
        }
    }

    FileDialog {
        id: exportFileDialog
        property string exportKind: "events"
        property string exportFormat: "csv"
        title: t("saveExportFile")
        fileMode: FileDialog.SaveFile
        currentFolder: blanky.defaultExportFolder
        nameFilters: exportFormat === "pdf" ? ["PDF (*.pdf)"] : ["CSV (*.csv)"]
        onAccepted: {
            var file = selectedFile.toString()
            if (exportKind === "audio")
                blanky.exportAudioDiagnosticsTo(exportFormat, file)
            else
                blanky.exportEventsTo(exportFormat, file)
        }
    }

    FloatingPanel {
        id: audioLogsPanel
        width: 760
        height: 520
        panelTitle: t("audioLogs")
        panelColor: root.panelColor
        borderColor: root.borderColor
        titleColor: root.textColor
        onOpening: { root.popupBackdropVisible = true; modalBackdrop.scheduleSnapshot() }
        onOpenedForBackdrop: modalBackdrop.scheduleSnapshot()
        onClosedForBackdrop: root.popupBackdropVisible = audioSettingsPanel.visible

        ColumnLayout {
            anchors.fill: parent
            spacing: 8

            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 38
                clip: true

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: blanky.audioDiagnosticHeaderText + "\n" + blanky.audioDiagnosticDividerText
                    color: root.mutedText
                    font.family: "Noto Sans Mono"
                    font.pixelSize: 11
                    font.bold: true
                    textFormat: Text.PlainText
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                ScrollView {
                    id: audioLogsScroll
                    anchors.fill: parent
                    clip: true
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    ScrollBar.vertical.policy: ScrollBar.AlwaysOn

                    TextEdit {
                        width: audioLogsScroll.availableWidth
                        height: Math.max(audioLogsScroll.availableHeight, contentHeight + 6)
                        text: blanky.audioDiagnosticRichText
                        readOnly: true
                        selectByMouse: true
                        wrapMode: TextEdit.NoWrap
                        color: root.textColor
                        font.family: "Noto Sans Mono"
                        font.pixelSize: 11
                        textFormat: TextEdit.RichText
                    }
                    background: Rectangle { color: root.panelAltColor; radius: 10; border.color: root.borderColor; border.width: 1 }
                }

                Label {
                    anchors.centerIn: parent
                    visible: blanky.audioDiagnosticLogText.length === 0
                    text: blanky.language === "pt" ? "Ainda n\u00e3o existem registos de voz." : t("noAudioLogs")
                    color: root.textColor
                    font.pixelSize: 14
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    z: 1
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Item { Layout.fillWidth: true }
                MenuActionButton {
                    text: t("exportAudioData")
                    toolTip: t("tooltipExportAudioData")
                    Layout.preferredWidth: 145
                    Layout.preferredHeight: 36
                    accentColor: root.successColor
                    textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor
                    onClicked: root.chooseExportDestination("audio", "csv")
                }
                MenuActionButton {
                    text: t("exportAudioReport")
                    toolTip: t("tooltipExportAudioReport")
                    Layout.preferredWidth: 160
                    Layout.preferredHeight: 36
                    accentColor: root.accentColor
                    textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor
                    onClicked: root.chooseExportDestination("audio", "pdf")
                }
            }
        }
    }

    Rectangle {
        id: accentGlow
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 3
        gradient: Gradient {
            GradientStop { position: 0.0; color: root.accentColor }
            GradientStop { position: 1.0; color: "transparent" }
        }
        opacity: 0.7
    }

    Behavior on color {
        ColorAnimation { duration: 180 }
    }
}
