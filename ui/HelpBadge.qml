import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: badge

    property string symbol: "i"
    property string label: ""
    property color accentColor: "#63cbff"
    property color surfaceColor: "#07111a"
    property color textColor: "#def2ff"
    property real textScale: 1.0

    implicitWidth: content.implicitWidth + Math.round(18 * textScale)
    implicitHeight: Math.round(28 * textScale)
    radius: Math.round(8 * textScale)
    color: surfaceColor
    border.color: accentColor
    border.width: 1

    RowLayout {
        id: content
        anchors.centerIn: parent
        spacing: Math.round(5 * badge.textScale)

        Label {
            text: badge.symbol
            color: badge.accentColor
            font.bold: true
            font.pixelSize: Math.round(13 * badge.textScale)
        }
        Label {
            text: badge.label
            color: badge.textColor
            font.bold: true
            font.pixelSize: Math.round(11 * badge.textScale)
        }
    }
}
