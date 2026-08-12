import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: control

    property string label: ""
    property string iconText: ""
    property string command: ""
    property string stateText: ""
    property color iconColor: "#63cbff"
    property color textColor: "#def2ff"
    property color mutedText: "#9dd9ff"
    property color borderColor: "#1f6fa8"
    property color panelColor: "#091722"
    property bool active: false
    property bool commandEnabled: true
    property bool singleLineTitle: false

    signal triggered(string command)

    radius: 8
    height: parent && parent.controlButtonHeight !== undefined ? parent.controlButtonHeight : 42
    color: active ? Qt.lighter(panelColor, 1.45) : panelColor
    opacity: commandEnabled ? 1.0 : 0.42
    border.color: active ? iconColor : borderColor
    border.width: active ? 2 : 1

    Text {
        anchors.centerIn: parent
        width: Math.max(0, parent.width - 16)
        height: Math.min(implicitHeight, parent.height - 8)
        text: control.iconText.length > 0
            ? "<span style='color:" + control.iconColor + ";'>" + control.iconText + "</span> " + control.label
            : control.label
        textFormat: Text.RichText
        color: control.textColor
        font.pixelSize: control.singleLineTitle ? 11 : 12
        font.bold: control.active
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        wrapMode: control.singleLineTitle ? Text.NoWrap : Text.WordWrap
        maximumLineCount: 2
        elide: Text.ElideRight
    }

    Label {
        visible: control.stateText.length > 0
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: 9
        anchors.bottomMargin: 6
        text: control.stateText
        color: control.active ? control.iconColor : control.mutedText
        font.pixelSize: 10
        font.bold: true
    }

    MouseArea {
        anchors.fill: parent
        enabled: control.commandEnabled
        cursorShape: control.commandEnabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: control.triggered(control.command)
    }
}
