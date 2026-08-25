import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: demoButton

    property string icon: ""
    property string label: ""
    property string statusText: ""
    property bool active: false
    property color accentColor: "#63cbff"
    property color surfaceColor: "#07111a"
    property color textColor: "#def2ff"
    property color mutedText: "#9dd9ff"
    property real textScale: 1.0

    implicitWidth: Math.max(Math.round(108 * textScale), content.implicitWidth + Math.round(24 * textScale))
    implicitHeight: Math.round(42 * textScale)
    radius: Math.round(9 * textScale)
    color: surfaceColor
    border.color: accentColor
    border.width: active ? 2 : 1

    Item {
        id: content
        anchors.fill: parent
        anchors.leftMargin: Math.round(10 * demoButton.textScale)
        anchors.rightMargin: Math.round(10 * demoButton.textScale)

        Label {
            id: iconLabel
            visible: demoButton.icon.length > 0
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            text: demoButton.icon
            color: demoButton.accentColor
            font.bold: true
            font.pixelSize: Math.round(14 * demoButton.textScale)
        }
        Label {
            id: titleLabel
            anchors.centerIn: parent
            width: parent.width - Math.round(26 * demoButton.textScale)
            text: demoButton.label
            color: demoButton.textColor
            font.bold: true
            font.pixelSize: Math.round(12 * demoButton.textScale)
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }
        Label {
            visible: demoButton.statusText.length > 0
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            text: demoButton.statusText
            color: demoButton.active ? demoButton.accentColor : demoButton.mutedText
            font.bold: true
            font.pixelSize: Math.round(9 * demoButton.textScale)
            elide: Text.ElideRight
            maximumLineCount: 1
        }
    }
}
