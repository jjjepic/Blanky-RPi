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
    readonly property bool hasStructuredContent: iconText.length > 0 || labelText.length > 0
    readonly property string displayText: hasStructuredContent
        ? iconText + (labelText.length > 0 ? " " + labelText : "")
        : text
    readonly property bool lightSurface: (panelColor.r + panelColor.g + panelColor.b) > 1.8

    signal clicked()

    width: 150
    height: prominent ? 44 : 40
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
            visible: !control.iconOnly && !control.subText
            anchors.centerIn: parent
            width: Math.min(implicitWidth, parent.width)
            height: Math.min(implicitHeight, parent.height)
            text: control.displayText
            textFormat: Text.RichText
            color: control.textColor
            font.pixelSize: control.textPixelSize
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            wrapMode: Text.NoWrap
            transform: Translate { x: control.textHorizontalOffset; y: control.textVerticalOffset }
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
                font.pixelSize: control.textPixelSize
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
                font.pixelSize: 10
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
                wrapMode: Text.NoWrap
            }
        }
    }

    Text {
        visible: control.iconOnly
        anchors.centerIn: parent
        anchors.horizontalCenterOffset: control.textHorizontalOffset
        anchors.verticalCenterOffset: control.textVerticalOffset
        text: control.text
        color: control.textColor
        font.pixelSize: control.textPixelSize
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: control.enabled
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: control.clicked()
    }

    ToolTip {
        parent: control
        visible: mouseArea.containsMouse && control.toolTip.length > 0
        delay: 450
        timeout: 5000
        text: control.toolTip
        background: Rectangle {
            color: control.lightSurface ? "#e6eef2" : "#061521"
            border.color: control.lightSurface ? "#277cab" : "#3ba8e5"
            border.width: 1
            radius: 7
        }
        contentItem: Label {
            text: control.toolTip
            color: control.lightSurface ? "#123d58" : "#dff5ff"
            font.pixelSize: 12
            font.bold: true
            leftPadding: 10
            rightPadding: 10
            topPadding: 6
            bottomPadding: 6
        }
    }
}
