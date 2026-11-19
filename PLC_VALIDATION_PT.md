# Validação da comunicação bidirecional no laboratório

Regista em cada ensaio o commit do Blanky, versões de `asyncua`/Python, IPs, firmware dos dois PLCs, versão dos programas Ladder, hora sincronizada e condições de rede. Não interpretes o retorno DB4 como ACK individual: o protocolo atual não contém identificador de pedido nem heartbeat do percurso entre PLCs.

## Preparação

1. Com os atuadores em condição segura, executa `python tools/diagnose_plc_opcua.py --url opc.tcp://192.168.30.3:4840` no Raspberry Pi (usa o endpoint guardado nas definições do Blanky, se for diferente). O diagnóstico **não escreve** no PLC: lista os namespaces, verifica os 24 nós de comando `ns=4` por metadados e lê os 25 sinais `i=2` a `i=26` do URI `http://OPC UA Receber`. A existência de um nó não prova que a escrita está autorizada nem que ele está associado ao DB correto.
2. Inicia o Blanky e observa o cartão OPC UA. A ligação ao servidor e a leitura de feedback são conceitos diferentes. Confirma que a leitura inicial completa não produz 25 Eventos nem fala em série.
3. No telemóvel, subscreve `blanky/monitor/pt/system`, `blanky/monitor/pt/mode`, `blanky/monitor/pt/cyl_c` e os tópicos `blanky/state_quality/*`. Nunca uses mensagens retidas em `mqtt_*`.
4. Executa `python -m unittest discover -s tests -q`. Os testes de integração com servidor OPC UA simulado requerem `asyncua`; os restantes funcionam sem hardware.

## Isolar a falha quando HMI e Blanky não comandam

Os PDFs fornecidos documentam `DB100` (comandos) e `DB4` (retorno) nos dois PLCs, com `TRCV_C`/`TSEND_C` no OB1. Porém, a página 32 da exportação do PLC Send&Receive diz que a pasta **Server interfaces** do OPC UA está vazia. Isso é incompatível com a interface de nós que o Blanky espera, mas **não demonstra** que o projeto atualmente descarregado no PLC seja igual ao PDF. Confirmar online no TIA Portal a interface OPC UA, a licença/ativação do servidor, o endpoint, os certificados/permissões e os NodeIds reais antes de alterar o mapa do Blanky.

1. Sem o Blanky a emitir comandos, testa primeiro um comando seguro diretamente na HMI e observa online no PLC Maquete o bit `Dados_HMI`, a condição global correspondente e o `DB4` de retorno. Se nem o bit da HMI muda, a falha é anterior à ponte OPC UA/TCP do Blanky. Confirma comunicação HMI-PLC, CPU em RUN, permissões e interbloqueios/erro de segurança. Não contornar interbloqueios.
2. Se a HMI muda o estado no PLC Maquete, verifica se `DB4` muda lá; depois observa `TSEND_C` no Maquete (`%M100.4` BUSY, `%M100.7` ERROR, `%MW101` STATUS) e `TRCV_C` no S&R (`%M20.2` ERROR, `%MW22` STATUS, `%MW24` RCVD_LEN), bem como `DB4` no S&R. O servidor OPC UA não substitui esta ligação TCP.
3. Se o `DB4` no S&R acompanha o Maquete mas o diagnóstico OPC UA não lê os 25 nós, a falha está na interface OPC UA, no mapeamento dos nós ou nas permissões. Se o retorno lê bem mas os comandos do Blanky falham, compara os BrowseNames apresentados pelo diagnóstico com o mapa `ns=4`, observa `DB100` no S&R durante o impulso OPC UA de 300 ms e verifica `TSEND_C` no S&R (`%M21.2` ERROR, `%MW26` STATUS) e `TRCV_C` no Maquete (`%M110.2` ERROR, `%MW112` STATUS, `%MW114` RCVD_LEN).
4. No modo **PLC sincronizado**, o Blanky não envia novos comandos comuns enquanto não tiver uma leitura inicial completa do retorno; isto é deliberado para não assumir estados desconhecidos. O modo **Teste local** pode continuar a escrever OPC UA quando o servidor está ligado, mesmo sem retorno, e os tópicos MQTT de comando também continuam ativos. Não interpretar a resposta local como confirmação do PLC ou da posição física.

## Matriz de ensaios

| Ensaio | Ação | Observação esperada |
| --- | --- | --- |
| Arranque externo | Iniciar pela HMI ou botão físico | `start` e modo atual mudam apenas após retorno DB4; nenhum comando é reenviado pelo Blanky. |
| Modo externo | Selecionar Manual na HMI | Painel Manual fica disponível com o modo comunicado pelo PLC. |
| Motor automático | Ativar saída de um motor no ciclo automático | Indicador e consulta mostram saída lógica ligada; não afirmar rotação física. |
| Pedido Blanky | Pedir `MOTOR_1_ON` por botão, texto, voz e telemóvel | Evento de pedido, etapa de escrita, estado observado ou timeout. O indicador não muda no instante da aceitação. |
| Comando repetido | Repetir o pedido enquanto pendente e depois do estado correspondente | Pedido redundante recusado sem nova escrita OPC UA. |
| A/B | Avançar/recuar com sensores de fim de curso | Mostrar posição só com par coerente; entre sensores mostrar não confirmado. |
| C/D | Pedir avanço e depois recuo por todas as modalidades | Avanço confirmado por `S_C1`/`S_D1`; recuo recusado pelo Blanky. Sensor de avanço `FALSE` não significa recuado. |
| Luz a piscar | Observar luz vermelha durante ciclo/paragem | Histórico técnico acompanha mudanças sem TTS por cada oscilação. |
| Recolha | Gerar pedido para Tapete 2/3 | Mostrar pedido de recolha manual, não movimentação de robô. |
| Erro PLC | Ativar `system_error` no PLC | Aviso visual e áudio prioritário, sem causa inventada. |
| Perda OPC UA | Desligar cabo/servidor e restabelecer | Estados passam a desconhecidos; fila antiga não é reproduzida; nova leitura inicial não gera eventos fictícios. |
| Perda entre PLCs | Interromper TSEND_C/TRCV_C mantendo OPC UA disponível | Documentar que o Blanky não consegue detetar com certeza esta falha sem heartbeat/diagnóstico publicado. |
| Falha de escrita | Tornar o nó de ensaio inacessível | Evento de falha; tentativa de repor o bit do impulso; nenhuma indicação falsa de atuação. |

Para tempos, regista separadamente o instante do pedido, enfileiramento, duração da escrita OPC UA e transição observada. `ack_ms` é nome histórico de diagnóstico e mede uma **observação de sinal após o pedido**, não um ACK do telegrama TCP. Repete cada ensaio sob as mesmas condições; não compares `opcua` e `asyncua` sem medições equivalentes. O impulso de 300 ms não garante entrega durante `BUSY` do `TSEND_C`; essa garantia exigiria confirmação individual implementada nos PLCs.
