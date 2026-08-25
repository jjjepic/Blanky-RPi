import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Translations.js" as I18n

Rectangle {
    id: panel

    property var controller
    property string language: "pt"
    property bool dark: true
    property color panelColor: "#091722"
    property color panelAltColor: "#07111a"
    property color borderColor: "#1f6fa8"
    property color textColor: "#def2ff"
    property color mutedText: "#9dd9ff"
    property color accentColor: "#63cbff"
    property color successColor: "#48d66b"
    property color warningColor: "#f8c25d"
    property color errorColor: "#ff6b6b"
    property color inactiveColor: "#8fa8b8"
    property bool colorIndependent: false
    property color successSurface: "#0c3423"
    property color infoSurface: "#0b3040"
    property color warningSurface: "#382c0d"
    property color errorSurface: "#38161d"
    property var stateMap: ({})
    property var detailsMap: ({})
    readonly property bool compact: panel.height < 300
    readonly property int cardHeight: compact ? 47 : 58
    readonly property int contentSpacing: compact ? 5 : 8

    function t(key) {
        return I18n.text(panel.language, key)
    }

    function parseStates(raw) {
        var out = {}
        var parts = String(raw || "").split("|")
        for (var i = 0; i < parts.length; i++) {
            var pair = parts[i].split("=")
            if (pair.length === 2)
                out[pair[0]] = pair[1]
        }
        return out
    }

    function stateFor(key) {
        return String(panel.stateMap[key] || "checking").trim()
    }

    function detailFor(key) {
        return String(panel.detailsMap[key] || "").trim()
    }

    function stateText(state) {
        if (state === "connected")
            return t("connected")
        if (state === "communicating")
            return t("communicating")
        if (state === "standby")
            return t("standby")
        if (state === "silent")
            return t("noCommunication")
        if (state === "error")
            return t("error")
        if (state === "checking")
            return t("checking")
        return t("offline")
    }

    function stateColor(state) {
        if (state === "connected")
            return panel.successColor
        if (state === "communicating")
            return panel.accentColor
        if (state === "standby")
            return panel.inactiveColor
        if (state === "silent")
            return panel.warningColor
        if (state === "checking")
            return panel.inactiveColor
        return panel.errorColor
    }

    function stateSurfaceColor(state) {
        if (panel.colorIndependent)
            return panel.panelAltColor
        if (state === "connected")
            return panel.successSurface
        if (state === "communicating")
            return panel.infoSurface
        if (state === "standby" || state === "checking")
            return panel.panelColor
        if (state === "silent")
            return panel.warningSurface
        return panel.errorSurface
    }

    function stateGlyph(state) {
        if (state === "connected")
            return "✓"
        if (state === "communicating")
            return "⇄"
        if (state === "standby")
            return "◷"
        if (state === "silent")
            return "!"
        if (state === "error")
            return "✕"
        if (state === "offline")
            return "✕"
        return "○"
    }

    Connections {
        target: panel.controller
        function onCommStatusCompactChanged() {
            panel.stateMap = panel.parseStates(panel.controller.commStatusCompact)
        }
        function onCommDetailsCompactChanged() {
            panel.detailsMap = panel.parseStates(panel.controller.commDetailsCompact)
        }
    }

    Component.onCompleted: {
        if (panel.controller)
            panel.stateMap = panel.parseStates(panel.controller.commStatusCompact)
        if (panel.controller)
            panel.detailsMap = panel.parseStates(panel.controller.commDetailsCompact)
    }

    color: panel.panelColor
    border.color: panel.borderColor
    border.width: 1
    radius: 10

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: panel.compact ? 7 : 10
        spacing: panel.contentSpacing

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: panel.borderColor }
            Label {
                text: panel.t("communications").toUpperCase()
                color: panel.accentColor
                font.pixelSize: 14
                font.bold: true
            }
            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: panel.borderColor }
        }

        GridLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: 2
            columnSpacing: panel.compact ? 14 : 18
            rowSpacing: panel.compact ? 12 : 16

            Repeater {
                model: [
                    { key: "microphone", icon: "🎙", label: panel.t("microphone") },
                    { key: "mqtt_base", icon: "📡", label: panel.t("mqttBase") },
                    { key: "mqtt_phone", icon: "📱", label: panel.t("mqttPhone") },
                    { key: "opcua", icon: "🔗", label: panel.t("opcua") }
                ]

                Rectangle {
                    readonly property string communicationStatus: panel.stateFor(modelData.key)
                    Layout.column: (modelData.key === "mqtt_base" || modelData.key === "mqtt_phone") ? 1 : 0
                    Layout.row: (modelData.key === "mqtt_phone" || modelData.key === "opcua") ? 1 : 0
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredHeight: panel.compact ? 62 : 70
                    Layout.minimumHeight: panel.compact ? 58 : 66
                    radius: 9
                    color: panel.panelAltColor
                    border.color: panel.stateColor(communicationStatus)
                    border.width: 1

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.leftMargin: panel.compact ? 9 : 12
                        anchors.rightMargin: panel.compact ? 9 : 12
                        anchors.topMargin: panel.compact ? 6 : 8
                        anchors.bottomMargin: panel.compact ? 6 : 8
                        spacing: panel.compact ? 3 : 5

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: panel.compact ? 4 : 6

                            Rectangle {
                                Layout.preferredWidth: panel.compact ? 28 : 34
                                Layout.preferredHeight: width
                                radius: width / 2
                                color: panel.stateSurfaceColor(communicationStatus)
                                border.color: panel.stateColor(communicationStatus)
                                border.width: 1

                                Label {
                                    anchors.centerIn: parent
                                    text: modelData.icon
                                    color: panel.stateColor(communicationStatus)
                                    font.pixelSize: panel.compact ? 15 : 18
                                }
                            }

                            Label {
                                text: modelData.label.toUpperCase()
                                color: panel.textColor
                                font.pixelSize: panel.compact ? 11 : 13
                                font.bold: true
                                elide: Text.ElideRight
                                Layout.fillWidth: true
                                Layout.minimumWidth: 0
                                verticalAlignment: Text.AlignVCenter
                            }

                            Rectangle {
                                Layout.preferredHeight: panel.compact ? 24 : 28
                                Layout.preferredWidth: Math.min(panel.compact ? 96 : 112, stateLabel.implicitWidth + (panel.compact ? 18 : 22))
                                radius: 7
                                color: panel.stateSurfaceColor(communicationStatus)
                                border.color: panel.stateColor(communicationStatus)
                                border.width: 1

                                Label {
                                    id: stateLabel
                                    anchors.centerIn: parent
                                    text: panel.stateGlyph(communicationStatus) + " " + panel.stateText(communicationStatus).toUpperCase()
                                    color: panel.stateColor(communicationStatus)
                                    font.pixelSize: panel.compact ? 9 : 10
                                    font.bold: true
                                    elide: Text.ElideRight
                                    width: parent.width - 10
                                    horizontalAlignment: Text.AlignHCenter
                                }
                            }
                        }

                        Item {
                            Layout.fillWidth: true
                            Layout.preferredHeight: panel.compact ? 4 : 6
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 1
                            color: panel.stateColor(communicationStatus)
                            opacity: panel.dark ? 0.72 : 0.58
                        }

                        Label {
                            text: panel.detailFor(modelData.key)
                            color: panel.mutedText
                            font.pixelSize: panel.compact ? 11 : 12
                            font.bold: true
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            Layout.minimumWidth: 0
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }

        }
    }
}
