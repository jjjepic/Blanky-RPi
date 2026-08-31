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
    readonly property real readabilityScale: typeof blanky !== "undefined" ? blanky.appearanceTextScale : 1.0
    readonly property bool hovered: commandMouse.containsMouse
    readonly property color hoverColor: active ? iconColor : borderColor
    readonly property real hoverLuminance: 0.2126 * hoverColor.r + 0.7152 * hoverColor.g + 0.0722 * hoverColor.b
    readonly property color hoverTextColor: hoverLuminance > 0.62 ? "#07111a" : "#f7fbff"

    signal triggered(string command)

    radius: 8
    height: parent && parent.controlButtonHeight !== undefined ? parent.controlButtonHeight : 42
    color: hovered && commandEnabled ? hoverColor : (active ? Qt.lighter(panelColor, 1.45) : panelColor)
    opacity: commandEnabled || active ? 1.0 : 0.62
    border.color: hovered && commandEnabled ? Qt.lighter(hoverColor, 1.12) : (active ? iconColor : borderColor)
    border.width: active || (hovered && commandEnabled) ? 2 : 1
    scale: hovered && commandEnabled ? 1.012 : 1.0
    z: hovered ? 1 : 0

    Behavior on color { ColorAnimation { duration: 140 } }
    Behavior on scale { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }

    Text {
        anchors.centerIn: parent
        width: Math.max(0, parent.width - 16)
        height: Math.min(implicitHeight, parent.height - 8)
        text: control.iconText.length > 0
            ? "<span style='color:" + (control.hovered && control.commandEnabled ? control.hoverTextColor : control.iconColor) + ";'>" + control.iconText + "</span> " + control.label
            : control.label
        textFormat: Text.RichText
        color: control.hovered && control.commandEnabled ? control.hoverTextColor : control.textColor
        font.pixelSize: Math.round((control.singleLineTitle ? 11 : 12) * control.readabilityScale)
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
        text: (control.active ? "✓ " : "○ ") + control.stateText
        color: control.hovered && control.commandEnabled ? control.hoverTextColor : (control.active ? control.iconColor : control.mutedText)
        font.pixelSize: Math.round(10 * control.readabilityScale)
        font.bold: true
    }

    MouseArea {
        id: commandMouse
        anchors.fill: parent
        enabled: control.commandEnabled
        hoverEnabled: true
        cursorShape: control.commandEnabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: control.triggered(control.command)
    }
}
