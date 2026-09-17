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
    readonly property int titlePixelSize: Math.round((singleLineTitle ? 11 : 12) * readabilityScale)
    readonly property int statePixelSize: Math.round(10 * readabilityScale)
    readonly property string titleText: iconText.length > 0 ? iconText + " " + label : label
    readonly property string formattedStateText: (active ? "✓ " : "○ ") + stateText
    readonly property bool hasState: stateText.length > 0
    readonly property real requiredHorizontalWidth: titleMetrics.advanceWidth + stateMetrics.advanceWidth
        + Math.round(34 * readabilityScale)
    readonly property bool stackedContent: hasState && (
        width < requiredHorizontalWidth || width < Math.round(180 * readabilityScale)
    )
    readonly property bool hovered: commandMouse.containsMouse
    readonly property bool hoverAnimationsEnabled: typeof blanky === "undefined" || blanky.hoverAnimationsEnabled
    readonly property bool strongHover: hovered && commandEnabled && hoverAnimationsEnabled
    readonly property color hoverColor: active ? iconColor : borderColor
    readonly property real hoverLuminance: 0.2126 * hoverColor.r + 0.7152 * hoverColor.g + 0.0722 * hoverColor.b
    readonly property color hoverTextColor: hoverLuminance > 0.62 ? "#07111a" : "#f7fbff"

    signal triggered(string command)

    radius: 8
    height: parent && parent.controlButtonHeight !== undefined ? parent.controlButtonHeight : 42
    color: strongHover ? hoverColor : (hovered && commandEnabled ? Qt.lighter(panelColor, 1.16) : (active ? Qt.lighter(panelColor, 1.45) : panelColor))
    opacity: commandEnabled || active ? 1.0 : 0.62
    border.color: strongHover ? Qt.lighter(hoverColor, 1.12) : (active ? iconColor : borderColor)
    border.width: active || strongHover ? 2 : 1
    scale: strongHover ? 1.012 : 1.0
    z: hovered ? 1 : 0

    Behavior on color { ColorAnimation { duration: 140 } }
    Behavior on scale { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }

    TextMetrics {
        id: titleMetrics
        text: control.titleText
        font.pixelSize: control.titlePixelSize
        font.bold: control.active
    }

    TextMetrics {
        id: stateMetrics
        text: control.formattedStateText
        font.pixelSize: control.statePixelSize
        font.bold: true
    }

    Loader {
        anchors.fill: parent
        anchors.leftMargin: Math.round(6 * control.readabilityScale)
        anchors.rightMargin: Math.round(6 * control.readabilityScale)
        anchors.topMargin: Math.round(2 * control.readabilityScale)
        anchors.bottomMargin: Math.round(2 * control.readabilityScale)
        sourceComponent: control.stackedContent ? stackedButtonContent : horizontalButtonContent
    }

    Component {
        id: horizontalButtonContent

        RowLayout {
            spacing: Math.round(7 * control.readabilityScale)

            Text {
                Layout.fillWidth: true
                Layout.minimumWidth: 0
                text: control.iconText.length > 0
                    ? "<span style='color:" + (control.strongHover ? control.hoverTextColor : control.iconColor) + ";'>" + control.iconText + "</span> " + control.label
                    : control.label
                textFormat: Text.RichText
                color: control.strongHover ? control.hoverTextColor : control.textColor
                font.pixelSize: control.titlePixelSize
                font.bold: control.active
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.NoWrap
                elide: Text.ElideRight
            }

            Rectangle {
                visible: control.hasState
                Layout.preferredWidth: Math.ceil(stateMetrics.advanceWidth + 12 * control.readabilityScale)
                Layout.preferredHeight: Math.ceil(stateMetrics.boundingRect.height + 5 * control.readabilityScale)
                radius: height / 2
                color: control.strongHover ? "transparent" : Qt.rgba(control.iconColor.r, control.iconColor.g, control.iconColor.b, control.active ? 0.16 : 0.07)
                border.color: control.strongHover ? control.hoverTextColor : (control.active ? control.iconColor : control.borderColor)
                border.width: 1

                Label {
                    anchors.centerIn: parent
                    text: control.formattedStateText
                    color: control.strongHover ? control.hoverTextColor : (control.active ? control.iconColor : control.mutedText)
                    font.pixelSize: control.statePixelSize
                    font.bold: true
                }
            }
        }
    }

    Component {
        id: stackedButtonContent

        ColumnLayout {
            spacing: 0

            Text {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.minimumHeight: 0
                text: control.iconText.length > 0
                    ? "<span style='color:" + (control.strongHover ? control.hoverTextColor : control.iconColor) + ";'>" + control.iconText + "</span> " + control.label
                    : control.label
                textFormat: Text.RichText
                color: control.strongHover ? control.hoverTextColor : control.textColor
                font.pixelSize: control.titlePixelSize
                font.bold: control.active
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.NoWrap
                elide: Text.ElideRight
            }

            Rectangle {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: Math.min(parent.width, Math.ceil(stateMetrics.advanceWidth + 12 * control.readabilityScale))
                Layout.preferredHeight: Math.ceil(stateMetrics.boundingRect.height + 3 * control.readabilityScale)
                radius: height / 2
                color: control.strongHover ? "transparent" : Qt.rgba(control.iconColor.r, control.iconColor.g, control.iconColor.b, control.active ? 0.16 : 0.07)
                border.color: control.strongHover ? control.hoverTextColor : (control.active ? control.iconColor : control.borderColor)
                border.width: 1

                Label {
                    anchors.centerIn: parent
                    width: parent.width - 6
                    text: control.formattedStateText
                    color: control.strongHover ? control.hoverTextColor : (control.active ? control.iconColor : control.mutedText)
                    font.pixelSize: control.statePixelSize
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                }
            }
        }
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
