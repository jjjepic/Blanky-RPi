import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Translations.js" as I18n

Rectangle {
    id: panel

    property var controller
    property string language: "pt"
    property bool dark: true
    property color panelColor: "#091722"
    property color panelAltColor: "#07111a"
    property color borderColor: "#1f6fa8"
    property color textColor: "#def2ff"
    property color mutedText: "#9dd9ff"
    property color accentColor: "#63cbff"
    property color successColor: "#48d66b"
    property color warningColor: "#f8c25d"
    property color errorColor: "#ff6b6b"
    property color inactiveColor: "#8fa8b8"
    property var stateMap: ({})
    readonly property bool manualAvailable: stateValue("mode_manual") === 1
    readonly property bool modeChangeActive: stateValue("mode_change") === 1
    readonly property bool modeSelected: stateValue("mode_fast") === 1
        || stateValue("mode_ideal") === 1 || manualAvailable
    readonly property bool canSelectMode: !modeSelected || modeChangeActive
    readonly property bool canRequestModeChange: modeSelected && !modeChangeActive
    readonly property color fastModeColor: warningColor
    readonly property color idealModeColor: accentColor
    readonly property color manualModeColor: successColor
    readonly property color changeModeColor: accentColor
    readonly property bool compact: panel.height < 430
    readonly property int sectionSpacing: compact ? 4 : 8
    readonly property int blockMargin: compact ? 7 : 10
    readonly property real actionButtonHeight: compact
        ? Math.max(28, Math.min(36, Math.floor((panel.height - 150) / 5)))
        : Math.max(40, Math.min(58, Math.floor((panel.height - 180) / 5)))

    function t(key, values) {
        return I18n.text(panel.language, key, values)
    }

    function stateValue(key) {
        return Number(panel.stateMap[key] || 0)
    }

    function toggleCommand(key, onCommand, offCommand) {
        return stateValue(key) === 1 ? offCommand : onCommand
    }

    function toggleStateText(key, onText, offText) {
        return stateValue(key) === 1 ? onText : offText
    }

    function activeModeText() {
        if (stateValue("mode_fast") === 1)
            return "▶ " + t("fast")
        if (stateValue("mode_ideal") === 1)
            return "▶ " + t("ideal")
        if (stateValue("mode_manual") === 1)
            return "✓ " + t("manual")
        if (stateValue("mode_change") === 1)
            return "! " + t("change")
        return "○ " + t("inactive")
    }

    function activeModeColor() {
        if (stateValue("mode_fast") === 1)
            return fastModeColor
        if (stateValue("mode_ideal") === 1)
            return idealModeColor
        if (stateValue("mode_manual") === 1)
            return manualModeColor
        if (stateValue("mode_change") === 1)
            return changeModeColor
        return panel.mutedText
    }

    function modeInfo() {
        return { text: activeModeText(), color: activeModeColor() }
    }

    function systemInfo() {
        if (stateValue("start") !== 1)
            return { text: "○ " + t("stopped"), color: panel.inactiveColor }
        if (stateValue("mode_change") === 1)
            return { text: "! " + t("waitingMode"), color: panel.warningColor }
        if (stateValue("mode_manual") === 1)
            return { text: "✓ " + t("manualActive"), color: activeModeColor() }
        if (stateValue("mode_fast") === 1)
            return { text: "▶ " + t("fastRunning"), color: activeModeColor() }
        if (stateValue("mode_ideal") === 1)
            return { text: "▶ " + t("idealRunning"), color: activeModeColor() }
        return { text: "✓ " + t("running"), color: panel.successColor }
    }

    function processInfo() {
        if (stateValue("start") !== 1)
            return { text: t("awaitingStart"), color: panel.mutedText }
        if (stateValue("mode_change") === 1)
            return { text: t("chooseMode"), color: activeModeColor() }
        if (stateValue("mode_manual") === 1)
            return { text: t("awaitingCommand"), color: activeModeColor() }
        if (stateValue("mode_fast") === 1)
            return { text: t("fastCycleActive"), color: activeModeColor() }
        if (stateValue("mode_ideal") === 1)
            return { text: t("idealCycleActive"), color: activeModeColor() }
        return { text: t("selectMode"), color: panel.warningColor }
    }

    color: panel.panelColor
    border.color: panel.borderColor
    border.width: 1
    radius: 10

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: panel.compact ? 7 : 10
        spacing: panel.sectionSpacing

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: panel.borderColor }
            Label {
                text: panel.t("operationPanel").toUpperCase()
                color: panel.accentColor
                font.pixelSize: 14
                font.bold: true
            }
            Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: panel.borderColor }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumHeight: 0
            spacing: panel.compact ? 7 : 12

            Rectangle {
                id: generalBlock
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: panel.panelAltColor
                border.color: panel.borderColor
                border.width: 1
                radius: 9

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: panel.blockMargin
                    spacing: panel.sectionSpacing

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: panel.borderColor }
                        Label {
                            text: panel.t("generalControl")
                            color: panel.accentColor
                            font.pixelSize: 14
                            font.bold: true
                        }
                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: panel.borderColor }
                    }

                    Label { text: panel.t("system"); color: panel.mutedText; font.bold: true; font.pixelSize: panel.compact ? 11 : 12; horizontalAlignment: Text.AlignHCenter; Layout.fillWidth: true }
                    ManualCommandButton {
                        Layout.fillWidth: true
                        Layout.preferredHeight: panel.actionButtonHeight
                        label: panel.stateValue("start") === 1 ? panel.t("stopAction") : panel.t("startAction")
                        singleLineTitle: true
                        iconText: panel.stateValue("start") === 1 ? "\u23F9" : "\u25B6"
                        command: panel.toggleCommand("start", "START", "STOP")
                        active: panel.stateValue("start") === 1
                        stateText: panel.toggleStateText("start", "ON", "OFF")
                        iconColor: active ? panel.successColor : panel.inactiveColor
                        textColor: panel.textColor; mutedText: panel.mutedText; borderColor: panel.borderColor; panelColor: panel.panelAltColor
                        onTriggered: function(command) { panel.controller.submitButtonCommand(command) }
                    }

                    Label { text: panel.t("modes"); color: panel.mutedText; font.bold: true; font.pixelSize: panel.compact ? 11 : 12; horizontalAlignment: Text.AlignHCenter; Layout.fillWidth: true }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: panel.compact ? 5 : 8

                        Row {
                            Layout.fillWidth: true
                            Layout.preferredHeight: panel.actionButtonHeight
                            spacing: panel.compact ? 5 : 8

                            ManualCommandButton { width: (parent.width - parent.spacing * 2) / 3; height: panel.actionButtonHeight; commandEnabled: panel.canSelectMode; label: panel.t("fast"); iconText: "\u26A1"; command: "MODE_FAST"; active: panel.stateValue("mode_fast") === 1; stateText: active ? "ON" : "OFF"; iconColor: panel.fastModeColor; textColor: panel.textColor; mutedText: panel.mutedText; borderColor: panel.borderColor; panelColor: panel.panelAltColor; onTriggered: function(command) { panel.controller.submitButtonCommand(command) } }
                            ManualCommandButton { width: (parent.width - parent.spacing * 2) / 3; height: panel.actionButtonHeight; commandEnabled: panel.canSelectMode; label: panel.t("ideal"); iconText: "\uD83C\uDFAF"; command: "MODE_IDEAL"; active: panel.stateValue("mode_ideal") === 1; stateText: active ? "ON" : "OFF"; iconColor: panel.idealModeColor; textColor: panel.textColor; mutedText: panel.mutedText; borderColor: panel.borderColor; panelColor: panel.panelAltColor; onTriggered: function(command) { panel.controller.submitButtonCommand(command) } }
                            ManualCommandButton { width: (parent.width - parent.spacing * 2) / 3; height: panel.actionButtonHeight; commandEnabled: panel.canSelectMode; label: panel.t("manual"); iconText: "\uD83D\uDD79"; command: "MODE_MANUAL"; active: panel.stateValue("mode_manual") === 1; stateText: active ? "ON" : "OFF"; iconColor: panel.manualModeColor; textColor: panel.textColor; mutedText: panel.mutedText; borderColor: panel.borderColor; panelColor: panel.panelAltColor; onTriggered: function(command) { panel.controller.submitButtonCommand(command) } }
                        }

                        ManualCommandButton { Layout.fillWidth: true; Layout.preferredHeight: panel.actionButtonHeight; commandEnabled: panel.canRequestModeChange; label: panel.t("change"); iconText: "\u21C4"; command: "MODE_UNSPEC"; active: panel.modeChangeActive; stateText: active ? "ON" : "OFF"; iconColor: panel.changeModeColor; textColor: panel.textColor; mutedText: panel.mutedText; borderColor: panel.borderColor; panelColor: panel.panelAltColor; onTriggered: function(command) { panel.controller.submitButtonCommand(command) } }
                    }

                    Label { text: panel.t("currentState"); color: panel.mutedText; font.bold: true; font.pixelSize: panel.compact ? 11 : 12; horizontalAlignment: Text.AlignHCenter; Layout.fillWidth: true }
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumHeight: panel.compact ? 80 : 112
                        color: panel.panelColor
                        border.color: panel.borderColor
                        border.width: 1
                        radius: 8

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: panel.compact ? 7 : 10
                            spacing: panel.compact ? 2 : 5

                            RowLayout {
                                Layout.fillWidth: true
                                Label { text: panel.t("activeMode"); color: panel.textColor; Layout.fillWidth: true }
                                Label { text: panel.modeInfo().text; color: panel.modeInfo().color; font.bold: true }
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Label { text: panel.t("systemState"); color: panel.textColor; Layout.fillWidth: true }
                                Label { text: panel.systemInfo().text; color: panel.systemInfo().color; font.bold: true; elide: Text.ElideRight; Layout.preferredWidth: 148; horizontalAlignment: Text.AlignRight }
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Label { text: panel.t("currentProcess"); color: panel.textColor; Layout.fillWidth: true }
                                Label { text: panel.processInfo().text; color: panel.processInfo().color; elide: Text.ElideNone; Layout.preferredWidth: 148; horizontalAlignment: Text.AlignRight }
                            }
                        }
                    }
                }
            }

            Rectangle {
                id: manualBlock
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: panel.panelAltColor
                border.color: panel.manualAvailable ? panel.successColor : panel.borderColor
                border.width: panel.manualAvailable ? 2 : 1
                radius: 9

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: panel.blockMargin
                    spacing: panel.sectionSpacing

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: panel.borderColor }
                        Label {
                            text: panel.t("manualControl")
                            color: panel.manualAvailable ? panel.successColor : panel.mutedText
                            font.pixelSize: 14
                            font.bold: true
                        }
                        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: panel.borderColor }
                    }

                    Label { text: panel.t("lights"); color: panel.mutedText; font.bold: true; font.pixelSize: panel.compact ? 11 : 12; horizontalAlignment: Text.AlignHCenter; Layout.fillWidth: true }
                    Row {
                        Layout.fillWidth: true
                        Layout.preferredHeight: panel.actionButtonHeight
                        spacing: panel.compact ? 5 : 8

                        ManualCommandButton { width: (parent.width - parent.spacing) / 2; height: panel.actionButtonHeight; commandEnabled: panel.manualAvailable; label: panel.t("greenLight"); iconText: "\u25CF"; command: panel.toggleCommand("light_green", "GREEN_ON", "GREEN_OFF"); active: panel.stateValue("light_green") === 1; stateText: panel.toggleStateText("light_green", "ON", "OFF"); iconColor: active ? panel.successColor : panel.inactiveColor; textColor: panel.textColor; mutedText: panel.mutedText; borderColor: panel.borderColor; panelColor: panel.panelAltColor; onTriggered: function(command) { panel.controller.submitButtonCommand(command) } }
                        ManualCommandButton { width: (parent.width - parent.spacing) / 2; height: panel.actionButtonHeight; commandEnabled: panel.manualAvailable; label: panel.t("redLight"); iconText: "\u25CF"; command: panel.toggleCommand("light_red", "RED_ON", "RED_OFF"); active: panel.stateValue("light_red") === 1; stateText: panel.toggleStateText("light_red", "ON", "OFF"); iconColor: active ? panel.errorColor : panel.inactiveColor; textColor: panel.textColor; mutedText: panel.mutedText; borderColor: panel.borderColor; panelColor: panel.panelAltColor; onTriggered: function(command) { panel.controller.submitButtonCommand(command) } }
                    }

                    Label { text: panel.t("cylinders"); color: panel.mutedText; font.bold: true; font.pixelSize: panel.compact ? 11 : 12; horizontalAlignment: Text.AlignHCenter; Layout.fillWidth: true }
                    Flow {
                        property real controlButtonHeight: panel.actionButtonHeight
                        Layout.fillWidth: true
                        spacing: panel.compact ? 5 : 8

                        ManualCommandButton { width: (parent.width - parent.spacing) / 2; commandEnabled: panel.manualAvailable; label: panel.t("cylinder", { letter: "A" }); iconText: "\u25B0"; command: panel.toggleCommand("cyl_a", "CYL_A_EXTEND", "CYL_A_RETRACT"); active: panel.stateValue("cyl_a") === 1; stateText: panel.toggleStateText("cyl_a", panel.t("forward"), panel.t("backward")); iconColor: panel.accentColor; textColor: panel.textColor; mutedText: panel.mutedText; borderColor: panel.borderColor; panelColor: panel.panelAltColor; onTriggered: function(command) { panel.controller.submitButtonCommand(command) } }
                        ManualCommandButton { width: (parent.width - parent.spacing) / 2; commandEnabled: panel.manualAvailable; label: panel.t("cylinder", { letter: "B" }); iconText: "\u25B0"; command: panel.toggleCommand("cyl_b", "CYL_B_EXTEND", "CYL_B_RETRACT"); active: panel.stateValue("cyl_b") === 1; stateText: panel.toggleStateText("cyl_b", panel.t("forward"), panel.t("backward")); iconColor: panel.accentColor; textColor: panel.textColor; mutedText: panel.mutedText; borderColor: panel.borderColor; panelColor: panel.panelAltColor; onTriggered: function(command) { panel.controller.submitButtonCommand(command) } }
                        ManualCommandButton { width: (parent.width - parent.spacing) / 2; commandEnabled: panel.manualAvailable; label: panel.t("cylinder", { letter: "C" }); iconText: "\u25B0"; command: panel.toggleCommand("cyl_c", "CYL_C_EXTEND", "CYL_C_RETRACT"); active: panel.stateValue("cyl_c") === 1; stateText: panel.toggleStateText("cyl_c", panel.t("forward"), panel.t("backward")); iconColor: panel.accentColor; textColor: panel.textColor; mutedText: panel.mutedText; borderColor: panel.borderColor; panelColor: panel.panelAltColor; onTriggered: function(command) { panel.controller.submitButtonCommand(command) } }
                        ManualCommandButton { width: (parent.width - parent.spacing) / 2; commandEnabled: panel.manualAvailable; label: panel.t("cylinder", { letter: "D" }); iconText: "\u25B0"; command: panel.toggleCommand("cyl_d", "CYL_D_EXTEND", "CYL_D_RETRACT"); active: panel.stateValue("cyl_d") === 1; stateText: panel.toggleStateText("cyl_d", panel.t("forward"), panel.t("backward")); iconColor: panel.accentColor; textColor: panel.textColor; mutedText: panel.mutedText; borderColor: panel.borderColor; panelColor: panel.panelAltColor; onTriggered: function(command) { panel.controller.submitButtonCommand(command) } }
                    }

                    Label { text: panel.t("motors"); color: panel.mutedText; font.bold: true; font.pixelSize: panel.compact ? 11 : 12; horizontalAlignment: Text.AlignHCenter; Layout.fillWidth: true }
                    Row {
                        Layout.fillWidth: true
                        Layout.preferredHeight: panel.actionButtonHeight
                        spacing: panel.compact ? 5 : 8

                        ManualCommandButton { width: (parent.width - parent.spacing * 2) / 3; height: panel.actionButtonHeight; commandEnabled: panel.manualAvailable; singleLineTitle: true; label: panel.t("motor", { number: 1 }); iconText: "\u2699"; command: panel.toggleCommand("motor_1", "MOTOR_1_ON", "MOTOR_1_OFF"); active: panel.stateValue("motor_1") === 1; stateText: panel.toggleStateText("motor_1", "ON", "OFF"); iconColor: active ? panel.accentColor : panel.inactiveColor; textColor: panel.textColor; mutedText: panel.mutedText; borderColor: panel.borderColor; panelColor: panel.panelAltColor; onTriggered: function(command) { panel.controller.submitButtonCommand(command) } }
                        ManualCommandButton { width: (parent.width - parent.spacing * 2) / 3; height: panel.actionButtonHeight; commandEnabled: panel.manualAvailable; singleLineTitle: true; label: panel.t("motor", { number: 2 }); iconText: "\u2699"; command: panel.toggleCommand("motor_2", "MOTOR_2_ON", "MOTOR_2_OFF"); active: panel.stateValue("motor_2") === 1; stateText: panel.toggleStateText("motor_2", "ON", "OFF"); iconColor: active ? panel.accentColor : panel.inactiveColor; textColor: panel.textColor; mutedText: panel.mutedText; borderColor: panel.borderColor; panelColor: panel.panelAltColor; onTriggered: function(command) { panel.controller.submitButtonCommand(command) } }
                        ManualCommandButton { width: (parent.width - parent.spacing * 2) / 3; height: panel.actionButtonHeight; commandEnabled: panel.manualAvailable; singleLineTitle: true; label: panel.t("motor", { number: 3 }); iconText: "\u2699"; command: panel.toggleCommand("motor_3", "MOTOR_3_ON", "MOTOR_3_OFF"); active: panel.stateValue("motor_3") === 1; stateText: panel.toggleStateText("motor_3", "ON", "OFF"); iconColor: active ? panel.accentColor : panel.inactiveColor; textColor: panel.textColor; mutedText: panel.mutedText; borderColor: panel.borderColor; panelColor: panel.panelAltColor; onTriggered: function(command) { panel.controller.submitButtonCommand(command) } }
                    }

                    Label { text: panel.t("robot"); color: panel.mutedText; font.bold: true; font.pixelSize: panel.compact ? 11 : 12; horizontalAlignment: Text.AlignHCenter; Layout.fillWidth: true }
                    Row {
                        Layout.fillWidth: true
                        Layout.preferredHeight: panel.actionButtonHeight
                        spacing: panel.compact ? 5 : 8

                        ManualCommandButton { width: (parent.width - parent.spacing) / 2; height: panel.actionButtonHeight; commandEnabled: panel.manualAvailable; label: panel.t("robotMetal"); iconText: "\uD83E\uDD16"; command: "ROBOT_TO_METAL"; active: panel.stateValue("robot_metal") === 1; stateText: active ? "ON" : "OFF"; iconColor: panel.accentColor; textColor: panel.textColor; mutedText: panel.mutedText; borderColor: panel.borderColor; panelColor: panel.panelAltColor; onTriggered: function(command) { panel.controller.submitButtonCommand(command) } }
                        ManualCommandButton { width: (parent.width - parent.spacing) / 2; height: panel.actionButtonHeight; commandEnabled: panel.manualAvailable; label: panel.t("robotNonMetal"); iconText: "\uD83E\uDD16"; command: "ROBOT_TO_NONMETAL"; active: panel.stateValue("robot_nonmetal") === 1; stateText: active ? "ON" : "OFF"; iconColor: panel.accentColor; textColor: panel.textColor; mutedText: panel.mutedText; borderColor: panel.borderColor; panelColor: panel.panelAltColor; onTriggered: function(command) { panel.controller.submitButtonCommand(command) } }
                    }
                }
            }
        }
    }
}
