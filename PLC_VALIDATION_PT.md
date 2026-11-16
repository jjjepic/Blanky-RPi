# Validação da comunicação bidirecional no laboratório

Regista em cada ensaio o commit do Blanky, versões de `asyncua`/Python, IPs, firmware dos dois PLCs, versão dos programas Ladder, hora sincronizada e condições de rede. Não interpretes o retorno DB4 como ACK individual: o protocolo atual não contém identificador de pedido nem heartbeat do percurso entre PLCs.

## Preparação

1. Com os atuadores em condição segura, confirma que o servidor OPC UA disponibiliza o namespace `http://OPC UA Receber` e os 25 IDs `i=2` a `i=26`. Verifica as permissões dos nós de comando existentes em `ns=4` sem escrever em atuadores fora do ensaio.
2. Inicia o Blanky e observa o cartão OPC UA. A ligação ao servidor e a leitura de feedback são conceitos diferentes. Confirma que a leitura inicial completa não produz 25 Eventos nem fala em série.
3. No telemóvel, subscreve `blanky/monitor/pt/system`, `blanky/monitor/pt/mode`, `blanky/monitor/pt/cyl_c` e os tópicos `blanky/state_quality/*`. Nunca uses mensagens retidas em `mqtt_*`.
4. Executa `python -m unittest discover -s tests -q`. Os testes de integração com servidor OPC UA simulado requerem `asyncua`; os restantes funcionam sem hardware.

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
