import QtQuick
import QtQuick.Controls

ToolTip {
    id: tooltip

    property bool lightSurface: false

    delay: 500
    timeout: 6000

    background: Rectangle {
        color: tooltip.lightSurface ? "#e6eef2" : "#061521"
        border.color: tooltip.lightSurface ? "#277cab" : "#3ba8e5"
        border.width: 1
        radius: 7
    }

    contentItem: Label {
        text: tooltip.text
        color: tooltip.lightSurface ? "#123d58" : "#dff5ff"
        font.pixelSize: 12
        font.bold: true
        leftPadding: 10
        rightPadding: 10
        topPadding: 6
        bottomPadding: 6
        wrapMode: Text.WordWrap
    }
}
