import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

FloatingPanel {
    id: dialog

    property string language: "pt"
    property color panelAltColor: "#07111a"
    property color mutedText: "#9dd9ff"
    property string sectionId: ""

    width: 980
    height: 680
    panelTitle: language === "pt" ? "Ajuda e Tutorial" : "Help and Tutorial"

    function sectionList() {
        if (language === "en") {
            return [
                { id: "start", icon: "▶", color: "#48d66b", title: "Getting started", summary: "A quick route for using Blanky safely.", blocks: [
                    { title: "What it is for", text: "Use this guide when you are using Blanky for the first time or need a quick reminder." },
                    { title: "Suggested order", text: "Choose a language. Check Communications. Start the system. Choose a mode. Then use voice, Text-Bot, buttons or phone." },
                    { title: "Important", text: "Blanky only performs commands allowed by the current system state. A rejected action does not change the machine." }
                ] },
                { id: "interaction", icon: "✦", color: "#63cbff", title: "Interacting with Blanky", summary: "Understand status, response and the main action bar.", blocks: [
                    { title: "What you see", text: "Status shows what Blanky is doing. Response gives a short, clear message about the latest interaction." },
                    { title: "What you can do", text: "Use Speak to give a voice command. Choose Voice and Speed for spoken responses. Listen again repeats the last response. Clear only clears the display." },
                    { title: "How it works", text: "Blanky receives the request, interprets it, checks safety rules and records technical details in Events." },
                    { title: "Ways to interact", text: "You can use voice, Text-Bot, operation buttons or the phone. These methods work in parallel." }
                ] },
                { id: "communications", icon: "⌁", color: "#63cbff", title: "Communications", summary: "Read the four connection cards.", blocks: [
                    { title: "Microphone", text: "Shows whether voice input is ready. Waiting for voice means Blanky is ready to listen." },
                    { title: "MQTT Base and Phone", text: "MQTT Base shows the connection to the control server. MQTT Phone shows phone communication; No activity means it is connected but no recent command was received." },
                    { title: "OPC UA", text: "Shows the connection to the PLC. Offline or No PLC connection means the machine connection is unavailable." },
                    { title: "States", text: "Connected means available. Communicating means data is moving. No activity means connected but idle. Offline means no connection." }
                ] },
                { id: "operation", icon: "⚙", color: "#b7f7d4", title: "Operation Panel", summary: "Use the General and Manual controls.", blocks: [
                    { title: "Structure", text: "The panel is divided into General Control and Manual Control. It shows the current mode, system state and process information." },
                    { title: "Safe use", text: "Start the system before selecting a mode. To choose another mode, use Change mode first." },
                    { title: "Manual control", text: "Lights, cylinders, motors and robot actions become available only when Manual mode is selected." }
                ] },
                { id: "general", icon: "◉", color: "#f8c25d", title: "General Control", summary: "Start, modes and current state.", blocks: [
                    { title: "System", text: "Start begins operation. Stop returns the operational components to their safe initial state." },
                    { title: "Modes", text: "Fast, Ideal and Manual select the operating style. When one is active, use Change before choosing a different mode." },
                    { title: "Current state", text: "Active mode, System and Current process give a short view of what the machine is ready to do." }
                ] },
                { id: "manual", icon: "☝", color: "#b7f7d4", title: "Manual Control", summary: "Operate individual components in Manual mode.", blocks: [
                    { title: "Availability", text: "This area is enabled only in Manual mode. If it is dimmed, select Manual mode through General Control." },
                    { title: "Controls", text: "Lights switch on or off. Cylinders change between Extended and Retracted. Motors switch on or off. Robot buttons send the robot to metal or non-metal." },
                    { title: "Important", text: "Each button follows the same safety rules as voice, Text-Bot and phone commands." }
                ] },
                { id: "events", icon: "≡", color: "#63cbff", title: "Events", summary: "Consult the technical history of requests.", blocks: [
                    { title: "Columns", text: "ID identifies the event. Time records when it happened. Source shows voice, button, text or phone. Command is the internal command. State is OK or REJECT. Description explains the result." },
                    { title: "Results", text: "OK means the command was accepted. REJECT means it was not performed, usually because a rule, mode or current state did not allow it." },
                    { title: "Export", text: "Export Data saves Events as CSV. Export Report creates a readable PDF report. You can choose where to save the file." }
                ] },
                { id: "textbot", icon: "⌨", color: "#63cbff", title: "Text-Bot", summary: "Send one or more written commands.", blocks: [
                    { title: "Offline", text: "Offline accepts commands and variants available in the local list." },
                    { title: "Online", text: "Online uses AI to interpret a natural request and extracts only valid commands. Safety rules still apply." },
                    { title: "How to use", text: "Type one or more commands. Press Enter to send, or Shift+Enter for a new line. The information button opens the command list." }
                ] },
                { id: "voice", icon: "🎙", color: "#48d66b", title: "Voice commands", summary: "Give short, direct spoken requests.", blocks: [
                    { title: "How to use", text: "Select Speak, wait for Blanky to listen, then say a command clearly. You can say modes directly, such as Fast, Ideal or Manual." },
                    { title: "Recognition", text: "Blanky accepts common wording and some close pronunciations. If it does not understand, speak again with a short and direct request." },
                    { title: "Audio log", text: "Audio settings can show the time, transcript, interpreted command and result of each spoken request." }
                ] },
                { id: "audio", icon: "⚙", color: "#b7f7d4", title: "Settings and audio", summary: "Adjust sound and microphone behaviour.", blocks: [
                    { title: "Volume", text: "The volume button controls spoken responses and the beep. Click its icon to mute or restore sound." },
                    { title: "Audio settings", text: "Automatic mode uses a microphone profile. Manual mode allows direct adjustment. The edit icon unlocks one setting while staying in Automatic mode." },
                    { title: "Diagnostics", text: "View logs to inspect spoken requests. Logs can be exported as CSV or PDF." }
                ] },
                { id: "alerts", icon: "!", color: "#ff6b6b", title: "Errors and warnings", summary: "Know what to do when a request is not accepted.", blocks: [
                    { title: "Rejected command", text: "Read the Response area and the Event description. The machine was not changed." },
                    { title: "Communication warning", text: "Check the relevant card. Offline means the service is unavailable; No activity usually means it is connected but waiting." },
                    { title: "Next step", text: "Start the system, select the required mode, or check the connection before trying again." }
                ] },
                { id: "tutorial", icon: "✓", color: "#48d66b", title: "Full tutorial", summary: "Follow a complete, informative sequence.", blocks: [
                    { title: "1. Prepare", text: "Choose your language and check the four Communications cards." },
                    { title: "2. Start", text: "Start the system, then select Fast, Ideal or Manual mode." },
                    { title: "3. Control", text: "Use voice, Text-Bot, phone or buttons. Use Manual Control only when Manual mode is active." },
                    { title: "4. Check", text: "Read Current state and Events. Use OK and REJECT to understand what happened." },
                    { title: "5. Finish", text: "Stop the system when operation is complete. This tutorial never sends commands automatically." }
                ] }
            ]
        }

        return [
            { id: "start", icon: "▶", color: "#48d66b", title: "Começar", summary: "Um percurso rápido para utilizar o Blanky em segurança.", blocks: [
                { title: "Para que serve", text: "Utiliza este guia quando estás a conhecer o Blanky ou precisas de relembrar os passos principais." },
                { title: "Ordem sugerida", text: "Escolhe o idioma. Confirma as Comunicações. Inicia o sistema. Escolhe um modo. Depois usa voz, Text-Bot, botões ou telemóvel." },
                { title: "Atenção", text: "O Blanky só executa comandos permitidos pelo estado atual. Uma ação rejeitada não altera a máquina." }
            ] },
            { id: "interaction", icon: "✦", color: "#63cbff", title: "Interação com o Blanky", summary: "Percebe o Estado, a Resposta e a barra de ações.", blocks: [
                { title: "O que pode ver", text: "O Estado mostra o que o Blanky está a fazer. A Resposta apresenta uma mensagem curta sobre a última interação." },
                { title: "O que pode fazer", text: "Usa Falar para dar um comando de voz. Escolhe Voz e Velocidade para as respostas faladas. Voltar a ouvir repete a última resposta. Limpar limpa apenas a apresentação." },
                { title: "Como funciona", text: "O Blanky recebe a ação, interpreta o pedido, verifica as regras de segurança e regista o detalhe técnico nos Eventos." },
                { title: "Formas de interagir", text: "Podes usar voz, Text-Bot, botões de operação ou telemóvel. Estes métodos funcionam em paralelo." }
            ] },
            { id: "communications", icon: "⌁", color: "#63cbff", title: "Comunicações", summary: "Lê os quatro cartões de ligação.", blocks: [
                { title: "Microfone", text: "Mostra se a entrada de voz está pronta. A aguardar voz significa que o Blanky está pronto para ouvir." },
                { title: "MQTT Base e Telemóvel", text: "MQTT Base mostra a ligação ao servidor de controlo. MQTT Telemóvel mostra a comunicação do telemóvel; Sem atividade significa ligado, mas sem comando recente." },
                { title: "OPC UA", text: "Mostra a ligação ao PLC. Offline ou Sem ligação ao PLC significa que a ligação à máquina não está disponível." },
                { title: "Estados", text: "Ligado significa disponível. A comunicar indica troca de dados. Sem atividade indica ligação sem uso recente. Offline significa sem ligação." }
            ] },
            { id: "operation", icon: "⚙", color: "#b7f7d4", title: "Painel de Operação", summary: "Utiliza o Controlo Geral e o Controlo Manual.", blocks: [
                { title: "Organização", text: "O painel divide-se em Controlo Geral e Controlo Manual. Mostra o modo ativo, o estado do sistema e o processo atual." },
                { title: "Utilização segura", text: "Inicia o sistema antes de escolher um modo. Para escolher outro modo, utiliza primeiro Trocar." },
                { title: "Controlo Manual", text: "Luzes, cilindros, motores e robô ficam disponíveis apenas quando o modo Manual está selecionado." }
            ] },
            { id: "general", icon: "◉", color: "#f8c25d", title: "Controlo Geral", summary: "Iniciar, modos e estado atual.", blocks: [
                { title: "Sistema", text: "Iniciar começa a operação. Parar repõe os componentes operacionais no estado inicial seguro." },
                { title: "Modos", text: "Rápido, Ideal e Manual escolhem a forma de operar. Quando um modo está ativo, usa Trocar antes de escolher outro." },
                { title: "Estado atual", text: "Modo ativo, Sistema e Processo atual dão uma visão curta do que a máquina está pronta para fazer." }
            ] },
            { id: "manual", icon: "☝", color: "#b7f7d4", title: "Controlo Manual", summary: "Controla componentes individuais no modo Manual.", blocks: [
                { title: "Disponibilidade", text: "Esta área só fica ativa no modo Manual. Se estiver atenuada, escolhe Manual no Controlo Geral." },
                { title: "Controlos", text: "As luzes ligam ou desligam. Os cilindros alternam entre Avançado e Recolhido. Os motores ligam ou desligam. Os botões do robô enviam-no para metal ou não metal." },
                { title: "Atenção", text: "Cada botão segue as mesmas regras de segurança dos comandos de voz, Text-Bot e telemóvel." }
            ] },
            { id: "events", icon: "≡", color: "#63cbff", title: "Eventos", summary: "Consulta o histórico técnico dos pedidos.", blocks: [
                { title: "Colunas", text: "ID identifica o Evento. Hora indica quando aconteceu. Origem mostra voz, botão, texto ou telemóvel. Comando é o nome interno. Estado é OK ou REJECT. Descrição explica o resultado." },
                { title: "Resultados", text: "OK significa que o comando foi aceite. REJECT significa que não foi executado, normalmente por causa de uma regra, modo ou estado atual." },
                { title: "Exportar", text: "Exportar Dados guarda os Eventos em CSV. Exportar Relatório cria um PDF legível. Podes escolher onde guardar o ficheiro." }
            ] },
            { id: "textbot", icon: "⌨", color: "#63cbff", title: "Text-Bot", summary: "Envia um ou mais comandos escritos.", blocks: [
                { title: "Offline", text: "Offline aceita comandos e variantes disponíveis na lista local." },
                { title: "Online", text: "Online usa IA para interpretar uma frase natural e extrai apenas comandos válidos. As regras de segurança mantêm-se." },
                { title: "Como utilizar", text: "Escreve um ou mais comandos. Pressiona Enter para enviar, ou Shift+Enter para criar uma nova linha. O botão de informação abre a lista de comandos." }
            ] },
            { id: "voice", icon: "🎙", color: "#48d66b", title: "Comandos de voz", summary: "Dá pedidos falados curtos e diretos.", blocks: [
                { title: "Como utilizar", text: "Seleciona Falar, espera que o Blanky fique a ouvir e diz o comando com clareza. Podes dizer apenas Rápido, Ideal ou Manual para escolher o modo." },
                { title: "Reconhecimento", text: "O Blanky aceita formas comuns de dizer um comando e algumas pronúncias próximas. Se não perceber, fala novamente com um pedido curto e direto." },
                { title: "Registo de áudio", text: "Nas configurações de áudio podes ver a hora, transcrição, comando interpretado e resultado de cada pedido falado." }
            ] },
            { id: "audio", icon: "⚙", color: "#b7f7d4", title: "Definições e áudio", summary: "Ajusta o som e o comportamento do microfone.", blocks: [
                { title: "Volume", text: "O botão de volume controla as respostas faladas e o bip. Clica no ícone para silenciar ou voltar a ativar o som." },
                { title: "Configurações de áudio", text: "O modo Automático usa um perfil de microfone. O modo Manual permite ajustar diretamente. O lápis desbloqueia um único ajuste mantendo o modo Automático." },
                { title: "Diagnóstico", text: "Ver logs permite consultar pedidos falados. Os registos podem ser exportados em CSV ou PDF." }
            ] },
            { id: "alerts", icon: "!", color: "#ff6b6b", title: "Erros e avisos", summary: "Sabe o que fazer quando um pedido não é aceite.", blocks: [
                { title: "Comando rejeitado", text: "Lê a área Resposta e a Descrição do Evento. A máquina não foi alterada." },
                { title: "Aviso de comunicação", text: "Consulta o cartão respetivo. Offline significa indisponível; Sem atividade normalmente significa ligado, mas à espera." },
                { title: "Passo seguinte", text: "Inicia o sistema, escolhe o modo necessário ou confirma a ligação antes de tentar novamente." }
            ] },
            { id: "tutorial", icon: "✓", color: "#48d66b", title: "Tutorial completo", summary: "Segue uma sequência completa e apenas informativa.", blocks: [
                { title: "1. Preparar", text: "Escolhe o idioma e confirma os quatro cartões de Comunicações." },
                { title: "2. Iniciar", text: "Inicia o sistema e depois escolhe Rápido, Ideal ou Manual." },
                { title: "3. Controlar", text: "Usa voz, Text-Bot, telemóvel ou botões. Utiliza o Controlo Manual apenas quando o modo Manual estiver ativo." },
                { title: "4. Confirmar", text: "Consulta o Estado atual e os Eventos. Usa OK e REJECT para perceber o que aconteceu." },
                { title: "5. Terminar", text: "Para o sistema quando a operação terminar. Este tutorial nunca envia comandos automaticamente." }
            ] }
        ]
    }

    function currentSection() {
        var all = sectionList()
        for (var i = 0; i < all.length; i++) {
            if (all[i].id === sectionId)
                return all[i]
        }
        return null
    }

    function showHome() {
        sectionId = ""
        helpScroll.contentItem.contentY = 0
    }

    function showSection(id) {
        sectionId = id
        helpScroll.contentItem.contentY = 0
    }

    function activeColor() {
        var section = currentSection()
        return section ? section.color : "#63cbff"
    }

    function blockIcon(index) {
        var icons = ["●", "→", "✓", "!"]
        return icons[index % icons.length]
    }

    function safeHelpText(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
    }

    function decorateHelpText(value) {
        var text = safeHelpText(value)
        var references = language === "pt" ? [
            { word: "Microfone", icon: "\uD83C\uDF99", color: "#48d66b" },
            { word: "MQTT Base", icon: "\uD83D\uDCE1", color: "#63cbff" },
            { word: "Telem\u00f3vel", icon: "\uD83D\uDCF1", color: "#f8c25d" },
            { word: "OPC UA", icon: "\uD83D\uDD17", color: "#ff6b6b" },
            { word: "Painel de Opera\u00e7\u00e3o", icon: "\u2699", color: "#b7f7d4" },
            { word: "Controlo Geral", icon: "\u25c9", color: "#f8c25d" },
            { word: "Controlo Manual", icon: "\u261d", color: "#b7f7d4" },
            { word: "Eventos", icon: "\u2261", color: "#63cbff" },
            { word: "Text-Bot", icon: "\u2328", color: "#63cbff" },
            { word: "Falar", icon: "\uD83C\uDF99", color: "#48d66b" },
            { word: "Volume", icon: "\uD83D\uDD0a", color: "#63cbff" }
        ] : [
            { word: "Microphone", icon: "\uD83C\uDF99", color: "#48d66b" },
            { word: "MQTT Base", icon: "\uD83D\uDCE1", color: "#63cbff" },
            { word: "Phone", icon: "\uD83D\uDCF1", color: "#f8c25d" },
            { word: "OPC UA", icon: "\uD83D\uDD17", color: "#ff6b6b" },
            { word: "Operation Panel", icon: "\u2699", color: "#b7f7d4" },
            { word: "General Control", icon: "\u25c9", color: "#f8c25d" },
            { word: "Manual Control", icon: "\u261d", color: "#b7f7d4" },
            { word: "Events", icon: "\u2261", color: "#63cbff" },
            { word: "Text-Bot", icon: "\u2328", color: "#63cbff" },
            { word: "Speak", icon: "\uD83C\uDF99", color: "#48d66b" },
            { word: "Volume", icon: "\uD83D\uDD0a", color: "#63cbff" }
        ]

        for (var i = 0; i < references.length; ++i) {
            var reference = references[i]
            var replacement = "<font color='" + reference.color + "'><b>" + reference.icon + " " + reference.word + "</b></font>"
            text = text.split(reference.word).join(replacement)
        }
        return text
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 12

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: dialog.sectionId === "" ? 54 : 42

            Label {
                anchors.fill: parent
                visible: dialog.sectionId === ""
                text: dialog.language === "pt"
                    ? "Escolhe uma área para saberes o que mostra e como a podes utilizar."
                    : "Choose an area to learn what it shows and how to use it."
                color: dialog.mutedText
                font.pixelSize: 14
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }

            MenuActionButton {
                visible: dialog.sectionId !== ""
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                text: dialog.language === "pt" ? "← Voltar às secções" : "← Back to sections"
                width: 190
                height: 36
                accentColor: "#63cbff"
                textColor: dialog.titleColor
                mutedText: dialog.mutedText
                borderColor: dialog.borderColor
                panelColor: dialog.panelAltColor
                onClicked: dialog.showHome()
            }
        }

        ScrollView {
            id: helpScroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            contentHeight: helpContent.height
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical.policy: ScrollBar.AlwaysOn

            Item {
                id: helpContent
                width: helpScroll.availableWidth
                height: dialog.sectionId === "" ? homeGrid.implicitHeight : detailColumn.implicitHeight

                GridLayout {
                    id: homeGrid
                    visible: dialog.sectionId === ""
                    width: parent.width
                    height: implicitHeight
                    columns: 2
                    columnSpacing: 12
                    rowSpacing: 12

                    Repeater {
                        model: dialog.sectionList()

                        Rectangle {
                            required property var modelData
                            Layout.preferredWidth: (parent.width - parent.columnSpacing) / 2
                            Layout.preferredHeight: 104
                            radius: 12
                            color: hoverArea.containsMouse ? Qt.lighter(dialog.panelAltColor, 1.18) : dialog.panelAltColor
                            border.color: modelData.color
                            border.width: 1

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 12

                                Label {
                                    text: modelData.icon
                                    color: modelData.color
                                    font.pixelSize: 25
                                    font.bold: true
                                    Layout.alignment: Qt.AlignVCenter
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.alignment: Qt.AlignVCenter
                                    spacing: 3

                                    Label {
                                        text: modelData.title
                                        color: dialog.titleColor
                                        font.pixelSize: 15
                                        font.bold: true
                                        Layout.fillWidth: true
                                        horizontalAlignment: Text.AlignLeft
                                        elide: Text.ElideRight
                                    }
                                    Label {
                                        text: modelData.summary
                                        color: dialog.mutedText
                                        font.pixelSize: 11
                                        Layout.fillWidth: true
                                        wrapMode: Text.WordWrap
                                        horizontalAlignment: Text.AlignLeft
                                        maximumLineCount: 2
                                        elide: Text.ElideRight
                                    }
                                }
                            }

                            MouseArea {
                                id: hoverArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: dialog.showSection(modelData.id)
                            }
                        }
                    }
                }

                Column {
                    id: detailColumn
                    visible: dialog.sectionId !== ""
                    width: parent.width
                    height: implicitHeight
                    spacing: 12

                    Rectangle {
                        width: parent.width
                        height: 92
                        radius: 14
                        color: dialog.panelAltColor
                        border.color: dialog.activeColor()
                        border.width: 1

                        Column {
                            anchors.centerIn: parent
                            spacing: 3
                            Label {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: dialog.currentSection() ? dialog.currentSection().icon : "?"
                                color: dialog.activeColor()
                                font.pixelSize: 27
                                font.bold: true
                            }
                            Label {
                                text: dialog.currentSection() ? dialog.currentSection().title : ""
                                color: dialog.titleColor
                                font.pixelSize: 18
                                font.bold: true
                            }
                        }
                    }

                    Repeater {
                        model: dialog.currentSection() ? dialog.currentSection().blocks : []

                        Rectangle {
                            required property var modelData
                            width: parent.width
                            implicitHeight: Math.max(82, blockContent.implicitHeight + 28)
                            radius: 12
                            color: dialog.panelAltColor
                            border.color: dialog.borderColor
                            border.width: 1

                            Column {
                                id: blockContent
                                width: parent.width - 28
                                anchors.centerIn: parent
                                spacing: 7
                                Label {
                                    width: parent.width
                                    text: dialog.blockIcon(index) + "  " + modelData.title
                                    color: dialog.activeColor()
                                    font.pixelSize: 15
                                    font.bold: true
                                    horizontalAlignment: Text.AlignLeft
                                }
                                Label {
                                    id: blockText
                                    width: parent.width
                                    text: dialog.decorateHelpText(modelData.text)
                                    color: dialog.textColor
                                    font.pixelSize: 13
                                    wrapMode: Text.WordWrap
                                    horizontalAlignment: Text.AlignLeft
                                    textFormat: Text.RichText
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
