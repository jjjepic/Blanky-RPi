# Blanky

[Português](README_PT.md) | [English](README_EN.md)

Blanky é uma interface assistiva para controlo de uma célula industrial simulada. Reúne interação por voz, Text-Bot, botões diretos, MQTT e OPC UA, mantendo as regras de segurança num único ponto de validação.

## O que permite fazer

- Controlar o sistema por voz em linguagem natural.
- Enviar um ou mais comandos pelo Text-Bot.
- Usar os controlos diretos para sistema, modos, motores, cilindros, luzes e pedidos de recolha.
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

O Text-Bot inicia em modo `Online`. Neste modo, a IA interpreta frases naturais e só devolve comandos permitidos ou consultas de estado validadas. Se o serviço Online não estiver disponível, o Blanky muda automaticamente para `Offline`, usa o reconhecimento local e informa esse fallback na área Resposta.

O modo `Offline` também pode ser escolhido manualmente. Aceita as variantes previstas na lista local e continua a aplicar as mesmas regras de segurança.

No reconhecimento Offline, "avança o cilindro A" seleciona o cilindro, não o arranque do sistema; "para" só significa parar quando surge sozinho ou no início da frase. As recusas e pedidos sem alteração usam frases naturais em PT/EN, iguais na Resposta, nos Eventos e na resposta falada, sem identificadores internos no texto da mensagem. Para escolher outro modo, usa o botão `Mudar de modo`.

O reconhecimento por voz precisa da OpenAI para transcrever o áudio. Se a interpretação Online falhar depois da transcrição, tenta o interpretador Offline. Sem acesso ao serviço de IA para transcrição, a voz não executa pedidos; os controlos diretos, MQTT e Text-Bot Offline continuam disponíveis.

A fala passa por um coordenador único: a síntese não bloqueia a interface, uma nova gravação interrompe respostas antigas antes de captar áudio e confirmações de botões/telemóvel próximas podem ser agrupadas. A fala de um comando aceite confirma apenas o **pedido aceite**, nunca uma posição física. Respostas solicitadas, avisos críticos e confirmações têm prioridades distintas. **Repetir resposta** usa a última fala iniciada, com a voz, velocidade e idioma atuais. Falhas de TTS/reprodução ficam no Diagnóstico de áudio. Consulta [AUDIO_VALIDATION_PT.md](AUDIO_VALIDATION_PT.md) para validar no Raspberry Pi.

## Consultas de estado

Por voz ou Text-Bot, Online ou Offline, podes perguntar pelo sistema, modo, motores, cilindros, luzes, robô, MQTT, OPC UA, OpenAI, erros, último evento e ações disponíveis. Exemplos: `Como está o sistema?`, `O cilindro A está avançado?`, `Diz-me o estado do OPC UA e da OpenAI`, `O que posso fazer agora?` e `Repete`. Podes misturar uma ação e uma pergunta, por exemplo `Liga o motor 1 e diz-me se o MQTT está ligado`.

Também podes consultar grupos: `Quais os motores ligados?`, `Que cilindros estão avançados?`, `O que é que está ligado?`. Para saber as preferências, pergunta `Que voz estás a usar?`, `Qual é o volume?` ou `Quais são as vozes disponíveis?`. As respostas faladas são curtas; o ecrã e os Eventos mantêm o detalhe, incluindo a origem do estado e os limites da confirmação pelo PLC.

## Definições por voz ou Text-Bot

Podes pedir `Põe o volume a 60`, `Aumenta o volume`, `Fala mais devagar`, `Muda a voz para a Coral`, `Muda para o tema claro` ou `Letra maior`. Também podes alterar idioma, perfil cromático, perfil de áudio, animações, escala do ecrã e modo Online/Offline do Text-Bot. Estas definições funcionam mesmo com o sistema parado, usam os mesmos limites dos controlos da interface e ficam registadas como `Definição`. Não enviam nada ao PLC. Parâmetros MQTT/OPC UA e a chave OpenAI só podem ser alterados no menu de definições.

As consultas funcionam com o sistema parado, são registadas como `Consulta` e não enviam comandos ao PLC. No modo sincronizado, o estado apresentado provém do retorno comunicado pelo PLC, nunca apenas do último pedido aceite. No modo de teste, as consultas identificam explicitamente os estados como locais e não confirmados. Motores e luzes refletem saídas lógicas; A/B refletem sensores de fim de curso; C/D só confirmam avanço, não recuo. A disponibilidade da OpenAI não é garantida só por existir uma chave configurada.

## Definições

O botão de engrenagem abre duas áreas independentes:

- `Áudio e Microfone`: perfis, captação, filtros, ajustes manuais e diagnóstico.
- `Comunicações e IA`: estado das ligações automáticas, endereço MQTT, porta, prefixo de tópicos, endpoint OPC UA e chave OpenAI temporária.

Em **Comunicações e IA**, o switch **Modo de controlo** alterna entre **PLC sincronizado** (padrão em cada arranque, depende do retorno) e **Teste local** (resposta e estados locais imediatos, mesmo sem PLC). O cabeçalho e o Painel de Operação identificam o modo. **Atenção:** no teste, os comandos continuam a ser enviados ao PLC sempre que a ligação OPC UA existir, e os tópicos MQTT de comando permanecem ativos; ambos podem acionar a maquete. O estado local não prova que isso ocorreu. O histórico e os tópicos `state_quality/*` assinalam `local`, exceto um erro ativo recebido do PLC, que continua a ser apresentado e bloqueia comandos. `monitor/control_mode` publica `test` ou `plc`. Para regressar aos estados reais, desliga o switch; qualquer pedido pendente tem de terminar antes da mudança. Esta opção não é guardada entre arranques.

No teste, os pedidos de avanço de C/D e de recolha do robô usam um impulso local/MQTT de 2 segundos: depois, o botão regressa a inativo para permitir novo pedido. Isto **não confirma o recuo físico**. A escrita OPC UA mantém o impulso normal de 0,3 s e C/D continuam sem nó de recuo dedicado. No modo sincronizado, C/D mostram `OFF` quando o PLC comunica um sinal de avanço válido mas inativo, e `? Incerto` quando não há leitura válida. `OFF` não comprova recuo.

Em **Eventos**, a vista simples mostra uma linha por pedido e atualiza-a com o resultado. Ativa **Eventos detalhados** em **Aparência e acessibilidade** para ver o registo técnico com os títulos fixos. Ambas as vistas usam o mesmo histórico da sessão. Todas as etapas continuam disponíveis nas exportações e não são lidas individualmente em voz alta.

Os campos que podem alterar uma ligação começam bloqueados. Use o ícone de lápis para os desbloquear e aplique as alterações quando terminar. MQTT reconecta automaticamente; ao mudar o endereço OPC UA, a ligação persistente é restabelecida no novo servidor.

Nos cartões de Comunicações, `OpenAI` substitui apenas a apresentação de `MQTT Base`; o serviço MQTT continua ativo. O cartão OpenAI não faz pedidos de teste: indica chave por configurar, espera, pedido em curso ou resultado do último pedido. O tempo mostrado é a duração do último pedido STT, interpretação IA ou geração/descarregamento TTS, não o tempo total de fala ou uma latência de ligação permanente. Após um pedido por voz, o cartão Microfone apresenta a duração da última gravação, com o mesmo valor de captação dos logs de áudio. A indicação `Ligado` mantém o significado anterior de áudio inicializado; não confirma se a ficha jack está inserida.

## OPC UA: envio e receção

O Blanky usa `asyncua` para enviar os comandos existentes do mapa `ns=4` e observar os 25 sinais de retorno do mapa `OPC UA Receber` (atualmente `ns=5`, identificadores `i=2` a `i=26`). O índice do espaço de nomes de receção é resolvido pelo URI `http://OPC UA Receber`; pode ser alterado com `BLANKY_OPCUA_RECEIVE_NAMESPACE_URI` se o PLC usar outro URI. A ligação é mantida mesmo sem comandos, com subscrição dos sinais e leitura periódica como alternativa quando a subscrição não está disponível.

O percurso de comando é Blanky → escrita OPC UA no PLC Send&Receive → DB100 → TSEND_C/TRCV_C → PLC Maquete. O retorno faz o percurso inverso a partir dos estados da maquete no DB4 até aos 25 nós de `OPC UA Receber`. No modo sincronizado, o envio não espera pela leitura inicial de retorno: pode-se iniciar com estado incerto, desde que haja ligação OPC UA. Pedidos pendentes de arranque e modo podem habilitar a sequência de controlo, mas não alteram os estados apresentados. Só os dados recebidos do PLC os atualizam, incluindo alterações originadas na HMI ou no ciclo automático. Uma quebra OPC UA invalida os valores atuais; a religação lê de novo a base antes de anunciar transições.

O Blanky distingue pedido aceite, enfileiramento, escrita OPC UA, estado observado e timeout/erro no histórico. O estado observado **não é um ACK individual** nem prova que aquele pedido causou a alteração. O servidor OPC UA ligado e a subscrição operacional também não provam, sem heartbeat próprio, a frescura da ligação TCP entre os dois PLCs. Sinais complementares incoerentes aparecem como não confirmados, não como `OFF` inventado. Motores e luzes representam saídas lógicas, A/B usam sensores de avanço/recuo, e C/D usam os sinais DBX2.0/DBX2.1 agora alimentados pelos sensores de avanço `S_C1`/`S_D1`. O valor `FALSE` de C/D não prova recuo. Não são inventados novos NodeIds para os sensores de recuo.

Nesta versão, o Blanky só pode pedir avanço de C/D; recuo por voz, Text-Bot, botão ou MQTT é recusado e nunca escrito no PLC. `ROBOT_TO_METAL` e `ROBOT_TO_NONMETAL` mantêm os nomes técnicos por compatibilidade, mas representam pedidos de recolha manual nos Tapetes 2 e 3; não há robô físico em operação. O PLC mantém a responsabilidade pela reposição de C/D ao sair do modo manual ou entrar em STOP/erro.

O cartão OPC UA mostra a última duração de escrita ou de observação de um sinal de retorno. A escrita concluída significa resposta do servidor OPC UA; o sinal é apenas um estado observado, sem atribuição causal inequívoca. O impulso de comando mantém 300 ms como ponto de partida, com tentativa de reposição a `FALSE` mesmo após falha e descarte dos pedidos antigos após reconexão. Uma falha apenas na leitura do retorno não apaga a fila de envio no modo de teste; a perda da ligação ou a alteração do endpoint continua a descartá-la. Isto não garante a entrega de todos os impulsos durante `BUSY` no TSEND_C; essa garantia exige protocolo de confirmação adicional nos PLCs. Antes de testar atuadores, executa o diagnóstico OPC UA só de leitura com `python tools/diagnose_plc_opcua.py --url <endpoint>` e segue o [procedimento de validação da nova comunicação](PLC_VALIDATION_PT.md).

Os testes sem hardware podem ser executados com `python -m unittest discover -s tests -q`. Os testes OPC UA de integração precisam de `asyncua` instalado; os testes simulados de retorno, comandos e falhas não precisam de PLC físico.

### Comparar `opcua` com `asyncua`

Para comparar as duas bibliotecas no mesmo Raspberry Pi e servidor, instale também a dependência de desenvolvimento antiga e execute a medição **apenas de leitura**:

```bash
pip install -r requirements-dev.txt
python tools/benchmark_opcua.py --url opc.tcp://192.168.30.3:4840 --samples 30 --csv tempos_opcua.csv
```

O resultado contém tempos de ligação e amostras individuais de leitura (`read_ms`), com mediana e percentil 95. As amostras alternam a ordem das bibliotecas. Repita o ensaio com `--connect-first asyncua` para inverter também a ordem de ligação. Para medir escrita e retorno (`write_ms`, `return_ms`), use **exclusivamente nós de diagnóstico sem ligação a atuadores**, criados para o ensaio; o script recusa os nós de comando conhecidos do Blanky:

```bash
python tools/benchmark_opcua.py --url opc.tcp://192.168.30.3:4840 --write-node 'ns=5;i=100' --return-node 'ns=5;i=101' --allow-write --samples 30 --csv tempos_comandos.csv
```

Os IDs `i=100` e `i=101` são apenas exemplos; **não existem no mapa fornecido**. O nó de retorno deve começar em `FALSE`, passar a `TRUE` após a receção do teste e voltar a `FALSE` antes da amostra seguinte. Se o mesmo nó for usado para escrita e retorno, mede-se apenas a leitura de volta do servidor, não o percurso pelos PLCs. Registe também a versão das bibliotecas, a resolução do temporizador/intervalo de polling, a carga do Raspberry Pi e a rede utilizada. Não há resultados do PLC real nesta branch.

## MQTT e telemóvel

O guia completo para Mosquitto e IoT MQTT Panel está em [MQTT_PANEL_SETUP_PT.md](MQTT_PANEL_SETUP_PT.md). Inclui tópicos de comando, tópicos de estado, monitorização MQTT apenas de leitura e Text-Bot no telemóvel com modos Online/Offline, configuração e testes de ligação.

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
