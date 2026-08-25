import QtQuick
import QtQuick.Controls

ToolTip {
    id: tooltip

    property bool lightSurface: false
    property color surfaceColor: lightSurface ? "#e6eef2" : "#061521"
    property color outlineColor: lightSurface ? "#277cab" : "#3ba8e5"
    property color foregroundColor: lightSurface ? "#123d58" : "#dff5ff"

    delay: 500
    timeout: 6000

    background: Rectangle {
        color: tooltip.surfaceColor
        border.color: tooltip.outlineColor
        border.width: 1
        radius: 7
    }

    contentItem: Label {
        text: tooltip.text
        color: tooltip.foregroundColor
        font.pixelSize: 12
        font.bold: true
        leftPadding: 10
        rightPadding: 10
        topPadding: 6
        bottomPadding: 6
        wrapMode: Text.WordWrap
    }
}
