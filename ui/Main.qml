import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import "Translations.js" as I18n

ApplicationWindow {
    id: root
    visible: true
    width: 1540
    height: 860
    minimumWidth: 1540
    minimumHeight: 850
    title: "Blanky"

    readonly property bool dark: blanky.darkMode
    readonly property color bgColor: dark ? "#02060d" : "#d7e3ea"
    readonly property color panelColor: dark ? "#091722" : "#c5d8e4"
    readonly property color panelAltColor: dark ? "#07111a" : "#e3edf2"
    readonly property color borderColor: dark ? "#1f6fa8" : "#5f98b8"
    readonly property color textColor: dark ? "#def2ff" : "#16384c"
    readonly property color mutedText: dark ? "#9dd9ff" : "#386b85"
    property var ttsVoiceModel: blanky.ttsVoiceOptions ? blanky.ttsVoiceOptions.split("|") : []
    property var stateMap: ({})
    property var commStateMap: ({})
    property bool popupBackdropVisible: false
    property string textBotMode: "offline"
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
            return "ID    | Time     | Source     | Command            | State  | Description"
        return "ID    | Hora     | Origem     | Comando            | Estado | Descri\u00e7\u00e3o"
    }

    function eventsHeaderDivider() {
        return "----- | -------- | ---------- | ------------------ | ------ | --------------------------------------------------------"
    }

    function t(key, values) {
        return I18n.text(blanky.language, key, values)
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

    function voiceLabel() {
        var voice = blanky.ttsVoice || ""
        if (!voice)
            return ""
        return voice.charAt(0).toUpperCase() + voice.slice(1).toLowerCase()
    }

    function commandHelpGroups() {
        var pt = blanky.language === "pt"
        return [
            { title: pt ? "Sistema" : "System", commands: [
                { icon: "\u25B6", color: "#48d66b", title: pt ? "Iniciar sistema" : "Start system", code: "START", description: pt ? "Inicia o funcionamento do sistema." : "Starts system operation.", examples: pt ? "iniciar · arrancar · come\u00e7ar" : "start · begin · launch" },
                { icon: "\u23F9", color: "#ff6b6b", title: pt ? "Parar sistema" : "Stop system", code: "STOP", description: pt ? "Para o sistema e rep\u00f5e os componentes." : "Stops the system and resets components.", examples: pt ? "parar · pausar · terminar" : "stop · halt · pause" }
            ]},
            { title: pt ? "Modos" : "Modes", commands: [
                { icon: "\u26A1", color: "#f8c25d", title: pt ? "Modo r\u00e1pido" : "Fast mode", code: "MODE_FAST", description: pt ? "Seleciona a opera\u00e7\u00e3o r\u00e1pida." : "Selects fast operation.", examples: pt ? "modo r\u00e1pido · alta velocidade · acelerado" : "fast mode · quick mode · high speed" },
                { icon: "\uD83C\uDFAF", color: "#63cbff", title: pt ? "Modo ideal" : "Ideal mode", code: "MODE_IDEAL", description: pt ? "Seleciona a opera\u00e7\u00e3o ideal." : "Selects ideal operation.", examples: pt ? "modo ideal · modo auto · modo normal" : "ideal mode · auto mode · normal mode" },
                { icon: "\uD83D\uDD79", color: "#b7f7d4", title: pt ? "Modo manual" : "Manual mode", code: "MODE_MANUAL", description: pt ? "Ativa os controlos manuais." : "Enables manual controls.", examples: pt ? "modo manual · opera\u00e7\u00e3o manual · manual" : "manual mode · operator mode · manual" },
                { icon: "\u21C4", color: "#9dd9ff", title: pt ? "Trocar modo" : "Change mode", code: "MODE_UNSPEC", description: pt ? "Permite escolher outro modo." : "Allows selecting another mode.", examples: pt ? "trocar modo · mudar modo · alterar modo" : "change mode · switch mode · set mode" }
            ]},
            { title: pt ? "Motores" : "Motors", commands: [
                { icon: "\u2699", color: "#63cbff", title: pt ? "Controlar motores" : "Control motors", code: "MOTOR_n_ON / MOTOR_n_OFF", description: pt ? "Liga ou desliga o motor indicado." : "Turns the selected motor on or off.", examples: pt ? "ligar motor 1 · desligar motor 2 · ativar motor 3" : "turn on motor 1 · disable motor 2 · start motor 3" }
            ]},
            { title: pt ? "Cilindros" : "Cylinders", commands: [
                { icon: "\u25B0", color: "#63cbff", title: pt ? "Controlar cilindros" : "Control cylinders", code: "CYL_X_EXTEND / CYL_X_RETRACT", description: pt ? "Avan\u00e7a ou recolhe o cilindro indicado." : "Extends or retracts the selected cylinder.", examples: pt ? "avan\u00e7ar cilindro A · recolher cilindro B · cilindro C recuar" : "extend cylinder A · retract cylinder B · cylinder C back" }
            ]},
            { title: pt ? "Luzes" : "Lights", commands: [
                { icon: "\u25CF", color: "#48d66b", title: pt ? "Luz verde" : "Green light", code: "GREEN_ON / GREEN_OFF", description: pt ? "Liga ou desliga a luz verde." : "Turns the green light on or off.", examples: pt ? "ligar luz verde · apagar verde · ativar verde" : "turn on green light · switch green off · enable green" },
                { icon: "\u25CF", color: "#ff6b6b", title: pt ? "Luz vermelha" : "Red light", code: "RED_ON / RED_OFF", description: pt ? "Liga ou desliga a luz vermelha." : "Turns the red light on or off.", examples: pt ? "ligar luz vermelha · apagar vermelha · desativar vermelho" : "turn on red light · switch red off · disable red" }
            ]},
            { title: pt ? "Rob\u00f4" : "Robot", commands: [
                { icon: "\uD83E\uDD16", color: "#b7f7d4", title: pt ? "Enviar rob\u00f4" : "Move robot", code: "ROBOT_TO_METAL / ROBOT_TO_NONMETAL", description: pt ? "Envia o rob\u00f4 para metal ou n\u00e3o metal." : "Sends the robot to metal or non-metal.", examples: pt ? "rob\u00f4 para metal · mandar rob\u00f4 para n\u00e3o metal · rob\u00f4 vai para metal" : "robot to metal · send robot to non-metal · move robot to metal" }
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

    function chooseExportDestination(kind, format) {
        exportFolderDialog.exportKind = kind
        exportFolderDialog.exportFormat = format
        exportFolderDialog.open()
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
            return "#48d66b"
        if (state === "communicating")
            return "#47c8ff"
        if (state === "standby")
            return "#aab7c2"
        if (state === "silent")
            return "#f8c25d"
        if (state === "checking")
            return "#8fa8b8"
        return "#ff6b6b"
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
    }

    Timer {
        id: eventsAutoscrollTimer
        interval: 1
        repeat: false
        onTriggered: root.scrollEventsToBottom()
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
            GradientStop { position: 0.0; color: dark ? "#03101b" : "#e3edf2" }
            GradientStop { position: 1.0; color: root.bgColor }
        }
    }

    ColumnLayout {
        id: mainColumn
        anchors.fill: parent
        anchors.margins: 18
        spacing: 12

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 50

            Row {
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                spacing: 7

                MenuActionButton {
                    text: dark ? "\u263D" : "\u2600"
                    width: 50
                    height: 44
                    textPixelSize: 22
                    accentColor: dark ? "#63cbff" : "#f8c25d"
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: dark ? t("tooltipThemeLight") : t("tooltipThemeDark")
                    onClicked: blanky.toggleTheme()
                }

                MenuActionButton {
                    text: "\uD83C\uDDF5\uD83C\uDDF9"
                    width: 54
                    height: 44
                    textPixelSize: 20
                    accentColor: blanky.language === "pt" ? "#48d66b" : "#6f91a8"
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: "Portugu\u00eas"
                    onClicked: blanky.setLanguage("pt")
                }

                MenuActionButton {
                    text: "\uD83C\uDDEC\uD83C\uDDE7"
                    width: 54
                    height: 44
                    textPixelSize: 20
                    accentColor: blanky.language === "en" ? "#48d66b" : "#6f91a8"
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: "English"
                    onClicked: blanky.setLanguage("en")
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
                    accentColor: blanky.soundEnabled ? "#63cbff" : "#ff6b6b"
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
                    accentColor: "#b7f7d4"
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: t("tooltipAudioSettings")
                    onClicked: audioSettingsPanel.open()
                }

                MenuActionButton {
                    iconText: "\u21BB"
                    width: 50
                    height: 44
                    textPixelSize: 22
                    accentColor: "#f8c25d"
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: t("tooltipReset")
                    onClicked: blanky.resetSystem()
                }

                MenuActionButton {
                    iconText: "\u23FB"
                    width: 50
                    height: 44
                    textPixelSize: 21
                    accentColor: "#ff6b6b"
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: t("tooltipShutdown")
                    onClicked: blanky.shutdownApplication()
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 14

            Item { Layout.fillWidth: true }

            Image {
                source: dark ? "../assets/blanky_logo_dark.png" : "../assets/blanky_logo_light.png"
                Layout.preferredWidth: 58
                Layout.preferredHeight: 58
                fillMode: Image.PreserveAspectFit
                smooth: true
            }

            Label {
                text: "Blanky"
                color: dark ? "#63cbff" : "#0a5e8f"
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
                                            font.pixelSize: 12
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
            color: dark ? "#050d17" : "#e3edf2"
            border.color: root.borderColor
            border.width: 2
            radius: 16

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 10

                Label {
                    text: blanky.statusText
                    color: dark ? "#9fe1ff" : "#0f5882"
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
                    color: dark ? "#081a2b" : "#d7e6ed"
                    border.color: dark ? "#2b83bf" : "#76b2d8"
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
                    Layout.preferredHeight: 44
                    prominent: true
                    accentColor: "#20d6a4"
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
                    Layout.preferredHeight: 44
                    prominent: true
                    accentColor: "#f8c25d"
                    textColor: root.textColor
                    mutedText: root.mutedText
                    borderColor: root.borderColor
                    panelColor: root.panelAltColor
                    toolTip: t("tooltipVoice")
                    onClicked: voicePanel.open()
                }

                MenuActionButton {
                    id: voiceSpeedButton
                    iconText: "\uD83D\uDC22"
                    labelText: t("voiceSpeed") + ": <b>" + root.ttsSpeedLabel() + "</b>"
                    Layout.fillWidth: true
                    Layout.preferredWidth: 205
                    Layout.minimumWidth: 175
                    Layout.preferredHeight: 44
                    prominent: true
                    accentColor: "#63cbff"
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
                    Layout.preferredHeight: 44
                    prominent: true
                    accentColor: "#b7f7d4"
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
                    Layout.preferredHeight: 44
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
                                        accentColor: root.textBotMode === "offline" ? "#48d66b" : root.borderColor
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
                                        accentColor: root.textBotMode === "online" ? "#63cbff" : root.borderColor
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
                                        accentColor: "#63cbff"
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
                                        accentColor: "#48d66b"
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
                                        accentColor: root.textBotMode === "offline" ? "#48d66b" : root.borderColor
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
                                        accentColor: root.textBotMode === "online" ? "#63cbff" : root.borderColor
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
                                        accentColor: "#63cbff"
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
                                        accentColor: "#48d66b"
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
                                    color: root.dark ? "#82d6ff" : "#0d5d8b"
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
                                    Layout.preferredHeight: 38
                                    clip: true

                                    Text {
                                        anchors.verticalCenter: parent.verticalCenter
                                        text: root.eventsHeaderText() + "\n" + root.eventsHeaderDivider()
                                        color: root.mutedText
                                        font.family: "Consolas"
                                        font.pixelSize: 12
                                        font.bold: true
                                        textFormat: Text.PlainText
                                    }
                                }

                                MenuActionButton {
                                    text: t("exportData")
                                    toolTip: t("tooltipExportData")
                                    Layout.preferredWidth: 130
                                    Layout.preferredHeight: 38
                                    accentColor: "#48d66b"
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
                                    Layout.preferredHeight: 38
                                    accentColor: "#63cbff"
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
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                            ScrollBar.vertical.policy: ScrollBar.AlwaysOn

                            TextEdit {
                                id: eventsContent
                                width: eventsScroll.availableWidth
                                height: Math.max(eventsScroll.availableHeight, contentHeight + 6)
                                text: blanky.monitorEventsText
                                readOnly: true
                                selectByMouse: true
                                wrapMode: TextEdit.Wrap
                                color: root.textColor
                                font.family: "Consolas"
                                font.pixelSize: 12
                                textFormat: TextEdit.PlainText
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
                                    spacing: 8

                                    Rectangle { Layout.preferredWidth: 18; Layout.preferredHeight: 1; color: root.borderColor }
                                    Label {
                                        text: t("textBot").toUpperCase()
                                        color: root.dark ? "#82d6ff" : "#0d5d8b"
                                        font.bold: true
                                        font.pixelSize: 14
                                    }
                                    Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: root.borderColor }
                                    MenuActionButton {
                                        text: t("textBotOffline")
                                        Layout.preferredWidth: 82; Layout.preferredHeight: 28
                                        accentColor: root.textBotMode === "offline" ? "#48d66b" : root.borderColor
                                        textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor
                                        onClicked: root.textBotMode = "offline"
                                    }
                                    MenuActionButton {
                                        text: t("textBotOnline")
                                        Layout.preferredWidth: 82; Layout.preferredHeight: 28
                                        accentColor: root.textBotMode === "online" ? "#63cbff" : root.borderColor
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
                                            color: root.textColor
                                            background: Rectangle {
                                                color: root.dark ? "#081a2b" : "#d7e6ed"
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
                                        accentColor: "#63cbff"; textColor: root.textColor; mutedText: root.mutedText
                                        borderColor: root.borderColor; panelColor: root.panelColor
                                        toolTip: t("tooltipTextBotInfo")
                                        onClicked: commandsPanel.open()
                                    }
                                    MenuActionButton {
                                        text: "\u27A4 " + t("send")
                                        Layout.preferredWidth: 92; Layout.fillHeight: true
                                        accentColor: "#48d66b"; textColor: root.textColor; mutedText: root.mutedText
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
        stateMap: root.commStateMap
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
        x: Math.max(12, Math.min(root.width - width - 12,
            primaryControlsPanel.x + actionControls.x + voiceSpeedButton.x + (voiceSpeedButton.width - width) / 2))
        y: primaryControlsPanel.y + actionControls.y + voiceSpeedButton.y + voiceSpeedButton.height + 8
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
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ScrollBar.vertical.policy: ScrollBar.AlwaysOn

                Column {
                    width: Math.max(commandHelpScroll.availableWidth - 8, 720)
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
                                    }
                                }
                            }
                        }
                    }
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
                                    text: modelData
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
                                accentColor: "#63cbff"
                                textColor: root.textColor
                                mutedText: root.mutedText
                                borderColor: root.borderColor
                                panelColor: root.panelColor
                                toolTip: t("previewVoice")
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
        onClosedForBackdrop: root.popupBackdropVisible = false

        ScrollView {
            id: redesignedAudioScroll
            anchors.fill: parent
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical.policy: ScrollBar.AlwaysOn

            Column {
                width: Math.max(redesignedAudioScroll.availableWidth - 10, 760)
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
                            BlankyToolTip { visible: sensitivityHintHover.hovered && !sensitivityUnlock.hovered; text: t("sensitivityHelp"); lightSurface: !root.dark }
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
                            BlankyToolTip { visible: waitHintHover.hovered && !waitUnlock.hovered; text: t("maxWaitHelp"); lightSurface: !root.dark }
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
                            BlankyToolTip { visible: minimumHintHover.hovered && !minimumUnlock.hovered; text: t("minimumCommandHelp"); lightSurface: !root.dark }
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
                            BlankyToolTip { visible: silenceHintHover.hovered && !silenceUnlock.hovered; text: t("silenceHelp"); lightSurface: !root.dark }
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
                            BlankyToolTip { visible: gainHintHover.hovered && !gainUnlock.hovered; text: t("gainHelp"); lightSurface: !root.dark }
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
                            BlankyToolTip { visible: highPassHintHover.hovered && !highPassUnlock.hovered; text: t("highPassHelp"); lightSurface: !root.dark }
                            Switch { checked: blanky.micHighpassEnabled; enabled: root.audioSettingIsEditable("highpass"); onClicked: blanky.setMicHighpassEnabled(checked) }
                            Label { text: t("highPass"); color: root.textColor; Layout.fillWidth: true }
                            MenuActionButton { id: highPassUnlock; visible: !root.audioSettingIsEditable("highpass"); text: "\u270E"; iconOnly: true; textPixelSize: 13; Layout.preferredWidth: 25; Layout.preferredHeight: 24; accentColor: "#f8c25d"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor; toolTip: t("unlockAudioSetting"); onClicked: root.unlockAudioSetting("highpass") }
                        }
                        RowLayout {
                            width: parent.width
                            opacity: root.audioSettingIsEditable("gate") ? 1 : 0.56
                            HoverHandler { id: noiseGateHintHover; enabled: !noiseGateUnlock.hovered }
                            BlankyToolTip { visible: noiseGateHintHover.hovered && !noiseGateUnlock.hovered; text: t("noiseGateHelp"); lightSurface: !root.dark }
                            Switch { checked: blanky.micNoiseGateEnabled; enabled: root.audioSettingIsEditable("gate"); onClicked: blanky.setMicNoiseGateEnabled(checked) }
                            Label { text: t("noiseGate"); color: root.textColor; Layout.fillWidth: true }
                            MenuActionButton { id: noiseGateUnlock; visible: !root.audioSettingIsEditable("gate"); text: "\u270E"; iconOnly: true; textPixelSize: 13; Layout.preferredWidth: 25; Layout.preferredHeight: 24; accentColor: "#f8c25d"; textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelColor; toolTip: t("unlockAudioSetting"); onClicked: root.unlockAudioSetting("gate") }
                        }
                        RowLayout {
                            width: parent.width
                            opacity: root.audioSettingIsEditable("reduction") ? 1 : 0.56
                            HoverHandler { id: noiseReductionHintHover; enabled: !noiseReductionUnlock.hovered }
                            BlankyToolTip { visible: noiseReductionHintHover.hovered && !noiseReductionUnlock.hovered; text: t("noiseReductionHelp"); lightSurface: !root.dark }
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
                        accentColor: "#48d66b"
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

    FolderDialog {
        id: exportFolderDialog
        property string exportKind: "events"
        property string exportFormat: "csv"
        title: t("chooseExportFolder")
        currentFolder: blanky.defaultExportFolder
        onAccepted: {
            var folder = selectedFolder.toString()
            if (exportKind === "audio")
                blanky.exportAudioDiagnosticsTo(exportFormat, folder)
            else
                blanky.exportEventsTo(exportFormat, folder)
        }
    }

    FloatingPanel {
        id: audioLogsPanel
        width: 880
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

            ScrollView {
                id: audioLogsScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                ScrollBar.vertical.policy: ScrollBar.AlwaysOn

                TextEdit {
                    width: audioLogsScroll.availableWidth
                    height: Math.max(audioLogsScroll.availableHeight, contentHeight + 6)
                    text: blanky.audioDiagnosticLogText || t("noAudioLogs")
                    readOnly: true
                    selectByMouse: true
                    wrapMode: TextEdit.NoWrap
                    color: root.textColor
                    font.family: "Noto Sans Mono"
                    font.pixelSize: 11
                    textFormat: TextEdit.PlainText
                }
                background: Rectangle { color: root.panelAltColor; radius: 10; border.color: root.borderColor; border.width: 1 }
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
                    accentColor: "#48d66b"
                    textColor: root.textColor; mutedText: root.mutedText; borderColor: root.borderColor; panelColor: root.panelAltColor
                    onClicked: root.chooseExportDestination("audio", "csv")
                }
                MenuActionButton {
                    text: t("exportAudioReport")
                    toolTip: t("tooltipExportAudioReport")
                    Layout.preferredWidth: 160
                    Layout.preferredHeight: 36
                    accentColor: "#63cbff"
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
            GradientStop { position: 0.0; color: dark ? "#1d8fd0" : "#6cb7df" }
            GradientStop { position: 1.0; color: "transparent" }
        }
        opacity: 0.7
    }

    Behavior on color {
        ColorAnimation { duration: 180 }
    }
}
