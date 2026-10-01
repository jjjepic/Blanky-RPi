import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: monitor

    property bool running: false
    property real textScale: 1.0
    property string title: ""
    property string subtitle: ""
    property string modeLabel: ""
    property string systemLabel: ""
    property string processLabel: ""
    property string modeText: ""
    property string systemText: ""
    property string processText: ""
    property color modeTone: textColor
    property color systemTone: textColor
    property color processTone: textColor
    property color panelColor: "#091722"
    property color accentColor: "#63cbff"
    property color successColor: "#48d66b"
    property color inactiveColor: "#8fa8b8"
    property color textColor: "#def2ff"
    property color mutedText: "#9dd9ff"

    implicitHeight: Math.round(136 * textScale)
    radius: 8
    clip: true
    color: panelColor
    border.color: accentColor
    border.width: 1

    Repeater {
        model: 6
        Rectangle {
            x: (index + 1) * monitor.width / 7
            y: 1
            width: 1
            height: monitor.height - 2
            color: monitor.accentColor
            opacity: 0.055
        }
    }

    Repeater {
        model: 4
        Rectangle {
            x: 1
            y: (index + 1) * monitor.height / 5
            width: monitor.width - 2
            height: 1
            color: monitor.accentColor
            opacity: 0.055
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Math.round(6 * monitor.textScale)
        spacing: Math.round(2 * monitor.textScale)

        RowLayout {
            Layout.fillWidth: true
            spacing: Math.round(6 * monitor.textScale)

            Rectangle {
                Layout.preferredWidth: Math.round(7 * monitor.textScale)
                Layout.preferredHeight: width
                radius: width / 2
                color: monitor.running ? monitor.successColor : monitor.inactiveColor
            }
            Label {
                text: monitor.title
                color: monitor.textColor
                font.bold: true
                font.pixelSize: Math.round(12 * monitor.textScale)
                Layout.fillWidth: true
                elide: Text.ElideRight
            }
            Label {
                text: monitor.subtitle.toUpperCase()
                color: monitor.mutedText
                font.pixelSize: Math.round(8 * monitor.textScale)
                font.letterSpacing: 1
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: monitor.accentColor
            opacity: 0.55
        }

        Repeater {
            model: [
                { symbol: "◇", label: monitor.modeLabel, value: monitor.modeText, tone: monitor.modeTone },
                { symbol: "▣", label: monitor.systemLabel, value: monitor.systemText, tone: monitor.systemTone },
                { symbol: "≋", label: monitor.processLabel, value: monitor.processText, tone: monitor.processTone }
            ]

            Item {
                required property var modelData
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: Math.round(23 * monitor.textScale)

                RowLayout {
                    anchors.fill: parent
                    spacing: Math.round(5 * monitor.textScale)

                    Label {
                        text: modelData.symbol
                        color: monitor.accentColor
                        font.pixelSize: Math.round(12 * monitor.textScale)
                        Layout.preferredWidth: Math.round(15 * monitor.textScale)
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Label {
                        text: modelData.label
                        color: monitor.mutedText
                        font.pixelSize: Math.round(10 * monitor.textScale)
                        Layout.preferredWidth: Math.round(73 * monitor.textScale)
                        elide: Text.ElideRight
                    }
                    Label {
                        text: modelData.value
                        color: modelData.tone
                        font.bold: true
                        font.pixelSize: Math.round(10 * monitor.textScale)
                        Layout.fillWidth: true
                        Layout.minimumWidth: 0
                        horizontalAlignment: Text.AlignRight
                        verticalAlignment: Text.AlignVCenter
                        wrapMode: Text.WordWrap
                        maximumLineCount: 2
                        elide: Text.ElideRight
                    }
                }
            }
        }
    }
}
