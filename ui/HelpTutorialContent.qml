import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Column {
    id: tutorial

    property string language: "pt"
    property string sectionId: ""
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
    property real textScale: 1.0
    property bool monochrome: false

    width: parent ? parent.width : 0
    spacing: Math.round(12 * textScale)

    function tr(pt, en) {
        return language === "pt" ? pt : en
    }

    function tone(toneName) {
        if (toneName === "success")
            return successColor
        if (toneName === "warning")
            return warningColor
        if (toneName === "error")
            return errorColor
        if (toneName === "inactive")
            return inactiveColor
        return accentColor
    }

    function step(titlePt, titleEn, textPt, textEn, demo, toneName, noteKind, noteTitlePt, noteTitleEn, notePt, noteEn) {
        return {
            title: tr(titlePt, titleEn), text: tr(textPt, textEn), demo: demo,
            tone: toneName || "accent", noteKind: noteKind || "",
            noteTitle: tr(noteTitlePt || "", noteTitleEn || ""),
            note: tr(notePt || "", noteEn || "")
        }
    }

    function steps() {
        if (sectionId === "start") {
            return [
                step("Escolhe o idioma", "Choose the language", "Seleciona o idioma que pretendes utilizar. Todos os textos e respostas do Blanky serão atualizados.", "Select the language you want to use. All Blanky text and responses update together.", "language", "accent", "expected", "O que deves ver", "What you should see", "O idioma selecionado fica visualmente destacado.", "The selected language is visually highlighted."),
                step("Escolhe uma vista", "Choose a view", "No Menu Inicial, escolhe Geral, Voz, Text-Bot, Operação ou Telemóvel. Todas mostram os mesmos Eventos e Comunicações.", "From the Main Menu choose General, Voice, Text-Bot, Operation or Phone. All views share Events and Communications.", "views", "accent", "info", "Navegação", "Navigation", "Nas vistas, o botão Home e o logótipo Blanky regressam ao Menu. O Power existe apenas no Menu Inicial.", "In a view, Home and the Blanky logo return to the Menu. Power appears only on the Main Menu."),
                step("Confirma as Comunicações", "Check Communications", "Antes de iniciar, confirma se os serviços necessários estão disponíveis.", "Before starting, check that the required services are available.", "communications", "accent", "info", "Como interpretar", "How to interpret", "✓ Pronto   ! Atenção   ✕ Problema de ligação", "✓ Ready   ! Attention   ✕ Connection problem"),
                step("Inicia o sistema", "Start the system", "Utiliza Iniciar por botão, voz, texto ou telemóvel. Antes disso, os botões dos modos permanecem desativados.", "Use Start by button, voice, text or phone. Until then, the mode buttons remain disabled.", "system", "success", "expected", "Depois de iniciar", "After starting", "O monitor Estado do sistema deverá indicar que podes escolher um modo.", "The System status monitor should indicate that you can choose a mode."),
                step("Escolhe um modo", "Choose a mode", "Rápido privilegia a rapidez. Ideal usa a configuração adequada. Manual permite controlar os componentes individualmente.", "Fast prioritises speed. Ideal uses the recommended configuration. Manual controls individual components.", "modes", "warning", "expected", "Modo ativo", "Active mode", "✓ Manual", "✓ Manual"),
                step("Interage com o Blanky", "Interact with Blanky", "Escolhe voz, Text-Bot, botões ou telemóvel conforme for mais simples para o teu pedido.", "Choose voice, Text-Bot, buttons or phone according to what is simplest for your request.", "methods", "accent", "tip", "Dica", "Tip", "Podes usar estas formas de interação em paralelo.", "You can use these interaction methods in parallel."),
                step("Confirma Resposta e Estado do sistema", "Check Response and System status", "O Blanky apresenta uma resposta à ação solicitada. Consulta também o monitor de estado antes de continuar.", "Blanky shows a response to the requested action. Check the status monitor before continuing.", "response", "success", "attention", "Importante", "Important", "Uma resposta rejeitada não altera a máquina.", "A rejected response does not change the machine.")
            ]
        }
        if (sectionId === "interaction") {
            return [
                step("Estado e Resposta", "Status and Response", "Estado indica a situação atual. Resposta mostra o resultado ou orientação do último pedido.", "Status shows the current situation. Response gives the result or guidance for the last request.", "response", "accent", "tip", "Exemplos", "Examples", "Pode começar.  |  Ligar Motor 1.  |  Comando não reconhecido.", "You can start.  |  Switch on Motor 1.  |  Command not recognised."),
                step("Barra de ações", "Action bar", "Nas vistas Geral e Voz, Falar inicia a voz. Voz, Velocidade e Voltar a ouvir ajustam as respostas faladas. Limpar limpa a apresentação.", "In General and Voice views, Speak starts voice input. Voice, Speed and Listen again adjust spoken responses. Clear clears the display.", "actionbar", "accent", "info", "Como funciona", "How it works", "O Blanky interpreta o pedido, verifica as regras de segurança e regista o detalhe nos Eventos.", "Blanky interprets the request, checks safety rules and records detail in Events."),
                step("Regressar ao Menu", "Return to Menu", "Em qualquer vista, usa o botão Home no canto superior direito ou clica no logótipo Blanky. O Power só está disponível no Menu Inicial.", "From any view, use Home in the upper right or click the Blanky logo. Power is available only on the Main Menu.", "navigation", "accent", "tip", "Sem perder o contexto", "Keep your context", "As vistas partilham o mesmo sistema, os Eventos e as Comunicações.", "Views share the same system, Events and Communications.")
            ]
        }
        if (sectionId === "communications") {
            return [
                step("Os quatro cartões", "The four cards", "Cada cartão mostra o serviço, o estado e uma mensagem simples sobre a ligação.", "Each card shows the service, status and a simple connection message.", "communications", "accent", "info", "Microfone e MQTT", "Microphone and MQTT", "Ligado significa disponível. Sem atividade significa ligado, mas à espera.", "Connected means available. No activity means connected, but waiting."),
                step("Ligação à máquina", "Machine connection", "OPC UA mostra a ligação ao PLC. Não é necessário conhecer detalhes técnicos para interpretar o cartão.", "OPC UA shows the PLC connection. You do not need technical details to read the card.", "opcua", "error", "attention", "OPC UA", "OPC UA", "✓ LIGADO: comunicação com o PLC.  ✕ OFFLINE: sem ligação ao PLC.", "✓ CONNECTED: PLC communication.  ✕ OFFLINE: no PLC connection.")
            ]
        }
        if (sectionId === "operation") {
            return [
                step("Duas áreas", "Two areas", "Controlo Geral gere o funcionamento global e mostra o monitor Estado do sistema. Controlo Manual atua nos componentes quando Manual está ativo.", "General Control manages the system and shows the System status monitor. Manual Control operates components when Manual is active.", "operation", "success", "attention", "Utilização segura", "Safe use", "Inicia o sistema antes de escolher um modo. Usa Trocar antes de escolher outro modo.", "Start the system before choosing a mode. Use Change before choosing another mode.")
            ]
        }
        if (sectionId === "general") {
            return [
                step("Sistema e modos", "System and modes", "Iniciar prepara a operação. Os botões Rápido, Ideal e Manual só ficam disponíveis depois de START.", "Start prepares operation. Fast, Ideal and Manual become available only after START.", "general", "warning", "info", "Trocar", "Change", "Quando existe um modo ativo, usa Trocar antes de selecionar outro modo.", "With a mode active, use Change before choosing another mode."),
                step("Estado do sistema", "System status", "Este monitor é apenas informativo: apresenta Modo ativo, Sistema e Processo em tempo real. O ponto verde indica que o sistema está iniciado.", "This monitor is read only: it shows Active mode, System and Process in real time. The green dot indicates that the system has started.", "currentstate", "success", "expected", "Exemplo", "Example", "Manual  |  Controlo manual ativo  |  A aguardar comando", "Manual  |  Manual control active  |  Waiting for command")
            ]
        }
        if (sectionId === "manual") {
            return [
                step("Controla por grupos", "Control by groups", "No modo Manual podes atuar sobre Luzes, Cilindros, Motores e Robô. Alguns controlos ficam indisponíveis quando o estado não permite a operação.", "In Manual mode you can act on Lights, Cylinders, Motors and Robot. Some controls become unavailable when the state does not allow operation.", "manual", "success", "expected", "Motor 1", "Motor 1", "○ OFF: motor parado.  ✓ ON: motor ativo.", "○ OFF: motor stopped.  ✓ ON: motor active.")
            ]
        }
        if (sectionId === "events") {
            return [
                step("Lê o histórico", "Read the history", "Eventos guarda ID, Hora, Origem, Comando, Estado e Descrição de cada pedido.", "Events stores ID, Time, Source, Command, State and Description for every request.", "events", "accent", "expected", "✓ OK", "✓ OK", "Comando aceite.", "Command accepted."),
                step("Quando aparece REJECT", "When REJECT appears", "REJECT significa que o pedido não foi executado por uma regra, modo ou estado atual. A máquina não é alterada.", "REJECT means the request was not executed due to a rule, mode or current state. The machine is not changed.", "reject", "error", "attention", "✕ REJEITADO", "✕ REJECTED", "Confirma a Descrição e escolhe o próximo passo indicado.", "Check Description and follow the suggested next step.")
            ]
        }
        if (sectionId === "textbot") {
            return [
                step("Escreve e envia", "Write and send", "Podes escrever um ou vários comandos. Enter envia; Shift+Enter cria uma nova linha.", "You can write one or more commands. Enter sends; Shift+Enter makes a new line.", "textbot", "accent", "tip", "Exemplos úteis", "Useful examples", "Ligar Motor 1  |  Acender luz verde  |  Ativar modo manual  |  Avançar Cilindro C", "Switch on Motor 1  |  Turn on green light  |  Activate manual mode  |  Extend Cylinder C"),
                step("Offline e Online", "Offline and Online", "O Text-Bot tenta começar Online. Se a IA não estiver disponível, passa a Offline e informa na Resposta. Offline usa a lista local.", "Text-Bot tries to start Online. If AI is unavailable, it switches to Offline and explains this in Response. Offline uses the local list.", "online", "success", "info", "Informação", "Information", "O botão i mostra os comandos disponíveis no modo atual.", "The i button shows commands available in the current mode.")
            ]
        }
        if (sectionId === "voice") {
            return [
                step("Fala naturalmente", "Speak naturally", "Não precisas de memorizar frases exatas. Diz de forma curta e clara o que pretendes fazer.", "You do not need to memorise exact phrases. Say clearly and briefly what you want to do.", "voice", "success", "tip", "Formas equivalentes", "Equivalent forms", "Liga o motor 1.  |  Podes ligar o motor 1?  |  Quero o motor 1 ligado.", "Switch on motor 1.  |  Can you switch on motor 1?  |  I want motor 1 on."),
                step("Se não for compreendido", "If it is not understood", "O Blanky responde sem executar uma ação incerta.", "Blanky responds without executing an uncertain action.", "unknown", "warning", "attention", "✕ Comando não reconhecido", "✕ Command not recognised", "Repete o pedido utilizando uma frase curta e clara.", "Repeat the request using a short, clear sentence.")
            ]
        }
        if (sectionId === "audio") {
            return [
                step("Definições", "Settings", "Abre um dos dois cartões: Áudio e microfone para captação e voz, ou Comunicações e IA para ligações e chave da API.", "Open one of the two cards: Audio and microphone for capture and voice, or Communications and AI for connections and the API key.", "settings", "warning", "info", "Diagnóstico", "Diagnostics", "Em Áudio e microfone, Ver logs permite consultar e exportar pedidos falados.", "In Audio and microphone, View logs lets you inspect and export spoken requests."),
                step("Aparência e acessibilidade", "Appearance and accessibility", "Escolhe um dos seis modos visuais, ajusta a leitura, a adaptação ao ecrã e as animações ao passar o rato.", "Choose one of six visual modes, adjust reading size, screen adaptation and hover animations.", "appearance", "accent", "tip", "Sempre legível", "Always readable", "Os símbolos e o texto mantêm o significado dos estados mesmo sem cor.", "Symbols and text retain state meaning even without colour.")
            ]
        }
        if (sectionId === "alerts") {
            return [
                step("Quando algo não é aceite", "When something is not accepted", "Lê a Resposta e a Descrição do Evento. Uma ação rejeitada não altera a máquina.", "Read Response and the Event Description. A rejected action does not change the machine.", "reject", "error", "attention", "Passo seguinte", "Next step", "Inicia o sistema, escolhe o modo necessário ou confirma a ligação antes de tentar novamente.", "Start the system, select the required mode or check the connection before trying again.")
            ]
        }
        return [
            step("Preparar", "Prepare", "No Menu Inicial, escolhe o idioma e uma vista. Confirma as Comunicações.", "From the Main Menu, choose a language and a view. Check Communications.", "views", "success", "info", "1 de 5", "1 of 5", "Este tutorial é apenas informativo e nunca envia comandos.", "This tutorial is informational only and never sends commands."),
            step("Iniciar", "Start", "Inicia o sistema e escolhe Rápido, Ideal ou Manual.", "Start the system and choose Fast, Ideal or Manual.", "modes", "success", "", "", "", "", ""),
            step("Controlar", "Control", "Usa voz, Text-Bot, telemóvel ou botões.", "Use voice, Text-Bot, phone or buttons.", "methods", "accent", "", "", "", "", ""),
            step("Confirmar", "Check", "Consulta Estado do sistema e Eventos antes de continuar.", "Check System status and Events before continuing.", "currentstate", "success", "", "", "", "", ""),
            step("Terminar", "Finish", "Para o sistema quando a operação terminar. Regressa ao Menu para desligar o Blanky.", "Stop the system when operation is complete. Return to the Menu to shut down Blanky.", "system", "warning", "attention", "Importante", "Important", "O tutorial nunca envia comandos automaticamente.", "The tutorial never sends commands automatically.")
        ]
    }

    function demoItems(kind) {
        if (kind === "language") return [{ icon: monochrome ? "PT" : "🇵🇹", label: "Português", state: "✓", tone: "success" }, { icon: monochrome ? "EN" : "🇬🇧", label: "English", state: "", tone: "accent" }]
        if (kind === "views") return [{ icon: "▦", label: tr("Geral", "General"), state: "", tone: "accent" }, { kind: "microphone", label: tr("Voz", "Voice"), state: "", tone: "success" }, { icon: "▤", label: "Text-Bot", state: "", tone: "warning" }, { icon: "☷", label: tr("Operação", "Operation"), state: "", tone: "accent" }, { icon: "▯", label: tr("Telemóvel", "Phone"), state: "", tone: "accent" }]
        if (kind === "navigation") return [{ kind: "home", label: tr("Menu Inicial", "Main Menu"), state: "", tone: "accent" }, { icon: "B", label: "Blanky", state: tr("Menu", "Menu"), tone: "accent" }, { kind: "power", label: tr("Desligar", "Shut down"), state: tr("Só no Menu", "Menu only"), tone: "error" }]
        if (kind === "communications") return [{ kind: "microphone", label: tr("MICROFONE", "MICROPHONE"), state: "✓ " + tr("LIGADO", "CONNECTED"), tone: "success" }, { icon: monochrome ? "⌁" : "📡", label: "MQTT BASE", state: "✓ " + tr("LIGADO", "CONNECTED"), tone: "success" }, { icon: monochrome ? "↔" : "🔗", label: "OPC UA", state: "✕ OFFLINE", tone: "error" }, { icon: monochrome ? "▯" : "📱", label: "MQTT " + tr("TELEMÓVEL", "PHONE"), state: "! " + tr("SEM ATIVIDADE", "NO ACTIVITY"), tone: "warning" }]
        if (kind === "opcua") return [{ icon: monochrome ? "↔" : "🔗", label: "OPC UA", state: "✓ " + tr("LIGADO", "CONNECTED"), tone: "success" }, { icon: monochrome ? "↔" : "🔗", label: "OPC UA", state: "✕ OFFLINE", tone: "error" }]
        if (kind === "system") return [{ icon: "▶", label: tr("Iniciar", "Start"), state: "○ OFF", tone: "success" }, { icon: "■", label: tr("Parar", "Stop"), state: "✓ ON", tone: "warning" }]
        if (kind === "modes") return [{ icon: monochrome ? "▶" : "⚡", label: tr("Rápido", "Fast"), state: "○ OFF", tone: "warning" }, { icon: monochrome ? "◎" : "🎯", label: tr("Ideal", "Ideal"), state: "○ OFF", tone: "accent" }, { icon: monochrome ? "☷" : "🕹", label: tr("Manual", "Manual"), state: "✓ ON", tone: "success" }]
        if (kind === "general") return [{ icon: "▶", label: tr("Iniciar", "Start"), state: "○ OFF", tone: "success" }, { icon: monochrome ? "▶" : "⚡", label: tr("Rápido", "Fast"), state: "○ OFF", tone: "warning" }, { icon: monochrome ? "☷" : "🕹", label: tr("Manual", "Manual"), state: "✓ ON", tone: "success" }, { icon: "⇄", label: tr("Trocar", "Change"), state: "○ OFF", tone: "accent" }]
        if (kind === "methods") return [{ kind: "microphone", label: tr("Voz", "Voice"), state: "", tone: "success" }, { icon: "⌨", label: "Text-Bot", state: "", tone: "accent" }, { icon: monochrome ? "☷" : "🖱", label: tr("Botões", "Buttons"), state: "", tone: "warning" }, { icon: monochrome ? "▯" : "📱", label: tr("Telemóvel", "Phone"), state: "MQTT", tone: "accent" }]
        if (kind === "response") return [{ icon: "i", label: tr("Resposta", "Response"), state: tr("Motor 1 ligado", "Motor 1 on"), tone: "accent" }, { icon: "◇", label: tr("Estado do sistema", "System status"), state: tr("Manual ativo", "Manual active"), tone: "success" }]
        if (kind === "actionbar") return [{ kind: "microphone", label: tr("FALAR", "SPEAK"), state: "", tone: "success" }, { kind: "microphone", label: tr("Voz", "Voice"), state: "", tone: "warning" }, { icon: "▶", label: tr("Velocidade", "Speed"), state: "", tone: "accent" }, { kind: "volume", label: tr("Voltar a ouvir", "Listen again"), state: "", tone: "success" }, { icon: "×", label: tr("Limpar", "Clear"), state: "", tone: "inactive" }]
        if (kind === "operation") return [{ icon: "◉", label: tr("Controlo Geral", "General Control"), state: "", tone: "accent" }, { icon: "☷", label: tr("Controlo Manual", "Manual Control"), state: "", tone: "success" }]
        if (kind === "currentstate") return [{ icon: "◇", label: tr("Modo ativo", "Active mode"), state: tr("✓ Manual", "✓ Manual"), tone: "success" }, { icon: "▣", label: tr("Sistema", "System"), state: tr("✓ Controlo manual ativo", "✓ Manual control active"), tone: "success" }, { icon: "≋", label: tr("Processo", "Process"), state: tr("A aguardar comando", "Waiting for command"), tone: "success" }]
        if (kind === "manual") return [{ icon: "●", label: tr("Luz verde", "Green light"), state: "✓ ON", tone: "success" }, { icon: "▰", label: tr("Cilindro A", "Cylinder A"), state: tr("Avançado", "Extended"), tone: "accent" }, { icon: "⚙", label: tr("Motor 1", "Motor 1"), state: "○ OFF", tone: "inactive" }, { icon: "♟", label: tr("Robô metal", "Robot metal"), state: "○ OFF", tone: "warning" }]
        if (kind === "events") return [{ icon: "✓", label: "[007] MOTOR_1_ON", state: "OK", tone: "success" }, { icon: "≡", label: tr("Eventos", "Events"), state: tr("Histórico", "History"), tone: "accent" }]
        if (kind === "reject") return [{ icon: "✕", label: "REJECT", state: tr("Não executado", "Not executed"), tone: "error" }, { icon: "!", label: tr("Ver descrição", "Read description"), state: "", tone: "warning" }]
        if (kind === "textbot") return [{ icon: "⌨", label: tr("Ligar Motor 1", "Switch on Motor 1"), state: "", tone: "accent" }, { icon: "➤", label: tr("Enviar", "Send"), state: "", tone: "success" }]
        if (kind === "online") return [{ icon: "○", label: "Offline", state: tr("Lista local", "Local list"), tone: "warning" }, { icon: "✓", label: "Online", state: "IA", tone: "success" }]
        if (kind === "voice") return [{ kind: "microphone", label: tr("Fala", "Speak"), state: "", tone: "success" }, { icon: "✦", label: tr("Blanky interpreta", "Blanky interprets"), state: "", tone: "accent" }, { icon: "✓", label: tr("Executa ou responde", "Executes or responds"), state: "", tone: "success" }]
        if (kind === "unknown") return [{ icon: "✕", label: tr("Não percebi", "Not understood"), state: "", tone: "error" }, { kind: "microphone", label: tr("Fale novamente", "Speak again"), state: "", tone: "warning" }]
        if (kind === "settings") return [{ kind: "microphone", label: tr("Áudio e microfone", "Audio and microphone"), state: "", tone: "warning" }, { icon: "↔", label: tr("Comunicações e IA", "Communications and AI"), state: "", tone: "success" }]
        if (kind === "audio") return [{ kind: "volume", label: tr("Volume", "Volume"), state: "", tone: "accent" }, { icon: "✦", label: tr("Voz", "Voice"), state: "", tone: "warning" }, { kind: "microphone", label: tr("Microfone", "Microphone"), state: "", tone: "success" }, { icon: "⚙", label: tr("Aparência", "Appearance"), state: "", tone: "accent" }]
        if (kind === "appearance") return [{ icon: "☾", label: tr("Escuro", "Dark"), state: "", tone: "accent" }, { icon: "☀", label: tr("Claro", "Light"), state: "", tone: "warning" }, { icon: "◐", label: tr("Alto contraste", "High contrast"), state: "", tone: "success" }, { icon: "◉", label: tr("Daltonismo", "Colour vision"), state: "", tone: "accent" }, { icon: "□", label: tr("Monocromático", "Monochrome"), state: "", tone: "inactive" }, { icon: "⚙", label: tr("Personalizado", "Custom"), state: "", tone: "accent" }]
        return []
    }

    Repeater {
        model: tutorial.steps()

        Column {
            id: stepBlock
            required property var modelData
            required property int index
            width: tutorial.width
            spacing: Math.round(8 * tutorial.textScale)

            HelpStepCard {
                width: parent.width
                number: String(stepBlock.index + 1)
                title: parent.modelData.title
                description: parent.modelData.text
                accentColor: tutorial.tone(parent.modelData.tone)
                surfaceColor: tutorial.panelAltColor
                textColor: tutorial.textColor
                mutedText: tutorial.mutedText
                textScale: tutorial.textScale

                GridLayout {
                    width: parent.width
                    columns: tutorial.demoItems(stepBlock.modelData.demo).length > 2 ? 2 : tutorial.demoItems(stepBlock.modelData.demo).length
                    columnSpacing: Math.round(8 * tutorial.textScale)
                    rowSpacing: Math.round(8 * tutorial.textScale)

                    Repeater {
                        model: tutorial.demoItems(stepBlock.modelData.demo)
                        HelpDemoButton {
                            required property var modelData
                            Layout.fillWidth: true
                            icon: modelData.icon || ""
                            iconKind: modelData.kind || ""
                            label: modelData.label
                            statusText: modelData.state
                            informational: stepBlock.modelData.demo === "currentstate"
                            active: modelData.tone === "success" && modelData.state.indexOf("✓") >= 0
                            accentColor: tutorial.tone(modelData.tone)
                            surfaceColor: tutorial.panelColor
                            textColor: tutorial.textColor
                            mutedText: tutorial.mutedText
                            textScale: tutorial.textScale
                        }
                    }
                }
            }

            HelpInfoCard {
                visible: parent.modelData.noteKind.length > 0
                width: parent.width
                kind: parent.modelData.noteKind
                title: parent.modelData.noteTitle
                message: parent.modelData.note
                accentColor: tutorial.accentColor
                successColor: tutorial.successColor
                warningColor: tutorial.warningColor
                errorColor: tutorial.errorColor
                surfaceColor: tutorial.panelAltColor
                textColor: tutorial.textColor
                mutedText: tutorial.mutedText
                textScale: tutorial.textScale
            }
        }
    }
}
