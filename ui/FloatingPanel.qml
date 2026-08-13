import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: panel

    property string panelTitle: ""
    property color panelColor: "#091722"
    property color borderColor: "#1f6fa8"
    property color titleColor: "#def2ff"
    property color textColor: "#def2ff"
    property bool rememberPosition: true
    default property alias panelContent: bodyHost.data
    signal opening()
    signal openedForBackdrop()
    signal closedForBackdrop()

    // A modal popup gives the active task visual and input focus.
    modal: true
    dim: false
    focus: true
    padding: 0
    clip: true
    closePolicy: Popup.CloseOnEscape
    parent: Overlay.overlay

    property bool _didCenter: false
    property real _dragStartMouseX: 0
    property real _dragStartMouseY: 0
    property real _dragStartPanelX: 0
    property real _dragStartPanelY: 0

    function clampPosition() {
        if (!parent)
            return
        var maxX = Math.max(12, parent.width - width - 12)
        var maxY = Math.max(12, parent.height - height - 12)
        x = Math.max(12, Math.min(x, maxX))
        y = Math.max(12, Math.min(y, maxY))
    }

    function centerInOverlay() {
        if (!parent)
            return
        x = Math.max(12, (parent.width - width) / 2)
        y = Math.max(12, (parent.height - height) / 2)
        _didCenter = true
    }

    onAboutToShow: opening()

    onOpened: {
        if (!_didCenter || !rememberPosition) {
            centerInOverlay()
        } else {
            clampPosition()
        }
        forceActiveFocus()
        openedForBackdrop()
    }
    onClosed: closedForBackdrop()

    onWidthChanged: clampPosition()
    onHeightChanged: clampPosition()

    background: Rectangle {
        radius: 16
        color: panel.panelColor
        border.color: panel.borderColor
        border.width: 1
    }

    contentItem: ColumnLayout {
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 52
            Layout.leftMargin: 1
            Layout.rightMargin: 1
            Layout.topMargin: 1
            color: Qt.darker(panel.panelColor, 1.18)
            // Keep the outer frame visible across the title bar.
            radius: 15

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 16
                color: parent.color
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 12
                spacing: 10

                Label {
                    text: panel.panelTitle
                    color: panel.titleColor
                    font.pixelSize: 20
                    font.bold: true
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                }

                MenuActionButton {
                    text: "\u2715"
                    iconOnly: true
                    textPixelSize: 17
                    Layout.preferredWidth: 36
                    Layout.preferredHeight: 36
                    accentColor: "#ff6b6b"
                    textColor: panel.titleColor
                    mutedText: panel.textColor
                    borderColor: panel.borderColor
                    panelColor: Qt.darker(panel.panelColor, 1.18)
                    onClicked: panel.close()
                }
            }

            MouseArea {
                anchors.fill: parent
                anchors.rightMargin: 52
                acceptedButtons: Qt.LeftButton
                onPressed: function(mouse) {
                    panel._dragStartMouseX = mouse.x
                    panel._dragStartMouseY = mouse.y
                    panel._dragStartPanelX = panel.x
                    panel._dragStartPanelY = panel.y
                }
                onPositionChanged: function(mouse) {
                    if (!(mouse.buttons & Qt.LeftButton))
                        return
                    panel.x = panel._dragStartPanelX + mouse.x - panel._dragStartMouseX
                    panel.y = panel._dragStartPanelY + mouse.y - panel._dragStartMouseY
                    panel.clampPosition()
                }
            }
        }

        Item {
            id: bodyHost
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 14
        }
    }
}
