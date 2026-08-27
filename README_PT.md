# Blanky

[Português](README_PT.md) | [English](README_EN.md)

Blanky é uma interface assistiva para controlo de uma célula industrial simulada. Reúne interação por voz, Text-Bot, botões diretos, MQTT e OPC UA, mantendo as regras de segurança num único ponto de validação.

## O que permite fazer

- Controlar o sistema por voz em linguagem natural.
- Enviar um ou mais comandos pelo Text-Bot.
- Usar os controlos diretos para sistema, modos, motores, cilindros, luzes e robô.
- Receber comandos de um telemóvel através de MQTT.
- Encaminhar comandos validados para o PLC por OPC UA.
- Consultar Eventos, diagnóstico de áudio e exportar dados em CSV ou PDF.
- Adaptar a interface aos modos Escuro, Claro, Alto contraste, Daltonismo, Monocromático e Personalizado.

## Arranque rápido

No Raspberry Pi ou numa máquina com Python 3.10+:

```bash
cd /home/jorge/Blanky20
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Para o atalho de ambiente de trabalho no Raspberry Pi, consulte [raspberrypi/README_PT.md](raspberrypi/README_PT.md).

## Chave OpenAI

Não guarde a chave API no repositório, em capturas de ecrã ou em documentos partilhados. Pode defini-la:

- no Raspberry Pi, no ficheiro local `~/.blanky/openai.env` criado pelo launcher;
- durante a sessão, em `Definições` > `Comunicações e IA` > `OpenAI`.

Também pode definir `OPENAI_API_KEY` como variável de ambiente, mas já não é necessário para abrir a aplicação.

O campo da interface é mascarado e a chave introduzida aí fica apenas na sessão atual. Se uma chave tiver sido exposta, deve ser revogada e substituída no painel da OpenAI.

## Interação por texto e voz

O Text-Bot inicia em modo `Online`. Neste modo, a IA interpreta frases naturais e só devolve comandos permitidos. Se o serviço Online não estiver disponível, o Blanky muda automaticamente para `Offline`, usa o reconhecimento local e informa esse fallback na área Resposta.

O modo `Offline` também pode ser escolhido manualmente. Aceita as variantes previstas na lista local e continua a aplicar as mesmas regras de segurança.

O reconhecimento por voz utiliza o fluxo Online para interpretar frases naturais. Sem acesso ao serviço de IA, a voz não executa comandos; os controlos diretos, MQTT e Text-Bot Offline continuam disponíveis.

## Definições

O botão de engrenagem abre duas áreas independentes:

- `Áudio e Microfone`: perfis, captação, filtros, ajustes manuais e diagnóstico.
- `Comunicações e IA`: estado das ligações automáticas, endereço MQTT, porta, prefixo de tópicos, endpoint OPC UA e chave OpenAI temporária.

Os campos que podem alterar uma ligação começam bloqueados. Use o ícone de lápis para os desbloquear e aplique as alterações quando terminar. MQTT reconecta automaticamente; um novo endereço OPC UA é usado no próximo comando enviado ao PLC.

## MQTT e telemóvel

O guia completo para Mosquitto e IoT MQTT Panel está em [MQTT_PANEL_SETUP_PT.md](MQTT_PANEL_SETUP_PT.md). Inclui tópicos de comando, tópicos de estado, configuração no telemóvel e testes de ligação.

## Estrutura do projeto

```text
blanky/       Lógica de comandos, áudio, MQTT, OPC UA e controlador QML
ui/           Interface QML e traduções PT/EN
assets/       Logótipos por modo visual
raspberrypi/  Launcher e atalho de ambiente de trabalho
exports/      Exportações geradas localmente, não versionadas
audio/        Áudio temporário gerado localmente, não versionado
```

## Segurança operacional

Todos os pedidos convergem para a mesma validação antes de produzir efeitos. Os Eventos mantêm a origem, o comando canónico e o resultado `OK` ou `REJECT`; a interface principal privilegia mensagens claras para o utilizador.

O modo Manual é necessário para comandar componentes individuais. Ao trocar de modo, os componentes manuais são desligados de forma segura antes de o novo modo ser aceite.

## Validação de acessibilidade cromática

Os perfis Universal, Protan, Deutan e Tritan usam cores semânticas, símbolos e texto; não constituem um diagnóstico nem uma declaração de conformidade legal. Para verificar contrastes, pares de estados e a simulação Machado, instale as dependências de desenvolvimento e execute:

```bash
pip install -r requirements-dev.txt
python tools/validate_color_profiles.py
```

O resultado detalhado é gravado em `docs/color_profile_validation.md`.
