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

    function stateGlyph(state) {
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
                color: panel.dark ? "#82d6ff" : "#0d5d8b"
                font.pixelSize: 14
                font.bold: true
            }
            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: panel.borderColor }
        }

        GridLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: 2
            columnSpacing: panel.contentSpacing
            rowSpacing: panel.contentSpacing

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
                    Layout.minimumHeight: panel.compact ? 62 : 72
                    radius: 9
                    color: panel.dark ? "#06121d" : "#e4edf2"
                    border.color: panel.stateColor(communicationStatus)
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: panel.compact ? 9 : 12
                        anchors.rightMargin: panel.compact ? 9 : 12
                        spacing: panel.compact ? 7 : 10

                        Label {
                            text: modelData.label.toUpperCase()
                            color: panel.mutedText
                            font.pixelSize: panel.compact ? 9 : 10
                            font.bold: true
                            elide: Text.ElideRight
                            Layout.preferredWidth: panel.compact ? 86 : 108
                            Layout.maximumWidth: panel.compact ? 98 : 124
                            verticalAlignment: Text.AlignVCenter
                        }

                        Label {
                            text: panel.detailFor(modelData.key)
                            color: panel.mutedText
                            font.pixelSize: panel.compact ? 10 : 11
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                            Layout.minimumWidth: 0
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }

                        Label {
                            text: panel.stateGlyph(communicationStatus)
                            color: panel.stateColor(communicationStatus)
                            font.pixelSize: panel.compact ? 15 : 17
                            font.bold: true
                            Layout.preferredWidth: panel.compact ? 13 : 16
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }

                        Label {
                            text: panel.stateText(communicationStatus)
                            color: panel.stateColor(communicationStatus)
                            font.pixelSize: panel.compact ? 10 : 11
                            font.bold: true
                            elide: Text.ElideRight
                            Layout.preferredWidth: panel.compact ? 78 : 92
                            Layout.maximumWidth: panel.compact ? 84 : 100
                            horizontalAlignment: Text.AlignRight
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }

        }
    }
}
