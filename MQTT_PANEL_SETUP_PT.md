# MQTT e IoT MQTT Panel

[Português](MQTT_PANEL_SETUP_PT.md) | [English](MQTT_PANEL_SETUP_EN.md)

Este guia liga o Blanky ao broker Mosquitto e configura o telemóvel no IoT MQTT Panel. Todos os comandos recebidos por MQTT passam pelas mesmas regras de segurança dos controlos locais.

## 1. Preparar o broker Mosquitto

No Raspberry Pi:

```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
sudo systemctl status mosquitto
```

Por defeito, o Blanky usa:

| Campo | Valor |
| --- | --- |
| Broker no Raspberry Pi | `localhost` |
| Porta | `1883` |
| Prefixo de tópicos | `blanky` |

No telemóvel, `localhost` não aponta para o Raspberry Pi. Use o endereço IP do Raspberry Pi na rede local, por exemplo `192.168.1.50`, e a porta `1883`.

Pode alterar o endereço do broker, porta e prefixo em `Definições` > `Comunicações e IA`. As alterações MQTT reconectam o serviço automaticamente.

## 2. Tópicos de comando

### Botões de ação

Configure cada um como botão no IoT MQTT Panel. Envie o payload `1`.

| Ação | Tópico |
| --- | --- |
| Iniciar | `blanky/mqtt_start` |
| Parar | `blanky/mqtt_stop` |
| Modo rápido | `blanky/mqtt_mode_fast` |
| Modo ideal | `blanky/mqtt_mode_ideal` |
| Modo manual | `blanky/mqtt_mode_manual` |
| Mudar de modo | `blanky/mqtt_mode_change` |
| Robô para metal | `blanky/mqtt_robot_to_metal` |
| Robô para não metal | `blanky/mqtt_robot_to_nonmetal` |

### Interruptores de nível

Configure cada um como switch. O payload `1` liga/avança e `0` desliga/recua.

| Componente | Tópico | `1` | `0` |
| --- | --- | --- | --- |
| Motor 1 | `blanky/mqtt_motor_1` | Ligar | Desligar |
| Motor 2 | `blanky/mqtt_motor_2` | Ligar | Desligar |
| Motor 3 | `blanky/mqtt_motor_3` | Ligar | Desligar |
| Cilindro A | `blanky/mqtt_cyl_a` | Avançar | Recuar |
| Cilindro B | `blanky/mqtt_cyl_b` | Avançar | Recuar |
| Cilindro C | `blanky/mqtt_cyl_c` | Avançar | Recuar |
| Cilindro D | `blanky/mqtt_cyl_d` | Avançar | Recuar |
| Luz verde | `blanky/mqtt_green` | Ligar | Desligar |
| Luz vermelha | `blanky/mqtt_red` | Ligar | Desligar |

Também são aceites `on`, `true`, `high` e `pulse` para ligar; `off`, `false` e `low` para desligar.

## 3. Sequência segura de utilização

1. Envie `mqtt_start`.
2. Escolha um modo: rápido, ideal ou manual.
3. Para componentes individuais, escolha primeiro o modo manual.
4. Para trocar de modo, envie `mqtt_mode_change` e escolha o novo modo.
5. Use `mqtt_stop` para parar e repor o sistema.

Se um pedido não cumprir esta sequência, o Blanky publica um evento de rejeição e não envia a ação ao PLC.

## 4. Monitorização no telemóvel

Os seguintes tópicos de estado usam `retain=true`, pelo que mostram o último estado logo que o painel se liga:

```text
blanky/state/start
blanky/state/mode_fast
blanky/state/mode_ideal
blanky/state/mode_manual
blanky/state/mode_change
blanky/state/motor_1 ... blanky/state/motor_3
blanky/state/cyl_a ... blanky/state/cyl_d
blanky/state/light_green
blanky/state/light_red
blanky/state/robot_metal
blanky/state/robot_nonmetal
```

Estes tópicos legados continuam disponíveis para os interruptores e indicadores existentes. Para um painel **apenas de leitura**, o Blanky publica agora também `blanky/monitor/*`. Nunca configure um painel de monitorização para publicar em `monitor/*` ou para enviar comandos por `mqtt_*`.

### Organização recomendada no IoT MQTT Panel

Configure o prefixo do dashboard como `blanky` e introduza apenas o sufixo indicado abaixo no campo Topic, por exemplo `state/start`. Em alternativa, use `blanky/state/start` e marque **Disable dashboard prefix topic**. Não combine o prefixo do dashboard com o caminho completo, ou pode subscrever `blanky/blanky/state/start` por engano.

| Grupo | Widget | Topic (com prefixo `blanky` no dashboard) | Configuração |
| --- | --- | --- | --- |
| Disponibilidade | Node Status | `monitor/availability` | Valores `online` / `offline`. Se o widget não permitir estes valores, use Multi-State Indicator. |
| Sistema | LED Indicator | `state/start` | Payload on `1`, off `0`; nome fixo `Sistema`. O LED não altera o nome dinamicamente. |
| Sistema | Text Output | `monitor/pt/system` | Mostra `Iniciado` ou `Parado`; colocar ao lado do LED. |
| Modo atual | Multi-State Indicator | `monitor/mode` | `stopped` = Parado; `choose_mode` = Escolher modo; `fast` = Rápido; `ideal` = Ideal; `manual` = Manual; `changing` = A escolher novo modo. |
| Modo atual | Text Output (alternativa) | `monitor/pt/mode` | Mostra a frase em português, caso o Multi-State não permita rótulos legíveis. |
| Motores | LED Indicator + Text Output | `state/motor_1` + `monitor/pt/motor_1` (também `_2`, `_3`) | `0` = Desligado; `1` = Ligado. |
| Cilindros | LED Indicator + Text Output | `state/cyl_a` + `monitor/pt/cyl_a` (também `_b`, `_c`, `_d`) | `0` = Recuo solicitado; `1` = Avanço solicitado. Não indica posição medida. |
| Luzes | LED Indicator + Text Output | `state/light_green` + `monitor/pt/light_green` (também `light_red`) | `0` = Apagada; `1` = Acesa. |
| Robô | Text Output | `monitor/pt/robot` | Sem destino ativo, Destino: peças metálicas ou Destino: peças não metálicas. A seleção é temporária. |
| Comunicações | Multi-State Indicator | `monitor/opcua` | `connected` / `disconnected`: ligação OPC UA, não confirmação de atuação. |
| Comunicações | Text Output | `monitor/pt/opcua_feedback` | `Ativo` ou `Indisponível`: receção de feedback OPC UA. |
| Tempos OPC UA | Text Output | `monitor/pt/opcua_write_time`, `monitor/pt/opcua_ack_time` | Última escrita e última confirmação do PLC, em ms; ausência indicada por texto. Não são tempos MQTT. |
| Última atividade | Text Output | `monitor/pt/last_message` | Última resposta ou recusa legível; não é um histórico completo. |

Os equivalentes em inglês estão em `monitor/en/...`. Todos os tópicos `monitor/*` são retidos, salvo se o broker ainda não tiver recebido a primeira publicação. Use texto, símbolo e posição além da cor; evite usar só vermelho/verde para estados críticos. O Node Status indica a **presença do processo Blanky no broker**, não que o sistema foi iniciado nem que o PLC está ligado. O valor `offline` é publicado ao sair normalmente e pelo Last Will se a ligação cair inesperadamente; pode haver um pequeno atraso até o broker detetar a perda. Ignore os últimos estados retidos quando a disponibilidade estiver `offline`.

Os tópicos `state/*` e `monitor/*` representam o estado interno do Blanky. A ligação OPC UA e o feedback indicam comunicação, **não confirmam individualmente a posição física de cada atuador**. Os sensores/estados recebidos do PLC ainda não são publicados em MQTT como estados físicos por componente.

Para diagnóstico avançado, continuam disponíveis:

| Tópico | Conteúdo |
| --- | --- |
| `blanky/events/last_command` | Último comando e origem, em JSON |
| `blanky/events/rejected` | Comando rejeitado e motivo, em JSON |

O cartão `MQTT Telemóvel` na interface Blanky mostra atividade durante 30 segundos depois de receber uma mensagem válida. `events/last_command` contém a última tentativa, mesmo que seja recusada; `events/rejected` não substitui `monitor/pt/last_message` para leitura acessível.

## 5. Testar a ligação

No Raspberry Pi, abra dois terminais:

```bash
mosquitto_sub -h localhost -v -t 'blanky/#'
```

Noutro terminal, envie um comando:

```bash
mosquitto_pub -h localhost -t blanky/mqtt_start -m 1
```

Deve ver o comando nos Eventos do Blanky e nos tópicos `blanky/events/last_command` e `blanky/state/*`.
Para observar apenas os novos tópicos de apresentação, use `mosquitto_sub -h localhost -v -t 'blanky/monitor/#'`.

## 6. Problemas frequentes

- `MQTT Base` offline: confirme se o serviço Mosquitto está ativo e se o host/porta em Definições correspondem ao broker.
- `MQTT Telemóvel` sem atividade: confirme o IP do Raspberry Pi, o prefixo `blanky` e se o telemóvel está na mesma rede.
- Comando rejeitado: confirme a sequência de segurança e o modo ativo antes de controlar componentes individuais.
- Nenhuma atualização de estado: subscreva `blanky/state/#` e confirme que o prefixo no painel é o mesmo configurado no Blanky.

Para instalações fora de uma rede local controlada, ative autenticação no Mosquitto e proteja o acesso à rede antes de expor a porta MQTT.
