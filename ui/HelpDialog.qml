import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

FloatingPanel {
    id: dialog

    property string language: "pt"
    property color panelAltColor: "#07111a"
    property color mutedText: "#9dd9ff"
    property color accentColor: "#63cbff"
    property color successColor: "#48d66b"
    property color warningColor: "#f8c25d"
    property color errorColor: "#ff6b6b"
    property color inactiveColor: "#8fa8b8"
    property real textScale: 1.0
    property string sectionId: ""

    width: 1060
    height: 720
    panelTitle: language === "pt" ? "Ajuda e Tutorial" : "Help and Tutorial"

    function tr(pt, en) {
        return language === "pt" ? pt : en
    }

    function sectionList() {
        return [
            { id: "start", icon: "▶", tone: "success", title: tr("Começar", "Getting started"), summary: tr("Primeiros passos para utilizar o Blanky em segurança.", "First steps for using Blanky safely.") },
            { id: "interaction", icon: "✦", tone: "accent", title: tr("Interação com o Blanky", "Interacting with Blanky"), summary: tr("Estado, Resposta e barra de ações.", "Status, Response and action bar.") },
            { id: "communications", icon: "⌁", tone: "accent", title: tr("Comunicações", "Communications"), summary: tr("Os quatro cartões de ligação.", "The four connection cards.") },
            { id: "operation", icon: "⚙", tone: "success", title: tr("Painel de Operação", "Operation Panel"), summary: tr("Controlo Geral e Controlo Manual.", "General and Manual Control.") },
            { id: "general", icon: "◉", tone: "warning", title: tr("Controlo Geral", "General Control"), summary: tr("Sistema, modos e estado atual.", "System, modes and current state.") },
            { id: "manual", icon: "☝", tone: "success", title: tr("Controlo Manual", "Manual Control"), summary: tr("Luzes, cilindros, motores e robô.", "Lights, cylinders, motors and robot.") },
            { id: "events", icon: "≡", tone: "accent", title: tr("Eventos", "Events"), summary: tr("Histórico e resultado dos pedidos.", "Request history and results.") },
            { id: "textbot", icon: "⌨", tone: "accent", title: "Text-Bot", summary: tr("Um ou vários comandos escritos.", "One or more written commands.") },
            { id: "voice", icon: "🎙", tone: "success", title: tr("Comandos de voz", "Voice commands"), summary: tr("Pedidos naturais, pelas tuas palavras.", "Natural requests in your own words.") },
            { id: "audio", icon: "🔊", tone: "warning", title: tr("Definições e áudio", "Settings and audio"), summary: tr("Som, microfone e acessibilidade.", "Sound, microphone and accessibility.") },
            { id: "alerts", icon: "!", tone: "error", title: tr("Erros e avisos", "Errors and warnings"), summary: tr("O que fazer quando algo não é aceite.", "What to do when a request is not accepted.") },
            { id: "tutorial", icon: "✓", tone: "success", title: tr("Tutorial completo", "Full tutorial"), summary: tr("Um percurso guiado pela interface.", "A guided route through the interface.") }
        ]
    }

    function currentIndex() {
        var all = sectionList()
        for (var i = 0; i < all.length; ++i) {
            if (all[i].id === sectionId)
                return i
        }
        return -1
    }

    function currentSection() {
        var index = currentIndex()
        return index < 0 ? null : sectionList()[index]
    }

    function semanticColor(tone) {
        if (tone === "success") return successColor
        if (tone === "warning") return warningColor
        if (tone === "error") return errorColor
        return accentColor
    }

    function showHome() {
        sectionId = ""
        helpScroll.contentItem.contentY = 0
    }

    function showSection(id) {
        sectionId = id
        helpScroll.contentItem.contentY = 0
    }

    function moveSection(offset) {
        var index = currentIndex() + offset
        if (index >= 0 && index < sectionList().length)
            showSection(sectionList()[index].id)
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: Math.round(10 * dialog.textScale)

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: dialog.sectionId === "" ? Math.round(46 * dialog.textScale) : Math.round(112 * dialog.textScale)

            Label {
                visible: dialog.sectionId === ""
                anchors.fill: parent
                text: dialog.tr("Escolhe uma área para perceberes a interface e utilizares o Blanky com segurança.", "Choose an area to understand the interface and use Blanky safely.")
                color: dialog.mutedText
                font.pixelSize: Math.round(14 * dialog.textScale)
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }

            ColumnLayout {
                visible: dialog.sectionId !== ""
                anchors.fill: parent
                spacing: Math.round(6 * dialog.textScale)

                RowLayout {
                    Layout.fillWidth: true
                    MenuActionButton {
                        text: dialog.tr("← Voltar às secções", "← Back to sections")
                        Layout.preferredWidth: Math.round(190 * dialog.textScale)
                        Layout.preferredHeight: Math.round(34 * dialog.textScale)
                        accentColor: dialog.accentColor; textColor: dialog.titleColor; mutedText: dialog.mutedText; borderColor: dialog.borderColor; panelColor: dialog.panelAltColor
                        onClicked: dialog.showHome()
                    }
                    Item { Layout.fillWidth: true }
                    HelpBadge {
                        symbol: dialog.currentSection() ? dialog.currentSection().icon : "?"
                        label: dialog.currentSection() ? dialog.currentSection().title : ""
                        accentColor: dialog.currentSection() ? dialog.semanticColor(dialog.currentSection().tone) : dialog.accentColor
                        surfaceColor: dialog.panelAltColor; textColor: dialog.titleColor; textScale: dialog.textScale
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Math.round(10 * dialog.textScale)
                    Rectangle { Layout.preferredWidth: 5; Layout.fillHeight: true; radius: 3; color: dialog.currentSection() ? dialog.semanticColor(dialog.currentSection().tone) : dialog.accentColor }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 1
                        Label { text: dialog.currentSection() ? dialog.currentSection().title : ""; color: dialog.titleColor; font.bold: true; font.pixelSize: Math.round(19 * dialog.textScale); Layout.fillWidth: true }
                        Label { text: dialog.currentSection() ? dialog.currentSection().summary : ""; color: dialog.mutedText; font.pixelSize: Math.round(12 * dialog.textScale); Layout.fillWidth: true; wrapMode: Text.WordWrap }
                    }
                }

                RowLayout {
                    visible: dialog.sectionId === "start" || dialog.sectionId === "tutorial"
                    Layout.fillWidth: true
                    spacing: 0
                    Repeater {
                        model: 6
                        RowLayout {
                            required property int index
                            Layout.fillWidth: true
                            spacing: 4
                            Label { text: (index + 1) + " ●"; color: dialog.successColor; font.bold: true; font.pixelSize: Math.round(11 * dialog.textScale) }
                            Rectangle { visible: index < 5; Layout.fillWidth: true; Layout.preferredHeight: 1; color: dialog.borderColor }
                        }
                    }
                }
            }
        }

        ScrollView {
            id: helpScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            // Reserve a gutter so the overlay scrollbar never covers tutorial text.
            contentWidth: availableWidth - Math.round(14 * dialog.textScale)
            contentHeight: helpContent.height
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical.policy: ScrollBar.AlwaysOn

            Item {
                id: helpContent
                width: helpScroll.availableWidth - Math.round(14 * dialog.textScale)
                height: dialog.sectionId === "" ? homeGrid.implicitHeight : sectionColumn.implicitHeight

                GridLayout {
                    id: homeGrid
                    visible: dialog.sectionId === ""
                    width: parent.width
                    height: implicitHeight
                    columns: 2
                    columnSpacing: Math.round(12 * dialog.textScale)
                    rowSpacing: Math.round(12 * dialog.textScale)

                    Repeater {
                        model: dialog.sectionList()
                        Rectangle {
                            required property var modelData
                            readonly property color cardColor: dialog.semanticColor(modelData.tone)
                            readonly property bool hovered: hoverArea.containsMouse
                            readonly property real cardLuminance: 0.2126 * cardColor.r + 0.7152 * cardColor.g + 0.0722 * cardColor.b
                            readonly property color hoverTextColor: cardLuminance > 0.62 ? "#07111a" : "#f7fbff"
                            Layout.preferredWidth: (parent.width - parent.columnSpacing) / 2
                            Layout.preferredHeight: Math.round(104 * dialog.textScale)
                            radius: Math.round(12 * dialog.textScale)
                            color: hovered ? cardColor : dialog.panelAltColor
                            border.color: cardColor
                            border.width: hovered ? 2 : 1
                            scale: hovered ? 1.012 : 1.0
                            z: hovered ? 1 : 0

                            Behavior on color { ColorAnimation { duration: 140 } }
                            Behavior on scale { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: Math.round(11 * dialog.textScale)
                                spacing: Math.round(11 * dialog.textScale)
                                Rectangle { Layout.preferredWidth: 4; Layout.fillHeight: true; radius: 2; color: hovered ? hoverTextColor : cardColor }
                                Label { text: modelData.icon; color: hovered ? hoverTextColor : cardColor; font.pixelSize: Math.round(24 * dialog.textScale); font.bold: true }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.alignment: Qt.AlignVCenter
                                    spacing: 3
                                    Label { text: modelData.title; color: hovered ? hoverTextColor : dialog.titleColor; font.bold: true; font.pixelSize: Math.round(15 * dialog.textScale); Layout.fillWidth: true; elide: Text.ElideRight }
                                    Label { text: modelData.summary; color: hovered ? hoverTextColor : dialog.mutedText; font.pixelSize: Math.round(11 * dialog.textScale); Layout.fillWidth: true; wrapMode: Text.WordWrap; maximumLineCount: 2; elide: Text.ElideRight }
                                }
                            }
                            MouseArea { id: hoverArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: dialog.showSection(modelData.id) }
                        }
                    }
                }

                Column {
                    id: sectionColumn
                    visible: dialog.sectionId !== ""
                    width: parent.width
                    height: implicitHeight
                    spacing: Math.round(12 * dialog.textScale)

                    HelpTutorialContent {
                        width: parent.width
                        language: dialog.language
                        sectionId: dialog.sectionId
                        panelColor: dialog.panelColor; panelAltColor: dialog.panelAltColor; borderColor: dialog.borderColor
                        textColor: dialog.textColor; mutedText: dialog.mutedText
                        accentColor: dialog.accentColor; successColor: dialog.successColor; warningColor: dialog.warningColor; errorColor: dialog.errorColor; inactiveColor: dialog.inactiveColor
                        textScale: dialog.textScale
                    }

                    RowLayout {
                        width: parent.width
                        spacing: 10
                        MenuActionButton {
                            text: dialog.tr("← Secção anterior", "← Previous section")
                            visible: dialog.currentIndex() > 0
                            Layout.preferredWidth: Math.round(180 * dialog.textScale)
                            Layout.preferredHeight: Math.round(36 * dialog.textScale)
                            accentColor: dialog.inactiveColor; textColor: dialog.titleColor; mutedText: dialog.mutedText; borderColor: dialog.borderColor; panelColor: dialog.panelAltColor
                            onClicked: dialog.moveSection(-1)
                        }
                        Item { Layout.fillWidth: true }
                        MenuActionButton {
                            text: dialog.tr("Próxima secção →", "Next section →")
                            visible: dialog.currentIndex() >= 0 && dialog.currentIndex() < dialog.sectionList().length - 1
                            Layout.preferredWidth: Math.round(180 * dialog.textScale)
                            Layout.preferredHeight: Math.round(36 * dialog.textScale)
                            accentColor: dialog.currentSection() ? dialog.semanticColor(dialog.currentSection().tone) : dialog.accentColor
                            textColor: dialog.titleColor; mutedText: dialog.mutedText; borderColor: dialog.borderColor; panelColor: dialog.panelAltColor
                            onClicked: dialog.moveSection(1)
                        }
                    }
                }
            }
        }
    }
}
