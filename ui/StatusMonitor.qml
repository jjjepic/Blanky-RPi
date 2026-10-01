import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: monitor

    property bool running: false
    property real textScale: 1.0
    property string title: ""
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

    implicitHeight: Math.round(140 * textScale)
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
            opacity: 0.025
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
            opacity: 0.025
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Math.round(6 * monitor.textScale)
        spacing: Math.round(4 * monitor.textScale)

        Label {
            Layout.fillWidth: true
            text: monitor.title
            color: monitor.accentColor
            font.bold: true
            font.pixelSize: Math.round(14 * monitor.textScale)
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 6
            color: Qt.rgba(monitor.accentColor.r, monitor.accentColor.g, monitor.accentColor.b, 0.025)
            border.color: Qt.rgba(monitor.accentColor.r, monitor.accentColor.g, monitor.accentColor.b, 0.55)
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: Math.round(5 * monitor.textScale)
                spacing: 0

                Repeater {
                    model: [
                        { symbol: "", label: monitor.modeLabel, value: monitor.modeText, tone: monitor.modeTone },
                        { symbol: "\u2699\uFE0E", label: monitor.systemLabel, value: monitor.systemText, tone: monitor.systemTone },
                        { symbol: "▤", label: monitor.processLabel, value: monitor.processText, tone: monitor.processTone }
                    ]

                    Item {
                        id: statusRow
                        required property var modelData
                        required property int index
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumHeight: Math.max(Math.round(35 * monitor.textScale),
                            categoryLabel.implicitHeight + categoryValue.implicitHeight + Math.round(10 * monitor.textScale))

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: Math.round(3 * monitor.textScale)
                            spacing: Math.round(7 * monitor.textScale)

                            Item {
                                Layout.preferredWidth: Math.round(27 * monitor.textScale)
                                Layout.fillHeight: true
                                Rectangle {
                                    visible: statusRow.index === 0
                                    anchors.centerIn: parent
                                    width: Math.round(12 * monitor.textScale)
                                    height: width
                                    radius: width / 2
                                    color: monitor.running ? monitor.successColor : monitor.inactiveColor
                                }
                                Label {
                                    visible: statusRow.index !== 0
                                    anchors.centerIn: parent
                                    text: statusRow.modelData.symbol
                                    color: monitor.accentColor
                                    font.pixelSize: Math.round(20 * monitor.textScale)
                                }
                            }

                            Rectangle {
                                Layout.preferredWidth: 1
                                Layout.fillHeight: true
                                color: monitor.accentColor
                                opacity: 0.20
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 0
                                Label {
                                    id: categoryLabel
                                    text: statusRow.modelData.label + ":"
                                    color: monitor.mutedText
                                    font.pixelSize: Math.round(10 * monitor.textScale)
                                }
                                Label {
                                    id: categoryValue
                                    text: statusRow.modelData.value
                                    color: statusRow.modelData.tone
                                    font.bold: true
                                    font.pixelSize: Math.round(13 * monitor.textScale)
                                    Layout.fillWidth: true
                                    Layout.minimumWidth: 0
                                    wrapMode: Text.WordWrap
                                    maximumLineCount: 2
                                    elide: Text.ElideRight
                                }
                            }
                        }

                        Rectangle {
                            visible: statusRow.index < 2
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            height: 1
                            color: monitor.accentColor
                            opacity: 0.35
                        }
                    }
                }
            }
        }
    }
}
