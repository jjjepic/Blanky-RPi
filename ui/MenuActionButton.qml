import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: control

    property string text: ""
    property string subText: ""
    property string iconText: ""
    property string labelText: ""
    property color accentColor: "#63cbff"
    property color textColor: "#def2ff"
    property color mutedText: "#9dd9ff"
    property color borderColor: "#1f6fa8"
    property color panelColor: "#07111a"
    property bool prominent: false
    property string toolTip: ""
    property int textPixelSize: prominent ? 13 : 12
    property real textHorizontalOffset: 0
    property real textVerticalOffset: 0
    property bool iconOnly: false
    readonly property real readabilityScale: typeof blanky !== "undefined" ? blanky.appearanceTextScale : 1.0
    readonly property bool hasStructuredContent: iconText.length > 0 || labelText.length > 0
    readonly property bool glyphButton: iconOnly || (hasStructuredContent && labelText.length === 0)
    readonly property string displayText: hasStructuredContent
        ? iconText + (labelText.length > 0 ? " " + labelText : "")
        : text
    readonly property bool lightSurface: (panelColor.r + panelColor.g + panelColor.b) > 1.8
    readonly property bool hovered: mouseArea.containsMouse

    signal clicked()

    width: 150
    height: Math.round((prominent ? 44 : 40) * (readabilityScale > 1 ? 1.10 : 1.0))
    radius: 11
    opacity: enabled ? 1.0 : 0.55
    color: mouseArea.containsMouse ? Qt.lighter(panelColor, 1.28) : panelColor
    border.color: accentColor
    border.width: prominent ? 2 : 1

    Item {
        anchors.fill: parent
        anchors.leftMargin: 10
        anchors.rightMargin: 10

        Text {
            visible: !control.glyphButton && !control.subText && !control.hasStructuredContent
            anchors.centerIn: parent
            width: Math.min(implicitWidth, parent.width)
            height: Math.min(implicitHeight, parent.height)
            text: control.displayText
            textFormat: Text.RichText
            color: control.textColor
            font.pixelSize: Math.round(control.textPixelSize * control.readabilityScale)
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            wrapMode: Text.NoWrap
            transform: Translate { x: control.textHorizontalOffset; y: control.textVerticalOffset }
        }

        Row {
            visible: !control.glyphButton && !control.subText && control.hasStructuredContent
            anchors.centerIn: parent
            height: parent.height
            spacing: control.labelText.length > 0 ? 4 : 0

            Text {
                visible: control.iconText.length > 0
                height: parent.height
                text: control.iconText
                color: control.textColor
                font.pixelSize: Math.round(control.textPixelSize * control.readabilityScale)
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                transform: Translate { x: control.textHorizontalOffset; y: control.textVerticalOffset }
            }

            Text {
                visible: control.labelText.length > 0
                height: parent.height
                text: control.labelText
                textFormat: Text.RichText
                color: control.textColor
                font.pixelSize: Math.round(control.textPixelSize * control.readabilityScale)
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
                wrapMode: Text.NoWrap
                transform: Translate { x: control.textHorizontalOffset; y: control.textVerticalOffset }
            }
        }

        Column {
            visible: !control.iconOnly && control.subText.length > 0
            anchors.centerIn: parent
            width: parent.width
            spacing: 1

            Text {
                width: parent.width
                text: control.text
                textFormat: Text.RichText
                color: control.textColor
                font.pixelSize: Math.round(control.textPixelSize * control.readabilityScale)
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
                wrapMode: Text.NoWrap
                transform: Translate { x: control.textHorizontalOffset; y: control.textVerticalOffset }
            }

            Text {
                width: parent.width
                text: control.subText
                color: control.mutedText
                font.pixelSize: Math.round(10 * control.readabilityScale)
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
                wrapMode: Text.NoWrap
            }
        }
    }

    Text {
        visible: control.glyphButton
        anchors.fill: parent
        text: control.iconText.length > 0 ? control.iconText : control.text
        color: control.textColor
        font.pixelSize: Math.round(control.textPixelSize * control.readabilityScale)
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        transform: Translate { x: control.textHorizontalOffset; y: control.textVerticalOffset }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: control.enabled
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: control.clicked()
    }

    BlankyToolTip {
        parent: control
        visible: mouseArea.containsMouse && control.toolTip.length > 0
        text: control.toolTip
        lightSurface: control.lightSurface
        surfaceColor: control.panelColor
        outlineColor: control.accentColor
        foregroundColor: control.textColor
    }
}
