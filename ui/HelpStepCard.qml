import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: stepCard

    property string number: "1"
    property string title: ""
    property string description: ""
    property color accentColor: "#63cbff"
    property color surfaceColor: "#07111a"
    property color textColor: "#def2ff"
    property color mutedText: "#9dd9ff"
    property real textScale: 1.0
    default property alias demoContent: demoHost.data

    Layout.fillWidth: true
    implicitHeight: content.implicitHeight + Math.round(28 * textScale)
    radius: Math.round(12 * textScale)
    color: surfaceColor
    border.color: accentColor
    border.width: 1

    ColumnLayout {
        id: content
        anchors.fill: parent
        anchors.margins: Math.round(14 * stepCard.textScale)
        spacing: Math.round(10 * stepCard.textScale)

        RowLayout {
            Layout.fillWidth: true
            spacing: Math.round(10 * stepCard.textScale)

            Rectangle {
                Layout.preferredWidth: Math.round(30 * stepCard.textScale)
                Layout.preferredHeight: Math.round(30 * stepCard.textScale)
                radius: width / 2
                color: stepCard.accentColor
                Label {
                    anchors.centerIn: parent
                    text: stepCard.number
                    color: stepCard.surfaceColor
                    font.bold: true
                    font.pixelSize: Math.round(14 * stepCard.textScale)
                }
            }
            Label {
                text: stepCard.title
                color: stepCard.textColor
                font.bold: true
                font.pixelSize: Math.round(16 * stepCard.textScale)
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
            }
        }

        Label {
            text: stepCard.description
            color: stepCard.mutedText
            font.pixelSize: Math.round(12 * stepCard.textScale)
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Item {
            id: demoHost
            Layout.fillWidth: true
            implicitHeight: childrenRect.height
            Layout.preferredHeight: implicitHeight
        }
    }
}
