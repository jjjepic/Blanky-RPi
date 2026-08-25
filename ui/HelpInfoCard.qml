import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: infoCard

    property string kind: "info"
    property string title: ""
    property string message: ""
    property color accentColor: "#63cbff"
    property color successColor: "#48d66b"
    property color warningColor: "#f8c25d"
    property color errorColor: "#ff6b6b"
    property color surfaceColor: "#07111a"
    property color textColor: "#def2ff"
    property color mutedText: "#9dd9ff"
    property real textScale: 1.0

    readonly property color semanticColor: kind === "tip" || kind === "expected" ? successColor
        : kind === "attention" ? warningColor
        : kind === "error" ? errorColor : accentColor
    readonly property string symbol: kind === "tip" ? "*"
        : kind === "expected" ? "✓"
        : kind === "attention" ? "!"
        : kind === "error" ? "✕" : "i"

    Layout.fillWidth: true
    implicitHeight: body.implicitHeight + Math.round(22 * textScale)
    radius: Math.round(9 * textScale)
    color: surfaceColor
    border.color: semanticColor
    border.width: 1

    RowLayout {
        id: body
        anchors.fill: parent
        anchors.margins: Math.round(11 * infoCard.textScale)
        spacing: Math.round(9 * infoCard.textScale)

        Label {
            text: infoCard.symbol
            color: infoCard.semanticColor
            font.bold: true
            font.pixelSize: Math.round(18 * infoCard.textScale)
            Layout.alignment: Qt.AlignTop
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Label {
                visible: infoCard.title.length > 0
                text: infoCard.title
                color: infoCard.semanticColor
                font.bold: true
                font.pixelSize: Math.round(12 * infoCard.textScale)
                Layout.fillWidth: true
            }
            Label {
                text: infoCard.message
                color: infoCard.textColor
                font.pixelSize: Math.round(12 * infoCard.textScale)
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }
        }
    }
}
