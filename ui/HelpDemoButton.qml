import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: demo

    property string icon: ""
    property string iconKind: ""
    property string label: ""
    property string statusText: ""
    property bool active: false
    property bool informational: false
    property color accentColor: "#63cbff"
    property color surfaceColor: "#07111a"
    property color textColor: "#def2ff"
    property color mutedText: "#9dd9ff"
    property real textScale: 1.0

    implicitWidth: Math.round(170 * textScale)
    implicitHeight: Math.round(46 * textScale)
    radius: Math.round((informational ? 5 : 9) * textScale)
    color: informational ? Qt.lighter(surfaceColor, 1.10) : surfaceColor
    border.color: accentColor
    border.width: informational ? 0 : (active ? 2 : 1)

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Math.round(10 * demo.textScale)
        anchors.rightMargin: Math.round(10 * demo.textScale)
        spacing: Math.round(6 * demo.textScale)

        Label {
            visible: demo.icon.length > 0 && demo.iconKind.length === 0
            text: demo.icon
            color: demo.accentColor
            font.bold: true
            font.pixelSize: Math.round(14 * demo.textScale)
            Layout.preferredWidth: Math.round(18 * demo.textScale)
            horizontalAlignment: Text.AlignHCenter
        }
        SymbolIcon {
            visible: demo.iconKind.length > 0
            kind: demo.iconKind
            iconColor: demo.accentColor
            Layout.preferredWidth: Math.round(18 * demo.textScale)
            Layout.preferredHeight: Math.round(18 * demo.textScale)
        }
        Label {
            text: demo.label
            color: demo.informational ? demo.mutedText : demo.textColor
            font.bold: !demo.informational
            font.pixelSize: Math.round(12 * demo.textScale)
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
        }
        Rectangle {
            visible: demo.statusText.length > 0 && !demo.informational
            Layout.preferredWidth: Math.min(Math.round(128 * demo.textScale), statusLabel.implicitWidth + Math.round(16 * demo.textScale))
            Layout.preferredHeight: Math.round(22 * demo.textScale)
            radius: height / 2
            color: Qt.rgba(demo.accentColor.r, demo.accentColor.g, demo.accentColor.b, 0.10)
            border.color: demo.accentColor
            border.width: 1

            Label {
                id: statusLabel
                anchors.centerIn: parent
                width: parent.width - Math.round(8 * demo.textScale)
                text: demo.statusText
                color: demo.active ? demo.accentColor : demo.mutedText
                font.bold: true
                font.pixelSize: Math.round(10 * demo.textScale)
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
            }
        }
        Label {
            visible: demo.statusText.length > 0 && demo.informational
            text: demo.statusText
            color: demo.accentColor
            font.bold: true
            font.pixelSize: Math.round(11 * demo.textScale)
            Layout.maximumWidth: Math.round(165 * demo.textScale)
            horizontalAlignment: Text.AlignRight
            wrapMode: Text.WordWrap
            maximumLineCount: 2
            elide: Text.ElideRight
        }
    }
}
